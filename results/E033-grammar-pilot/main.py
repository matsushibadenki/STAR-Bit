"""E033 prospective numeric/route grammar pilot with a frozen Function."""
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get("E033_OUT", str(HERE / "run")))
E019 = ROOT / "results/E019-function-space-genesis"
E023 = ROOT / "results/E023-leave-one-task-out-transfer"
E024 = ROOT / "results/E024-probe-utility-diversity"
E026 = ROOT / "results/E026-counterfactual-admission"
E028 = ROOT / "results/E028-module-causal-ablation"
E030 = ROOT / "results/E030-provenance-barrier"
E031 = ROOT / "results/E031-route-family-portability"


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


e031 = load("e031_for_e033", E031 / "main.py")
e030 = e031.e030
e028 = e031.e028
e024 = e031.e024
base = e031.base


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tasks_from_grammar():
    def unsigned_sum(bits):
        return sum(bits[index] << index for index in range(3)) + sum(bits[index + 3] << index for index in range(3))

    def route_pair(bits):
        return (bits[2] if bits[0] else bits[4]), (bits[5] if bits[3] else bits[1])

    functions = {
        "numeric_sum_ge4": lambda bits: unsigned_sum(bits) >= 4,
        "numeric_sum_ge5": lambda bits: unsigned_sum(bits) >= 5,
        "numeric_sum_ge7": lambda bits: unsigned_sum(bits) >= 7,
        "route_cross_and": lambda bits: route_pair(bits)[0] & route_pair(bits)[1],
        "route_cross_or": lambda bits: route_pair(bits)[0] | route_pair(bits)[1],
        "route_cross_xnor": lambda bits: not (route_pair(bits)[0] ^ route_pair(bits)[1]),
    }
    return {name: e031.signature(function) for name, function in functions.items()}


def metric(values):
    values = np.asarray(values, float)
    return {"mean": float(values.mean()), "unbiased_variance": float(values.var(ddof=1)), "n": len(values)}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    tasks = tasks_from_grammar()
    inputs, old_targets = base.inputs_and_targets()
    probes, evaluations = e024.task_signatures()
    earlier = set(inputs) | set(old_targets.values()) | set(probes.values()) | set(evaluations.values()) | set(e031.task_signatures().values())
    assert len(set(tasks.values())) == 6 and not (set(tasks.values()) & earlier)
    admitted, frozen_row = e028.frozen()
    seeds = list(range(1480, 1488))
    conditions = ("no_transfer", "admitted", "one_hop_barrier", "random_matched")
    forbidden = earlier | set(tasks.values()) | {admitted.signature}
    random_libraries = {}
    random_manifest = []
    used_random = set()
    for seed in seeds:
        for task_index, task in enumerate(tasks):
            candidate, draws = e031.random_matched(admitted, seed * 43 + task_index, forbidden | used_random)
            used_random.add(candidate.signature)
            random_libraries[seed, task] = candidate
            random_manifest.append({"seed": seed, "task": task, "signature": str(candidate.signature), "expression": candidate.expression, "cost": candidate.cost(), "draws": draws})
    (OUT / "frozen_manifest.json").write_text(json.dumps({"grammar_tasks": {task: str(target) for task, target in tasks.items()}, "admitted": frozen_row, "random_matched": random_manifest, "previous_task_signatures": sorted(str(value) for value in earlier)}, indent=2))

    records = []
    started = time.monotonic()
    with (OUT / "progress.jsonl").open("w") as progress:
        for seed in seeds:
            for task, target in tasks.items():
                for condition in conditions:
                    if condition == "no_transfer":
                        library = []
                    elif condition == "random_matched":
                        library = [random_libraries[seed, task]]
                    else:
                        library = [admitted]
                    row = e030.provenance_search(seed, target, library, barrier=condition == "one_hop_barrier")
                    row.pop("trace")
                    row.update({"seed": seed, "task": task, "family": "numeric" if task.startswith("numeric_") else "route", "condition": condition, "library_signatures": [str(candidate.signature) for candidate in library]})
                    records.append(row)
                    progress.write(json.dumps(row) + "\n")
                    progress.flush()
                    print(seed, task, condition, int(row["exact"]), row["best_error"], flush=True)

    aggregate = {}
    for task in tasks:
        aggregate[task] = {}
        for condition in conditions:
            rows = [row for row in records if row["task"] == task and row["condition"] == condition]
            aggregate[task][condition] = {"exact": metric([row["exact"] for row in rows]), "best_error": metric([row["best_error"] for row in rows]), "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]), "uses_transfer": sum(row["exact"] and row["uses_transfer"] for row in rows)}
    sources = (HERE / "main.py", HERE / "PROTOCOL.md", E031 / "main.py", E030 / "main.py", E028 / "main.py", E026 / "main.py", E026 / "run/admission.json", E024 / "main.py", E023 / "main.py", E019 / "search.py", E019 / "search_v2.py")
    result = {"records": records, "aggregate": aggregate, "settings": {"seeds": seeds, "tasks": list(tasks), "conditions": list(conditions), "beam": 128, "rounds": 6, "max_cost": 16}, "elapsed_seconds": time.monotonic() - started, "sources": {str(path.relative_to(ROOT)): sha(path) for path in sources}}
    (OUT / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({"aggregate": aggregate, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
