# E015 confirmatory protocol: joint Logic Expert and Router optimization

Date: 2026-09-12, after two tuning pilots and before main-seed outcomes.

## Pilot decision

Pilot 1 used random gate tables and achieved mean hard test exact 0.7422/0.0938 for learned routing on numeric/selection. The prespecified pilot-2 module prior improved these to 0.9609/0.9844. The main experiment therefore uses the unchanged pilot-2 configuration and estimates routing effects under a verified Logic PE prior. Pilot seeds 40–43 are excluded.

## Models and conditions

Use seeds 700–715, two task families, and four stateful Logic Experts. Each Expert has trainable two-input LUT truth-table logits and trainable logits over the fixed E014 schedule library. Gate logits start at magnitude ±1.5 toward the verified full-adder or mux-stage tables plus identical seeded noise. Schedule logits and learned Router start random. All parameters remain trainable.

- `learned_balanced`: a linear softmax Router reads the immutable six input bits. From update 0, optimize task BCE + 0.1 × load-balance loss + 0.01 × normalized schedule entropy + 0.01 × gate-table softness. Load loss is `4 * sum(mean_route_probability^2) - 1` on the train batch.
- `fixed_hash`: the Router is a seed-fixed label-independent lookup from each six-bit input to one Expert. It assigns exactly 16 of all 64 inputs to each Expert. Expert gate and schedule parameters receive the same optimizer, initialization, data, and updates; Router weights are inert.

Each run uses a seed-fixed 32 train / 32 untouched test split, 800 full-batch Adam updates, learning rate 0.03, temperature linearly annealed 1→0.1, CPU one thread. Conditions share initial Expert tensors within task and seed. Stop after 16 seeds or 900 wall seconds; preserve progress if exceeded.

## Main endpoints

Primary: hard test exact-match difference learned-balanced minus fixed-hash, separately for precision-numeric and route-selection tasks. Report means, unbiased variances, paired differences, Cohen dz, seed bootstrap 95% CI (10,000 resamples, seed 1015), and two-sided exact sign-flip permutation p-values with Holm correction over two tasks.

Secondary: hard/soft train, test, and full exact/bit accuracy; hard and soft Expert utilization, utilization CV and entropy; initial/final balance loss; selected schedules; gate-table hardening; wall time. Do not select checkpoints by test score.

## Expert intervention sequence

After all training and without retraining, evaluate full and held-out test predictions in this fixed order for both soft and hard models:

1. self replacement of Expert 0; outputs must be unchanged.
2. same-run Expert 0/1 parameter swap with Router unchanged.
3. symmetry control: same swap plus learned-Router columns 0/1 or fixed-hash labels 0/1; outputs must be unchanged.
4. cross-seed replacement of Expert 0 using the next seed cyclically within the same task and routing condition.
5. zero-function Expert-0 and prior-initialized but untrained Expert-0 controls.

Cross-seed Expert numbers are not functionally aligned. Donor selection and order use no test score. Report performance change from unmodified baseline descriptively with seed bootstrap CI. Because cyclic donors are reused, do not claim independent-sample significance for swaps.

## Interpretation

The learned-versus-fixed comparison isolates input routing conditional on the shared module prior and joint Expert optimization. It does not demonstrate discovery of full-adder/mux semantics from scratch, large-scale MoE behavior, or length extrapolation. Source balancing in E014 was structural; E015 explicitly applies differentiable load loss from the first update.

If learned-balanced improves both task families after Holm correction and swap invariance checks pass, declare Logic Routing Milestone 2 complete. Otherwise report the boundary and return to router regularization or module discovery without adding seeds.

