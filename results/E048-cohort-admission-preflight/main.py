import hashlib,importlib.util,json,time
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E048-cohort-admission-preflight'; OUT=HERE/'run'
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
m=load('e047_for_e048',ROOT/'results/E047-later-capacity-confirmation/main.py'); lib=load('e022_for_e048',ROOT/'results/E022-fixed-function-transfer/main.py'); e031=m.old.e031
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(exist_ok=False); tasks=m.e042.tasks_from_registry(); seeds=list(range(1650,1656)); learned,manifest=lib.source_library(); cohort=[c for c in learned if c.primitives>=4]; assert len(cohort)==8
 records=[]; union=set(); started=time.monotonic()
 with (OUT/'progress.jsonl').open('w') as f:
  for seed in seeds:
   for task,target in tasks.items():
    if sum(x['elapsed_seconds'] for x in records)>=900:
     (OUT/'incomplete.json').write_text(json.dumps({'completed':len(records)})); return
    row=m.scheduled_search(seed,target,None,128,2,'no_transfer',16,192); assert not row['exact']
    # scheduled_search exposes only round1 selection; capture round2 deterministically with a select wrapper.
    original=m.e026.select; selected=[]
    def capture(*args):
     beam=original(*args); selected.append([str(c.signature) for c in beam]); return beam
    m.e026.select=capture
    try: replay=m.scheduled_search(seed,target,None,128,2,'no_transfer',16,192)
    finally: m.e026.select=original
    assert replay['best_error']==row['best_error'] and len(selected)==2 and len(selected[1])==192
    row['elapsed_seconds']+=replay['elapsed_seconds']; beam=set(map(int,selected[1])); union|=beam; available=[str(c.signature) for c in cohort if c.signature not in beam and c.signature!=target]
    record={'seed':seed,'task':task,'round2_selected':selected[1],'available':available,'elapsed_seconds':row['elapsed_seconds']}; records.append(record); f.write(json.dumps(record)+'\n'); f.flush()
 eligible=[c for c in cohort if c.signature not in union and c.signature not in set(tasks.values())]; inputs,targets=m.base.inputs_and_targets(); forbidden=union|set(tasks.values())|set(inputs)|set(targets.values())|{c.signature for c in learned}; randoms=[]; used=set()
 for seed in seeds:
  for ti,task in enumerate(tasks):
   matched=[]
   for j,c in enumerate(eligible):
    candidate,draws=e031.random_matched(c,seed*1009+ti*31+j,forbidden|used); used.add(candidate.signature); matched.append({'template':str(c.signature),'signature':str(candidate.signature),'cost':candidate.cost(),'expression':candidate.expression,'draws':draws})
   randoms.append({'seed':seed,'task':task,'cohort':matched})
 sources=[HERE/'main.py',HERE/'PROTOCOL.md',ROOT/'results/E047-later-capacity-confirmation/main.py',ROOT/'results/E022-fixed-function-transfer/main.py',ROOT/'results/E021-cost-normalized-promotion/run/results.json',ROOT/'results/E031-route-family-portability/main.py']
 result={'records':records,'settings':{'seeds':seeds,'tasks':list(tasks),'initial':128,'later':192,'rounds':2},'source_cohort':[x for x in manifest if int(x['signature']) in {c.signature for c in cohort}],'admitted':[str(c.signature) for c in eligible],'random_controls':randoms,'search_seconds':sum(x['elapsed_seconds'] for x in records),'sources':{str(p.relative_to(ROOT)):sha(p) for p in sources}}
 (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)); print(json.dumps({'admitted':len(eligible),'completed':len(records),'search_seconds':result['search_seconds']}))
if __name__=='__main__': main()
