# E017 bit-vector SAT probe preregistration

Date: 2026-09-12, after the row-wise SAT encoding returned UNKNOWN for comparator and carry at 5–10 LUTs, and before bit-vector outcomes.

Repeat the same complete-table circuit synthesis with an equivalent 64-bit truth-vector encoding. One Z3 bit-vector represents a gate over all 64 input rows, replacing 64 per-row Boolean variables. Keep arbitrary two-input four-entry LUTs, ordered source indices, final-gate output, gate counts 1–10, 10-second timeout, random seed 0, and one thread unchanged.

Verify every SAT witness with the independent Python bit-parallel evaluator. Compare status and elapsed time descriptively with the row-wise probe; this is an encoding diagnostic, not a model result. If all tasks are SAT, fix the maximum first-SAT capacity for the main learned-circuit abstraction experiment. If comparator or carry remains unresolved, stop E017 before Module-mining claims.

