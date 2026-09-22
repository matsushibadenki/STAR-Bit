"""E037 independent-seed Function comparison on frozen numeric/route targets."""
import hashlib
import importlib.util
import json
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get("E037_OUT", str(HERE / "run")))
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
E036 = ROOT / "results/E036-beam-calibration"


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


e035 = load("e035_for_e037", E035 / "main.py")
e031 = e035.e033.e031
e030 = e031.e030
e028 = e031.e028
e024 = e031.e024
base = e031.base


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    route_selection = json.loads((E034 / "run/selected_task_budgets.json").read_text())["selected_pairs"]
    numeric_selection = json.loads((E036 / "run/selected_numeric_width.json").read_text())
    assert route_selection == [{"task": "route_cross_and", "family": "route", "round_budget": 4}]
    assert numeric_selection["selected_task"] == "numeric_symmetric_ge5" and numeric_selection["selected_numeric_width"] == 256
    targets = {"numeric_symmetric_ge5": e035.tasks_from_grammar()[1]["numeric_symmetric_ge5"], "route_cross_and": e035.e033.tasks_from_grammar()["route_cross_and"]}
    budgets = {"numeric_symmetric_ge5": {"beam": 256, "rounds": 6}, "route_cross_and": {"beam": 128, "rounds": 4}}
    admitted, frozen_function = e028.frozen()
    inputs, old_targets = base.inputs_and_targets()
    probes, evaluations = e024.task_signatures()
    forbidden = set(inputs) | set(old_targets.values()) | set(probes.values()) | set(evaluations.values()) | set(e031.task_signatures().values()) | set(e035.e033.tasks_from_grammar().values()) | set(e035.tasks_from_grammar()[1].values()) | {admitted.signature}
    seeds = list(range(1520, 1526))
    conditions = ["no_transfer", "admitted", "one_hop_barrier", "inert_slot", "random_matched"]
    random_libraries = {}
    random_manifest = []
    used_random = set()
    for seed in seeds:
        for task_index, task in enumerate(targets):
            candidate, draws = e031.random_matched(admitted, seed * 47 + task_index, forbidden | used_random)
            assert candidate.signature not in used_random and candidate.cost() == admitted.cost()
            used_random.add(candidate.signature)
            random_libraries[seed, task] = candidate
            random_manifest.append({"seed": seed, "task": task, "signature": str(candidate.signature), "expression": candidate.expression, "cost": candidate.cost(), "draws": draws})
    settings = {"seeds": seeds, "tasks": list(targets), "conditions": conditions, "budgets": budgets, "max_cost": 16}
    (OUT / "frozen_manifest.json").write_text(json.dumps({"settings": settings, "targets": {task: str(target) for task, target in targets.items()}, "admitted": frozen_function, "random_matched": random_manifest, "route_selection": route_selection, "numeric_selection": numeric_selection}, indent=2, allow_nan=False))
    records = []
    started = time.monotonic()
    with (OUT / "progress.jsonl").open("w") as progress:
        for seed in seeds:
            for task, target in targets.items():
                budget = budgets[task]
                for condition in conditions:
                    if time.monotonic() - started >= 900:
                        (OUT / "incomplete.json").write_text(json.dumps({"completed": len(records), "expected": 60, "elapsed_seconds": time.monotonic() - started}, indent=2))
                        return
                    library = [] if condition == "no_transfer" else [random_libraries[seed, task]] if condition == "random_matched" else [admitted]
                    if condition == "inert_slot":
                        row = e028.search_inert(seed, target, library, {admitted.signature}, beam_size=budget["beam"], rounds=budget["rounds"], max_cost=16)
                    else:
                        row = e030.provenance_search(seed, target, library, barrier=condition == "one_hop_barrier", beam_size=budget["beam"], rounds=budget["rounds"], max_cost=16)
                        row.pop("trace")
                    row.update({"seed": seed, "task": task, "family": "numeric" if task.startswith("numeric_") else "route", "condition": condition, "beam": budget["beam"], "round_budget": budget["rounds"], "library_signatures": [str(candidate.signature) for candidate in library]})
                    records.append(row)
                    progress.write(json.dumps(row, allow_nan=False) + "\n")
                    progress.flush()
                    print(seed, task, condition, int(row["exact"]), row["best_error"], flush=True)
    assert len(records) == 60
    sources = (HERE / "main.py", HERE / "PROTOCOL.md", E036 / "run/selected_numeric_width.json", E035 / "main.py", E035 / "run/frozen_tasks.json", E034 / "run/selected_task_budgets.json", E033 / "main.py", E031 / "main.py", E030 / "main.py", E028 / "main.py", E026 / "main.py", E026 / "run/admission.json", E024 / "main.py", E023 / "main.py", E019 / "search.py", E019 / "search_v2.py")
    result = {"records": records, "settings": settings, "elapsed_seconds": time.monotonic() - started, "sources": {str(path.relative_to(ROOT)): sha(path) for path in sources}}
    (OUT / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({"completed": len(records), "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
