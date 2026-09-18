# E027 preregistration: independent counterfactual-admission confirmation

Date: 2026-09-16, before E027 outcomes.

E026 selected one Function from 45 using probe-only with/without rollouts and improved the four-seed evaluation from legacy 2/16 to 5/16. Independently test that mitigation on new seeds without changing the selected Function, tasks, search budget, or decision rule.

Freeze the E026 admitted Function and its expression before evaluation. Use seeds 1370–1385, the four E024 held-out tasks, beam 128, six rounds, tree cost at most 16, normalized offspring credit, signature-stable deterministic tie-breaking, and no protected Library slots. Compare `no_transfer`, `legacy_all8`, `counterfactual`, and per-seed structurally matched `random_matched`. Random control streams are separated from search seeds.

Primary outcome: paired exact tasks per seed, counterfactual minus legacy. Confirm mitigation only when the mean gain is at least +0.5, the bootstrap 95% interval excludes zero, and counterfactual is no more than 0.25 task per seed below no transfer. Secondary outcomes are counterfactual versus random matched, per-task exact McNemar tests with Holm correction, best truth-table error, Function use, runtime, and circuit cost.

Treat task-crossing transfer as independently supported only when counterfactual exceeds random by at least +0.25 task per seed with a bootstrap interval excluding zero, and at least one non-equality task has four learned-only paired successes whose solutions use the admitted Function. Stop after the fixed 16 seeds regardless of result. This experiment tests search reachability, not hardware speed, gate-count compression, or Router learning.
