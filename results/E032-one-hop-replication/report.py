"""Independent E032 audit and paired inference."""
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "run"
E019 = ROOT / "results/E019-function-space-genesis"
sys.path.insert(0, str(E019))
import search as base


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


e032 = load("e032_for_report", HERE / "main.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(expression, inputs):
    if expression[0] == "input":
        return inputs[expression[1]]
    signature = base.lut_outputs(evaluate(expression[3], inputs), evaluate(expression[4], inputs))[expression[2]]
    assert signature == int(expression[1])
    return signature


def signflip(values):
    values = np.asarray(values, float)
    observed = abs(values.mean())
    count = 0
    for mask in range(2 ** len(values)):
        flip_mean = sum(value if mask & (1 << index) else -value for index, value in enumerate(values)) / len(values)
        count += abs(flip_mean) >= observed - 1e-12
    return count / (2 ** len(values))


def paired(values, rng):
    values = np.asarray(values, float)
    bootstrap = values[rng.integers(0, len(values), (20000, len(values)))].mean(axis=1)
    standard_deviation = values.std(ddof=1)
    return {"mean": float(values.mean()), "unbiased_variance": float(values.var(ddof=1)), "ci95": np.quantile(bootstrap, [.025, .975]).tolist(), "cohen_dz": None if standard_deviation == 0 else float(values.mean() / standard_deviation), "exact_signflip_p": signflip(values), "differences": values.tolist()}


def metric(values):
    values = np.asarray(values, float)
    return {"mean": None if len(values) == 0 else float(values.mean()), "unbiased_variance": None if len(values) < 2 else float(values.var(ddof=1)), "n": len(values)}


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


strict_json = lambda content: json.loads(content, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
result = strict_json((OUT / "results.json").read_text())
assert len(result["records"]) == 160
assert result["settings"]["seeds"] == list(range(1460, 1476))
assert result["settings"]["tasks"] == ["numeric_unsigned_sum_ge6", "route_dual_mux_xnor"]
assert result["settings"]["conditions"] == ["no_transfer", "admitted", "one_hop_barrier", "inert_slot", "random_matched"]
assert len({(row["seed"], row["task"], row["condition"]) for row in result["records"]}) == 160
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected, name

progress = [strict_json(line) for line in (OUT / "progress.jsonl").read_text().splitlines()]
assert progress == result["records"]
manifest = strict_json((OUT / "frozen_manifest.json").read_text())
tasks = {name: int(signature) for name, signature in manifest["tasks"].items()}
assert tasks == {name: e032.e031.task_signatures()[name] for name in tasks}
inputs, old_targets = base.inputs_and_targets()
probes, evaluations = e032.e024.task_signatures()
forbidden = set(inputs) | set(old_targets.values()) | set(probes.values()) | set(evaluations.values()) | set(e032.e031.task_signatures().values())
admitted = manifest["admitted"]
admitted_signature = int(admitted["signature"])
admitted_cost = admitted["primitives"], admitted["routing_bits"], admitted["depth"]
assert evaluate(admitted["expression"], inputs) == admitted_signature
random_signatures = set()
for item in manifest["random_matched"]:
    signature = int(item["signature"])
    assert evaluate(item["expression"], inputs) == signature
    assert tuple(item["cost"]) == admitted_cost
    assert signature not in forbidden | random_signatures | {admitted_signature}
    random_signatures.add(signature)
assert len(random_signatures) == 32

verified = 0
for row in result["records"]:
    if row["expression"] is not None:
        assert row["exact"] and evaluate(row["expression"], inputs) == tasks[row["task"]]
        verified += 1

seeds = result["settings"]["seeds"]
conditions = result["settings"]["conditions"]
by = {(row["seed"], row["task"], row["condition"]): row for row in result["records"]}
rng = np.random.default_rng(2032)
summary = {"aggregate": result["aggregate"], "by_task": {}, "paired": {}, "holm_secondary_numeric": {}, "records_verified": 160, "solutions_verified": verified, "random_libraries_verified": 32, "analysis_source_hash": sha(HERE / "report.py")}
for task in tasks:
    summary["by_task"][task] = {}
    for condition in conditions:
        rows = [by[seed, task, condition] for seed in seeds]
        summary["by_task"][task][condition] = {"exact": metric([row["exact"] for row in rows]), "best_error": metric([row["best_error"] for row in rows]), "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]), "solution_primitives": metric([row["primitives"] for row in rows if row["exact"]]), "solution_routing_bits": metric([row["routing_bits"] for row in rows if row["exact"]]), "solution_depth": metric([row["depth"] for row in rows if row["exact"]]), "uses_transfer": sum(row["exact"] and row["uses_transfer"] for row in rows)}
    comparisons = [("one_hop_barrier", "admitted"), ("one_hop_barrier", "inert_slot"), ("one_hop_barrier", "no_transfer"), ("one_hop_barrier", "random_matched"), ("admitted", "inert_slot"), ("admitted", "random_matched"), ("inert_slot", "no_transfer")]
    for left, right in comparisons:
        differences = [int(by[seed, task, left]["exact"]) - int(by[seed, task, right]["exact"]) for seed in seeds]
        summary["paired"][f"{task}:{left}-minus-{right}"] = paired(differences, rng)

numeric = "numeric_unsigned_sum_ge6"
route = "route_dual_mux_xnor"
secondary = [("one_hop_barrier", "no_transfer"), ("one_hop_barrier", "random_matched"), ("admitted", "inert_slot"), ("admitted", "random_matched"), ("inert_slot", "no_transfer"), ("one_hop_barrier", "inert_slot")]
adjusted = holm([summary["paired"][f"{numeric}:{left}-minus-{right}"]["exact_signflip_p"] for left, right in secondary])
summary["holm_secondary_numeric"] = {f"{left}-minus-{right}": value for (left, right), value in zip(secondary, adjusted)}
primary = summary["paired"][f"{numeric}:one_hop_barrier-minus-admitted"]
mechanism = summary["paired"][f"{numeric}:one_hop_barrier-minus-inert_slot"]
summary["replication_criterion_met"] = bool(primary["mean"] >= .25 and primary["ci95"][0] > 0 and primary["exact_signflip_p"] <= .05)
summary["one_hop_mechanism_criterion_met"] = bool(summary["replication_criterion_met"] and mechanism["mean"] >= .125 and mechanism["exact_signflip_p"] <= .05)
interaction = [int(by[seed, numeric, "one_hop_barrier"]["exact"]) - int(by[seed, numeric, "admitted"]["exact"]) - int(by[seed, route, "one_hop_barrier"]["exact"]) + int(by[seed, route, "admitted"]["exact"]) for seed in seeds]
summary["paired"]["numeric-minus-route:barrier-minus-admitted"] = paired(interaction, rng)
summary["inert_vs_no_transfer_identical_exact_and_error"] = all(by[seed, task, "inert_slot"]["exact"] == by[seed, task, "no_transfer"]["exact"] and by[seed, task, "inert_slot"]["best_error"] == by[seed, task, "no_transfer"]["best_error"] for seed in seeds for task in tasks)

(OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False))

lines = ["# E032：one-hop伝播の独立seed確認とinert-slot対照", "", "実行日：2026-09-22。E031で探索的に見つけた数値`unsigned_sum_ge6`のbarrier差を、新規16 seedで条件付き独立確認した。route対照はE031で定義済みのdual-mux XNOR。各taskで移植なし・採用Function・one-hop barrier・inert slot・同一費用randomの5条件、計160探索を事前固定した。", "", "| task | no transfer | admitted | one-hop barrier | inert slot | random matched |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
for task in tasks:
    counts = [int(sum(by[seed, task, condition]["exact"] for seed in seeds)) for condition in conditions]
    lines.append(f"| {task} | " + " | ".join(f"{count}/16" for count in counts) + " |")
lines += ["", "| paired exact/seed | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |", "| --- | ---: | ---: | --- | ---: | ---: |"]
for task in tasks:
    for left, right in (("one_hop_barrier", "admitted"), ("one_hop_barrier", "inert_slot"), ("one_hop_barrier", "no_transfer"), ("one_hop_barrier", "random_matched"), ("admitted", "inert_slot"), ("admitted", "random_matched"), ("inert_slot", "no_transfer")):
        item = summary["paired"][f"{task}:{left}-minus-{right}"]
        effect = "NA" if item["cohen_dz"] is None else f"{item['cohen_dz']:.3f}"
        lines.append(f"| {task}: {left}−{right} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {effect} | {item['exact_signflip_p']:.5f} |")
lines += ["", "## 判定", "", "事前登録した数値のbarrier−admitted再現基準は" + ("達成。" if summary["replication_criterion_met"] else "未達。"), "one-hop固有機構のbarrier−inert追加基準は" + ("達成。" if summary["one_hop_mechanism_criterion_met"] else "未達。"), f"Primaryはbarrier−admitted {primary['mean']:+.4f} exact/seed、95% CI [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}]、exact p={primary['exact_signflip_p']:.5f}。barrier−inertは{mechanism['mean']:+.4f}、95% CI [{mechanism['ci95'][0]:.4f}, {mechanism['ci95'][1]:.4f}]、exact p={mechanism['exact_signflip_p']:.5f}。", "", "主効果は新seedでも再現したが、barrierがinert/no-transferより明確に良いとは言えない。数値でinert slotとno-transferは全16 seedでexact・best errorが一致した。barrierの数値成功12式はいずれも最終式でFunctionを使わず、直接部品としての再利用は観測されなかった。したがって、今回の強い対比は『無制限にFunctionを伝播させると探索が悪化しうる』であり、『一段使うこと自体が必要』とは示されていない。", "", "inert条件は同じtruth signatureのFunction-free再生成も親利用を禁止する保守的な対照である。このtaskでは移植なしと同じexact・best errorだったが、他taskでも無害とは限らない。", "", "数値の6つの副次比較にHolm補正を適用した。"]
for left, right in secondary:
    key = f"{left}-minus-{right}"
    item = summary["paired"][f"{numeric}:{key}"]
    lines.append(f"- {left}−{right}: p={item['exact_signflip_p']:.5f}、Holm p={summary['holm_secondary_numeric'][key]:.5f}。")
interaction_result = summary["paired"]["numeric-minus-route:barrier-minus-admitted"]
lines += ["", f"数値−経路選択のbarrier−admitted効果差は{interaction_result['mean']:+.4f}、95% CI [{interaction_result['ci95'][0]:.4f}, {interaction_result['ci95'][1]:.4f}]、exact p={interaction_result['exact_signflip_p']:.5f}。route側はadmitted 4/16、barrier 2/16で方向が逆だが、単一route taskでありtask-family差の確証ではない。", "", "成功式の平均tree cost（primitive / routing bits / depth）と移植Function使用数：", ""]
for task in tasks:
    for condition in conditions:
        item = summary["by_task"][task][condition]
        cost = "NA" if item["solution_primitives"]["mean"] is None else f"{item['solution_primitives']['mean']:.2f} / {item['solution_routing_bits']['mean']:.2f} / {item['solution_depth']['mean']:.2f}"
        lines.append(f"- {task} / {condition}: {cost}; Function使用 {item['uses_transfer']}、best error平均 {item['best_error']['mean']:.3f}、時間平均 {item['elapsed_seconds']['mean']:.3f}秒。")
lines += ["", f"全{verified} exact式を64入力で再評価し、160 record、32 random Functionの費用とsignature、task、source hash、strict JSONを監査した。対象はBoolean beam探索であり、概念形成、Library記述圧縮、実gate削減、ハードウェア速度、Stateや学習Routerの効果は測っていない。", "", "## Roadmap", "", "- [Done] E031の数値barrier優位を新規16 seedで独立確認し、inert-slot対照で初期候補数の交絡を検査した。", "- [Done] 数値対経路選択でFunctionの作用方向が異なることを同一予算で記録した。", "- [Next] Functionの使用をstage/roundで制限する費用付きadmissionを、task生成grammarを先に固定したpilotで検証する。task難度の選別にはpilotだけを使い、独立seedを保持する。", "- [Later] State付きFunction形成・分解とRouter統合へ進み、step 0負荷分散、固定random経路、同一run内から別seedへのExpert交換、総費用を比較する。", "", "English: The numeric barrier advantage over unrestricted Function propagation replicated on 16 new seeds (12/16 versus 2/16, paired gain +0.625, exact p=0.00195). The barrier did not significantly beat an inert slot or no transfer (12/16 versus 8/16), so beneficial one-hop composition remains unproven. The route task showed the opposite direction (barrier 2/16, admitted 4/16).", "", "简体中文：在16个新种子上，数值任务中一跳屏障相对无限制函数传播的优势得到复现（12/16对2/16，配对增益+0.625，精确p=0.00195）。但屏障未显著优于惰性槽或无迁移（12/16对8/16），因此尚未证明一跳组合本身有益。路由任务呈相反方向（屏障2/16，普通函数4/16）。", "", "[事前计划](../results/E032-one-hop-replication/PROTOCOL.md) / [生数据](../results/E032-one-hop-replication/run/results.json) / [冻结Manifest](../results/E032-one-hop-replication/run/frozen_manifest.json) / [审计摘要](../results/E032-one-hop-replication/run/audit_summary.json)"]
report = "\n".join(lines) + "\n"
(ROOT / "docs/STAR-Bit-E032-one-hop-replication.md").write_text(report)
(HERE / "REPORT.md").write_text(report.replace("(../results/E032-one-hop-replication/", "("))
print(json.dumps({"primary": primary, "mechanism": mechanism, "replication": summary["replication_criterion_met"], "mechanism_met": summary["one_hop_mechanism_criterion_met"], "verified": verified}, indent=2))
