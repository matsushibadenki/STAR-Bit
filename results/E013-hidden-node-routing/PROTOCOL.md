# E013 preregistration: can another hidden node carry the target?

Date: 2026-09-12, before E013 outcomes.

## Question

E012 failed its 25% recovery milestone after increasing only output arity. Determine whether the target bit can be synthesized at another existing hidden node, separating a fixed output-routing bottleneck from the inability of any single hidden node to materialize the target.

Use all 108 output-bit cases classified UNSAT in E009, seeds 500–515. Hidden wiring and gate count remain fixed; all two-input hidden truth tables remain freely synthesizable.

- `layer1_select`: one case-wide one-hot selector may choose any of the 32 second hidden-layer nodes (bank indices 38–69). The chosen node must equal the target for all 64 inputs.
- `all_hidden_select`: the selector may choose any of all 64 hidden nodes (bank indices 6–69).

This is an oracle output-routing feasibility test. The selector is shared across samples, so it chooses one structural connection rather than one node per input. The original output gate is bypassed as an identity connection. E009 UNSAT is the fixed-parent control; E008 direct LUT6 is the positive capacity control.

## Execution and verification

Run 216 queries with Z3 5.1.0.0, seed 0, proof enabled, one thread, timeout 2,000 ms/query, and total wall limit 900 seconds. Save formulas, statuses, selected-node witnesses, gate tables, source/checkpoint hashes, and progress. Independently re-evaluate every SAT witness on all 64 inputs. UNSAT is a solver verdict without independent proof checking. UNKNOWN remains unresolved.

## Endpoints

Primary endpoints are fixed-budget SAT discovery for each scope and the paired gain of all-hidden over layer1-only, with UNKNOWN counted as not discovered. Report per-seed mean, unbiased variance, and 10,000-resample seed-bootstrap 95% CI (seed 1013). Run five planned two-sided exact McNemar tests—global and four task × original-architecture strata—and Holm-correct them.

Report the selected layer/node, per-bit counts, and numeric-precision versus route-selection results. A layer1 SAT means one existing second-layer node can carry the complete target, so fixed output parent choice is a sufficient obstruction for that case. An all-hidden UNSAT means no individual existing hidden node can carry the target under this fixed wiring, subject to solver validity; it does not exclude combining several nodes or modifying hidden wiring.

## Milestone rule

If at least 25% of cases are SAT in either scope and both task families have SAT cases, carry the witnessed hidden-node routing pattern into a multiple-seed learning experiment with fixed-random routing as control. Otherwise, diagnose or modify hidden wiring before attempting learned routing. No seed extension or outcome-selected reruns.

