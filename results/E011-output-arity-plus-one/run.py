"""E011: exact synthesis after adding one direct input to an output gate."""
import gzip
import hashlib
import json
import os
import sys
import time
from pathlib import Path

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "run"
sys.path.insert(0, str(ROOT / "results/E008-fixed-wiring-sat"))
import solve as base

np, z3 = base.np, base.z3


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def influences(x, target):
    indices = np.arange(len(x))
    return [float(np.mean(target != target[indices ^ (1 << bit)])) for bit in range(x.shape[1])]


def select_sources(output_ports, influence, task, seed, bit):
    available = [source for source in range(6) if source not in output_ports]
    assert available
    task_index = int(task == "selection")
    rng = np.random.default_rng(111000 + task_index * 10000 + seed * 19 + bit)
    random_source = int(rng.choice(available))
    best = max(influence[source] for source in available)
    best_sources = [source for source in available if influence[source] == best]
    influence_source = int(rng.choice(best_sources))
    return random_source, influence_source, available


def main():
    OUT.mkdir(exist_ok=False)
    e009_path = ROOT / "results/E009-output-bit-diagnosis/run/results.json"
    selected = [row for row in json.loads(e009_path.read_text())["records"] if row["status"] == "unsat"]
    assert len(selected) == 108
    records = []
    started = time.monotonic()
    for case_index, prior in enumerate(selected):
        checkpoint = ROOT / (
            f"results/E007-full-domain/run/{prior['task']}-{prior['seed']}-"
            f"{prior['condition']}-full64-1600.npz"
        )
        arrays = np.load(checkpoint)
        original = np.concatenate([arrays["pair0"], arrays["pair1"]]).tolist() + arrays["head"].tolist()
        x, y = base.data(prior["task"])
        target = y[:, prior["bit"]]
        gate_index = 64 + prior["bit"]
        influence = influences(x, target)
        random_source, influence_source, available = select_sources(
            original[gate_index], influence, prior["task"], prior["seed"], prior["bit"]
        )
        for condition, source in (("random_add", random_source), ("influence_add", influence_source)):
            if time.monotonic() - started > 900:
                raise RuntimeError("wall budget exceeded; progress retained")
            wires = [list(ports) for ports in original]
            old_arity = len(wires[gate_index])
            wires[gate_index].append(source)
            assert len(wires[gate_index]) == old_arity + 1
            assert all(wires[index] == original[index] for index in range(len(wires)) if index != gate_index)
            ctx, solver, tables = base.build(x, target[:, None], wires, [70 + prior["bit"]])
            solver.set(timeout=2000, random_seed=0, threads=1)
            stem = (
                f"{prior['task']}-{prior['seed']}-{prior['condition']}-"
                f"bit{prior['bit']}-{condition}"
            )
            formula = OUT / f"{stem}.smt2.gz"
            with gzip.open(formula, "wt") as handle:
                handle.write(solver.to_smt2())
            checked = time.monotonic()
            status = str(solver.check())
            elapsed = time.monotonic() - checked
            row = dict(
                case_index=case_index,
                task=prior["task"],
                seed=prior["seed"],
                original_architecture=prior["condition"],
                bit=prior["bit"],
                condition=condition,
                status=status,
                seconds=elapsed,
                old_arity=old_arity,
                new_arity=old_arity + 1,
                added_truth_bits=2 ** (old_arity + 1) - 2**old_arity,
                new_source=source,
                available_sources=available,
                influences=influence,
                same_source=random_source == influence_source,
                checkpoint_sha256=digest(checkpoint),
                formula_sha256=digest(formula),
            )
            if status == "sat":
                model = solver.model()
                truth = [
                    [int(z3.is_true(model.eval(value, model_completion=True))) for value in table]
                    for table in tables
                ]
                predicted = base.evaluate(x, wires, truth, [70 + prior["bit"]])
                assert np.array_equal(predicted, target[:, None])
                (OUT / f"{stem}-witness.json").write_text(
                    json.dumps(dict(wires=wires, tables=truth, outputs=[70 + prior["bit"]]))
                )
                row["independent_exact"] = 1
            elif status == "unknown":
                row["reason"] = solver.reason_unknown()
            records.append(row)
            (OUT / "progress.json").write_text(json.dumps(records, indent=2))
            print(stem, status, flush=True)
    sources = [Path(__file__), HERE / "PROTOCOL.md", Path(base.__file__)]
    result = dict(
        records=records,
        elapsed_seconds=time.monotonic() - started,
        z3_version=z3.get_version_string(),
        numpy_version=np.__version__,
        timeout_ms=2000,
        solver_seed=0,
        source_hashes={str(path.relative_to(ROOT)): digest(path) for path in sources},
        e009_results_sha256=digest(e009_path),
    )
    (OUT / "results.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
