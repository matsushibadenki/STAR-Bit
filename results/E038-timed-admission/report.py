"""Audit E038 and analyze the exploratory timed-admission pilot."""
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


e038 = load("e038_for_report", HERE / "main.py")


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
seeds = list(range(1530, 1536))
numeric = "numeric_symmetric_ge5"
route = "route_cross_and"
tasks = [numeric, route]
conditions = ["no_transfer", "early_learned", "late_learned", "late_inert", "late_random"]
budgets = {numeric: {"beam": 256, "rounds": 6}, route: {"beam": 128, "rounds": 4}}
assert result["settings"] == {"seeds": seeds, "tasks": tasks, "conditions": conditions, "budgets": budgets, "max_cost": 16}
assert len(result["records"]) == 60
assert len({(row["seed"], row["task"], row["condition"]) for row in result["records"]}) == 60
assert [strict_json(line) for line in (OUT / "progress.jsonl").read_text().splitlines()] == result["records"]
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected, name
frozen = strict_json((OUT / "frozen_manifest.json").read_text())
assert frozen["settings"] == result["settings"]
targets = {task: int(value) for task, value in frozen["targets"].items()}
assert list(targets) == tasks
admitted, frozen_function = e038.e028.frozen()
assert frozen["admitted"] == strict_json(json.dumps(frozen_function))
smoke = strict_json((OUT / "smoke.json").read_text())
assert smoke == e038.smoke(admitted)
assert len(frozen["random_matched"]) == 12
random_by = {(item["seed"], item["task"]): item for item in frozen["random_matched"]}
assert len(random_by) == 12 and len({item["signature"] for item in frozen["random_matched"]}) == 12
inputs, _ = base.inputs_and_targets()
for item in frozen["random_matched"]:
    assert tuple(item["cost"]) == admitted.cost()
    assert e038.e023.evaluate(item["expression"], inputs) == int(item["signature"])
    assert e038.e023.expression_cost(item["expression"]) == admitted.cost()
    assert int(item["signature"]) not in set(targets.values()) | {admitted.signature} | set(inputs)

by = {(row["seed"], row["task"], row["condition"]): row for row in result["records"]}
verified = 0
for row in result["records"]:
    assert row["beam"] == budgets[row["task"]]["beam"] and row["round_budget"] == budgets[row["task"]]["rounds"]
    assert row["family"] == ("numeric" if row["task"] == numeric else "route")
    expected_library = [] if row["condition"] == "no_transfer" else [random_by[row["seed"], row["task"]]["signature"]] if row["condition"] == "late_random" else [str(admitted.signature)]
    assert row["library_signatures"] == expected_library
    if row["condition"] in ("no_transfer", "late_inert"):
        assert not row["uses_transfer"]
    if row["expression"] is not None:
        assert row["exact"] and evaluate(row["expression"], inputs) == targets[row["task"]]
        verified += 1
assert verified == sum(int(row["exact"]) for row in result["records"])
late_conditions = ("late_learned", "late_inert", "late_random")
first_round_equal = 0
inserted = 0
collisions = 0
for seed in seeds:
    for task in tasks:
        reference = by[seed, task, "no_transfer"]
        assert reference["injection_round"] is None
        assert by[seed, task, "early_learned"]["injection_round"] == 1
        for condition in late_conditions:
            row = by[seed, task, condition]
            assert row["best_error_history"][0] == reference["best_error_history"][0]
            assert row["first_round_selected"] == reference["first_round_selected"]
            first_round_equal += 1
            if reference["round"] == 1:
                assert row["injection_round"] is None and row["slot_replaced_signature"] is None
            else:
                assert row["injection_round"] == 2 and row["slot_replaced_signature"] is not None
                inserted += 1
            collisions += int(row["injected_collision"])

summary = {"by_task_condition": {}, "primary": {}, "secondary": {}, "holm_secondary": {}, "timing_gate_passed": False, "function_specific_gate_passed": False, "records_verified": 60, "solutions_verified": verified, "first_round_pairs_verified": first_round_equal, "late_injections": inserted, "injection_collisions": collisions, "analysis_source_hash": sha(HERE / "report.py")}
for task in tasks:
    summary["by_task_condition"][task] = {}
    for condition in conditions:
        rows = [by[seed, task, condition] for seed in seeds]
        summary["by_task_condition"][task][condition] = {"exact": metric([row["exact"] for row in rows]), "best_error": metric([row["best_error"] for row in rows]), "generated_unique_signatures": metric([row["generated_unique_signatures"] for row in rows]), "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]), "solution_primitives": metric([row["primitives"] for row in rows if row["exact"]]), "solution_routing_bits": metric([row["routing_bits"] for row in rows if row["exact"]]), "solution_depth": metric([row["depth"] for row in rows if row["exact"]]), "exact_uses_transfer": sum(bool(row["exact"] and row["uses_transfer"]) for row in rows)}

rng = np.random.default_rng(2038)
def delta(seed, task, left, right):
    return int(by[seed, task, left]["exact"]) - int(by[seed, task, right]["exact"])

summary["primary"] = paired([sum(delta(seed, task, "late_learned", "early_learned") for task in tasks) / len(tasks) for seed in seeds], rng)
summary["timing_gate_passed"] = bool(summary["primary"]["mean"] >= .25 and summary["primary"]["exact_signflip_p"] <= .05)
contrast_values = {
    "numeric:late-minus-early": [delta(seed, numeric, "late_learned", "early_learned") for seed in seeds],
    "route:late-minus-early": [delta(seed, route, "late_learned", "early_learned") for seed in seeds],
    "pooled:late-learned-minus-inert": [sum(delta(seed, task, "late_learned", "late_inert") for task in tasks) / len(tasks) for seed in seeds],
    "pooled:late-learned-minus-random": [sum(delta(seed, task, "late_learned", "late_random") for task in tasks) / len(tasks) for seed in seeds],
}
for key, values in contrast_values.items():
    summary["secondary"][key] = paired(values, rng)
summary["holm_secondary"] = {key: value for key, value in zip(contrast_values, holm([summary["secondary"][key]["exact_signflip_p"] for key in contrast_values]))}
specific = "pooled:late-learned-minus-inert"
learned_uses = sum(summary["by_task_condition"][task][condition]["exact_uses_transfer"] for task in tasks for condition in ("early_learned", "late_learned"))
summary["learned_success_uses"] = learned_uses
summary["function_specific_gate_passed"] = bool(summary["secondary"][specific]["mean"] > 0 and summary["holm_secondary"][specific] <= .05 and learned_uses > 0)
(OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False))

