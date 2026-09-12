"""Audit and report the E015 confirmatory run."""
import hashlib, json, math, sys
from pathlib import Path
import numpy as np
import torch

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; OUT = HERE / "run"; sys.path.insert(0, str(HERE))
import model as m


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(values, rng):
    values = np.asarray(values, float); means = values[rng.integers(0, len(values), (10000, len(values)))].mean(1)
    return dict(mean=float(values.mean()), variance=float(values.var(ddof=1)), ci95=np.quantile(means, [.025, .975]).tolist())


def permutation_p(differences):
    differences = np.asarray(differences, float); observed = abs(differences.mean()); hits = 0
    for mask in range(2 ** len(differences)):
        signs = np.array([1 if mask & (1 << bit) else -1 for bit in range(len(differences))])
        hits += abs((differences * signs).mean()) >= observed - 1e-15
    return hits / (2 ** len(differences))


def holm(values):
    answer = [0.] * len(values); running = 0.
    for rank, index in enumerate(sorted(range(len(values)), key=values.__getitem__)):
        running = max(running, min(1., values[index] * (len(values) - rank))); answer[index] = running
    return answer


def cv(values):
    values = np.asarray(values, float); return float(values.std() / values.mean())


result = json.loads((OUT / "results.json").read_text()); assert len(result["records"]) == 64 and len(result["interventions"]) == 384
for name, expected in result["sources"].items(): assert sha(HERE / name) == expected
records = result["records"]
for row in records:
    checkpoint = OUT / row["checkpoint"]; assert sha(checkpoint) == row["checkpoint_sha256"]
    state = torch.load(checkpoint, weights_only=True); assert set(state) == {"gate_logits", "schedule_logits", "router_weight", "hash_map"}
    train, test = row["train_indices"], row["test_indices"]
    assert sorted(train + test) == list(range(64)) and not set(train) & set(test)
    assert np.array_equal(np.bincount(state["hash_map"].numpy(), minlength=4), np.full(4, 16))
    if row["task"] == "numeric" and row["condition"] == "fixed_hash":
        assert row["evaluation"]["hard"]["utilization_train"] == [.25, .25, .25, .25]

for item in result["interventions"]:
    assert item["variant"] in {"self_replace", "same_run_swap", "symmetry_control", "cross_seed", "zero_expert", "reinitialized_expert"}
    if item["variant"] in {"self_replace", "symmetry_control"}:
        assert item["hard"]["max_output_change"] < 1e-6 and item["soft"]["max_output_change"] < 1e-6

rng = np.random.default_rng(1015); aggregates = {}; comparisons = []
for task in ("numeric", "selection"):
    task_rows = [row for row in records if row["task"] == task]
    for condition in ("fixed_hash", "learned_balanced"):
        group = [row for row in task_rows if row["condition"] == condition]
        aggregates[(task, condition)] = {}
        for hard in ("soft", "hard"):
            for split in ("train", "test", "full"):
                for metric in ("exact", "bit_accuracy"):
                    aggregates[(task, condition)][f"{hard}_{split}_{metric}"] = summary([row["evaluation"][hard][split][metric] for row in group], rng)
        aggregates[(task, condition)]["complete_test_seeds"] = sum(row["evaluation"]["hard"]["test"]["exact"] == 1 for row in group)
        aggregates[(task, condition)]["final_balance_loss"] = summary([row["curve"][-1]["balance_loss"] for row in group], rng)
        aggregates[(task, condition)]["hard_full_utilization_cv"] = summary([cv(row["evaluation"]["hard"]["utilization_full"]) for row in group], rng)
        aggregates[(task, condition)]["soft_train_utilization_cv"] = summary([cv(row["evaluation"]["soft"]["utilization_train"]) for row in group], rng)
    by = {(row["seed"], row["condition"]): row for row in task_rows}
    differences = [by[seed, "learned_balanced"]["evaluation"]["hard"]["test"]["exact"] - by[seed, "fixed_hash"]["evaluation"]["hard"]["test"]["exact"] for seed in range(700, 716)]
    item = summary(differences, rng); sd = np.std(differences, ddof=1)
    comparisons.append(dict(task=task, **item, cohen_dz=float(np.mean(differences) / sd), p=permutation_p(differences)))
for item, adjusted in zip(comparisons, holm([item["p"] for item in comparisons])): item["holm_p"] = adjusted

swap_stats = {}
for task in ("numeric", "selection"):
    for condition in ("fixed_hash", "learned_balanced"):
        for variant in ("same_run_swap", "cross_seed", "zero_expert", "reinitialized_expert"):
            group = [item for item in result["interventions"] if item["task"] == task and item["condition"] == condition and item["variant"] == variant]
            changes = [item["hard"]["test"]["exact"] - item["hard"]["baseline_test"]["exact"] for item in group]
            swap_stats[(task, condition, variant)] = summary(changes, rng)

lines = ["# E015：Logic Expert・schedule・Router共同最適化", "", "実行日：2026-09-12。E014で検証したLogic PE gate表を弱い事前値として、4 ExpertのLUT表・schedule分布・入力Routerを共同最適化した。16 main seed、各32 train/32 test、800更新。", "", "## hard test主要結果", "", "| task | routing | exact平均 | 不偏分散 | 95% CI | bit平均 | 完全一致seed |", "| --- | --- | ---: | ---: | --- | ---: | ---: |"]
for task in ("numeric", "selection"):
    for condition in ("fixed_hash", "learned_balanced"):
        item = aggregates[(task, condition)]; exact = item["hard_test_exact"]; bit = item["hard_test_bit_accuracy"]
        lines.append(f"| {task} | {condition} | {exact['mean']:.6f} | {exact['variance']:.6f} | [{exact['ci95'][0]:.6f}, {exact['ci95'][1]:.6f}] | {bit['mean']:.6f} | {item['complete_test_seeds']}/16 |")
