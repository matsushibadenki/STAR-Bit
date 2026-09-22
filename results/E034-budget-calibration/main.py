"""E034 baseline-only search-round calibration for E033's frozen task grammar."""
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get("E034_OUT", str(HERE / "run")))
E019 = ROOT / "results/E019-function-space-genesis"
E023 = ROOT / "results/E023-leave-one-task-out-transfer"
E024 = ROOT / "results/E024-probe-utility-diversity"
E026 = ROOT / "results/E026-counterfactual-admission"
E028 = ROOT / "results/E028-module-causal-ablation"
E030 = ROOT / "results/E030-provenance-barrier"
E031 = ROOT / "results/E031-route-family-portability"
E033 = ROOT / "results/E033-grammar-pilot"


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


e033 = load("e033_for_e034", E033 / "main.py")
e026 = e033.e031.e026


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metric(values):
    array = np.asarray(values, float)
    return {"mean": float(array.mean()), "unbiased_variance": float(array.var(ddof=1)), "n": len(array)}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    tasks = e033.tasks_from_grammar()
    frozen = json.loads((E033 / "run/frozen_manifest.json").read_text())["grammar_tasks"]
    assert {name: str(signature) for name, signature in tasks.items()} == frozen
    seeds = list(range(1490, 1496))
    round_budgets = (4, 6, 8)
    (OUT / "frozen_tasks.json").write_text(json.dumps({"tasks": frozen, "seeds": seeds, "round_budgets": round_budgets, "beam": 128, "max_cost": 16}, indent=2))
    records = []
    started = time.monotonic()
    with (OUT / "progress.jsonl").open("w") as progress:
        for seed in seeds:
            for task, target in tasks.items():
                for rounds in round_budgets:
                    row = e026.search(seed, target, [], 128, rounds, max_cost=16, save_expression=True)
                    row.update({"seed": seed, "task": task, "family": "numeric" if task.startswith("numeric_") else "route", "round_budget": rounds, "library_signatures": []})
                    records.append(row)
                    progress.write(json.dumps(row) + "\n")
                    progress.flush()
                    print(seed, task, rounds, int(row["exact"]), row["best_error"], flush=True)
    aggregate = {}
    for task in tasks:
        aggregate[task] = {}
        for rounds in round_budgets:
            subset = [row for row in records if row["task"] == task and row["round_budget"] == rounds]
            aggregate[task][str(rounds)] = {"exact": metric([row["exact"] for row in subset]), "best_error": metric([row["best_error"] for row in subset]), "generated_unique_signatures": metric([row["generated_unique_signatures"] for row in subset]), "elapsed_seconds": metric([row["elapsed_seconds"] for row in subset])}
    sources = (HERE / "main.py", HERE / "PROTOCOL.md", E033 / "main.py", E033 / "run/frozen_manifest.json", E031 / "main.py", E030 / "main.py", E028 / "main.py", E026 / "main.py", E024 / "main.py", E023 / "main.py", E019 / "search.py", E019 / "search_v2.py")
    result = {"records": records, "aggregate": aggregate, "settings": {"seeds": seeds, "tasks": list(tasks), "round_budgets": round_budgets, "beam": 128, "max_cost": 16, "initial_library": []}, "elapsed_seconds": time.monotonic() - started, "sources": {str(path.relative_to(ROOT)): sha(path) for path in sources}}
    (OUT / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({"aggregate": aggregate, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
