# E035 preregistration: baseline-only weighted-sum grammar calibration

Date: 2026-09-22, before E035 search outcomes. E034 found no mid-difficulty numeric target by varying the round cap. Keep the search budget at six rounds, beam 128, tree cost at most 16, and an empty Function library. Change only the numeric truth-table grammar: six weighted-sum threshold tasks, with bit weights in input-index order:

| task | weights | threshold |
| --- | --- | ---: |
| `numeric_symmetric_ge5` | `(1,2,3,1,2,3)` | 5 |
| `numeric_symmetric_ge6` | `(1,2,3,1,2,3)` | 6 |
| `numeric_symmetric_ge7` | `(1,2,3,1,2,3)` | 7 |
| `numeric_asymmetric_ge5` | `(1,2,4,1,2,3)` | 5 |
| `numeric_asymmetric_ge6` | `(1,2,4,1,2,3)` | 6 |
| `numeric_asymmetric_ge7` | `(1,2,4,1,2,3)` | 7 |

All six signatures were checked for uniqueness and noncollision with E031/E033 task signatures before search. The signed 2026-09-22 hypothesis is feasibility rather than a directed performance claim: changing weights and threshold at fixed compute may yield at least one numeric task with neither floor nor ceiling baseline success. Run fresh seeds 1500–1505 for every task (36 searches), even if early outcomes are all zero or exact. Use E026's signature-stable search, the same 64-entry input truth table, and no transfer. The E034 routing candidate `route_cross_and@4` remains frozen and is not rerun or reselected here.

Primary criterion: baseline exact count 2–4/6 is middle difficulty; 0–1/6 floor; 5–6/6 ceiling. Freeze **every** middle numeric task from this rule. If none qualify, record that feasibility failed and do not run Function conditions. If some qualify, later confirmation may compare them with the frozen E034 route candidate using new independent seeds; E035 itself does not claim Function efficacy. Never use earlier or future Function outcomes to select among these six numeric targets.

For each task report exact mean/unbiased variance, best-error mean/unbiased variance, elapsed time, generated unique signatures, and successful-expression primitive/routing/depth cost. Secondary paired contrasts are asymmetric-minus-symmetric baseline exact rate at each threshold, with seed as the unit: mean, unbiased variance, Cohen dz, 20,000-resample bootstrap 95% CI, exact two-sided sign-flip p, and Holm correction over three thresholds. These contrasts describe grammar sensitivity, not learned abstraction. Also report the six target positive-class counts.

Re-evaluate every exact expression over all 64 inputs; verify 36 unique records, progress-log equality, strict JSON, source hashes, frozen targets, and absence of Function library use. Persist every record immediately. Stop after all 36 searches, or after 15 minutes of total CPU work with an incomplete progress log preserved; do not add seeds based on success rates. No external compute or publication.
