# E017 pilot 2 preregistration: forced-depth, task-agnostic LUT diversity

Date: 2026-09-12, after pilot 1 failed its 0.90 hard-test viability threshold and before pilot-2 outcomes.

Pilot 1 collapsed to zero- or one-gate paths. Replace its all-previous-node skip topology with five layers of 16 gates. Layer 0 reads the six inputs; every later layer reads the six inputs plus only the immediately preceding layer. The output must select a node in the final layer. This preserves learnable wiring while requiring a five-stage path; LUTs can learn identity functions when a stage is unnecessary.

Compare two task-independent initializations:

- `random_tables`: table logits sampled around zero.
- `diverse_tables`: the 16 possible two-input LUTs occur once per layer, with logit magnitude 0.5 in a seed-random permutation. No task label, target output, named gate, or hand-written circuit is used.

Use the same four tasks and pilot seeds 920–923, deterministic 48/16 splits, four restarts per task/seed/condition, 1,600 Adam updates, learning rate 0.02, temperature 1→0.2, and straight-through wires/tables in the second half. Choose one restart using hard train accuracy, then soft train BCE, then restart index; test labels are not used. Report both selected-run accuracy and all-restart success.

Regularization coefficients are table softness 0.002 and selector entropy 0.001. Remove pilot-1 depth cost because depth is now structural. Select `diverse_tables` if its hard-test mean is at least 0.02 higher or it yields more full-domain exact task/seed runs; otherwise select `random_tables`.

Proceed to the E017 main abstraction experiment only if the selected condition reaches at least 0.90 mean hard test accuracy and at least one full-domain exact run in each task. Otherwise retain the negative result and move to a discrete refinement or synthesis stage before Module analysis.

