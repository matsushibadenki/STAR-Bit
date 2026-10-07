import hashlib,importlib.util,inspect,json,time
from pathlib import Path
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E051-pruning-provenance-diagnostic'
spec=importlib.util.spec_from_file_location('e049',ROOT/'results/E049-frozen-cohort-semantics/main.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
src=inspect.getsource(m.scheduled_search)
src=src.replace('    solution = None','    snapshots = {}\n    solution = None')
src=src.replace('        if target in pool:', "        if round_index == 3:\n            snapshots['pool'] = dict(pool)\n        if target in pool:")
src=src.replace('        if round_index == 2:\n            round2_selected', "        if round_index == 3:\n            snapshots['selected'] = list(beam)\n        if round_index == 2:\n            round2_selected")
src=src.replace("return {'round2_selected':", "return {'snapshots': snapshots, 'beam_candidates': beam, 'round2_selected':")
ns=dict(m.__dict__); exec(compile(src,str(HERE/'main.py')+':instrumented','exec'),ns); search=ns['scheduled_search']
def main():
 out=HERE/'run'; out.mkdir(); old=ROOT/'results/E049-frozen-cohort-semantics/run'; manifest=json.loads((old/'manifest.json').read_text()); pre=json.loads((old/'preflight.json').read_text()); randoms={(x['seed'],x['task']):x['cohort'] for x in manifest['random']}; originals={(x['seed'],x['task'],x['condition']):x for x in json.loads((old/'results.json').read_text())['records']}; targets=m.e042.tasks_from_registry(); rows=[]; start=time.monotonic(); inputs,_=m.base.inputs_and_targets()
 def evaluate(e):
  if e[0]=='input': return inputs[e[1]]
  s=m.base.lut_outputs(evaluate(e[3]),evaluate(e[4]))[e[2]]; assert s==int(e[1]); return s
 def uses(c,library): return bool(m.e023.expression_signatures(c.expression)&library)
 with (out/'progress.jsonl').open('w') as f:
  for prior in pre:
   if time.monotonic()-start>900: break
   seed,task=prior['seed'],prior['task']; target=targets[task]; replay=search(seed,target,None,128,2,'no_transfer',16,192); beam=replay['beam_candidates']; assert replay['round2_selected']==prior['round2']; beamerr=min(m.base.error(c.signature,target) for c in beam)
   for condition,group in [('learned',manifest['source']),('random',randoms[seed,task])]:
    cohort=[m.base.Candidate(int(c['signature']),c['primitives'],c['routing_bits'],c['depth'],c['expression']) for c in group]; library={c.signature for c in cohort}; children=set()
    for c in cohort:
     for b in beam:
      if c.primitives+b.primitives+1>16: continue
      children.update(s for s in m.base.lut_outputs(c.signature,b.signature) if s not in (c.signature,b.signature))
    useful={s for s in children if m.base.error(s,target)<beamerr}; r=search(seed,target,None,128,4,'no_transfer',16,192,cohort); original=originals[seed,task,condition]
    for key in ['exact','round','best_error','uses_transfer','expression','primitives','routing_bits','depth','first_round_selected','round2_selected','input_width_history']:
     assert json.loads(json.dumps(r[key]))==original[key],key
    snapshot=r['snapshots']; pool=snapshot['pool']; selected=snapshot.get('selected'); selected_sigs=set() if selected is None else {c.signature for c in selected}; canonical={s for s in children if s in pool and uses(pool[s],library)}
    if selected is not None:
     for c in selected: assert evaluate(c.expression)==c.signature and m.e023.expression_cost(c.expression)==c.cost()
    row=dict(seed=seed,task=task,condition=condition,terminal_round3=selected is None,child_signatures=len(children),useful_signatures=len(useful),canonical_child_provenance=len(canonical),canonical_useful_provenance=len(canonical&useful),selected_child_signatures=None if selected is None else len(selected_sigs&children),selected_useful_signatures=None if selected is None else len(selected_sigs&useful),selected_useful_provenance=None if selected is None else len(selected_sigs&useful&canonical),selected_all_provenance=None if selected is None else sum(uses(c,library) for c in selected),selected_candidates=None if selected is None else [dict(signature=str(c.signature),primitives=c.primitives,routing_bits=c.routing_bits,depth=c.depth,expression=c.expression) for c in selected],exact=r['exact'],solution_round=r['round'],uses_transfer=r['uses_transfer']); assert children<=set(pool); rows.append(row); f.write(json.dumps(row)+'\n'); f.flush()
   print(seed,task,flush=True)
 paths=[HERE/'main.py',HERE/'PROTOCOL.md',ROOT/'results/E049-frozen-cohort-semantics/main.py',old/'manifest.json',old/'preflight.json',old/'results.json']; (out/'results.json').write_text(json.dumps(dict(records=rows,complete=len(rows)==96,seconds=time.monotonic()-start,sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}),indent=2,allow_nan=False))
if __name__=='__main__': main()
