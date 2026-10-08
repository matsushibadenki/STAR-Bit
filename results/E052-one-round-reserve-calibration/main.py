import hashlib,importlib.util,json,math,time
from pathlib import Path
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E052-one-round-reserve-calibration'; OUT=HERE/'run'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
old=load('e039_for_e046',ROOT/'results/E039-capacity-admission/main.py'); e042=load('e042_for_e046',ROOT/'results/E042-difficulty-suite-calibration/main.py'); base=old.base; e026=old.e026; features=old.features; e023=old.e023
def scheduled_search(seed, target, module, beam_size, rounds, condition, max_cost=16, later_width=None, cohort=(), blocked=False, reserve=False):
    assert condition in ('no_transfer', 'learned_replace', 'learned_add', 'inert_replace', 'inert_add', 'random_replace', 'random_add')
    assert (module is None) == (condition == 'no_transfer')
    inputs, _ = base.inputs_and_targets()
    beam = [base.Candidate(signature, 0, 0, 0, ('input', index)) for index, signature in enumerate(inputs)]
    library_signatures = {c.signature for c in cohort}
    credit, partners, last = {}, {}, {}
    reserve_audit = None
    solution = None
    best, history, generated = 64, [], len(beam)
    first_round_selected = []
    input_width_history = []
    round2_selected = []
    injection_strategy = None if condition == 'no_transfer' else condition.rsplit('_', 1)[1]
    inert = condition.startswith('inert_')
    injected_collision = False
    slot_replaced_signature = None
    round_two_input_width = None
    started = time.monotonic()
    for round_index in range(1, rounds + 1):
        input_width_history.append(len(beam))
        if round_index == 2:
            round_two_input_width = len(beam)
        pool = {candidate.signature: candidate for candidate in beam}
        edges = []
        for index, left in enumerate(beam):
            for right in beam[index:]:
                if blocked and (left.signature in library_signatures or right.signature in library_signatures):
                    continue
                primitives = left.primitives + right.primitives + 1
                if primitives > max_cost:
                    continue
                routing = left.routing_bits + right.routing_bits + 2 * math.ceil(math.log2(6 + max(1, primitives)))
                depth = max(left.depth, right.depth) + 1
                for code, signature in enumerate(base.lut_outputs(left.signature, right.signature)):
                    candidate = base.Candidate(signature, primitives, routing, depth, ('lut', signature, code, left.expression, right.expression))
                    old = pool.get(signature)
                    if old is None:
                        pool[signature] = candidate
                        generated += 1
                    elif base.better(candidate, old):
                        pool[signature] = candidate
                    if signature not in (left.signature, right.signature):
                        edges.append((signature, left, right))
        best = min(best, min(base.error(signature, target) for signature in pool))
        history.append(best)
        if target in pool:
            solution = pool[target]
            break
        top = {candidate.signature for candidate in sorted(pool.values(), key=lambda candidate: (base.error(candidate.signature, target), *candidate.cost(), e026.stable(candidate.signature, seed, round_index)))[:128]}
        for signature, left, right in edges:
            novelty = max(0, features.support_mask(signature).bit_count() - max(features.support_mask(left.signature).bit_count(), features.support_mask(right.signature).bit_count())) if 0 < signature.bit_count() < 64 else 0
            for parent, other in ((left, right), (right, left)):
                amount = novelty + (max(0, min(base.error(parent.signature, target), base.error(other.signature, target)) - base.error(signature, target)) if signature in top else 0)
                if amount:
                    credit[parent.signature] = credit.get(parent.signature, 0) + amount
                    partners.setdefault(parent.signature, set()).add(other.signature)
                    last[parent.signature] = round_index
        for signature in [signature for signature, last_seen in last.items() if round_index - last_seen > 2]:
            credit.pop(signature, None); partners.pop(signature, None); last.pop(signature, None)
        input_before_selection = [c.signature for c in beam]
        beam = e026.select(pool, target, beam_size if round_index == 1 or later_width is None else later_width, seed, round_index, credit, partners, last)
        if round_index == 3 and reserve:
            ordinary = list(beam)
            input_signatures = set(input_before_selection)
            eligible = [c for c in pool.values() if c.signature not in input_signatures and c.signature not in library_signatures and e023.expression_signatures(c.expression) & library_signatures]
            protected = sorted(eligible, key=lambda c: (*c.cost(), e026.stable(c.signature, seed, round_index)))[:16]
            protected_signatures = {c.signature for c in protected}
            beam = protected + [c for c in ordinary if c.signature not in protected_signatures][:192-len(protected)]
            assert len(beam)==192 and len({c.signature for c in beam})==192
            reserve_audit = {'eligible': len(eligible), 'protected': [str(c.signature) for c in protected], 'displaced': [str(c.signature) for c in ordinary if c.signature not in {v.signature for v in beam}], 'selected': [{'signature':str(c.signature),'primitives':c.primitives,'routing_bits':c.routing_bits,'depth':c.depth,'expression':c.expression} for c in beam]}
        if round_index == 2:
            round2_selected = [str(c.signature) for c in beam]
            assert not (set(map(int,round2_selected)) & library_signatures)
            beam.extend(cohort)
            generated += len(cohort)
        if round_index == 1 and module is not None:
            first_round_selected = [str(candidate.signature) for candidate in beam]
            collision_index = next((index for index, candidate in enumerate(beam) if candidate.signature == module.signature), None)
            injected_collision = collision_index is not None
            if collision_index is not None:
                slot_replaced_signature = str(beam[collision_index].signature)
                beam[collision_index] = module
            elif injection_strategy == 'replace':
                slot_replaced_signature = str(beam[-1].signature)
                beam[-1] = module
                generated += 1
            else:
                beam.append(module)
                generated += 1
        elif round_index == 1:
            first_round_selected = [str(candidate.signature) for candidate in beam]
    used = [] if solution is None else sorted(e023.expression_signatures(solution.expression) & library_signatures)
    return {'reserve_audit': reserve_audit, 'round2_selected': round2_selected, 'input_width_history': input_width_history, 'exact': solution is not None, 'round': None if solution is None else round_index, 'best_error': best, 'best_error_history': history, 'uses_transfer': bool(used), 'used_signatures': [str(signature) for signature in used], 'expression': None if solution is None else solution.expression, 'primitives': None if solution is None else solution.primitives, 'routing_bits': None if solution is None else solution.routing_bits, 'depth': None if solution is None else solution.depth, 'generated_unique_signatures': generated, 'elapsed_seconds': time.monotonic() - started, 'first_round_selected': first_round_selected, 'injection_strategy': injection_strategy, 'injected_collision': injected_collision, 'slot_replaced_signature': slot_replaced_signature, 'round_two_input_width': round_two_input_width}


