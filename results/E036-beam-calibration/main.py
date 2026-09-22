"""E036 single-task baseline beam-width calibration."""
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get("E036_OUT", str(HERE / "run")))
E019 = ROOT / "results/E019-function-space-genesis"
E023 = ROOT / "results/E023-leave-one-task-out-transfer"
E024 = ROOT / "results/E024-probe-utility-diversity"
E026 = ROOT / "results/E026-counterfactual-admission"
E028 = ROOT / "results/E028-module-causal-ablation"
E030 = ROOT / "results/E030-provenance-barrier"
E031 = ROOT / "results/E031-route-family-portability"
E033 = ROOT / "results/E033-grammar-pilot"
E034 = ROOT / "results/E034-budget-calibration"
E035 = ROOT / "results/E035-numeric-grammar"


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


e035 = load("e035_for_e036", E035 / "main.py")
e026 = e035.e026


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    task = "numeric_symmetric_ge5"
    target = e035.tasks_from_grammar()[1][task]
    frozen_e035 = json.loads((E035 / "run/frozen_tasks.json").read_text())
    assert frozen_e035["signatures"][task] == str(target)
    route_selection = json.loads((E034 / "run/selected_task_budgets.json").read_text())["selected_pairs"]
    assert route_selection == [{"task": "route_cross_and", "family": "route", "round_budget": 4}]
    seeds = list(range(1510, 1516))
    widths = [64, 128, 192, 256]
    settings = {"seeds": seeds, "task": task, "target_signature": str(target), "beam_widths": widths, "rounds": 6, "max_cost": 16, "initial_library": []}
    (OUT / "frozen_settings.json").write_text(json.dumps({"settings": settings, "frozen_route_candidate": route_selection}, indent=2, allow_nan=False))
    records = []
    started = time.monotonic()
    with (OUT / "progress.jsonl").open("w") as progress:
        for seed in seeds:
            for width in widths:
                if time.monotonic() - started >= 900:
                    (OUT / "incomplete.json").write_text(json.dumps({"completed": len(records), "expected": 24, "elapsed_seconds": time.monotonic() - started}, indent=2))
                    return
                row = e026.search(seed, target, [], width, 6, max_cost=16, save_expression=True)
                row.update({"seed": seed, "task": task, "beam_width": width, "condition": "no_transfer", "library_signatures": []})
                records.append(row)
                progress.write(json.dumps(row, allow_nan=False) + "\n")
                progress.flush()
                print(seed, width, int(row["exact"]), row["best_error"], flush=True)
    assert len(records) == 24
    sources = (HERE / "main.py", HERE / "PROTOCOL.md", E035 / "main.py", E035 / "run/frozen_tasks.json", E034 / "run/selected_task_budgets.json", E033 / "main.py", E031 / "main.py", E030 / "main.py", E028 / "main.py", E026 / "main.py", E024 / "main.py", E023 / "main.py", E019 / "search.py", E019 / "search_v2.py")
    result = {"records": records, "settings": settings, "elapsed_seconds": time.monotonic() - started, "sources": {str(path.relative_to(ROOT)): sha(path) for path in sources}}
    (OUT / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({"completed": len(records), "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
