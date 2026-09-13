"""E022 fixed learned-Function transfer experiment."""
import hashlib
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
sys.path.insert(0, str(E021))
import search as base
import search_v2 as features
import main as promotion

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


def source_library():
    result = json.loads((E021 / "run/results.json").read_text())
    rows = [row for row in result["records"] if row["condition"] == "normalized_retired"]
    inputs, targets = base.inputs_and_targets()
    forbidden = set(inputs) | set(targets.values())
    occurrences = defaultdict(set)
    expressions = {}
    for row in rows:
        for task, solution in row["solutions"].items():
            walk(solution["expression"], (row["seed"], task), occurrences, expressions)
    bands = ((1, 1), (2, 3), (4, 7), (8, 15))
    selected = []
    for low, high in bands:
        candidates = []
        for signature, sources in occurrences.items():
            if signature in forbidden:
                continue
            cost, expression = expressions[signature]
            if low <= cost[0] <= high:
                candidates.append((-len(sources), cost, signature, expression, sources))
        candidates.sort(key=lambda item: (item[0], item[1], item[2]))
        assert len(candidates) >= 4
        for _, cost, signature, expression, sources in candidates[:4]:
            selected.append(base.Candidate(signature, *cost, expression))
    assert len(selected) == 16 and len({candidate.signature for candidate in selected}) == 16
    manifest = []
    for candidate in selected:
        sources = occurrences[candidate.signature]
        manifest.append({
            "signature": str(candidate.signature),
            "primitives": candidate.primitives,
            "routing_bits": candidate.routing_bits,
            "depth": candidate.depth,
            "source_count": len(sources),
            "source_seeds": sorted({seed for seed, _ in sources}),
            "source_tasks": sorted({task for _, task in sources}),
            "expression": candidate.expression,
        })
    return selected, manifest


def randomize_expression(expression, rng):
    if expression[0] == "input":
        return ("input", rng.randrange(6))
    left = randomize_expression(expression[3], rng)
    right = randomize_expression(expression[4], rng)
    left_signature = evaluate(left)
    right_signature = evaluate(right)
    code = rng.randrange(16)
    signature = base.lut_outputs(left_signature, right_signature)[code]
    return ("lut", signature, code, left, right)


def evaluate(expression):
    inputs, _ = base.inputs_and_targets()
    if expression[0] == "input":
        return inputs[expression[1]]
    return base.lut_outputs(evaluate(expression[3]), evaluate(expression[4]))[expression[2]]


def random_matched_library(learned, seed):
    inputs, targets = base.inputs_and_targets()
    forbidden = set(inputs) | set(targets.values())
    rng = random.Random(seed + 50000)
    selected = []
    used = set()
    for template in learned:
        for _ in range(10000):
            expression = randomize_expression(template.expression, rng)
            signature = evaluate(expression)
            if signature not in forbidden and signature not in used:
                cost = expression_cost(expression)
                assert cost == template.cost()
                selected.append(base.Candidate(signature, *cost, expression))
                used.add(signature)
                break
        else:
            raise RuntimeError("could not construct unique matched random Function")
    return selected


def expression_signatures(expression):
    if expression[0] == "input":
        return set()
    return {int(expression[1])} | expression_signatures(expression[3]) | expression_signatures(expression[4])


