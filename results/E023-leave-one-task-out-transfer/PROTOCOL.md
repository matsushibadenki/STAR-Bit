# E023 preregistration: leave-one-task-out Function transfer

Date: 2026-09-13, after E022 and before E023 outcomes.

E022 showed cross-seed transfer, but its Library could contain a partial circuit learned from the same target task. E023 removes that route. For each held-out task, build a different Library using exact E021 circuits from the other three tasks only. Exclude all raw inputs and all four final target signatures. Select two Functions from each primitive-cost band 1, 2–3, 4–7, and 8–15, ranked by reuse across source `(seed, task)` solutions and then structural cost. The resulting eight Functions are fixed during target search.

Use held-out tasks parity, comparator, mux, and carry; new search seeds 1320–1335; beam 128; six rounds; expanded-tree cost at most 16; and a single-target version of E021 normalized offspring credit with retirement after two stale rounds. Compare:

- `no_transfer`: raw inputs only; secondary compute reference.
- `random_cost_matched`: randomize every input and LUT in each source expression while preserving expression shape, primitive count, routing bits, and depth.
- `random_error_matched`: draw 2,048 cost-matched random variants per Library slot and retain the unique non-target variant with closest full-truth-table error to the held-out target. This deliberately target-informed oracle control matches immediate usefulness more strongly.
- `learned_cross_task`: Functions learned only from the other three tasks.

Random controls use streams separated from the search seed. All three eight-Function Libraries occupy eight protected beam slots. Learned and control Libraries have identical structural-cost vectors. `random_error_matched` is the primary control; `random_cost_matched` and `no_transfer` are secondary.

Primary outcome: per-search-seed count of exact held-out tasks, learned minus error-matched random. Report mean, unbiased variance, bootstrap 95% CI, Cohen dz, and exact sign-flip p. Secondary outcomes: per-task exact paired McNemar tests with Holm correction, discovery round, runtime, error-matching residual, and use of transferred signatures.

Call task-crossing transfer promising only if the mean paired gain over error-matched random is at least +0.25 task per seed, its bootstrap interval excludes zero, comparator or carry has at least four learned-only successes, and every learned-only success uses a transferred signature. This remains a synthetic four-task pilot and does not establish transfer to a new task family.
