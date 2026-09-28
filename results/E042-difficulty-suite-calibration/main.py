"""E042 independent baseline calibration of a frozen mixed-difficulty suite."""
import hashlib, importlib.util, json, os, time
from pathlib import Path
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E042-difficulty-suite-calibration'; OUT=Path(os.environ.get('E042_OUT',str(HERE/'run')))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
e041=load('e041_for_e042',ROOT/'results/E041-adjacent-grammar-calibration/main.py'); e040=e041.e040; e039=e041.e039
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def tasks_from_registry():
 a=e039.tasks_from_grammar(); b=e040.tasks_from_grammar(); c=e041.tasks_from_grammar()
 names=('numeric_2bit_sum_ge3','numeric_4bit_weighted_ge4','numeric_rotated_weight_ge6','numeric_5bit_weighted_ge5','route_mux_xor_bit','route_mux_conditional_flip','route_rotated_cross_xnor','route_nested_mux')
 merged={**a,**b,**c}; tasks={name:merged[name] for name in names}; assert len(tasks)==8 and len(set(tasks.values()))==8; return tasks
def main():
 OUT.mkdir(parents=True,exist_ok=False); tasks=tasks_from_registry(); seeds=list(range(1570,1582)); beam=128; rounds=4; max_cost=16
 strata={'numeric':{'easy':['numeric_2bit_sum_ge3','numeric_4bit_weighted_ge4'],'hard':['numeric_rotated_weight_ge6','numeric_5bit_weighted_ge5']},'route':{'easy':['route_mux_xor_bit','route_mux_conditional_flip'],'hard':['route_rotated_cross_xnor','route_nested_mux']}}
 assert [x for family in ('numeric','route') for level in ('easy','hard') for x in strata[family][level]]==list(tasks)
 settings={'seeds':seeds,'tasks':list(tasks),'beam':beam,'rounds':rounds,'max_cost':max_cost,'condition':'no_transfer','strata':strata}
 (OUT/'frozen_manifest.json').write_text(json.dumps({'settings':settings,'targets':{k:str(v) for k,v in tasks.items()},'positive_class_counts':{k:v.bit_count() for k,v in tasks.items()}},indent=2,allow_nan=False))
 records=[]; started=time.monotonic()
 with (OUT/'progress.jsonl').open('w') as progress:
  for seed in seeds:
   for task,target in tasks.items():
    if sum(r['elapsed_seconds'] for r in records)>=900:
     (OUT/'incomplete.json').write_text(json.dumps({'completed':len(records),'expected':96,'search_seconds':sum(r['elapsed_seconds'] for r in records)},indent=2)); return
    row=e039.scheduled_search(seed,target,None,beam,rounds,'no_transfer',max_cost); row.update({'seed':seed,'task':task,'family':'numeric' if task.startswith('numeric_') else 'route','beam':beam,'round_budget':rounds,'library_signatures':[]})
    records.append(row); progress.write(json.dumps(row,allow_nan=False)+'\n'); progress.flush(); print(seed,task,int(row['exact']),row['round'],row['best_error'],row['round_two_input_width'],flush=True)
 assert len(records)==96
 sources=(HERE/'main.py',HERE/'PROTOCOL.md',ROOT/'results/E041-adjacent-grammar-calibration/main.py',ROOT/'results/E041-adjacent-grammar-calibration/run/results.json',ROOT/'results/E040-full-width-calibration/main.py',ROOT/'results/E040-full-width-calibration/run/results.json',ROOT/'results/E039-capacity-admission/main.py',ROOT/'results/E039-capacity-admission/run/results.json',ROOT/'results/E026-counterfactual-admission/main.py',ROOT/'results/E019-function-space-genesis/search.py')
 result={'records':records,'settings':settings,'elapsed_seconds':time.monotonic()-started,'search_seconds':sum(r['elapsed_seconds'] for r in records),'sources':{str(p.relative_to(ROOT)):sha(p) for p in sources}}; (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps({'completed':96,'search_seconds':result['search_seconds']},indent=2))
if __name__=='__main__': main()
