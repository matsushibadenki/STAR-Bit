"""NumPy differentiable 16-function gate network; fixed random wiring."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):
    os.environ[name]='1'
import hashlib
import json
import time
from pathlib import Path
import numpy as np
import logic_modules as lm
from global_accept import fit
from pilot import summary,comparison,holm

TABLE=((np.arange(16)[:,None]>>np.arange(4))&1).astype(float)

def softmax(x):
    e=np.exp(x-x.max(-1,keepdims=True))
    return e/e.sum(-1,keepdims=True)

class Net:
    def __init__(self,seed):
        rng=np.random.default_rng(seed)
        self.pairs=[];self.weights=[];n=6
        for width in (32,32,4):
            pairs=rng.integers(n,size=(width,2))
            self.pairs.append(pairs)
            self.weights.append(rng.normal(0,.1,(width,16)))
            n+=width

    def forward(self,x,temp=1.,hard=False):
        bank=x.copy();cache=[]
        for pairs,w in zip(self.pairs,self.weights):
            a,b=bank[:,pairs[:,0]],bank[:,pairs[:,1]]
            p=np.eye(16)[w.argmax(1)] if hard else softmax(w/temp)
            q=p@TABLE
            v=np.stack(((1-a)*(1-b),a*(1-b),(1-a)*b,a*b),axis=-1)
            out=(v*q[None]).sum(-1)
            cache.append((bank.shape[1],pairs,a,b,p,q,v))
            bank=np.concatenate((bank,out),axis=1)
        return bank[:,-4:],cache

    def gradients(self,x,y,temp):
        pred,cache=self.forward(x,temp)
        clipped=np.clip(pred,1e-9,1-1e-9)
        loss=-(y*np.log(clipped)+(1-y)*np.log(1-clipped)).mean()
        grad=np.zeros((len(x),74))
        grad[:,-4:]=(clipped-y)/(clipped*(1-clipped)*y.size)
        grads=[]
        for n,pairs,a,b,p,q,v in reversed(cache):
            dy=grad[:,n:]
            dq=(dy[:,:,None]*v).sum(0)
            dp=dq@TABLE.T
            grads.append(p*(dp-(dp*p).sum(1,keepdims=True))/temp)
            da=(q[:,1]-q[:,0])[None]*(1-b)+(q[:,3]-q[:,2])[None]*b
            db=(q[:,2]-q[:,0])[None]*(1-a)+(q[:,3]-q[:,1])[None]*a
            prev=grad[:,:n].copy()
            np.add.at(prev,(slice(None),pairs[:,0]),dy*da)
            np.add.at(prev,(slice(None),pairs[:,1]),dy*db)
            grad=prev
        return float(loss),list(reversed(grads))

def gate_expr(k,a,b):
    zero=('XOR',a,a)
    # Fixed truth-table convention index = a + 2*b.
    expressions=[zero,('NOT',('OR',a,b)),('AND',a,('NOT',b)),('NOT',b),
                 ('AND',('NOT',a),b),('NOT',a),('XOR',a,b),('NOT',('AND',a,b)),
                 ('AND',a,b),('NOT',('XOR',a,b)),a,('OR',a,('NOT',b)),
                 b,('OR',('NOT',a),b),('OR',a,b),('NOT',zero)]
    return expressions[k]

def export(net):
    bank=[f'x{i}' for i in range(6)]
    for pairs,w in zip(net.pairs,net.weights):
        new=[gate_expr(int(k),bank[a],bank[b]) for (a,b),k in zip(pairs,w.argmax(1))]
        bank.extend(new)
    return bank[-4:]

def dataset(task):
    x=((np.arange(64)[:,None]>>np.arange(6))&1).astype(float)
    if task=='numeric':
        val=(x[:,:3]@np.array([1,2,4])+x[:,3:]@np.array([1,2,4])).astype(int)
        y=((val[:,None]>>np.arange(4))&1).astype(float)
    else:
        shift=(x[:,0]+2*x[:,1]).astype(int)
        y=np.stack([x[np.arange(64),2+(shift+i)%4] for i in range(4)],axis=1)
    idx=np.random.default_rng(7001).permutation(64)
    return x,y,idx[:32],idx[32:]

def metrics(p,y):
    bits=p>=.5
    return dict(exact=float((bits==y).all(1).mean()),bit_accuracy=float((bits==y).mean()))

def checks():
    inp={'a':np.array([0,1,0,1],dtype=bool),'b':np.array([0,0,1,1],dtype=bool)}
    for k in range(16):
        assert np.array_equal(lm.evaluate(gate_expr(k,'a','b'),inp,{}),TABLE[k])
    net=Net(777);x,y,_,_=dataset('numeric')
    loss,grads=net.gradients(x[:5],y[:5],.8)
    maxerr=0.
    for layer,i,j in [(0,0,3),(1,2,7),(2,1,6),(0,20,12),(2,3,15)]:
        orig=net.weights[layer][i,j];eps=1e-5
        net.weights[layer][i,j]=orig+eps;l1=net.gradients(x[:5],y[:5],.8)[0]
        net.weights[layer][i,j]=orig-eps;l0=net.gradients(x[:5],y[:5],.8)[0]
        net.weights[layer][i,j]=orig
        err=abs((l1-l0)/(2*eps)-grads[layer][i,j]);maxerr=max(maxerr,err)
        assert err<1e-6,(layer,i,j,err)
    return dict(gate_tables_verified=16,max_gradient_error=maxerr)

def run():
    root=Path(__file__).resolve().parent
    out=root/'run';out.mkdir(exist_ok=False)
    start=time.monotonic();verification=checks();rows=[]
    for seed in range(200,208):
        for task in ('numeric','selection'):
            x,y,tr,te=dataset(task)
            inputs={f'x{i}':x[:,i].astype(bool) for i in range(6)}
            for mode in ('fixed','annealed'):
                net=Net(seed);m=[np.zeros_like(w) for w in net.weights];v=[a.copy() for a in m]
                curves=[]
                for step in range(400):
                    if time.monotonic()-start>900: raise RuntimeError('900-second protocol budget reached')
                    temp=1. if mode=='fixed' else 1.-.8*step/399
                    loss,grad=net.gradients(x[tr],y[tr],temp)
                    for l,g in enumerate(grad):
                        m[l]=.9*m[l]+.1*g;v[l]=.999*v[l]+.001*g*g
                        net.weights[l]-=.03*(m[l]/(1-.9**(step+1)))/(np.sqrt(v[l]/(1-.999**(step+1)))+1e-8)
                    if step%50==0 or step==399:curves.append(dict(step=step,loss=loss,temp=temp))
                soft,_=net.forward(x,temp);hard,_=net.forward(x,hard=True)
                programs=export(net)
                compiled=np.stack([lm.evaluate(p,inputs,{}) for p in programs],axis=1)
                assert np.array_equal(hard.astype(bool),compiled)
                lib,stages,history,trials=fit(programs,'global_accept',seed)
                compressed=programs
                for lookup in stages:compressed=[lm.rewrite(p,lookup,lib,'functional') for p in compressed]
                rewritten=np.stack([lm.evaluate(p,inputs,lib) for p in compressed],axis=1)
                assert np.array_equal(compiled,rewritten)
                rows.append(dict(seed=seed,task=task,condition=mode,soft_test=metrics(soft[te],y[te]),
                                 hard_test=metrics(hard[te],y[te]),soft_train=metrics(soft[tr],y[tr]),hard_train=metrics(hard[tr],y[tr]),
                                 hard_minus_soft=metrics(hard[te],y[te])['exact']-metrics(soft[te],y[te])['exact'],
                                 primitive_symbols=lm.description(programs,{}),compressed_symbols=lm.description(compressed,lib),
                                 modules=len(lib),primitive_dag=len(set(n for p in programs for n in lm.nodes(p))),
                                 allocated_logic_gates=68,export_equivalent=True,compressed_equivalent=True,
                                 curves=curves,library=lib,history=history))
                np.savez(out/f'{task}-{seed}-{mode}.npz',**{f'w{i}':w for i,w in enumerate(net.weights)},
                         **{f'pair{i}':p for i,p in enumerate(net.pairs)})
                (out/'progress.json').write_text(json.dumps(rows,indent=2))
                print(task,seed,mode,rows[-1]['soft_test'],rows[-1]['hard_test'],flush=True)
    contrasts=[];aggregates=[]
    for task in ('numeric','selection'):
        by={(r['seed'],r['condition']):r for r in rows if r['task']==task}
        contrasts.append(dict(task=task,**comparison([by[s,'annealed']['hard_test']['exact']-by[s,'fixed']['hard_test']['exact'] for s in range(200,208)])))
        for mode in ('fixed','annealed'):
            group=[r for r in rows if r['task']==task and r['condition']==mode]
            aggregates.append(dict(task=task,condition=mode,
                                   metrics={f'{kind}_{metric}':summary([r[kind][metric] for r in group]) for kind in ('soft_test','hard_test','soft_train','hard_train') for metric in ('exact','bit_accuracy')},
                                   compression={k:summary([r[k] for r in group]) for k in ('primitive_symbols','compressed_symbols','modules','primitive_dag','hard_minus_soft')}))
    holm(contrasts)
    result=dict(records=rows,aggregates=aggregates,contrasts=contrasts,verification=verification,
                elapsed_seconds=time.monotonic()-start,numpy=np.__version__,split={'train':tr.tolist(),'test':te.tolist()},
                sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')},
                protocol_sha256=hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest())
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':run()
