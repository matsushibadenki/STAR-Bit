"""Audit E035 records and report baseline grammar feasibility."""
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


e035 = load("e035_for_report", HERE / "main.py")


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
    bootstrap = values[rng.integers(0, len(values), (20000, len(values)))].mean(axis=1)
    standard_deviation = values.std(ddof=1)
    return {"mean": float(values.mean()), "unbiased_variance": float(values.var(ddof=1)), "ci95": np.quantile(bootstrap, [.025, .975]).tolist(), "cohen_dz": None if standard_deviation == 0 else float(values.mean() / standard_deviation), "exact_signflip_p": signflip(values), "differences": values.tolist()}


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


result = strict_json((OUT / "results.json").read_text())
grammar, tasks = e035.tasks_from_grammar()
seeds = list(range(1500, 1506))
assert result["settings"] == {"seeds": seeds, "tasks": list(tasks), "beam": 128, "rounds": 6, "max_cost": 16, "initial_library": []}
assert len(result["records"]) == 36
assert len({(row["seed"], row["task"]) for row in result["records"]}) == 36
assert [strict_json(line) for line in (OUT / "progress.jsonl").read_text().splitlines()] == result["records"]
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected, name
frozen = strict_json((OUT / "frozen_tasks.json").read_text())
assert frozen["signatures"] == {name: str(value) for name, value in tasks.items()}
assert frozen["positive_class_counts"] == {name: value.bit_count() for name, value in tasks.items()}
assert frozen["settings"] == result["settings"]
assert frozen["frozen_route_candidate"] == [{"task": "route_cross_and", "family": "route", "round_budget": 4}]
inputs, _ = base.inputs_and_targets()
verified = 0
for row in result["records"]:
    assert row["condition"] == "no_transfer" and row["library_signatures"] == [] and not row["uses_transfer"]
    if row["expression"] is not None:
        assert row["exact"] and evaluate(row["expression"], inputs) == tasks[row["task"]]
        verified += 1

by = {(row["seed"], row["task"]): row for row in result["records"]}
summary = {"by_task": {}, "paired": {}, "holm_threshold_contrasts": {}, "difficulty": {}, "selected_numeric_tasks": [], "records_verified": 36, "solutions_verified": verified, "analysis_source_hash": sha(HERE / "report.py")}
for task, target in tasks.items():
    rows = [by[seed, task] for seed in seeds]
    summary["by_task"][task] = {"exact": metric([row["exact"] for row in rows]), "best_error": metric([row["best_error"] for row in rows]), "generated_unique_signatures": metric([row["generated_unique_signatures"] for row in rows]), "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]), "solution_primitives": metric([row["primitives"] for row in rows if row["exact"]]), "solution_routing_bits": metric([row["routing_bits"] for row in rows if row["exact"]]), "solution_depth": metric([row["depth"] for row in rows if row["exact"]]), "positive_class_count": target.bit_count()}
    count = sum(int(row["exact"]) for row in rows)
    stratum = "floor" if count <= 1 else "ceiling" if count >= 5 else "middle"
    summary["difficulty"][task] = {"exact_count": count, "stratum": stratum}
    if stratum == "middle":
        summary["selected_numeric_tasks"].append(task)

rng = np.random.default_rng(2035)
keys = []
for threshold in (5, 6, 7):
    key = f"asymmetric-minus-symmetric-ge{threshold}"
    keys.append(key)
    differences = [int(by[seed, f"numeric_asymmetric_ge{threshold}"]["exact"]) - int(by[seed, f"numeric_symmetric_ge{threshold}"]["exact"]) for seed in seeds]
    summary["paired"][key] = paired(differences, rng)
summary["holm_threshold_contrasts"] = {key: value for key, value in zip(keys, holm([summary["paired"][key]["exact_signflip_p"] for key in keys]))}
summary["numeric_feasible"] = bool(summary["selected_numeric_tasks"])
(OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False))
(OUT / "selected_numeric_tasks.json").write_text(json.dumps({"rule": "baseline-only exact 0-1/6 floor, 2-4/6 middle, 5-6/6 ceiling; freeze every middle target", "selected_numeric_tasks": summary["selected_numeric_tasks"], "frozen_route_candidate": frozen["frozen_route_candidate"], "numeric_feasible": summary["numeric_feasible"], "independent_function_evaluation_performed": False}, indent=2, allow_nan=False))

