"""Run the outcome-separated E015 optimization pilot."""
import hashlib, json, os, sys, time
from pathlib import Path
import torch

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
torch.set_num_threads(1)

HERE = Path(__file__).resolve().parent
OUT = HERE / "pilot"
sys.path.insert(0, str(HERE))
import model as m


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def swapped_evaluation(model, task, mode):
    x, _ = m.data(task)
    gate = model.gate_logits.detach().clone(); schedule = model.schedule_logits.detach().clone(); router = model.router_weight.detach().clone(); mapping = model.hash_map.detach().clone()
    gate[[0, 1]] = gate[[1, 0]]; schedule[[0, 1]] = schedule[[1, 0]]
    if model.condition == "learned_balanced": router[:, [0, 1]] = router[:, [1, 0]]
    else:
        swapped = mapping.clone(); swapped[mapping == 0] = 1; swapped[mapping == 1] = 0; mapping = swapped
    with torch.no_grad():
        original = model(x, .2, True)[0]
        symmetric = model(x, .2, True, gate, schedule, router, mapping)[0]
    return float((original - symmetric).abs().max())


def main():
    OUT.mkdir(exist_ok=False); started = time.monotonic(); oracle_checks = {}
    for task in ("numeric", "selection"):
        x, y = m.data(task); net = m.LogicMixture(task, 39, "learned_balanced"); gates, schedules = m.oracle_parameters(net)
        with torch.no_grad(): prediction = net(x, .2, True, gates, schedules)[0]
        oracle_checks[task] = m.metrics(prediction, y)
        assert oracle_checks[task]["exact"] == 1
    records = []
    for seed in range(40, 44):
        for task in ("numeric", "selection"):
            for condition in ("fixed_hash", "learned_balanced"):
                if time.monotonic() - started > 900: raise RuntimeError("pilot budget exceeded")
                net, record = m.train(task, seed, condition, steps=400, learning_rate=.03, temperature_floor=.2, discrete_weight=.01, balance_weight=.1)
                record["symmetric_swap_max_error"] = swapped_evaluation(net, task, condition)
                assert record["symmetric_swap_max_error"] < 1e-6
                record["checkpoint"] = f"{task}-{seed}-{condition}.pt"
                torch.save(dict(gate_logits=net.gate_logits.detach(), schedule_logits=net.schedule_logits.detach(), router_weight=net.router_weight.detach(), hash_map=net.hash_map.detach()), OUT / record["checkpoint"])
                records.append(record); (OUT / "progress.json").write_text(json.dumps(records, indent=2)); print(task, seed, condition, record["evaluations"]["hard"], flush=True)
    result = dict(records=records, oracle_checks=oracle_checks, elapsed_seconds=time.monotonic() - started, torch_version=torch.__version__, sources={path.name: sha(path) for path in (Path(__file__), HERE / "model.py", HERE / "PILOT-PROTOCOL.md")})
    (OUT / "results.json").write_text(json.dumps(result, indent=2)); print(json.dumps(dict(oracle=oracle_checks, elapsed_seconds=result["elapsed_seconds"]), indent=2))


if __name__ == "__main__": main()
