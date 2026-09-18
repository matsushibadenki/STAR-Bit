"""E027 independent confirmation of counterfactual Module admission."""
import hashlib,importlib.util,json,os,sys,time
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit');HERE=ROOT/'results/E027-counterfactual-admission-confirmation';OUT=Path(os.environ.get('E027_OUT',str(HERE/'run')));E019=ROOT/'results/E019-function-space-genesis';E024=ROOT/'results/E024-probe-utility-diversity';E026=ROOT/'results/E026-counterfactual-admission'
sys.path.insert(0,str(E019));import search as base
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
e024=load('e024',E024/'main.py');e026=load('e026',E026/'main.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metric(v):a=np.asarray(v,float);return {'mean':float(a.mean()),'variance':float(a.var(ddof=1))}
def admitted():
 data=json.loads((E026/'run/admission.json').read_text());assert len(data['selected_signatures'])==1;row=next(x for x in data['candidates'] if x['admitted']);e=row['expression'];candidate=base.Candidate(int(row['signature']),row['primitives'],row['routing_bits'],row['depth'],e);return [candidate],row
def main():
 OUT.mkdir(parents=True,exist_ok=False);selected,manifest=admitted();libraries,_,_,evaluations=e024.select_libraries();legacy=libraries['probe_utility_diverse'];(OUT/'frozen_admission.json').write_text(json.dumps(manifest,indent=2));conditions=('no_transfer','legacy_all8','counterfactual','random_matched');records=[];started=time.monotonic()
 for seed in range(1370,1386):
  for ti,(task,target) in enumerate(evaluations.items()):
   for condition in conditions:
    library=[] if condition=='no_transfer' else legacy if condition=='legacy_all8' else selected if condition=='counterfactual' else e026.random_matched(selected,seed*29+ti);row=e026.search(seed,target,library,128,6,save_expression=True);row.update({'seed':seed,'task':task,'condition':condition,'library_signatures':[str(x.signature) for x in library]});records.append(row);(OUT/'progress.json').write_text(json.dumps(records,indent=2));print(seed,task,condition,int(row['exact']),row['round'],flush=True)
 aggregate={}
 for c in conditions:
  g=[r for r in records if r['condition']==c];aggregate[c]={'exact':metric([r['exact'] for r in g]),'exact_by_task':{t:sum(r['exact'] for r in g if r['task']==t) for t in evaluations},'uses_transfer':sum(r['exact'] and r['uses_transfer'] for r in g),'elapsed_seconds':metric([r['elapsed_seconds'] for r in g]),'best_error':metric([r['best_error'] for r in g]),'primitives':metric([r['primitives'] for r in g if r['primitives'] is not None])}
 result={'records':records,'aggregate':aggregate,'settings':{'seeds':list(range(1370,1386)),'tasks':list(evaluations),'conditions':list(conditions),'beam':128,'rounds':6,'max_cost':16,'admitted_count':1},'elapsed_seconds':time.monotonic()-started,'sources':{str(p.relative_to(ROOT)):sha(p) for p in (HERE/'main.py',HERE/'PROTOCOL.md',E026/'main.py',E026/'run/admission.json',E026/'run/results.json',E024/'main.py',E019/'search.py')}};(OUT/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({'aggregate':aggregate,'elapsed_seconds':result['elapsed_seconds']},indent=2))
if __name__=='__main__':main()
