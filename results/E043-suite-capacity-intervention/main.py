"""E043 collision-free delayed admission on frozen difficulty suites."""
import hashlib, importlib.util, json, os, time
from pathlib import Path
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E043-suite-capacity-intervention'; OUT=Path(os.environ.get('E043_OUT',str(HERE/'run')))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
e042=load('e042_for_e043',ROOT/'results/E042-difficulty-suite-calibration/main.py'); e039=e042.e039; base=e039.base
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=False); tasks=e042.tasks_from_registry(); seeds=list(range(1590,1596)); beam=128; rounds=4; max_cost=16
 conditions=['no_transfer','learned_replace','learned_add','inert_replace','inert_add','random_replace','random_add']; admitted,frozen_function=e039.e028.frozen()
 round1={}; union=set()
 for seed in seeds:
  for task,target in tasks.items():
   row=e039.scheduled_search(seed,target,None,beam,1,'no_transfer',max_cost); assert not row['exact'] and len(row['first_round_selected'])==128
   signatures={int(x) for x in row['first_round_selected']}; assert admitted.signature not in signatures; round1[seed,task]=row['first_round_selected']; union|=signatures
 inputs,old_targets=base.inputs_and_targets(); probes,evaluations=e039.e024.task_signatures()
 forbidden=set(inputs)|set(old_targets.values())|set(probes.values())|set(evaluations.values())|set(tasks.values())|union|{admitted.signature}; random_libraries={}; random_manifest=[]; used=set()
 for seed in seeds:
  for task_index,task in enumerate(tasks):
   candidate,draws=e039.e031.random_matched(admitted,seed*71+task_index,forbidden|used); assert candidate.signature not in union and candidate.cost()==admitted.cost() and candidate.signature not in used
   used.add(candidate.signature); random_libraries[seed,task]=candidate; random_manifest.append({'seed':seed,'task':task,'signature':str(candidate.signature),'expression':candidate.expression,'cost':candidate.cost(),'draws':draws})
 settings={'seeds':seeds,'tasks':list(tasks),'conditions':conditions,'beam':beam,'rounds':rounds,'max_cost':max_cost,'suite_source':'E042'}
 (OUT/'frozen_manifest.json').write_text(json.dumps({'settings':settings,'targets':{k:str(v) for k,v in tasks.items()},'admitted':frozen_function,'random_matched':random_manifest},indent=2,allow_nan=False)); (OUT/'round1_preflight.json').write_text(json.dumps([{'seed':s,'task':t,'selected':round1[s,t]} for s in seeds for t in tasks],indent=2,allow_nan=False))
 records=[]; started=time.monotonic()
 with (OUT/'progress.jsonl').open('w') as progress:
  for seed in seeds:
   for task,target in tasks.items():
    for condition in conditions:
     if sum(r['elapsed_seconds'] for r in records)>=900:
      (OUT/'incomplete.json').write_text(json.dumps({'completed':len(records),'expected':336,'search_seconds':sum(r['elapsed_seconds'] for r in records)},indent=2)); return
     module=None if condition=='no_transfer' else random_libraries[seed,task] if condition.startswith('random_') else admitted
     row=e039.scheduled_search(seed,target,module,beam,rounds,condition,max_cost); row.update({'seed':seed,'task':task,'family':'numeric' if task.startswith('numeric_') else 'route','condition':condition,'beam':beam,'round_budget':rounds,'library_signatures':[] if module is None else [str(module.signature)]})
     records.append(row); progress.write(json.dumps(row,allow_nan=False)+'\n'); progress.flush(); print(seed,task,condition,int(row['exact']),row['best_error'],flush=True)
 assert len(records)==336
 sources=(HERE/'main.py',HERE/'PROTOCOL.md',ROOT/'results/E042-difficulty-suite-calibration/main.py',ROOT/'results/E042-difficulty-suite-calibration/run/results.json',ROOT/'results/E042-difficulty-suite-calibration/run/suite_selection.json',ROOT/'results/E039-capacity-admission/main.py',ROOT/'results/E039-capacity-admission/run/results.json',ROOT/'results/E028-module-causal-ablation/main.py',ROOT/'results/E026-counterfactual-admission/run/admission.json',ROOT/'results/E019-function-space-genesis/search.py')
 result={'records':records,'settings':settings,'elapsed_seconds':time.monotonic()-started,'search_seconds':sum(r['elapsed_seconds'] for r in records),'sources':{str(p.relative_to(ROOT)):sha(p) for p in sources}}; (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps({'completed':336,'search_seconds':result['search_seconds']},indent=2))
if __name__=='__main__': main()
