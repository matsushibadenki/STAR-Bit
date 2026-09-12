"""E012: exact synthesis after adding two direct inputs to an output gate."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def influences(x, target):
    indices = np.arange(len(x))
    return [float(np.mean(target != target[indices ^ (1 << bit)])) for bit in range(x.shape[1])]


def sources(output_ports, influence, task, seed, bit):
    available = [source for source in range(6) if source not in output_ports]
    assert len(available) >= 2
    rng = np.random.default_rng(121000 + int(task == "selection") * 10000 + seed * 23 + bit)
    random_pair = sorted(int(value) for value in rng.choice(available, size=2, replace=False))
    jitter = {source: float(rng.random()) for source in available}
    ranked = sorted(available, key=lambda source: (-influence[source], jitter[source]))
    influence_pair = sorted(ranked[:2])
    return random_pair, influence_pair, available


def main():
    OUT.mkdir(exist_ok=False)
    source_results = ROOT / "results/E009-output-bit-diagnosis/run/results.json"
    cases = [row for row in json.loads(source_results.read_text())["records"] if row["status"] == "unsat"]
    assert len(cases) == 108
    records = []
    started = time.monotonic()
    for case_index, prior in enumerate(cases):
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
        random_pair, influence_pair, available = sources(
            original[gate_index], influence, prior["task"], prior["seed"], prior["bit"]
        )
        for condition, added in (("random_add2", random_pair), ("influence_add2", influence_pair)):
            if time.monotonic() - started > 900:
                raise RuntimeError("wall budget exceeded; progress retained")
            wires = [list(ports) for ports in original]
            old_arity = len(wires[gate_index])
            wires[gate_index].extend(added)
            assert len(wires[gate_index]) == old_arity + 2 and len(set(added)) == 2
            assert all(wires[index] == original[index] for index in range(len(wires)) if index != gate_index)
            ctx, solver, tables = base.build(x, target[:, None], wires, [70 + prior["bit"]])
            solver.set(timeout=3000, random_seed=0, threads=1)
            stem = f"{prior['task']}-{prior['seed']}-{prior['condition']}-bit{prior['bit']}-{condition}"
            formula = OUT / f"{stem}.smt2.gz"
            with gzip.open(formula, "wt") as handle:
                handle.write(solver.to_smt2())
            checked = time.monotonic()
            status = str(solver.check())
            seconds = time.monotonic() - checked
            row = dict(
                case_index=case_index,
                task=prior["task"],
                seed=prior["seed"],
                original_architecture=prior["condition"],
                bit=prior["bit"],
                condition=condition,
                status=status,
                seconds=seconds,
                old_arity=old_arity,
                new_arity=old_arity + 2,
                added_truth_bits=2 ** (old_arity + 2) - 2**old_arity,
                new_sources=added,
                available_sources=available,
                influences=influence,
                same_sources=random_pair == influence_pair,
                checkpoint_sha256=sha(checkpoint),
                formula_sha256=sha(formula),
            )
            if status == "sat":
                model = solver.model()
                truth = [[int(z3.is_true(model.eval(value, model_completion=True))) for value in table] for table in tables]
                actual = base.evaluate(x, wires, truth, [70 + prior["bit"]])
                assert np.array_equal(actual, target[:, None])
                (OUT / f"{stem}-witness.json").write_text(json.dumps(dict(wires=wires, tables=truth, outputs=[70 + prior["bit"]])))
                row["independent_exact"] = 1
            elif status == "unknown":
                row["reason"] = solver.reason_unknown()
            records.append(row)
            (OUT / "progress.json").write_text(json.dumps(records, indent=2))
            print(stem, status, flush=True)
    source_files = [Path(__file__), HERE / "PROTOCOL.md", Path(base.__file__)]
    result = dict(
        records=records,
        elapsed_seconds=time.monotonic() - started,
        z3_version=z3.get_version_string(),
        numpy_version=np.__version__,
        timeout_ms=3000,
        solver_seed=0,
        source_hashes={str(path.relative_to(ROOT)): sha(path) for path in source_files},
        e009_results_sha256=sha(source_results),
    )
    (OUT / "results.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
