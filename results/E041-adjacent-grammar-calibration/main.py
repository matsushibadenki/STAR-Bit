"""E041 adjacent-grammar baseline calibration."""
import hashlib, importlib.util, json, os, time
from pathlib import Path
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E041-adjacent-grammar-calibration'; OUT=Path(os.environ.get('E041_OUT',str(HERE/'run')))
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
e040=load('e040_for_e041',ROOT/'results/E040-full-width-calibration/main.py'); e039=e040.e039; base=e040.base
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def tasks_from_grammar():
 def mux(b): return b[1] if b[0] else b[2]
 def conditional(b):
  u=mux(b); return (u != b[5]) if b[4] else u
 functions={
  'numeric_5bit_weighted_ge4':lambda b:sum(x*w for x,w in zip(b[:5],(1,2,1,2,1)))>=4,
  'numeric_5bit_weighted_ge5':lambda b:sum(x*w for x,w in zip(b[:5],(1,2,1,2,1)))>=5,
  'numeric_4bit_weighted_ge4':lambda b:sum(x*w for x,w in zip(b[:4],(1,2,2,3)))>=4,
  'route_mux_xor_bit':lambda b:mux(b)!=b[3],
  'route_mux_xnor_bit':lambda b:mux(b)==b[3],
  'route_mux_conditional_flip':conditional,
 }
 return {name:e039.e031.signature(function) for name,function in functions.items()}
def prior_signatures(): return e040.prior_signatures()|set(e040.tasks_from_grammar().values())
def main():
 OUT.mkdir(parents=True,exist_ok=False); tasks=tasks_from_grammar(); assert len(tasks)==6 and len(set(tasks.values()))==6 and not(set(tasks.values())&prior_signatures())
 seeds=list(range(1560,1566)); budgets=[2,3,4]; beam=128; max_cost=16; settings={'seeds':seeds,'tasks':list(tasks),'round_budgets':budgets,'beam':beam,'max_rounds':4,'max_cost':max_cost,'condition':'no_transfer'}
 (OUT/'frozen_manifest.json').write_text(json.dumps({'settings':settings,'targets':{k:str(v) for k,v in tasks.items()},'positive_class_counts':{k:v.bit_count() for k,v in tasks.items()}},indent=2,allow_nan=False))
 records=[]; started=time.monotonic()
 with (OUT/'progress.jsonl').open('w') as progress:
  for seed in seeds:
   for task,target in tasks.items():
    if sum(r['elapsed_seconds'] for r in records)>=900:
     (OUT/'incomplete.json').write_text(json.dumps({'completed':len(records),'expected':36,'search_seconds':sum(r['elapsed_seconds'] for r in records)},indent=2)); return
    row=e039.scheduled_search(seed,target,None,beam,4,'no_transfer',max_cost); row.update({'seed':seed,'task':task,'family':'numeric' if task.startswith('numeric_') else 'route','beam':beam,'max_rounds':4,'library_signatures':[]})
    records.append(row); progress.write(json.dumps(row,allow_nan=False)+'\n'); progress.flush(); print(seed,task,int(row['exact']),row['round'],row['best_error'],row['round_two_input_width'],flush=True)
 assert len(records)==36
 sources=(HERE/'main.py',HERE/'PROTOCOL.md',ROOT/'results/E040-full-width-calibration/main.py',ROOT/'results/E040-full-width-calibration/run/results.json',ROOT/'results/E039-capacity-admission/main.py',ROOT/'results/E035-numeric-grammar/main.py',ROOT/'results/E033-grammar-pilot/main.py',ROOT/'results/E026-counterfactual-admission/main.py',ROOT/'results/E019-function-space-genesis/search.py')
 result={'records':records,'settings':settings,'elapsed_seconds':time.monotonic()-started,'search_seconds':sum(r['elapsed_seconds'] for r in records),'sources':{str(p.relative_to(ROOT)):sha(p) for p in sources}}; (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps({'completed':36,'search_seconds':result['search_seconds']},indent=2))
if __name__=='__main__': main()
