# E015 pilot protocol

Date: 2026-09-12, before pilot outcomes.

Purpose: verify differentiable execution, hardening, and runtime before fixing the confirmatory multi-seed experiment. Use seeds 40–43, both tasks, learned-balanced and fixed-balanced-hash routing, 400 updates. These seeds cannot enter the main experiment. Tune only step count, temperature floor, learning rate, and discretization penalty from pilot diagnostics; preserve all pilot outputs and document changes.

Four Logic Experts each learn their reusable two-input LUT truth tables and a soft distribution over the same E014 schedule library. The learned router is a linear softmax over immutable six-bit input and receives load-balancing loss from update 0. The fixed control maps each of all 64 immutable inputs to Experts through a seeded lookup containing exactly 16 assignments per Expert. It never reads labels or split membership.

Pilot checks: oracle configuration evaluates exactly, autograd gradients are finite, all 32 train/32 test splits are disjoint, fixed full-domain utilization is uniform, symmetry-preserving Expert+Router swaps retain outputs, and training finishes within 900 seconds. Pilot estimates are not confirmatory results.

