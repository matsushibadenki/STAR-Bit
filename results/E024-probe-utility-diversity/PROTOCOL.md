# E024 pilot preregistration: probe utility and Function diversity

Date: 2026-09-14, before E024 outcomes.

E023 showed that source reuse/frequency and target error do not identify cross-task Modules. Test a causal proxy: retain a Function when composing it once with a raw input improves unseen probe targets beyond every one-LUT composition of raw inputs. Combine this probe utility with signature diversity so the Library does not collapse to similar truth tables.

The source pool is every internal Function from E021 normalized exact circuits, excluding six raw inputs and the four original final targets. Module selection uses four fixed probe tasks only: majority (`sum(bits)>=3`), exactly-two, unsigned 3-bit less-than, and a fixed mixed Boolean expression. Evaluation uses four different tasks fixed before selection: threshold-two, threshold-four, unsigned 3-bit equality, and XOR of two 2-way muxes. No evaluation target is read during selection.

Select eight Functions, two from each primitive-cost band 1, 2–3, 4–7, and 8–15. Compare:

- `no_transfer`: raw inputs only.
- `frequency_cost`: E023-style source occurrence and structural-cost ranking.
- `probe_utility`: normalized one-step probe improvement and probe-task breadth.
- `probe_utility_diverse`: the same utility plus greedy minimum Hamming-distance diversity within each cost band.
- `random_matched`: randomized inputs/LUTs with the same expression shapes and structural costs as `probe_utility_diverse`.

Use new search seeds 1340–1343, beam 128, six rounds, expanded-tree cost at most 16, single-target normalized offspring credit, two-round retirement, and protected eight-Function Library slots. This is a four-seed screening pilot. The primary comparison is utility-diverse minus random-matched exact evaluation tasks per seed; report mean, unbiased variance, bootstrap 95% CI, Cohen dz, and exact sign-flip p. Report task success, transferred-Function use, Library pairwise Hamming distance, and secondary comparisons.

Advance this selector to 16 seeds only if its mean exact-task gain over random is at least +0.5, at least two evaluation tasks improve in two or more paired seeds, and every claimed learned-only success uses a transferred Function. A negative result redirects work toward multi-step or state-aware utility rather than tuning these tasks or adding seeds.
