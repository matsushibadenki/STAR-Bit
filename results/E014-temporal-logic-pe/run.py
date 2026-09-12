"""E014 temporal reusable Logic PE experiment."""
import hashlib, itertools, json, os, time
from pathlib import Path
import numpy as np

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"

HERE = Path(__file__).resolve().parent
OUT = HERE / "run"


def sha_bytes(value): return hashlib.sha256(value).hexdigest()
def sha_file(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def data():
    x = ((np.arange(64)[:, None] >> np.arange(6)) & 1).astype(np.uint8)
    total = x[:, :3] @ np.array([1, 2, 4]) + x[:, 3:] @ np.array([1, 2, 4])
    numeric = ((total[:, None] >> np.arange(4)) & 1).astype(np.uint8)
    shift = x[:, 0] + 2 * x[:, 1]
    selection = np.stack([x[np.arange(64), 2 + (shift + i) % 4] for i in range(4)], axis=1)
    return x, {"numeric": numeric, "selection": selection}


def full_adder(a, b, carry):
    propagate = a ^ b
    result = propagate ^ carry
    next_carry = (a & b) | (propagate & carry)
    return result, next_carry


def add_schedule(x, left_order, right_order):
    carry = np.zeros(len(x), dtype=np.uint8); outputs = []
    for left, right in zip(left_order, right_order):
        result, carry = full_adder(x[:, left], x[:, 3 + right], carry); outputs.append(result)
    return np.column_stack(outputs + [carry])


def shift_permutation(offset): return [(index + offset) % 4 for index in range(4)]


def mux_stage(state, selector, a_shift, b_shift):
    a = state[:, shift_permutation(a_shift)]; b = state[:, shift_permutation(b_shift)]
    return np.where(selector[:, None].astype(bool), b, a).astype(np.uint8)


def selection_schedule(x, route):
    state = x[:, 2:6].copy()
    order, a0, b0, a1, b1 = route
    selectors = (0, 1) if order == 0 else (1, 0)
    state = mux_stage(state, x[:, selectors[0]], a0, b0)
    return mux_stage(state, x[:, selectors[1]], a1, b1)


def candidates(x):
    permutations = list(itertools.permutations(range(3)))
    add_routes = [(left, right) for left in permutations for right in permutations]
    add_outputs = np.stack([add_schedule(x, *route) for route in add_routes])
    select_routes = list(itertools.product(range(2), range(4), range(4), range(4), range(4)))
    select_outputs = np.stack([selection_schedule(x, route) for route in select_routes])
    return {"numeric": (add_routes, add_outputs), "selection": (select_routes, select_outputs)}


def metrics(predicted, target, indices):
    equal = predicted[:, indices] == target[None, indices]
    return equal.all(2).mean(1), equal.mean((1, 2))


def route_json(route):
    if isinstance(route, tuple): return [route_json(value) for value in route]
    return int(route)


def main():
    OUT.mkdir(exist_ok=False)
    started = time.monotonic(); x, targets = data(); library = candidates(x); records = []
    oracle_index = {"numeric": library["numeric"][0].index(((0, 1, 2), (0, 1, 2)))}
    valid_selection = [i for i, output in enumerate(library["selection"][1]) if np.array_equal(output, targets["selection"])]
    assert valid_selection
    oracle_index["selection"] = valid_selection[0]
    library_summary = {}
    for task, (routes, outputs) in library.items():
        target = targets[task]
        assert np.array_equal(outputs[oracle_index[task]], target)
        library_summary[task] = dict(size=len(routes), exact_full_domain=sum(np.array_equal(output, target) for output in outputs), outputs_sha256=sha_bytes(outputs.tobytes()), oracle_index=oracle_index[task], oracle_route=route_json(routes[oracle_index[task]]))
        for seed in range(600, 616):
            if time.monotonic() - started > 900: raise RuntimeError("wall budget exceeded")
            rng = np.random.default_rng(seed + (10000 if task == "selection" else 0))
            order = rng.permutation(64); train, test = order[:32], order[32:]
            train_exact, train_bit = metrics(outputs, target, train)
            best_exact = train_exact.max(); eligible = np.flatnonzero(train_exact == best_exact)
            best_bit = train_bit[eligible].max(); eligible = eligible[train_bit[eligible] == best_bit]
            selected_index = int(rng.choice(eligible)); random_index = int(rng.integers(len(routes)))
            for condition, index in (("fixed_random", random_index), ("train_selected", selected_index), ("structured_oracle", oracle_index[task])):
                prediction = outputs[index]
                record = dict(seed=seed, task=task, condition=condition, route_index=index, route=route_json(routes[index]), train_indices=train.tolist(), test_indices=test.tolist(), train_exact=float((prediction[train] == target[train]).all(1).mean()), train_bit=float((prediction[train] == target[train]).mean()), test_exact=float((prediction[test] == target[test]).all(1).mean()), test_bit=float((prediction[test] == target[test]).mean()), full_exact=float((prediction == target).all(1).mean()), full_bit=float((prediction == target).mean()), source_load_variance=0.0)
                records.append(record)
    costs = {
        "numeric": {"temporal_physical_gates": 5, "spatial_physical_gates": 15, "active_gate_evaluations": 15, "cycles": 3, "state_bits": 5, "candidate_route_bits": int(np.ceil(np.log2(36)))},
        "selection": {"temporal_physical_gates": 12, "spatial_physical_gates": 24, "active_gate_evaluations": 24, "cycles": 2, "state_bits": 4, "candidate_route_bits": 9},
    }
    result = dict(records=records, library=library_summary, costs=costs, elapsed_seconds=time.monotonic() - started, numpy_version=np.__version__, source_sha256=sha_file(Path(__file__)), protocol_sha256=sha_file(HERE / "PROTOCOL.md"))
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(library=library_summary, elapsed_seconds=result["elapsed_seconds"]), indent=2))


if __name__ == "__main__": main()
