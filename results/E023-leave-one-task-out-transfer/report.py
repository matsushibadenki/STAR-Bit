"""Audit and report E023 leave-one-task-out transfer."""
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path("/Users/littlebuddha/Desktop/alias/STAR-Bit")
HERE = Path(__file__).resolve().parent
OUT = HERE / "run"
E019 = ROOT / "results/E019-function-space-genesis"
sys.path.insert(0, str(E019))
import search as base

spec = importlib.util.spec_from_file_location("e023_main", HERE / "main.py")
experiment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(experiment)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(expression, inputs):
    if expression[0] == "input":
        return inputs[expression[1]]
    signature = int(expression[1])
    value = base.lut_outputs(evaluate(expression[3], inputs), evaluate(expression[4], inputs))[expression[2]]
    assert value == signature
    return value


def expression_signatures(expression):
    if expression[0] == "input":
        return set()
    return {int(expression[1])} | expression_signatures(expression[3]) | expression_signatures(expression[4])


def exact_sign_flip_p(differences):
    observed = abs(np.mean(differences))
    extreme = 0
    for mask in range(2 ** len(differences)):
        signed = [value * (1 if mask & (1 << index) else -1) for index, value in enumerate(differences)]
        extreme += abs(np.mean(signed)) >= observed - 1e-12
    return extreme / (2 ** len(differences))


def exact_mcnemar(left, right):
    left_only = sum(a and not b for a, b in zip(left, right))
    right_only = sum(b and not a for a, b in zip(left, right))
    discordant = left_only + right_only
    if discordant == 0:
        return 1.0, left_only, right_only
    tail = sum(math.comb(discordant, k) for k in range(min(left_only, right_only) + 1)) / (2 ** discordant)
    return min(1.0, 2 * tail), left_only, right_only


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


def paired_summary(differences, rng):
    values = np.asarray(differences, dtype=float)
    bootstrap = values[rng.integers(0, len(values), (20000, len(values)))].mean(axis=1)
    sd = values.std(ddof=1)
    return {
        "mean": float(values.mean()),
        "variance": float(values.var(ddof=1)),
        "ci95": np.quantile(bootstrap, [0.025, 0.975]).tolist(),
        "cohen_dz": None if sd == 0 else float(values.mean() / sd),
        "exact_sign_flip_p": exact_sign_flip_p(values),
        "paired_differences": values.tolist(),
    }


result = json.loads((OUT / "results.json").read_text())
assert len(result["records"]) == 256
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected

inputs, targets = base.inputs_and_targets()
manifest = json.loads((OUT / "cross_task_libraries.json").read_text())
rebuilt_libraries = {}
for task in base.TASKS:
    library, rebuilt_manifest = experiment.build_cross_task_library(task)
    rebuilt_libraries[task] = library
    assert rebuilt_manifest == manifest[task]
    assert all(task not in item["source_tasks"] for item in manifest[task])
    assert len(library) == 8
    assert not ({candidate.signature for candidate in library} & (set(inputs) | set(targets.values())))

verified = 0
transfer_used = 0
residuals = []
for row in result["records"]:
    task = row["task"]
    if row["condition"] == "learned_cross_task":
        expected_library = rebuilt_libraries[task]
    elif row["condition"] == "random_cost_matched":
        expected_library, expected_residuals = experiment.random_library(rebuilt_libraries[task], task, row["seed"], False)
        assert expected_residuals == row["error_match_residuals"]
    elif row["condition"] == "random_error_matched":
        expected_library, expected_residuals = experiment.random_library(rebuilt_libraries[task], task, row["seed"], True)
        assert expected_residuals == row["error_match_residuals"]
        residuals.extend(expected_residuals)
    else:
        expected_library = []
    assert [str(candidate.signature) for candidate in expected_library] == row["library_signatures"]
    if expected_library:
        assert [candidate.cost() for candidate in expected_library] == [candidate.cost() for candidate in rebuilt_libraries[task]]
    if row["solution"]:
        solution = row["solution"]
        assert evaluate(solution["expression"], inputs) == targets[task]
        library_signatures = {candidate.signature for candidate in expected_library}
        used = expression_signatures(solution["expression"]) & library_signatures
        assert bool(used) == solution["uses_transferred_function"]
        assert sorted(str(signature) for signature in used) == sorted(solution["transferred_signatures_used"])
        verified += 1
        transfer_used += bool(used)

by_key = {(row["seed"], row["task"], row["condition"]): row for row in result["records"]}
seeds = result["settings"]["seeds"]
rng = np.random.default_rng(2023)


def per_seed_counts(condition):
    return [sum(by_key[seed, task, condition]["exact"] for task in base.TASKS) for seed in seeds]