lines = ["# E038：Functionの投入時刻を変える機構Pilot", "", "実行日：2026-09-22。E037で結果を見た2 taskをそのまま用いる探索的な機構実験。新規6 seedで移植なし／初回学習Function／初回探索後の学習Function・inert・同費用randomを比較した。各task内のbeamとround上限は固定し、遅延投入では選択済みbeamの最後の1枠を置換した。計60探索。新taskでの独立確認ではない。", "", "| task | 条件 | exact/6 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | Function使用成功/成功数 | 秒/探索平均 | 成功式 primitive / routing bits / depth平均 |", "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
for task in tasks:
    for condition in conditions:
        item = summary["by_task_condition"][task][condition]
        count = round(item["exact"]["mean"] * 6)
        cost = "NA" if item["solution_primitives"]["mean"] is None else f"{item['solution_primitives']['mean']:.2f} / {item['solution_routing_bits']['mean']:.2f} / {item['solution_depth']['mean']:.2f}"
        lines.append(f"| {task} | {condition} | {count}/6 | {item['exact']['mean']:.4f} / {item['exact']['unbiased_variance']:.4f} | {item['best_error']['mean']:.3f} / {item['best_error']['unbiased_variance']:.3f} | {item['exact_uses_transfer']}/{count} | {item['elapsed_seconds']['mean']:.2f} | {cost} |")
primary = summary["primary"]
effect = "NA" if primary["cohen_dz"] is None else f"{primary['cohen_dz']:.3f}"
lines += ["", "## 事前主指標：両task平均の遅延−初回exact差", "", f"平均差 {primary['mean']:+.4f}、不偏分散 {primary['unbiased_variance']:.4f}、bootstrap 95% CI [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}]、Cohen dz {effect}、two-sided exact sign-flip p={primary['exact_signflip_p']:.4f}。方向性pilot基準（平均≥+0.25かつp≤0.05）は" + ("達成。" if summary["timing_gate_passed"] else "未達。"), "", "## 副次exact比較（4比較Holm補正）", "", "| 比較 | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |", "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
for key, item in summary["secondary"].items():
    effect = "NA" if item["cohen_dz"] is None else f"{item['cohen_dz']:.3f}"
    lines.append(f"| {key} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {effect} | {item['exact_signflip_p']:.4f} | {summary['holm_secondary'][key]:.4f} |")
lines += ["", "学習Function固有の利益基準（遅延学習−遅延inertが正でHolm p≤0.05、かつ学習signatureを使う成功式≥1）は" + ("達成。" if summary["function_specific_gate_passed"] else "未達。"), f"遅延条件36対の初回beamとbest errorを移植なしと照合した。実際のround 2投入は{inserted}/36、signature衝突は{collisions}件。", "", "生成unique signature数（平均 / 不偏分散）：", ""]
for task in tasks:
    for condition in conditions:
        item = summary["by_task_condition"][task][condition]["generated_unique_signatures"]
        lines.append(f"- {task} / {condition}: {item['mean']:.1f} / {item['unbiased_variance']:.1f}。")
lines += ["", f"全{verified}件のexact式を64入力で再評価した。60 unique record、progress一致、strict JSON、source hash、12 random Functionの費用・signature、別seed smokeを監査した。54件後の実行session中断から凍結設定を変えず残り6件を再開し、探索ごとのCPU時間合計は{result['elapsed_seconds']:.1f}秒だった。探索時間やsignature数は推論の実測速度や物理ゲート数ではない。", "", "## Roadmap", "", "- [Done] 投入時刻を変え、同時刻inert・randomとの違いを新シードで探索的に測った。", "- [Next] timing効果の有無と最終式のFunction使用を分け、新しいtaskを事前固定して移植性を確認する。", "- [Later] 費用付きLibrary形成・分解とState、負荷分散Router、固定random経路、Expert交換へ進む。", "", "English: E038 is an exploratory timing study on two previously inspected tasks. A timing change alone does not establish transferable learned-Function benefit; the matched inert and random controls and final-expression usage separate those mechanisms.", "", "简体中文：E038是在两个先前已检视任务上的探索性投入时序实验。仅改变时序不能证明学习函数的可迁移收益；同时间的惰性和随机对照及最终表达式使用情况用于区分机制。", "", "[事前計画](../results/E038-timed-admission/PROTOCOL.md) / [生データ](../results/E038-timed-admission/run/results.json) / [凍結設定](../results/E038-timed-admission/run/frozen_manifest.json) / [監査](../results/E038-timed-admission/run/audit_summary.json)"]
report = "\n".join(lines) + "\n"
(ROOT / "docs/STAR-Bit-E038-timed-admission.md").write_text(report)
(HERE / "REPORT.md").write_text(report.replace("(../results/E038-timed-admission/", "("))
print(json.dumps({"timing_gate_passed": summary["timing_gate_passed"], "function_specific_gate_passed": summary["function_specific_gate_passed"], "verified": verified, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))
