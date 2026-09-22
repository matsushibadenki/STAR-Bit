"""Audit and analyze E034 baseline-only round-budget calibration."""
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


e034 = load("e034_for_report", HERE / "main.py")


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
assert result["settings"]["seeds"] == list(range(1490, 1496))
assert result["settings"]["tasks"] == list(e034.e033.tasks_from_grammar())
assert result["settings"]["round_budgets"] == [4, 6, 8]
assert result["settings"]["initial_library"] == []
assert len(result["records"]) == 108
assert len({(row["seed"], row["task"], row["round_budget"]) for row in result["records"]}) == 108
assert [strict_json(line) for line in (OUT / "progress.jsonl").read_text().splitlines()] == result["records"]
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected, name

frozen = strict_json((OUT / "frozen_tasks.json").read_text())
tasks = e034.e033.tasks_from_grammar()
assert frozen["tasks"] == {name: str(signature) for name, signature in tasks.items()}
assert frozen["round_budgets"] == [4, 6, 8]
inputs, _ = base.inputs_and_targets()
verified = 0
for row in result["records"]:
    assert row["library_signatures"] == [] and not row["uses_transfer"]
    if row["expression"] is not None:
        assert row["exact"] and evaluate(row["expression"], inputs) == tasks[row["task"]]
        verified += 1

seeds = result["settings"]["seeds"]
budgets = result["settings"]["round_budgets"]
families = {"numeric": [task for task in tasks if task.startswith("numeric_")], "route": [task for task in tasks if task.startswith("route_")]}
by = {(row["seed"], row["task"], row["round_budget"]): row for row in result["records"]}
for seed in seeds:
    for task in tasks:
        for lower, upper in zip(budgets, budgets[1:]):
            assert int(by[seed, task, lower]["exact"]) <= int(by[seed, task, upper]["exact"])
            assert by[seed, task, lower]["best_error"] >= by[seed, task, upper]["best_error"]
            assert by[seed, task, upper]["best_error_history"][:len(by[seed, task, lower]["best_error_history"])] == by[seed, task, lower]["best_error_history"]

rng = np.random.default_rng(2034)
summary = {"by_task": {}, "paired": {}, "holm_family_contrasts": {}, "difficulty": {}, "selected_pairs": [], "records_verified": 108, "solutions_verified": verified, "analysis_source_hash": sha(HERE / "report.py")}
for task in tasks:
    summary["by_task"][task] = {}
    for budget in budgets:
        rows = [by[seed, task, budget] for seed in seeds]
        summary["by_task"][task][str(budget)] = {"exact": metric([row["exact"] for row in rows]), "best_error": metric([row["best_error"] for row in rows]), "generated_unique_signatures": metric([row["generated_unique_signatures"] for row in rows]), "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]), "solution_primitives": metric([row["primitives"] for row in rows if row["exact"]]), "solution_routing_bits": metric([row["routing_bits"] for row in rows if row["exact"]]), "solution_depth": metric([row["depth"] for row in rows if row["exact"]])}
        count = sum(row["exact"] for row in rows)
        summary["difficulty"].setdefault(task, {})[str(budget)] = {"exact": count, "stratum": "floor" if count <= 1 else "ceiling" if count >= 5 else "middle"}
    middle = [budget for budget in budgets if summary["difficulty"][task][str(budget)]["stratum"] == "middle"]
    if middle:
        summary["selected_pairs"].append({"task": task, "family": "numeric" if task.startswith("numeric_") else "route", "round_budget": min(middle)})

keys = []
for family, family_tasks in families.items():
    for upper, lower in ((6, 4), (8, 6)):
        differences = [sum(int(by[seed, task, upper]["exact"]) - int(by[seed, task, lower]["exact"]) for task in family_tasks) / len(family_tasks) for seed in seeds]
        key = f"{family}:{upper}-minus-{lower}"
        keys.append(key)
        summary["paired"][key] = paired(differences, rng)
summary["holm_family_contrasts"] = {key: value for key, value in zip(keys, holm([summary["paired"][key]["exact_signflip_p"] for key in keys]))}
summary["calibration_feasible_both_families"] = all(any(pair["family"] == family for pair in summary["selected_pairs"]) for family in families)
(OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False))
(OUT / "selected_task_budgets.json").write_text(json.dumps({"rule": "baseline-only exact 0-1/6 floor, 2-4/6 middle, 5-6/6 ceiling; choose lowest middle round budget per task", "selected_pairs": summary["selected_pairs"], "calibration_feasible_both_families": summary["calibration_feasible_both_families"], "independent_function_evaluation_performed": False}, indent=2, allow_nan=False))

