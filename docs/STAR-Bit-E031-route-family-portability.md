# E031：固定Functionの経路選択Task Familyへの移植性

実行日：2026-09-21。E026で採用した固定Functionを再調整せず、新規8 seed × 事前定義5 task（経路選択3、数値2）× 4条件の160探索で評価した。対照は移植なし、一段伝播barrier、同一費用のrandom Functionである。

## 結果

| family / task | no transfer | admitted | barrier | random matched |
| --- | ---: | ---: | ---: | ---: |
| route / route_dual_mux_xnor | 1/8 | 2/8 | 1/8 | 2/8 |
| route / route_cross_mux_xor | 1/8 | 0/8 | 1/8 | 1/8 |
| route / route_cascade_mux | 0/8 | 0/8 | 0/8 | 0/8 |
| numeric / numeric_popcount_bit1 | 0/8 | 0/8 | 0/8 | 0/8 |
| numeric / numeric_unsigned_sum_ge6 | 4/8 | 0/8 | 6/8 | 3/8 |

family内のexact task数をseedごとに対応比較した。

| paired count/seed | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| --- | ---: | ---: | --- | ---: | ---: |
| route: admitted−random_matched | -0.1250 | 0.1250 | [-0.3750, 0.0000] | -0.354 | 1.0000 |
| route: admitted−no_transfer | +0.0000 | 0.2857 | [-0.3750, 0.3750] | 0.000 | 1.0000 |
| route: admitted−one_hop_barrier | +0.0000 | 0.2857 | [-0.3750, 0.3750] | 0.000 | 1.0000 |
| numeric: admitted−random_matched | -0.3750 | 0.2679 | [-0.7500, -0.1250] | -0.725 | 0.2500 |
| numeric: admitted−no_transfer | -0.5000 | 0.2857 | [-0.8750, -0.1250] | -0.935 | 0.1250 |
| numeric: admitted−one_hop_barrier | -0.7500 | 0.2143 | [-1.0000, -0.3750] | -1.620 | 0.0312 |

## 判定

事前登録したroute-family portability基準は満たさなかった。
Primaryのadmitted−randomはrouteで-0.1250 task/seed、95% CI [-0.3750, 0.0000]、exact p=1.0000だった。2/8のadmitted成功はいずれもFunctionを最終式で直接使ったが、admitted-onlyかつ直接使用のwitnessが得られたroute taskは1/3だった。
routeとnumericのadmitted−random成功率効果の差は+0.1458、95% CI [-0.0625, 0.3333]。これはtask種別差の記述値であり、8 seedの探索的比較である。

固定Functionはroute全体でrandom対照を上回らず、数値側では成功を減らした。`numeric_unsigned_sum_ge6`ではadmitted 0/8に対しbarrier 6/8、no-transfer 4/8、random 3/8だった。admitted対barrierのexact sign-flip pは0.0312だが、このtask内3比較のHolm補正後は0.0938である。したがって、Functionを深く伝播させることが探索を妨げ、一段だけの摂動がbeamを有利に変える可能性はあるものの、確証とは扱わない。

taskごとの3比較をHolm補正した。

- route_dual_mux_xnor: admitted vs random_matched、left-only 1、right-only 1、p=1.0000、Holm p=1.0000。
- route_dual_mux_xnor: admitted vs no_transfer、left-only 2、right-only 1、p=1.0000、Holm p=1.0000。
- route_dual_mux_xnor: admitted vs one_hop_barrier、left-only 2、right-only 1、p=1.0000、Holm p=1.0000。
- route_cross_mux_xor: admitted vs random_matched、left-only 0、right-only 1、p=1.0000、Holm p=1.0000。
- route_cross_mux_xor: admitted vs no_transfer、left-only 0、right-only 1、p=1.0000、Holm p=1.0000。
- route_cross_mux_xor: admitted vs one_hop_barrier、left-only 0、right-only 1、p=1.0000、Holm p=1.0000。
- route_cascade_mux: admitted vs random_matched、left-only 0、right-only 0、p=1.0000、Holm p=1.0000。
- route_cascade_mux: admitted vs no_transfer、left-only 0、right-only 0、p=1.0000、Holm p=1.0000。
- route_cascade_mux: admitted vs one_hop_barrier、left-only 0、right-only 0、p=1.0000、Holm p=1.0000。
- numeric_popcount_bit1: admitted vs random_matched、left-only 0、right-only 0、p=1.0000、Holm p=1.0000。
- numeric_popcount_bit1: admitted vs no_transfer、left-only 0、right-only 0、p=1.0000、Holm p=1.0000。
- numeric_popcount_bit1: admitted vs one_hop_barrier、left-only 0、right-only 0、p=1.0000、Holm p=1.0000。
- numeric_unsigned_sum_ge6: admitted vs random_matched、left-only 0、right-only 3、p=0.2500、Holm p=0.2500。
- numeric_unsigned_sum_ge6: admitted vs no_transfer、left-only 0、right-only 4、p=0.1250、Holm p=0.2500。
- numeric_unsigned_sum_ge6: admitted vs one_hop_barrier、left-only 0、right-only 6、p=0.0312、Holm p=0.0938。

全22 exact式を64入力で再評価し、160 record、40個のrandom Function、同一費用、task分離、source hashを監査した。3 task中2つは全条件でほぼ床、`route_cascade_mux`は全条件0/8だったため、route-family全般への外挿には限界がある。結果はBoolean beam探索に限り、学習抽象化、圧縮、実gate削減、速度、State、Router効果を示さない。

## Roadmap

- [Done] 同一dual-mux XORへの反復を止め、事前定義した5つの新規targetで固定Function、barrier、random同費用対照を比較した。
- [Done] 精密数値と経路選択を分け、平均、不偏分散、効果量、bootstrap CI、exact検定、Holm補正を保存した。
- [Next] taskを結果で選ばず生成する小規模grammarを凍結し、pilotで床・天井を測った後、別seedで中難度層を独立確認する。Function条件が探索容量を1 slot増やす交絡を消すため、no-transferにも同数のinert slotを入れる。
- [Later] State付きFunctionと形成・分解を導入し、十分な再現性が得られてから負荷分散付きRouterと固定ランダム経路へ統合する。

English: The frozen learned Function did not beat equal-cost random Functions across three preregistered routing tasks (−0.125 exact tasks/seed; 95% CI −0.375 to 0.000). It also suppressed the solvable numeric-sum target, while the one-hop barrier reached 6/8. The latter contrast was nominally significant but not significant after within-task Holm correction, so it is a hypothesis about harmful deep propagation rather than confirmation.

简体中文：冻结的已学习函数在三个预注册路由任务上没有优于同成本随机函数（每个种子少0.125个精确任务；95% CI为−0.375至0.000）。它还抑制了可求解的数值求和任务，而一跳屏障达到6/8。该差异未经校正时显著，但在任务内Holm校正后不显著，因此目前只能作为“深层传播可能有害”的假设。

[事前计划](../results/E031-route-family-portability/PROTOCOL.md) / [生数据](../results/E031-route-family-portability/run/results.json) / [Task manifest](../results/E031-route-family-portability/run/task_manifest.json) / [冻结Library](../results/E031-route-family-portability/run/frozen_libraries.json) / [审计摘要](../results/E031-route-family-portability/run/audit_summary.json)
