# E017 pilot preregistration: learnable wiring for circuit abstraction

Date: 2026-09-12. This pilot chooses one training mode before the E017 main seeds are generated.

Train a small differentiable logic-gate network from input/output examples. Unlike E004, both gate truth tables and the two source wires of every gate are trainable. Use six Boolean inputs, three hidden layers of 12/12/8 two-input LUT gates, and four task families: six-bit parity, unsigned 3-bit comparison, a 2-to-1 mux with nuisance inputs, and the carry-out bit of 3-bit addition.

Use pilot seeds 900–903, a deterministic 48/16 train/test split per task and seed, 1,200 Adam updates, learning rate 0.03, temperature 1→0.15, table-softness coefficient 0.01, selector-entropy coefficient 0.005, and depth-cost coefficient 0.001. Compare two modes sharing initialization and splits:

- `soft_only`: continuous mixtures throughout training.
- `st_second_half`: continuous mixtures for 600 updates, then straight-through one-hot wires and binary LUT entries.

Primary pilot diagnostic is hard test accuracy and the number of tasks reaching hard full-domain exact accuracy. Also report soft accuracy, hardening gap, live hard-gate count, finite gradients, and hard-export equivalence on all 64 inputs. This is configuration selection, not confirmatory inference; pilot seeds will not enter the main experiment.

Choose `st_second_half` if it improves mean hard test accuracy by at least 0.02 or produces more full-domain exact task/seed runs. Otherwise choose `soft_only`. Do not tune per task. If neither mode reaches at least 0.90 mean hard test accuracy, stop and redesign rather than interpreting Module statistics.

