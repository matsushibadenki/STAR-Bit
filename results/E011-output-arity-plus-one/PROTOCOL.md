# E011 preregistration: add one output connection

Date: 2026-09-12, written before inspecting E011 outcomes.

## Milestone question

E010 showed that replacing one output connection never repaired the 108 output-bit cases classified UNSAT in E009, and every target-relevant raw input was already present somewhere in the output ancestry. Test whether adding one direct raw-input connection, while retaining all existing connections and gates, is enough to recover exact representability.

## Cases and conditions

Use all and only the 108 E009-UNSAT cases from seeds 500–515. Each case has two paired conditions:

- `random_add`: add one uniformly selected raw input that is not already a direct input of the affected output gate.
- `influence_add`: add an available raw input with maximum Boolean influence on the target bit. Influence is the fraction of the 64 inputs for which toggling that input changes the target. Ties use a fixed case-specific RNG.

Both conditions add exactly one connection to the output gate and retain every original wire. Thus gate2 becomes LUT3 and lut4 becomes LUT5 for the affected output only. Gate count and hidden wiring remain fixed. The influence condition reads the complete target truth table and is an oracle structural diagnostic, not a learnable connection rule.

## Solver and stopping

Run 108 cases × 2 conditions = 216 all-input Boolean synthesis queries. Use Z3 5.1.0.0, solver seed 0, one thread, proof enabled, and 2,000 ms per query. Stop the whole experiment at 900 seconds and retain progress. Save every formula, result, source/checkpoint hash, and SAT witness. Independently evaluate each witness on all 64 inputs. Treat UNSAT as a solver verdict without independent proof validation; UNKNOWN is unresolved.

## Endpoints and inference

Primary endpoint: fixed-budget SAT discovery, with UNKNOWN counted as not discovered. Report per-seed mean, unbiased variance, paired difference, and 10,000-resample seed-bootstrap 95% CI using seed 1011.

Run five planned two-sided exact McNemar tests: global and each task × original architecture stratum. Holm-correct all five. Case-level tests are diagnostic because output bits within a wiring are dependent; seed bootstrap is the preferred uncertainty summary. Report precision-numeric and route-selection tasks separately.

Secondary endpoints include SAT/UNSAT/UNKNOWN counts per bit, Boolean influences, same-source selections, truth-table bits added (4→8 for gate2 output; 16→32 for lut4 output), and recovery per added truth-table bit. Do not compare solver speed or interpret target-informed synthesis as training or generalization.

## Adaptive continuation fixed in advance

If neither condition recovers at least 10% of cases, the next experiment will add two raw-input connections while retaining original wires. Otherwise, use the better one-add structure in a new multiple-seed learning experiment with an equal-arity random fixed-source control. No success-driven seed additions are allowed.

