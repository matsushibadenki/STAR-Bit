"""Audit and report E021 cost-normalized promotion pilot."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/Users/littlebuddha/Desktop/alias/STAR-Bit")
HERE = Path(__file__).resolve().parent
OUT = HERE / "run"
E019 = ROOT / "results/E019-function-space-genesis"
sys.path.insert(0, str(E019))
import search as base


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(expression, inputs):
    if expression[0] == "input":
        return inputs[expression[1]]
    _, signature, code, left, right = expression
    value = base.lut_outputs(evaluate(left, inputs), evaluate(right, inputs))[code]
    assert value == int(signature)
    return value


def exact_sign_flip_p(differences):
    observed = abs(np.mean(differences))
    extreme = 0
    for mask in range(2 ** len(differences)):
        signed = [value * (1 if mask & (1 << index) else -1) for index, value in enumerate(differences)]
        extreme += abs(np.mean(signed)) >= observed - 1e-12
    return extreme / (2 ** len(differences))


def paired_summary(differences, rng):
    differences = np.asarray(differences, dtype=float)
    bootstrap = differences[rng.integers(0, len(differences), (10000, len(differences)))].mean(axis=1)
    sd = differences.std(ddof=1)
    return {
        "mean": float(differences.mean()),
        "variance": float(differences.var(ddof=1)),
        "ci95": np.quantile(bootstrap, [0.025, 0.975]).tolist(),
        "cohen_dz": None if sd == 0 else float(differences.mean() / sd),
        "exact_p": exact_sign_flip_p(differences),
        "paired_differences": differences.tolist(),
    }


result = json.loads((OUT / "results.json").read_text())
assert len(result["records"]) == 8
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected

inputs, targets = base.inputs_and_targets()
verified = 0
for row in result["records"]:
    for task, solution in row["solutions"].items():
        assert evaluate(solution["expression"], inputs) == targets[task]
        verified += 1

by_key = {(row["seed"], row["condition"]): row for row in result["records"]}
rng = np.random.default_rng(2021)
comparisons = {}
for metric in ("exact_targets", "final_promoted", "credited_signatures", "elapsed_seconds"):
    differences = [
        by_key[seed, "normalized_retired"][metric] - by_key[seed, "raw_promotion"][metric]
        for seed in result["settings"]["seeds"]
    ]
    comparisons[metric] = paired_summary(differences, rng)

raw = result["aggregate"]["raw_promotion"]
normalized = result["aggregate"]["normalized_retired"]
credited_reduction = 1 - normalized["credited_signatures"]["mean"] / raw["credited_signatures"]["mean"]
final_reduction = 1 - normalized["final_promoted"]["mean"] / raw["final_promoted"]["mean"]
runtime_reduction = 1 - normalized["elapsed_seconds"]["mean"] / raw["elapsed_seconds"]["mean"]

lines = [
    "# E021：Cost-normalized Promotion and Retirement pilot",
    "",
    "実行日：2026-09-13。E020のoffspring creditを、task間再利用、composition partner数、primitive・routing・depth費用で正規化し、2 round更新されないcreditを退役させた。新規4 seedを同一seedのraw promotion対照と比較した。",
    "",
    "## 主要結果",
    "",
    "| condition | exact target平均 | 不偏分散 | parity | comparator | mux | carry | 最終beam内credit付きFunction | credit台帳 | 秒平均 |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for condition in ("raw_promotion", "normalized_retired"):
    aggregate = result["aggregate"][condition]
    per_task = aggregate["exact_by_task"]
    lines.append(
        f"| {condition} | {aggregate['exact_targets']['mean']:.3f} | {aggregate['exact_targets']['variance']:.3f} | "
        f"{per_task['parity']}/4 | {per_task['comparator']}/4 | {per_task['mux']}/4 | {per_task['carry']}/4 | "
        f"{aggregate['final_promoted']['mean']:.2f} | {aggregate['credited_signatures']['mean']:.2f} | {aggregate['elapsed_seconds']['mean']:.3f} |"
    )

lines += [
    "",
    "| paired指標（normalized−raw） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |",
    "| --- | ---: | ---: | --- | ---: | ---: |",
]
for metric, label in (
    ("exact_targets", "exact targets"),
    ("final_promoted", "最終beam内credit付きFunction"),
    ("credited_signatures", "credit台帳"),
    ("elapsed_seconds", "実行秒"),
):
    comparison = comparisons[metric]
    dz = "NA" if comparison["cohen_dz"] is None else f"{comparison['cohen_dz']:.3f}"
    lines.append(
        f"| {label} | {comparison['mean']:+.3f} | {comparison['variance']:.3f} | "
        f"[{comparison['ci95'][0]:.3f}, {comparison['ci95'][1]:.3f}] | {dz} | {comparison['exact_p']:.3f} |"
    )

lines += [
    "",
    f"credit台帳は平均{credited_reduction:.1%}縮小し、実行時間は{runtime_reduction:.1%}短縮した。exact target平均は2.25から2.50へ低下せず、seed 1282でcarryを初めて発見した。一方、事前登録した主指標の『最終beam内credit付きFunctionを30%以上削減』は{final_reduction:.1%}削減に留まり、総合viability判定は不成立だった。target別上位枠にcredit済みFunctionが再流入するため、promotion専用枠を64へ減らしても最終beamのcredit付き総数は64に制限されない。",
    "",
    "4 seedのpilotでexact targets差は[0, 0, 1, 0]、exact sign-flip p=1.000であり、carry 1/4は発見事実であって再現性の証拠ではない。多重検定を伴う確証的主張は行わない。",
    "",
    "## 発見回路と構造費用",
    "",
    "normalized_retiredのcarryはseed 1282・round 8で15 primitives、106 routing bits、depth 7だった。comparatorはseed 1283でrawの16 primitives・114 bitsから13 primitives・92 bitsへ改善し、同じround 7で到達した。parityは全seed、muxも全seedで完全一致した。保存した全expressionをtruth table全64行で再評価し、全19解を検証した。",
    "",
    "carry到達は、古いcreditを捨てることが単なる省メモリ化ではなく、beamの競合を変えて新しい探索経路を開く場合があることを示す。ただし条件差には正規化、枠数、退役の三要因が含まれるため、どの要因がcarryに寄与したかはまだ分離できない。",
    "",
    "## 判定と次段階",
    "",
    "E021はarchive台帳と時間を減らしながら探索性能を維持したが、事前登録した最終beam 30%削減基準を満たさなかった。したがって『効率的な自律Module Genesisが成立した』とは判定しない。carryが少なくとも1 seedで見つかったため、事前計画どおり次は発見Functionの固定移植を16 seedで評価できる。移植元と評価先を分離し、同一run由来、別seed由来、ランダム同費用Functionを比較して、学習された中間Functionの効果を分離する。",
    "",
    "## Roadmap",
    "",
    "- [Done] creditをtask再利用と構造費用で正規化し、stale credit retirementを実装した。",
    "- [Done] 新規4 seedの対応比較で平均・不偏分散・bootstrap CI・効果量・exact sign-flip検定を報告した。",
    "- [Done] carry exactを初めて1/4 seedで発見し、全19回路を64入力で再検証した。",
    "- [Done] E022で移植元と評価seedを分離し、学習Function対ランダム同費用Functionを16 seedで比較した。",
    "- [Next] promotion枠由来とtarget枠への再流入を別々に記録し、正規化・枠数・retirementの要因を分解する。",
    "- [Next] E022の同一task transferを、target task由来Functionを除くleave-one-task-out条件へ進める。",
    "- [Later] task横断transfer後にFunctionを固定Moduleへ昇格し、別タスク学習step、総記述bit、primitive実行数を測る。",
    "",
    "English: Cost normalization and retirement reduced the credit registry by 46.9% and runtime by 5.5% without lowering mean target discovery. Carry was found for the first time in one of four seeds, but the preregistered 30% reduction in credited functions remaining in the final beam was not met, and the pilot is too small for a confirmatory claim.",
    "",
    "简体中文：成本归一化与退役机制使credit台账缩小46.9%，运行时间缩短5.5%，且平均目标发现数没有下降。首次在4个种子中的1个找到carry，但最终beam内带credit函数减少30%的预注册标准未达成，因此不能作确认性结论。",
    "",
    "[事前計画](../results/E021-cost-normalized-promotion/PROTOCOL.md) / [生データ](../results/E021-cost-normalized-promotion/run/results.json) / [監査要約](../results/E021-cost-normalized-promotion/run/audit_summary.json)",
]

audit = {
    "aggregate": result["aggregate"],
    "paired_comparisons": comparisons,
    "credited_registry_reduction": credited_reduction,
    "final_beam_credited_reduction": final_reduction,
    "runtime_reduction": runtime_reduction,
    "solutions_verified": verified,
    "main_threshold_met": result["viable"],
    "carry_found": normalized["exact_by_task"]["carry"] > 0,
}
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2))
text = "\n".join(lines) + "\n"
(HERE / "REPORT.md").write_text(text)
(ROOT / "docs/STAR-Bit-E021-cost-normalized-promotion.md").write_text(text)
print(json.dumps(audit, indent=2))
