"""E038 timed admission against inert and same-cost random controls."""
import hashlib
import importlib.util
import json
import math
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get("E038_OUT", str(HERE / "run")))
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
E037 = ROOT / "results/E037-family-confirmation"


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


e037 = load("e037_for_e038", E037 / "main.py")
e031 = e037.e031
e026 = e031.e026
e024 = e037.e024
e028 = e037.e028
base = e037.base
features = e026.features
e023 = e031.e023


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def timed_search(seed, target, module, beam_size, rounds, mode, max_cost=16):
    assert mode in ("no_transfer", "early_learned", "late_learned", "late_inert", "late_random")
    assert (module is None) == (mode == "no_transfer")
    inputs, _ = base.inputs_and_targets()
    beam = [base.Candidate(signature, 0, 0, 0, ("input", index)) for index, signature in enumerate(inputs)]
    if mode == "early_learned":
        beam.append(module)
    library_signatures = set() if module is None else {module.signature}
    credit, partners, last = {}, {}, {}
    solution = None
    best = 64
    history = []
    first_round_selected = []
    generated = len(beam)
    injection_round = 1 if mode == "early_learned" else None
    injected_collision = False
    slot_replaced_signature = None
    started = time.monotonic()
    for round_index in range(1, rounds + 1):
        pool = {candidate.signature: candidate for candidate in beam}
        edges = []
        for index, left in enumerate(beam):
            for right in beam[index:]:
                if mode == "late_inert" and (left.signature == module.signature or right.signature == module.signature):
                    continue
                primitives = left.primitives + right.primitives + 1
                if primitives > max_cost:
                    continue
                routing = left.routing_bits + right.routing_bits + 2 * math.ceil(math.log2(6 + max(1, primitives)))
                depth = max(left.depth, right.depth) + 1
                for code, signature in enumerate(base.lut_outputs(left.signature, right.signature)):
                    candidate = base.Candidate(signature, primitives, routing, depth, ("lut", signature, code, left.expression, right.expression))
                    old = pool.get(signature)
                    if old is None:
                        pool[signature] = candidate
                        generated += 1
                    elif base.better(candidate, old):
                        pool[signature] = candidate
                    if signature not in (left.signature, right.signature):
                        edges.append((signature, left, right))
        best = min(best, min(base.error(signature, target) for signature in pool))
        history.append(best)
        if target in pool:
            solution = pool[target]
            break
        top = {candidate.signature for candidate in sorted(pool.values(), key=lambda candidate: (base.error(candidate.signature, target), *candidate.cost(), e026.stable(candidate.signature, seed, round_index)))[:128]}
        for signature, left, right in edges:
            novelty = max(0, features.support_mask(signature).bit_count() - max(features.support_mask(left.signature).bit_count(), features.support_mask(right.signature).bit_count())) if 0 < signature.bit_count() < 64 else 0
            for parent, other in ((left, right), (right, left)):
                amount = novelty + (max(0, min(base.error(parent.signature, target), base.error(other.signature, target)) - base.error(signature, target)) if signature in top else 0)
                if amount:
                    credit[parent.signature] = credit.get(parent.signature, 0) + amount
                    partners.setdefault(parent.signature, set()).add(other.signature)
                    last[parent.signature] = round_index
        for signature in [signature for signature, last_seen in last.items() if round_index - last_seen > 2]:
            credit.pop(signature, None)
            partners.pop(signature, None)
            last.pop(signature, None)
        beam = e026.select(pool, target, beam_size, seed, round_index, credit, partners, last)
        if round_index == 1:
            first_round_selected = [str(candidate.signature) for candidate in beam]
            if mode.startswith("late_"):
                assert beam
                collision_index = next((index for index, candidate in enumerate(beam) if candidate.signature == module.signature), None)
                injected_collision = collision_index is not None
                replace_index = collision_index if collision_index is not None else len(beam) - 1
                slot_replaced_signature = str(beam[replace_index].signature)
                beam[replace_index] = module
                if not injected_collision:
                    generated += 1
                injection_round = 2
    used = [] if solution is None else sorted(e023.expression_signatures(solution.expression) & library_signatures)
    return {"exact": solution is not None, "round": None if solution is None else round_index, "best_error": best, "best_error_history": history, "uses_transfer": bool(used), "used_signatures": [str(signature) for signature in used], "expression": None if solution is None else solution.expression, "primitives": None if solution is None else solution.primitives, "routing_bits": None if solution is None else solution.routing_bits, "depth": None if solution is None else solution.depth, "generated_unique_signatures": generated, "elapsed_seconds": time.monotonic() - started, "first_round_selected": first_round_selected, "injection_round": injection_round, "injected_collision": injected_collision, "slot_replaced_signature": slot_replaced_signature}


