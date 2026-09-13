# E020 pilot preregistration: learned offspring promotion

Date: 2026-09-13, before outcomes.

E019 showed that exact function-signature merging removes syntactic duplicates, while a hand-selected affine archive recovers parity but is not autonomous Module Genesis. Replace the affine list with evidence collected during search: promote a parent signature when its generated children (a) improve a target relative to both parents, or (b) expand dependency support while remaining nonconstant. Store target-task reuse, improvement credit, novel-child credit, parent partners, cost, and depth.

Compare `target_greedy` and `offspring_promotion` with seeds 1260–1263, beam 256, eight rounds, all unordered beam pairs, all 16 LUTs, and maximum tree cost 16. Both receive equal target-error quotas and identical generation budgets. Promotion receives no named function family, intermediate labels, gate names, or target circuit. The four final truth signatures remain visible as objectives.

Primary pilot outcome: exact targets per seed and all-four-target success. Secondary outcomes: per-task success, discovery round and costs, promoted signatures, reuse-task count, generated unique signatures, equivalent merges, and runtime. Proceed to a 16-seed Module experiment only if promotion finds all four targets in at least 3/4 seeds and exceeds greedy total exact targets. Otherwise keep the negative result and do not call the archive autonomous abstraction.

