import sys,time,json,hashlib,gzip
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'results/E008-fixed-wiring-sat'))
import solve as base
np,z3=base.np,base.z3
HERE=Path(__file__).resolve().parent
OUT=HERE/'run'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=False)
 started=time.monotonic(); rows=[]
 prior=json.loads((ROOT/'results/E008-fixed-wiring-sat/run_bounded/results.json').read_text())
 for r in prior['records']:
  name=f"{r['task']}-{r['seed']}-{r['condition']}"
  path=ROOT/f"results/E007-full-domain/run/{name}-full64-1600.npz"
  a=np.load(path); wires=np.concatenate([a['pair0'],a['pair1']]).tolist()+a['head'].tolist()
  x,y=base.data(r['task'])
  for bit in range(4):
   if time.monotonic()-started>900:raise RuntimeError('budget exceeded; progress retained')
   ctx,s,tables=base.build(x,y[:,bit:bit+1],wires,[70+bit]);s.set(timeout=1000)
   stem=f'{name}-bit{bit}'
   with gzip.open(OUT/f'{stem}.smt2.gz','wt') as f:f.write(s.to_smt2())
   t=time.monotonic(); status=str(s.check());elapsed=time.monotonic()-t
   row=dict(task=r['task'],seed=r['seed'],condition=r['condition'],bit=bit,status=status,joint_status=r['status'],seconds=elapsed,checkpoint_sha256=digest(path),formula_sha256=digest(OUT/f'{stem}.smt2.gz'))
   if status=='sat':
    model=s.model(); truth=[[int(z3.is_true(model.eval(v,model_completion=True))) for v in tab] for tab in tables]
    assert np.array_equal(base.evaluate(x,wires,truth,[70+bit]),y[:,bit:bit+1])
    (OUT/f'{stem}-witness.json').write_text(json.dumps(dict(wires=wires,tables=truth,outputs=[70+bit])))
    row['independent_exact']=1
   elif status=='unknown':row['reason']=s.reason_unknown()
   rows.append(row);(OUT/'progress.json').write_text(json.dumps(rows,indent=2))
   print(stem,status,flush=True)
 result=dict(records=rows,elapsed_seconds=time.monotonic()-started,z3=z3.get_version_string(),source_hashes={str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),HERE/'PROTOCOL.md',Path(base.__file__),ROOT/'results/E008-fixed-wiring-sat/pilot.py']})
 (OUT/'results.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