def smoke(admitted):
    _, evaluations = e024.task_signatures()
    target = evaluations["eval_dual_mux_xor"]
    checks = {}
    for condition, module in (("no_transfer", None), ("early_learned", admitted)):
        new = timed_search(19000, target, module, 64, 2, condition)
        old = e026.search(19000, target, [] if module is None else [module], 64, 2, save_expression=True)
        keys = ("exact", "round", "best_error_history", "generated_unique_signatures", "expression", "uses_transfer")
        assert all(new[key] == old[key] for key in keys), condition
        checks[condition] = {"seed": 19000, "rounds": 2, "matched_keys": list(keys)}
    return checks


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    frozen_e037 = json.loads((E037 / "run/frozen_manifest.json").read_text())
    targets = {task: int(value) for task, value in frozen_e037["targets"].items()}
    budgets = frozen_e037["settings"]["budgets"]
    assert list(targets) == ["numeric_symmetric_ge5", "route_cross_and"]
    assert budgets == {"numeric_symmetric_ge5": {"beam": 256, "rounds": 6}, "route_cross_and": {"beam": 128, "rounds": 4}}
    admitted, frozen_function = e028.frozen()
    assert frozen_e037["admitted"] == json.loads(json.dumps(frozen_function))
    (OUT / "smoke.json").write_text(json.dumps(smoke(admitted), indent=2))
    inputs, old_targets = base.inputs_and_targets()
    probes, evaluations = e024.task_signatures()
    forbidden = set(inputs) | set(old_targets.values()) | set(probes.values()) | set(evaluations.values()) | set(e031.task_signatures().values()) | set(e037.e035.e033.tasks_from_grammar().values()) | set(e037.e035.tasks_from_grammar()[1].values()) | {admitted.signature}
    seeds = list(range(1530, 1536))
    conditions = ["no_transfer", "early_learned", "late_learned", "late_inert", "late_random"]
    random_libraries = {}
    random_manifest = []
    used_random = set()
    for seed in seeds:
        for task_index, task in enumerate(targets):
            candidate, draws = e031.random_matched(admitted, seed * 53 + task_index, forbidden | used_random)
            assert candidate.signature not in used_random and candidate.cost() == admitted.cost()
            used_random.add(candidate.signature)
            random_libraries[seed, task] = candidate
            random_manifest.append({"seed": seed, "task": task, "signature": str(candidate.signature), "expression": candidate.expression, "cost": candidate.cost(), "draws": draws})
    settings = {"seeds": seeds, "tasks": list(targets), "conditions": conditions, "budgets": budgets, "max_cost": 16}
    (OUT / "frozen_manifest.json").write_text(json.dumps({"settings": settings, "targets": {task: str(target) for task, target in targets.items()}, "admitted": frozen_function, "random_matched": random_manifest, "source_task_selection": {"numeric": "E036", "route": "E034"}}, indent=2, allow_nan=False))
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
                    module = None if condition == "no_transfer" else random_libraries[seed, task] if condition == "late_random" else admitted
                    row = timed_search(seed, target, module, budget["beam"], budget["rounds"], condition)
                    row.update({"seed": seed, "task": task, "family": "numeric" if task.startswith("numeric_") else "route", "condition": condition, "beam": budget["beam"], "round_budget": budget["rounds"], "library_signatures": [] if module is None else [str(module.signature)]})
                    records.append(row)
                    progress.write(json.dumps(row, allow_nan=False) + "\n")
                    progress.flush()
                    print(seed, task, condition, int(row["exact"]), row["best_error"], flush=True)
    assert len(records) == 60
    sources = (HERE / "main.py", HERE / "PROTOCOL.md", E037 / "run/frozen_manifest.json", E037 / "main.py", E036 / "run/selected_numeric_width.json", E035 / "main.py", E034 / "run/selected_task_budgets.json", E033 / "main.py", E031 / "main.py", E030 / "main.py", E028 / "main.py", E026 / "main.py", E026 / "run/admission.json", E024 / "main.py", E023 / "main.py", E019 / "search.py", E019 / "search_v2.py")
    result = {"records": records, "settings": settings, "elapsed_seconds": time.monotonic() - started, "sources": {str(path.relative_to(ROOT)): sha(path) for path in sources}}
    (OUT / "results.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({"completed": len(records), "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
