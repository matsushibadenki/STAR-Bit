"""E005: label-free input-coverage wiring versus depth-matched random wiring."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):
    os.environ[name]='1'
import hashlib
import itertools
import json
import time
from pathlib import Path
import numpy as np
from e004 import Net,checks,dataset,export,metrics
import logic_modules as lm
from pilot import summary,comparison,holm


def lineage(pairs):
    support=[{i} for i in range(6)]
    ancestors=[set() for _ in range(6)]
    for layer in pairs:
        base=len(support)
        additions=[support[a]|support[b] for a,b in layer]
        gates=[ancestors[a]|ancestors[b]|{base+i} for i,(a,b) in enumerate(layer)]
        support.extend(additions);ancestors.extend(gates)
    return support[-4:],ancestors[-4:]


def rewire(net,mode,seed):
    if mode=='random_skip':return
    rng=np.random.default_rng(seed+81000)
    support=[{i} for i in range(6)]
    previous=list(range(6))
    result=[]
    for width in (32,32,4):
        candidates=list(itertools.combinations(previous,2))
        if mode=='coverage_layered':
            sizes=[len(support[a]|support[b]) for a,b in candidates]
            best=max(sizes)
            candidates=[p for p,size in zip(candidates,sizes) if size==best]
        chosen=[candidates[i] for i in rng.integers(len(candidates),size=width)]
        # Orientation randomized in both arms to avoid privileging input order.
        chosen=[(b,a) if flip else (a,b) for (a,b),flip in zip(chosen,rng.integers(2,size=width))]
        base=len(support)
        support.extend([support[a]|support[b] for a,b in chosen])
        previous=list(range(base,base+width))
        result.append(np.asarray(chosen,dtype=int))
    net.pairs=result


def ceilings(x,y,support):
    bit=[]
    for i,columns in enumerate(support):
        columns=sorted(columns)
        keys=(x[:,columns]@(2**np.arange(len(columns)))).astype(int)
        correct=0
        for key in np.unique(keys):
            ys=y[keys==key,i]
            correct+=max(ys.sum(),len(ys)-ys.sum())
        bit.append(float(correct/len(y)))
    return dict(per_bit=bit,bit_mean=float(np.mean(bit)),exact_upper=float(min(bit)))


def structural_checks():
    net=Net(333);original=[w.copy() for w in net.weights]
    rewire(net,'coverage_layered',333)
    assert all(np.array_equal(a,b) for a,b in zip(original,net.weights))
    assert all(len(s)==6 for s in lineage(net.pairs)[0])
    x,y,_,_=dataset('numeric')
    assert ceilings(x,y,[set(range(6))]*4)['bit_mean']==1.
    # With no input information, best prediction is class majority.
    no=ceilings(x,y,[set()]*4)
    assert np.allclose(no['per_bit'],np.maximum(y.mean(0),1-y.mean(0)))
    return {'coverage_preserves_initial_logits':True,'full_input_ceiling':1.,**checks()}


def run():
    root=Path(__file__).resolve().parent
    out=root/'run';out.mkdir(exist_ok=False)
    start=time.monotonic();verification=structural_checks();rows=[]
    for seed in range(300,316):
        for task in ('numeric','selection'):
            x,y,tr,te=dataset(task)
            inputs={f'x{i}':x[:,i].astype(bool) for i in range(6)}
            for mode in ('random_skip','random_layered','coverage_layered'):
                net=Net(seed);rewire(net,mode,seed)
                support,ancestors=lineage(net.pairs)
                upper=ceilings(x,y,support)
                m=[np.zeros_like(w) for w in net.weights];v=[a.copy() for a in m]
                curves=[];tick=time.perf_counter()
                for step in range(400):
                    if time.monotonic()-start>900:raise RuntimeError('900-second limit; progress preserved')
                    loss,grad=net.gradients(x[tr],y[tr],1.)
                    for l,g in enumerate(grad):
                        m[l]=.9*m[l]+.1*g;v[l]=.999*v[l]+.001*g*g
                        net.weights[l]-=.03*(m[l]/(1-.9**(step+1)))/(np.sqrt(v[l]/(1-.999**(step+1)))+1e-8)
                    if step%50==0 or step==399:curves.append(dict(step=step,loss=loss))
                train_seconds=time.perf_counter()-tick
                soft,_=net.forward(x);hard,_=net.forward(x,hard=True)
                programs=export(net)
                circuit=np.stack([lm.evaluate(p,inputs,{}) for p in programs],axis=1)
                assert np.array_equal(circuit,hard.astype(bool))
                full=metrics(hard,y)
                assert full['bit_accuracy']<=upper['bit_mean']+1e-9
                assert full['exact']<=upper['exact_upper']+1e-9
                rows.append(dict(seed=seed,task=task,condition=mode,
                                 soft_test=metrics(soft[te],y[te]),hard_test=metrics(hard[te],y[te]),
                                 soft_train=metrics(soft[tr],y[tr]),hard_train=metrics(hard[tr],y[tr]),hard_full=full,
                                 upper=upper,output_support=[sorted(s) for s in support],
                                 mean_input_coverage=float(np.mean([len(s) for s in support])),
                                 reachable_gates=len(set().union(*ancestors)),
                                 primitive_dag=len(set(n for p in programs for n in lm.nodes(p))),
                                 train_seconds=train_seconds,curves=curves,export_equivalent=True))
                np.savez(out/f'{task}-{seed}-{mode}.npz',**{f'w{i}':w for i,w in enumerate(net.weights)},
                         **{f'pair{i}':p for i,p in enumerate(net.pairs)})
                (out/'progress.json').write_text(json.dumps(rows,indent=2))
        print('Completed seed',seed,flush=True)
    contrasts=[];aggregates=[];effects={}
    for task in ('numeric','selection'):
        by={(r['seed'],r['condition']):r for r in rows if r['task']==task}
        for baseline in ('random_layered','random_skip'):
            difference=[by[s,'coverage_layered']['hard_test']['exact']-by[s,baseline]['hard_test']['exact'] for s in range(300,316)]
            contrasts.append(dict(task=task,baseline=baseline,**comparison(difference)))
            if baseline=='random_layered':effects[task]=np.array(difference)
        for mode in ('random_skip','random_layered','coverage_layered'):
            group=[r for r in rows if r['task']==task and r['condition']==mode]
            aggregates.append(dict(task=task,condition=mode,
                                   metrics={f'{kind}_{metric}':summary([r[kind][metric] for r in group]) for kind in ('soft_test','hard_test','soft_train','hard_train','hard_full') for metric in ('exact','bit_accuracy')},
                                   structure={k:summary([r[k] for r in group]) for k in ('mean_input_coverage','reachable_gates','primitive_dag','train_seconds')},
                                   ceilings={k:summary([r['upper'][k] for r in group]) for k in ('bit_mean','exact_upper')}))
    contrasts.append(dict(task='selection_minus_numeric',baseline='interaction',**comparison(effects['selection']-effects['numeric'])))
    holm(contrasts)
    result=dict(records=rows,aggregates=aggregates,contrasts=contrasts,verification=verification,
                elapsed_seconds=time.monotonic()-start,numpy=np.__version__,split={'train':tr.tolist(),'test':te.tolist()},
                sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')},
                protocol_sha256=hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest())
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(contrasts,indent=2))

if __name__=='__main__':run()
