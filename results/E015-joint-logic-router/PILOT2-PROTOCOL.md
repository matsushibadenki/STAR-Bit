# E015 pilot 2 amendment

Written after pilot 1 and before pilot 2 outcomes.

Pilot 1 showed finite gradients and exact oracle execution, but randomly initialized selection modules achieved only 0.0625–0.125 hard test exact after 400 steps. The second and final tuning pilot initializes only gate-table logits toward the verified E014 full-adder/mux semantics at magnitude 1.5 plus the original seeded noise. Schedule logits and learned Router remain random. All gate logits remain trainable.

Use the same non-confirmatory seeds 40–43, 800 steps, learning rate 0.03, temperature 1→0.1, balance weight 0.1 from update 0, and discretization weight 0.01. Conditions remain balanced fixed hash and learned balanced Router. If mean hard test exact is not higher than pilot 1 for selection, the main experiment will retain random initialization and report the limitation rather than continue tuning. If higher, use module-prior initialization unchanged in the main seeds and describe the estimand as routing under a verified module prior.

