# E017 SAT synthesis probe

Date: 2026-09-12, after the three optimization pilots and before SAT outcomes.

Use SAT as a diagnostic oracle over complete Boolean input/output tables. A circuit has six inputs and a sequence of arbitrary two-input four-entry LUTs; each LUT may read inputs or preceding LUTs, and the final LUT is the output. No named gate, intermediate target, task-specific circuit, or Module Library is supplied.

For each of parity, comparator, mux, and carry, try gate counts 1 through 10 in order with a 10-second timeout per count, Z3 random seed 0, one thread. Verify every SAT witness with an independent bit-parallel evaluator on all 64 rows. Record SAT/UNSAT/UNKNOWN separately. This probe asks whether compact exact circuits can be synthesized from examples; it is not a DLGN training result and will not be used for significance claims.

If all tasks receive verified witnesses, use their largest first-SAT gate count as the fixed capacity for a new-seed hybrid experiment. Otherwise retain the optimization boundary and do not mine incomplete circuits.

