# E014 preregistration: temporal Logic PE and learned schedule selection

Date: 2026-09-12, before E014 outcomes.

## Milestone

E013 showed that fixed two-layer hidden wiring rarely contains a single node capable of the target. Implement the proposed gate-count/time trade: reusable stateful Logic PE modules execute a small program over multiple cycles. Test whether schedule selection on training examples beats a fixed random schedule while physical gate count stays fixed.

This is the first executable state/time-reuse prototype. It is not a neural MoE or language model.

## Programs and costs

- Numeric precision task: add two 3-bit integers. A five-gate full-adder PE (`XOR, XOR, AND, AND, OR`) is reused for 3 cycles with one carry-state bit. Temporal physical gates=5, active gate evaluations=15, latency=3 cycles. Spatial unrolling uses 15 physical gates, 15 evaluations, 1 macro-cycle.
- Route-selection task: rotate/select four data bits using two selector bits. A four-lane mux-stage PE uses 12 two-input gates (3 per lane) and is reused for 2 cycles with 4 state bits. Temporal physical gates=12, active evaluations=24, latency=2. Spatial unrolling uses 24 physical gates, 24 evaluations, 1 macro-cycle.

All metrics count primitive two-input Boolean gates. State storage, control bits, and route-description bits are reported separately. The physical-gate reduction is not an operation-count reduction.

## Routing conditions and balance

Use split seeds 600–615, independently permuting the complete 64-input truth table into 32 train and 32 test examples.

- `fixed_random`: select one schedule uniformly from the fixed candidate library without labels.
- `train_selected`: score every candidate on the train half, maximize train exact accuracy then bit accuracy, and use seeded random tie-breaking. Evaluate the chosen schedule on the untouched test half.
- `structured_oracle`: the known ripple order or barrel-shift schedule, as an exact positive control.

Numeric candidates are all 3!×3!=36 permutations of operand-bit presentation; each source bit is consumed once. Selection candidates are 2 selector orders × four cyclic choices for each of the two mux inputs at both cycles =512; cyclic permutations give every state lane equal source load. Thus routing load imbalance is exactly zero from the outset for every candidate and condition. There is no learned soft router or load-balancing auxiliary loss in this discrete experiment; the balance constraint is enforced by construction.

The only selected parameter is routing schedule. Gate functions, PE count, cycles, and candidate library are identical between fixed-random and train-selected conditions, isolating schedule-selection effect within this prototype.

## Metrics and statistics

Primary metric: test exact-match accuracy per input. Secondary: test bit accuracy, train accuracy, exact full-domain schedule recovery, physical gates, active evaluations, cycles, state bits, route-description bits, and source-load variance.

Report mean, unbiased variance, paired mean difference, standardized paired effect where defined, and seed-bootstrap 95% CI (10,000 resamples, seed 1014). Run paired two-sided exact sign/permutation tests for train-selected versus fixed-random in each of two tasks and Holm-correct both. Structured-oracle is a ceiling control and is not part of significance testing.

No seeds may be added. Candidate libraries, tie-breaking, splits, and stopping are fixed before results. CPU one thread, wall limit 900 seconds. Save candidate-output hashes, split indices, selected routes, raw per-seed metrics, source hash, and exhaustive equivalence checks.

## Interpretation and continuation

Training selection can overfit the 32 examples. A gain on the held-out half supports schedule selection for these finite Boolean tasks but does not establish neural learned routing or length generalization. If both tasks reach mean test exact ≥0.95, the next milestone is to learn gate tables jointly with route scores and include a fixed-random route plus balance loss. Otherwise, enlarge or regularize the schedule library without changing PE count.

