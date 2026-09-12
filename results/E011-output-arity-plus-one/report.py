"""Audit E011 and write its report."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mcnemar(left, right):
    left_only = sum(a and not b for a, b in zip(left, right))
    right_only = sum(b and not a for a, b in zip(left, right))
    n = left_only + right_only
    if n == 0:
        return 1.0, left_only, right_only
    k = min(left_only, right_only)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return min(1.0, p), left_only, right_only


def holm(p_values):
    order = sorted(range(len(p_values)), key=p_values.__getitem__)
    adjusted = [0.0] * len(p_values)
    prior = 0.0
    for rank, index in enumerate(order):
        prior = max(prior, min(1.0, p_values[index] * (len(p_values) - rank)))
        adjusted[index] = prior
    return adjusted


def ci(values, rng):
    values = np.asarray(values, dtype=float)
    sampled = values[rng.integers(0, len(values), size=(10000, len(values)))].mean(axis=1)
    return np.quantile(sampled, [0.025, 0.975]).tolist()


result = json.loads((OUT / "results.json").read_text())
rows = result["records"]
assert len(rows) == 216
assert sha(ROOT / "results/E009-output-bit-diagnosis/run/results.json") == result["e009_results_sha256"]
for relative, expected in result["source_hashes"].items():
    assert sha(ROOT / relative) == expected

verified = 0
for row in rows:
    stem = f"{row['task']}-{row['seed']}-{row['original_architecture']}-bit{row['bit']}-{row['condition']}"
    assert sha(OUT / f"{stem}.smt2.gz") == row["formula_sha256"]
    if row["status"] == "sat":
        witness = json.loads((OUT / f"{stem}-witness.json").read_text())
        x, y = base.data(row["task"])
        actual = base.evaluate(x, witness["wires"], witness["tables"], witness["outputs"])
        assert np.array_equal(actual, y[:, row["bit"] : row["bit"] + 1])
        verified += 1

pairs = {}
for row in rows:
    pairs.setdefault(row["case_index"], {})[row["condition"]] = row
assert len(pairs) == 108 and all(len(pair) == 2 for pair in pairs.values())

conditions = ("random_add", "influence_add")
seed_rates = {condition: [] for condition in conditions}
for seed in range(500, 516):
    selected = [pair for pair in pairs.values() if pair["random_add"]["seed"] == seed]
    for condition in conditions:
        seed_rates[condition].append(np.mean([pair[condition]["status"] == "sat" for pair in selected]))
rng = np.random.default_rng(1011)
stats = {}
for condition in conditions:
    values = seed_rates[condition]
    stats[condition] = dict(
        sat=sum(pair[condition]["status"] == "sat" for pair in pairs.values()),
        unknown=sum(pair[condition]["status"] == "unknown" for pair in pairs.values()),
        mean=float(np.mean(values)),
        variance=float(np.var(values, ddof=1)),
        ci95=ci(values, rng),
    )
diff = np.asarray(seed_rates["influence_add"]) - np.asarray(seed_rates["random_add"])
stats["difference"] = dict(mean=float(diff.mean()), variance=float(diff.var(ddof=1)), ci95=ci(diff, rng))

plans = [("all", None, None)] + [
    (f"{task}/{arch}", task, arch)
    for task in ("numeric", "selection")
    for arch in ("gate2", "lut4")
]
tests = []
for label, task, arch in plans:
    chosen = [
        pair for pair in pairs.values()
        if (task is None or pair["random_add"]["task"] == task)
        and (arch is None or pair["random_add"]["original_architecture"] == arch)
    ]
    left = [pair["random_add"]["status"] == "sat" for pair in chosen]
    right = [pair["influence_add"]["status"] == "sat" for pair in chosen]
    p, left_only, right_only = mcnemar(left, right)
    tests.append(dict(label=label, n=len(chosen), random=sum(left), influence=sum(right), left_only=left_only, right_only=right_only, p=p))
for test, adjusted in zip(tests, holm([test["p"] for test in tests])):
    test["holm_p"] = adjusted

lines = [
    "# E011：出力arityを1増やす",
    "",
    "実行日：2026-09-12。E009で単一bitがUNSATだった108caseについて、既存配線を残して出力ゲートへ生入力を1本追加した。元gate2はLUT3、元lut4はLUT5となる。新規学習ではない。",
    "",
    "| 条件 | SAT/108 | UNKNOWN | seed平均 | 不偏分散 | seed bootstrap 95% CI |",
    "| --- | ---: | ---: | ---: | ---: | --- |",
]
for condition in conditions:
    item = stats[condition]
    lines.append(f"| {condition} | {item['sat']} | {item['unknown']} | {item['mean']:.6f} | {item['variance']:.6f} | [{item['ci95'][0]:.6f}, {item['ci95'][1]:.6f}] |")
effect = stats["difference"]
lines += [
    "",
    f"influence−randomのseed平均差は{effect['mean']:+.6f}、不偏分散{effect['variance']:.6f}、95% CI [{effect['ci95'][0]:.6f}, {effect['ci95'][1]:.6f}]。UNKNOWNは固定予算内の未発見として扱った。",
    "",
    "| 比較 | n | random SAT | influence SAT | randomのみ | influenceのみ | exact p | Holm p |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for test in tests:
    lines.append(f"| {test['label']} | {test['n']} | {test['random']} | {test['influence']} | {test['left_only']} | {test['right_only']} | {test['p']:.6g} | {test['holm_p']:.6g} |")
lines += [
    "",
    "二側exact McNemarの5比較をHolm補正した。case内のbit依存があるためp値は診断用で、seed bootstrapを主な不確実性表示とする。",
    "",
    "## タスク・元構造別",
    "",
    "| task | 元構造 | 対象 | 条件 | SAT | UNSAT | UNKNOWN |",
    "| --- | --- | ---: | --- | ---: | ---: | ---: |",
]
for task in ("numeric", "selection"):
    for arch in ("gate2", "lut4"):
        for condition in conditions:
            chosen = [pair[condition] for pair in pairs.values() if pair[condition]["task"] == task and pair[condition]["original_architecture"] == arch]
            counts = [sum(row["status"] == status for row in chosen) for status in ("sat", "unsat", "unknown")]
            lines.append(f"| {task} | {arch} | {len(chosen)} | {condition} | {counts[0]} | {counts[1]} | {counts[2]} |")
lines += [
    "",
    f"両条件が同じ追加元を選んだcaseは{sum(pair['random_add']['same_source'] for pair in pairs.values())}/108。元gate2では真理値表を4→8bit、元lut4では16→32bitへ増やした。",
    "",
    "## 判定",
    "",
    "事前基準の10%回復には届かなかった。1接続追加だけでは大半の表現制約は残る。少数のSATは、隠れ配線全体を変更せず出力への情報経路と表容量だけを増やして回復できるcaseがあることを示す。influence条件の優位性は確認できない。",
    "",
    f"SAT証人{verified}件を保存ファイルから独立再評価し、対象bitの全64入力一致を確認した。216論理式、checkpoint、実行ソースhashも検査した。UNSATは独立proof checker未検証のZ3判定で、UNKNOWNは不能を意味しない。",
    "",
    f"Z3 {result['z3_version']}、NumPy {result['numpy_version']}、単一thread、各問2000ms、全実行{result['elapsed_seconds']:.1f}秒。influence条件は全正解を読むoracleであり、学習routingや汎化の証拠ではない。",
    "",
    "精密数値と経路選択を分けると、回復は元gate2ではnumericの2件のみ、元lut4では少数か時間切れだった。母数が大きく異なるため、タスク間の一般的な優劣とは結論しない。",
    "",
    "事前規則に従い、次は元接続を保持した2接続追加を同じ対照で診断する。それでも不足なら出力だけでなく隠れ層のボトルネックを局所化する。",
    "",
    "English: Adding one output input recovered only a few exact-synthesis cases and did not meet the preregistered 10% threshold. Oracle influence selection did not outperform random selection.",
    "",
    "简体中文：增加一条输出连接只恢复了少量精确综合案例，未达到预注册的10%阈值。基于目标影响度的选择未优于随机选择。",
    "",
    "[実行前計画](../results/E011-output-arity-plus-one/PROTOCOL.md) / [生データ](../results/E011-output-arity-plus-one/run/results.json)",
]

audit = dict(verified_witnesses=verified, statistics=stats, tests=tests)
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2))
text = "\n".join(lines) + "\n"
(HERE / "REPORT.md").write_text(text)
(ROOT / "docs/STAR-Bit-E011-output-arity-plus-one.md").write_text(text)
print(json.dumps(audit, indent=2))
