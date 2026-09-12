"""E015 confirmatory joint optimization and Expert interventions."""
import hashlib, json, os, sys, time
from pathlib import Path
import numpy as np
import torch

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
torch.set_num_threads(1)
HERE = Path(__file__).resolve().parent; OUT = HERE / "run"; sys.path.insert(0, str(HERE))
import model as m
import pilot2


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_rows(base, replacement, rows=(0,)):
    result = base.detach().clone()
    for row in rows: result[row] = replacement[row]
    return result


def intervention_tensors(net, variant, donor=None, reinitialized=None):
    gate = net.gate_logits.detach().clone(); schedule = net.schedule_logits.detach().clone(); router = net.router_weight.detach().clone(); mapping = net.hash_map.detach().clone()
    if variant in ("same_run_swap", "symmetry_control"):
        gate[[0, 1]] = gate[[1, 0]]; schedule[[0, 1]] = schedule[[1, 0]]
        if variant == "symmetry_control":
            if net.condition == "learned_balanced": router[:, [0, 1]] = router[:, [1, 0]]
            else:
                swapped = mapping.clone(); swapped[mapping == 0] = 1; swapped[mapping == 1] = 0; mapping = swapped
    elif variant == "cross_seed":
        gate[0] = donor.gate_logits.detach()[0]; schedule[0] = donor.schedule_logits.detach()[0]
    elif variant == "zero_expert":
        gate[0] = -10
    elif variant == "reinitialized_expert":
        gate[0] = reinitialized.gate_logits.detach()[0]; schedule[0] = reinitialized.schedule_logits.detach()[0]
    elif variant != "self_replace": raise ValueError(variant)
    return gate, schedule, router, mapping


def evaluate_intervention(net, record, variant, donor=None, reinitialized=None):
    x, y = m.data(record["task"]); train = np.asarray(record["train_indices"]); test = np.asarray(record["test_indices"])
    gate, schedule, router, mapping = intervention_tensors(net, variant, donor, reinitialized); answer = dict(task=record["task"], seed=record["seed"], condition=record["condition"], variant=variant)
    with torch.no_grad():
        for hard in (False, True):
            label = "hard" if hard else "soft"; baseline = net(x, .1, hard)[0]; changed = net(x, .1, hard, gate, schedule, router, mapping)[0]
            answer[label] = dict(test=m.metrics(changed[test], y[test]), full=m.metrics(changed, y), baseline_test=m.metrics(baseline[test], y[test]), baseline_full=m.metrics(baseline, y), max_output_change=float((changed - baseline).abs().max()))
    return answer


def main():
    OUT.mkdir(exist_ok=False); started = time.monotonic(); models = {}; records = []
    for seed in range(700, 716):
        for task in ("numeric", "selection"):
            for condition in ("fixed_hash", "learned_balanced"):
                if time.monotonic() - started > 900: raise RuntimeError("main wall budget exceeded; progress retained")
                net, record = pilot2.train_prior(task, seed, condition); checkpoint = f"{task}-{seed}-{condition}.pt"; record["checkpoint"] = checkpoint
                state = dict(gate_logits=net.gate_logits.detach(), schedule_logits=net.schedule_logits.detach(), router_weight=net.router_weight.detach(), hash_map=net.hash_map.detach()); torch.save(state, OUT / checkpoint); record["checkpoint_sha256"] = sha(OUT / checkpoint)
                models[(task, condition, seed)] = net; records.append(record); (OUT / "training-progress.json").write_text(json.dumps(records, indent=2)); print("train", task, seed, condition, record["evaluation"]["hard"]["test"], flush=True)
    interventions = []
    for task in ("numeric", "selection"):
        for condition in ("fixed_hash", "learned_balanced"):
            for seed in range(700, 716):
                net = models[task, condition, seed]; record = next(row for row in records if (row["task"], row["condition"], row["seed"]) == (task, condition, seed)); donor_seed = 700 + ((seed - 700 + 1) % 16); donor = models[task, condition, donor_seed]
                fresh = m.LogicMixture(task, 90000 + seed, condition); prior, _ = m.oracle_parameters(fresh)
                with torch.no_grad(): fresh.gate_logits.copy_(prior.sign() * 1.5 + fresh.gate_logits)
                for variant in ("self_replace", "same_run_swap", "symmetry_control", "cross_seed", "zero_expert", "reinitialized_expert"):
                    item = evaluate_intervention(net, record, variant, donor, fresh); item["donor_seed"] = donor_seed if variant == "cross_seed" else None; interventions.append(item)
                assert interventions[-6]["hard"]["max_output_change"] == 0 and interventions[-6]["soft"]["max_output_change"] == 0
                assert interventions[-4]["hard"]["max_output_change"] < 1e-6 and interventions[-4]["soft"]["max_output_change"] < 1e-6
                (OUT / "intervention-progress.json").write_text(json.dumps(interventions, indent=2))
    source_files = (Path(__file__), HERE / "model.py", HERE / "pilot2.py", HERE / "PROTOCOL.md")
    result = dict(records=records, interventions=interventions, elapsed_seconds=time.monotonic() - started, torch_version=torch.__version__, numpy_version=np.__version__, settings=dict(seeds=list(range(700, 716)), steps=800, learning_rate=.03, temperature_floor=.1, discrete_weight=.01, balance_weight=.1, experts=4), sources={path.name: sha(path) for path in source_files})
    (OUT / "results.json").write_text(json.dumps(result, indent=2)); print(json.dumps(dict(elapsed_seconds=result["elapsed_seconds"], trajectories=len(records), interventions=len(interventions)), indent=2))


if __name__ == "__main__": main()
