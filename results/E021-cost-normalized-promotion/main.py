"""E021 cost-normalized archive promotion and retirement pilot."""
import hashlib, json, math, random, sys, time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; E019=ROOT/'results/E019-function-space-genesis'; sys.path.insert(0,str(E019))
import search as base
import search_v2 as features
OUT=HERE/'run'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def add_credit(store,tasks,partners,last,parent,other,amount,task,round_index):
    store[parent]=store.get(parent,0.)+amount
    partners.setdefault(parent,set()).add(other)
    if task is not None: tasks.setdefault(parent,set()).add(task)
    last[parent]=round_index

def select(pool,targets,condition,beam_size,rng,credit,credit_tasks,partners,last,round_index):
    values=list(pool.values()); chosen={}
    def add(seq,limit=None):
        count=0
        for c in seq:
            if c.signature not in chosen:
                chosen[c.signature]=c; count+=1
                if limit is not None and count>=limit: break
    for task in base.TASKS:
        target=targets[task]; add(sorted(values,key=lambda c:(base.error(c.signature,target),*c.cost(),c.signature)),16)
    if condition=='raw_promotion':
        ranked=sorted(values,key=lambda c:(-len(credit_tasks.get(c.signature,set())),-credit.get(c.signature,0),-len(partners.get(c.signature,set())),*c.cost(),c.signature)); add((c for c in ranked if credit.get(c.signature,0)>0),96)
    else:
        def score(c):
            sig=c.signature; reuse=1+len(credit_tasks.get(sig,set())); per_partner=credit.get(sig,0)/max(1,len(partners.get(sig,set()))); structural=1+.35*c.primitives+.02*c.routing_bits+.25*c.depth
            return reuse*per_partner/structural
        ranked=sorted(values,key=lambda c:(-score(c),*c.cost(),c.signature)); add((c for c in ranked if credit.get(c.signature,0)>0 and round_index-last.get(c.signature,round_index)<=2),64)
    buckets={}
    for c in values:
        key=(features.support_mask(c.signature),c.signature.bit_count()//8)
        if condition=='raw_promotion': rank=(len(credit_tasks.get(c.signature,set())),credit.get(c.signature,0),len(partners.get(c.signature,set())),-c.primitives,-c.routing_bits,-c.depth)
        else:
            rank=(len(credit_tasks.get(c.signature,set())),credit.get(c.signature,0)/max(1,len(partners.get(c.signature,set()))),-c.primitives,-c.routing_bits,-c.depth)
        if key not in buckets or rank>buckets[key][0]: buckets[key]=(rank,c)
    diverse=[v[1] for v in buckets.values()]; rng.shuffle(diverse); add(diverse,80 if condition=='raw_promotion' else 64)
    ranked=sorted(values,key=lambda c:(min(base.error(c.signature,t) for t in targets.values()),*c.cost(),c.signature)); add(ranked)
    remainder=values[:]; rng.shuffle(remainder); add(remainder)
    return list(chosen.values())[:beam_size]

def run(seed,condition,beam_size=256,rounds=8,max_cost=16):
    inputs,targets=base.inputs_and_targets(); rng=random.Random(seed); beam=[base.Candidate(sig,0,0,0,('input',i)) for i,sig in enumerate(inputs)]
    found={}; credit={}; credit_tasks={}; partners={}; last={}; generated=len(beam); merges=0; retired_total=0; history=[]
    for round_index in range(1,rounds+1):
        pool={c.signature:c for c in beam}; edges=[]
        for i,left in enumerate(beam):
            for right in beam[i:]:
                primitives=left.primitives+right.primitives+1
                if primitives>max_cost: continue
                routing=left.routing_bits+right.routing_bits+2*math.ceil(math.log2(6+max(1,primitives))); depth=max(left.depth,right.depth)+1
                for code,sig in enumerate(base.lut_outputs(left.signature,right.signature)):
                    candidate=base.Candidate(sig,primitives,routing,depth,('lut',sig,code,left.expression,right.expression)); old=pool.get(sig)
                    if old is None: pool[sig]=candidate; generated+=1
                    else:
                        merges+=1
                        if base.better(candidate,old): pool[sig]=candidate
                    if sig not in (left.signature,right.signature): edges.append((sig,left,right))
        top={task:{c.signature for c in sorted(pool.values(),key=lambda c:(base.error(c.signature,targets[task]),*c.cost(),c.signature))[:128]} for task in base.TASKS}
        for sig,left,right in edges:
            child_support=features.support_mask(sig).bit_count(); parent_support=max(features.support_mask(left.signature).bit_count(),features.support_mask(right.signature).bit_count()); novelty=max(0,child_support-parent_support) if 0<sig.bit_count()<64 else 0
            for parent,other in ((left,right),(right,left)):
                if novelty: add_credit(credit,credit_tasks,partners,last,parent.signature,other.signature,novelty,None,round_index)
                for task in base.TASKS:
                    if sig in top[task]:
                        gain=max(0,min(base.error(parent.signature,targets[task]),base.error(other.signature,targets[task]))-base.error(sig,targets[task]))
                        if gain: add_credit(credit,credit_tasks,partners,last,parent.signature,other.signature,gain,task,round_index)
        if condition=='normalized_retired':
            stale=[sig for sig,seen in last.items() if round_index-seen>2]
            for sig in stale:
                credit.pop(sig,None); credit_tasks.pop(sig,None); partners.pop(sig,None); last.pop(sig,None)
            retired_total+=len(stale)
        for task,target in targets.items():
            if task not in found and target in pool: found[task]={'round':round_index,'candidate':pool[target]}
        beam=select(pool,targets,condition,beam_size,rng,credit,credit_tasks,partners,last,round_index)
        missing=[item['candidate'] for task,item in found.items() if all(c.signature!=targets[task] for c in beam)]
        for offset,c in enumerate(missing,1): beam[-offset]=c
        final_promoted=sum(credit.get(c.signature,0)>0 for c in beam)
        history.append({'round':round_index,'pool':len(pool),'found':sorted(found),'credit_entries':len(credit),'final_promoted':final_promoted,'retired_total':retired_total})
        if len(found)==4: break
    solutions={task:{'round':x['round'],'signature':str(x['candidate'].signature),'primitives':x['candidate'].primitives,'routing_bits':x['candidate'].routing_bits,'depth':x['candidate'].depth,'expression':x['candidate'].expression} for task,x in found.items()}
    return {'seed':seed,'condition':condition,'exact_targets':len(found),'all_exact':len(found)==4,'solutions':solutions,'credited_signatures':len(credit),'retired_signatures':retired_total,'final_promoted':history[-1]['final_promoted'],'generated_unique_signatures':generated,'equivalent_merges':merges,'history':history}

def metric(v): a=np.asarray(v,float); return {'mean':float(a.mean()),'variance':float(a.var(ddof=1))}
def main():
    OUT.mkdir(exist_ok=False); started=time.monotonic(); records=[]
    for seed in range(1280,1284):
        for condition in ('raw_promotion','normalized_retired'):
            begin=time.monotonic(); row=run(seed,condition); row['elapsed_seconds']=time.monotonic()-begin; records.append(row); (OUT/'progress.json').write_text(json.dumps(records,indent=2)); print(seed,condition,row['exact_targets'],sorted(row['solutions']),row['final_promoted'],row['credited_signatures'],row['elapsed_seconds'],flush=True)
    aggregate={}
    for condition in ('raw_promotion','normalized_retired'):
        g=[r for r in records if r['condition']==condition]; aggregate[condition]={k:metric([r[k] for r in g]) for k in ('exact_targets','final_promoted','credited_signatures','retired_signatures','elapsed_seconds','generated_unique_signatures','equivalent_merges')}; aggregate[condition]['exact_by_task']={t:sum(t in r['solutions'] for r in g) for t in base.TASKS}
    viable=aggregate['normalized_retired']['exact_targets']['mean']>=aggregate['raw_promotion']['exact_targets']['mean']-.25 and aggregate['normalized_retired']['final_promoted']['mean']<=.7*aggregate['raw_promotion']['final_promoted']['mean'] and aggregate['normalized_retired']['elapsed_seconds']['mean']<aggregate['raw_promotion']['elapsed_seconds']['mean']
    result={'records':records,'aggregate':aggregate,'viable':viable,'elapsed_seconds':time.monotonic()-started,'settings':{'seeds':list(range(1280,1284)),'beam':256,'rounds':8,'max_cost':16,'retirement_age':2},'sources':{str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),HERE/'PROTOCOL.md',E019/'search.py',E019/'search_v2.py')}}; (OUT/'results.json').write_text(json.dumps(result,indent=2)); print(json.dumps({'aggregate':aggregate,'viable':viable,'elapsed_seconds':result['elapsed_seconds']},indent=2))
if __name__=='__main__': main()