primary = paired_summary(
    np.asarray(per_seed_counts("learned_cross_task")) - np.asarray(per_seed_counts("random_error_matched")), rng
)
secondary_cost = paired_summary(
    np.asarray(per_seed_counts("learned_cross_task")) - np.asarray(per_seed_counts("random_cost_matched")), rng
)
secondary_none = paired_summary(
    np.asarray(per_seed_counts("learned_cross_task")) - np.asarray(per_seed_counts("no_transfer")), rng
)

task_tests = []
for task in base.TASKS:
    learned = [by_key[seed, task, "learned_cross_task"]["exact"] for seed in seeds]
    control = [by_key[seed, task, "random_error_matched"]["exact"] for seed in seeds]
    pvalue, learned_only, control_only = exact_mcnemar(learned, control)
    task_tests.append({"task": task, "learned_only": learned_only, "control_only": control_only, "p": pvalue})
adjusted = holm([item["p"] for item in task_tests])
for item, value in zip(task_tests, adjusted):
    item["holm_p"] = value

learned_only_rows = []
for seed in seeds:
    for task in base.TASKS:
        learned = by_key[seed, task, "learned_cross_task"]
        control = by_key[seed, task, "random_error_matched"]
        if learned["exact"] and not control["exact"]:
            learned_only_rows.append(learned)
all_learned_only_use_transfer = bool(learned_only_rows) and all(row["solution"]["uses_transferred_function"] for row in learned_only_rows)
hard_improvement = max(item["learned_only"] for item in task_tests if item["task"] in ("comparator", "carry"))
promising = primary["mean"] >= 0.25 and primary["ci95"][0] > 0 and hard_improvement >= 4 and all_learned_only_use_transfer

residual_array = np.asarray(residuals, dtype=float)
residual_summary = {
    "mean": float(residual_array.mean()),
    "variance": float(residual_array.var(ddof=1)),
    "median": float(np.median(residual_array)),
    "maximum": int(residual_array.max()),
    "exact_match_fraction": float(np.mean(residual_array == 0)),
}

