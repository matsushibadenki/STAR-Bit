"""Audit E014 and generate the milestone report."""
import hashlib, itertools, json, math, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "run"
sys.path.insert(0, str(HERE))
import run as experiment


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(values, rng):
    values = np.asarray(values, float)
    means = values[rng.integers(0, len(values), (10000, len(values)))].mean(1)
    return dict(mean=float(values.mean()), variance=float(values.var(ddof=1)), ci95=np.quantile(means, [.025, .975]).tolist())


def exact_permutation(differences):
    differences = np.asarray(differences, float); observed = abs(differences.mean()); count = 0; total = 2 ** len(differences)
    for mask in range(total):
        signs = np.array([1 if mask & (1 << bit) else -1 for bit in range(len(differences))])
        count += abs((differences * signs).mean()) >= observed - 1e-15
    return count / total


def holm(values):
    order = sorted(range(len(values)), key=values.__getitem__); answer = [0.] * len(values); prior = 0.
    for rank, index in enumerate(order):
        prior = max(prior, min(1., values[index] * (len(values) - rank))); answer[index] = prior
    return answer


result = json.loads((OUT / "results.json").read_text())
assert sha(HERE / "run.py") == result["source_sha256"] and sha(HERE / "PROTOCOL.md") == result["protocol_sha256"]
verification = json.loads((OUT / "verification.json").read_text())
assert all(value is True for key, value in verification.items() if key != "verify_source_sha256")
assert sha(HERE / "verify.py") == verification["verify_source_sha256"]
x, targets = experiment.data(); libraries = experiment.candidates(x)
for task, (_, outputs) in libraries.items():
    assert hashlib.sha256(outputs.tobytes()).hexdigest() == result["library"][task]["outputs_sha256"]

assert len(result["records"]) == 96
for row in result["records"]:
    routes, outputs = libraries[row["task"]]; prediction = outputs[row["route_index"]]; target = targets[row["task"]]
    train, test = np.asarray(row["train_indices"]), np.asarray(row["test_indices"])
    assert sorted(np.r_[train, test].tolist()) == list(range(64)) and not set(train) & set(test)
    checks = dict(train_exact=float((prediction[train] == target[train]).all(1).mean()), train_bit=float((prediction[train] == target[train]).mean()), test_exact=float((prediction[test] == target[test]).all(1).mean()), test_bit=float((prediction[test] == target[test]).mean()), full_exact=float((prediction == target).all(1).mean()), full_bit=float((prediction == target).mean()))
    assert all(abs(row[key] - value) < 1e-12 for key, value in checks.items()) and row["source_load_variance"] == 0

rng = np.random.default_rng(1014); summaries = {}; comparisons = []
for task in ("numeric", "selection"):
    task_rows = [row for row in result["records"] if row["task"] == task]
    for condition in ("fixed_random", "train_selected", "structured_oracle"):
        group = [row for row in task_rows if row["condition"] == condition]
        summaries[(task, condition)] = {metric: summarize([row[metric] for row in group], rng) for metric in ("test_exact", "test_bit", "train_exact", "full_exact")}
    by = {(row["seed"], row["condition"]): row for row in task_rows}
    differences = [by[seed, "train_selected"]["test_exact"] - by[seed, "fixed_random"]["test_exact"] for seed in range(600, 616)]
    effect = summarize(differences, rng); sd = np.std(differences, ddof=1)
    comparisons.append(dict(task=task, **effect, cohen_dz=None if sd == 0 else float(np.mean(differences) / sd), p=exact_permutation(differences)))
for row, adjusted in zip(comparisons, holm([row["p"] for row in comparisons])): row["holm_p"] = adjusted

lines = ["# E014：State付きLogic PEの時間再利用とschedule選択", "", "実行日：2026-09-12。小さな論理モジュールをState付きで複数cycle再利用し、物理ゲート数と時間を交換する実行可能なprototypeを作った。ゲート関数と候補集合を固定し、train-selected scheduleと固定ランダムscheduleを16 split seedで比較した。", "", "## 未使用test半分の結果", "", "| task | routing | exact平均 | 不偏分散 | 95% CI | bit accuracy平均 | 全領域完全schedule/16 |", "| --- | --- | ---: | ---: | --- | ---: | ---: |"]
for task in ("numeric", "selection"):
    for condition in ("fixed_random", "train_selected", "structured_oracle"):
        item = summaries[(task, condition)]["test_exact"]; bit = summaries[(task, condition)]["test_bit"]
        complete = sum(row["full_exact"] == 1 for row in result["records"] if row["task"] == task and row["condition"] == condition)
        lines.append(f"| {task} | {condition} | {item['mean']:.6f} | {item['variance']:.6f} | [{item['ci95'][0]:.6f}, {item['ci95'][1]:.6f}] | {bit['mean']:.6f} | {complete} |")
