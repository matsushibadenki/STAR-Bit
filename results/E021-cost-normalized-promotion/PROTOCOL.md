# E021 pilot preregistration: cost-normalized promotion and retirement

Date: 2026-09-13, after E020 and before E021 outcomes.

E020 offspring credit discovered comparator without a hand-selected function family, but credited 626–652 parent signatures per seed and increased runtime about eightfold. Test whether task reuse and structural cost can concentrate the archive without losing target reachability.

Use new seeds 1280–1283, beam 256, eight rounds, all unordered beam pairs, all 16 two-input LUTs, and maximum tree cost 16. Compare:

- `raw_promotion`: reproduce E020 credit and selection on the new seeds.
- `normalized_retired`: rank credit by distinct target tasks, credit per composition partner, primitive count, routing bits, and depth; reserve at most 64 promoted slots instead of 96; retire credit entries with no new credit for more than two rounds.

Both conditions receive the same 16-candidate target-error quota per task and identical candidate-generation budget. No named function family, intermediate label, target circuit, or test-selected configuration is used.

Primary outcomes are exact targets per seed and final promoted functions. Secondary outcomes are per-task success, runtime, total credited signatures, retired signatures, primitive/routing/depth of exact solutions, unique signatures, and equivalent merges. Report paired mean differences, unbiased variance, bootstrap 95% CI, Cohen dz where defined, and exact sign-flip p as pilot diagnostics.

Treat normalization as viable if its exact-target mean is no more than 0.25 below raw promotion, final promoted count is at least 30% lower, and mean runtime is lower. Do not proceed to a 16-seed Module transfer experiment unless carry is also found in at least one seed; otherwise add State as a separate preregistered factor.

