"""E016 independent fixed-hash replication for numeric routing."""
import hashlib, json, math, os, sys, time
from pathlib import Path
import numpy as np
import torch

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
torch.set_num_threads(1)
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]; OUT = HERE / "run"; MODEL_DIR = ROOT / "results/E015-joint-logic-router"; sys.path.insert(0, str(MODEL_DIR))
import model as m


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def train(seed, condition):
    x, y = m.data("numeric"); rng = np.random.default_rng(seed); order = rng.permutation(64); train_idx, test_idx = order[:32], order[32:]
    net = m.LogicMixture("numeric", seed, condition); net.hash_map.copy_(m.balanced_hash(seed + 40000)); prior, _ = m.oracle_parameters(net)
    with torch.no_grad(): net.gate_logits.copy_(prior.sign() * 1.5 + net.gate_logits)
    optimizer = torch.optim.Adam(net.parameters(), lr=.03); curve = []
    for step in range(800):
        temperature = 1 - .9 * step / 799; prediction, routing, schedule = net(x[train_idx], temperature, False)
        task_loss = torch.nn.functional.binary_cross_entropy(prediction.clamp(1e-6, 1 - 1e-6), y[train_idx]); importance = routing.mean(0); balance = 4 * importance.square().sum() - 1
        entropy = -(schedule * schedule.clamp_min(1e-12).log()).sum(1).mean() / math.log(schedule.shape[1]); table = torch.sigmoid(net.gate_logits / temperature); softness = (4 * table * (1 - table)).mean(); loss = task_loss + .1 * balance + .01 * (entropy + softness)
        optimizer.zero_grad(); loss.backward(); optimizer.step()
        if step in (0, 799) or step % 200 == 0: curve.append(dict(step=step, task_loss=float(task_loss.detach()), balance_loss=float(balance.detach()), schedule_entropy=float(entropy.detach()), table_softness=float(softness.detach())))
    evaluation = {}
    with torch.no_grad():
        for hard in (False, True):
            prediction, routing, schedule = net(x, .1, hard); label = "hard" if hard else "soft"
            evaluation[label] = dict(train=m.metrics(prediction[train_idx], y[train_idx]), test=m.metrics(prediction[test_idx], y[test_idx]), full=m.metrics(prediction, y), utilization_train=routing[train_idx].mean(0).tolist(), utilization_test=routing[test_idx].mean(0).tolist(), utilization_full=routing.mean(0).tolist(), selected_schedules=schedule.argmax(1).tolist())
    return net, dict(seed=seed, task="numeric", condition=condition, split_seed=seed, hash_seed=seed + 40000, train_indices=train_idx.tolist(), test_indices=test_idx.tolist(), fixed_train_counts=torch.bincount(net.hash_map[torch.tensor(train_idx)], minlength=4).tolist(), evaluation=evaluation, curve=curve)


def main():
    OUT.mkdir(exist_ok=False); started = time.monotonic(); records = []
    for seed in range(800, 816):
        for condition in ("fixed_hash", "learned_balanced"):
            if time.monotonic() - started > 900: raise RuntimeError("wall budget exceeded; progress retained")
            net, record = train(seed, condition); checkpoint = f"numeric-{seed}-{condition}.pt"; torch.save(dict(gate_logits=net.gate_logits.detach(), schedule_logits=net.schedule_logits.detach(), router_weight=net.router_weight.detach(), hash_map=net.hash_map.detach()), OUT / checkpoint); record.update(checkpoint=checkpoint, checkpoint_sha256=sha(OUT / checkpoint)); records.append(record); (OUT / "progress.json").write_text(json.dumps(records, indent=2)); print(seed, condition, record["evaluation"]["hard"]["test"], record["fixed_train_counts"], flush=True)
    fixed_counts = [row["fixed_train_counts"] for row in records if row["condition"] == "fixed_hash"]
    assert any(counts != [8, 8, 8, 8] for counts in fixed_counts)
    source_files = (Path(__file__), HERE / "PROTOCOL.md", MODEL_DIR / "model.py")
    result = dict(records=records, elapsed_seconds=time.monotonic() - started, torch_version=torch.__version__, numpy_version=np.__version__, settings=dict(seeds=list(range(800, 816)), steps=800, hash_offset=40000), sources={str(path.relative_to(ROOT)): sha(path) for path in source_files})
    (OUT / "results.json").write_text(json.dumps(result, indent=2)); print(json.dumps(dict(elapsed_seconds=result["elapsed_seconds"], trajectories=len(records)), indent=2))


if __name__ == "__main__": main()
