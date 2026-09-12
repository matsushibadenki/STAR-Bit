"""Audit E012 and create a statistical report."""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "run"
sys.path.insert(0, str(ROOT / "results/E008-fixed-wiring-sat"))
import solve as base


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def paired_p(left, right):
    left_only = sum(a and not b for a, b in zip(left, right))
    right_only = sum(b and not a for a, b in zip(left, right))
    n = left_only + right_only
    if not n: return 1.0, left_only, right_only
    k = min(left_only, right_only)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n), left_only, right_only


def holm(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    answer, running = [0.0] * len(values), 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, values[index] * (len(values) - rank)))
        answer[index] = running
    return answer


def boot(values, rng):
    values = np.asarray(values, float)
    means = values[rng.integers(0, len(values), (10000, len(values)))].mean(1)
    return np.quantile(means, [.025, .975]).tolist()


result = json.loads((OUT / "results.json").read_text())
rows = result["records"]
assert len(rows) == 216
assert sha(ROOT / "results/E009-output-bit-diagnosis/run/results.json") == result["e009_results_sha256"]
for relative, expected in result["source_hashes"].items(): assert sha(ROOT / relative) == expected
verified = 0
for row in rows:
    stem = f"{row['task']}-{row['seed']}-{row['original_architecture']}-bit{row['bit']}-{row['condition']}"
    assert sha(OUT / f"{stem}.smt2.gz") == row["formula_sha256"]
    if row["status"] == "sat":
        witness = json.loads((OUT / f"{stem}-witness.json").read_text())
        x, y = base.data(row["task"])
        assert np.array_equal(base.evaluate(x, witness["wires"], witness["tables"], witness["outputs"]), y[:, row["bit"]:row["bit"] + 1])
        verified += 1
pairs = {}
for row in rows: pairs.setdefault(row["case_index"], {})[row["condition"]] = row
assert len(pairs) == 108 and all(len(pair) == 2 for pair in pairs.values())

conditions = ("random_add2", "influence_add2")
rates = {condition: [] for condition in conditions}
for seed in range(500, 516):
    group = [pair for pair in pairs.values() if pair["random_add2"]["seed"] == seed]
    for condition in conditions: rates[condition].append(np.mean([pair[condition]["status"] == "sat" for pair in group]))
rng = np.random.default_rng(1012)
stats = {}
for condition in conditions:
    values = rates[condition]
    stats[condition] = dict(sat=sum(pair[condition]["status"] == "sat" for pair in pairs.values()), unknown=sum(pair[condition]["status"] == "unknown" for pair in pairs.values()), mean=float(np.mean(values)), variance=float(np.var(values, ddof=1)), ci95=boot(values, rng))
delta = np.asarray(rates["influence_add2"]) - np.asarray(rates["random_add2"])
stats["difference"] = dict(mean=float(delta.mean()), variance=float(delta.var(ddof=1)), ci95=boot(delta, rng))

specs = [("all", None, None)] + [(f"{task}/{arch}", task, arch) for task in ("numeric", "selection") for arch in ("gate2", "lut4")]
tests = []
for label, task, arch in specs:
    group = [pair for pair in pairs.values() if (task is None or pair["random_add2"]["task"] == task) and (arch is None or pair["random_add2"]["original_architecture"] == arch)]
    left = [pair["random_add2"]["status"] == "sat" for pair in group]
    right = [pair["influence_add2"]["status"] == "sat" for pair in group]
    p, left_only, right_only = paired_p(left, right)
    tests.append(dict(label=label, n=len(group), random=sum(left), influence=sum(right), random_only=left_only, influence_only=right_only, p=p))
for row, adjusted in zip(tests, holm([row["p"] for row in tests])): row["holm_p"] = adjusted

