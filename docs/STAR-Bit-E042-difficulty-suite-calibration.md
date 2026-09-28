# E042：凍結Difficulty Suiteの独立Seed校正

実行日：2026-09-28。E040–E041で凍結したeasy/hard各2 taskをfamilyごとに混ぜ、Functionなし・新規12 seed・実効beam幅128・4 roundで評価した。単一truth tableではなく4 task suiteの平均を主要評価単位とする。

| family | suite exact平均 / 不偏分散 | bootstrap 95% CI | seed別成功task数 | suite best error平均 / 不偏分散 |
| --- | ---: | --- | --- | ---: |
| numeric | 0.5000 / 0.0000 | [0.5000, 0.5000] | [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2] | 1.229 / 0.005 |
| route | 0.5208 / 0.0052 | [0.5000, 0.5625] | [2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2] | 3.354 / 0.835 |

suite feasibility gateは達成した。
numeric−route exact比率差は-0.0208、不偏分散0.0052、95% CI [-0.0625, 0.0000]、dz -0.289、exact p=1.0000。

| task | exact/12 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | 秒平均 | 成功式 primitive / routing / depth平均 |
| --- | ---: | ---: | ---: | ---: | ---: |
| numeric_2bit_sum_ge3 | 12/12 | 1.0000 / 0.0000 | 0.000 / 0.000 | 0.534 | 5.00 / 34.00 / 3.00 |
| numeric_4bit_weighted_ge4 | 12/12 | 1.0000 / 0.0000 | 0.000 / 0.000 | 0.522 | 5.00 / 32.00 / 3.00 |
| numeric_rotated_weight_ge6 | 0/12 | 0.0000 / 0.0000 | 2.917 / 0.083 | 1.560 | NA |
| numeric_5bit_weighted_ge5 | 0/12 | 0.0000 / 0.0000 | 2.000 / 0.000 | 1.462 | NA |
| route_mux_xor_bit | 12/12 | 1.0000 / 0.0000 | 0.000 / 0.000 | 0.523 | 4.00 / 26.00 / 3.00 |
| route_mux_conditional_flip | 12/12 | 1.0000 / 0.0000 | 0.000 / 0.000 | 0.524 | 5.00 / 34.00 / 3.00 |
| route_rotated_cross_xnor | 1/12 | 0.0833 / 0.0833 | 7.667 / 7.152 | 1.569 | 8.00 / 54.00 / 4.00 |
| route_nested_mux | 0/12 | 0.0000 / 0.0000 | 5.750 / 4.205 | 1.549 | NA |

## Round 4−2感度（Holm補正）

| task | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric_2bit_sum_ge3 | +1.0000 | 0.0000 | [1.0000, 1.0000] | NA | 0.000488 | 0.003906 |
| numeric_4bit_weighted_ge4 | +1.0000 | 0.0000 | [1.0000, 1.0000] | NA | 0.000488 | 0.003906 |
| numeric_rotated_weight_ge6 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.000000 | 1.000000 |
| numeric_5bit_weighted_ge5 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.000000 | 1.000000 |
| route_mux_xor_bit | +1.0000 | 0.0000 | [1.0000, 1.0000] | NA | 0.000488 | 0.003906 |
| route_mux_conditional_flip | +1.0000 | 0.0000 | [1.0000, 1.0000] | NA | 0.000488 | 0.003906 |
| route_rotated_cross_xnor | +0.0833 | 0.0833 | [0.0000, 0.2500] | 0.289 | 1.000000 | 1.000000 |
| route_nested_mux | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.000000 | 1.000000 |

numericは全seedで2/4、routeは11 seedで2/4・1 seedで3/4となり、両familyに床と天井の回避、かつ介入で動けるheadroomを確保した。これはFunction効果ではなく、評価設計のfeasibility達成である。全suiteを凍結し、個別taskを選び直さず独立介入へ進む。

全49 exact式を64入力で再評価した。96 record、24 suite row、progress、strict JSON、source hash、suite membership、Library不使用、実効幅128を監査。探索CPU時間合計98.9秒。

## Roadmap

- [Done] family別のeasy/hard混合suiteを独立12 seedで校正し、事前feasibility gateを満たした。
- [Next] 全8 taskを固定し、衝突なしlearned/inert/random Moduleのreplace/addを新規seedで比較する。
- [Later] Function固有の再利用が確認された後にState形成・分解、Logic/Ternary Router、総物理費用へ進む。

English: E042 validated a frozen mixed-difficulty evaluation unit on 12 independent seeds. Numeric averaged 0.50 exact and routing 0.521, with every seed retaining both solved and unsolved tasks. This establishes evaluation headroom, not a Function effect.

简体中文：E042在12个独立种子上验证了冻结的混合难度评估单元。数值任务平均exact为0.50，路由任务为0.521，每个种子都同时包含成功和未成功任务。这只证明评估空间可用，并非函数效应。

[事前計画](../results/E042-difficulty-suite-calibration/PROTOCOL.md) / [生データ](../results/E042-difficulty-suite-calibration/run/results.json) / [Suite行](../results/E042-difficulty-suite-calibration/run/suite_rows.json) / [凍結判断](../results/E042-difficulty-suite-calibration/run/suite_selection.json) / [監査](../results/E042-difficulty-suite-calibration/run/audit_summary.json)
