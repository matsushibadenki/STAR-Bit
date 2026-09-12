"""Audit and report the E019 function-space pilots."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import search


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name / "results.json").read_text())


def evaluate(expression, inputs):
    if expression[0] == "input":
        return inputs[expression[1]]
    _, signature, code, left, right = expression
    value = search.lut_outputs(evaluate(left, inputs), evaluate(right, inputs))[code]
    assert value == int(signature)
    return value


pilot1 = load("pilot")
pilot2 = load("pilot2")
for result in (pilot1, pilot2):
    for name, expected in result["sources"].items():
        assert sha(HERE / name) == expected

inputs, targets = search.inputs_and_targets()
for result in (pilot1, pilot2):
    for row in result["records"]:
        for task, solution in row["solutions"].items():
            assert evaluate(solution["expression"], inputs) == targets[task]
            assert int(solution["signature"]) == targets[task]
            assert solution["primitives"] <= result["settings"]["max_cost"]

affine_solutions = [
    solution
    for row in pilot2["records"] if row["condition"] == "affine_scaffold"
    for solution in row["solutions"].values()
]
assert sum(solution["uses_affine_intermediate"] for solution in affine_solutions if solution["signature"] == str(targets["parity"])) == 4

lines = [
    "# E019：Function-space Module Genesis pilot",
    "",
    "実行日：2026-09-12。回路構文ではなく64入力のtruth signatureを中間機能の識別子とし、同一機能を生成した異なる構文を即時統合した。正解への現在誤差だけで候補を残す探索と、将来のcomposition可能性を残す探索を比較した。",
    "",
    "## 結論",
    "",
    "**機能signatureによる同値統合は数十万件の構文重複を除去できたが、それだけでは有用な中間機能を保持できなかった。タスク非依存のaffine scaffoldを明示的に保持すると、最終parityと単体では無相関なpartial parityが残り、parity exactを0/4から4/4へ回復した。comparator/carryは未解決であり、自律的Module Genesisはまだ成立していない。**",
    "",
    "## Pilot 1：一段lookahead",
    "",
    "| condition | exact target平均 | parity | comparator | mux | carry | 一意signature平均 | 同値merge平均 | 秒平均 |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for condition in ("target_greedy", "composition_pareto"):
    item = pilot1["aggregate"][condition]
    per = item["exact_by_task"]
    lines.append(
        f"| {condition} | {item['exact_targets']['mean']:.1f} | {per['parity']}/4 | {per['comparator']}/4 | {per['mux']}/4 | {per['carry']}/4 | "
        f"{item['generated_unique_signatures']['mean']:.0f} | {item['equivalent_function_merges']['mean']:.0f} | {item['seconds']['mean']:.3f} |"
    )
lines += [
    "",
    "一段lookaheadと7次元Pareto保持を追加しても、両条件ともmuxだけ4/4だった。partial parityは完成まで複数compositionを要し、一段先のtarget errorでは価値を認識できなかった。",
    "",
    "## Pilot 2：affine scaffold",
    "",
    "| condition | exact target平均 | 不偏分散 | parity | comparator | mux | carry | 一意signature平均 | 同値merge平均 | 秒平均 |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for condition in ("target_greedy", "affine_scaffold"):
    item = pilot2["aggregate"][condition]
    per = item["exact_by_task"]
    lines.append(
        f"| {condition} | {item['exact_targets']['mean']:.1f} | {item['exact_targets']['variance']:.1f} | {per['parity']}/4 | {per['comparator']}/4 | {per['mux']}/4 | {per['carry']}/4 | "
        f"{item['unique_signatures']['mean']:.0f} | {item['equivalent_merges']['mean']:.0f} | {item['seconds']['mean']:.3f} |"
    )
lines += [
    "",
    "affine scaffoldは、6入力のXOR部分集合とその反転に対応する128 signatureを、探索中に生成された場合だけ保持する。ゲート名、task固有module、中間教師は与えていないが、affine関数族を人手で選んだ帰納バイアスである。",
    "",
    "全4 seedでmuxはround 2、3 primitives、routing 20 bits、depth 2で発見された。affine条件のparityはround 3、5 primitives、routing 32 bits、depth 3で発見され、すべてaffine中間signatureを再利用した。これは『正解への即時相関がない踏み石を保持すれば到達可能性が変わる』という限定的な肯定結果である。",
    "",
    "comparator/carryはbeam 256、7 round、tree cost 14でも0/4だった。affine保持はexact target数を1から2へ増やしたが、事前の全4 target 3/4 seed基準を満たさないため16-seed mainへ進めない。pilot結果に有意差検定は適用しない。",
    "",
    "## Module Genesis Problemへの含意",
    "",
    "E014–E016では検証済みModuleが存在すればroutingが機能した。E017–E019では、primitiveから良い中間機能を作り、将来価値が現れるまでarchiveへ残す部分がボトルネックになった。E019は同値関数mergeと踏み石保持を別々に検査し、後者がparityの到達性を変えることを示した。",
    "",
    "次は関数族を人手指定せず、生成された上位の子候補へ複数round・複数taskで繰り返し寄与した親signatureへpromotion scoreを与える。`reuse_count`、改善したtask数、子のPareto rank、生成costを保存し、昇格・維持・削除を決める。これによりaffine scaffoldをlearned archive promotionへ置き換える。",
    "",
    "## Roadmap",
    "",
    "- [Done] 64-bit signatureを機能identityとして、同値構文を生成時点で統合した。",
    "- [Done] target-greedy、一段composition lookahead、Pareto保持を同じ生成予算で比較した。",
    "- [Done] task非依存affine scaffoldによりparity exactを0/4から4/4へ回復した。",
    "- [Done] primitive、routing bits、depth、親expression、発見round、同値merge数を保存した。",
    "- [Next] 子候補への寄与から親Functionを自動昇格するlearned archive promotionを実装する。",
    "- [Next] comparator/carryを含む全task exact後に、Module定義bit・call routing bit・reuse・階層深度を測る。",
    "- [Later] source task Libraryを別taskへ固定移植し、from-scratchとの探索予算差を16 seedで比較する。",
    "",
    "English: Exact truth signatures removed large amounts of syntactic duplication but did not by themselves preserve useful stepping stones. A task-independent affine scaffold recovered parity in 4/4 seeds, demonstrating that intermediate retention can change reachability. Comparator and carry remain unsolved, and the scaffold is an explicit inductive bias rather than autonomous Module Genesis.",
    "",
    "简体中文：精确真值签名消除了大量语法重复，但本身不足以保留有用的中间踏脚石。任务无关的仿射支架使parity从0/4恢复到4/4，说明中间功能保留可以改变目标可达性。comparator与carry仍未解决，该支架属于显式归纳偏置，并非自主模块生成。",
    "",
    "[Pilot 1計画](../results/E019-function-space-genesis/PILOT-PROTOCOL.md) / [Pilot 2計画](../results/E019-function-space-genesis/PILOT2-PROTOCOL.md) / [Pilot 1生データ](../results/E019-function-space-genesis/pilot/results.json) / [Pilot 2生データ](../results/E019-function-space-genesis/pilot2/results.json)",
]

audit = {
    "pilot1": pilot1["aggregate"],
    "pilot2": pilot2["aggregate"],
    "solutions_verified": sum(len(row["solutions"]) for result in (pilot1, pilot2) for row in result["records"]),
    "affine_parity_solutions_using_affine_intermediate": 4,
    "main_threshold_met": pilot2["viable"],
}
(HERE / "audit_summary.json").write_text(json.dumps(audit, indent=2))
text = "\n".join(lines) + "\n"
(HERE / "REPORT.md").write_text(text)
(ROOT / "docs/STAR-Bit-E019-function-space-genesis.md").write_text(text)
print(json.dumps(audit, indent=2))
