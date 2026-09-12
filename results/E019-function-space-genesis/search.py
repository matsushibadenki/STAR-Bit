"""Function-signature beam search for Module Genesis."""
from dataclasses import dataclass
import math
import random

MASK = (1 << 64) - 1
TASKS = ("parity", "comparator", "mux", "carry")


def inputs_and_targets():
    inputs = []
    for bit in range(6):
        signature = sum(((row >> bit) & 1) << row for row in range(64))
        inputs.append(signature)
    targets = {}
    for task in TASKS:
        value = 0
        for row in range(64):
            bits = [(row >> bit) & 1 for bit in range(6)]
            if task == "parity":
                output = sum(bits) % 2
            elif task == "comparator":
                output = sum(bits[i] << i for i in range(3)) > sum(bits[i+3] << i for i in range(3))
            elif task == "mux":
                output = bits[1] if bits[0] else bits[2]
            else:
                output = sum(bits[i] << i for i in range(3)) + sum(bits[i+3] << i for i in range(3)) >= 8
            value |= int(output) << row
        targets[task] = value
    return inputs, targets


def lut_outputs(a, b):
    terms = ((~a & ~b) & MASK, (a & ~b) & MASK, (~a & b) & MASK, a & b)
    outputs = [0] * 16
    for code in range(1, 16):
        low = code & -code
        bit = low.bit_length() - 1
        outputs[code] = outputs[code ^ low] | terms[bit]
    return outputs


def error(signature, target):
    return (signature ^ target).bit_count()


@dataclass(frozen=True)
class Candidate:
    signature: int
    primitives: int
    routing_bits: int
    depth: int
    expression: object

    def cost(self):
        return self.primitives, self.routing_bits, self.depth


def better(left, right):
    return left.cost() < right.cost()


def pareto(candidates, targets):
    ordered = sorted(candidates, key=lambda c: (sum(error(c.signature, target) for target in targets.values()), *c.cost(), c.signature))
    frontier = []
    vectors = []
    for candidate in ordered:
        vector = tuple(error(candidate.signature, targets[task]) for task in TASKS) + candidate.cost()
        if any(all(a <= b for a, b in zip(existing, vector)) for existing in vectors):
            continue
        keep_candidates = []
        keep_vectors = []
        for old, old_vector in zip(frontier, vectors):
            if not all(a <= b for a, b in zip(vector, old_vector)):
                keep_candidates.append(old)
                keep_vectors.append(old_vector)
        keep_candidates.append(candidate)
        keep_vectors.append(vector)
        frontier, vectors = keep_candidates, keep_vectors
    return frontier


def select_beam(pool, targets, mode, beam_size, rng, input_signatures):
    chosen = {}

    def add(sequence, limit=None):
        count = 0
        for candidate in sequence:
            if candidate.signature not in chosen:
                chosen[candidate.signature] = candidate
                count += 1
                if limit is not None and count >= limit:
                    break

    values = list(pool.values())
    for task in TASKS:
        target = targets[task]
        add(sorted(values, key=lambda c: (error(c.signature, target), *c.cost(), c.signature)), 16)
    add(sorted(values, key=lambda c: (*c.cost(), c.signature)), 8)

    if mode == "composition_pareto":
        add(pareto(values, targets), 16)
        anchor_candidates = list(chosen.values())[:72]
        provisional = sorted(values, key=lambda c: (min(error(c.signature, target) for target in targets.values()), c.primitives, c.signature))[:384]
        lookahead = []
        for candidate in provisional:
            best = [64] * len(TASKS)
            for anchor in anchor_candidates:
                for output in lut_outputs(candidate.signature, anchor.signature):
                    for index, task in enumerate(TASKS):
                        best[index] = min(best[index], error(output, targets[task]))
            lookahead.append((min(best), sum(best), candidate.primitives, candidate.routing_bits, candidate.depth, candidate.signature, candidate))
        add((item[-1] for item in sorted(lookahead)), 24)

        buckets = {}
        for candidate in values:
            ones = candidate.signature.bit_count()
            dependency = 0
            for bit, input_signature in enumerate(input_signatures):
                shifted = ((candidate.signature & input_signature) >> (1 << bit)) if False else 0
                paired_difference = 0
                step = 1 << bit
                for base in range(0, 64, 2 * step):
                    low = (candidate.signature >> base) & ((1 << step) - 1)
                    high = (candidate.signature >> (base + step)) & ((1 << step) - 1)
                    paired_difference |= low ^ high
                if paired_difference:
                    dependency |= 1 << bit
            bucket = (ones // 4, dependency, candidate.depth)
            buckets.setdefault(bucket, []).append(candidate)
        bucket_keys = list(buckets)
        rng.shuffle(bucket_keys)
        diversity = []
        for key in bucket_keys:
            group = buckets[key]
            diversity.append(group[rng.randrange(len(group))])
        add(diversity, 16)

    remainder = values[:]
    rng.shuffle(remainder)
    add(remainder)
    return list(chosen.values())[:beam_size]


def expression_signatures(expression):
    if expression[0] == "input":
        return set()
    _, signature, _, left, right = expression
    return {signature} | expression_signatures(left) | expression_signatures(right)


def run(seed, mode, beam_size=128, rounds=7, max_cost=14):
    input_signatures, targets = inputs_and_targets()
    rng = random.Random(seed)
    beam = [Candidate(signature, 0, 0, 0, ("input", index)) for index, signature in enumerate(input_signatures)]
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
                for code, signature in enumerate(lut_outputs(left.signature, right.signature)):
                    candidate = Candidate(signature, primitives, routing, depth, ("lut", signature, code, left.expression, right.expression))
                    existing = pool.get(signature)
                    if existing is None:
                        pool[signature] = candidate
                        generated_unique += 1
                    else:
                        equivalent_merges += 1
                        if better(candidate, existing):
                            pool[signature] = candidate
        for task, target in targets.items():
            if task not in found and target in pool:
                found[task] = {"round": round_index, "candidate": pool[target]}
        beam = select_beam(pool, targets, mode, beam_size, rng, input_signatures)
        missing_found = [item["candidate"] for task, item in found.items() if all(candidate.signature != targets[task] for candidate in beam)]
        for offset, candidate in enumerate(missing_found, 1):
            beam[-offset] = candidate
        history.append({"round": round_index, "pair_count": pair_count, "pool_signatures": len(pool), "beam": len(beam), "found": sorted(found)})
        if len(found) == len(TASKS):
            break
    solutions = {}
    for task, item in found.items():
        candidate = item["candidate"]
        solutions[task] = {"round": item["round"], "signature": str(candidate.signature), "primitives": candidate.primitives, "routing_bits": candidate.routing_bits, "depth": candidate.depth, "expression": candidate.expression}
    overlap = {}
    for left_index, left_task in enumerate(TASKS):
        if left_task not in found:
            continue
        left_nodes = expression_signatures(found[left_task]["candidate"].expression)
        for right_task in TASKS[left_index+1:]:
            if right_task not in found:
                continue
            right_nodes = expression_signatures(found[right_task]["candidate"].expression)
            overlap[f"{left_task}/{right_task}"] = len(left_nodes & right_nodes)
    return {
        "seed": seed,
        "condition": mode,
        "exact_targets": len(found),
        "all_exact": len(found) == len(TASKS),
        "solutions": solutions,
        "intermediate_overlap": overlap,
        "generated_unique_signatures": generated_unique,
        "equivalent_function_merges": equivalent_merges,
        "history": history,
    }