lines = ["# E035：重み付き数値Grammarの移植なし難度校正", "", "実行日：2026-09-22。数値truth tableの重みと閾値を事前固定した6 taskについて、移植なし・beam128・6 round・tree cost16で新規6 seedを実行した。計36探索。E034のroute候補は`route_cross_and@4`に固定したまま再選定していない。", "", "| task | 正例/64 | exact/6 | 難度 | best error平均 ± SD | 成功式のprimitive / routing bits / depth平均 |", "| --- | ---: | ---: | --- | ---: | ---: |"]
for task in tasks:
    item = summary["by_task"][task]
    count = summary["difficulty"][task]["exact_count"]
    sd = item["best_error"]["unbiased_variance"] ** .5
    cost = "NA" if item["solution_primitives"]["mean"] is None else f"{item['solution_primitives']['mean']:.2f} / {item['solution_routing_bits']['mean']:.2f} / {item['solution_depth']['mean']:.2f}"
    lines.append(f"| {task} | {item['positive_class_count']} | {count}/6 | {summary['difficulty'][task]['stratum']} | {item['best_error']['mean']:.3f} ± {sd:.3f} | {cost} |")
lines += ["", "## 事前選定と対照", "", "middleは移植なしexact 2–4/6。候補はすべて凍結し、後からFunction成績で絞らない。数値候補: " + (", ".join(f"`{task}`" for task in summary["selected_numeric_tasks"]) if summary["selected_numeric_tasks"] else "なし") + "。", "", "同じseedでのasymmetric−symmetric exact率の対応差：", "", "| threshold | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |", "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
for threshold, key in zip((5, 6, 7), keys):
    item = summary["paired"][key]
    effect = "NA" if item["cohen_dz"] is None else f"{item['cohen_dz']:.3f}"
    lines.append(f"| {threshold} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {effect} | {item['exact_signflip_p']:.4f} | {summary['holm_threshold_contrasts'][key]:.4f} |")
lines += ["", "各taskのexact平均・不偏分散、best error平均・不偏分散、生成signature数平均・不偏分散、時間平均秒：", ""]
for task in tasks:
    item = summary["by_task"][task]
    lines.append(f"- {task}: exact {item['exact']['mean']:.3f} / {item['exact']['unbiased_variance']:.3f}; error {item['best_error']['mean']:.3f} / {item['best_error']['unbiased_variance']:.3f}; signatures {item['generated_unique_signatures']['mean']:.1f} / {item['generated_unique_signatures']['unbiased_variance']:.1f}; time {item['elapsed_seconds']['mean']:.3f}秒。")
verification_note = f"全{verified} exact式を64入力で再評価した。" if verified else "exact解は0件で、全入力再評価の対象はなかった。"
lines += ["", verification_note + "36 unique record、progress一致、strict JSON、source hash、Function library不使用を監査した。正例数はtruth tableの構成比であり、探索難度や精度の証明ではない。", "", "## Roadmap", "", "- [Done] 新しい重み付き数値grammarを結果より前に凍結し、移植なしだけで6 seedの難度を測った。"]
if summary["numeric_feasible"]:
    lines += ["- [Next] 今回凍結した数値候補とE034のroute候補を、新規独立seedで移植なし／通常Function／一段barrier／同費用randomの同一予算比較に進める。"]
else:
    lines += ["- [Next] 誤り1/64まで到達した`numeric_symmetric_ge5`を候補にbeam幅のbaseline-only pilotを事前固定する。Function条件で候補を選ばない。"]
lines += ["- [Later] 費用付きFunction admissionとState付き形成・分解を検証し、負荷分散付きRouter、均衡固定random経路、同一run内→別seed Expert交換へ進む。", "", "English: This experiment calibrated numeric task difficulty using baseline search only; any middle-difficulty tasks are frozen for independent testing. It does not evaluate a learned Function.", "", "简体中文：本实验仅用基线搜索校准数值任务难度；所有中等难度候选均被冻结，留待独立种子验证。本实验不评价学习函数。", "", "[事前計画](../results/E035-numeric-grammar/PROTOCOL.md) / [生データ](../results/E035-numeric-grammar/run/results.json) / [凍結Task](../results/E035-numeric-grammar/run/frozen_tasks.json) / [選定Task](../results/E035-numeric-grammar/run/selected_numeric_tasks.json) / [監査](../results/E035-numeric-grammar/run/audit_summary.json)"]
report = "\n".join(lines) + "\n"
(ROOT / "docs/STAR-Bit-E035-numeric-grammar.md").write_text(report)
(HERE / "REPORT.md").write_text(report.replace("(../results/E035-numeric-grammar/", "("))
print(json.dumps({"selected_numeric_tasks": summary["selected_numeric_tasks"], "verified": verified, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))
