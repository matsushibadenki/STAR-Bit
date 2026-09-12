"""Run E017 pilot-3 discrete refinement."""
import hashlib
import json
import time
from pathlib import Path

import refine

HERE = Path(__file__).resolve().parent
OUT = HERE / "pilot3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    pilot2 = json.loads((HERE / "pilot2/results.json").read_text())
    starts = {(row["seed"], row["task"]): row for row in pilot2["selected_records"] if row["initialization"] == "diverse_tables"}
    records = []
    started = time.monotonic()
    for seed in range(920, 924):
        for task_index, task in enumerate(("parity", "comparator", "mux", "carry")):
            for condition in ("dlgn_start", "random_start"):
                if condition == "dlgn_start":
                    start = refine.from_spec(starts[seed, task]["spec"])
                else:
                    start = refine.random_genome(seed * 100 + task_index)
                best, metrics = refine.search(task, start, seed * 1000 + task_index * 10 + (condition == "random_start"))
                row = {"seed": seed, "task": task, "condition": condition, **metrics, "genome": best}
                records.append(row)
                (OUT / "progress.json").write_text(json.dumps(records, indent=2))
                print(seed, task, condition, metrics, flush=True)
    aggregate = {}
    for condition in ("dlgn_start", "random_start"):
        group = [row for row in records if row["condition"] == condition]
        aggregate[condition] = {
            "exact_runs": sum(row["exact"] for row in group),
            "exact_by_task": {task: sum(row["exact"] for row in group if row["task"] == task) for task in ("parity", "comparator", "mux", "carry")},
            "mean_initial_error": sum(row["initial_error"] for row in group) / len(group),
            "mean_final_error": sum(row["final_error"] for row in group) / len(group),
        }
    viable = all(value >= 3 for value in aggregate["dlgn_start"]["exact_by_task"].values())
    result = {
        "records": records,
        "aggregate": aggregate,
        "viable": viable,
        "elapsed_seconds": time.monotonic() - started,
        "sources": {path.name: sha(path) for path in (Path(__file__), HERE / "refine.py", HERE / "PILOT3-PROTOCOL.md", HERE / "pilot2/results.json")},
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"aggregate": aggregate, "viable": viable, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
