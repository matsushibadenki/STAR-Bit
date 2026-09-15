# E025 pilot preregistration: usage-gated Module eviction

Date: 2026-09-15, before E025 outcomes.

E024 found that every fixed eight-Function Library condition underperformed no transfer. Test whether the harm comes from permanently protected beam slots rather than the initial admission of transferred Functions.

Use the unchanged E024 `probe_utility_diverse` Library and evaluation tasks, new search seeds 1350–1353, beam 128, six rounds, expanded-tree cost at most 16, normalized offspring credit, and two-round retirement. Compare:

- `no_transfer`: raw inputs only.
- `fixed_protected`: all eight learned Functions remain protected, reproducing the E024 policy on new seeds.
- `unprotected`: all eight learned Functions are admitted at round 0 but receive no protected slots.
- `usage_gated`: each learned Function receives a two-round probation. Protection is renewed only when that Function is a parent of a top-128 child that improves target error over both parents. Otherwise it is evicted from protected slots after round 2; it may survive through ordinary selection.
- `random_usage_gated`: structurally matched random Functions with the same usage rule and separated random stream.

The primary outcome is paired exact evaluation tasks per seed for `usage_gated` minus `fixed_protected`. Secondary comparisons are usage-gated learned versus no transfer, unprotected, and usage-gated random. Record mean active protected slots by round, eviction count, causal-use count, final-solution use, runtime, and exact task rates. Report mean, unbiased variance, bootstrap 95% CI, Cohen dz, exact sign-flip tests, and Holm-adjusted task-level McNemar tests.

Call eviction a viable mitigation only if usage-gated improves by at least +0.5 exact task per seed over fixed protection, its mean is no more than 0.25 task below no transfer, and at least half the Library is evicted by round 3 on average. This four-seed pilot does not justify a transfer claim. If the criterion fails, stop protecting imported Modules and test multi-step utility only as an admission proposal under ordinary beam competition.
