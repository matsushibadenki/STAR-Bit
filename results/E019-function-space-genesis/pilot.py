"""Run the preregistered E019 function-space pilot."""
import hashlib
import json
import time
from pathlib import Path

import numpy as np

import search

HERE = Path(__file__).resolve().parent
OUT = HERE / "pilot"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(values):
    values = np.asarray(values, float)
    return {"mean": float(values.mean()), "variance": float(values.var(ddof=1))}


def main():
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    records = []
    for seed in range(1200, 1204):
        for condition in ("target_greedy", "composition_pareto"):
            begin = time.monotonic()
            row = search.run(seed, condition)
            row["elapsed_seconds"] = time.monotonic() - begin
            records.append(row)
            (OUT / "progress.json").write_text(json.dumps(records, indent=2))
            print(seed, condition, row["exact_targets"], sorted(row["solutions"]), row["elapsed_seconds"], flush=True)
    aggregate = {}
    for condition in ("target_greedy", "composition_pareto"):
        group = [row for row in records if row["condition"] == condition]
        aggregate[condition] = {
            "exact_targets": metric([row["exact_targets"] for row in group]),
            "all_exact_seeds": sum(row["all_exact"] for row in group),
            "exact_by_task": {task: sum(task in row["solutions"] for row in group) for task in search.TASKS},
            "generated_unique_signatures": metric([row["generated_unique_signatures"] for row in group]),
            "equivalent_function_merges": metric([row["equivalent_function_merges"] for row in group]),
            "seconds": metric([row["elapsed_seconds"] for row in group]),
        }
    viable = aggregate["composition_pareto"]["all_exact_seeds"] >= 3 and aggregate["composition_pareto"]["exact_targets"]["mean"] > aggregate["target_greedy"]["exact_targets"]["mean"]
    result = {
        "records": records,
        "aggregate": aggregate,
        "viable": viable,
        "elapsed_seconds": time.monotonic() - started,
        "settings": {"seeds": list(range(1200, 1204)), "beam": 128, "rounds": 7, "max_cost": 14},
        "sources": {path.name: sha(path) for path in (Path(__file__), HERE / "search.py", HERE / "PILOT-PROTOCOL.md")},
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"aggregate": aggregate, "viable": viable, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
