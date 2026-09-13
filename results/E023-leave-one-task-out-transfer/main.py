"""E023 leave-one-task-out Function transfer experiment."""
import hashlib
import importlib.util
import json
import math
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
E019 = ROOT / "results/E019-function-space-genesis"
E021 = ROOT / "results/E021-cost-normalized-promotion"
sys.path.insert(0, str(E019))
import search as base
import search_v2 as features

spec = importlib.util.spec_from_file_location("e021_promotion", E021 / "main.py")
promotion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promotion)
OUT = HERE / "run"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expression_cost(expression):
    if expression[0] == "input":
        return 0, 0, 0
    left = expression_cost(expression[3])
    right = expression_cost(expression[4])
    primitives = left[0] + right[0] + 1
    routing = left[1] + right[1] + 2 * math.ceil(math.log2(6 + max(1, primitives)))
    return primitives, routing, max(left[2], right[2]) + 1


def walk(expression, source, occurrences, expressions):
    if expression[0] == "input":
        return
    signature = int(expression[1])
    occurrences[signature].add(source)
    cost = expression_cost(expression)
    if signature not in expressions or cost < expressions[signature][0]:
        expressions[signature] = (cost, expression)
    walk(expression[3], source, occurrences, expressions)
    walk(expression[4], source, occurrences, expressions)


def build_cross_task_library(held_task):
    result = json.loads((E021 / "run/results.json").read_text())
    rows = [row for row in result["records"] if row["condition"] == "normalized_retired"]
    inputs, targets = base.inputs_and_targets()
    forbidden = set(inputs) | set(targets.values())
    occurrences = defaultdict(set)
    expressions = {}
    for row in rows:
        for task, solution in row["solutions"].items():
            if task != held_task:
                walk(solution["expression"], (row["seed"], task), occurrences, expressions)
    selected = []
    manifest = []
    for low, high in ((1, 1), (2, 3), (4, 7), (8, 15)):
        candidates = []
        for signature, sources in occurrences.items():
            if signature in forbidden:
                continue
            cost, expression = expressions[signature]
            if low <= cost[0] <= high:
                candidates.append((-len(sources), cost, signature, expression, sources))
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        assert len(candidates) >= 2
        for _, cost, signature, expression, sources in candidates[:2]:
            candidate = base.Candidate(signature, *cost, expression)
            selected.append(candidate)
            manifest.append({
                "signature": str(signature),
                "primitives": cost[0],
                "routing_bits": cost[1],
                "depth": cost[2],
                "source_count": len(sources),
                "source_seeds": sorted({seed for seed, _ in sources}),
                "source_tasks": sorted({task for _, task in sources}),
                "target_error": base.error(signature, targets[held_task]),
                "expression": expression,
            })
    assert len(selected) == 8
    assert all(held_task not in item["source_tasks"] for item in manifest)
    return selected, manifest


def evaluate(expression, inputs):
    if expression[0] == "input":
        return inputs[expression[1]]
    return base.lut_outputs(evaluate(expression[3], inputs), evaluate(expression[4], inputs))[expression[2]]


def randomize_expression(expression, rng, inputs):
    if expression[0] == "input":
        return ("input", rng.randrange(6))
    left = randomize_expression(expression[3], rng, inputs)
    right = randomize_expression(expression[4], rng, inputs)
    code = rng.randrange(16)
    signature = base.lut_outputs(evaluate(left, inputs), evaluate(right, inputs))[code]
    return ("lut", signature, code, left, right)


def random_library(templates, held_task, seed, error_matched):
    inputs, targets = base.inputs_and_targets()
    forbidden = set(inputs) | set(targets.values())
    rng = random.Random(seed + (70000 if error_matched else 60000))
    used = set()
    selected = []
    residuals = []
    for template in templates:
        draw_count = 2048 if error_matched else 1
        best = None
        attempts = 0
        while attempts < max(10000, draw_count):
            expression = randomize_expression(template.expression, rng, inputs)
            signature = evaluate(expression, inputs)
            attempts += 1
            if signature in forbidden or signature in used:
                continue
            cost = expression_cost(expression)
            assert cost == template.cost()
            residual = abs(base.error(signature, targets[held_task]) - base.error(template.signature, targets[held_task]))
            item = (residual, signature, expression)
            if best is None or item[:2] < best[:2]:
                best = item
            if not error_matched or attempts >= draw_count:
                break
        if best is None:
            raise RuntimeError("could not construct matched random Function")
        residual, signature, expression = best
        selected.append(base.Candidate(signature, *template.cost(), expression))
        used.add(signature)
        residuals.append(residual)
    return selected, residuals


