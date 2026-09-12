"""Audit and report E013."""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "run"
sys.path.insert(0, str(ROOT / "results/E008-fixed-wiring-sat"))
import solve as base


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def exact(left, right):
    a = sum(x and not y for x, y in zip(left, right)); b = sum(y and not x for x, y in zip(left, right)); n = a + b
    return (1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(min(a, b) + 1)) / 2**n), a, b)


def holm(values):
    answer = [0.] * len(values); running = 0.
    for rank, index in enumerate(sorted(range(len(values)), key=values.__getitem__)):
        running = max(running, min(1., values[index] * (len(values) - rank))); answer[index] = running
    return answer


def ci(values, rng):
    values = np.asarray(values, float); means = values[rng.integers(0, len(values), (10000, len(values)))].mean(1)
    return np.quantile(means, [.025, .975]).tolist()


result = json.loads((OUT / "results.json").read_text()); rows = result["records"]
assert len(rows) == 216 and sha(ROOT / "results/E009-output-bit-diagnosis/run/results.json") == result["e009_results_sha256"]
for relative, expected in result["source_hashes"].items(): assert sha(ROOT / relative) == expected
verified = 0
for row in rows:
    stem = f"{row['task']}-{row['seed']}-{row['original_architecture']}-bit{row['bit']}-{row['condition']}"
    assert sha(OUT / f"{stem}.smt2.gz") == row["formula_sha256"]
    if row["status"] == "sat":
        witness = json.loads((OUT / f"{stem}-witness.json").read_text()); x, y = base.data(row["task"])
        assert np.array_equal(base.evaluate(x, witness["wires"], witness["tables"], witness["outputs"]), y[:, row["bit"]:row["bit"] + 1]); verified += 1
pairs = {}
for row in rows: pairs.setdefault(row["case_index"], {})[row["condition"]] = row
assert len(pairs) == 108 and all(len(pair) == 2 for pair in pairs.values())
conditions = ("layer1_select", "all_hidden_select")
rates = {condition: [] for condition in conditions}
for seed in range(500, 516):
    group = [pair for pair in pairs.values() if pair["layer1_select"]["seed"] == seed]
    for condition in conditions: rates[condition].append(np.mean([pair[condition]["status"] == "sat" for pair in group]))
rng = np.random.default_rng(1013); stats = {}
for condition in conditions:
    values = rates[condition]; stats[condition] = dict(sat=sum(pair[condition]["status"] == "sat" for pair in pairs.values()), unknown=sum(pair[condition]["status"] == "unknown" for pair in pairs.values()), mean=float(np.mean(values)), variance=float(np.var(values, ddof=1)), ci95=ci(values, rng))
delta = np.asarray(rates["all_hidden_select"]) - np.asarray(rates["layer1_select"])
stats["difference"] = dict(mean=float(delta.mean()), variance=float(delta.var(ddof=1)), ci95=ci(delta, rng))
specs = [("all", None, None)] + [(f"{task}/{arch}", task, arch) for task in ("numeric", "selection") for arch in ("gate2", "lut4")]
tests = []
for label, task, arch in specs:
    group = [pair for pair in pairs.values() if (task is None or pair["layer1_select"]["task"] == task) and (arch is None or pair["layer1_select"]["original_architecture"] == arch)]
    left = [pair["layer1_select"]["status"] == "sat" for pair in group]; right = [pair["all_hidden_select"]["status"] == "sat" for pair in group]
    p, left_only, right_only = exact(left, right); tests.append(dict(label=label, n=len(group), layer1=sum(left), all_hidden=sum(right), layer1_only=left_only, all_only=right_only, p=p))
for test, adjusted in zip(tests, holm([test["p"] for test in tests])): test["holm_p"] = adjusted

