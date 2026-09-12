# E019 pilot 2 preregistration: algebraic scaffold retention

Date: 2026-09-12, after one-step composition lookahead found only mux and before pilot-2 outcomes.

The first function-space pilot merged equivalent signatures but discarded intermediates whose value appeared more than one composition later. Test an explicit task-independent scaffold: retain any discovered affine Boolean signature over the six inputs. The 128 affine signatures are generated algebraically as XOR subsets plus optional complement, but the search receives no task-specific intermediate, named gate, or target circuit. This is an inductive bias, not spontaneous discovery, and will be reported as such.

Compare `target_greedy` with `affine_scaffold` using beam 256, seven complete unordered-pair composition rounds, all 16 two-input LUTs, maximum tree cost 14, and seeds 1220–1223. Both conditions reserve equal target-error quotas. The scaffold condition then reserves discovered affine functions and fills remaining capacity using support-mask/output-balance diversity; the greedy condition fills by current target error and cost. Candidate-generation budget is identical within seed after the beam is full.

Report exact tasks, first round, primitive/routing/depth cost, signatures generated, equivalent merges, and which exact solutions reuse affine intermediates. Proceed to a 16-seed main only if the scaffold finds all four targets in at least 3/4 seeds and strictly exceeds greedy total exact targets. Otherwise keep Module Genesis unresolved and test learned archive promotion rather than adding more hand-selected function families.

