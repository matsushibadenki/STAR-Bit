"""Audit and report E031 route-family portability."""
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
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


experiment = load("e031_report_target", HERE / "main.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(expression, inputs):
    if expression[0] == "input":
        return inputs[expression[1]]
    signature = base.lut_outputs(evaluate(expression[3], inputs), evaluate(expression[4], inputs))[expression[2]]
    assert signature == int(expression[1])
    return signature


def expression_signatures(expression):
    if expression[0] == "input":
        return set()
    return {int(expression[1])} | expression_signatures(expression[3]) | expression_signatures(expression[4])


def signflip(differences):
    observed = abs(float(np.mean(differences)))
    extreme = 0
    for mask in range(2 ** len(differences)):
        value = np.mean([difference * (1 if mask & (1 << index) else -1) for index, difference in enumerate(differences)])
        extreme += abs(value) >= observed - 1e-12
    return extreme / (2 ** len(differences))


def paired(differences, rng):
    values = np.asarray(differences, float)
    bootstrap = values[rng.integers(0, len(values), (20000, len(values)))].mean(1)
    standard_deviation = values.std(ddof=1)
    return {
        "mean": float(values.mean()),
        "unbiased_variance": float(values.var(ddof=1)),
        "ci95": np.quantile(bootstrap, [.025, .975]).tolist(),
        "cohen_dz": None if standard_deviation == 0 else float(values.mean() / standard_deviation),
        "exact_signflip_p": signflip(values),
        "differences": values.tolist(),
    }


def metric(values):
    values = np.asarray(values, float)
    return {"mean": None if len(values) == 0 else float(values.mean()), "unbiased_variance": None if len(values) < 2 else float(values.var(ddof=1)), "n": len(values)}


def mcnemar(left, right):
    left_only = sum(a and not b for a, b in zip(left, right))
    right_only = sum(b and not a for a, b in zip(left, right))
    discordant = left_only + right_only
    p = 1.0 if discordant == 0 else min(1.0, 2 * sum(math.comb(discordant, k) for k in range(min(left_only, right_only) + 1)) / 2 ** discordant)
    return p, left_only, right_only


def holm(values):
    order = sorted(range(len(values)), key=lambda index: values[index])
    adjusted = [0.0] * len(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        adjusted[index] = running
    return adjusted


result = json.loads((OUT / "results.json").read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
assert len(result["records"]) == 160
assert result["settings"]["seeds"] == list(range(1450, 1458))
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected, name

tasks = experiment.task_signatures()
assert list(tasks) == result["settings"]["tasks"]
inputs, _ = base.inputs_and_targets()
verified = 0
for row in result["records"]:
    if row["expression"] is not None:
        assert row["exact"] and evaluate(row["expression"], inputs) == tasks[row["task"]]
        verified += 1

libraries = json.loads((OUT / "frozen_libraries.json").read_text())
admitted_signature = int(libraries["admitted"]["signature"])
assert evaluate(libraries["admitted"]["expression"], inputs) == admitted_signature
random_signatures = set()
for item in libraries["random_matched"]:
    candidate_signature = int(item["signature"])
    assert evaluate(item["expression"], inputs) == candidate_signature
    assert tuple(item["cost"]) == (libraries["admitted"]["primitives"], libraries["admitted"]["routing_bits"], libraries["admitted"]["depth"])
    assert candidate_signature not in random_signatures and candidate_signature not in set(tasks.values())
    random_signatures.add(candidate_signature)
assert len(random_signatures) == 40

seeds = result["settings"]["seeds"]
conditions = result["settings"]["conditions"]
families = {"route": [task for task in tasks if task.startswith("route_")], "numeric": [task for task in tasks if task.startswith("numeric_")]}
by = {(row["seed"], row["task"], row["condition"]): row for row in result["records"]}
rng = np.random.default_rng(2031)
summary = {"aggregate": result["aggregate"], "by_task": {}, "paired": {}, "mcnemar": {}, "direct_use": {}, "solutions_verified": verified, "records_verified": len(result["records"]), "analysis_source_hash": sha(HERE / "report.py")}

for task in tasks:
    summary["by_task"][task] = {}
    for condition in conditions:
        rows = [by[seed, task, condition] for seed in seeds]
        summary["by_task"][task][condition] = {
            "exact": metric([row["exact"] for row in rows]),
            "best_error": metric([row["best_error"] for row in rows]),
            "elapsed_seconds": metric([row["elapsed_seconds"] for row in rows]),
            "solution_primitives": metric([row["primitives"] for row in rows if row["exact"]]),
            "solution_routing_bits": metric([row["routing_bits"] for row in rows if row["exact"]]),
            "solution_depth": metric([row["depth"] for row in rows if row["exact"]]),
            "uses_transfer": sum(row["exact"] and row["uses_transfer"] for row in rows),
        }
    comparisons = (("admitted", "random_matched"), ("admitted", "no_transfer"), ("admitted", "one_hop_barrier"))
    tests = []
    for left, right in comparisons:
        left_values = [by[seed, task, left]["exact"] for seed in seeds]
        right_values = [by[seed, task, right]["exact"] for seed in seeds]
        p, left_only, right_only = mcnemar(left_values, right_values)
        tests.append({"left": left, "right": right, "left_only": left_only, "right_only": right_only, "p": p})
    for item, adjusted in zip(tests, holm([item["p"] for item in tests])):
        item["holm_p"] = adjusted
    summary["mcnemar"][task] = tests

for family, family_tasks in families.items():
    for left, right in (("admitted", "random_matched"), ("admitted", "no_transfer"), ("admitted", "one_hop_barrier")):
        differences = []
        for seed in seeds:
            differences.append(sum(by[seed, task, left]["exact"] for task in family_tasks) - sum(by[seed, task, right]["exact"] for task in family_tasks))
        summary["paired"][f"{family}:{left}-minus-{right}"] = paired(differences, rng)

interaction = []
for seed in seeds:
    route_difference = sum(by[seed, task, "admitted"]["exact"] - by[seed, task, "random_matched"]["exact"] for task in families["route"]) / len(families["route"])
    numeric_difference = sum(by[seed, task, "admitted"]["exact"] - by[seed, task, "random_matched"]["exact"] for task in families["numeric"]) / len(families["numeric"])
    interaction.append(route_difference - numeric_difference)
summary["paired"]["route-minus-numeric:admitted-minus-random"] = paired(interaction, rng)

admitted_only_tasks = 0
for task in families["route"]:
    witnesses = []
    for seed in seeds:
        admitted = by[seed, task, "admitted"]
        random_row = by[seed, task, "random_matched"]
        if admitted["exact"] and not random_row["exact"] and admitted["expression"] is not None and admitted_signature in expression_signatures(admitted["expression"]):
            witnesses.append(seed)
    summary["direct_use"][task] = witnesses
    admitted_only_tasks += bool(witnesses)
primary = summary["paired"]["route:admitted-minus-random_matched"]
summary["portability_criterion_met"] = primary["mean"] >= .5 and primary["ci95"][0] > 0 and admitted_only_tasks >= 2

(OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False))

lines = [
    "# E031：固定Functionの経路選択Task Familyへの移植性",
    "",
    "実行日：2026-09-21。E026で採用した固定Functionを再調整せず、新規8 seed × 事前定義5 task（経路選択3、数値2）× 4条件の160探索で評価した。対照は移植なし、一段伝播barrier、同一費用のrandom Functionである。",
    "",
    "## 結果",
    "",
    "| family / task | no transfer | admitted | barrier | random matched |",
    "| --- | ---: | ---: | ---: | ---: |",
]
for family, family_tasks in families.items():
    for task in family_tasks:
        counts = [int(summary["by_task"][task][condition]["exact"]["mean"] * len(seeds)) for condition in conditions]
        lines.append(f"| {family} / {task} | {counts[0]}/8 | {counts[1]}/8 | {counts[2]}/8 | {counts[3]}/8 |")

lines += ["", "family内のexact task数をseedごとに対応比較した。", "", "| paired count/seed | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |", "| --- | ---: | ---: | --- | ---: | ---: |"]
for family in ("route", "numeric"):
    for left, right in (("admitted", "random_matched"), ("admitted", "no_transfer"), ("admitted", "one_hop_barrier")):
        item = summary["paired"][f"{family}:{left}-minus-{right}"]
        dz = "NA" if item["cohen_dz"] is None else f"{item['cohen_dz']:.3f}"
        lines.append(f"| {family}: {left}−{right} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {dz} | {item['exact_signflip_p']:.4f} |")

interaction_result = summary["paired"]["route-minus-numeric:admitted-minus-random"]
lines += [
    "",
    "## 判定",
    "",
    "事前登録したroute-family portability基準は" + ("満たした。" if summary["portability_criterion_met"] else "満たさなかった。"),
    f"Primaryのadmitted−randomはrouteで{primary['mean']:+.4f} task/seed、95% CI [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}]、exact p={primary['exact_signflip_p']:.4f}だった。2/8のadmitted成功はいずれもFunctionを最終式で直接使ったが、admitted-onlyかつ直接使用のwitnessが得られたroute taskは{admitted_only_tasks}/3だった。",
    f"routeとnumericのadmitted−random成功率効果の差は{interaction_result['mean']:+.4f}、95% CI [{interaction_result['ci95'][0]:.4f}, {interaction_result['ci95'][1]:.4f}]。これはtask種別差の記述値であり、8 seedの探索的比較である。",
    "",
    "固定Functionはroute全体でrandom対照を上回らず、数値側では成功を減らした。`numeric_unsigned_sum_ge6`ではadmitted 0/8に対しbarrier 6/8、no-transfer 4/8、random 3/8だった。admitted対barrierのexact sign-flip pは0.0312だが、このtask内3比較のHolm補正後は0.0938である。したがって、Functionを深く伝播させることが探索を妨げ、一段だけの摂動がbeamを有利に変える可能性はあるものの、確証とは扱わない。",
    "",
    "taskごとの3比較をHolm補正した。",
    "",
]
for task in tasks:
    for item in summary["mcnemar"][task]:
        lines.append(f"- {task}: {item['left']} vs {item['right']}、left-only {item['left_only']}、right-only {item['right_only']}、p={item['p']:.4f}、Holm p={item['holm_p']:.4f}。")

lines += [
    "",
    f"全{verified} exact式を64入力で再評価し、160 record、40個のrandom Function、同一費用、task分離、source hashを監査した。3 task中2つは全条件でほぼ床、`route_cascade_mux`は全条件0/8だったため、route-family全般への外挿には限界がある。結果はBoolean beam探索に限り、学習抽象化、圧縮、実gate削減、速度、State、Router効果を示さない。",
    "",
    "## Roadmap",
    "",
    "- [Done] 同一dual-mux XORへの反復を止め、事前定義した5つの新規targetで固定Function、barrier、random同費用対照を比較した。",
    "- [Done] 精密数値と経路選択を分け、平均、不偏分散、効果量、bootstrap CI、exact検定、Holm補正を保存した。",
    "- [Next] taskを結果で選ばず生成する小規模grammarを凍結し、pilotで床・天井を測った後、別seedで中難度層を独立確認する。Function条件が探索容量を1 slot増やす交絡を消すため、no-transferにも同数のinert slotを入れる。",
    "- [Later] State付きFunctionと形成・分解を導入し、十分な再現性が得られてから負荷分散付きRouterと固定ランダム経路へ統合する。",
    "",
    "English: The frozen learned Function did not beat equal-cost random Functions across three preregistered routing tasks (−0.125 exact tasks/seed; 95% CI −0.375 to 0.000). It also suppressed the solvable numeric-sum target, while the one-hop barrier reached 6/8. The latter contrast was nominally significant but not significant after within-task Holm correction, so it is a hypothesis about harmful deep propagation rather than confirmation.",
    "",
    "简体中文：冻结的已学习函数在三个预注册路由任务上没有优于同成本随机函数（每个种子少0.125个精确任务；95% CI为−0.375至0.000）。它还抑制了可求解的数值求和任务，而一跳屏障达到6/8。该差异未经校正时显著，但在任务内Holm校正后不显著，因此目前只能作为“深层传播可能有害”的假设。",
    "",
    "[事前计划](../results/E031-route-family-portability/PROTOCOL.md) / [生数据](../results/E031-route-family-portability/run/results.json) / [Task manifest](../results/E031-route-family-portability/run/task_manifest.json) / [冻结Library](../results/E031-route-family-portability/run/frozen_libraries.json) / [审计摘要](../results/E031-route-family-portability/run/audit_summary.json)",
]
report = "\n".join(lines) + "\n"
(ROOT / "docs/STAR-Bit-E031-route-family-portability.md").write_text(report)
(HERE / "REPORT.md").write_text(report.replace("(../results/E031-route-family-portability/", "("))
print(json.dumps({"primary": primary, "interaction": interaction_result, "criterion": summary["portability_criterion_met"], "verified": verified, "direct_use": summary["direct_use"]}, indent=2))
