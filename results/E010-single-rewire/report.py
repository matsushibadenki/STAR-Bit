"""Audit E010 artifacts and generate its immutable result report."""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "run"
sys.path.insert(0, str(ROOT / "results/E008-fixed-wiring-sat"))
import solve as base


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_mcnemar(a, b):
    random_only = sum(x == 1 and y == 0 for x, y in zip(a, b))
    guided_only = sum(x == 0 and y == 1 for x, y in zip(a, b))
    discordant = random_only + guided_only
    if discordant == 0:
        return 1.0, random_only, guided_only
    tail = min(random_only, guided_only)
    p = 2 * sum(math.comb(discordant, i) for i in range(tail + 1)) / (2**discordant)
    return min(1.0, p), random_only, guided_only


def holm(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted = [0.0] * len(values)
    running = 0.0
    count = len(values)
    for rank, index in enumerate(order):
        running = max(running, min(1.0, values[index] * (count - rank)))
        adjusted[index] = running
    return adjusted


def bootstrap_ci(values, rng, draws=10000):
    values = np.asarray(values, dtype=float)
    samples = values[rng.integers(0, len(values), size=(draws, len(values)))].mean(axis=1)
    return [float(x) for x in np.quantile(samples, [0.025, 0.975])]


result = json.loads((OUT / "results.json").read_text())
records = result["records"]
assert len(records) == 216
assert digest(ROOT / "results/E009-output-bit-diagnosis/run/results.json") == result["e009_results_sha256"]
for relative, expected in result["source_hashes"].items():
    assert digest(ROOT / relative) == expected

verified = 0
for row in records:
    stem = (
        f"{row['task']}-{row['seed']}-{row['architecture']}-"
        f"bit{row['bit']}-{row['condition']}"
    )
    formula = OUT / f"{stem}.smt2.gz"
    assert digest(formula) == row["formula_sha256"]
    if row["status"] == "sat":
        witness = json.loads((OUT / f"{stem}-witness.json").read_text())
        x, y = base.data(row["task"])
        predicted = base.evaluate(x, witness["wires"], witness["tables"], witness["outputs"])
        assert np.array_equal(predicted, y[:, row["bit"] : row["bit"] + 1])
        verified += 1

pairs = {}
for row in records:
    pairs.setdefault(row["case_index"], {})[row["condition"]] = row
assert len(pairs) == 108 and all(len(pair) == 2 for pair in pairs.values())

conditions = ["random_raw", "dependency_raw"]
seed_rates = {condition: [] for condition in conditions}
for seed in range(500, 516):
    seed_pairs = [pair for pair in pairs.values() if pair["random_raw"]["seed"] == seed]
    assert seed_pairs
    for condition in conditions:
        seed_rates[condition].append(np.mean([pair[condition]["status"] == "sat" for pair in seed_pairs]))

rng = np.random.default_rng(1010)
statistics = {}
for condition in conditions:
    values = seed_rates[condition]
    statistics[condition] = dict(
        mean=float(np.mean(values)),
        variance=float(np.var(values, ddof=1)),
        ci95=bootstrap_ci(values, rng),
        total_sat=sum(pair[condition]["status"] == "sat" for pair in pairs.values()),
    )
differences = np.asarray(seed_rates["dependency_raw"]) - np.asarray(seed_rates["random_raw"])
statistics["paired_difference"] = dict(
    mean=float(np.mean(differences)),
    variance=float(np.var(differences, ddof=1)),
    ci95=bootstrap_ci(differences, rng),
)

tests = [("all", None, None)] + [
    (f"{task}/{architecture}", task, architecture)
    for task in ("numeric", "selection")
    for architecture in ("gate2", "lut4")
]
test_rows = []
for label, task, architecture in tests:
    selected = [
        pair
        for pair in pairs.values()
        if (task is None or pair["random_raw"]["task"] == task)
        and (architecture is None or pair["random_raw"]["architecture"] == architecture)
    ]
    random_hits = [int(pair["random_raw"]["status"] == "sat") for pair in selected]
    guided_hits = [int(pair["dependency_raw"]["status"] == "sat") for pair in selected]
    p, random_only, guided_only = exact_mcnemar(random_hits, guided_hits)
    test_rows.append(
        dict(
            label=label,
            n=len(selected),
            random_sat=sum(random_hits),
            guided_sat=sum(guided_hits),
            difference=float(np.mean(guided_hits) - np.mean(random_hits)),
            random_only=random_only,
            guided_only=guided_only,
            p=p,
        )
    )
for row, adjusted in zip(test_rows, holm([row["p"] for row in test_rows])):
    row["holm_p"] = adjusted

same = sum(pair["random_raw"]["same_replacement"] for pair in pairs.values())
fallback = sum(pair["dependency_raw"]["guided_fallback"] for pair in pairs.values())
unknown = {condition: sum(pair[condition]["status"] == "unknown" for pair in pairs.values()) for condition in conditions}

lines = [
    "# E010：出力直前の1接続修正",
    "",
    "実行日：2026-09-12。E009で単一出力bitがUNSATだった108caseについて、出力ゲートの入力接続を1本だけ生入力へ変更し、全64入力に一致するゲート表が存在するかを調べた。ゲート数は増やしていない。",
    "",
    "`random_raw`は無作為な生入力、`dependency_raw`は正解真理値表から求めた依存入力のうち、元の出力祖先にない入力を使う。後者はoracle診断であり、学習法ではない。",
    "",
    "## 主要結果",
    "",
    "| 条件 | SAT/108 | seed平均 | 不偏分散 | seed bootstrap 95% CI | UNKNOWN |",
    "| --- | ---: | ---: | ---: | --- | ---: |",
]
for condition in conditions:
    item = statistics[condition]
    lines.append(
        f"| {condition} | {item['total_sat']} | {item['mean']:.6f} | "
        f"{item['variance']:.6f} | [{item['ci95'][0]:.6f}, {item['ci95'][1]:.6f}] | {unknown[condition]} |"
    )
effect = statistics["paired_difference"]
lines += [
    "",
    f"依存入力修正−無作為修正のseed平均差は{effect['mean']:+.6f}、不偏分散{effect['variance']:.6f}、95% CI [{effect['ci95'][0]:.6f}, {effect['ci95'][1]:.6f}]。UNKNOWNは固定1秒予算で未発見として数えた。",
    "",
    "## 事前指定したpaired比較",
    "",
    "| 範囲 | n | random SAT | dependency SAT | 差 | randomのみ | dependencyのみ | exact p | Holm p |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for row in test_rows:
    lines.append(
        f"| {row['label']} | {row['n']} | {row['random_sat']} | {row['guided_sat']} | "
        f"{row['difference']:+.6f} | {row['random_only']} | {row['guided_only']} | "
        f"{row['p']:.6g} | {row['holm_p']:.6g} |"
    )
lines += [
    "",
    "検定は二側exact McNemar、5比較をHolm補正した。同じseed内の複数bitは独立ではないため、case水準のp値は診断用であり、seed bootstrap CIを主な不確実性表示とする。",
    "",
    "## タスク種別と構造別",
    "",
    "| task | 構造 | 対象 | 条件 | SAT | UNSAT | UNKNOWN |",
    "| --- | --- | ---: | --- | ---: | ---: | ---: |",
]
for task in ("numeric", "selection"):
    for architecture in ("gate2", "lut4"):
        for condition in conditions:
            selected = [
                pair[condition]
                for pair in pairs.values()
                if pair[condition]["task"] == task and pair[condition]["architecture"] == architecture
            ]
            counts = [sum(row["status"] == status for row in selected) for status in ("sat", "unsat", "unknown")]
            lines.append(
                f"| {task} | {architecture} | {len(selected)} | {condition} | "
                f"{counts[0]} | {counts[1]} | {counts[2]} |"
            )
lines += [
    "",
    f"両条件が同じ接続先を偶然選んだcaseは{same}/108。依存入力が祖先にすべて存在したためfallbackしたcaseは{fallback}/108。",
    "全108caseで正解bitに関係する生入力はすでに出力祖先へ到達していた。このため、事前仮説の『欠けた依存入力を1本補う』操作は一度も適用されず、dependency_rawは関連入力への直結バイパスとして働いた。到達性不足ではなく、有限幅の中間表現または出力arityを含む情報ボトルネックが候補として残る。",
    "",
    "## 検証と限界",
    "",
    f"SAT証人は{verified}件で、今回は再評価対象がなかった。216論理式、元checkpoint、実行ソースのhashを検査した。全判定はUNSATだったが、独立proof checkerでは検証していないためZ3の判定として扱う。",
    "",
    f"Z3 {result['z3_version']}、NumPy {result['numpy_version']}、単一thread、各問1000ms、全実行{result['elapsed_seconds']:.1f}秒。正解表を用いた接続選択と全入力SAT合成なので、未知入力への汎化、勾配学習、学習されたrouting、抽象化の証拠ではない。",
    "",
    "精密数値タスクと経路選択タスクを分けて示した。構造差だけでなく、出力bitの依存変数数と回路の深さが異なるため、タスク間差を一般的な難易度差と断定しない。",
    "",
    "## 次の改善案",
    "",
    "依存入力への1接続修正でSATが増えるなら、次は全正解を見ない接続提案器を導入し、同じ1接続予算の固定ランダム対照と複数seedで学習精度を比較する。改善しない構造には、事前固定した2接続修正を試し、ゲート追加より先に配線自由度の寄与を分離する。",
    "",
    "Routerをまだ扱わないため、負荷分散補助損失、固定ランダムrouting、同一ラン内から別seedへのExpert交換は後続MoE統合実験の必須対照として維持する。",
    "",
    "English: One output wire was replaced with either a random raw input or an oracle target-dependent input. SAT witnesses were independently evaluated. This is an exact-synthesis diagnosis, not learned routing or generalization.",
    "",
    "简体中文：将输出门的一条连接替换为随机原始输入或由目标依赖关系选择的输入。SAT见证经过独立求值。这是精确综合诊断，不代表学习路由或泛化。",
    "",
    "[実行前計画](../results/E010-single-rewire/PROTOCOL.md) / [生データ](../results/E010-single-rewire/run/results.json)",
]

audit = dict(
    verified_witnesses=verified,
    statistics=statistics,
    tests=test_rows,
    same_replacement_cases=same,
    guided_fallback_cases=fallback,
)
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2))
text = "\n".join(lines) + "\n"
(HERE / "REPORT.md").write_text(text)
(ROOT / "docs/STAR-Bit-E010-single-rewire.md").write_text(text)
print(json.dumps(audit, indent=2))
