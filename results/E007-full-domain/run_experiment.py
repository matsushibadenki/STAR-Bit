import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import hashlib,itertools,json,time
from pathlib import Path
import numpy as np
from e004 import Net,TABLE,softmax,dataset,metrics
from experiment import rewire
from pilot import summary,comparison,holm

def sigmoid(x):return 1/(1+np.exp(-np.clip(x,-50,50)))

class Model(Net):
    def __init__(self,seed,mode):
        super().__init__(seed);rewire(self,'coverage_layered',seed)
        self.mode=mode
        if mode=='gate2':return
        q=softmax(self.weights[-1])@TABLE
        self.head=self.pairs[-1].copy()
        if mode=='lut4':
            rng=np.random.default_rng(seed+92000)
            self.head=np.array([list(p)+rng.choice([i for i in range(38,70) if i not in p],2,replace=False).tolist() for p in self.head])
            q=np.tile(q,(1,4))
        self.weights[-1]=np.log(q/(1-q))
        self.bits=((np.arange(q.shape[1])[:,None]>>np.arange(self.head.shape[1]))&1)

    def forward(self,x,temp=1.,hard=False):
        if self.mode=='gate2':return super().forward(x,temp,hard)
        bank=x.copy();cache=[]
        for pairs,w in zip(self.pairs[:2],self.weights[:2]):
            a,b=bank[:,pairs[:,0]],bank[:,pairs[:,1]]
            p=np.eye(16)[w.argmax(1)] if hard else softmax(w)
            q=p@TABLE
            v=np.stack(((1-a)*(1-b),a*(1-b),(1-a)*b,a*b),axis=-1)
            out=(v*q[None]).sum(-1)
            cache.append((bank.shape[1],pairs,a,b,p,q,v))
            bank=np.concatenate((bank,out),axis=1)
        z=bank[:,self.head]
        factors=np.where(self.bits[None,None,:,:],z[:,:,None,:],1-z[:,:,None,:])
        basis=factors.prod(-1)
        q=(self.weights[-1]>=0).astype(float) if hard else sigmoid(self.weights[-1])
        pred=(basis*q[None]).sum(-1)
        return pred,(cache,factors,basis,q)

    def gradients(self,x,y,temp=1.):
        if self.mode=='gate2':return super().gradients(x,y,temp)
        pred,(cache,factors,basis,q)=self.forward(x)
        p=np.clip(pred,1e-9,1-1e-9)
        loss=-(y*np.log(p)+(1-y)*np.log(1-p)).mean()
        dy=(p-y)/(p*(1-p)*y.size)
        head_grad=(dy[:,:,None]*basis).sum(0)*q*(1-q)
        grad=np.zeros((len(x),70))
        for j in range(self.head.shape[1]):
            other=np.prod(np.delete(factors,j,axis=-1),axis=-1)
            dz=(other*(2*self.bits[:,j]-1)[None,None,:]*q[None]).sum(-1)*dy
            np.add.at(grad,(slice(None),self.head[:,j]),dz)
        grads=[head_grad]
        for n,pairs,a,b,p,q,v in reversed(cache):
            dy=grad[:,n:];dq=(dy[:,:,None]*v).sum(0);dp=dq@TABLE.T
            grads.append(p*(dp-(dp*p).sum(1,keepdims=True)))
            da=(q[:,1]-q[:,0])[None]*(1-b)+(q[:,3]-q[:,2])[None]*b
            db=(q[:,2]-q[:,0])[None]*(1-a)+(q[:,3]-q[:,1])[None]*a
            prev=grad[:,:n].copy()
            np.add.at(prev,(slice(None),pairs[:,0]),dy*da)
            np.add.at(prev,(slice(None),pairs[:,1]),dy*db)
            grad=prev
        return float(loss),list(reversed(grads))

    def hard_reference(self,x):
        bank=x.astype(int)
        for pairs,w in zip(self.pairs[:2],self.weights[:2]):
            idx=bank[:,pairs[:,0]]+2*bank[:,pairs[:,1]]
            out=((w.argmax(1)[None,:]>>idx)&1)
            bank=np.concatenate((bank,out),axis=1)
        if self.mode=='gate2':
            pairs=self.pairs[-1];idx=bank[:,pairs[:,0]]+2*bank[:,pairs[:,1]]
            return (self.weights[-1].argmax(1)[None,:]>>idx)&1
        idx=(bank[:,self.head]*(2**np.arange(self.head.shape[1]))).sum(-1)
        return (self.weights[-1]>=0)[np.arange(4)[None,:],idx]

