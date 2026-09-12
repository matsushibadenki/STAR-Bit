# E016 preregistration: independent-hash numeric replication

Date: 2026-09-12, after detecting the E015 numeric split/hash RNG coupling and before E016 outcomes.

Replicate only the E015 numeric primary comparison with new seeds 800–815. Keep the verified Logic PE prior, 4 Experts, 800 Adam updates, learning rate 0.03, temperature 1→0.1, discretization coefficient 0.01, and learned-Router balance coefficient 0.1 from update 0.

The 32/32 split uses RNG seed `model_seed`. The fixed label-independent hash uses the separate RNG seed `model_seed + 40000`; it is generated before training and assigns exactly 16 of all 64 immutable input values to each Expert. Assert that no main seed has an exactly 8/8/8/8 fixed-hash train allocation across all 16 seeds as a batch-level diagnostic; individual seeds may be balanced by chance. Learned and fixed conditions share initial Expert tensors within seed.

Primary metric: hard test exact learned-balanced minus fixed-hash. Report means, unbiased variances, paired mean difference, Cohen dz, 10,000-seed bootstrap 95% CI (seed 1016), and a two-sided exact sign-flip permutation p-value. This is one prespecified replication comparison, so no multiplicity correction is needed. Report hard/soft bit accuracy, complete seeds, train/full metrics, balance loss, and utilization.

Stop after 16 seeds or 900 seconds. Do not add seeds or tune settings. Save checkpoints, splits, hash maps, curves, hashes, and raw metrics. If the paired p≤0.05 and CI excludes zero in the same direction as E015, treat the numeric routing result as independently confirmed within this module-prior setup. Otherwise retain only the E015 selection result as the Milestone-2 confirmatory result.