def main():
 OUT.mkdir(); tasks=e042.tasks_from_registry(); seeds=list(range(1670,1676)); conditions=['baseline','learned_standard','learned_reserve','inert_reserve','random_reserve']; source=json.loads((ROOT/'results/E048-cohort-admission-preflight/run/results.json').read_text()); cohort=[base.Candidate(int(x['signature']),x['primitives'],x['routing_bits'],x['depth'],x['expression']) for x in source['source_cohort']]; pre=[]; union=set()
 for seed in seeds:
  for task,target in tasks.items():
   row=scheduled_search(seed,target,None,128,2,'no_transfer',16,192); assert not row['exact']; beam=set(map(int,row['round2_selected'])); assert not beam&{c.signature for c in cohort}; union|=beam; pre.append({'seed':seed,'task':task,'round1':row['first_round_selected'],'round2':row['round2_selected'],'seconds':row['elapsed_seconds']})
 inputs,old_targets=base.inputs_and_targets(); forbidden=union|set(inputs)|set(old_targets.values())|set(tasks.values())|{c.signature for c in cohort}; used=set(); randoms={}; manifest=[]
 for seed in seeds:
  for ti,task in enumerate(tasks):
   group=[]
   for j,c in enumerate(cohort):
    candidate,draws=old.e031.random_matched(c,seed*1013+ti*37+j,forbidden|used); used.add(candidate.signature); group.append(candidate)
   randoms[seed,task]=group; manifest.append({'seed':seed,'task':task,'cohort':[{'signature':str(c.signature),'primitives':c.primitives,'routing_bits':c.routing_bits,'depth':c.depth,'expression':c.expression} for c in group]})
 (OUT/'preflight.json').write_text(json.dumps(pre,indent=2)); (OUT/'manifest.json').write_text(json.dumps({'source':source['source_cohort'],'random':manifest},indent=2)); rows=[]
 with (OUT/'progress.jsonl').open('w') as f:
  for seed in seeds:
   for task,target in tasks.items():
    for condition in conditions:
     if sum(x['elapsed_seconds'] for x in rows)>=900: break
     library=[] if condition=='baseline' else randoms[seed,task] if condition=='random_reserve' else cohort
     row=scheduled_search(seed,target,None,128,4,'no_transfer',16,192,library,condition=='inert_reserve',condition.endswith('_reserve')); row.update(seed=seed,task=task,condition=condition,library=[str(c.signature) for c in library]); rows.append(row); f.write(json.dumps(row,allow_nan=False)+'\n'); f.flush()
    print(seed,task,len(rows),flush=True)
 paths=[HERE/'main.py',HERE/'PROTOCOL.md',ROOT/'results/E049-frozen-cohort-semantics/main.py',ROOT/'results/E048-cohort-admission-preflight/run/results.json',ROOT/'results/E026-counterfactual-admission/main.py',ROOT/'results/E019-function-space-genesis/search.py']; (OUT/'results.json').write_text(json.dumps({'records':rows,'complete':len(rows)==240,'search_seconds':sum(x['elapsed_seconds'] for x in rows),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}},indent=2,allow_nan=False))
if __name__=='__main__': main()
