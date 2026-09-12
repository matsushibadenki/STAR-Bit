"""Run the preregistered E017 forced-depth pilot."""
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch

import model_v2 as m

HERE = Path(__file__).resolve().parent
OUT = HERE / "pilot2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    selected_records = []
    restart_records = []
    for seed in range(920, 924):
        for task in m.TASKS:
            for initialization in ("random_tables", "diverse_tables"):
                candidates = []
                for restart in range(4):
                    network, row = m.one_run(task, seed, initialization, restart)
                    candidates.append((network, row))
                    restart_records.append({key: value for key, value in row.items() if key not in {"spec", "curve"}})
                network, chosen = max(candidates, key=lambda pair: (pair[1]["hard_train"]["accuracy"], -pair[1]["final_train_bce"], -pair[1]["restart"]))
                name = f"{task}-{seed}-{initialization}.pt"
                torch.save(network.state_dict(), OUT / name)
                chosen["checkpoint"] = name
                chosen["checkpoint_sha256"] = sha(OUT / name)
                chosen["restart_hard_train"] = [pair[1]["hard_train"]["accuracy"] for pair in candidates]
                selected_records.append(chosen)
                (OUT / "progress.json").write_text(json.dumps(selected_records, indent=2))
                print(task, seed, initialization, "restart", chosen["restart"], chosen["hard_test"], chosen["hard_full"], chosen["live_gates"], flush=True)
    aggregate = {}
    for initialization in ("random_tables", "diverse_tables"):
        group = [row for row in selected_records if row["initialization"] == initialization]
        aggregate[initialization] = {
            "hard_test_mean": float(np.mean([row["hard_test"]["accuracy"] for row in group])),
            "hard_full_exact_runs": int(sum(row["hard_full"]["accuracy"] == 1 for row in group)),
            "full_exact_by_task": {task: int(sum(row["hard_full"]["accuracy"] == 1 for row in group if row["task"] == task)) for task in m.TASKS},
            "live_gates_mean": float(np.mean([row["live_gates"] for row in group])),
        }
    diverse, random = aggregate["diverse_tables"], aggregate["random_tables"]
    selected = "diverse_tables" if diverse["hard_test_mean"] - random["hard_test_mean"] >= .02 or diverse["hard_full_exact_runs"] > random["hard_full_exact_runs"] else "random_tables"
    chosen = aggregate[selected]
    viable = chosen["hard_test_mean"] >= .90 and all(value >= 1 for value in chosen["full_exact_by_task"].values())
    result = {
        "selected_records": selected_records,
        "restart_records": restart_records,
        "aggregate": aggregate,
        "selected": selected,
        "viable": viable,
        "elapsed_seconds": time.monotonic() - started,
        "sources": {path.name: sha(path) for path in (HERE / "model.py", HERE / "model_v2.py", Path(__file__), HERE / "PILOT2-PROTOCOL.md")},
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"aggregate": aggregate, "selected": selected, "viable": viable, "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
