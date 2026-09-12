"""Independent spatial-reference checks for E014."""
import hashlib, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as temporal


def spatial_add(x):
    zero = np.zeros(len(x), dtype=np.uint8)
    sum0, carry1 = temporal.full_adder(x[:, 0], x[:, 3], zero)
    sum1, carry2 = temporal.full_adder(x[:, 1], x[:, 4], carry1)
    sum2, carry3 = temporal.full_adder(x[:, 2], x[:, 5], carry2)
    return np.column_stack([sum0, sum1, sum2, carry3])


def spatial_selection(x):
    initial = x[:, 2:6]
    stage0 = np.column_stack([
        np.where(x[:, 0], initial[:, (index + 1) % 4], initial[:, index])
        for index in range(4)
    ]).astype(np.uint8)
    return np.column_stack([
        np.where(x[:, 1], stage0[:, (index + 2) % 4], stage0[:, index])
        for index in range(4)
    ]).astype(np.uint8)


x, targets = temporal.data()
temporal_numeric = temporal.add_schedule(x, (0, 1, 2), (0, 1, 2))
temporal_selection = temporal.selection_schedule(x, (0, 0, 1, 0, 2))
checks = dict(
    full_adder_truth_table=True,
    mux_truth_table=True,
    numeric_spatial_temporal_equal=bool(np.array_equal(spatial_add(x), temporal_numeric)),
    numeric_target_equal=bool(np.array_equal(temporal_numeric, targets["numeric"])),
    selection_spatial_temporal_equal=bool(np.array_equal(spatial_selection(x), temporal_selection)),
    selection_target_equal=bool(np.array_equal(temporal_selection, targets["selection"])),
)
for a in (0, 1):
    for b in (0, 1):
        for carry in (0, 1):
            result, next_carry = temporal.full_adder(np.array([a]), np.array([b]), np.array([carry]))
            assert int(result[0]) == ((a + b + carry) & 1) and int(next_carry[0]) == ((a + b + carry) >> 1)
for selector in (0, 1):
    for a in (0, 1):
        for b in (0, 1):
            state = np.array([[a, 0, 0, b]], dtype=np.uint8)
            actual = temporal.mux_stage(state, np.array([selector]), 0, 3)[0, 0]
            assert int(actual) == (b if selector else a)
assert all(checks.values())
checks["verify_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(HERE / "run/verification.json").write_text(json.dumps(checks, indent=2))
print(json.dumps(checks, indent=2))
