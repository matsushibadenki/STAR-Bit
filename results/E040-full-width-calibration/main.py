"""E040 baseline-only task calibration with full realized beam width."""
import hashlib, importlib.util, json, os, time
from pathlib import Path

ROOT = Path('/Users/littlebuddha/Desktop/alias/STAR-Bit')
HERE = ROOT / 'results/E040-full-width-calibration'
OUT = Path(os.environ.get('E040_OUT', str(HERE / 'run')))

def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
e039=load('e039_for_e040',ROOT/'results/E039-capacity-admission/main.py')
base=e039.base

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def tasks_from_grammar():
    def numbers(b): return b[0]+2*b[1], b[2]+2*b[3]
    def rotated(b): return (b[3] if b[0] else b[4]), (b[2] if b[1] else b[5])
    def nested(b):
        u=b[2] if b[0] else b[4]; v=b[5] if b[3] else b[1]
        return u if b[2] else (u != v)
    functions={
      'numeric_2bit_sum_ge3':lambda b:sum(numbers(b))>=3,
      'numeric_2bit_absdiff_ge2':lambda b:abs(numbers(b)[0]-numbers(b)[1])>=2,
      'numeric_2bit_product_ge3':lambda b:numbers(b)[0]*numbers(b)[1]>=3,
      'route_rotated_cross_xor':lambda b:rotated(b)[0] != rotated(b)[1],
      'route_rotated_cross_xnor':lambda b:rotated(b)[0] == rotated(b)[1],
      'route_nested_mux':nested,
    }
    return {name:e039.e031.signature(function) for name,function in functions.items()}

def prior_signatures():
    inputs,targets=base.inputs_and_targets(); probes,evaluations=e039.e024.task_signatures()
    return set(inputs)|set(targets.values())|set(probes.values())|set(evaluations.values())|set(e039.e031.task_signatures().values())|set(e039.e038.e037.e035.e033.tasks_from_grammar().values())|set(e039.e038.e037.e035.tasks_from_grammar()[1].values())|set(e039.tasks_from_grammar().values())

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    tasks=tasks_from_grammar(); assert len(tasks)==6 and len(set(tasks.values()))==6 and not (set(tasks.values())&prior_signatures())
    seeds=list(range(1550,1556)); budgets=[3,4,5]; beam=128; max_cost=16
    settings={'seeds':seeds,'tasks':list(tasks),'round_budgets':budgets,'beam':beam,'max_rounds':5,'max_cost':max_cost,'condition':'no_transfer'}
    (OUT/'frozen_manifest.json').write_text(json.dumps({'settings':settings,'targets':{k:str(v) for k,v in tasks.items()},'positive_class_counts':{k:v.bit_count() for k,v in tasks.items()}},indent=2,allow_nan=False))
    records=[]; started=time.monotonic()
    with (OUT/'progress.jsonl').open('w') as progress:
      for seed in seeds:
       for task,target in tasks.items():
        if sum(r['elapsed_seconds'] for r in records)>=900:
            (OUT/'incomplete.json').write_text(json.dumps({'completed':len(records),'expected':36,'search_seconds':sum(r['elapsed_seconds'] for r in records)},indent=2)); return
        row=e039.scheduled_search(seed,target,None,beam,5,'no_transfer',max_cost)
        row.update({'seed':seed,'task':task,'family':'numeric' if task.startswith('numeric_') else 'route','beam':beam,'max_rounds':5,'library_signatures':[]})
        records.append(row); progress.write(json.dumps(row,allow_nan=False)+'\n'); progress.flush()
        print(seed,task,int(row['exact']),row['round'],row['best_error'],row['round_two_input_width'],flush=True)
    assert len(records)==36
    sources=(HERE/'main.py',HERE/'PROTOCOL.md',ROOT/'results/E039-capacity-admission/main.py',ROOT/'results/E039-capacity-admission/run/results.json',ROOT/'results/E035-numeric-grammar/main.py',ROOT/'results/E033-grammar-pilot/main.py',ROOT/'results/E031-route-family-portability/main.py',ROOT/'results/E026-counterfactual-admission/main.py',ROOT/'results/E019-function-space-genesis/search.py')
    result={'records':records,'settings':settings,'elapsed_seconds':time.monotonic()-started,'search_seconds':sum(r['elapsed_seconds'] for r in records),'sources':{str(p.relative_to(ROOT)):sha(p) for p in sources}}
    (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps({'completed':36,'search_seconds':result['search_seconds']},indent=2))

if __name__=='__main__': main()
