# E033 preregistration: prospective task-grammar difficulty pilot

Date: 2026-09-22, before E033 outcomes. E032 confirmed that unrestricted propagation of E026's fixed Function harmed one numeric target relative to a one-hop barrier, but did not establish a benefit over no transfer. The one available route comparator moved in the opposite direction. Test whether this task-type interaction survives a prospectively generated set of targets; do not use E033 outcomes to refit the Function or claim independent confirmation.

Freeze a six-target grammar before running:

- `numeric_sum_ge4`, `numeric_sum_ge5`, `numeric_sum_ge7`: interpret bits 0–2 and 3–5 as two unsigned three-bit integers and test whether their sum reaches threshold 4, 5, or 7.
- `route_cross_and`, `route_cross_or`, `route_cross_xnor`: let `left = b2 if b0 else b4` and `right = b5 if b3 else b1`; combine them with AND, OR, or XNOR.

These thresholds and operators are fixed as written, not chosen by pilot results. Verify all six truth signatures are distinct from one another and from E019, E024 and E031 task signatures. Freeze E026's one admitted Function. Use fresh seeds 1480–1487 and four conditions for every seed/target: `no_transfer`, unrestricted `admitted`, `one_hop_barrier`, and one structurally/cost-matched `random_matched` Function drawn deterministically before any E033 search. The barrier follows E030: Function-derived expressions can make round-1 children but cannot serve as parents in later rounds; clean equivalent representatives may compose. Each search uses E026's signature-stable selector, beam 128, six rounds, tree cost ≤16, one CPU thread. Stop after exactly 192 searches regardless of outcome. Save each row immediately.

Primary exploratory metric is the paired seed-level family interaction: mean exact rate per numeric task for `barrier - admitted` minus the same rate per route task. Report mean, unbiased variance, Cohen dz, 20,000-resample paired bootstrap 95% CI, and two-sided exact sign-flip p. Treat interaction ≥+0.20 with CI lower bound above zero as a pilot signal only, not confirmation. Secondary contrasts within each family are `barrier - admitted`, `barrier - no_transfer`, `admitted - random_matched`, and `admitted - no_transfer`; report paired statistics and Holm-adjusted p-values across the eight family contrasts. Report all per-task counts, best errors, runtime, solution cost, and Function use including negative results.

For a later independent-seed experiment, classify task difficulty using **only** E033 `no_transfer` exact counts: 0–1/8=floor, 2–6/8=middle, 7–8/8=ceiling. Freeze every middle task before any new-seed run; do not select from admitted/barrier/random outcomes. If either family has no middle task, do not invent a substitute within E033. Pilot and future confirmation must remain separate.

Audit all exact expressions over all 64 inputs; verify task signatures, random library cost and uniqueness, 192 unique records, strict JSON, source hashes, and progress log. This measures Boolean beam-search behavior, not learned Router performance, autonomous concepts, description compression, physical gates, or acceleration.
