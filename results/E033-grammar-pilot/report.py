"""Audit and analyze the prospective E033 grammar pilot."""
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


e033 = load("e033_for_report", HERE / "main.py")


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
assert result["settings"]["seeds"] == list(range(1480, 1488))
assert result["settings"]["conditions"] == ["no_transfer", "admitted", "one_hop_barrier", "random_matched"]
assert result["settings"]["tasks"] == list(e033.tasks_from_grammar())
assert len(result["records"]) == 192
assert len({(row["seed"], row["task"], row["condition"]) for row in result["records"]}) == 192
assert [strict_json(line) for line in (OUT / "progress.jsonl").read_text().splitlines()] == result["records"]
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected, name

manifest = strict_json((OUT / "frozen_manifest.json").read_text())
tasks = e033.tasks_from_grammar()
assert {name: str(signature) for name, signature in tasks.items()} == manifest["grammar_tasks"]
assert len(set(tasks.values())) == 6
inputs, old_targets = base.inputs_and_targets()
probes, evaluations = e033.e024.task_signatures()
earlier = set(inputs) | set(old_targets.values()) | set(probes.values()) | set(evaluations.values()) | set(e033.e031.task_signatures().values())
assert not (set(tasks.values()) & earlier)
admitted = manifest["admitted"]
admitted_signature = int(admitted["signature"])
admitted_cost = admitted["primitives"], admitted["routing_bits"], admitted["depth"]
assert evaluate(admitted["expression"], inputs) == admitted_signature
random_signatures = set()
for item in manifest["random_matched"]:
    signature = int(item["signature"])
    assert evaluate(item["expression"], inputs) == signature
    assert tuple(item["cost"]) == admitted_cost
    assert signature not in earlier | set(tasks.values()) | random_signatures | {admitted_signature}
    random_signatures.add(signature)
assert len(random_signatures) == 48

verified = 0
for row in result["records"]:
    if row["expression"] is not None:
        assert row["exact"] and evaluate(row["expression"], inputs) == tasks[row["task"]]
        verified += 1

seeds = result["settings"]["seeds"]
conditions = result["settings"]["conditions"]
families = {"numeric": [task for task in tasks if task.startswith("numeric_")], "route": [task for task in tasks if task.startswith("route_")]}
by = {(row["seed"], row["task"], row["condition"]): row for row in result["records"]}
rng = np.random.default_rng(2033)
summary = {"by_task": {}, "paired": {}, "holm_family_contrasts": {}, "difficulty": {}, "records_verified": 192, "solutions_verified": verified, "random_libraries_verified": 48, "analysis_source_hash": sha(HERE / "report.py")}

for task in tasks:
    summary["by_task"][task] = {}
    for condition in conditions:
        rows = [by[seed, task, condition] for seed in seeds]
        summary["by_task"][task][condition] = {"exact": metric([row["exact"] for row in rows]), "best_error": metric([row["best_error"] for row in rows]), "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]), "solution_primitives": metric([row["primitives"] for row in rows if row["exact"]]), "solution_routing_bits": metric([row["routing_bits"] for row in rows if row["exact"]]), "solution_depth": metric([row["depth"] for row in rows if row["exact"]]), "uses_transfer": sum(row["exact"] and row["uses_transfer"] for row in rows)}
    baseline_count = sum(by[seed, task, "no_transfer"]["exact"] for seed in seeds)
    stratum = "floor" if baseline_count <= 1 else "ceiling" if baseline_count >= 7 else "middle"
    summary["difficulty"][task] = {"no_transfer_exact": baseline_count, "stratum": stratum}

contrasts = (("one_hop_barrier", "admitted"), ("one_hop_barrier", "no_transfer"), ("admitted", "random_matched"), ("admitted", "no_transfer"))
for family, family_tasks in families.items():
    for left, right in contrasts:
        differences = [sum(int(by[seed, task, left]["exact"]) - int(by[seed, task, right]["exact"]) for task in family_tasks) / len(family_tasks) for seed in seeds]
        summary["paired"][f"{family}:{left}-minus-{right}"] = paired(differences, rng)

keys = [f"{family}:{left}-minus-{right}" for family in families for left, right in contrasts]
summary["holm_family_contrasts"] = {key: value for key, value in zip(keys, holm([summary["paired"][key]["exact_signflip_p"] for key in keys]))}
interaction = [sum(int(by[seed, task, "one_hop_barrier"]["exact"]) - int(by[seed, task, "admitted"]["exact"]) for task in families["numeric"]) / 3 - sum(int(by[seed, task, "one_hop_barrier"]["exact"]) - int(by[seed, task, "admitted"]["exact"]) for task in families["route"]) / 3 for seed in seeds]
summary["paired"]["numeric-minus-route:barrier-minus-admitted"] = paired(interaction, rng)
primary = summary["paired"]["numeric-minus-route:barrier-minus-admitted"]
summary["pilot_signal_gate_met"] = bool(primary["mean"] >= .20 and primary["ci95"][0] > 0)
summary["future_middle_tasks"] = [task for task in tasks if summary["difficulty"][task]["stratum"] == "middle"]
(OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False))
(OUT / "difficulty_strata.json").write_text(json.dumps({"rule": "no_transfer exact 0-1=floor; 2-6=middle; 7-8=ceiling", "tasks": summary["difficulty"], "future_middle_tasks": summary["future_middle_tasks"], "independent_evaluation_performed": False}, indent=2, allow_nan=False))

