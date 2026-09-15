"""E026 counterfactual Module admission pilot."""
import hashlib,importlib.util,json,math,random,sys,time
from pathlib import Path
import numpy as np

ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit');HERE=Path(__file__).resolve().parent;OUT=HERE/'run';E019=ROOT/'results/E019-function-space-genesis';E023=ROOT/'results/E023-leave-one-task-out-transfer';E024=ROOT/'results/E024-probe-utility-diversity'
sys.path.insert(0,str(E019));import search as base;import search_v2 as features
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
e023=load('e023',E023/'main.py');e024=load('e024',E024/'main.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stable(signature,seed,round_index):
 x=(signature^(seed*0x9E3779B97F4A7C15)^(round_index*0xBF58476D1CE4E5B9))&base.MASK;x^=x>>30;x=(x*0xBF58476D1CE4E5B9)&base.MASK;x^=x>>27;x=(x*0x94D049BB133111EB)&base.MASK;return x^(x>>31)
def select(pool,target,beam_size,seed,round_index,credit,partners,last):
 values=list(pool.values());chosen={}
 def add(seq,limit=None):
  n=0
  for c in seq:
   if c.signature not in chosen:
    chosen[c.signature]=c;n+=1
    if limit is not None and n>=limit:break
 add(sorted(values,key=lambda c:(base.error(c.signature,target),*c.cost(),stable(c.signature,seed,round_index))),32)
 def score(c):return (credit.get(c.signature,0)/max(1,len(partners.get(c.signature,set()))))/(1+.35*c.primitives+.02*c.routing_bits+.25*c.depth)
 add((c for c in sorted(values,key=lambda c:(-score(c),*c.cost(),stable(c.signature,seed,round_index))) if credit.get(c.signature,0)>0 and round_index-last.get(c.signature,round_index)<=2),48)
 buckets={}
 for c in values:
  key=(features.support_mask(c.signature),c.signature.bit_count()//8);rank=(score(c),-c.primitives,-c.routing_bits,-c.depth,-stable(c.signature,seed,round_index))
  if key not in buckets or rank>buckets[key][0]:buckets[key]=(rank,c)
 add((x[1] for x in sorted(buckets.values(),key=lambda x:(-x[0][0],stable(x[1].signature,seed,round_index)))),32)
 add(sorted(values,key=lambda c:(base.error(c.signature,target),*c.cost(),stable(c.signature,seed,round_index))));add(sorted(values,key=lambda c:stable(c.signature,seed,round_index)))
 return list(chosen.values())[:beam_size]
def search(seed,target,library,beam_size,rounds,max_cost=16,save_expression=False):
 inputs,_=base.inputs_and_targets();library_sigs={c.signature for c in library};beam=[base.Candidate(s,0,0,0,('input',i)) for i,s in enumerate(inputs)]+list(library);credit={};partners={};last={};solution=None;best=64;history=[];generated=len(beam);started=time.monotonic()
 for round_index in range(1,rounds+1):
  pool={c.signature:c for c in beam};edges=[]
  for i,left in enumerate(beam):
   for right in beam[i:]:
    primitives=left.primitives+right.primitives+1
    if primitives>max_cost:continue
    routing=left.routing_bits+right.routing_bits+2*math.ceil(math.log2(6+max(1,primitives)));depth=max(left.depth,right.depth)+1
    for code,sig in enumerate(base.lut_outputs(left.signature,right.signature)):
     c=base.Candidate(sig,primitives,routing,depth,('lut',sig,code,left.expression,right.expression));old=pool.get(sig)
     if old is None:pool[sig]=c;generated+=1
     elif base.better(c,old):pool[sig]=c
     if sig not in (left.signature,right.signature):edges.append((sig,left,right))
  best=min(best,min(base.error(sig,target) for sig in pool));history.append(best)
  if target in pool:solution=pool[target];break
  top={c.signature for c in sorted(pool.values(),key=lambda c:(base.error(c.signature,target),*c.cost(),stable(c.signature,seed,round_index)))[:128]}
  for sig,left,right in edges:
   novelty=max(0,features.support_mask(sig).bit_count()-max(features.support_mask(left.signature).bit_count(),features.support_mask(right.signature).bit_count())) if 0<sig.bit_count()<64 else 0
   for parent,other in ((left,right),(right,left)):
    amount=novelty+(max(0,min(base.error(parent.signature,target),base.error(other.signature,target))-base.error(sig,target)) if sig in top else 0)
    if amount:credit[parent.signature]=credit.get(parent.signature,0)+amount;partners.setdefault(parent.signature,set()).add(other.signature);last[parent.signature]=round_index
  for sig in [s for s,v in last.items() if round_index-v>2]:credit.pop(sig,None);partners.pop(sig,None);last.pop(sig,None)
  beam=select(pool,target,beam_size,seed,round_index,credit,partners,last)
 used=[] if solution is None else sorted(e023.expression_signatures(solution.expression)&library_sigs)
 return {'exact':solution is not None,'round':None if solution is None else round_index,'best_error':best,'best_error_history':history,'uses_transfer':bool(used),'used_signatures':[str(x) for x in used],'expression':None if solution is None or not save_expression else solution.expression,'primitives':None if solution is None else solution.primitives,'routing_bits':None if solution is None else solution.routing_bits,'depth':None if solution is None else solution.depth,'generated_unique_signatures':generated,'elapsed_seconds':time.monotonic()-started}
def candidate_pool():return [x['candidate'] for x in e024.source_pool()]
def admit():
 probes,_=e024.task_signatures();pool=candidate_pool();baselines={};diagnostics=[]
 for pi,(name,target) in enumerate(probes.items()):baselines[name]=search(24600+pi,target,[],64,3)['best_error']
 for candidate in pool:
  deltas={}
  for pi,(name,target) in enumerate(probes.items()):deltas[name]=baselines[name]-search(24600+pi,target,[candidate],64,3)['best_error']
  net=sum(deltas.values());positive=sum(x>0 for x in deltas.values());structural=1+.35*candidate.primitives+.02*candidate.routing_bits+.25*candidate.depth;diagnostics.append({'candidate':candidate,'deltas':deltas,'net':net,'positive_tasks':positive,'score':net/structural})
 eligible=[x for x in diagnostics if x['net']>0 and x['positive_tasks']>=2];eligible.sort(key=lambda x:(-x['score'],-x['positive_tasks'],x['candidate'].cost(),x['candidate'].signature));selected=[x['candidate'] for x in eligible[:8]]
 manifest=[{'signature':str(x['candidate'].signature),'primitives':x['candidate'].primitives,'routing_bits':x['candidate'].routing_bits,'depth':x['candidate'].depth,'probe_deltas':x['deltas'],'net':x['net'],'positive_tasks':x['positive_tasks'],'score':x['score'],'admitted':x['candidate'] in selected,'expression':x['candidate'].expression} for x in diagnostics]
 return selected,manifest,baselines
def random_matched(templates,seed):
 inputs,old=base.inputs_and_targets();probes,evaluations=e024.task_signatures();forbidden=set(inputs)|set(old.values())|set(probes.values())|set(evaluations.values());rng=random.Random(seed+90000);out=[];used=set()
 for template in templates:
  for _ in range(10000):
   e=e023.randomize_expression(template.expression,rng,inputs);sig=e023.evaluate(e,inputs)
   if sig not in forbidden and sig not in used:assert e023.expression_cost(e)==template.cost();out.append(base.Candidate(sig,*template.cost(),e));used.add(sig);break
  else:raise RuntimeError('random match failed')
 return out
def metric(v):a=np.asarray(v,float);return {'mean':float(a.mean()),'variance':float(a.var(ddof=1))}
def main():
 OUT.mkdir(exist_ok=False);libraries,_,probes,evaluations=e024.select_libraries();legacy=libraries['probe_utility_diverse'];admitted,manifest,baselines=admit();(OUT/'admission.json').write_text(json.dumps({'baselines':baselines,'selected_signatures':[str(x.signature) for x in admitted],'candidates':manifest},indent=2));conditions=('no_transfer','legacy_all8','counterfactual','random_matched');records=[];started=time.monotonic()
 for seed in range(1360,1364):
  for ti,(task,target) in enumerate(evaluations.items()):
   for condition in conditions:
    library=[] if condition=='no_transfer' else legacy if condition=='legacy_all8' else admitted if condition=='counterfactual' else random_matched(admitted,seed*23+ti);row=search(seed,target,library,128,6,save_expression=True);row.update({'seed':seed,'task':task,'condition':condition,'library_signatures':[str(x.signature) for x in library]});records.append(row);(OUT/'progress.json').write_text(json.dumps(records,indent=2));print(seed,task,condition,int(row['exact']),row['round'],flush=True)
 aggregate={}
 for c in conditions:
  g=[r for r in records if r['condition']==c];aggregate[c]={'exact':metric([r['exact'] for r in g]),'exact_by_task':{t:sum(r['exact'] for r in g if r['task']==t) for t in evaluations},'uses_transfer':sum(r['exact'] and r['uses_transfer'] for r in g),'elapsed_seconds':metric([r['elapsed_seconds'] for r in g]),'best_error':metric([r['best_error'] for r in g])}
 result={'records':records,'aggregate':aggregate,'settings':{'seeds':list(range(1360,1364)),'tasks':list(evaluations),'conditions':list(conditions),'beam':128,'rounds':6,'max_cost':16,'diagnostic_beam':64,'diagnostic_rounds':3,'admitted_count':len(admitted)},'elapsed_seconds':time.monotonic()-started,'sources':{str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),HERE/'PROTOCOL.md',E024/'main.py',E024/'run/results.json',E023/'main.py',E019/'search.py')}};(OUT/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({'admitted':len(admitted),'aggregate':aggregate,'elapsed_seconds':result['elapsed_seconds']},indent=2))
if __name__=='__main__':main()
