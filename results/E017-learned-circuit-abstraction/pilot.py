"""Run the preregistered E017 wiring-learning pilot."""
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch

import model as m

HERE = Path(__file__).resolve().parent
OUT = HERE / "pilot"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    records = []
    for seed in range(900, 904):
        for task in m.TASKS:
            for mode in ("soft_only", "st_second_half"):
                network, record = m.train(task, seed, mode)
                name = f"{task}-{seed}-{mode}.pt"
                torch.save(network.state_dict(), OUT / name)
                record["checkpoint"] = name
                record["checkpoint_sha256"] = sha(OUT / name)
                records.append(record)
                (OUT / "progress.json").write_text(json.dumps(records, indent=2))
                print(task, seed, mode, record["hard_test"], record["hard_full"], record["live_gates"], flush=True)
    aggregate = {}
    for mode in ("soft_only", "st_second_half"):
        group = [row for row in records if row["mode"] == mode]
        aggregate[mode] = {
            "hard_test_mean": float(np.mean([row["hard_test"]["accuracy"] for row in group])),
            "hard_full_exact_runs": int(sum(row["hard_full"]["accuracy"] == 1 for row in group)),
            "soft_test_mean": float(np.mean([row["soft_test"]["accuracy"] for row in group])),
            "live_gates_mean": float(np.mean([row["live_gates"] for row in group])),
        }
    st = aggregate["st_second_half"]
    soft = aggregate["soft_only"]
    selected = "st_second_half" if st["hard_test_mean"] - soft["hard_test_mean"] >= .02 or st["hard_full_exact_runs"] > soft["hard_full_exact_runs"] else "soft_only"
    viable = aggregate[selected]["hard_test_mean"] >= .90
    result = {
        "records": records,
        "aggregate": aggregate,
        "selected": selected,
        "viable": viable,
        "elapsed_seconds": time.monotonic() - started,
        "sources": {path.name: sha(path) for path in (HERE / "model.py", Path(__file__), HERE / "PILOT-PROTOCOL.md")},
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"aggregate": aggregate, "selected": selected, "viable": viable, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
