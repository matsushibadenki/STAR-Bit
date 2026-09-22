"""E035 baseline-only calibration of six predeclared weighted-sum targets."""
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get("E035_OUT", str(HERE / "run")))
E019 = ROOT / "results/E019-function-space-genesis"
E023 = ROOT / "results/E023-leave-one-task-out-transfer"
E024 = ROOT / "results/E024-probe-utility-diversity"
E026 = ROOT / "results/E026-counterfactual-admission"
E028 = ROOT / "results/E028-module-causal-ablation"
E030 = ROOT / "results/E030-provenance-barrier"
E031 = ROOT / "results/E031-route-family-portability"
E033 = ROOT / "results/E033-grammar-pilot"
E034 = ROOT / "results/E034-budget-calibration"


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


e033 = load("e033_for_e035", E033 / "main.py")
e026 = e033.e031.e026


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tasks_from_grammar():
    grammar = {
        "numeric_symmetric_ge5": ((1, 2, 3, 1, 2, 3), 5),
        "numeric_symmetric_ge6": ((1, 2, 3, 1, 2, 3), 6),
        "numeric_symmetric_ge7": ((1, 2, 3, 1, 2, 3), 7),
        "numeric_asymmetric_ge5": ((1, 2, 4, 1, 2, 3), 5),
        "numeric_asymmetric_ge6": ((1, 2, 4, 1, 2, 3), 6),
        "numeric_asymmetric_ge7": ((1, 2, 4, 1, 2, 3), 7),
    }
    signatures = {
        name: e033.e031.signature(lambda bits, w=weights, t=threshold: sum(bit * weight for bit, weight in zip(bits, w)) >= t)
        for name, (weights, threshold) in grammar.items()
    }
    return grammar, signatures


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    grammar, tasks = tasks_from_grammar()
    old = set(e033.e031.task_signatures().values()) | set(e033.tasks_from_grammar().values())
    assert len(set(tasks.values())) == 6 and not (set(tasks.values()) & old)
    route_selection = json.loads((E034 / "run/selected_task_budgets.json").read_text())
    assert route_selection["selected_pairs"] == [{"task": "route_cross_and", "family": "route", "round_budget": 4}]
    seeds = list(range(1500, 1506))
    settings = {"seeds": seeds, "tasks": list(tasks), "beam": 128, "rounds": 6, "max_cost": 16, "initial_library": []}
    (OUT / "frozen_tasks.json").write_text(json.dumps({"grammar": grammar, "signatures": {name: str(value) for name, value in tasks.items()}, "positive_class_counts": {name: value.bit_count() for name, value in tasks.items()}, "settings": settings, "frozen_route_candidate": route_selection["selected_pairs"]}, indent=2, allow_nan=False))
    records = []
    started = time.monotonic()
    with (OUT / "progress.jsonl").open("w") as progress:
        for seed in seeds:
            for task, target in tasks.items():
                if time.monotonic() - started >= 900:
                    (OUT / "incomplete.json").write_text(json.dumps({"completed": len(records), "expected": 36, "elapsed_seconds": time.monotonic() - started}, indent=2))
                    return
                row = e026.search(seed, target, [], 128, 6, max_cost=16, save_expression=True)
                row.update({"seed": seed, "task": task, "condition": "no_transfer", "library_signatures": []})
                records.append(row)
                progress.write(json.dumps(row, allow_nan=False) + "\n")
                progress.flush()
                print(seed, task, int(row["exact"]), row["best_error"], flush=True)
    assert len(records) == 36
    sources = (HERE / "main.py", HERE / "PROTOCOL.md", E034 / "run/selected_task_budgets.json", E033 / "main.py", E031 / "main.py", E030 / "main.py", E028 / "main.py", E026 / "main.py", E024 / "main.py", E023 / "main.py", E019 / "search.py", E019 / "search_v2.py")
    result = {"records": records, "settings": settings, "elapsed_seconds": time.monotonic() - started, "sources": {str(path.relative_to(ROOT)): sha(path) for path in sources}}
    (OUT / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({"completed": len(records), "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
