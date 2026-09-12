# E019 pilot preregistration: function-space Module Genesis

Date: 2026-09-12, after E018 showed that reducing constraints alone did not solve comparator/carry.

Replace syntax-level circuit mutation with function-space search. Represent every intermediate node by its exact 64-row truth signature. Merge candidates with identical signatures immediately and retain the lower `(primitive LUT count, routing bits, depth)` representation. This tests the proposed transition from gate-space search to function-space search.

Search the four E017 tasks jointly from six input signatures using arbitrary two-input LUT composition. Compare:

- `target_greedy`: retain candidates using current Hamming error to each target plus cost.
- `composition_pareto`: retain the same target-error quotas, plus candidates with low one-composition lookahead error, globally nondominated `(four task errors, primitive count, routing bits, depth)`, and seed-random functional diversity.

Both conditions use beam 128, seven composition rounds, the same complete unordered pair expansion within the beam, all 16 LUTs per pair, maximum tree cost 14, and seeds 1200–1203 only for deterministic tie/diversity ordering. Search reads truth tables but no task names, named gates, intermediate targets, modules, or hand-written circuits. The four output signatures are targets; intermediate supervision is absent.

Primary feasibility outcomes are exact targets found per seed and whether all four targets are present. Also report first discovery round, primitive/routing/depth cost, unique generated signatures, equivalent-function merges, retained frontier size, and overlap of intermediate signatures used by exact target expressions. This is a method-selection pilot; do not use significance tests as confirmatory evidence.

Proceed to a 16-seed main Module experiment if `composition_pareto` finds all four targets in at least 3/4 seeds and exceeds `target_greedy` in total exact targets. Otherwise retain the boundary and revise composition scoring or representation without mining incomplete targets.
