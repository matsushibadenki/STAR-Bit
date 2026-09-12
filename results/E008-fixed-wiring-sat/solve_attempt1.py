"""E008 fixed-wiring exact synthesis, not training or generalization."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import gzip,hashlib,json,sys,time
from pathlib import Path
sys.path.insert(0,'/private/tmp/starbit-z3')
import numpy as np
import z3
from pilot import summary

def data(task):
    x=((np.arange(64)[:,None]>>np.arange(6))&1).astype(int)
    if task=='numeric':
        val=x[:,:3]@np.array([1,2,4])+x[:,3:]@np.array([1,2,4])
        y=(val[:,None]>>np.arange(4))&1
    else:
        shift=x[:,0]+2*x[:,1]
        y=np.stack([x[np.arange(64),2+(shift+i)%4] for i in range(4)],axis=1)
    return x,y

def mux(args,table):
    if not args:return table[0]
    half=len(table)//2
    return z3.If(args[-1],mux(args[:-1],table[half:]),mux(args[:-1],table[:half]))

def build(x,y,wires,outputs):
    ctx=z3.Context(proof=True)
    solver=z3.Solver(ctx=ctx);solver.set(timeout=10000,random_seed=0,threads=1)
    tables=[[z3.Bool(f'g{i}_t{j}',ctx) for j in range(2**len(p))] for i,p in enumerate(wires)]
    for sample,(features,target) in enumerate(zip(x,y)):
        bank=[z3.BoolVal(bool(v),ctx) for v in features]
        equations=[]
        for i,ports in enumerate(wires):
            node=z3.Bool(f'row{sample}_g{i}',ctx)
            equations.append(node==mux([bank[p] for p in ports],tables[i]))
            bank.append(node)
        equations.extend(bank[o]==z3.BoolVal(bool(v),ctx) for o,v in zip(outputs,target))
        solver.add(*equations)
    return ctx,solver,tables

def evaluate(x,wires,tables,outputs):
    bank=x.copy()
    for ports,table in zip(wires,tables):
        idx=(bank[:,ports]*(2**np.arange(len(ports)))).sum(1).astype(int)
        bank=np.column_stack((bank,np.asarray(table,dtype=int)[idx]))
    return bank[:,outputs]

def selftests():
    x=((np.arange(4)[:,None]>>np.arange(2))&1)
    y=(x[:,0]^x[:,1])[:,None]
    ctx,s,t=build(x,y,[[0,1]],[2]);assert s.check()==z3.sat
    model=s.model();witness=[[int(z3.is_true(model.eval(b,model_completion=True))) for b in t[0]]]
    assert np.array_equal(evaluate(x,[[0,1]],witness,[2]),y)
    ctx,s,t=build(x,y,[[0,0]],[2]);assert s.check()==z3.unsat
    assert s.proof() is not None
    return dict(xor_sat=True,inaccessible_input_xor_unsat=True)

def run():
    root=Path(__file__).resolve().parent;out=root/'run';out.mkdir(exist_ok=False)
    old=root.parent/'E007-full-domain/run'
    previous=json.loads((old/'results.json').read_text())
    lookup={(r['task'],r['seed'],r['condition']):r for r in previous['records'] if r['training']=='full64'}
    tests=selftests();start=time.monotonic();rows=[]
    for seed in range(500,516):
        for task in ('numeric','selection'):
            x,y=data(task)
            for mode in ('gate2','lut4'):
                if time.monotonic()-start>880:raise RuntimeError('Global time budget; partial progress saved')
                name=f'{task}-{seed}-{mode}'
                checkpoint=old/f'{name}-full64-1600.npz'
                saved=np.load(checkpoint)
                wires=saved['pair0'].tolist()+saved['pair1'].tolist()+saved['head'].tolist()
                outputs=list(range(70,74))
                tick=time.monotonic();ctx,solver,tables=build(x,y,wires,outputs)
                encoding_seconds=time.monotonic()-tick
                with gzip.open(out/f'{name}.smt2.gz','wt') as file:file.write(solver.to_smt2())
                tick=time.monotonic();status=solver.check();solve_seconds=time.monotonic()-tick
                record=dict(seed=seed,task=task,condition=mode,status=str(status),encoding_seconds=encoding_seconds,solve_seconds=solve_seconds,
                            learned_hard_exact=lookup[task,seed,mode]['observations']['1600']['hard_all']['exact'],
                            source_checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                            formula_sha256=hashlib.sha256((out/f'{name}.smt2.gz').read_bytes()).hexdigest())
                if status==z3.sat:
                    model=solver.model()
                    solution=[[int(z3.is_true(model.eval(b,model_completion=True))) for b in table] for table in tables]
                    pred=evaluate(x,wires,solution,outputs)
                    assert np.array_equal(pred,y),name
                    record.update(witness_exact=1.,learned_failed=record['learned_hard_exact']<1)
                    (out/f'{name}-witness.json').write_text(json.dumps(dict(wires=wires,tables=solution,outputs=outputs),indent=2))
                elif status==z3.unsat:
                    assert record['learned_hard_exact']<1,'Contradiction with learned perfect solution'
                    with gzip.open(out/f'{name}-proof.txt.gz','wt') as file:file.write(solver.proof().sexpr())
                    record['independently_checked_proof']=False
                else:record['reason_unknown']=solver.reason_unknown()
                rows.append(record)
                (out/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
                print(name,record['status'],'seconds',round(solve_seconds,3),flush=True)
                del tables,solver,ctx
    aggregates=[]
    for task in ('numeric','selection'):
        for mode in ('gate2','lut4'):
            group=[r for r in rows if r['task']==task and r['condition']==mode]
            aggregates.append(dict(task=task,condition=mode,n=len(group),
                                   counts={status:sum(r['status']==status for r in group) for status in ('sat','unsat','unknown')},
                                   sat_with_learning_error=sum(r.get('learned_failed',False) for r in group),
                                   learned_accuracy=summary([r['learned_hard_exact'] for r in group]),
                                   solve_seconds=summary([r['solve_seconds'] for r in group])))
    result=dict(records=rows,aggregates=aggregates,selftests=tests,z3_version=z3.get_version_string(),numpy=np.__version__,
                elapsed_seconds=time.monotonic()-start,timeout_per_case_ms=10000,
                sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')},
                protocol_sha256=hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest(),
                E007_results_sha256=hashlib.sha256((old/'results.json').read_bytes()).hexdigest())
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':run()
