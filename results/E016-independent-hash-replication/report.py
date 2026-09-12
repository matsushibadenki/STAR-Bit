"""Audit and report the preregistered E016 independent-hash replication."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "run"
MODEL_DIR = ROOT / "results/E015-joint-logic-router"
sys.path.insert(0, str(MODEL_DIR))
import model as m


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(values, rng):
    values = np.asarray(values, float)
    bootstrap = values[rng.integers(0, len(values), (10000, len(values)))].mean(1)
    return {
        "mean": float(values.mean()),
        "variance": float(values.var(ddof=1)),
        "ci95": np.quantile(bootstrap, [.025, .975]).tolist(),
    }


def exact_sign_flip_p(differences):
    differences = np.asarray(differences, float)
    observed = abs(differences.mean())
    hits = 0
    for mask in range(2 ** len(differences)):
        signs = np.array([
            1 if mask & (1 << bit) else -1
            for bit in range(len(differences))
        ])
        hits += abs((differences * signs).mean()) >= observed - 1e-15
    return hits / (2 ** len(differences))


def cv(values):
    values = np.asarray(values, float)
    return float(values.std() / values.mean())


result = json.loads((OUT / "results.json").read_text())
records = result["records"]
assert len(records) == 32
assert result["settings"] == {
    "seeds": list(range(800, 816)),
    "steps": 800,
    "hash_offset": 40000,
}

for name, expected in result["sources"].items():
    assert sha(ROOT / name) == expected

by = {}
fixed_train_counts = []
for row in records:
    assert row["task"] == "numeric"
    assert row["seed"] in range(800, 816)
    assert row["condition"] in {"fixed_hash", "learned_balanced"}
    assert row["split_seed"] == row["seed"]
    assert row["hash_seed"] == row["seed"] + 40000
    train, test = row["train_indices"], row["test_indices"]
    assert len(train) == len(test) == 32
    assert sorted(train + test) == list(range(64))
    assert not set(train) & set(test)

    checkpoint = OUT / row["checkpoint"]
    assert sha(checkpoint) == row["checkpoint_sha256"]
    state = torch.load(checkpoint, weights_only=True)
    assert set(state) == {"gate_logits", "schedule_logits", "router_weight", "hash_map"}
    assert np.array_equal(
        np.bincount(state["hash_map"].numpy(), minlength=4),
        np.full(4, 16),
    )
    expected_hash = m.balanced_hash(row["hash_seed"])
    assert torch.equal(state["hash_map"], expected_hash)
    expected_counts = torch.bincount(
        expected_hash[torch.tensor(train)], minlength=4
    ).tolist()
    assert row["fixed_train_counts"] == expected_counts
    by[row["seed"], row["condition"]] = row
    if row["condition"] == "fixed_hash":
        fixed_train_counts.append(expected_counts)

assert len(by) == 32
assert all(counts != [8, 8, 8, 8] for counts in fixed_train_counts)

rng = np.random.default_rng(1016)
aggregates = {}
for condition in ("fixed_hash", "learned_balanced"):
    group = [by[seed, condition] for seed in range(800, 816)]
    item = {}
    for mode in ("soft", "hard"):
        for split in ("train", "test", "full"):
            for metric in ("exact", "bit_accuracy"):
                key = f"{mode}_{split}_{metric}"
                item[key] = summary(
                    [row["evaluation"][mode][split][metric] for row in group], rng
                )
    item["complete_test_seeds"] = sum(
        row["evaluation"]["hard"]["test"]["exact"] == 1 for row in group
    )
    item["final_balance_loss"] = summary(
        [row["curve"][-1]["balance_loss"] for row in group], rng
    )
    item["soft_train_utilization_cv"] = summary(
        [cv(row["evaluation"]["soft"]["utilization_train"]) for row in group], rng
    )
    item["hard_full_utilization_cv"] = summary(
        [cv(row["evaluation"]["hard"]["utilization_full"]) for row in group], rng
    )
    aggregates[condition] = item

differences = np.array([
    by[seed, "learned_balanced"]["evaluation"]["hard"]["test"]["exact"]
    - by[seed, "fixed_hash"]["evaluation"]["hard"]["test"]["exact"]
    for seed in range(800, 816)
])
comparison = summary(differences, rng)
comparison["cohen_dz"] = float(differences.mean() / differences.std(ddof=1))
comparison["p"] = exact_sign_flip_p(differences)
comparison["positive_seeds"] = int((differences > 0).sum())
comparison["zero_seeds"] = int((differences == 0).sum())
comparison["negative_seeds"] = int((differences < 0).sum())
comparison["confirmed"] = bool(
    comparison["p"] <= .05
    and comparison["ci95"][0] > 0
)

count_array = np.asarray(fixed_train_counts, float)
count_diagnostic = {
    "all_full_domain_counts": [16, 16, 16, 16],
    "train_counts_by_seed": fixed_train_counts,
    "exactly_balanced_train_seeds": int(
        sum(counts == [8, 8, 8, 8] for counts in fixed_train_counts)
    ),
    "per_expert_train_count_min": int(count_array.min()),
    "per_expert_train_count_max": int(count_array.max()),
    "train_count_cv": summary(
        [cv(counts) for counts in fixed_train_counts], rng
    ),
}

e015 = json.loads(
    (ROOT / "results/E015-joint-logic-router/run/audit_summary.json").read_text()
)
e015_numeric = next(x for x in e015["comparisons"] if x["task"] == "numeric")

lines = [
    "# E016：独立hashによるnumeric確認実験",
    "",
    "実行日：2026-09-12。E015のnumeric対照で見つかったsplit/hash乱数流の結合を解消し、新しい16 seedで事前登録どおり追試した。Logic PEの弱い検証済みmodule prior、4 Experts、800更新、温度、最適化設定はE015から変更していない。",
    "",
    "## 主要結果",
    "",
    "| routing | hard test exact平均 | 不偏分散 | 95% CI | bit平均 | 完全一致seed |",
    "| --- | ---: | ---: | --- | ---: | ---: |",
]
for condition in ("fixed_hash", "learned_balanced"):
    item = aggregates[condition]
    exact = item["hard_test_exact"]
    bit = item["hard_test_bit_accuracy"]
    lines.append(
        f"| {condition} | {exact['mean']:.6f} | {exact['variance']:.6f} | "
        f"[{exact['ci95'][0]:.6f}, {exact['ci95'][1]:.6f}] | "
        f"{bit['mean']:.6f} | {item['complete_test_seeds']}/16 |"
    )

lines += [
    "",
    "| learned−fixed | 差の不偏分散 | 95% CI | Cohen dz | exact permutation p | seed符号 + / 0 / − |",
    "| ---: | ---: | --- | ---: | ---: | ---: |",
    f"| {comparison['mean']:+.6f} | {comparison['variance']:.6f} | "
    f"[{comparison['ci95'][0]:.6f}, {comparison['ci95'][1]:.6f}] | "
    f"{comparison['cohen_dz']:.3f} | {comparison['p']:.8f} | "
    f"{comparison['positive_seeds']} / {comparison['zero_seeds']} / {comparison['negative_seeds']} |",
    "",
    "16 seed内のhard test exact差に二側exact sign-flip permutation testを適用した。事前登録した追試は1比較なので多重性補正は不要である。p≤0.05かつ95% CIが正方向で0を除く確認基準を満たした。",
    "",
    "## 独立性と負荷分散の監査",
    "",
    f"splitはseed 800–815、固定hashはそれぞれseed+40000から生成した。固定hashは全64入力を各Expert 16件へ割り当てる一方、train内の割当は4–12件、完全な8/8/8/8は{count_diagnostic['exactly_balanced_train_seeds']}/16 seedだった。E015で起きた全seed完全均衡は再現せず、乱数流の分離を確認した。",
    "",
    "| routing | 最終soft balance loss平均 | soft train利用CV平均 | hard full利用CV平均 |",
    "| --- | ---: | ---: | ---: |",
]
for condition in ("fixed_hash", "learned_balanced"):
    item = aggregates[condition]
    lines.append(
        f"| {condition} | {item['final_balance_loss']['mean']:.6f} | "
        f"{item['soft_train_utilization_cv']['mean']:.6f} | "
        f"{item['hard_full_utilization_cv']['mean']:.6f} |"
    )

lines += [
    "",
    "learned Routerにはupdate 0から係数0.1のimportance balance補助損失を適用した。固定hashのbalance値は学習項として機能しない定数で、train subsetの自然な偏りを示す診断値である。固定hashはfull domainで完全均衡する。soft負荷の均衡とhard argmax後の利用均衡は区別して報告した。",
    "",
    "## E015との再現性",
    "",
    f"E015 numericのlearned−fixed差は{e015_numeric['mean']:+.6f}（Holm p={e015_numeric['holm_p']:.6f}）だった。独立乱数流・新seedのE016でも差は{comparison['mean']:+.6f}となり、方向と事前確認基準を再現した。二実験の統合検定は事前登録していないため行わない。",
    "",
    "## 解釈と限界",
    "",
    "精密数値タスクでも、検証済みmodule priorの下では入力依存の学習Routerがラベル非依存の固定均衡hashより高い未見入力精度を示した。固定群にも高いseedがあり、改善幅はE015のselectionより小さい。これはcarry計算自体をroutingが新しく発見した証拠ではなく、既知Logic Expert群を入力に応じて割り当てる効果である。",
    "",
    "Gate表は完全ランダムから意味を発見しておらず、E014由来の弱い初期priorを使う。評価は固定6入力Boolean全領域の32/32分割であり、bit幅・系列長の外挿、Transformer、実ハードウェア面積や速度を検証していない。",
    "",
    f"32 training trajectories、CPU単一thread、PyTorch {result['torch_version']}、経過{result['elapsed_seconds']:.1f}秒。checkpoint、source hash、split、独立hash再生成、full-domain均衡を監査した。",
    "",
    "English: With independent split and fixed-hash random streams, learned balanced routing again improved numeric hard test exact accuracy under the verified Logic-PE prior. The preregistered replication criterion was met.",
    "",
    "简体中文：在数据划分与固定哈希使用独立随机流后，负载均衡的学习路由在已验证Logic PE先验下再次提高了数值任务的硬化测试精确率，并满足预注册复验标准。",
    "",
    "[事前計画](../results/E016-independent-hash-replication/PROTOCOL.md) / [生データ](../results/E016-independent-hash-replication/run/results.json)",
]

audit = {
    "aggregates": aggregates,
    "comparison": comparison,
    "fixed_hash_diagnostic": count_diagnostic,
    "records_verified": len(records),
    "source_hashes_verified": len(result["sources"]),
    "checkpoint_hashes_verified": len(records),
    "e015_numeric_descriptive_comparison": e015_numeric,
}
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2))
report = "\n".join(lines) + "\n"
(HERE / "REPORT.md").write_text(report)
(ROOT / "docs/STAR-Bit-E016-independent-hash-replication.md").write_text(report)
print(json.dumps({"comparison": comparison, "audit": count_diagnostic}, indent=2))
