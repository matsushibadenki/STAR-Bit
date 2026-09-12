# E018 pilot preregistration: counterexample-guided exact circuit formation

Date: 2026-09-12, after E017 stopped before Module mining.

Test whether counterexample-guided inductive synthesis (CEGIS) resolves the all-row SAT timeout without increasing the circuit capacity. Use the same six-input tasks, sequential arbitrary two-input LUT representation, and complete truth-table verifier as E017. Fix capacity at 10 LUTs, the largest preregistered E017 probe size.

Compare two conditions for seeds 1100–1103:

- `all_rows`: constrain all 64 input/output rows in the first solve.
- `cegis`: begin with eight rows sampled by the seed, solve, evaluate the candidate on all 64 rows, and add the lowest-index failing row. Repeat for at most 40 counterexamples.

Each solver check has a 10-second timeout, one thread, and its model seed. Overall wall limit is 900 seconds. Conditions use identical capacity and exact verifier. Save SAT/UNSAT/UNKNOWN, solver calls, constrained rows, elapsed time, witness, and hashes. No task name, named gate, intermediate target, module, or hand-written topology enters the solver.

Primary feasibility outcome is verified full-domain exact success by task and condition. Report mean/unbiased variance across four seeds for success, solver calls, and time. This pilot selects a synthesis method; do not use its p-values as confirmatory evidence. Proceed to a 16-seed E018 abstraction main only if CEGIS succeeds in at least 3/4 seeds for every task and strictly exceeds all-row total successes. Otherwise redesign the representation.

The later main cost objective is reserved until exact formation passes: among exact circuits compare the Pareto vector `(primitive LUTs, library definition bits, call-site routing bits, state bits)`, rather than choosing a scalar lambda after observing results.

