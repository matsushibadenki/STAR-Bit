# E026 pilot preregistration: counterfactual Module admission

Date: 2026-09-15, after E025 and before E026 outcomes.

E025 showed that local child improvement marks every imported Function as useful and that even unprotected admission changes the search trajectory. Test admission by the actual counterfactual quantity: the difference between short searches run with and without one Function under signature-stable deterministic tie-breaking.

Build the candidate pool from all internal E021 normalized exact circuits, excluding raw inputs and the four original outputs. For every candidate and each of the four E024 probe tasks, run a three-round beam-64 search with that candidate and a paired search without it. Shared signatures receive identical deterministic priorities derived from `(search seed, round, signature)`, so adding a Function cannot shift the random order of existing Functions. Admit at most eight candidates that improve at least two probe tasks and have positive total error reduction, ranked by net probe gain per structural cost. Evaluation targets are the unchanged E024 held-out tasks and selection never reads them.

Use new evaluation seeds 1360–1363, beam 128, six rounds, tree cost at most 16, normalized offspring credit, deterministic beam completion, and no protected Library slots. Compare:

- `no_transfer`: raw inputs only.
- `legacy_all8`: the eight E024 utility-diverse Functions, admitted without protection.
- `counterfactual`: only Functions passing paired probe rollout admission.
- `random_matched`: randomized expression trees matching the admitted count and structural costs, with a separated control stream.

Primary outcome: paired exact evaluation tasks per seed, counterfactual minus legacy admission. Secondary comparisons are counterfactual versus no transfer and random matched. Report admission count, probe deltas, best-error trajectories, transferred-Function use, runtime, mean, unbiased variance, bootstrap 95% CI, Cohen dz, exact sign-flip tests, and Holm-adjusted task-level McNemar tests.

Call counterfactual admission a viable mitigation if it improves at least +0.5 exact task per seed over legacy, is no more than 0.25 below no transfer, and admits no candidate that has non-positive preregistered probe net gain. Advance transfer claims only if it also exceeds random matched by at least +0.5. Otherwise retain deterministic tie-breaking but stop importing this source pool and move to State-aware multi-step Function generation.
