"""E025 usage-gated Module eviction pilot."""
import hashlib, importlib.util, json, math, random, sys, time
from pathlib import Path
import numpy as np

ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=Path(__file__).resolve().parent; OUT=HERE/'run'
E019=ROOT/'results/E019-function-space-genesis'; E023=ROOT/'results/E023-leave-one-task-out-transfer'; E024=ROOT/'results/E024-probe-utility-diversity'
sys.path.insert(0,str(E019)); import search as base; import search_v2 as features
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
e023=load('e023',E023/'main.py');e024=load('e024',E024/'main.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def run(seed,task,target,condition,learned,beam_size=128,rounds=6,max_cost=16):
    inputs,_=base.inputs_and_targets()
    if condition=='no_transfer':library=[]
    elif condition=='random_usage_gated':library=e024.random_library(learned,seed*19+list(e024.task_signatures()[1]).index(task))
    else:library=learned
    library_signatures={c.signature for c in library}; rng=random.Random(seed);beam=[base.Candidate(s,0,0,0,('input',i)) for i,s in enumerate(inputs)]+list(library)
    credit={};partners={};last={};last_use={s:0 for s in library_signatures};ever_used=set();evicted=set();history=[];solution=None;generated=len(beam);started=time.monotonic()
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
        top={c.signature for c in sorted(pool.values(),key=lambda c:(base.error(c.signature,target),*c.cost(),c.signature))[:128]}
        for sig,left,right in edges:
            improvement=sig in top and base.error(sig,target)<min(base.error(left.signature,target),base.error(right.signature,target))
            if improvement:
                for parent in (left,right):
                    if parent.signature in library_signatures:last_use[parent.signature]=round_index;ever_used.add(parent.signature)
            novelty=max(0,features.support_mask(sig).bit_count()-max(features.support_mask(left.signature).bit_count(),features.support_mask(right.signature).bit_count())) if 0<sig.bit_count()<64 else 0
            for parent,other in ((left,right),(right,left)):
                amount=novelty+(max(0,min(base.error(parent.signature,target),base.error(other.signature,target))-base.error(sig,target)) if sig in top else 0)
                if amount:credit[parent.signature]=credit.get(parent.signature,0)+amount;partners.setdefault(parent.signature,set()).add(other.signature);last[parent.signature]=round_index
        for sig in [s for s,v in last.items() if round_index-v>2 and s not in library_signatures]:credit.pop(sig,None);partners.pop(sig,None);last.pop(sig,None)
        if condition=='fixed_protected':active=set(library_signatures)
        elif condition in ('usage_gated','random_usage_gated'):
            active={s for s in library_signatures if round_index-last_use[s]<=2};evicted|=library_signatures-active
        else:active=set()
        if target in pool:solution=pool[target];history.append({'round':round_index,'active_protected':len(active),'ever_causal_used':len(ever_used),'evicted':len(evicted),'exact':True});break
        beam=e023.select_single(pool,target,beam_size,rng,credit,partners,last,round_index);present={c.signature for c in beam};mandatory=[c for c in library if c.signature in active and c.signature not in present]
        for offset,c in enumerate(mandatory,1):beam[-offset]=c
        history.append({'round':round_index,'active_protected':len(active),'ever_causal_used':len(ever_used),'evicted':len(evicted),'exact':False})
    used=[] if solution is None else sorted(e023.expression_signatures(solution.expression)&library_signatures)
    return {'seed':seed,'task':task,'condition':condition,'exact':solution is not None,'round':None if solution is None else round_index,'uses_transfer':bool(used),'used_signatures':[str(x) for x in used],'causal_used_signatures':[str(x) for x in sorted(ever_used)],'evicted_signatures':[str(x) for x in sorted(evicted)],'active_round3':next((x['active_protected'] for x in history if x['round']==3),history[-1]['active_protected']),'final_active_protected':history[-1]['active_protected'],'history':history,'expression':None if solution is None else solution.expression,'primitives':None if solution is None else solution.primitives,'routing_bits':None if solution is None else solution.routing_bits,'depth':None if solution is None else solution.depth,'library_signatures':[str(x) for x in library_signatures],'generated_unique_signatures':generated,'elapsed_seconds':time.monotonic()-started}

def metric(v):a=np.asarray(v,float);return {'mean':float(a.mean()),'variance':float(a.var(ddof=1))}
def main():
    OUT.mkdir(exist_ok=False);libraries,manifest,probes,evaluations=e024.select_libraries();learned=libraries['probe_utility_diverse'];(OUT/'library.json').write_text(json.dumps(manifest['probe_utility_diverse'],indent=2));conditions=('no_transfer','fixed_protected','unprotected','usage_gated','random_usage_gated');records=[];started=time.monotonic()
    for seed in range(1350,1354):
        for task,target in evaluations.items():
            for condition in conditions:
                row=run(seed,task,target,condition,learned);records.append(row);(OUT/'progress.json').write_text(json.dumps(records,indent=2));print(seed,task,condition,int(row['exact']),row['round'],row['active_round3'],flush=True)
    aggregate={}
    for c in conditions:
        g=[r for r in records if r['condition']==c];aggregate[c]={'exact':metric([r['exact'] for r in g]),'exact_by_task':{t:sum(r['exact'] for r in g if r['task']==t) for t in evaluations},'uses_transfer':sum(r['exact'] and r['uses_transfer'] for r in g),'active_round3':metric([r['active_round3'] for r in g]),'final_active':metric([r['final_active_protected'] for r in g]),'causal_used':metric([len(r['causal_used_signatures']) for r in g]),'elapsed_seconds':metric([r['elapsed_seconds'] for r in g])}
    result={'records':records,'aggregate':aggregate,'settings':{'seeds':list(range(1350,1354)),'tasks':list(evaluations),'conditions':list(conditions),'beam':128,'rounds':6,'max_cost':16,'library_size':8,'probation_rounds':2},'elapsed_seconds':time.monotonic()-started,'sources':{str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),HERE/'PROTOCOL.md',E024/'main.py',E024/'run/results.json',E023/'main.py',E019/'search.py')}};(OUT/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({'aggregate':aggregate,'elapsed_seconds':result['elapsed_seconds']},indent=2))
if __name__=='__main__':main()
