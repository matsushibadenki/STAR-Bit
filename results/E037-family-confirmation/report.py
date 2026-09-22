"""Audit E037 and analyze the preregistered task-specific Function comparison."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "run"
sys.path.insert(0, str(ROOT / "results/E019-function-space-genesis"))
import search as base


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


e037 = load("e037_for_report", HERE / "main.py")


def strict_json(content):
    return json.loads(content, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(expression, inputs):
    if expression[0] == "input":
        return inputs[expression[1]]
    signature = base.lut_outputs(evaluate(expression[3], inputs), evaluate(expression[4], inputs))[expression[2]]
    assert signature == int(expression[1])
    return signature


def metric(values):
    values = np.asarray(values, float)
    return {"mean": None if len(values) == 0 else float(values.mean()), "unbiased_variance": None if len(values) < 2 else float(values.var(ddof=1)), "n": len(values)}


def signflip(values):
    values = np.asarray(values, float)
    observed = abs(values.mean())
    extreme = 0
    for mask in range(1 << len(values)):
        signed = [value if mask & (1 << index) else -value for index, value in enumerate(values)]
        extreme += abs(np.mean(signed)) >= observed - 1e-12
    return extreme / (1 << len(values))


def paired(values, rng):
    values = np.asarray(values, float)
    samples = values[rng.integers(0, len(values), (20000, len(values)))].mean(axis=1)
    sd = values.std(ddof=1)
    return {"mean": float(values.mean()), "unbiased_variance": float(values.var(ddof=1)), "ci95": np.quantile(samples, [.025, .975]).tolist(), "cohen_dz": None if sd == 0 else float(values.mean() / sd), "exact_signflip_p": signflip(values), "differences": values.tolist()}


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


result = strict_json((OUT / "results.json").read_text())
seeds = list(range(1520, 1526))
numeric = "numeric_symmetric_ge5"
route = "route_cross_and"
tasks = [numeric, route]
conditions = ["no_transfer", "admitted", "one_hop_barrier", "inert_slot", "random_matched"]
budgets = {numeric: {"beam": 256, "rounds": 6}, route: {"beam": 128, "rounds": 4}}
assert result["settings"] == {"seeds": seeds, "tasks": tasks, "conditions": conditions, "budgets": budgets, "max_cost": 16}
assert len(result["records"]) == 60
assert len({(row["seed"], row["task"], row["condition"]) for row in result["records"]}) == 60
assert [strict_json(line) for line in (OUT / "progress.jsonl").read_text().splitlines()] == result["records"]
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected, name
frozen = strict_json((OUT / "frozen_manifest.json").read_text())
assert frozen["settings"] == result["settings"]
target_signatures = {numeric: e037.e035.tasks_from_grammar()[1][numeric], route: e037.e035.e033.tasks_from_grammar()[route]}
assert frozen["targets"] == {name: str(value) for name, value in target_signatures.items()}
assert frozen["route_selection"] == [{"task": route, "family": "route", "round_budget": 4}]
assert frozen["numeric_selection"]["selected_task"] == numeric and frozen["numeric_selection"]["selected_numeric_width"] == 256
admitted, frozen_function = e037.e028.frozen()
assert frozen["admitted"] == json.loads(json.dumps(frozen_function))
assert len(frozen["random_matched"]) == 12
random_by = {(item["seed"], item["task"]): item for item in frozen["random_matched"]}
assert len(random_by) == 12
assert len({item["signature"] for item in frozen["random_matched"]}) == 12
for item in frozen["random_matched"]:
    assert tuple(item["cost"]) == admitted.cost()
    assert e037.e031.e023.evaluate(item["expression"], base.inputs_and_targets()[0]) == int(item["signature"])
    assert e037.e031.e023.expression_cost(item["expression"]) == admitted.cost()
    assert int(item["signature"]) not in set(target_signatures.values()) | {admitted.signature}

inputs, _ = base.inputs_and_targets()
verified = 0
for row in result["records"]:
    assert row["beam"] == budgets[row["task"]]["beam"] and row["round_budget"] == budgets[row["task"]]["rounds"]
    assert row["family"] == ("numeric" if row["task"] == numeric else "route")
    expected_library = [] if row["condition"] == "no_transfer" else [random_by[row["seed"], row["task"]]["signature"]] if row["condition"] == "random_matched" else [str(admitted.signature)]
    assert row["library_signatures"] == expected_library
    if row["condition"] in ("no_transfer", "inert_slot"):
        assert not row["uses_transfer"]
    if row["expression"] is not None:
        assert row["exact"] and evaluate(row["expression"], inputs) == target_signatures[row["task"]]
        verified += 1
assert verified == sum(int(row["exact"]) for row in result["records"])

by = {(row["seed"], row["task"], row["condition"]): row for row in result["records"]}
summary = {"by_task_condition": {}, "primary_interaction": {}, "secondary_exact": {}, "holm_secondary": {}, "primary_gate_passed": False, "one_hop_specific_gate_passed": False, "records_verified": 60, "solutions_verified": verified, "analysis_source_hash": sha(HERE / "report.py")}
summary["numeric_seedwise_performance_identity"] = {
    "barrier_vs_inert": sum(by[seed, numeric, "one_hop_barrier"]["exact"] == by[seed, numeric, "inert_slot"]["exact"] and by[seed, numeric, "one_hop_barrier"]["best_error"] == by[seed, numeric, "inert_slot"]["best_error"] for seed in seeds),
    "inert_vs_no_transfer": sum(by[seed, numeric, "inert_slot"]["exact"] == by[seed, numeric, "no_transfer"]["exact"] and by[seed, numeric, "inert_slot"]["best_error"] == by[seed, numeric, "no_transfer"]["best_error"] for seed in seeds),
}
for task in tasks:
    summary["by_task_condition"][task] = {}
    for condition in conditions:
        rows = [by[seed, task, condition] for seed in seeds]
        summary["by_task_condition"][task][condition] = {"exact": metric([row["exact"] for row in rows]), "best_error": metric([row["best_error"] for row in rows]), "generated_unique_signatures": metric([row["generated_unique_signatures"] for row in rows]), "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]), "solution_primitives": metric([row["primitives"] for row in rows if row["exact"]]), "solution_routing_bits": metric([row["routing_bits"] for row in rows if row["exact"]]), "solution_depth": metric([row["depth"] for row in rows if row["exact"]]), "exact_uses_transfer": sum(bool(row["exact"] and row["uses_transfer"]) for row in rows)}

rng = np.random.default_rng(2037)
def delta(seed, task, left, right):
    return int(by[seed, task, left]["exact"]) - int(by[seed, task, right]["exact"])

interaction = [delta(seed, numeric, "one_hop_barrier", "admitted") - delta(seed, route, "one_hop_barrier", "admitted") for seed in seeds]
summary["primary_interaction"] = paired(interaction, rng)
summary["primary_gate_passed"] = summary["primary_interaction"]["mean"] >= .25 and summary["primary_interaction"]["exact_signflip_p"] <= .05
comparisons = [(numeric, "one_hop_barrier", "admitted"), (numeric, "one_hop_barrier", "inert_slot"), (route, "one_hop_barrier", "admitted"), (route, "admitted", "random_matched")]
keys = []
for task, left, right in comparisons:
    key = f"{task}:{left}-minus-{right}"
    keys.append(key)
    summary["secondary_exact"][key] = paired([delta(seed, task, left, right) for seed in seeds], rng)
summary["holm_secondary"] = {key: value for key, value in zip(keys, holm([summary["secondary_exact"][key]["exact_signflip_p"] for key in keys]))}
specific_key = f"{numeric}:one_hop_barrier-minus-inert_slot"
summary["one_hop_specific_gate_passed"] = summary["secondary_exact"][specific_key]["mean"] > 0 and summary["holm_secondary"][specific_key] <= .05
(OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False))

lines = ["# E037：凍結した数値・経路候補でFunction条件を独立シード確認", "", "実行日：2026-09-22。E034のroute`cross_and@beam128/4round`とE036のnumeric`symmetric_ge5@beam256/6round`を凍結し、新規6 seedで5条件を各task内同一予算で比較した。計60探索。FunctionもE026の採用1件を再学習せず凍結した。", "", "| task | 条件 | exact/6 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | 使用した成功式/成功数 | 秒/探索平均 | 成功式 primitive / routing bits / depth平均 |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
for task in tasks:
    for condition in conditions:
        item = summary["by_task_condition"][task][condition]
        count = round(item["exact"]["mean"] * 6)
        cost = "NA" if item["solution_primitives"]["mean"] is None else f"{item['solution_primitives']['mean']:.2f} / {item['solution_routing_bits']['mean']:.2f} / {item['solution_depth']['mean']:.2f}"
        lines.append(f"| {task} | {condition} | {count}/6 | {item['exact']['mean']:.4f} / {item['exact']['unbiased_variance']:.4f} | {item['best_error']['mean']:.3f} / {item['best_error']['unbiased_variance']:.3f} | {item['exact_uses_transfer']}/{count} | {item['elapsed_seconds']['mean']:.2f} | {cost} |")
lines += ["", "## 事前主仮説", "", "主指標は`(barrier−admitted)_numeric − (barrier−admitted)_route`のseed対応exact差。タスク別の探索費用が異なるため、これは凍結設定での比較であり、一般的な数値対経路の因果差とは解釈しない。", ""]
primary = summary["primary_interaction"]
effect = "NA" if primary["cohen_dz"] is None else f"{primary['cohen_dz']:.3f}"
lines += [f"平均差 {primary['mean']:+.4f}、不偏分散 {primary['unbiased_variance']:.4f}、bootstrap 95% CI [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}]、Cohen dz {effect}、two-sided exact sign-flip p={primary['exact_signflip_p']:.4f}。事前の方向性確認基準（平均≥+0.25、p≤0.05）は" + ("達成。" if summary["primary_gate_passed"] else "未達。"), "", "## 副次比較（4比較Holm補正）", "", "| 比較 | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |", "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
for key in keys:
    item = summary["secondary_exact"][key]
    effect = "NA" if item["cohen_dz"] is None else f"{item['cohen_dz']:.3f}"
    lines.append(f"| {key} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {effect} | {item['exact_signflip_p']:.4f} | {summary['holm_secondary'][key]:.4f} |")
lines += ["", "one-hop固有の利益判定（数値barrier−inertが正かつHolm p≤0.05）は" + ("達成。" if summary["one_hop_specific_gate_passed"] else "未達。"), "", "各条件の生成unique signature数（平均 / 不偏分散）：", ""]
lines.insert(lines.index("各条件の生成unique signature数（平均 / 不偏分散）："), "数値taskではbarrierとinert、inertと移植なしが、どちらも6/6 seedでexact・best error一致。学習Functionを含む成功式は0件で、Functionの直接部品再利用は確認できない。")
for task in tasks:
    for condition in conditions:
        item = summary["by_task_condition"][task][condition]["generated_unique_signatures"]
        lines.append(f"- {task} / {condition}: {item['mean']:.1f} / {item['unbiased_variance']:.1f}。")
lines += ["", f"全{verified}件のexact式を64入力で再評価した。60 unique record、progress一致、strict JSON、source hash、12 random Functionの費用・signatureを監査した。", "", "## Roadmap", "", "- [Done] baselineだけで凍結した両taskを独立seedと同task内同予算で5条件比較した。", "- [Next] 結果の原因を、Functionの直接使用、beam摂動、inertとの違い、探索計算量から分けて検討する。", "- [Later] 複数taskへの拡張後、費用付きadmission、State形成・分解、負荷分散Routerへ進む。", "", "English: E037 compares five Function controls on fresh seeds for two frozen task/budget settings. Any interaction is limited to those settings because compute budgets differ across task families.", "", "简体中文：E037在新种子上比较两个冻结任务／预算设置的五个函数对照。由于任务族间计算预算不同，交互作用的解释仅限这些设置。", "", "[事前計画](../results/E037-family-confirmation/PROTOCOL.md) / [生データ](../results/E037-family-confirmation/run/results.json) / [凍結設定](../results/E037-family-confirmation/run/frozen_manifest.json) / [監査](../results/E037-family-confirmation/run/audit_summary.json)"]
report = "\n".join(lines) + "\n"
(ROOT / "docs/STAR-Bit-E037-family-confirmation.md").write_text(report)
(HERE / "REPORT.md").write_text(report.replace("(../results/E037-family-confirmation/", "("))
print(json.dumps({"primary_gate_passed": summary["primary_gate_passed"], "one_hop_specific_gate_passed": summary["one_hop_specific_gate_passed"], "verified": verified, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))
