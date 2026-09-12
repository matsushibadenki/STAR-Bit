"""E018 CEGIS versus all-row SAT pilot."""
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, "/private/tmp/starbit-z3")
import z3

E017 = Path(__file__).resolve().parents[1] / "E017-learned-circuit-abstraction"
sys.path.insert(0, str(E017))
import refine

HERE = Path(__file__).resolve().parent
OUT = HERE / "pilot"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose(index, sources):
    value = sources[-1]
    for position in reversed(range(len(sources)-1)):
        value = z3.If(index == position, sources[position], value)
    return value


def build(task, seed, gates=10):
    columns, target = refine.columns_and_target(task)
    solver = z3.Solver()
    solver.set(timeout=10000, random_seed=seed, threads=1)
    genes = []
    outputs = []
    for gate in range(gates):
        a = z3.Int(f"a_{gate}")
        b = z3.Int(f"b_{gate}")
        table = [z3.Bool(f"t_{gate}_{entry}") for entry in range(4)]
        solver.add(a >= 0, a < 6 + gate, b >= 0, b < 6 + gate, a <= b)
        sources = [z3.BitVecVal(value, 64) for value in columns] + outputs
        left, right = choose(a, sources), choose(b, sources)
        terms = [~left & ~right, left & ~right, ~left & right, left & right]
        output = z3.BitVecVal(0, 64)
        for enabled, term in zip(table, terms):
            output = output | z3.If(enabled, term, z3.BitVecVal(0, 64))
        outputs.append(output)
        genes.append((a, b, table))
    return solver, genes, outputs[-1], columns, target


def add_rows(solver, output, target, rows):
    mask = sum(1 << row for row in rows)
    solver.add((output & z3.BitVecVal(mask, 64)) == z3.BitVecVal(target & mask, 64))


def extract(model, genes):
    sequential = []
    for a, b, table in genes:
        code = sum(int(z3.is_true(model.eval(value, model_completion=True))) << bit for bit, value in enumerate(table))
        sequential.append([model.eval(a).as_long(), model.eval(b).as_long(), code])
    return {"sequential": sequential, "output": len(sequential)-1}


def evaluate(genome, columns):
    bank = list(columns)
    for a, b, code in genome["sequential"]:
        bank.append(refine.lut(bank[a], bank[b], code))
    return bank[-1]


def run_one(task, seed, condition):
    solver, genes, output, columns, target = build(task, seed)
    if condition == "all_rows":
        constrained = list(range(64))
    else:
        constrained = sorted(random.Random(seed).sample(range(64), 8))
    add_rows(solver, output, target, constrained)
    calls = []
    witness = None
    begin = time.monotonic()
    for iteration in range(41):
        check_start = time.monotonic()
        status = solver.check()
        calls.append({"iteration": iteration, "status": str(status), "seconds": time.monotonic()-check_start, "constrained_rows": len(constrained), "reason_unknown": solver.reason_unknown() if status == z3.unknown else None})
        if status != z3.sat:
            break
        candidate = extract(solver.model(), genes)
        observed = evaluate(candidate, columns)
        errors = [row for row in range(64) if ((observed ^ target) >> row) & 1]
        if not errors:
            witness = candidate
            break
        if condition == "all_rows" or iteration == 40:
            break
        counterexample = errors[0]
        constrained.append(counterexample)
        add_rows(solver, output, target, [counterexample])
    exact = witness is not None
    if exact:
        assert evaluate(witness, columns) == target
    return {
        "task": task,
        "seed": seed,
        "condition": condition,
        "exact": exact,
        "final_status": calls[-1]["status"],
        "solver_calls": len(calls),
        "constrained_rows": constrained,
        "elapsed_seconds": time.monotonic()-begin,
        "calls": calls,
        "witness": witness,
    }


def metric(values):
    values = np.asarray(values, float)
    return {"mean": float(values.mean()), "variance": float(values.var(ddof=1))}


def main():
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    records = []
    for seed in range(1100, 1104):
        for task in ("parity", "comparator", "mux", "carry"):
            for condition in ("all_rows", "cegis"):
                if time.monotonic() - started > 900:
                    raise RuntimeError("900-second wall budget reached; progress retained")
                row = run_one(task, seed, condition)
                records.append(row)
                (OUT / "progress.json").write_text(json.dumps(records, indent=2))
                print(seed, task, condition, row["exact"], row["final_status"], row["solver_calls"], row["elapsed_seconds"], flush=True)
    aggregate = {}
    for condition in ("all_rows", "cegis"):
        group = [row for row in records if row["condition"] == condition]
        aggregate[condition] = {
            "exact_total": sum(row["exact"] for row in group),
            "exact_by_task": {task: sum(row["exact"] for row in group if row["task"] == task) for task in ("parity", "comparator", "mux", "carry")},
            "success": metric([row["exact"] for row in group]),
            "solver_calls": metric([row["solver_calls"] for row in group]),
            "seconds": metric([row["elapsed_seconds"] for row in group]),
        }
    viable = all(value >= 3 for value in aggregate["cegis"]["exact_by_task"].values()) and aggregate["cegis"]["exact_total"] > aggregate["all_rows"]["exact_total"]
    result = {
        "records": records,
        "aggregate": aggregate,
        "viable": viable,
        "elapsed_seconds": time.monotonic()-started,
        "z3_version": z3.get_version_string(),
        "sources": {str(path.relative_to(HERE.parents[1])): sha(path) for path in (Path(__file__), HERE / "PILOT-PROTOCOL.md", E017 / "refine.py")},
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"aggregate": aggregate, "viable": viable, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
