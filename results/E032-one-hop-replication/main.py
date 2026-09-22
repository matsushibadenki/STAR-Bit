"""E032 independent-seed one-hop replication with an inert-slot control."""
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get("E032_OUT", str(HERE / "run")))
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


e031 = load("e031_for_e032", E031 / "main.py")
e030 = e031.e030
e028 = e031.e028
e026 = e031.e026
e024 = e031.e024
e023 = e031.e023
base = e031.base


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(values):
    values = np.asarray(values, float)
    return {"mean": float(values.mean()), "unbiased_variance": float(values.var(ddof=1)), "n": len(values)}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    admitted, frozen_row = e028.frozen()
    all_tasks = e031.task_signatures()
    tasks = {name: all_tasks[name] for name in ("numeric_unsigned_sum_ge6", "route_dual_mux_xnor")}
    seeds = list(range(1460, 1476))
    conditions = ("no_transfer", "admitted", "one_hop_barrier", "inert_slot", "random_matched")
    inputs, old_targets = base.inputs_and_targets()
    probes, evaluations = e024.task_signatures()
    forbidden = set(inputs) | set(old_targets.values()) | set(probes.values()) | set(evaluations.values()) | set(all_tasks.values()) | {admitted.signature}
    random_libraries = {}
    random_manifest = []
    used_random = set()
    for seed in seeds:
        for task_index, task in enumerate(tasks):
            candidate, draws = e031.random_matched(admitted, seed * 41 + task_index, forbidden | used_random)
            assert candidate.signature not in used_random
            used_random.add(candidate.signature)
            random_libraries[seed, task] = candidate
            random_manifest.append({"seed": seed, "task": task, "signature": str(candidate.signature), "expression": candidate.expression, "cost": candidate.cost(), "draws": draws})
    (OUT / "frozen_manifest.json").write_text(json.dumps({"admitted": frozen_row, "tasks": {task: str(target) for task, target in tasks.items()}, "random_matched": random_manifest}, indent=2))

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
                    if condition == "inert_slot":
                        row = e028.search_inert(seed, target, library, {admitted.signature})
                    else:
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