aggregate = result["aggregate"]
lines = [
    "# E023：Leave-one-task-out Function Transfer",
    "",
    "実行日：2026-09-13。各評価taskについて、そのtaskのsource回路を完全に除外し、残る3 taskから費用帯別に8内部Functionを固定移植した。新規16 seed、4 task、4条件の256探索を事前固定した設定で実行した。",
    "",
    "## 主要結果",
    "",
    "| condition | exact / 64 | 成功率平均 | 不偏分散 | parity | comparator | mux | carry | 秒平均 / task |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for condition in ("no_transfer", "random_cost_matched", "random_error_matched", "learned_cross_task"):
    item = aggregate[condition]
    per_task = item["exact_by_task"]
    total = sum(per_task.values())
    lines.append(
        f"| {condition} | {total}/64 | {item['exact']['mean']:.4f} | {item['exact']['variance']:.4f} | "
        f"{per_task['parity']}/16 | {per_task['comparator']}/16 | {per_task['mux']}/16 | {per_task['carry']}/16 | {item['elapsed_seconds']['mean']:.3f} |"
    )

lines += [
    "",
    "| paired比較（1 seed当たりexact task数） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |",
    "| --- | ---: | ---: | --- | ---: | ---: |",
]
for label, comparison in (
    ("learned−error-matched random（primary）", primary),
    ("learned−cost-matched random", secondary_cost),
    ("learned−no transfer", secondary_none),
):
    dz = "NA" if comparison["cohen_dz"] is None else f"{comparison['cohen_dz']:.3f}"
    lines.append(
        f"| {label} | {comparison['mean']:+.4f} | {comparison['variance']:.4f} | "
        f"[{comparison['ci95'][0]:.4f}, {comparison['ci95'][1]:.4f}] | {dz} | {comparison['exact_sign_flip_p']:.6f} |"
    )

lines += [
    "",
    "primaryのlearned cross-taskとerror-matched randomはいずれも27/64で、対応平均差は0だった。通常のcost-matched randomは37/64、移植なしは34/64で、learned cross-taskの27/64を上回った。事前登録したtask-crossing transfer基準は不成立である。",
    "",
    "## タスク別結果",
    "",
    "| task | learned | error-matched random | learnedのみ成功 | controlのみ成功 | exact McNemar p | Holm p |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for item in task_tests:
    task = item["task"]
    lines.append(
        f"| {task} | {aggregate['learned_cross_task']['exact_by_task'][task]}/16 | {aggregate['random_error_matched']['exact_by_task'][task]}/16 | "
        f"{item['learned_only']} | {item['control_only']} | {item['p']:.6f} | {item['holm_p']:.6f} |"
    )

lines += [
    "",
    "learned cross-taskはparity 10/16、comparator 0/16、mux 16/16、carry 1/16だった。経路選択muxは全条件16/16で飽和し、構造追加の差を測れない。精密Boolean側ではcomparator/carryへのtask横断再利用は確認できず、E022で増えた難タスク到達は同一task由来Functionへの依存が強かったと解釈するのが妥当である。",
    "",
    f"error-matched controlの512スロットにおけるlearned Functionとのtruth-table誤差差は平均{residual_summary['mean']:.3f} bit、中央値{residual_summary['median']:.1f}、最大{residual_summary['maximum']}で、完全一致率は{residual_summary['exact_match_fraction']:.1%}だった。それでも通常のcost-matched randomより成功が少ないため、単体のtarget errorを揃えることは良い踏み石を作る十分条件ではない。error類似Functionへの集中が機能多様性を失わせた可能性がある。",
    "",
    "learned条件のexact 27解のうち、移植signatureを最終式に含んだのは3解だけだった。Libraryは固定枠を占めて探索軌跡を変えたものの、多くの解で計算部品として再利用されていない。保存した全125 exact式は64入力で再評価した。",
    "",
    "## 結論と次の改善",
    "",
    "E022が示したのは同一task・別seedへの部分回路transferであり、E023では別taskへ持ち出せるConceptを確認できなかった。Module Genesisの現在のボトルネックは、Functionを保存することから、複数taskで因果的に役立つFunctionを選ぶことへ移った。",
    "",
    "次はsource task名ではなく、Functionが未知のprobe task群で生む改善量をcreditにする。Library slotを占めるだけのFunctionと実際に式へ組み込まれるFunctionを分離し、cross-task offspring utility、機能多様性、費用を同時に最適化する。新しいtask familyをsource選定後に生成し、選定用taskへの過適合も分離する。",
    "",
    "## Roadmap",
    "",
    "- [Done] target task由来Functionを完全に除外したleave-one-task-out Libraryを4 task別に構成した。",
    "- [Done] 16 seed、256探索でcost-matched random、error-matched oracle random、移植なしを比較した。",
    "- [Done] 平均・不偏分散・bootstrap CI・効果量・exact検定・Holm補正と全125式の再評価を完了した。",
    "- [Done] task-crossing transfer基準は不成立。learnedとprimary controlは27/64で同率、learned Function使用は3/27解だった。",
    "- [Next] 未知probe taskでのoffspring改善を使うcross-task utility creditと、signature多様性制約を追加する。",
    "- [Next] source選定後に固定した新規task familyで、Library selectionへの過適合を測る。",
    "- [Later] task横断再利用が成立してからSTAR-Bit Routerへ統合し、load balance、固定random route、Expert交換、総回路費用を再評価する。",
    "",
    "English: Removing every same-task source circuit eliminated the E022 transfer advantage. Learned cross-task Functions and the error-matched random control both solved 27/64 cases, while cost-matched random Functions solved 37/64. Only 3/27 learned-condition solutions actually used a transferred Function. Cross-seed reuse is supported; cross-task conceptual reuse is not.",
    "",
    "简体中文：完全排除同任务源电路后，E022的迁移优势消失。跨任务学习函数与误差匹配随机对照均成功27/64，而成本匹配随机函数成功37/64；学习条件中只有3/27个解实际使用了迁移函数。目前支持跨种子复用，但不支持跨任务概念复用。",
    "",
    "[事前計画](../results/E023-leave-one-task-out-transfer/PROTOCOL.md) / [生データ](../results/E023-leave-one-task-out-transfer/run/results.json) / [Library](../results/E023-leave-one-task-out-transfer/run/cross_task_libraries.json) / [監査要約](../results/E023-leave-one-task-out-transfer/run/audit_summary.json)",
]

audit = {
    "aggregate": aggregate,
    "primary_comparison": primary,
    "secondary_cost_comparison": secondary_cost,
    "secondary_no_transfer_comparison": secondary_none,
    "task_tests": task_tests,
    "error_match_residual": residual_summary,
    "solutions_verified": verified,
    "solutions_using_any_transfer": transfer_used,
    "learned_only_successes": len(learned_only_rows),
    "all_learned_only_successes_use_transfer": all_learned_only_use_transfer,
    "promising_threshold_met": promising,
}
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2))
text = "\n".join(lines) + "\n"
(HERE / "REPORT.md").write_text(text)
(ROOT / "docs/STAR-Bit-E023-leave-one-task-out-transfer.md").write_text(text)
print(json.dumps(audit, indent=2))
