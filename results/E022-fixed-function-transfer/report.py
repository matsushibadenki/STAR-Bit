"""Audit and report E022 fixed learned-Function transfer."""
import hashlib
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
    tail = sum(math.comb(discordant, k) for k in range(0, min(left_only, right_only) + 1)) / (2 ** discordant)
    return min(1.0, 2 * tail), left_only, right_only


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    total = len(pvalues)
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (total - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


result = json.loads((OUT / "results.json").read_text())
assert len(result["records"]) == 48
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected

inputs, targets = base.inputs_and_targets()
verified = 0
transfer_membership_verified = 0
for row in result["records"]:
    library = {int(signature) for signature in row["library_signatures"]}
    for task, solution in row["solutions"].items():
        assert evaluate(solution["expression"], inputs) == targets[task]
        used = expression_signatures(solution["expression"]) & library
        assert bool(used) == solution["uses_transferred_function"]
        assert sorted(str(signature) for signature in used) == sorted(solution["transferred_signatures_used"])
        verified += 1
        transfer_membership_verified += bool(used)

manifest = json.loads((OUT / "learned_library.json").read_text())
assert len(manifest) == 16
target_signatures = set(targets.values())
assert not ({int(item["signature"]) for item in manifest} & (set(inputs) | target_signatures))

by_key = {(row["seed"], row["condition"]): row for row in result["records"]}
seeds = result["settings"]["seeds"]
differences = np.array([
    by_key[seed, "learned_transfer"]["exact_targets"] - by_key[seed, "random_matched"]["exact_targets"]
    for seed in seeds
], dtype=float)
rng = np.random.default_rng(2022)
bootstrap = differences[rng.integers(0, len(differences), (20000, len(differences)))].mean(axis=1)
sd = differences.std(ddof=1)
primary = {
    "mean": float(differences.mean()),
    "variance": float(differences.var(ddof=1)),
    "ci95": np.quantile(bootstrap, [0.025, 0.975]).tolist(),
    "cohen_dz": float(differences.mean() / sd),
    "exact_sign_flip_p": exact_sign_flip_p(differences),
    "paired_differences": differences.tolist(),
}

task_tests = []
for task in base.TASKS:
    learned = [task in by_key[seed, "learned_transfer"]["solutions"] for seed in seeds]
    random_control = [task in by_key[seed, "random_matched"]["solutions"] for seed in seeds]
    pvalue, learned_only, random_only = exact_mcnemar(learned, random_control)
    task_tests.append({"task": task, "learned_only": learned_only, "random_only": random_only, "p": pvalue})
adjusted = holm([item["p"] for item in task_tests])
for item, value in zip(task_tests, adjusted):
    item["holm_p"] = value

hard_improvement = max(item["learned_only"] for item in task_tests if item["task"] in ("comparator", "carry"))
all_learned_solutions_use_transfer = all(
    solution["uses_transferred_function"]
    for row in result["records"]
    if row["condition"] == "learned_transfer"
    for solution in row["solutions"].values()
)
promising = (
    primary["mean"] >= 0.5
    and primary["ci95"][0] > 0
    and hard_improvement >= 4
    and all_learned_solutions_use_transfer
)

aggregate = result["aggregate"]
lines = [
    "# E022：Fixed Learned-Function Transfer",
    "",
    "実行日：2026-09-13。E021のexact回路から出力Functionと生入力を除いた内部signatureを費用帯別に16個固定し、新規16 search seedへ移植した。同じ式木形状のLUTと入力だけを無作為化した同費用Library、移植なしを比較した。source seed 1280–1283と評価seed 1300–1315は分離している。",
    "",
    "## 主要結果",
    "",
    "| condition | exact target平均 | 不偏分散 | parity | comparator | mux | carry | 秒平均 |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for condition in ("no_transfer", "random_matched", "learned_transfer"):
    item = aggregate[condition]
    per_task = item["exact_by_task"]
    lines.append(
        f"| {condition} | {item['exact_targets']['mean']:.4f} | {item['exact_targets']['variance']:.4f} | "
        f"{per_task['parity']}/16 | {per_task['comparator']}/16 | {per_task['mux']}/16 | {per_task['carry']}/16 | {item['elapsed_seconds']['mean']:.3f} |"
    )

lines += [
    "",
    "| learned−random matched | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |",
    "| ---: | ---: | --- | ---: | ---: |",
    f"| {primary['mean']:+.4f} | {primary['variance']:.4f} | [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}] | {primary['cohen_dz']:.3f} | {primary['exact_sign_flip_p']:.6f} |",
    "",
    "学習Libraryはランダム同費用Libraryより1 seed当たり平均0.5625個多くexact targetへ到達し、bootstrap区間は0を除いた。事前登録した+0.5基準を満たした。no-transferは初回候補数が少なく生成予算も一致しないため、参考値としてのみ扱う。",
    "",
    "## タスク別の構造自由度",
    "",
    "| task | learned | random matched | learnedのみ成功 | randomのみ成功 | exact McNemar p | Holm p |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for item in task_tests:
    task = item["task"]
    lines.append(
        f"| {task} | {aggregate['learned_transfer']['exact_by_task'][task]}/16 | {aggregate['random_matched']['exact_by_task'][task]}/16 | "
        f"{item['learned_only']} | {item['random_only']} | {item['p']:.6f} | {item['holm_p']:.6f} |"
    )

lines += [
    "",
    "comparatorは1/16から5/16、carryは1/16から4/16へ増えた。comparatorのlearnedのみ成功が4 seedで事前基準を満たしたが、4タスクのHolm補正後に有意な個別差はない。parityは12/16から14/16、既に飽和したmuxは両条件16/16だった。したがって今回の構造自由度は、簡単な経路選択muxよりも、多段の精密Boolean構成を要するcomparator/carryで到達可能性を広げる傾向を示した。",
    "",
    "learned_transferの39/39 exact解は移植signatureを少なくとも1個含んだ。ランダムLibraryでも15解が移植signatureを使い、comparatorとcarryを各1回発見した。追加枠や固定保持だけでも探索は変わるが、費用を揃えた対応対照より学習Functionが上回った。",
    "",
    "## 解釈の境界",
    "",
    "事前登録したpromising基準は満たしたため、学習された中間Functionが別search seedの探索到達性を改善する証拠が得られた。これはE020/E021のarchive内昇格から、初めて固定Libraryとしての再利用へ進んだ節目である。",
    "",
    "ただしLibraryには評価対象と同じtaskのsource回路から得た部分回路が含まれる。出力signature自体は除外したが、comparator/carryの出力一歩手前に近いtask固有Functionを含み得る。今回示したのは同一タスク・別seedのsource-informed transferであり、別タスクへ使えるConcept、自然発生的なtask-independent Module、計算量削減の証明ではない。ランダムLibraryはseedごとに異なるため、単一の対照生成分布に対する結果でもある。",
    "",
    "## Roadmap",
    "",
    "- [Done] sourceと評価seedを分離し、出力を除いた16 learned Functionsを固定Libraryとして移植した。",
    "- [Done] 同じprimitive・routing・depthと式木形状を持つ固定random Libraryを対照にした。",
    "- [Done] 16 seedで平均・不偏分散・bootstrap CI・効果量・exact検定・Holm補正を報告し、保存した95 exact解を全64入力で再検証した。",
    "- [Done] learned−random exact target差+0.5625、95% CIが0を除き、comparatorのlearnedのみ成功4 seedという事前基準を満たした。",
    "- [Done] E023でtarget task由来Functionを除くleave-one-task-out移植と、truth-table errorを揃える対照を実施した。task横断優位性は確認できなかった。",
    "- [Next] 同一Libraryを複数random control Libraryと比較し、Library抽選の分散をモデルseedの分散から分離する。",
    "- [Next] 未知probe taskへのoffspring寄与とsignature多様性からcross-task Moduleを選定する。",
    "- [Later] task横断transferが再現した後にLibrary記述bit、物理primitive、active演算、Router・State費用を含む総費用でSTAR-Bit本体へ統合する。",
    "",
    "English: A fixed 16-Function Library learned from separate source seeds improved exact target discovery by +0.5625 over shape- and cost-matched random Functions across 16 evaluation seeds. The preregistered pilot criterion was met, especially through comparator/carry reachability, but same-task source subcircuits were allowed; task-independent conceptual transfer remains untested.",
    "",
    "简体中文：在16个独立评估种子中，来自分离源种子的16个固定学习函数，相比形状与成本匹配的随机函数，使精确目标发现平均提高+0.5625，并满足预注册pilot标准。提升主要来自comparator/carry，但源库允许同任务子电路，因此尚未证明任务无关的概念迁移。",
    "",
    "[事前計画](../results/E022-fixed-function-transfer/PROTOCOL.md) / [生データ](../results/E022-fixed-function-transfer/run/results.json) / [Library](../results/E022-fixed-function-transfer/run/learned_library.json) / [監査要約](../results/E022-fixed-function-transfer/run/audit_summary.json)",
]

audit = {
    "aggregate": aggregate,
    "primary_comparison": primary,
    "task_tests": task_tests,
    "solutions_verified": verified,
    "solutions_using_any_transfer": transfer_membership_verified,
    "all_learned_solutions_use_transfer": all_learned_solutions_use_transfer,
    "source_library_size": len(manifest),
    "source_outputs_excluded": True,
    "promising_threshold_met": promising,
}
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2))
text = "\n".join(lines) + "\n"
(HERE / "REPORT.md").write_text(text)
(ROOT / "docs/STAR-Bit-E022-fixed-function-transfer.md").write_text(text)
print(json.dumps(audit, indent=2))