lines = ["# E034：移植なし条件だけで探索Round予算を校正", "", "実行日：2026-09-22。E033で事前固定した6 taskを変えず、移植なし・beam128・tree cost16でround上限4/6/8を新規6 seedで比較した。合計108探索。Functionの成績で予算を選んでいない。", "", "| family / task | 4 round | 6 round | 8 round | 選定予算 |", "| --- | ---: | ---: | ---: | ---: |"]
for family, family_tasks in families.items():
    for task in family_tasks:
        counts = [summary["difficulty"][task][str(budget)]["exact"] for budget in budgets]
        selected = next((pair["round_budget"] for pair in summary["selected_pairs"] if pair["task"] == task), None)
        lines.append(f"| {family} / {task} | " + " | ".join(f"{count}/6 ({summary['difficulty'][task][str(budget)]['stratum']})" for count, budget in zip(counts, budgets)) + f" | {selected if selected is not None else 'なし'} |")
lines += ["", "## 事前選定基準", "", "middleは移植なしexact 2–4/6。複数予算が該当するときは同じtaskの最小roundを採用した。両familyに候補があるという実行前feasibility基準は" + ("達成した。" if summary["calibration_feasible_both_families"] else "満たさなかった。"), "", "- 選定されたtask–budget: " + (", ".join(f"{pair['task']}@{pair['round_budget']}" for pair in summary["selected_pairs"]) if summary["selected_pairs"] else "なし") + "。", "- 確認用の別seedでFunction条件を比較するまでは、構造自由度や一段barrierの一般化効果を主張しない。", "", "family平均exact率の対応差（seed単位）：", "", "| family / rounds | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |", "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
for key in keys:
    item = summary["paired"][key]
    effect = "NA" if item["cohen_dz"] is None else f"{item['cohen_dz']:.3f}"
    lines.append(f"| {key} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {effect} | {item['exact_signflip_p']:.4f} | {summary['holm_family_contrasts'][key]:.4f} |")
lines += ["", "各task/予算のexact平均・不偏分散、best error平均・不偏分散、生成signature数平均、成功解tree cost平均（primitive / routing bits / depth）、時間平均秒：", ""]
for task in tasks:
    for budget in budgets:
        item = summary["by_task"][task][str(budget)]
        cost = "NA" if item["solution_primitives"]["mean"] is None else f"{item['solution_primitives']['mean']:.2f} / {item['solution_routing_bits']['mean']:.2f} / {item['solution_depth']['mean']:.2f}"
        lines.append(f"- {task} / r{budget}: exact {item['exact']['mean']:.3f} / {item['exact']['unbiased_variance']:.3f}; error {item['best_error']['mean']:.3f} / {item['best_error']['unbiased_variance']:.3f}; signatures {item['generated_unique_signatures']['mean']:.1f}; cost {cost}; time {item['elapsed_seconds']['mean']:.3f}秒。")
lines += ["", f"全{verified} exact式を64入力で再評価し、108 unique record、progress一致、budget間のprefix・exact/error単調性、strict JSON、source hashを監査した。計測時間はCPU探索時間であり、推論速度やハードウェア効率ではない。", "", "## Roadmap", "", "- [Done] E033の6 taskを固定したまま、移植なし条件だけでround予算4/6/8の難度曲線を測った。", "- [Done] middleの選定をbaseline exactだけに限定し、Function条件の結果を見る前にtask–budget候補を凍結した。", "- [Next] 両familyに候補があれば、新規seedで凍結候補すべての移植なし／通常Function／一段barrier／同費用randomを評価する。候補がなければ新grammarを事前固定する。", "- [Later] State付き形成・分解、費用付きadmission、負荷分散付きRouterと固定random経路、同一run内→別seed Expert交換へ進む。", "", "English: E034 varied only the baseline search-round budget across six frozen tasks. Mid-difficulty task–budget pairs, if any, were chosen solely from baseline exact counts. No learned-Function efficacy was evaluated here.", "", "简体中文：E034只改变六个固定任务的基线搜索轮数预算。中等难度的任务–预算组合仅依据基线精确成功数选定；本实验未评价学习函数的效果。", "", "[事前计划](../results/E034-budget-calibration/PROTOCOL.md) / [生数据](../results/E034-budget-calibration/run/results.json) / [冻结Task](../results/E034-budget-calibration/run/frozen_tasks.json) / [选定Task–Budget](../results/E034-budget-calibration/run/selected_task_budgets.json) / [审计摘要](../results/E034-budget-calibration/run/audit_summary.json)"]
lines = ["- [Next] 数値grammarまたはbeam幅をbaselineのみのpilotで校正し、両familyに中難度候補を確保する。確認用seedは独立に確保する。" if line.startswith("- [Next] ") else line for line in lines]
lines.insert(-1, "English: Only route_cross_and at four rounds met the middle band (3/6); numeric had none, so the two-family confirmation gate failed.")
lines.insert(-1, "简体中文：只有四轮的route_cross_and进入中等难度（3/6）；数值任务没有候选，因此双任务族确认门槛未通过。")
report = "\n".join(lines) + "\n"
(ROOT / "docs/STAR-Bit-E034-budget-calibration.md").write_text(report)
(HERE / "REPORT.md").write_text(report.replace("(../results/E034-budget-calibration/", "("))
print(json.dumps({"selected_pairs": summary["selected_pairs"], "feasible": summary["calibration_feasible_both_families"], "verified": verified, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))
