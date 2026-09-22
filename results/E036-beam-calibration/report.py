"""Audit and report E036 baseline beam-width calibration."""
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


e036 = load("e036_for_report", HERE / "main.py")


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
seeds = list(range(1510, 1516))
widths = [64, 128, 192, 256]
task = "numeric_symmetric_ge5"
target = e036.e035.tasks_from_grammar()[1][task]
assert result["settings"] == {"seeds": seeds, "task": task, "target_signature": str(target), "beam_widths": widths, "rounds": 6, "max_cost": 16, "initial_library": []}
assert len(result["records"]) == 24
assert len({(row["seed"], row["beam_width"]) for row in result["records"]}) == 24
assert [strict_json(line) for line in (OUT / "progress.jsonl").read_text().splitlines()] == result["records"]
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected, name
frozen = strict_json((OUT / "frozen_settings.json").read_text())
assert frozen["settings"] == result["settings"]
assert frozen["frozen_route_candidate"] == [{"task": "route_cross_and", "family": "route", "round_budget": 4}]
inputs, _ = base.inputs_and_targets()
verified = 0
for row in result["records"]:
    assert row["task"] == task and row["condition"] == "no_transfer" and row["library_signatures"] == [] and not row["uses_transfer"]
    if row["expression"] is not None:
        assert row["exact"] and evaluate(row["expression"], inputs) == target
        verified += 1
assert verified == sum(int(row["exact"]) for row in result["records"])

by = {(row["seed"], row["beam_width"]): row for row in result["records"]}
summary = {"by_width": {}, "paired_exact": {}, "paired_error": {}, "holm_exact": {}, "holm_error": {}, "difficulty": {}, "selected_numeric_width": None, "records_verified": 24, "solutions_verified": verified, "analysis_source_hash": sha(HERE / "report.py")}
for width in widths:
    rows = [by[seed, width] for seed in seeds]
    summary["by_width"][str(width)] = {"exact": metric([row["exact"] for row in rows]), "best_error": metric([row["best_error"] for row in rows]), "generated_unique_signatures": metric([row["generated_unique_signatures"] for row in rows]), "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]), "solution_primitives": metric([row["primitives"] for row in rows if row["exact"]]), "solution_routing_bits": metric([row["routing_bits"] for row in rows if row["exact"]]), "solution_depth": metric([row["depth"] for row in rows if row["exact"]])}
    count = sum(int(row["exact"]) for row in rows)
    summary["difficulty"][str(width)] = {"exact_count": count, "stratum": "floor" if count <= 1 else "ceiling" if count >= 5 else "middle"}
    if summary["selected_numeric_width"] is None and 2 <= count <= 4:
        summary["selected_numeric_width"] = width

rng = np.random.default_rng(2036)
keys = []
for lower, upper in zip(widths, widths[1:]):
    key = f"{upper}-minus-{lower}"
    keys.append(key)
    summary["paired_exact"][key] = paired([int(by[seed, upper]["exact"]) - int(by[seed, lower]["exact"]) for seed in seeds], rng)
    summary["paired_error"][key] = paired([by[seed, upper]["best_error"] - by[seed, lower]["best_error"] for seed in seeds], rng)
summary["holm_exact"] = {key: value for key, value in zip(keys, holm([summary["paired_exact"][key]["exact_signflip_p"] for key in keys]))}
summary["holm_error"] = {key: value for key, value in zip(keys, holm([summary["paired_error"][key]["exact_signflip_p"] for key in keys]))}
(OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False))
(OUT / "selected_numeric_width.json").write_text(json.dumps({"rule": "baseline-only exact 0-1/6 floor, 2-4/6 middle, 5-6/6 ceiling; choose lowest middle beam width", "selected_task": task if summary["selected_numeric_width"] is not None else None, "selected_numeric_width": summary["selected_numeric_width"], "frozen_route_candidate": frozen["frozen_route_candidate"], "independent_function_evaluation_performed": False}, indent=2, allow_nan=False))