lines += ["", "| task | train-selected − random | 差の不偏分散 | 95% CI | Cohen dz | exact permutation p | Holm p |", "| --- | ---: | ---: | --- | ---: | ---: | ---: |"]
for row in comparisons: lines.append(f"| {row['task']} | {row['mean']:+.6f} | {row['variance']:.6f} | [{row['ci95'][0]:.6f}, {row['ci95'][1]:.6f}] | {row['cohen_dz']:.3f} | {row['p']:.8f} | {row['holm_p']:.8f} |")
lines += ["", "検定は16seed内のtest exact差に対する二側exact sign-flip permutationで、2タスクをHolm補正した。train-selectedは全seedで全領域完全scheduleを回復し、今回の候補集合・32例splitでは過学習を観測しなかった。", "", "## 物理ゲート数と時間の交換", "", "| task | temporal物理gate | spatial物理gate | 削減 | active gate評価 | cycle | State bit | route記述bit |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
for task in ("numeric", "selection"):
    cost = result["costs"][task]; reduction = 1 - cost["temporal_physical_gates"] / cost["spatial_physical_gates"]
    lines.append(f"| {task} | {cost['temporal_physical_gates']} | {cost['spatial_physical_gates']} | {reduction:.2%} | {cost['active_gate_evaluations']} | {cost['cycles']} | {cost['state_bits']} | {cost['candidate_route_bits']} |")
lines += ["", "加算は5-gate full-adderを3回使い、空間展開比で物理ゲートを66.7%削減した。経路選択は12-gate mux stageを2回使い50%削減した。active gate評価数は減らず、Stateとlatencyが増える。これは面積相当の論理資源と時間の交換である。実ハードウェアの面積・消費電力・遅延測定ではない。", "", "全候補は入力置換または巡回置換で構成し、各cycleのsource load varianceは0。負荷分散を候補空間で強制した。soft routerの補助損失はまだ存在しないため、今後のMoE実験で『load-balancing lossを最初から入れた』証拠には数えない。", "", "## 何が分離できたか", "", "fixed_randomとtrain_selectedは、PEの論理関数、物理ゲート数、active評価数、cycle数、候補scheduleを共有する。異なるのは32 train例を使ったschedule選択だけである。この小規模設定では、学習データによるrouting選択の効果を固定ランダムroutingから分離できた。", "", f"加算候補36個中、全領域完全scheduleは{result['library']['numeric']['exact_full_domain']}個。経路選択候補512個中{result['library']['selection']['exact_full_domain']}個。選択方式には正しいscheduleを含む強いモジュール事前知識があるため、一般的な構造学習の成功とは言えない。", "", "精密数値と経路選択の両方でtest exact 1.0だが、加算はcarryの逐次State、経路選択は二段barrel shiftという異なる時間構造を使う。構造的自由度が効く形はタスク種別ごとに異なる。", "", "## 検証と次段階", "", "96記録のsplit非重複、route index、train/test/full指標を候補出力から再計算し、候補出力hash、実行ソースhash、protocol hashを照合した。structured spatial版とtemporal版は全64入力で同じ正解を返す。", "", f"NumPy {result['numpy_version']}、CPU単一thread、候補生成と16seed評価は{result['elapsed_seconds']:.3f}秒。", "", "次はゲート表とroute scoreを共同学習する。学習Routerには最初からload-balancing補助損失を入れ、同じPE・計算予算の固定ランダムrouteを対照にする。その後、同一run内の別Expert、次に別seed Expertの交換を行う。", "", "English: A stateful temporal Logic PE cut physical primitive gates by 66.7% for addition and 50% for selection while preserving active operations. Train-selected schedules reached 100% held-out exact accuracy across 16 seeds and beat balanced fixed-random schedules.", "", "简体中文：带状态的时间复用Logic PE在加法任务减少66.7%的物理门、选择任务减少50%，但活动运算次数不变。训练集选择的调度在16个种子上均达到100%的留出精确率，并优于负载均衡的固定随机调度。", "", "[実行前計画](../results/E014-temporal-logic-pe/PROTOCOL.md) / [生データ](../results/E014-temporal-logic-pe/run/results.json)"]
audit = dict(summaries={f"{task}/{condition}": value for (task, condition), value in summaries.items()}, comparisons=comparisons, records_verified=len(result["records"]), source_load_variance_verified=0, spatial_reference_verification=verification)
(OUT / "audit_summary.json").write_text(json.dumps(audit, indent=2)); text = "\n".join(lines) + "\n"; (HERE / "REPORT.md").write_text(text); (ROOT / "docs/STAR-Bit-E014-temporal-logic-pe.md").write_text(text); print(json.dumps(audit, indent=2))
