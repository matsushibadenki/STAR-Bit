"""E019 function-space search with task-independent affine retention."""
import math
import random

import search as base


LOW_MASKS = []
for bit in range(6):
    step = 1 << bit
    mask = 0
    for start in range(0, 64, 2 * step):
        mask |= ((1 << step) - 1) << start
    LOW_MASKS.append(mask)


def support_mask(signature):
    result = 0
    for bit, low_mask in enumerate(LOW_MASKS):
        step = 1 << bit
        high_mask = base.MASK ^ low_mask
        flipped = ((signature & low_mask) << step) | ((signature & high_mask) >> step)
        if flipped != signature:
            result |= 1 << bit
    return result


def affine_signatures(inputs):
    values = {0, base.MASK}
    for mask in range(1, 64):
        signature = 0
        for bit in range(6):
            if mask & (1 << bit):
                signature ^= inputs[bit]
        values.add(signature)
        values.add(signature ^ base.MASK)
    assert len(values) == 128
    return values


def select(pool, targets, condition, beam_size, rng, input_signatures):
    values = list(pool.values())
    chosen = {}

    def add(sequence, limit=None):
        count = 0
        for candidate in sequence:
            if candidate.signature not in chosen:
                chosen[candidate.signature] = candidate
                count += 1
                if limit is not None and count >= limit:
                    break

    for task in base.TASKS:
        target = targets[task]
        add(sorted(values, key=lambda c: (base.error(c.signature, target), *c.cost(), c.signature)), 16)
    if condition == "affine_scaffold":
        affine = affine_signatures(input_signatures)
        add(sorted((candidate for candidate in values if candidate.signature in affine), key=lambda c: (*c.cost(), c.signature)))
        buckets = {}
        for candidate in values:
            bucket = (support_mask(candidate.signature), candidate.signature.bit_count() // 4)
            previous = buckets.get(bucket)
            if previous is None or candidate.cost() < previous.cost() or (candidate.cost() == previous.cost() and rng.random() < .5):
                buckets[bucket] = candidate
        diverse = list(buckets.values())
        rng.shuffle(diverse)
        add(diverse)
    else:
        ranked = sorted(values, key=lambda c: (min(base.error(c.signature, target) for target in targets.values()), *c.cost(), c.signature))
        add(ranked)
    if len(chosen) < beam_size:
        remainder = values[:]
        rng.shuffle(remainder)
        add(remainder)
    return list(chosen.values())[:beam_size]


def contains_affine_intermediate(expression, affine, output_signature):
    if expression[0] == "input":
        return False
    _, signature, _, left, right = expression
    return (signature != output_signature and signature in affine) or contains_affine_intermediate(left, affine, output_signature) or contains_affine_intermediate(right, affine, output_signature)


def run(seed, condition, beam_size=256, rounds=7, max_cost=14):
    input_signatures, targets = base.inputs_and_targets()
    affine = affine_signatures(input_signatures)
    rng = random.Random(seed)
    beam = [base.Candidate(signature, 0, 0, 0, ("input", index)) for index, signature in enumerate(input_signatures)]
    found = {}
    generated_unique = len(beam)
    equivalent_merges = 0
    history = []
    for round_index in range(1, rounds + 1):
        pool = {candidate.signature: candidate for candidate in beam}
        pair_count = 0
        for left_index, left in enumerate(beam):
            for right in beam[left_index:]:
                pair_count += 1
                primitives = left.primitives + right.primitives + 1
                if primitives > max_cost:
                    continue
                address_bits = 2 * math.ceil(math.log2(6 + max(1, primitives)))
                routing = left.routing_bits + right.routing_bits + address_bits
                depth = max(left.depth, right.depth) + 1
                for code, signature in enumerate(base.lut_outputs(left.signature, right.signature)):
                    candidate = base.Candidate(signature, primitives, routing, depth, ("lut", signature, code, left.expression, right.expression))
                    existing = pool.get(signature)
                    if existing is None:
                        pool[signature] = candidate
                        generated_unique += 1
                    else:
                        equivalent_merges += 1
                        if base.better(candidate, existing):
                            pool[signature] = candidate
        for task, target in targets.items():
            if task not in found and target in pool:
                found[task] = {"round": round_index, "candidate": pool[target]}
        beam = select(pool, targets, condition, beam_size, rng, input_signatures)
        missing = [item["candidate"] for task, item in found.items() if all(candidate.signature != targets[task] for candidate in beam)]
        for offset, candidate in enumerate(missing, 1):
            beam[-offset] = candidate
        history.append({"round": round_index, "pair_count": pair_count, "pool_signatures": len(pool), "beam": len(beam), "found": sorted(found), "affine_retained": sum(candidate.signature in affine for candidate in beam)})
        if len(found) == len(base.TASKS):
            break
    solutions = {}
    for task, item in found.items():
        candidate = item["candidate"]
        solutions[task] = {
            "round": item["round"],
            "signature": str(candidate.signature),
            "primitives": candidate.primitives,
            "routing_bits": candidate.routing_bits,
            "depth": candidate.depth,
            "uses_affine_intermediate": contains_affine_intermediate(candidate.expression, affine, candidate.signature),
            "expression": candidate.expression,
        }
    return {
        "seed": seed,
        "condition": condition,
        "exact_targets": len(found),
        "all_exact": len(found) == len(base.TASKS),
        "solutions": solutions,
        "generated_unique_signatures": generated_unique,
        "equivalent_function_merges": equivalent_merges,
        "history": history,
    }

