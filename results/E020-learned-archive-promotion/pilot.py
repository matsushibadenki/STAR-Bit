"""E020 learned offspring-credit archive promotion pilot."""
import hashlib, json, math, random, sys, time
from pathlib import Path
import numpy as np

ROOT = Path('/Users/littlebuddha/Desktop/alias/STAR-Bit')
E019 = ROOT / 'results/E019-function-space-genesis'
sys.path.insert(0, str(E019))
import search as base
import search_v2 as features

HERE = Path(__file__).resolve().parent
OUT = HERE / 'run'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def select(pool, targets, condition, beam_size, rng, credits, credit_tasks, partners):
    values=list(pool.values()); chosen={}
    def add(seq, limit=None):
        count=0
        for c in seq:
            if c.signature not in chosen:
                chosen[c.signature]=c; count+=1
                if limit is not None and count>=limit: break
    for task in base.TASKS:
        target=targets[task]
        add(sorted(values,key=lambda c:(base.error(c.signature,target),*c.cost(),c.signature)),16)
    if condition=='offspring_promotion':
        ranked=sorted(values,key=lambda c:(-len(credit_tasks.get(c.signature,set())),-credits.get(c.signature,0),-len(partners.get(c.signature,set())),*c.cost(),c.signature))
        add((c for c in ranked if credits.get(c.signature,0)>0),96)
        buckets={}
        for c in values:
            key=(features.support_mask(c.signature),c.signature.bit_count()//8)
            score=(len(credit_tasks.get(c.signature,set())),credits.get(c.signature,0),len(partners.get(c.signature,set())),-c.primitives,-c.routing_bits,-c.depth)
            if key not in buckets or score>buckets[key][0]: buckets[key]=(score,c)
        diverse=[item[1] for item in buckets.values()]; rng.shuffle(diverse); add(diverse,80)
    else:
        add(sorted(values,key=lambda c:(min(base.error(c.signature,t) for t in targets.values()),*c.cost(),c.signature)))
    remainder=values[:]; rng.shuffle(remainder); add(remainder)
    return list(chosen.values())[:beam_size]

def run(seed,condition,beam_size=256,rounds=8,max_cost=16):
    inputs,targets=base.inputs_and_targets(); rng=random.Random(seed)
    beam=[base.Candidate(sig,0,0,0,('input',i)) for i,sig in enumerate(inputs)]
    found={}; credits={}; credit_tasks={}; partners={}; generated=len(beam); merges=0; history=[]
    for round_index in range(1,rounds+1):
        pool={c.signature:c for c in beam}; generated_edges=[]
        for i,left in enumerate(beam):
            for right in beam[i:]:
                primitives=left.primitives+right.primitives+1
                if primitives>max_cost: continue
                routing=left.routing_bits+right.routing_bits+2*math.ceil(math.log2(6+max(1,primitives)))
                depth=max(left.depth,right.depth)+1
                for code,sig in enumerate(base.lut_outputs(left.signature,right.signature)):
                    candidate=base.Candidate(sig,primitives,routing,depth,('lut',sig,code,left.expression,right.expression))
                    old=pool.get(sig)
                    if old is None: pool[sig]=candidate; generated+=1
                    else:
                        merges+=1
                        if base.better(candidate,old): pool[sig]=candidate
                    if condition=='offspring_promotion' and sig not in (left.signature,right.signature):
                        generated_edges.append((sig,left,right))
        if condition=='offspring_promotion':
            top_by_task={}
            for task in base.TASKS:
                target=targets[task]
                top_by_task[task]={c.signature for c in sorted(pool.values(),key=lambda c:(base.error(c.signature,target),*c.cost(),c.signature))[:128]}
            for sig,left,right in generated_edges:
                child=pool[sig]
                child_support=features.support_mask(sig).bit_count()
                parent_support=max(features.support_mask(left.signature).bit_count(),features.support_mask(right.signature).bit_count())
                novelty=max(0,child_support-parent_support) if 0<sig.bit_count()<64 else 0
                for parent,other in ((left,right),(right,left)):
                    partners.setdefault(parent.signature,set()).add(other.signature)
                    if novelty:
                        credits[parent.signature]=credits.get(parent.signature,0)+novelty
                    for task in base.TASKS:
                        if sig in top_by_task[task]:
                            target=targets[task]
                            gain=max(0,min(base.error(parent.signature,target),base.error(other.signature,target))-base.error(sig,target))
                            if gain:
                                credits[parent.signature]=credits.get(parent.signature,0)+gain
                                credit_tasks.setdefault(parent.signature,set()).add(task)
        for task,target in targets.items():
            if task not in found and target in pool: found[task]={'round':round_index,'candidate':pool[target]}
        beam=select(pool,targets,condition,beam_size,rng,credits,credit_tasks,partners)
        missing=[item['candidate'] for task,item in found.items() if all(c.signature!=targets[task] for c in beam)]
        for offset,c in enumerate(missing,1): beam[-offset]=c
        promoted=sum(credits.get(c.signature,0)>0 for c in beam)
        history.append({'round':round_index,'pool':len(pool),'beam':len(beam),'found':sorted(found),'promoted':promoted})
        if len(found)==4: break
    solutions={task:{'round':item['round'],'primitives':item['candidate'].primitives,'routing_bits':item['candidate'].routing_bits,'depth':item['candidate'].depth,'signature':str(item['candidate'].signature),'expression':item['candidate'].expression} for task,item in found.items()}
    top_promoted=sorted(({'signature':str(sig),'credit':credit,'reuse_tasks':sorted(credit_tasks.get(sig,set())),'partners':len(partners.get(sig,set())),'cost':pool[sig].cost() if sig in pool else None} for sig,credit in credits.items()),key=lambda x:(-len(x['reuse_tasks']),-x['credit'],-x['partners'],x['signature']))[:32]
    return {'seed':seed,'condition':condition,'exact_targets':len(found),'all_exact':len(found)==4,'solutions':solutions,'generated_unique_signatures':generated,'equivalent_merges':merges,'promoted_signatures':len(credits),'top_promoted':top_promoted,'history':history}

def metric(v):
    a=np.asarray(v,float); return {'mean':float(a.mean()),'variance':float(a.var(ddof=1))}

def main():
    OUT.mkdir(exist_ok=False); started=time.monotonic(); records=[]
    for seed in range(1260,1264):
        for condition in ('target_greedy','offspring_promotion'):
            begin=time.monotonic(); row=run(seed,condition); row['elapsed_seconds']=time.monotonic()-begin; records.append(row)
            (OUT/'progress.json').write_text(json.dumps(records,indent=2)); print(seed,condition,row['exact_targets'],sorted(row['solutions']),row['elapsed_seconds'],flush=True)
    aggregate={}
    for condition in ('target_greedy','offspring_promotion'):
        group=[r for r in records if r['condition']==condition]
        aggregate[condition]={'exact_targets':metric([r['exact_targets'] for r in group]),'all_exact_seeds':sum(r['all_exact'] for r in group),'exact_by_task':{t:sum(t in r['solutions'] for r in group) for t in base.TASKS},'seconds':metric([r['elapsed_seconds'] for r in group]),'unique_signatures':metric([r['generated_unique_signatures'] for r in group]),'equivalent_merges':metric([r['equivalent_merges'] for r in group])}
    viable=aggregate['offspring_promotion']['all_exact_seeds']>=3 and aggregate['offspring_promotion']['exact_targets']['mean']>aggregate['target_greedy']['exact_targets']['mean']
    result={'records':records,'aggregate':aggregate,'viable':viable,'elapsed_seconds':time.monotonic()-started,'settings':{'seeds':list(range(1260,1264)),'beam':256,'rounds':8,'max_cost':16},'sources':{str(p):sha(p) for p in (Path(__file__),HERE/'PROTOCOL.md',E019/'search.py',E019/'search_v2.py')}}
    (OUT/'results.json').write_text(json.dumps(result,indent=2)); print(json.dumps({'aggregate':aggregate,'viable':viable,'elapsed_seconds':result['elapsed_seconds']},indent=2))
if __name__=='__main__': main()
