# E012 preregistration: add two output connections

Date: 2026-09-12, written after E011 completion and before E012 outcomes.

E011 recovered fewer than the preregistered 10% of E009-UNSAT output-bit cases after adding one output connection. Following its continuation rule, add two distinct direct raw-input connections while retaining every original connection and gate.

Use all 108 E009-UNSAT cases, seeds 500–515, and two paired conditions. `random_add2` samples two available raw inputs without replacement. `influence_add2` selects the two available inputs with greatest Boolean influence on the target bit; fixed case-specific RNG breaks ties. Available inputs exclude raw inputs already directly connected to that output. Both conditions add exactly two connections. Original gate2 outputs become LUT4 (4→16 truth bits); original lut4 outputs become LUT6 (16→64 truth bits).

This is an oracle exact-synthesis diagnosis because influence and the solver use the complete target truth table. It is not learned routing, generalization, or module discovery.

Run 216 queries with Z3 5.1.0.0, seed 0, proof enabled, one thread, 3,000 ms per query, and a 900-second wall limit. Save per-query progress, formulas, statuses, source/checkpoint hashes, and SAT witnesses. Independently evaluate every witness on all 64 inputs. UNSAT is a solver verdict without independent proof validation; UNKNOWN remains unresolved.

Primary metric is fixed-budget SAT discovery, counting UNKNOWN as not discovered. Report seed mean, unbiased variance, paired difference, and 10,000-resample seed-bootstrap 95% CI (seed 1012). Use two-sided exact McNemar tests globally and in four task × original-architecture strata, with Holm correction across five comparisons. Prefer seed CI because bits within a wiring are dependent. Report precision-numeric and route-selection tasks separately.

The milestone decision is fixed: if either condition recovers at least 25% of all 108 cases and at least one case in both task families, carry the better fixed structure into a multiple-seed learning experiment. Otherwise, stop increasing output arity and diagnose a hidden-layer bottleneck. No seed extension or successful-case filtering.