lines = ["# E012：出力arityを2増やす", "", "実行日：2026-09-12。E009で単一bitがUNSATだった108caseに、元接続を残して異なる生入力を2本追加した。元gate2はLUT4、元lut4はLUT6となる。", "", "| 条件 | SAT/108 | UNKNOWN | seed平均 | 不偏分散 | seed bootstrap 95% CI |", "| --- | ---: | ---: | ---: | ---: | --- |"]
for condition in conditions:
    item = stats[condition]
    lines.append(f"| {condition} | {item['sat']} | {item['unknown']} | {item['mean']:.6f} | {item['variance']:.6f} | [{item['ci95'][0]:.6f}, {item['ci95'][1]:.6f}] |")
effect = stats["difference"]
lines += ["", f"influence−randomのseed平均差は{effect['mean']:+.6f}、不偏分散{effect['variance']:.6f}、95% CI [{effect['ci95'][0]:.6f}, {effect['ci95'][1]:.6f}]。", "", "| 比較 | n | random SAT | influence SAT | randomのみ | influenceのみ | exact p | Holm p |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
for test in tests: lines.append(f"| {test['label']} | {test['n']} | {test['random']} | {test['influence']} | {test['random_only']} | {test['influence_only']} | {test['p']:.6g} | {test['holm_p']:.6g} |")
lines += ["", "二側exact McNemarの5比較をHolm補正。bit間依存があるためcase水準p値は診断用で、seed bootstrap CIを優先する。", "", "| task | 元構造 | 対象 | 条件 | SAT | UNSAT | UNKNOWN |", "| --- | --- | ---: | --- | ---: | ---: | ---: |"]
for task in ("numeric", "selection"):
    for arch in ("gate2", "lut4"):
        for condition in conditions:
            group = [pair[condition] for pair in pairs.values() if pair[condition]["task"] == task and pair[condition]["original_architecture"] == arch]
            counts = [sum(row["status"] == status for row in group) for status in ("sat", "unsat", "unknown")]
            lines.append(f"| {task} | {arch} | {len(group)} | {condition} | {counts[0]} | {counts[1]} | {counts[2]} |")
lines += ["", f"同じ2入力を選んだcaseは{sum(pair['random_add2']['same_sources'] for pair in pairs.values())}/108。元gate2の出力表は4→16bit、元lut4は16→64bit。", "", "## 判定", "", "回復はrandom 9/108、influence 13/108で、事前の25%基準に届かなかった。両タスクにSATはあるが、出力表を最大4倍にしても大半の制約が残る。influence選択の優位性もHolm補正後には確認できない。規則どおり出力arityの追加を止め、隠れ層と出力接続先を診断する。", "", f"SAT証人{verified}件を再読込し、全64入力で一致を確認。216論理式、checkpoint、ソースhashを検査した。UNSATは独立proof checker未検証のZ3判定。UNKNOWNは0件。", "", f"Z3 {result['z3_version']}、NumPy {result['numpy_version']}、単一thread、各問3000ms、全実行{result['elapsed_seconds']:.1f}秒。全正解を使うoracle exact synthesisであり、学習や汎化ではない。", "", "精密数値では元gate2の回復が中心だった。経路選択では元gate2 64件中1件、元lut4 3件は全件回復した。母数が異なるため、構造自由度が経路選択一般に効かないとは結論しない。", "", "English: Two added output inputs recovered 9 random and 13 oracle-selected cases, below the preregistered 25% milestone. Output arity expansion now stops and hidden-node routing is diagnosed next.", "", "简体中文：增加两条输出连接后，随机条件恢复9例、目标影响度条件恢复13例，低于预注册的25%阈值。下一步停止扩大输出表，诊断隐藏节点路由。", "", "[実行前計画](../results/E012-output-arity-plus-two/PROTOCOL.md) / [生データ](../results/E012-output-arity-plus-two/run/results.json)"]
audit = dict(verified_witnesses=verified, statistics=stats, tests=tests)
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2))
text = "\n".join(lines) + "\n"
(HERE / "REPORT.md").write_text(text)
(ROOT / "docs/STAR-Bit-E012-output-arity-plus-two.md").write_text(text)
print(json.dumps(audit, indent=2))
