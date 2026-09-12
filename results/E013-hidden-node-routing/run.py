"""E013: exact synthesis with a case-wide selector over hidden nodes."""
import gzip, hashlib, json, os, sys, time
from pathlib import Path

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "run"
sys.path.insert(0, str(ROOT / "results/E008-fixed-wiring-sat"))
import solve as base
np, z3 = base.np, base.z3


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def build(x, target, hidden_wires, candidates):
    ctx = z3.Context(proof=True)
    solver = z3.Solver(ctx=ctx)
    solver.set(timeout=2000, random_seed=0, threads=1)
    tables = [[z3.Bool(f"g{i}_t{j}", ctx) for j in range(4)] for i in range(64)]
    selectors = [z3.Bool(f"select_{index}", ctx) for index in candidates]
    solver.add(z3.PbEq([(selector, 1) for selector in selectors], 1))
    for sample, (features, expected) in enumerate(zip(x, target)):
        bank = [z3.BoolVal(bool(value), ctx) for value in features]
        equations = []
        for gate, ports in enumerate(hidden_wires):
            node = z3.Bool(f"row{sample}_g{gate}", ctx)
            equations.append(node == base.mux([bank[port] for port in ports], tables[gate]))
            bank.append(node)
        chosen = z3.Or(*[z3.And(selector, bank[index]) for selector, index in zip(selectors, candidates)])
        equations.append(chosen == z3.BoolVal(bool(expected), ctx))
        solver.add(*equations)
    return solver, tables, selectors


def main():
    OUT.mkdir(exist_ok=False)
    e009 = ROOT / "results/E009-output-bit-diagnosis/run/results.json"
    cases = [row for row in json.loads(e009.read_text())["records"] if row["status"] == "unsat"]
    assert len(cases) == 108
    records, started = [], time.monotonic()
    for case_index, prior in enumerate(cases):
        checkpoint = ROOT / f"results/E007-full-domain/run/{prior['task']}-{prior['seed']}-{prior['condition']}-full64-1600.npz"
        arrays = np.load(checkpoint)
        hidden_wires = np.concatenate([arrays["pair0"], arrays["pair1"]]).tolist()
        assert len(hidden_wires) == 64
        x, y = base.data(prior["task"])
        target = y[:, prior["bit"]]
        for condition, candidates in (("layer1_select", list(range(38, 70))), ("all_hidden_select", list(range(6, 70)))):
            if time.monotonic() - started > 900: raise RuntimeError("wall budget exceeded; progress retained")
            solver, tables, selectors = build(x, target, hidden_wires, candidates)
            stem = f"{prior['task']}-{prior['seed']}-{prior['condition']}-bit{prior['bit']}-{condition}"
            formula = OUT / f"{stem}.smt2.gz"
            with gzip.open(formula, "wt") as handle: handle.write(solver.to_smt2())
            checked = time.monotonic(); status = str(solver.check()); seconds = time.monotonic() - checked
            row = dict(case_index=case_index, task=prior["task"], seed=prior["seed"], original_architecture=prior["condition"], bit=prior["bit"], condition=condition, status=status, seconds=seconds, candidate_count=len(candidates), checkpoint_sha256=sha(checkpoint), formula_sha256=sha(formula))
            if status == "sat":
                model = solver.model()
                selected = [index for selector, index in zip(selectors, candidates) if z3.is_true(model.eval(selector, model_completion=True))]
                assert len(selected) == 1
                truth = [[int(z3.is_true(model.eval(value, model_completion=True))) for value in table] for table in tables]
                actual = base.evaluate(x, hidden_wires, truth, selected)
                assert np.array_equal(actual, target[:, None])
                (OUT / f"{stem}-witness.json").write_text(json.dumps(dict(wires=hidden_wires, tables=truth, outputs=selected)))
                row.update(independent_exact=1, selected_node=selected[0], selected_layer=0 if selected[0] < 38 else 1)
            elif status == "unknown": row["reason"] = solver.reason_unknown()
            records.append(row)
            (OUT / "progress.json").write_text(json.dumps(records, indent=2))
            print(stem, status, flush=True)
    source_files = [Path(__file__), HERE / "PROTOCOL.md", Path(base.__file__)]
    result = dict(records=records, elapsed_seconds=time.monotonic() - started, z3_version=z3.get_version_string(), numpy_version=np.__version__, timeout_ms=2000, solver_seed=0, source_hashes={str(path.relative_to(ROOT)): sha(path) for path in source_files}, e009_results_sha256=sha(e009))
    (OUT / "results.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__": main()