def expression_signatures(expression):
    if expression[0] == "input":
        return set()
    return {int(expression[1])} | expression_signatures(expression[3]) | expression_signatures(expression[4])


def select_single(pool, target, beam_size, rng, credit, partners, last, round_index):
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

    add(sorted(values, key=lambda c: (base.error(c.signature, target), *c.cost(), c.signature)), 32)

    def score(candidate):
        signature = candidate.signature
        per_partner = credit.get(signature, 0) / max(1, len(partners.get(signature, set())))
        structural = 1 + 0.35 * candidate.primitives + 0.02 * candidate.routing_bits + 0.25 * candidate.depth
        return per_partner / structural

    ranked = sorted(values, key=lambda c: (-score(c), *c.cost(), c.signature))
    add((c for c in ranked if credit.get(c.signature, 0) > 0 and round_index - last.get(c.signature, round_index) <= 2), 48)
    buckets = {}
    for candidate in values:
        key = (features.support_mask(candidate.signature), candidate.signature.bit_count() // 8)
        rank = (credit.get(candidate.signature, 0) / max(1, len(partners.get(candidate.signature, set()))), -candidate.primitives, -candidate.routing_bits, -candidate.depth)
        if key not in buckets or rank > buckets[key][0]:
            buckets[key] = (rank, candidate)
    diverse = [item[1] for item in buckets.values()]
    rng.shuffle(diverse)
    add(diverse, 32)
    add(sorted(values, key=lambda c: (base.error(c.signature, target), *c.cost(), c.signature)))
    remainder = values[:]
    rng.shuffle(remainder)
    add(remainder)
    return list(chosen.values())[:beam_size]


def run(seed, held_task, condition, learned, beam_size=128, rounds=6, max_cost=16):
    inputs, targets = base.inputs_and_targets()
    target = targets[held_task]
    residuals = []
    if condition == "learned_cross_task":
        library = learned
    elif condition == "random_cost_matched":
        library, residuals = random_library(learned, held_task, seed, False)
    elif condition == "random_error_matched":
        library, residuals = random_library(learned, held_task, seed, True)
    else:
        library = []
    protected = {candidate.signature for candidate in library}
    rng = random.Random(seed)
    beam = [base.Candidate(signature, 0, 0, 0, ("input", index)) for index, signature in enumerate(inputs)] + list(library)
    credit = {}
    partners = {}
    last = {}
    generated = len(beam)
    merges = 0
    retired = 0
    solution = None
    history = []
    started = time.monotonic()
    for round_index in range(1, rounds + 1):
        pool = {candidate.signature: candidate for candidate in beam}
        edges = []
        for left_index, left in enumerate(beam):
            for right in beam[left_index:]:
                primitives = left.primitives + right.primitives + 1
                if primitives > max_cost:
                    continue
                routing = left.routing_bits + right.routing_bits + 2 * math.ceil(math.log2(6 + max(1, primitives)))
                depth = max(left.depth, right.depth) + 1
                for code, signature in enumerate(base.lut_outputs(left.signature, right.signature)):
                    candidate = base.Candidate(signature, primitives, routing, depth, ("lut", signature, code, left.expression, right.expression))
                    old = pool.get(signature)
                    if old is None:
                        pool[signature] = candidate
                        generated += 1
                    else:
                        merges += 1
                        if base.better(candidate, old):
                            pool[signature] = candidate
                    if signature not in (left.signature, right.signature):
                        edges.append((signature, left, right))
        top = {candidate.signature for candidate in sorted(pool.values(), key=lambda c: (base.error(c.signature, target), *c.cost(), c.signature))[:128]}
        for signature, left, right in edges:
            child_support = features.support_mask(signature).bit_count()
            parent_support = max(features.support_mask(left.signature).bit_count(), features.support_mask(right.signature).bit_count())
            novelty = max(0, child_support - parent_support) if 0 < signature.bit_count() < 64 else 0
            for parent, other in ((left, right), (right, left)):
                amount = novelty
                if signature in top:
                    amount += max(0, min(base.error(parent.signature, target), base.error(other.signature, target)) - base.error(signature, target))
                if amount:
                    credit[parent.signature] = credit.get(parent.signature, 0) + amount
                    partners.setdefault(parent.signature, set()).add(other.signature)
                    last[parent.signature] = round_index
        stale = [signature for signature, seen in last.items() if round_index - seen > 2 and signature not in protected]
        for signature in stale:
            credit.pop(signature, None)
            partners.pop(signature, None)
            last.pop(signature, None)
        retired += len(stale)
        if target in pool:
            solution = {"round": round_index, "candidate": pool[target]}
            history.append({"round": round_index, "pool": len(pool), "exact": True, "credit_entries": len(credit)})
            break
        beam = select_single(pool, target, beam_size, rng, credit, partners, last, round_index)
        present = {candidate.signature for candidate in beam}
        missing = [candidate for candidate in library if candidate.signature not in present]
        for offset, candidate in enumerate(missing, 1):
            beam[-offset] = candidate
        history.append({"round": round_index, "pool": len(pool), "exact": False, "credit_entries": len(credit)})
    output = None
    if solution is not None:
        candidate = solution["candidate"]
        used = sorted(expression_signatures(candidate.expression) & protected)
        output = {
            "round": solution["round"],
            "signature": str(candidate.signature),
            "primitives": candidate.primitives,
            "routing_bits": candidate.routing_bits,
            "depth": candidate.depth,
            "uses_transferred_function": bool(used),
            "transferred_signatures_used": [str(signature) for signature in used],
            "expression": candidate.expression,
        }
    return {
        "seed": seed,
        "task": held_task,
        "condition": condition,
        "exact": solution is not None,
        "solution": output,
        "library_size": len(library),
        "library_signatures": [str(candidate.signature) for candidate in library],
        "error_match_residuals": residuals,
        "generated_unique_signatures": generated,
        "equivalent_merges": merges,
        "credited_signatures": len(credit),
        "retired_signatures": retired,
        "elapsed_seconds": time.monotonic() - started,
        "history": history,
    }


def metric(values):
    values = np.asarray(values, dtype=float)
    return {"mean": float(values.mean()), "variance": float(values.var(ddof=1))}


def main():
    OUT.mkdir(exist_ok=False)
    libraries = {}
    manifests = {}
    for task in base.TASKS:
        libraries[task], manifests[task] = build_cross_task_library(task)
    (OUT / "cross_task_libraries.json").write_text(json.dumps(manifests, indent=2))
    records = []
    started = time.monotonic()
    conditions = ("no_transfer", "random_cost_matched", "random_error_matched", "learned_cross_task")
    for seed in range(1320, 1336):
        for task in base.TASKS:
            for condition in conditions:
                row = run(seed, task, condition, libraries[task])
                records.append(row)
                (OUT / "progress.json").write_text(json.dumps(records, indent=2))
                print(seed, task, condition, int(row["exact"]), row["solution"]["round"] if row["solution"] else None, f"{row['elapsed_seconds']:.3f}", flush=True)
    aggregate = {}
    for condition in conditions:
        group = [row for row in records if row["condition"] == condition]
        aggregate[condition] = {
            "exact": metric([row["exact"] for row in group]),
            "elapsed_seconds": metric([row["elapsed_seconds"] for row in group]),
            "generated_unique_signatures": metric([row["generated_unique_signatures"] for row in group]),
            "exact_by_task": {task: sum(row["exact"] for row in group if row["task"] == task) for task in base.TASKS},
            "uses_transfer_by_task": {task: sum(row["exact"] and row["solution"]["uses_transferred_function"] for row in group if row["task"] == task) for task in base.TASKS},
        }
    result = {
        "records": records,
        "aggregate": aggregate,
        "settings": {"seeds": list(range(1320, 1336)), "tasks": list(base.TASKS), "conditions": list(conditions), "beam": 128, "rounds": 6, "max_cost": 16, "library_size": 8, "error_control_draws_per_slot": 2048},
        "elapsed_seconds": time.monotonic() - started,
        "sources": {str(path.relative_to(ROOT)): sha(path) for path in (Path(__file__), HERE / "PROTOCOL.md", E021 / "main.py", E021 / "run/results.json", E019 / "search.py", E019 / "search_v2.py")},
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"aggregate": aggregate, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
