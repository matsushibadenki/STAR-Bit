"""Equivalent 64-bit-vector SAT encoding for E017 circuit synthesis."""
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/private/tmp/starbit-z3")
import z3

import refine

HERE = Path(__file__).resolve().parent
OUT = HERE / "sat_bv_probe"
MASK = (1 << 64) - 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def choose(index, sources):
    value = sources[-1]
    for position in reversed(range(len(sources) - 1)):
        value = z3.If(index == position, sources[position], value)
    return value


def solve(task, gates):
    columns, target = refine.columns_and_target(task)
    solver = z3.Solver()
    solver.set(timeout=10000, random_seed=0, threads=1)
    outputs = []
    genes = []
    for gate in range(gates):
        source_count = 6 + gate
        a_index = z3.Int(f"a_{gate}")
        b_index = z3.Int(f"b_{gate}")
        table = [z3.Bool(f"t_{gate}_{entry}") for entry in range(4)]
        solver.add(a_index >= 0, a_index < source_count, b_index >= 0, b_index < source_count, a_index <= b_index)
        sources = [z3.BitVecVal(value, 64) for value in columns] + outputs
        a = choose(a_index, sources)
        b = choose(b_index, sources)
        not_a, not_b = ~a, ~b
        terms = [not_a & not_b, a & not_b, not_a & b, a & b]
        output = z3.BitVecVal(0, 64)
        for enabled, term in zip(table, terms):
            output = output | z3.If(enabled, term, z3.BitVecVal(0, 64))
        outputs.append(output)
        genes.append((a_index, b_index, table))
    solver.add(outputs[-1] == z3.BitVecVal(target, 64))
    status = solver.check()
    row = {"task": task, "gates": gates, "status": str(status), "reason_unknown": solver.reason_unknown() if status == z3.unknown else None}
    if status != z3.sat:
        return row
    model = solver.model()
    sequential = []
    for a_index, b_index, table in genes:
        code = sum(int(z3.is_true(model.eval(entry, model_completion=True))) << bit for bit, entry in enumerate(table))
        sequential.append([model.eval(a_index).as_long(), model.eval(b_index).as_long(), code])
    bank = list(columns)
    for a, b, code in sequential:
        bank.append(refine.lut(bank[a], bank[b], code))
    assert bank[-1] == target
    row.update(verified=True, genome={"sequential": sequential, "output": gates - 1})
    return row


def main():
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    records = []
    first_sat = {}
    for task in ("parity", "comparator", "mux", "carry"):
        for gates in range(1, 11):
            begin = time.monotonic()
            row = solve(task, gates)
            row["seconds"] = time.monotonic() - begin
            records.append(row)
            (OUT / "progress.json").write_text(json.dumps(records, indent=2))
            print(task, gates, row["status"], row["seconds"], flush=True)
            if row["status"] == "sat":
                first_sat[task] = gates
                break
    result = {
        "records": records,
        "first_sat": first_sat,
        "all_tasks_sat": len(first_sat) == 4,
        "elapsed_seconds": time.monotonic() - started,
        "z3_version": z3.get_version_string(),
        "sources": {path.name: sha(path) for path in (Path(__file__), HERE / "refine.py", HERE / "SAT-BV-PROTOCOL.md")},
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"first_sat": first_sat, "all_tasks_sat": result["all_tasks_sat"], "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