lines = ["# E033：事前固定した数値・経路選択Grammarの難度Pilot", "", "実行日：2026-09-22。6つの新規truth tableを結果を見る前にgrammarで固定し、8 seed × 6 task × 4条件の192探索を実施した。これはtask難度とFunction作用方向を調べるpilotであり、新しい確認用seedをまだ使っていない。", "", "| family / task | no transfer | admitted | one-hop barrier | random matched | no-transfer難度 |", "| --- | ---: | ---: | ---: | ---: | --- |"]
for family, family_tasks in families.items():
    for task in family_tasks:
        counts = [sum(by[seed, task, condition]["exact"] for seed in seeds) for condition in conditions]
        lines.append(f"| {family} / {task} | " + " | ".join(f"{count}/8" for count in counts) + f" | {summary['difficulty'][task]['stratum']} |")
lines += ["", "family平均exact率をseedごとに対応比較した。", "", "| paired success rate | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |", "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
for key in keys:
    item = summary["paired"][key]
    effect = "NA" if item["cohen_dz"] is None else f"{item['cohen_dz']:.3f}"
    lines.append(f"| {key} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {effect} | {item['exact_signflip_p']:.4f} | {summary['holm_family_contrasts'][key]:.4f} |")
effect = "NA" if primary["cohen_dz"] is None else f"{primary['cohen_dz']:.3f}"
lines += ["", "## Pilot判定と独立確認の境界", "", f"事前のfamily interactionは{primary['mean']:+.4f}（不偏分散{primary['unbiased_variance']:.4f}、95% CI [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}]、dz={effect}、exact p={primary['exact_signflip_p']:.4f}）。pilot signal gateは" + ("達成した。" if summary["pilot_signal_gate_met"] else "満たさなかった。"), "この値は生成grammarの探索結果であり、新規task・seedへ一般化したという確認ではない。", "", "事前に固定した難度規則はno-transfer exact 0–1/8=floor、2–6/8=middle、7–8/8=ceiling。次の独立確認候補は**no-transferだけ**で決まり、Function条件の結果では選ばない。", "", "- middle: " + (", ".join(summary["future_middle_tasks"]) if summary["future_middle_tasks"] else "なし") + "。", "- familyごとのmiddle数: " + ", ".join(f"{family} {sum(task in summary['future_middle_tasks'] for task in family_tasks)}/{len(family_tasks)}" for family, family_tasks in families.items()) + "。", "", "task別のbest error平均／不偏分散、成功解tree cost平均（primitive / routing bits / depth）、Function使用成功数、時間平均秒：", ""]
for task in tasks:
    for condition in conditions:
        item = summary["by_task"][task][condition]
        cost = "NA" if item["solution_primitives"]["mean"] is None else f"{item['solution_primitives']['mean']:.2f} / {item['solution_routing_bits']['mean']:.2f} / {item['solution_depth']['mean']:.2f}"
        lines.append(f"- {task} / {condition}: error {item['best_error']['mean']:.3f} / {item['best_error']['unbiased_variance']:.3f}; cost {cost}; Function使用 {item['uses_transfer']}; 時間 {item['elapsed_seconds']['mean']:.3f}秒。")
lines += ["", f"全{verified} exact式を64入力で再評価し、192 unique record、progress一致、48 random Functionの費用・signature、task分離、strict JSON、source hashを監査した。Functionの使用を回路記述量・実gate数・実測速度の削減と混同しない。Router、State、Ternary ExpertはE033では評価していない。", "", "## Roadmap", "", "- [Done] 結果に依存しない数値／経路選択grammarを凍結し、両familyの難度とFunction伝播差を同じ探索予算でpilot評価した。", "- [Done] 次の対象はno-transferのみで層別化し、pilotと独立確認を分離した。", "- [Next] middleが両familyにあれば凍結した全middle taskを新規seedで評価する。どちらかにmiddleがなければ、別grammarを事前定義してpilotをやり直す。", "- [Later] 費用付きFunction admission、State付き形成・分解、その後にstep 0負荷分散付きRouterと固定random経路、同一run内→別seed Expert交換へ進む。", "", "English: Six targets were frozen from a numeric/route grammar before outcomes. This pilot reports all successes and failures, and selects any future mid-difficulty targets only from no-transfer success counts. Its family interaction is exploratory; no independent-seed confirmation is claimed.", "", "简体中文：在观察结果前，用数值与路由规则固定了六个目标。本预实验报告所有成功与失败，并仅依据无迁移条件的成功数选择后续中等难度目标。任务族交互作用仍属探索性结果，尚未进行独立种子确认。", "", "[事前计划](../results/E033-grammar-pilot/PROTOCOL.md) / [生数据](../results/E033-grammar-pilot/run/results.json) / [难度分层](../results/E033-grammar-pilot/run/difficulty_strata.json) / [冻结Manifest](../results/E033-grammar-pilot/run/frozen_manifest.json) / [审计摘要](../results/E033-grammar-pilot/run/audit_summary.json)"]
lines.insert(-1, "English / 简体中文: No task met the preregistered middle band (0/6). The next grammar must be fixed before another pilot. / 六个任务都未进入预注册的中等难度区间（0/6）；下一套任务规则必须在新预实验前固定。")
report = "\n".join(lines) + "\n"
(ROOT / "docs/STAR-Bit-E033-grammar-pilot.md").write_text(report)
(HERE / "REPORT.md").write_text(report.replace("(../results/E033-grammar-pilot/", "("))
print(json.dumps({"primary": primary, "pilot_gate": summary["pilot_signal_gate_met"], "middle": summary["future_middle_tasks"], "verified": verified}, indent=2))
