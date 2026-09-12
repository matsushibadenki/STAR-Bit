"""E010: fixed-budget synthesis after exactly one output-wire replacement."""
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
sys.path.insert(0, str(ROOT / "results/E008-fixed-wiring-sat"))
import solve as base

np, z3 = base.np, base.z3
OUT = HERE / "run"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relevant_inputs(x, target):
    relevant = []
    indices = np.arange(len(x))
    for bit in range(x.shape[1]):
        paired = indices ^ (1 << bit)
        if np.any(target != target[paired]):
            relevant.append(bit)
    return relevant


def raw_ancestors(wires, gate_index):
    memo = {}

    def visit(index):
        if index in memo:
            return memo[index]
        found = set()
        for source in wires[index]:
            source = int(source)
            if source < 6:
                found.add(source)
            else:
                found.update(visit(source - 6))
        memo[index] = found
        return found

    return sorted(visit(gate_index))


def choices(wires, gate_index, relevant, task_index, seed, bit):
    rng = np.random.default_rng(101000 + task_index * 10000 + seed * 17 + bit)
    port = int(rng.integers(len(wires[gate_index])))
    old = int(wires[gate_index][port])
    random_pool = [i for i in range(6) if i != old]
    random_source = int(rng.choice(random_pool))
    ancestors = raw_ancestors(wires, gate_index)
    missing = [i for i in relevant if i not in ancestors]
    guided_pool = missing or [i for i in relevant if i != old]
    if not guided_pool:
        raise AssertionError("no valid dependency-guided replacement")
    guided_source = int(rng.choice(guided_pool))
    return port, old, random_source, guided_source, ancestors, missing, not bool(missing)


def main():
    OUT.mkdir(exist_ok=False)
    e009 = json.loads((ROOT / "results/E009-output-bit-diagnosis/run/results.json").read_text())
    selected = [row for row in e009["records"] if row["status"] == "unsat"]
    assert len(selected) == 108
    started = time.monotonic()
    records = []
    for case_index, prior in enumerate(selected):
        checkpoint = ROOT / (
            f"results/E007-full-domain/run/{prior['task']}-{prior['seed']}-"
            f"{prior['condition']}-full64-1600.npz"
        )
        arrays = np.load(checkpoint)
        original = np.concatenate([arrays["pair0"], arrays["pair1"]]).tolist() + arrays["head"].tolist()
        x, y = base.data(prior["task"])
        target = y[:, prior["bit"]]
        relevant = relevant_inputs(x, target)
        gate_index = 64 + prior["bit"]
        port, old, random_source, guided_source, ancestors, missing, fallback = choices(
            original, gate_index, relevant, int(prior["task"] == "selection"), prior["seed"], prior["bit"]
        )
        for condition, source in (("random_raw", random_source), ("dependency_raw", guided_source)):
            if time.monotonic() - started > 900:
                raise RuntimeError("wall budget exceeded; progress retained")
            wires = [list(row) for row in original]
            wires[gate_index][port] = source
            differences = sum(a != b for wa, wb in zip(original, wires) for a, b in zip(wa, wb))
            assert differences == 1 and source != old
            ctx, solver, tables = base.build(x, target[:, None], wires, [70 + prior["bit"]])
            solver.set(timeout=1000, random_seed=0, threads=1)
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
                architecture=prior["condition"],
                bit=prior["bit"],
                condition=condition,
                status=status,
                seconds=elapsed,
                port=port,
                old_source=old,
                new_source=source,
                relevant_inputs=relevant,
                original_ancestors=ancestors,
                missing_relevant_inputs=missing,
                guided_fallback=fallback,
                same_replacement=random_source == guided_source,
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
                witness = dict(wires=wires, tables=truth, outputs=[70 + prior["bit"]])
                (OUT / f"{stem}-witness.json").write_text(json.dumps(witness))
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
        timeout_ms=1000,
        solver_seed=0,
        source_hashes={str(path.relative_to(ROOT)): digest(path) for path in sources},
        e009_results_sha256=digest(ROOT / "results/E009-output-bit-diagnosis/run/results.json"),
    )
    (OUT / "results.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
