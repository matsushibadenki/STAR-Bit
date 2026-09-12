# E017 pilot 3 preregistration: discrete refinement from examples

Date: 2026-09-12, after pilot 2 passed mean accuracy but failed the all-task exact-circuit condition, and before pilot-3 outcomes.

The continuous DLGN now learns exact parity and mux circuits but stalls on comparator and carry. Test whether a discrete circuit search can refine its hardened wiring and LUTs. This is a separate circuit-identification stage: use the complete 64-row Boolean truth table because the next Module analysis requires an exact source circuit. Do not claim predictive generalization from this stage; retain pilot-2 48/16 results as the generalization diagnostic.

Use the selected `diverse_tables` hard circuits from pilot-2 seeds 920–923 as warm starts. Compare against a random hard circuit with the same five-layer, 16-gate-per-layer architecture and the same per-run proposal budget. Search mutates source wires, LUT truth tables, and the final output selection. Fitness is full-domain Hamming error, followed by live-gate count only after exact accuracy. It reads only input/output rows and the starting circuit; it receives no task name, named primitive, intermediate target, module, or hand-written circuit.

Use 100,000 proposals per task/seed/condition, deterministic search seed, at most four gene mutations per proposal, and accept strict improvements plus 10% of neutral proposals. Stop early at exact accuracy. Conditions are `dlgn_start` and `random_start`; 4 tasks × 4 seeds × 2 conditions = 32 searches.

Report exact success count by task, proposals to exact, initial/final error, and live-gate count. Proceed to a new-seed E017 main only if `dlgn_start` reaches exact accuracy in at least 3/4 seeds for every task. The random control measures warm-start value; it is not a Router control.