lines = ["# E036：数値タスクの移植なしBeam幅校正", "", "実行日：2026-09-22。E035でbest error 1/64だった`numeric_symmetric_ge5`を固定し、移植なし・6 round・tree cost16でbeam幅64/128/192/256を新規6 seedで比較した。24探索。E034のroute候補は`route_cross_and@4`のまま固定した。", "", "| beam | exact/6 | 難度 | best error平均 ± SD | signature数平均 | 秒/探索平均 | 成功式 primitive / routing bits / depth平均 |", "| ---: | ---: | --- | ---: | ---: | ---: | ---: |"]
for width in widths:
    item = summary["by_width"][str(width)]
    difficulty = summary["difficulty"][str(width)]
    sd = item["best_error"]["unbiased_variance"] ** .5
    cost = "NA" if item["solution_primitives"]["mean"] is None else f"{item['solution_primitives']['mean']:.2f} / {item['solution_routing_bits']['mean']:.2f} / {item['solution_depth']['mean']:.2f}"
    lines.append(f"| {width} | {difficulty['exact_count']}/6 | {difficulty['stratum']} | {item['best_error']['mean']:.3f} ± {sd:.3f} | {item['generated_unique_signatures']['mean']:.1f} | {item['elapsed_seconds']['mean']:.3f} | {cost} |")
lines += ["", "各幅のexact平均・不偏分散、およびbest error平均・不偏分散：", ""]
for width in widths:
    item = summary["by_width"][str(width)]
    lines.append(f"- beam{width}: exact {item['exact']['mean']:.4f} / {item['exact']['unbiased_variance']:.4f}; best error {item['best_error']['mean']:.4f} / {item['best_error']['unbiased_variance']:.4f}。")
selected = summary["selected_numeric_width"]
lines += ["", "## 対応比較と選定", "", "事前の中難度規則は移植なしexact 2–4/6。複数該当時は最小beam幅を採用する。選定結果：" + (f"`{task}@beam{selected}`。" if selected is not None else "候補なし。"), "", "幅を変えるとbeam軌跡も変わるため、seed内の成功やbest errorが単調に改善するとは仮定しない。下のbest error差は`大きい幅−小さい幅`で、負値が改善を表す。", ""]
for label, source, adjusted in (("exact率", summary["paired_exact"], summary["holm_exact"]), ("best error", summary["paired_error"], summary["holm_error"])):
    lines += [f"### {label}の対応差", "", "| 幅の差 | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |", "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
    for key in keys:
        item = source[key]
        effect = "NA" if item["cohen_dz"] is None else f"{item['cohen_dz']:.3f}"
        lines.append(f"| {key} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {effect} | {item['exact_signflip_p']:.4f} | {adjusted[key]:.4f} |")
    lines.append("")
verification = f"全{verified}件のexact式を64入力で再評価した。" if verified else "exact解は0件で、全入力再評価の対象はなかった。"
lines += [verification + "24 unique record、progress一致、strict JSON、source hash、Function library不使用を監査した。計測時間とsignature数は探索の計算量であり、推論速度や物理ゲート数を示さない。", "", "## Roadmap", "", "- [Done] E035で選んだ近接数値タスクを固定し、beam幅だけをbaseline-onlyで校正した。"]
if selected is None:
    lines.append("- [Next] 数値taskの表現難度を別の事前固定grammarまたは探索選択則で校正する。Functionの結果から候補を選ばない。")
else:
    lines.append("- [Next] 凍結した数値task/幅とE034のroute候補を、新規独立seedで移植なし／通常Function／一段barrier／同費用random／inertを各task内の同一予算で比較する。")
lines += ["- [Later] 費用付きFunction admission、State付き形成・分解、初回負荷分散Router・均衡固定random経路・Expert交換を検証する。", "", "English: E036 changed only the beam width of a baseline numeric search. The selected width, if any, is a pilot difficulty setting and does not establish learned-Function value.", "", "简体中文：E036仅调整数值任务基线搜索的beam宽度。即使选出宽度，它也只是预实验的难度设置，不能证明学习函数的价值。", "", "[事前計画](../results/E036-beam-calibration/PROTOCOL.md) / [生データ](../results/E036-beam-calibration/run/results.json) / [固定設定](../results/E036-beam-calibration/run/frozen_settings.json) / [選定結果](../results/E036-beam-calibration/run/selected_numeric_width.json) / [監査](../results/E036-beam-calibration/run/audit_summary.json)"]
report = "\n".join(lines) + "\n"
(ROOT / "docs/STAR-Bit-E036-beam-calibration.md").write_text(report)
(HERE / "REPORT.md").write_text(report.replace("(../results/E036-beam-calibration/", "("))
print(json.dumps({"selected_numeric_width": selected, "verified": verified, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))
