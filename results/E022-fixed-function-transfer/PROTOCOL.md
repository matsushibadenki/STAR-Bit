# E022 preregistration: fixed learned-Function transfer

Date: 2026-09-13, after E021 and before E022 outcomes.

E021 found carry once and therefore met the preregistered gate for a 16-seed transfer test. Test whether intermediate truth-signature Functions learned in source runs improve search on held-out search seeds, beyond merely adding fixed Functions of the same structural cost.

Build the source Library only from exact circuits found by E021 `normalized_retired` runs. Remove all six raw inputs and all four task-output signatures. Divide remaining internal Functions into four preregistered primitive-cost bands (1, 2–3, 4–7, 8–15) and retain four per band, ranked by reuse across source `(seed, task)` solutions and then structural cost. This produces 16 Functions without naming an operation or inspecting E022 outcomes.

Run search seeds 1300–1315 with beam 256, six rounds, maximum expanded-tree cost 16 and the E021 normalized-credit/retirement rule. Compare:

- `no_transfer`: six inputs only; a compute-reference condition.
- `random_matched`: 16 fixed Functions made by randomizing every LUT and input in each learned Function's expression tree, preserving its primitive count, routing bits and depth. The control seed is deterministically separated from the search seed.
- `learned_transfer`: the fixed 16-Function source Library.

The learned and random Libraries occupy the same 16 protected beam slots and receive the same candidate-generation and selection procedure. They cannot be retired during the run. The no-transfer condition has a smaller first-round pool and is therefore secondary. Random Functions are label-independent and fixed before each search begins. The learned Library is fixed across evaluation seeds. Source seeds 1280–1283 and evaluation seeds 1300–1315 do not overlap.

Primary outcome: paired difference in exact targets between `learned_transfer` and `random_matched`. Report mean, unbiased variance, bootstrap 95% CI, Cohen dz and exact sign-flip p. Secondary outcomes: per-task exact rates with exact paired McNemar p and Holm correction, discovery round, runtime, and whether each solution contains a transferred signature. Report no-transfer descriptively.

Call transfer promising only if learned-minus-random exact-target mean is at least +0.5, its bootstrap interval excludes zero, at least one hard task (`comparator` or `carry`) improves in at least four paired seeds, and every claimed improvement uses a transferred signature. This tests source-informed cross-seed transfer; because source and target task identities overlap, it does not establish task-independent conceptual reuse.
