import ast,hashlib,inspect,itertools,json,math,time
from pathlib import Path
import importlib.util
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E050-composition-budget-diagnostic'
spec=importlib.util.spec_from_file_location('e049',ROOT/'results/E049-frozen-cohort-semantics/main.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
# Recover round2 candidates without modifying archived E049.
src=inspect.getsource(m.scheduled_search).replace("return {'round2_selected':", "return {'beam_candidates': beam, 'round2_selected':")
ns=dict(m.__dict__); exec(compile(src,str(HERE/'main.py')+':replay','exec'),ns); replay=ns['scheduled_search']
def main():
 out=HERE/'run'; out.mkdir(); manifest=json.loads((ROOT/'results/E049-frozen-cohort-semantics/run/manifest.json').read_text()); pre=json.loads((ROOT/'results/E049-frozen-cohort-semantics/run/preflight.json').read_text()); randoms={(x['seed'],x['task']):x['cohort'] for x in manifest['random']}; tasks=m.e042.tasks_from_registry(); records=[]; start=time.monotonic(); inputs,_=m.base.inputs_and_targets()
 def evaluate(e):
  if e[0]=='input': return inputs[e[1]]
  sig=m.base.lut_outputs(evaluate(e[3]),evaluate(e[4]))[e[2]]; assert sig==int(e[1]); return sig
 with (out/'progress.jsonl').open('w') as f:
  for prior in pre:
   if time.monotonic()-start>900: break
   seed,task=prior['seed'],prior['task']; target=tasks[task]; r=replay(seed,target,None,128,2,'no_transfer',16,192); beam=r['beam_candidates']; assert r['round2_selected']==prior['round2']; assert len(beam)==192
   for b in beam: assert evaluate(b.expression)==b.signature and m.e023.expression_cost(b.expression)==b.cost()
   for condition,group in [('learned',manifest['source']),('random',randoms[seed,task])]:
    feasible=0; best=64; unconstrained=64; exact=0; rejected_exact=0; min_exact=None; sigs=set(); legal_sigs=set(); useful=0; beam_error=min(m.base.error(b.signature,target) for b in beam)
    for c in group:
     assert evaluate(c['expression'])==int(c['signature']); assert m.e023.expression_cost(c['expression'])==(c['primitives'],c['routing_bits'],c['depth'])
     for b in beam:
      cost=c['primitives']+b.primitives+1; legal=cost<=16; feasible+=int(legal)
      for sig in m.base.lut_outputs(int(c['signature']),b.signature):
       if sig in (int(c['signature']),b.signature): continue
       err=m.base.error(sig,target); unconstrained=min(unconstrained,err); sigs.add(sig)
       if legal: best=min(best,err); legal_sigs.add(sig); useful+=int(err<beam_error)
       if sig==target:
        min_exact=cost if min_exact is None else min(cost,min_exact); exact+=int(legal); rejected_exact+=int(not legal)
    row=dict(seed=seed,task=task,condition=condition,pairs=len(group)*len(beam),feasible_pairs=feasible,feasible_fraction=feasible/(len(group)*len(beam)),best_child_error=best,unconstrained_best_child_error=unconstrained,beam_best_error=beam_error,exact_children=exact,rejected_exact_children=rejected_exact,min_exact_child_cost=min_exact,unique_children=len(sigs),legal_unique_children=len(legal_sigs),useful_legal_children=useful,source_costs=[c['primitives'] for c in group],beam_costs=[b.primitives for b in beam]); records.append(row); f.write(json.dumps(row)+'\n'); f.flush()
   print(seed,task,flush=True)
 paths=[HERE/'main.py',HERE/'PROTOCOL.md',ROOT/'results/E049-frozen-cohort-semantics/main.py',ROOT/'results/E049-frozen-cohort-semantics/run/manifest.json',ROOT/'results/E049-frozen-cohort-semantics/run/preflight.json']
 (out/'results.json').write_text(json.dumps(dict(records=records,complete=len(records)==96,seconds=time.monotonic()-start,sources={str(x.relative_to(ROOT)):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths}),indent=2,allow_nan=False))
if __name__=='__main__': main()
