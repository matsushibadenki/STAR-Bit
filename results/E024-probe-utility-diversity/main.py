"""E024 probe-utility and signature-diversity Module selection pilot."""
import hashlib, importlib.util, json, math, os, random, sys, time
from collections import defaultdict
from pathlib import Path
import numpy as np

ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit')
HERE=ROOT/'results/E024-probe-utility-diversity'
OUT=Path(os.environ.get('E024_OUT', str(HERE/'run')))
E019=ROOT/'results/E019-function-space-genesis'; E021=ROOT/'results/E021-cost-normalized-promotion'; E023=ROOT/'results/E023-leave-one-task-out-transfer'
sys.path.insert(0,str(E019)); import search as base; import search_v2 as features
spec=importlib.util.spec_from_file_location('e023',E023/'main.py'); e023=importlib.util.module_from_spec(spec); spec.loader.exec_module(e023)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def task_signatures():
    probes={}; evaluations={}
    definitions={
      'probe_majority':lambda b:sum(b)>=3,
      'probe_exactly2':lambda b:sum(b)==2,
      'probe_less3':lambda b:sum(b[i]<<i for i in range(3))<sum(b[i+3]<<i for i in range(3)),
      'probe_mix':lambda b:(b[0]&b[3])^(b[1]|b[4])^(b[2]&b[5]),
      'eval_threshold2':lambda b:sum(b)>=2,
      'eval_threshold4':lambda b:sum(b)>=4,
      'eval_equal3':lambda b:sum(b[i]<<i for i in range(3))==sum(b[i+3]<<i for i in range(3)),
      'eval_dual_mux_xor':lambda b:(b[1] if b[0] else b[2])^(b[4] if b[3] else b[5]),
    }
    for name,fn in definitions.items():
        sig=0
        for row in range(64):
            bits=[(row>>i)&1 for i in range(6)]; sig|=int(fn(bits))<<row
        (probes if name.startswith('probe_') else evaluations)[name]=sig
    return probes,evaluations

def source_pool():
    result=json.loads((E021/'run/results.json').read_text()); rows=[r for r in result['records'] if r['condition']=='normalized_retired']
    inputs,targets=base.inputs_and_targets(); forbidden=set(inputs)|set(targets.values()); occ=defaultdict(set); expr={}
    for row in rows:
        for task,sol in row['solutions'].items(): e023.walk(sol['expression'],(row['seed'],task),occ,expr)
    pool=[]
    for sig,sources in occ.items():
        if sig in forbidden: continue
        cost,expression=expr[sig]; pool.append({'candidate':base.Candidate(sig,*cost,expression),'source_count':len(sources),'source_tasks':sorted({t for _,t in sources})})
    return pool

def utility(candidate,probes,inputs):
    primitive_best={name:min(base.error(out,target) for i,a in enumerate(inputs) for b in inputs[i:] for out in base.lut_outputs(a,b)) for name,target in probes.items()}
    gains={}
    for name,target in probes.items():
        best=min(base.error(out,target) for x in inputs for out in base.lut_outputs(candidate.signature,x))
        gains[name]=max(0,primitive_best[name]-best)
    breadth=sum(v>0 for v in gains.values()); structural=1+.35*candidate.primitives+.02*candidate.routing_bits+.25*candidate.depth
    return (sum(gains.values())+2*breadth)/structural,gains

def band(p): return (1,1) if p==1 else (2,3) if p<=3 else (4,7) if p<=7 else (8,15)

def select_libraries():
    inputs,_=base.inputs_and_targets(); probes,evaluations=task_signatures(); pool=source_pool()
    for item in pool: item['utility'],item['gains']=utility(item['candidate'],probes,inputs)
    libraries={}; manifests={}
    frequency=[]; utility_only=[]; diverse=[]
    for lo,hi in ((1,1),(2,3),(4,7),(8,15)):
        group=[x for x in pool if lo<=x['candidate'].primitives<=hi]
        frequency+=sorted(group,key=lambda x:(-x['source_count'],x['candidate'].cost(),x['candidate'].signature))[:2]
        ranked=sorted(group,key=lambda x:(-x['utility'],x['candidate'].cost(),x['candidate'].signature)); utility_only+=ranked[:2]
        scores=[x['utility'] for x in group]; low=min(scores); high=max(scores)
        chosen=[]
        while len(chosen)<2:
            best=None
            for item in group:
                if item in chosen: continue
                normalized=0 if high==low else (item['utility']-low)/(high-low)
                distance=1 if not chosen else min((item['candidate'].signature^x['candidate'].signature).bit_count()/64 for x in chosen)
                key=(normalized+.5*distance,item['utility'],-item['candidate'].primitives,-item['candidate'].signature)
                if best is None or key>best[0]: best=(key,item)
            chosen.append(best[1])
        diverse+=chosen
    for name,items in [('frequency_cost',frequency),('probe_utility',utility_only),('probe_utility_diverse',diverse)]:
        libraries[name]=[x['candidate'] for x in items]
        manifests[name]=[{'signature':str(x['candidate'].signature),'primitives':x['candidate'].primitives,'routing_bits':x['candidate'].routing_bits,'depth':x['candidate'].depth,'source_count':x['source_count'],'source_tasks':x['source_tasks'],'utility':x['utility'],'probe_gains':x['gains'],'expression':x['candidate'].expression} for x in items]
    return libraries,manifests,probes,evaluations

