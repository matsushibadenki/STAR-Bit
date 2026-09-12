# E010 preregistration: one-wire output repair

Date: 2026-09-12, before outcome inspection.

## Question and hypothesis

E009 found 108 individually UNSAT output-bit cases among the fixed E007 wirings. Test whether changing exactly one input connection of the affected output gate can recover exact representability without adding gates.

The primary hypothesis is that an oracle dependency-guided source has a higher fixed-budget SAT discovery rate than a random raw-input source. “Oracle” means that the complete target truth table is used only to identify which raw inputs affect that output bit. This is a structural diagnosis, not a learnable routing result.

## Cases and conditions

- Include every E009 `unsat` case: seed 500–515, numeric/selection, gate2/lut4, output bits as observed. Do not include SAT or UNKNOWN cases and do not add seeds after seeing results.
- Reuse the original fixed wiring. Select one output-gate port deterministically from a case-specific fixed RNG seed and use the same port in both conditions.
- `random_raw`: replace that port with a uniformly selected raw input among 0–5, excluding the existing source when it is raw.
- `dependency_raw`: replace the same port with a target-relevant raw input absent from the output's ancestral cone. If none is missing, use a relevant raw input different from the existing source and record the fallback.
- Exactly one wire changes in both conditions. Gate counts, arity, and all other connections stay fixed. Each condition receives an independent free truth-table synthesis; no learned E007 table is retained.

Relevant inputs are computed by exhaustive Boolean sensitivity: toggling the input changes the target bit for at least one paired input. This label-derived choice is an oracle diagnostic.

## Solver and stopping

For 108 cases × 2 conditions = 216 solver queries, constrain the chosen bit over all 64 inputs. Z3 5.1.0.0, random seed 0, one thread, proof generation enabled, timeout 1,000 ms per query, total wall limit 900 seconds. Save progress after every query. SAT witnesses must reproduce all 64 targets in a separate NumPy evaluator. UNSAT is a solver verdict without independent proof checking. UNKNOWN remains unresolved.

## Metrics and statistics

Primary metric: SAT discovery among the 108 E009-UNSAT cases, with UNKNOWN counted as not discovered under the fixed budget. Report the paired difference `dependency_raw - random_raw`, per-seed mean, unbiased variance, and seed bootstrap 95% CI (10,000 resamples, seed 1010).

Use two-sided exact McNemar tests for the global comparison and four task × architecture comparisons. Apply Holm correction to these five planned tests. Strata with no discordant pairs have p=1. The observations share wirings and output cones, so case-level p-values are diagnostic; the seed bootstrap is the preferred uncertainty summary. Do not test solver speed or compare E009/E010 success rates because selection and solver behavior differ.

Secondary results: source choice, relevant/missing inputs, per-output outcomes, cases recovered by either condition, and whether both selected the same replacement. Report task type explicitly: numeric precision versus route selection.

## Interpretation and next step

A SAT result proves existence only for that repaired wiring and target bit. It does not show that gradient learning finds it or that it generalizes. If dependency-guided repair helps, the next training experiment should learn or propose sparse connections without access to test labels, with a random-rewire control. If one wire is inadequate, test a preregistered two-wire repair before increasing gate count.