sat_cases = [pair["layer1_select"] for pair in pairs.values() if pair["layer1_select"]["status"] == "sat"]
lines = ["# E013：隠れノード選択によるボトルネック診断", "", "実行日：2026-09-12。E009-UNSATの108出力bitで、固定出力親を外し、第二層32ノードまたは全64隠れノードからcase全体で1ノードを選んだ。選択ノードを出力へ恒等接続するoracle exact synthesisである。", "", "| 選択範囲 | SAT/108 | UNKNOWN | seed平均 | 不偏分散 | seed bootstrap 95% CI |", "| --- | ---: | ---: | ---: | ---: | --- |"]
for condition in conditions:
    item = stats[condition]; lines.append(f"| {condition} | {item['sat']} | {item['unknown']} | {item['mean']:.6f} | {item['variance']:.6f} | [{item['ci95'][0]:.6f}, {item['ci95'][1]:.6f}] |")
effect = stats["difference"]; lines += ["", f"全隠れ−第二層のseed平均差は{effect['mean']:+.6f}、不偏分散{effect['variance']:.6f}、95% CI [{effect['ci95'][0]:.6f}, {effect['ci95'][1]:.6f}]。", "", "| 比較 | n | 第二層 SAT | 全隠れ SAT | 第二層のみ | 全隠れのみ | exact p | Holm p |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
for test in tests: lines.append(f"| {test['label']} | {test['n']} | {test['layer1']} | {test['all_hidden']} | {test['layer1_only']} | {test['all_only']} | {test['p']:.6g} | {test['holm_p']:.6g} |")
lines += ["", "二側exact McNemarの5比較をHolm補正。両範囲の判定は全caseで一致した。", "", "## SATとなったcase", "", "| task | seed | 元構造 | bit | 第二層node |", "| --- | ---: | --- | ---: | ---: |"]
for row in sat_cases: lines.append(f"| {row['task']} | {row['seed']} | {row['original_architecture']} | {row['bit']} | {row['selected_node']} |")
lines += ["", "## 判定", "", "SATは4/108で事前の25%基準に届かず、すべてnumeric・元gate2・bit1だった。全隠れへ広げても追加SATはなく、第一層だけを直接読む利点も確認できない。経路選択67caseはすべてUNSAT判定だった。固定された出力親だけでなく、単一隠れノードが必要な多入力機能を作れないことが主要な制約である。", "", "二入力ゲートの第二層ノードが直接依存できる葉は最大4個であり、6入力に依存する出力には構造上不足し得る。元gate2の出力まで含めれば理論上8葉へ届くが、固定された部分木の組合せが対象関数に合っていない。次は隠れ配線または時間再利用で深さを与える。", "", f"SAT証人{verified}件を再読込し全64入力一致を確認。216論理式、checkpoint、ソースhashも検査した。UNSATは独立proof checker未検証のZ3判定。UNKNOWNは0件。", "", f"Z3 {result['z3_version']}、NumPy {result['numpy_version']}、単一thread、各問2000ms、全実行{result['elapsed_seconds']:.1f}秒。", "", "学習されたroutingや汎化の結果ではない。精密数値と経路選択で差は明瞭だが、この二つの人工関数族を越えて一般化しない。", "", "English: Selecting any existing hidden node recovered only four numeric bit-1 cases and no routing-task case. The main bottleneck lies inside fixed hidden wiring, not only in output parent choice.", "", "简体中文：从任意隐藏节点中选择，只恢复了4个数值任务bit-1案例，路径选择任务没有恢复。主要瓶颈位于固定隐藏连接内部。", "", "[実行前計画](../results/E013-hidden-node-routing/PROTOCOL.md) / [生データ](../results/E013-hidden-node-routing/run/results.json)"]
audit = dict(verified_witnesses=verified, statistics=stats, tests=tests)
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2)); text = "\n".join(lines) + "\n"; (HERE / "REPORT.md").write_text(text); (ROOT / "docs/STAR-Bit-E013-hidden-node-routing.md").write_text(text); print(json.dumps(audit, indent=2))
