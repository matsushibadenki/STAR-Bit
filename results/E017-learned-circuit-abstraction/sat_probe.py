"""Run the preregistered E017 SAT capacity probe."""
import hashlib
import json
import time
from pathlib import Path

import sat_synth

HERE = Path(__file__).resolve().parent
OUT = HERE / "sat_probe"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    started = time.monotonic()
    records = []
    first_sat = {}
    for task in ("parity", "comparator", "mux", "carry"):
        for gates in range(1, 11):
            begin = time.monotonic()
            row, genome = sat_synth.solve(task, gates)
            row["seconds"] = time.monotonic() - begin
            records.append(row)
            (OUT / "progress.json").write_text(json.dumps(records, indent=2))
            print(task, gates, row["status"], row["seconds"], flush=True)
            if genome is not None:
                first_sat[task] = gates
                break
    result = {
        "records": records,
        "first_sat": first_sat,
        "all_tasks_sat": len(first_sat) == 4,
        "elapsed_seconds": time.monotonic() - started,
        "z3_version": sat_synth.z3.get_version_string(),
        "sources": {path.name: sha(path) for path in (Path(__file__), HERE / "sat_synth.py", HERE / "refine.py", HERE / "SAT-PROBE-PROTOCOL.md")},
    }
    (OUT / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({"first_sat": first_sat, "all_tasks_sat": result["all_tasks_sat"], "elapsed_seconds": result["elapsed_seconds"]}, indent=2))


if __name__ == "__main__":
    main()