def run(seed, condition, learned, beam_size=256, rounds=6, max_cost=16):
    inputs, targets = base.inputs_and_targets()
    if condition == "learned_transfer":
        library = learned
    elif condition == "random_matched":
        library = random_matched_library(learned, seed)
    else:
        library = []
    protected = {candidate.signature for candidate in library}
    rng = random.Random(seed)
    beam = [base.Candidate(signature, 0, 0, 0, ("input", index)) for index, signature in enumerate(inputs)] + list(library)
    found = {}
    credit = {}
    credit_tasks = {}
    partners = {}
    last = {}
    generated = len(beam)
    merges = 0
    retired_total = 0
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
        top = {
            task: {candidate.signature for candidate in sorted(pool.values(), key=lambda c: (base.error(c.signature, targets[task]), *c.cost(), c.signature))[:128]}
            for task in base.TASKS
        }
        for signature, left, right in edges:
            child_support = features.support_mask(signature).bit_count()
            parent_support = max(features.support_mask(left.signature).bit_count(), features.support_mask(right.signature).bit_count())
            novelty = max(0, child_support - parent_support) if 0 < signature.bit_count() < 64 else 0
            for parent, other in ((left, right), (right, left)):
                if novelty:
                    promotion.add_credit(credit, credit_tasks, partners, last, parent.signature, other.signature, novelty, None, round_index)
                for task in base.TASKS:
                    if signature in top[task]:
                        gain = max(0, min(base.error(parent.signature, targets[task]), base.error(other.signature, targets[task])) - base.error(signature, targets[task]))
                        if gain:
                            promotion.add_credit(credit, credit_tasks, partners, last, parent.signature, other.signature, gain, task, round_index)
        stale = [signature for signature, seen in last.items() if round_index - seen > 2 and signature not in protected]
        for signature in stale:
            credit.pop(signature, None)
            credit_tasks.pop(signature, None)
            partners.pop(signature, None)
            last.pop(signature, None)
        retired_total += len(stale)
        for task, target in targets.items():
            if task not in found and target in pool:
                found[task] = {"round": round_index, "candidate": pool[target]}
        beam = promotion.select(pool, targets, "normalized_retired", beam_size, rng, credit, credit_tasks, partners, last, round_index)
        mandatory = list(library) + [item["candidate"] for item in found.values()]
        present = {candidate.signature for candidate in beam}
        missing = [candidate for candidate in mandatory if candidate.signature not in present]
        for offset, candidate in enumerate(missing, 1):
            beam[-offset] = candidate
        history.append({"round": round_index, "pool": len(pool), "found": sorted(found), "credit_entries": len(credit), "retired_total": retired_total})
        if len(found) == 4:
            break
    solutions = {}
    for task, item in found.items():
        candidate = item["candidate"]
        used = sorted(expression_signatures(candidate.expression) & protected)
        solutions[task] = {
            "round": item["round"],
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
        "condition": condition,
        "exact_targets": len(found),
        "solutions": solutions,
        "library_size": len(library),
        "library_signatures": [str(candidate.signature) for candidate in library],
        "generated_unique_signatures": generated,
        "equivalent_merges": merges,
        "credited_signatures": len(credit),
        "retired_signatures": retired_total,
        "elapsed_seconds": time.monotonic() - started,
        "history": history,
    }


def metric(values):
    values = np.asarray(values, dtype=float)
    return {"mean": float(values.mean()), "variance": float(values.var(ddof=1))}


def main():
    OUT.mkdir(exist_ok=False)
    learned, manifest = source_library()
    (OUT / "learned_library.json").write_text(json.dumps(manifest, indent=2))
    records = []
    started = time.monotonic()
    for seed in range(1300, 1316):
        for condition in ("no_transfer", "random_matched", "learned_transfer"):
            row = run(seed, condition, learned)
            records.append(row)
            (OUT / "progress.json").write_text(json.dumps(records, indent=2))
            print(seed, condition, row["exact_targets"], sorted(row["solutions"]), f"{row['elapsed_seconds']:.3f}", flush=True)
    aggregate = {}
    for condition in ("no_transfer", "random_matched", "learned_transfer"):
        group = [row for row in records if row["condition"] == condition]
        aggregate[condition] = {metric_name: metric([row[metric_name] for row in group]) for metric_name in ("exact_targets", "elapsed_seconds", "generated_unique_signatures", "equivalent_merges", "credited_signatures", "retired_signatures")}
        aggregate[condition]["exact_by_task"] = {task: sum(task in row["solutions"] for row in group) for task in base.TASKS}
        aggregate[condition]["uses_transfer_by_task"] = {task: sum(row["solutions"].get(task, {}).get("uses_transferred_function", False) for row in group) for task in base.TASKS}
    result = {
        "records": records,
        "aggregate": aggregate,
        "settings": {"seeds": list(range(1300, 1316)), "beam": 256, "rounds": 6, "max_cost": 16, "library_size": 16},
        "elapsed_seconds": time.monotonic() - started,
        "sources": {str(path.relative_to(ROOT)): sha(path) for path in (Path(__file__), HERE / "PROTOCOL.md", E021 / "main.py", E021 / "run/results.json", E019 / "search.py", E019 / "search_v2.py")},
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"aggregate": aggregate, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
