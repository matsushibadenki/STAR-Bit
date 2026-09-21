"""E031 frozen-Function portability across prospective route/numeric task families."""
import hashlib
import importlib.util
import json
import os
import random
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get("E031_OUT", str(HERE / "run")))
E019 = ROOT / "results/E019-function-space-genesis"
E023 = ROOT / "results/E023-leave-one-task-out-transfer"
E024 = ROOT / "results/E024-probe-utility-diversity"
E026 = ROOT / "results/E026-counterfactual-admission"
E028 = ROOT / "results/E028-module-causal-ablation"
E030 = ROOT / "results/E030-provenance-barrier"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e030 = load("e030_for_e031", E030 / "main.py")
base = e030.base
e023 = e030.e023
e024 = e030.e024
e026 = e030.e026
e028 = e030.e028


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(function):
    value = 0
    for row in range(64):
        bits = [(row >> index) & 1 for index in range(6)]
        value |= int(function(bits)) << row
    return value


def task_signatures():
    functions = {
        "route_dual_mux_xnor": lambda b: not ((b[1] if b[0] else b[2]) ^ (b[4] if b[3] else b[5])),
        "route_cross_mux_xor": lambda b: (b[2] if b[0] else b[4]) ^ (b[5] if b[3] else b[1]),
        "route_cascade_mux": lambda b: (b[2] if b[1] else b[3]) if b[0] else (b[5] if b[4] else b[3]),
        "numeric_popcount_bit1": lambda b: (sum(b) >> 1) & 1,
        "numeric_unsigned_sum_ge6": lambda b: sum(b[index] << index for index in range(3)) + sum(b[index + 3] << index for index in range(3)) >= 6,
    }
    return {name: signature(function) for name, function in functions.items()}


def random_matched(template, seed, forbidden):
    inputs, _ = base.inputs_and_targets()
    rng = random.Random(seed + 131000)
    for draw in range(10000):
        expression = e023.randomize_expression(template.expression, rng, inputs)
        candidate_signature = e023.evaluate(expression, inputs)
        if candidate_signature in forbidden:
            continue
        assert e023.expression_cost(expression) == template.cost()
        return base.Candidate(candidate_signature, *template.cost(), expression), draw + 1
    raise RuntimeError("random match failed")


def metric(values):
    array = np.asarray(values, float)
    return {"mean": float(array.mean()), "unbiased_variance": None if len(array) < 2 else float(array.var(ddof=1)), "n": len(array)}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    admitted, frozen_row = e028.frozen()
    inputs, old_targets = base.inputs_and_targets()
    probes, evaluations = e024.task_signatures()
    tasks = task_signatures()
    assert len(set(tasks.values())) == len(tasks)
    old_signatures = set(inputs) | set(old_targets.values()) | set(probes.values()) | set(evaluations.values())
    assert not (set(tasks.values()) & old_signatures)

    seeds = list(range(1450, 1458))
    conditions = ("no_transfer", "admitted", "one_hop_barrier", "random_matched")
    forbidden = old_signatures | set(tasks.values()) | {admitted.signature}
    random_libraries = {}
    random_manifest = []
    used_random = set()
    for seed in seeds:
        for task_index, task in enumerate(tasks):
            candidate, draws = random_matched(admitted, seed * 37 + task_index, forbidden | used_random)
            used_random.add(candidate.signature)
            random_libraries[(seed, task)] = candidate
            random_manifest.append({"seed": seed, "task": task, "signature": str(candidate.signature), "expression": candidate.expression, "cost": candidate.cost(), "draws": draws})

    (OUT / "task_manifest.json").write_text(json.dumps({"tasks": {name: str(value) for name, value in tasks.items()}, "families": {"route": [name for name in tasks if name.startswith("route_")], "numeric": [name for name in tasks if name.startswith("numeric_")]}, "checked_against": sorted(str(value) for value in old_signatures)}, indent=2))
    (OUT / "frozen_libraries.json").write_text(json.dumps({"admitted": frozen_row, "random_matched": random_manifest}, indent=2))

    records = []
    started = time.monotonic()
    with (OUT / "progress.jsonl").open("w") as progress:
        for seed in seeds:
            for task, target in tasks.items():
                for condition in conditions:
                    if condition == "no_transfer":
                        library = []
                    elif condition == "random_matched":
                        library = [random_libraries[(seed, task)]]
                    else:
                        library = [admitted]
                    row = e030.provenance_search(seed, target, library, barrier=condition == "one_hop_barrier")
                    row.pop("trace")
                    row.update({"seed": seed, "task": task, "family": "route" if task.startswith("route_") else "numeric", "condition": condition, "library_signatures": [str(candidate.signature) for candidate in library]})
                    records.append(row)
                    progress.write(json.dumps(row) + "\n")
                    progress.flush()
                    print(seed, task, condition, int(row["exact"]), row["best_error"], flush=True)

    aggregate = {}
    for condition in conditions:
        rows = [row for row in records if row["condition"] == condition]
        aggregate[condition] = {
            "exact": metric([row["exact"] for row in rows]),
            "exact_by_task": {task: sum(row["exact"] for row in rows if row["task"] == task) for task in tasks},
            "exact_by_family": {family: metric([row["exact"] for row in rows if row["family"] == family]) for family in ("route", "numeric")},
            "best_error": metric([row["best_error"] for row in rows]),
            "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]),
            "uses_transfer": sum(row["exact"] and row["uses_transfer"] for row in rows),
        }
    sources = (HERE / "main.py", HERE / "PROTOCOL.md", E030 / "main.py", E028 / "main.py", E026 / "main.py", E026 / "run/admission.json", E024 / "main.py", E023 / "main.py", E019 / "search.py", E019 / "search_v2.py")
    result = {
        "records": records,
        "aggregate": aggregate,
        "settings": {"seeds": seeds, "tasks": list(tasks), "conditions": list(conditions), "beam": 128, "rounds": 6, "max_cost": 16},
        "elapsed_seconds": time.monotonic() - started,
        "sources": {str(path.relative_to(ROOT)): sha(path) for path in sources},
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({"aggregate": aggregate, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
