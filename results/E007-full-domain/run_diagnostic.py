import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import hashlib,json,time
from pathlib import Path
import numpy as np
from run_experiment import Model,dataset,checks,sigmoid
from e004 import metrics
from pilot import summary,comparison,holm

def adam(weights,grad,m,v,step):
    for l,g in enumerate(grad):
        m[l]=.9*m[l]+.1*g;v[l]=.999*v[l]+.001*g*g
        weights[l]-=.03*(m[l]/(1-.9**(step+1)))/(np.sqrt(v[l]/(1-.999**(step+1)))+1e-8)

def snapshot(net,x,y,train,unseen):
    soft=net.forward(x)[0];hard=net.forward(x,hard=True)[0]
    assert np.array_equal(hard,net.hard_reference(x))
    return dict(soft_all=metrics(soft,y),hard_all=metrics(hard,y),
                soft_train=metrics(soft[train],y[train]),hard_train=metrics(hard[train],y[train]),
                soft_unseen=None if unseen is None else metrics(soft[unseen],y[unseen]),
                hard_unseen=None if unseen is None else metrics(hard[unseen],y[unseen]),hard_equivalent=True)

def run():
    root=Path(__file__).resolve().parent;out=root/'run';out.mkdir(exist_ok=False)
    start=time.monotonic();verification=checks();records=[];controls=[]
    for seed in range(500,516):
        for task in ('numeric','selection'):
            x,y,half,unseen=dataset(task)
            for mode in ('gate2','lut4'):
                for amount in ('half32','full64'):
                    tr=half if amount=='half32' else np.arange(64)
                    net=Model(seed,mode);m=[np.zeros_like(w) for w in net.weights];v=[a.copy() for a in m]
                    tick=time.monotonic();observations={};curve=[]
                    for step in range(1600):
                        if time.monotonic()-start>900:raise RuntimeError('900-second budget reached; progress saved')
                        loss,g=net.gradients(x[tr],y[tr]);adam(net.weights,g,m,v,step)
                        if step%100==0 or step in (399,1599):curve.append(dict(step=step+1,loss=loss))
                        if step in (399,1599):
                            observations[str(step+1)]=snapshot(net,x,y,tr,unseen if amount=='half32' else None)
                            np.savez(out/f'{task}-{seed}-{mode}-{amount}-{step+1}.npz',
                                     **{f'w{i}':w for i,w in enumerate(net.weights)},**{f'pair{i}':p for i,p in enumerate(net.pairs)},
                                     head=net.pairs[-1] if mode=='gate2' else net.head)
                    records.append(dict(seed=seed,task=task,condition=mode,training=amount,observations=observations,curve=curve,
                                        train_examples=len(tr),updates=1600,example_presentations=1600*len(tr),seconds=time.monotonic()-tick))
                    (out/'progress.json').write_text(json.dumps(dict(records=records,controls=controls),indent=2))
            # Positive control: a separately trainable probability per input/output.
            rng=np.random.default_rng(seed)
            w=rng.normal(0,.1,(64,4));weights=[w];m=[np.zeros_like(w)];v=[np.zeros_like(w)]
            for step in range(400):
                p=sigmoid(w);adam(weights,[(p-y)/y.size],m,v,step)
            hard=w>=0
            # Independent address computation, rather than relying on row order.
            address=(x@(2**np.arange(6))).astype(int)
            reference=hard[address]
            assert np.array_equal(reference,hard)
            controls.append(dict(seed=seed,task=task,condition='direct_lut6',training='full64',updates=400,
                                 soft_all=metrics(sigmoid(w),y),hard_all=metrics(hard,y),trainable_logits=256,hard_table_bits=256,
                                 head_input_connections=24,hard_equivalent=True))
            np.savez(out/f'{task}-{seed}-direct_lut6.npz',weights=w)
        (out/'progress.json').write_text(json.dumps(dict(records=records,controls=controls),indent=2))
        print('Completed seed',seed,flush=True)
    contrasts=[];aggregates=[]
    by={(r['task'],r['seed'],r['condition'],r['training']):r for r in records}
    def values(task,mode,amount,step):
        return np.array([by[task,s,mode,amount]['observations'][str(step)]['hard_all']['exact'] for s in range(500,516)])
    for task in ('numeric','selection'):
        for mode in ('gate2','lut4'):
            contrasts.append(dict(task=task,condition=mode,contrast='full1600_minus_half1600',**comparison(values(task,mode,'full64',1600)-values(task,mode,'half32',1600))))
            contrasts.append(dict(task=task,condition=mode,contrast='full1600_minus_full400',**comparison(values(task,mode,'full64',1600)-values(task,mode,'full64',400))))
            for amount in ('half32','full64'):
                for step in (400,1600):
                    group=[by[task,s,mode,amount]['observations'][str(step)] for s in range(500,516)]
                    aggregates.append(dict(task=task,condition=mode,training=amount,step=step,
                                           perfect_hard_runs=int((values(task,mode,amount,step)==1).sum()),
                                           metrics={f'{k}_{metric}':summary([r[k][metric] for r in group]) for k in ('soft_all','hard_all','soft_train','hard_train') for metric in ('exact','bit_accuracy')},
                                           unseen=None if amount=='full64' else {f'{k}_{metric}':summary([r[k][metric] for r in group]) for k in ('soft_unseen','hard_unseen') for metric in ('exact','bit_accuracy')}))
        contrasts.append(dict(task=task,condition='lut4_vs_gate2',contrast='full1600_lut4_minus_gate2',**comparison(values(task,'lut4','full64',1600)-values(task,'gate2','full64',1600))))
    holm(contrasts)
    result=dict(records=records,controls=controls,aggregates=aggregates,contrasts=contrasts,verification=verification,
                elapsed_seconds=time.monotonic()-start,numpy=np.__version__,split={'half_train':half.tolist(),'half_unseen':unseen.tolist()},
                sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')},
                protocol_sha256=hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest())
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Complete:',len(records),'main runs;',len(controls),'controls')

if __name__=='__main__':run()