def checks():
    x,y,_,_=dataset('numeric');errors=[]
    a,b,c=[Model(499,m) for m in ('gate2','lut2','lut4')]
    assert np.allclose(a.forward(x)[0],b.forward(x)[0],atol=1e-12)
    assert np.allclose(b.forward(x)[0],c.forward(x)[0],atol=1e-12)
    for model in (b,c):
        _,g=model.gradients(x[:8],y[:8])
        for l,i,j in ((0,2,3),(1,5,6),(2,1,2)):
            old=model.weights[l][i,j];eps=1e-5
            model.weights[l][i,j]=old+eps;p=model.gradients(x[:8],y[:8])[0]
            model.weights[l][i,j]=old-eps;n=model.gradients(x[:8],y[:8])[0]
            model.weights[l][i,j]=old
            errors.append(abs((p-n)/(2*eps)-g[l][i,j]));assert errors[-1]<1e-6
    return dict(initial_soft_match=True,max_gradient_error=max(errors))

def run():
    root=Path(__file__).resolve().parent;out=root/'run';out.mkdir(exist_ok=False)
    start=time.monotonic();verification=checks();rows=[]
    for seed in range(400,416):
        for task in ('numeric','selection'):
            x,y,tr,te=dataset(task)
            initial=None
            for mode in ('gate2','lut2','lut4'):
                net=Model(seed,mode);prediction=net.forward(x)[0]
                if initial is None:initial=prediction
                assert np.allclose(prediction,initial,atol=1e-12)
                m=[np.zeros_like(w) for w in net.weights];v=[w.copy() for w in m];curves=[]
                for step in range(400):
                    if time.monotonic()-start>900:raise RuntimeError('Budget exceeded; progress preserved')
                    loss,g=net.gradients(x[tr],y[tr])
                    for l,grad in enumerate(g):
                        m[l]=.9*m[l]+.1*grad;v[l]=.999*v[l]+.001*grad*grad
                        net.weights[l]-=.03*(m[l]/(1-.9**(step+1)))/(np.sqrt(v[l]/(1-.999**(step+1)))+1e-8)
                    if step%50==0 or step==399:curves.append(dict(step=step,loss=loss))
                soft=net.forward(x)[0];hard=net.forward(x,hard=True)[0]
                assert np.array_equal(hard,net.hard_reference(x))
                rows.append(dict(seed=seed,task=task,condition=mode,
                                 soft_test=metrics(soft[te],y[te]),hard_test=metrics(hard[te],y[te]),
                                 soft_train=metrics(soft[tr],y[tr]),hard_train=metrics(hard[tr],y[tr]),
                                 trainable_logits=sum(w.size for w in net.weights),
                                 hard_table_bits=320 if mode=='lut4' else 272,output_connections=16 if mode=='lut4' else 8,
                                 hard_equivalent=True,curves=curves))
                np.savez(out/f'{task}-{seed}-{mode}.npz',**{f'w{i}':w for i,w in enumerate(net.weights)},
                         **{f'pair{i}':p for i,p in enumerate(net.pairs)},head=net.pairs[-1] if mode=='gate2' else net.head)
                (out/'progress.json').write_text(json.dumps(rows,indent=2))
        print('Completed seed',seed,flush=True)
    aggregates=[];contrasts=[];effects={}
    for task in ('numeric','selection'):
        by={(r['seed'],r['condition']):r for r in rows if r['task']==task}
        for baseline in ('lut2','gate2'):
            delta=np.array([by[s,'lut4']['hard_test']['exact']-by[s,baseline]['hard_test']['exact'] for s in range(400,416)])
            contrasts.append(dict(task=task,baseline=baseline,**comparison(delta)))
            if baseline=='lut2':effects[task]=delta
        for mode in ('gate2','lut2','lut4'):
            group=[r for r in rows if r['task']==task and r['condition']==mode]
            aggregates.append(dict(task=task,condition=mode,metrics={f'{k}_{m}':summary([r[k][m] for r in group]) for k in ('soft_test','hard_test','soft_train','hard_train') for m in ('exact','bit_accuracy')}))
    contrasts.append(dict(task='selection_minus_numeric',baseline='interaction',**comparison(effects['selection']-effects['numeric'])))
    holm(contrasts)
    result=dict(records=rows,aggregates=aggregates,contrasts=contrasts,verification=verification,elapsed_seconds=time.monotonic()-start,
                sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')},protocol_sha256=hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest(),numpy=np.__version__)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(contrasts,indent=2))

if __name__=='__main__':run()
