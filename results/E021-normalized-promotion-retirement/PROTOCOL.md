# E021 pilot preregistration: normalized promotion and retirement

Date: 2026-09-13, before outcomes.

E020 improved Function-space search, but credited 626–652 parent signatures per seed and retained 182–194 promoted Functions in the final beam. E021 tests whether this archive can be made smaller and faster without losing the discovered exact circuits.

Compare `raw_promotion` and `normalized_retirement` on new seeds 1280–1283. Both use beam 256, eight rounds, maximum tree cost 16, every unordered beam pair, all 16 two-input LUTs, and the same four target signatures. Neither condition receives function-family names, intermediate labels, or a target circuit.

`raw_promotion` reproduces E020. `normalized_retirement` credits only the best-cost representative of each unique child signature, divides improvement and support novelty by child description cost, decays credit by 0.5 per round, and retains a promoted parent only when it received credit in the last two rounds or helped at least two target tasks. Promotion is capped at 80 beam entries; diversity is capped at 64. Target-error quotas are unchanged.

Primary outcome: paired exact targets per seed. Secondary outcomes: task success, runtime, generated signatures, equivalent merges, credited signatures, eligible archive size, promoted beam entries, retirement count, circuit cost, and discovery round. The normalized policy passes this pilot when its mean exact-target count is no more than 0.25 below raw promotion and its final eligible archive is at most half the raw credited archive. Runtime reduction is measured but is not a pass condition. With four seeds, confidence intervals and the exact paired sign-flip test are descriptive rather than confirmatory.
