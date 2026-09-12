"""Audit and report the E018 CEGIS pilot."""
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "pilot"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    values = np.asarray(values, float)
    return {"mean": float(values.mean()), "variance": float(values.var(ddof=1))}


result = json.loads((OUT / "results.json").read_text())
assert len(result["records"]) == 32
for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected

for row in result["records"]:
    assert row["task"] in {"parity", "comparator", "mux", "carry"}
    assert row["seed"] in range(1100, 1104)
    assert row["condition"] in {"all_rows", "cegis"}
    assert row["final_status"] in {"sat", "unsat", "unknown"}
    assert len(row["calls"]) == row["solver_calls"]
    if row["exact"]:
        assert row["witness"] is not None and row["final_status"] == "sat"

by_task = {}
for task in ("parity", "comparator", "mux", "carry"):
    for condition in ("all_rows", "cegis"):
        group = [row for row in result["records"] if row["task"] == task and row["condition"] == condition]
        by_task[f"{task}/{condition}"] = {
            "success": stats([row["exact"] for row in group]),
            "seconds": stats([row["elapsed_seconds"] for row in group]),
            "solver_calls": stats([row["solver_calls"] for row in group]),
        }

success_times = {}
for task in ("parity", "mux"):
    for condition in ("all_rows", "cegis"):
        group = [row["elapsed_seconds"] for row in result["records"] if row["task"] == task and row["condition"] == condition and row["exact"]]
        success_times[f"{task}/{condition}"] = stats(group)

lines = [
    "# E018：CEGISによるexact circuit形成pilot",
    "",
    "実行日：2026-09-12。E017でcomparator/carryのexact circuit形成が不安定だったため、10 LUTの同一容量で全64行SATと反例誘導合成（CEGIS）を4 seed比較した。",
    "",
    "## 結果",
    "",
    "| condition | exact総数 | parity | comparator | mux | carry | 成功率平均 | 不偏分散 | 時間平均（秒） |",
    "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
]
for condition in ("all_rows", "cegis"):
    item = result["aggregate"][condition]
    per = item["exact_by_task"]
    lines.append(
        f"| {condition} | {item['exact_total']}/16 | {per['parity']}/4 | {per['comparator']}/4 | {per['mux']}/4 | {per['carry']}/4 | "
        f"{item['success']['mean']:.3f} | {item['success']['variance']:.6f} | {item['seconds']['mean']:.3f} |"
    )
lines += [
    "",
    "CEGISはall-row SATを上回るという事前条件を満たさず、両条件ともexact 8/16だった。成功はparityとmuxに限られ、comparator/carryは全seedでUNKNOWNになった。UNKNOWNはUNSATではない。設定選択pilotなので有意差検定は行わない。",
    "",
    "## 成功タスクでの探索時間",
    "",
    "| task | all_rows平均秒（不偏分散） | CEGIS平均秒（不偏分散） |",
    "| --- | ---: | ---: |",
]
for task in ("parity", "mux"):
    direct = success_times[f"{task}/all_rows"]
    cegis = success_times[f"{task}/cegis"]
    lines.append(f"| {task} | {direct['mean']:.3f} ({direct['variance']:.3f}) | {cegis['mean']:.3f} ({cegis['variance']:.3f}) |")
lines += [
    "",
    "CEGISはparityを平均4.110秒から0.483秒、muxを3.266秒から0.332秒へ短縮した。一方、難しいタスクでは16–23回程度のSAT modelと反例追加後に10秒timeoutへ入り、全条件平均時間はall_rows 6.851秒からCEGIS 12.478秒へ増えた。成功率と成功時速度を分けて解釈する必要がある。",
    "",
    "## 判定",
    "",
    "CEGISは既に解ける関数の制約縮約には有効だったが、comparator/carryの探索壁を越えなかった。したがって16-seed Module abstraction mainへは進まない。現在確認できたのは、parity/muxでのexact circuit形成と、その探索時間短縮に限られる。",
    "",
    "次は全候補配線を直接SAT変数にする方法から、各中間nodeを64-bit機能signatureで一意化する列生成へ移す。同じBoolean関数の構文違いを探索前に統合し、候補集合を `error, primitive count, routing bits, state bits` のPareto dominanceで枝刈りする。その後にだけGlobal Module Libraryの定義費用とtransferを評価する。",
    "",
    "## Roadmap",
    "",
    "- [Done] 4 seed×4 task×2条件の32探索を同じ10 LUT容量で完了した。",
    "- [Done] CEGIS witnessを全64入力で独立照合し、source hashと全solver callを保存した。",
    "- [Done] 成功率と成功時速度を分離し、CEGISが簡単な2タスクだけを高速化することを確認した。",
    "- [Next] 機能signature列生成とPareto枝刈りでcomparator/carryのexact形成率を改善する。",
    "- [Next] 全4タスクのexact条件を満たしてからSyntax／Functional／Global Moduleを比較する。",
    "- [Later] `primitive + library + routing + state` の総費用とcross-task transferを16 seedで評価する。",
    "",
    f"32 searches、Z3 {result['z3_version']}、単一thread、総経過{result['elapsed_seconds']:.1f}秒。",
    "",
    "English: CEGIS accelerated exact synthesis for parity and mux but did not improve the 8/16 overall success count; comparator and carry remained unresolved. Module-abstraction claims remain gated on exact circuit formation.",
    "",
    "简体中文：CEGIS加速了parity与mux的精确合成，但总成功数仍为8/16，comparator与carry仍未解决。因此，模块抽象结论继续以精确电路形成为前提。",
    "",
    "[事前計画](../results/E018-cegis-mdl/PILOT-PROTOCOL.md) / [生データ](../results/E018-cegis-mdl/pilot/results.json) / [E017境界実験](STAR-Bit-E017-learned-circuit-abstraction.md)",
]

audit = {"aggregate": result["aggregate"], "by_task": by_task, "success_times": success_times, "records_verified": len(result["records"]), "main_threshold_met": result["viable"]}
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2))
text = "\n".join(lines) + "\n"
(HERE / "REPORT.md").write_text(text)
(ROOT / "docs/STAR-Bit-E018-cegis-mdl.md").write_text(text)
print(json.dumps(audit, indent=2))
