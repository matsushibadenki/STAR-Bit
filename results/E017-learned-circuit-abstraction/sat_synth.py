"""SAT synthesis of sequential arbitrary two-input LUT circuits."""
import sys
from pathlib import Path

sys.path.insert(0, "/private/tmp/starbit-z3")
import z3

import refine


def select(index, sources):
    return z3.Or([z3.And(index == position, value) for position, value in enumerate(sources)])


def solve(task, gates, timeout_ms=10000, random_seed=0):
    columns, target = refine.columns_and_target(task)
    solver = z3.Solver()
    solver.set(timeout=timeout_ms, random_seed=random_seed, threads=1)
    a_index = [z3.Int(f"a_{gate}") for gate in range(gates)]
    b_index = [z3.Int(f"b_{gate}") for gate in range(gates)]
    tables = [[z3.Bool(f"t_{gate}_{entry}") for entry in range(4)] for gate in range(gates)]
    values = [[z3.Bool(f"v_{gate}_{row}") for row in range(64)] for gate in range(gates)]
    for gate in range(gates):
        solver.add(a_index[gate] >= 0, a_index[gate] < 6 + gate)
        solver.add(b_index[gate] >= 0, b_index[gate] < 6 + gate)
        solver.add(a_index[gate] <= b_index[gate])
        for row in range(64):
            sources = [z3.BoolVal(bool((column >> row) & 1)) for column in columns]
            sources += [values[earlier][row] for earlier in range(gate)]
            a = select(a_index[gate], sources)
            b = select(b_index[gate], sources)
            output = z3.Or(
                z3.And(z3.Not(a), z3.Not(b), tables[gate][0]),
                z3.And(a, z3.Not(b), tables[gate][1]),
                z3.And(z3.Not(a), b, tables[gate][2]),
                z3.And(a, b, tables[gate][3]),
            )
            solver.add(values[gate][row] == output)
    for row in range(64):
        solver.add(values[-1][row] == z3.BoolVal(bool((target >> row) & 1)))
    status = solver.check()
    record = {"task": task, "gates": gates, "status": str(status), "reason_unknown": solver.reason_unknown() if status == z3.unknown else None}
    if status != z3.sat:
        return record, None
    model = solver.model()
    genome = {"layers": [], "output": gates - 1}
    sequential = []
    for gate in range(gates):
        code = sum(int(z3.is_true(model.eval(tables[gate][entry], model_completion=True))) << entry for entry in range(4))
        sequential.append([model.eval(a_index[gate]).as_long(), model.eval(b_index[gate]).as_long(), code])
    genome["sequential"] = sequential
    observed = evaluate_sequential(genome, columns)
    assert observed == target
    record["verified"] = True
    record["genome"] = genome
    return record, genome


def evaluate_sequential(genome, columns):
    bank = list(columns)
    for a, b, code in genome["sequential"]:
        bank.append(refine.lut(bank[a], bank[b], code))
    return bank[6 + genome["output"]]

