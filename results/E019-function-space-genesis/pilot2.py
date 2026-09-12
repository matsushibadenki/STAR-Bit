"""Run the E019 affine-scaffold pilot."""
import hashlib
import json
import time
from pathlib import Path

import numpy as np

import search
import search_v2

HERE = Path(__file__).resolve().parent
OUT = HERE / "pilot2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(values):
    values = np.asarray(values, float)
    return {"mean": float(values.mean()), "variance": float(values.var(ddof=1))}


def main():
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    records = []
    for seed in range(1220, 1224):
        for condition in ("target_greedy", "affine_scaffold"):
            begin = time.monotonic()
            row = search_v2.run(seed, condition)
            row["elapsed_seconds"] = time.monotonic() - begin
            records.append(row)
            (OUT / "progress.json").write_text(json.dumps(records, indent=2))
            print(seed, condition, row["exact_targets"], sorted(row["solutions"]), row["elapsed_seconds"], flush=True)
    aggregate = {}
    for condition in ("target_greedy", "affine_scaffold"):
        group = [row for row in records if row["condition"] == condition]
        aggregate[condition] = {
            "exact_targets": metric([row["exact_targets"] for row in group]),
            "all_exact_seeds": sum(row["all_exact"] for row in group),
            "exact_by_task": {task: sum(task in row["solutions"] for row in group) for task in search.TASKS},
            "seconds": metric([row["elapsed_seconds"] for row in group]),
            "unique_signatures": metric([row["generated_unique_signatures"] for row in group]),
            "equivalent_merges": metric([row["equivalent_function_merges"] for row in group]),
        }
    viable = aggregate["affine_scaffold"]["all_exact_seeds"] >= 3 and aggregate["affine_scaffold"]["exact_targets"]["mean"] > aggregate["target_greedy"]["exact_targets"]["mean"]
    result = {
        "records": records,
        "aggregate": aggregate,
        "viable": viable,
        "elapsed_seconds": time.monotonic()-started,
        "settings": {"seeds": list(range(1220,1224)), "beam": 256, "rounds": 7, "max_cost": 14},
        "sources": {path.name: sha(path) for path in (Path(__file__), HERE / "search.py", HERE / "search_v2.py", HERE / "PILOT2-PROTOCOL.md")},
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"aggregate": aggregate, "viable": viable, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