def random_library(templates,seed):
    inputs,old_targets=base.inputs_and_targets(); probes,evaluations=task_signatures(); forbidden=set(inputs)|set(old_targets.values())|set(probes.values())|set(evaluations.values()); rng=random.Random(seed+80000); out=[]; used=set()
    for template in templates:
        for _ in range(10000):
            expression=e023.randomize_expression(template.expression,rng,inputs); sig=e023.evaluate(expression,inputs)
            if sig not in forbidden and sig not in used:
                assert e023.expression_cost(expression)==template.cost(); out.append(base.Candidate(sig,*template.cost(),expression)); used.add(sig); break
        else: raise RuntimeError('random library construction failed')
    return out

def run(seed,task,target,condition,libraries,beam_size=128,rounds=6,max_cost=16):
    inputs,_=base.inputs_and_targets()
    if condition=='no_transfer': library=[]
    elif condition=='random_matched': library=random_library(libraries['probe_utility_diverse'],seed*17+list(task_signatures()[1]).index(task))
    else: library=libraries[condition]
    protected={c.signature for c in library}; rng=random.Random(seed); beam=[base.Candidate(s,0,0,0,('input',i)) for i,s in enumerate(inputs)]+list(library); credit={};partners={};last={};generated=len(beam); solution=None; started=time.monotonic()
    for round_index in range(1,rounds+1):
        pool={c.signature:c for c in beam}; edges=[]
        for i,left in enumerate(beam):
            for right in beam[i:]:
                primitives=left.primitives+right.primitives+1
                if primitives>max_cost: continue
                routing=left.routing_bits+right.routing_bits+2*math.ceil(math.log2(6+max(1,primitives))); depth=max(left.depth,right.depth)+1
                for code,sig in enumerate(base.lut_outputs(left.signature,right.signature)):
                    c=base.Candidate(sig,primitives,routing,depth,('lut',sig,code,left.expression,right.expression)); old=pool.get(sig)
                    if old is None: pool[sig]=c;generated+=1
                    elif base.better(c,old): pool[sig]=c
                    if sig not in (left.signature,right.signature): edges.append((sig,left,right))
        top={c.signature for c in sorted(pool.values(),key=lambda c:(base.error(c.signature,target),*c.cost(),c.signature))[:128]}
        for sig,left,right in edges:
            novelty=max(0,features.support_mask(sig).bit_count()-max(features.support_mask(left.signature).bit_count(),features.support_mask(right.signature).bit_count())) if 0<sig.bit_count()<64 else 0
            for parent,other in ((left,right),(right,left)):
                amount=novelty+(max(0,min(base.error(parent.signature,target),base.error(other.signature,target))-base.error(sig,target)) if sig in top else 0)
                if amount: credit[parent.signature]=credit.get(parent.signature,0)+amount;partners.setdefault(parent.signature,set()).add(other.signature);last[parent.signature]=round_index
        for sig in [s for s,v in last.items() if round_index-v>2 and s not in protected]: credit.pop(sig,None);partners.pop(sig,None);last.pop(sig,None)
        if target in pool: solution=pool[target];break
        beam=e023.select_single(pool,target,beam_size,rng,credit,partners,last,round_index); present={c.signature for c in beam}; missing=[c for c in library if c.signature not in present]
        for offset,c in enumerate(missing,1): beam[-offset]=c
    used=[] if solution is None else sorted(e023.expression_signatures(solution.expression)&protected)
    return {'seed':seed,'task':task,'condition':condition,'exact':solution is not None,'round':None if solution is None else round_index,'uses_transfer':bool(used),'used_signatures':[str(x) for x in used],'primitives':None if solution is None else solution.primitives,'routing_bits':None if solution is None else solution.routing_bits,'depth':None if solution is None else solution.depth,'expression':None if solution is None else solution.expression,'library_signatures':[str(c.signature) for c in library],'generated_unique_signatures':generated,'elapsed_seconds':time.monotonic()-started}

def metric(v): a=np.asarray(v,float);return {'mean':float(a.mean()),'variance':float(a.var(ddof=1))}
def main():
    OUT.mkdir(parents=True,exist_ok=False); libraries,manifests,probes,evaluations=select_libraries(); (OUT/'libraries.json').write_text(json.dumps(manifests,indent=2)); records=[]; started=time.monotonic(); conditions=('no_transfer','frequency_cost','probe_utility','probe_utility_diverse','random_matched')
    for seed in range(1340,1344):
        for task,target in evaluations.items():
            for condition in conditions:
                row=run(seed,task,target,condition,libraries);records.append(row);(OUT/'progress.json').write_text(json.dumps(records,indent=2));print(seed,task,condition,int(row['exact']),row['round'],flush=True)
    aggregate={}
    for c in conditions:
        g=[r for r in records if r['condition']==c];aggregate[c]={'exact':metric([r['exact'] for r in g]),'elapsed_seconds':metric([r['elapsed_seconds'] for r in g]),'exact_by_task':{t:sum(r['exact'] for r in g if r['task']==t) for t in evaluations},'uses_transfer':sum(r['exact'] and r['uses_transfer'] for r in g)}
    result={'records':records,'aggregate':aggregate,'settings':{'seeds':list(range(1340,1344)),'beam':128,'rounds':6,'max_cost':16,'library_size':8,'probe_tasks':list(probes),'evaluation_tasks':list(evaluations)},'elapsed_seconds':time.monotonic()-started,'sources':{str(p.relative_to(ROOT)):sha(p) for p in (HERE/'main.py',HERE/'PROTOCOL.md',E021/'run/results.json',E023/'main.py',E019/'search.py')}};(OUT/'results.json').write_text(json.dumps(result,indent=2));print(json.dumps({'aggregate':aggregate,'elapsed_seconds':result['elapsed_seconds']},indent=2))
if __name__=='__main__':main()
