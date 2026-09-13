"""E021 cost-normalized offspring credit with age-based retirement."""
import hashlib, json, math, random, sys, time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
E019 = ROOT / "results/E019-function-space-genesis"
sys.path.insert(0, str(E019))
import search as base
import search_v2 as features

HERE = Path(__file__).resolve().parent
OUT = HERE / "run"

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def add_unique(chosen, sequence, limit=None):
    count = 0
    for candidate in sequence:
        if candidate.signature not in chosen:
            chosen[candidate.signature] = candidate
            count += 1
            if limit is not None and count >= limit:
                break

def select(pool, targets, condition, beam_size, rng, credit, tasks, partners, last_round, round_index):
    values = list(pool.values()); chosen = {}
    for task in base.TASKS:
        target = targets[task]
        add_unique(chosen, sorted(values, key=lambda c:(base.error(c.signature,target), *c.cost(), c.signature)), 16)
    if condition == "raw_promotion":
        ranked = sorted(values, key=lambda c:(-len(tasks.get(c.signature,set())), -credit.get(c.signature,0), -len(partners.get(c.signature,set())), *c.cost(), c.signature))
        eligible = [c for c in ranked if credit.get(c.signature,0) > 0]
        add_unique(chosen, eligible, 96)
        diversity_limit = 80
    else:
        def eligible(c): return credit.get(c.signature,0) > 0 and (round_index-last_round.get(c.signature,-99) <= 2 or len(tasks.get(c.signature,set())) >= 2)
        ranked = sorted((c for c in values if eligible(c)), key=lambda c:(-len(tasks.get(c.signature,set())), -credit.get(c.signature,0), -len(partners.get(c.signature,set())), *c.cost(), c.signature))
        eligible = ranked
        add_unique(chosen, ranked, 80)
        diversity_limit = 64
    buckets = {}
    for candidate in values:
        key = (features.support_mask(candidate.signature), candidate.signature.bit_count() // 8)
        score = (len(tasks.get(candidate.signature,set())), credit.get(candidate.signature,0), len(partners.get(candidate.signature,set())), -candidate.primitives, -candidate.routing_bits, -candidate.depth)
        if key not in buckets or score > buckets[key][0]: buckets[key] = (score, candidate)
    diverse = [item[1] for item in buckets.values()]; rng.shuffle(diverse)
    add_unique(chosen, diverse, diversity_limit)
    remainder = values[:]; rng.shuffle(remainder); add_unique(chosen, remainder)
    return list(chosen.values())[:beam_size], len(eligible)

def run(seed, condition, beam_size=256, rounds=8, max_cost=16):
    inputs, targets = base.inputs_and_targets(); rng = random.Random(seed)
    beam = [base.Candidate(sig,0,0,0,("input",i)) for i,sig in enumerate(inputs)]
    found={}; credit={}; tasks={}; partners={}; last_round={}; generated=len(beam); merges=0; history=[]; retired=set()
    for round_index in range(1, rounds+1):
        if condition == "normalized_retirement":
            credit = {sig:value*.5 for sig,value in credit.items() if value*.5 >= 1e-9}
        pool={c.signature:c for c in beam}; generated_edges=[]; best_parents={}
        for i,left in enumerate(beam):
            for right in beam[i:]:
                primitives=left.primitives+right.primitives+1
                if primitives>max_cost: continue
                routing=left.routing_bits+right.routing_bits+2*math.ceil(math.log2(6+max(1,primitives)))
                depth=max(left.depth,right.depth)+1
                for code,sig in enumerate(base.lut_outputs(left.signature,right.signature)):
                    candidate=base.Candidate(sig,primitives,routing,depth,("lut",sig,code,left.expression,right.expression))
                    old=pool.get(sig)
                    if old is None:
                        pool[sig]=candidate; generated+=1; best_parents[sig]=(left,right)
                    else:
                        merges+=1
                        if base.better(candidate,old): pool[sig]=candidate; best_parents[sig]=(left,right)
                    if condition=="raw_promotion" and sig not in (left.signature,right.signature): generated_edges.append((sig,left,right))
        top_by_task={task:{c.signature for c in sorted(pool.values(),key=lambda c:(base.error(c.signature,target),*c.cost(),c.signature))[:128]} for task,target in targets.items()}
        if condition == "normalized_retirement":
            useful=set().union(*top_by_task.values())
            generated_edges=[(sig,*best_parents[sig]) for sig in useful if sig in best_parents and sig not in best_parents[sig][0:1] and sig != best_parents[sig][1].signature]
        credited_this_round=set()
        for sig,left,right in generated_edges:
            child=pool[sig]
            novelty=max(0, features.support_mask(sig).bit_count()-max(features.support_mask(left.signature).bit_count(),features.support_mask(right.signature).bit_count())) if 0<sig.bit_count()<64 else 0
            denominator=1.0 if condition=="raw_promotion" else 1.0+child.primitives+child.routing_bits/16+child.depth
            for parent,other in ((left,right),(right,left)):
                partners.setdefault(parent.signature,set()).add(other.signature)
                amount=novelty/denominator
                for task,target in targets.items():
                    if sig in top_by_task[task]:
                        gain=max(0,min(base.error(parent.signature,target),base.error(other.signature,target))-base.error(sig,target))
                        amount += gain/denominator
                        if gain: tasks.setdefault(parent.signature,set()).add(task)
                if amount:
                    credit[parent.signature]=credit.get(parent.signature,0)+amount
                    last_round[parent.signature]=round_index; credited_this_round.add(parent.signature)
        if condition == "normalized_retirement":
            for sig in list(credit):
                if round_index-last_round.get(sig,-99)>2 and len(tasks.get(sig,set()))<2: retired.add(sig)
        for task,target in targets.items():
            if task not in found and target in pool: found[task]={"round":round_index,"candidate":pool[target]}
        beam,eligible_count=select(pool,targets,condition,beam_size,rng,credit,tasks,partners,last_round,round_index)
        missing=[item["candidate"] for task,item in found.items() if all(c.signature!=targets[task] for c in beam)]
        for offset,candidate in enumerate(missing,1): beam[-offset]=candidate
        promoted=sum(credit.get(c.signature,0)>0 and (condition=="raw_promotion" or round_index-last_round.get(c.signature,-99)<=2 or len(tasks.get(c.signature,set()))>=2) for c in beam)
        history.append({"round":round_index,"pool":len(pool),"beam":len(beam),"found":sorted(found),"credited_this_round":len(credited_this_round),"credited_total":len(credit),"eligible_archive":eligible_count,"promoted_in_beam":promoted,"retired_total":len(retired)})
        if len(found)==len(base.TASKS): break
    solutions={task:{"round":item["round"],"primitives":item["candidate"].primitives,"routing_bits":item["candidate"].routing_bits,"depth":item["candidate"].depth,"signature":str(item["candidate"].signature),"expression":item["candidate"].expression} for task,item in found.items()}
    return {"seed":seed,"condition":condition,"exact_targets":len(found),"all_exact":len(found)==4,"solutions":solutions,"generated_unique_signatures":generated,"equivalent_merges":merges,"credited_signatures":len(credit),"final_eligible_archive":history[-1]["eligible_archive"],"final_promoted_in_beam":history[-1]["promoted_in_beam"],"retired_signatures":len(retired),"history":history}

def metric(values):
    a=np.asarray(values,float); return {"mean":float(a.mean()),"variance":float(a.var(ddof=1))}

def paired_stats(diffs):
    a=np.asarray(diffs,float); rng=np.random.default_rng(20260913)
    means=np.mean(rng.choice(a,(20000,len(a)),replace=True),axis=1)
    observed=abs(float(a.mean())); signs=np.array([[1 if mask&(1<<i) else -1 for i in range(len(a))] for mask in range(1<<len(a))])
    p=float(np.mean(np.abs(np.mean(signs*a,axis=1))>=observed-1e-12))
    sd=float(a.std(ddof=1)); return {"mean_difference":float(a.mean()),"difference_variance":float(a.var(ddof=1)),"bootstrap_95_ci":[float(np.quantile(means,.025)),float(np.quantile(means,.975))],"cohen_dz":float(a.mean()/sd) if sd else None,"exact_sign_flip_p":p}

def main():
    OUT.mkdir(exist_ok=False); started=time.monotonic(); records=[]
    for seed in range(1280,1284):
        for condition in ("raw_promotion","normalized_retirement"):
            begin=time.monotonic(); row=run(seed,condition); row["elapsed_seconds"]=time.monotonic()-begin; records.append(row)
            (OUT/"progress.json").write_text(json.dumps(records,indent=2)); print(seed,condition,row["exact_targets"],sorted(row["solutions"]),row["final_eligible_archive"],row["elapsed_seconds"],flush=True)
    aggregate={}
    for condition in ("raw_promotion","normalized_retirement"):
        group=[r for r in records if r["condition"]==condition]
        aggregate[condition]={"exact_targets":metric([r["exact_targets"] for r in group]),"all_exact_seeds":sum(r["all_exact"] for r in group),"exact_by_task":{task:sum(task in r["solutions"] for r in group) for task in base.TASKS},"seconds":metric([r["elapsed_seconds"] for r in group]),"unique_signatures":metric([r["generated_unique_signatures"] for r in group]),"equivalent_merges":metric([r["equivalent_merges"] for r in group]),"credited_signatures":metric([r["credited_signatures"] for r in group]),"final_eligible_archive":metric([r["final_eligible_archive"] for r in group]),"final_promoted_in_beam":metric([r["final_promoted_in_beam"] for r in group]),"retired_signatures":metric([r["retired_signatures"] for r in group])}
    raw={r["seed"]:r for r in records if r["condition"]=="raw_promotion"}; norm={r["seed"]:r for r in records if r["condition"]=="normalized_retirement"}
    comparison={"exact_targets":paired_stats([norm[s]["exact_targets"]-raw[s]["exact_targets"] for s in raw]),"runtime_ratio":aggregate["normalized_retirement"]["seconds"]["mean"]/aggregate["raw_promotion"]["seconds"]["mean"],"archive_ratio":aggregate["normalized_retirement"]["final_eligible_archive"]["mean"]/aggregate["raw_promotion"]["credited_signatures"]["mean"]}
    passes=comparison["exact_targets"]["mean_difference"]>=-.25 and comparison["archive_ratio"]<=.5
    result={"records":records,"aggregate":aggregate,"comparison":comparison,"passes_pilot":passes,"elapsed_seconds":time.monotonic()-started,"settings":{"seeds":list(range(1280,1284)),"beam":256,"rounds":8,"max_cost":16,"credit_decay":.5,"max_age":2,"promotion_quota":80},"sources":{str(path.relative_to(ROOT)):sha(path) for path in (Path(__file__),HERE/"PROTOCOL.md",E019/"search.py",E019/"search_v2.py")}}
    (OUT/"results.json").write_text(json.dumps(result,indent=2)); print(json.dumps({"aggregate":aggregate,"comparison":comparison,"passes_pilot":passes,"elapsed_seconds":result["elapsed_seconds"]},indent=2))

if __name__ == "__main__": main()