lines += ["", "| task | learned−fixed | 差の分散 | 95% CI | Cohen dz | exact permutation p | Holm p |", "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
for item in comparisons: lines.append(f"| {item['task']} | {item['mean']:+.6f} | {item['variance']:.6f} | [{item['ci95'][0]:.6f}, {item['ci95'][1]:.6f}] | {item['cohen_dz']:.3f} | {item['p']:.8f} | {item['holm_p']:.8f} |")
lines += ["", "16seed内のhard test exact差に二側exact sign-flip permutation testを適用し、2タスクをHolm補正した。両タスクで補正後有意だが、numeric固定hashには後述のsplit結合がある。", "", "## 負荷分散", "", "| task | routing | 最終soft balance loss平均 | soft train利用CV | hard full利用CV |", "| --- | --- | ---: | ---: | ---: |"]
for task in ("numeric", "selection"):
    for condition in ("fixed_hash", "learned_balanced"):
        item = aggregates[(task, condition)]
        lines.append(f"| {task} | {condition} | {item['final_balance_loss']['mean']:.6f} | {item['soft_train_utilization_cv']['mean']:.6f} | {item['hard_full_utilization_cv']['mean']:.6f} |")
lines += ["", "learned Routerには最初の更新から係数0.1のimportance balance損失を適用した。soft負荷はほぼ均衡したが、argmax後のhard full利用は完全均衡とは限らない。固定hashは全64入力で各Expert 16件を構造的に保証する。", "", "## Expert介入：hard test exactの変化", "", "交換後−無交換。負は悪化。", "", "| task | routing | 同一run 0/1交換 | 次seed Expert 0 | zero Expert 0 | 再初期化 Expert 0 |", "| --- | --- | ---: | ---: | ---: | ---: |"]
for task in ("numeric", "selection"):
    for condition in ("fixed_hash", "learned_balanced"):
        values = [swap_stats[(task, condition, variant)]["mean"] for variant in ("same_run_swap", "cross_seed", "zero_expert", "reinitialized_expert")]
        lines.append(f"| {task} | {condition} | {values[0]:+.6f} | {values[1]:+.6f} | {values[2]:+.6f} | {values[3]:+.6f} |")
lines += ["", "同一runではExpertだけを0/1交換し、Routerは固定した。learned selectionは平均−0.2617と大きく悪化し、ExpertとRouterの対応依存がある。次seed Expert 0移植は平均−0.0859。番号を機能整列していないため、移植失敗を知識非局在の証明とはしない。", "", "自己置換とExpert 0/1＋Router対応の同時交換はsoft/hard全2048評価で最大出力差0。介入実装の置換対称性を確認した。cross-seed donorは事前固定した次seedで、再学習・test選択なし。循環donor共有のため交換差に有意差検定は行わず、全平均・分散・CIを生JSONへ保存した。", "", "## 監査で判明した制約", "", "numericではsplit permutationと固定hash lookupが同じseedから同じ乱数手順で生成され、結果として全seedのtrain割当も8/8/8/8になった。ラベルは使っていないが、対照routingとsplitが意図せず結合している。固定群を有利にし得るためnumeric差は保守的に見えるものの、独立対照としては不十分である。別seed・独立hash streamによるE016確認を行う。selectionはsplit seed+20000、hash seed+5000で分離されている。", "", "## 判定と限界", "", "module prior下では、learned routingは均衡固定hashよりnumeric +0.0566、selection +0.3359 hard test exact高かった。特に経路選択で構造自由度が効くという軸を支持する。一方、numericは両群が高精度で天井効果が強い。", "", "Gate表は完全ランダムから意味を発見しておらず、pilot結果に基づく既知module priorを使う。E014候補libraryもタスク固有で、汎用的な構造発見、長さ外挿、LLM能力の証拠ではない。", "", f"64 training trajectories、384 intervention records、CPU単一thread、PyTorch {result['torch_version']}、経過{result['elapsed_seconds']:.1f}秒。checkpoint・source hash、split、full-domain hash balance、自己交換と対称交換を再検査した。", "", "English: Under a verified Logic-PE prior, jointly optimized balanced routing beat a fixed balanced hash, especially on route selection. Numeric fixed-hash generation was unintentionally coupled to the split RNG and requires independent replication.", "", "简体中文：在已验证的Logic PE先验下，联合优化的负载均衡路由优于固定均衡哈希，尤其是在路径选择任务上。数值任务的固定哈希与数据划分随机流意外耦合，需要独立复验。", "", "[事前計画](../results/E015-joint-logic-router/PROTOCOL.md) / [生データ](../results/E015-joint-logic-router/run/results.json)"]

audit = dict(aggregates={f"{task}/{condition}": value for (task, condition), value in aggregates.items()}, comparisons=comparisons, swaps={f"{task}/{condition}/{variant}": value for (task, condition, variant), value in swap_stats.items()}, records_verified=len(records), interventions_verified=len(result["interventions"]), numeric_split_hash_coupling=True)
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2)); text = "\n".join(lines) + "\n"; (HERE / "REPORT.md").write_text(text); (ROOT / "docs/STAR-Bit-E015-joint-logic-router.md").write_text(text); print(json.dumps(dict(comparisons=comparisons, records=64, interventions=384), indent=2))
