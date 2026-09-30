# E044：凍結Suiteの容量Dose–Response校正

実行日：2026-09-30。E042の8 taskを固定し、新規6 seed、要求beam幅64/96/128/160/192、Libraryなしで240探索した。探索CPU時間274.9秒。初回poolは164 signatureが上限だったため、要求幅192条件のround 1/2実効幅は164（他は要求値どおり）だった。

| family | 要求幅（round 2実効幅） | exact/24 | seed別exact平均 / 不偏分散 | seed別best error平均 / 不偏分散 | 生成signature平均 | 秒平均 | 成功式 primitive / routing / depth平均 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| numeric | 64 (64) | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 24020.2 | 0.325 | 6.50 / 43.33 / 3.42 |
| numeric | 96 (96) | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 40870.8 | 0.647 | 5.25 / 34.67 / 3.08 |
| numeric | 128 (128) | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 57010.8 | 1.071 | 5.00 / 33.00 / 3.00 |
| numeric | 160 (160) | 12/24 | 0.5000 / 0.0000 | 1.000 / 0.000 | 82689.7 | 1.657 | 5.00 / 33.00 / 3.00 |
| numeric | 192 (164) | 12/24 | 0.5000 / 0.0000 | 1.000 / 0.000 | 117434.4 | 2.179 | 5.00 / 33.00 / 3.00 |
| route | 64 (64) | 8/24 | 0.3333 / 0.0167 | 4.833 / 0.267 | 25594.4 | 0.348 | 4.75 / 31.00 / 3.00 |
| route | 96 (96) | 10/24 | 0.4167 / 0.0167 | 4.458 / 0.410 | 42521.5 | 0.698 | 4.50 / 29.80 / 3.00 |
| route | 128 (128) | 12/24 | 0.5000 / 0.0000 | 3.625 / 0.119 | 63292.8 | 1.102 | 4.50 / 30.00 / 3.00 |
| route | 160 (160) | 13/24 | 0.5417 / 0.0104 | 2.167 / 0.667 | 93587.6 | 1.639 | 4.69 / 31.38 / 3.08 |
| route | 192 (164) | 21/24 | 0.8750 / 0.0187 | 0.500 / 0.600 | 133778.1 | 1.789 | 5.90 / 39.43 / 3.43 |

## 事前主指標：要求幅192−64 exact差

全8 task平均差 +0.2708、不偏分散 0.0151、bootstrap 95% CI [0.1875, 0.3542]、dz 2.204、exact p=0.0312。容量感度基準は達成。 要求幅192のround 1/2実効幅は164であり、結果の解釈に残す。
局所要求幅160−96 exact差は+0.0625、95% CI [0.0000, 0.1458]、p=0.5000。

| family | exact差 | 95% CI | dz | exact p | Holm p | error改善 | 95% CI | Holm p |
| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: |
| numeric | +0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 | +0.250 | [0.250, 0.250] | 0.0625 |
| route | +0.5417 | [0.3750, 0.7083] | 2.204 | 0.0312 | 0.0625 | +4.333 | [3.333, 5.083] | 0.0625 |

## Task別の幅192−64差

| task | exact差 | 95% CI | Holm p | error改善 | 95% CI | Holm p |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| numeric_2bit_sum_ge3 | +0.0000 | [0.0000, 0.0000] | 1.0000 | +0.000 | [0.000, 0.000] | 1.0000 |
| numeric_4bit_weighted_ge4 | +0.0000 | [0.0000, 0.0000] | 1.0000 | +0.000 | [0.000, 0.000] | 1.0000 |
| numeric_rotated_weight_ge6 | +0.0000 | [0.0000, 0.0000] | 1.0000 | +1.000 | [1.000, 1.000] | 0.2500 |
| numeric_5bit_weighted_ge5 | +0.0000 | [0.0000, 0.0000] | 1.0000 | +0.000 | [0.000, 0.000] | 1.0000 |
| route_mux_xor_bit | +0.0000 | [0.0000, 0.0000] | 1.0000 | +0.000 | [0.000, 0.000] | 1.0000 |
| route_mux_conditional_flip | +0.6667 | [0.3333, 1.0000] | 0.8750 | +2.667 | [1.333, 4.000] | 0.6250 |
| route_rotated_cross_xnor | +0.8333 | [0.5000, 1.0000] | 0.5000 | +7.333 | [4.333, 9.333] | 0.3750 |
| route_nested_mux | +0.6667 | [0.3333, 1.0000] | 0.8750 | +7.333 | [6.667, 8.000] | 0.2500 |

全体の容量感度gateは達成したが、作用はtask種別で大きく異なった。numeric exactは全要求幅で12/24のまま、要求幅160から`numeric_rotated_weight_ge6`のerrorだけ3→2へ改善した。route exactは要求幅64の8/24から要求幅192の21/24へ増え、hard routingにも到達した。family 2比較のHolm補正後pはexact・errorとも0.0625であり、6 seedではfamily別有意差の主張には届かない。

E043の±1候補介入が不変だった一方、32〜64枠規模の要求容量差ではrouteが反応した。次は要求幅192の初回pool上限を事前に164へ明示して独立seedでrouteの164対128とnumericのerror改善を確認する。その後、同じ候補数のlearned cohort、composition不能inert cohort、同費用random cohortを追加・置換して、容量と意味を分離する。

全124 exact式を64入力で再評価した。240 record、240 round 1/2実効幅、192 prefix照合、Library使用0、strict JSON、progress、source hashを監査。物理ゲート数・推論速度・Router学習は未測定。

## Roadmap

- [Done] frozen suiteでsemantic-freeな5段階容量responseを測定し、全体exact感度gateを達成した。
- [Next] 独立seedでroute実効幅164対128とnumeric best-error応答を固定確認し、候補cohort数を凍結する。
- [Later] learned／inert／同費用random cohortのadd/replaceを比較し、成立後にState形成・分解とLogic/Ternary Routerへ進む。

English: E044 passed the preregistered overall capacity-sensitivity gate: requested width 192 improved exact by 0.271 over width 64. The round-one/two realized width was capped at 164. The response was concentrated in routing (8/24 to 21/24); numeric stayed at 12/24 exact, with only one hard task improving from error 3 to 2. Family-level Holm-adjusted p-values were 0.0625.

简体中文：E044达到预注册的整体容量敏感性标准：请求宽度192相对64的exact提高0.271，但前两轮的实际宽度上限为164。变化集中在路由任务（8/24升至21/24）；数值任务维持12/24，仅一个困难任务的误差从3降至2。任务族层面的Holm校正p值为0.0625。

[事前計画](../results/E044-capacity-dose-response/PROTOCOL.md) / [生データ](../results/E044-capacity-dose-response/run/results.json) / [凍結設定](../results/E044-capacity-dose-response/run/frozen_manifest.json) / [監査](../results/E044-capacity-dose-response/run/audit_summary.json)
