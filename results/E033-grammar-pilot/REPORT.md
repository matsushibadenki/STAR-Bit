# E033：事前固定した数値・経路選択Grammarの難度Pilot

実行日：2026-09-22。6つの新規truth tableを結果を見る前にgrammarで固定し、8 seed × 6 task × 4条件の192探索を実施した。これはtask難度とFunction作用方向を調べるpilotであり、新しい確認用seedをまだ使っていない。

| family / task | no transfer | admitted | one-hop barrier | random matched | no-transfer難度 |
| --- | ---: | ---: | ---: | ---: | --- |
| numeric / numeric_sum_ge4 | 8/8 | 8/8 | 8/8 | 8/8 | ceiling |
| numeric / numeric_sum_ge5 | 0/8 | 0/8 | 0/8 | 0/8 | floor |
| numeric / numeric_sum_ge7 | 0/8 | 0/8 | 4/8 | 2/8 | floor |
| route / route_cross_and | 8/8 | 7/8 | 7/8 | 8/8 | ceiling |
| route / route_cross_or | 8/8 | 5/8 | 5/8 | 7/8 | ceiling |
| route / route_cross_xnor | 1/8 | 0/8 | 1/8 | 1/8 | floor |

family平均exact率をseedごとに対応比較した。

| paired success rate | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric:one_hop_barrier-minus-admitted | +0.1667 | 0.0317 | [0.0417, 0.2917] | 0.935 | 0.1250 | 0.8750 |
| numeric:one_hop_barrier-minus-no_transfer | +0.1667 | 0.0317 | [0.0417, 0.2917] | 0.935 | 0.1250 | 0.8750 |
| numeric:admitted-minus-random_matched | -0.0833 | 0.0238 | [-0.2083, 0.0000] | -0.540 | 0.5000 | 1.0000 |
| numeric:admitted-minus-no_transfer | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| route:one_hop_barrier-minus-admitted | +0.0417 | 0.0456 | [-0.0833, 0.1667] | 0.195 | 1.0000 | 1.0000 |
| route:one_hop_barrier-minus-no_transfer | -0.1667 | 0.0317 | [-0.2917, -0.0417] | -0.935 | 0.1250 | 0.8750 |
| route:admitted-minus-random_matched | -0.1667 | 0.0635 | [-0.3333, -0.0417] | -0.661 | 0.2500 | 1.0000 |
| route:admitted-minus-no_transfer | -0.2083 | 0.0298 | [-0.2917, -0.0833] | -1.208 | 0.0625 | 0.5000 |

## Pilot判定と独立確認の境界

事前のfamily interactionは+0.1250（不偏分散0.0615、95% CI [-0.0417, 0.2917]、dz=0.504、exact p=0.3750）。pilot signal gateは満たさなかった。
この値は生成grammarの探索結果であり、新規task・seedへ一般化したという確認ではない。

事前に固定した難度規則はno-transfer exact 0–1/8=floor、2–6/8=middle、7–8/8=ceiling。次の独立確認候補は**no-transferだけ**で決まり、Function条件の結果では選ばない。

- middle: なし。
- familyごとのmiddle数: numeric 0/3, route 0/3。

task別のbest error平均／不偏分散、成功解tree cost平均（primitive / routing bits / depth）、Function使用成功数、時間平均秒：

- numeric_sum_ge4 / no_transfer: error 0.000 / 0.000; cost 9.00 / 62.00 / 4.00; Function使用 0; 時間 2.027秒。
- numeric_sum_ge4 / admitted: error 0.000 / 0.000; cost 9.00 / 62.00 / 4.00; Function使用 0; 時間 2.221秒。
- numeric_sum_ge4 / one_hop_barrier: error 0.000 / 0.000; cost 9.00 / 62.00 / 4.00; Function使用 0; 時間 1.958秒。
- numeric_sum_ge4 / random_matched: error 0.000 / 0.000; cost 9.00 / 62.00 / 4.00; Function使用 0; 時間 2.218秒。
- numeric_sum_ge5 / no_transfer: error 1.875 / 0.125; cost NA; Function使用 0; 時間 4.577秒。
- numeric_sum_ge5 / admitted: error 1.250 / 0.214; cost NA; Function使用 0; 時間 4.862秒。
- numeric_sum_ge5 / one_hop_barrier: error 1.875 / 0.125; cost NA; Function使用 0; 時間 4.272秒。
- numeric_sum_ge5 / random_matched: error 1.625 / 0.268; cost NA; Function使用 0; 時間 4.794秒。
- numeric_sum_ge7 / no_transfer: error 2.000 / 0.000; cost NA; Function使用 0; 時間 4.906秒。
- numeric_sum_ge7 / admitted: error 2.000 / 0.000; cost NA; Function使用 0; 時間 5.200秒。
- numeric_sum_ge7 / one_hop_barrier: error 1.000 / 1.143; cost 15.00 / 110.00 / 6.00; Function使用 0; 時間 4.242秒。
- numeric_sum_ge7 / random_matched: error 1.500 / 0.857; cost 15.00 / 110.00 / 6.00; Function使用 0; 時間 4.648秒。
- route_cross_and / no_transfer: error 0.000 / 0.000; cost 11.75 / 82.50 / 4.50; Function使用 0; 時間 2.600秒。
- route_cross_and / admitted: error 0.125 / 0.125; cost 12.71 / 88.86 / 4.57; Function使用 0; 時間 3.053秒。
- route_cross_and / one_hop_barrier: error 0.250 / 0.500; cost 13.00 / 90.86 / 4.57; Function使用 0; 時間 2.645秒。
- route_cross_and / random_matched: error 0.000 / 0.000; cost 12.25 / 86.25 / 4.75; Function使用 1; 時間 2.791秒。
- route_cross_or / no_transfer: error 0.000 / 0.000; cost 11.25 / 79.75 / 4.12; Function使用 0; 時間 2.130秒。
- route_cross_or / admitted: error 0.625 / 0.839; cost 12.20 / 85.60 / 4.40; Function使用 0; 時間 3.582秒。
- route_cross_or / one_hop_barrier: error 0.750 / 1.071; cost 11.80 / 82.80 / 4.20; Function使用 0; 時間 3.280秒。
- route_cross_or / random_matched: error 0.125 / 0.125; cost 11.29 / 80.00 / 4.14; Function使用 0; 時間 3.121秒。
- route_cross_xnor / no_transfer: error 3.500 / 2.000; cost 7.00 / 46.00 / 4.00; Function使用 0; 時間 5.301秒。
- route_cross_xnor / admitted: error 4.625 / 0.839; cost NA; Function使用 0; 時間 5.763秒。
- route_cross_xnor / one_hop_barrier: error 3.500 / 2.000; cost 7.00 / 46.00 / 4.00; Function使用 0; 時間 4.574秒。
- route_cross_xnor / random_matched: error 3.750 / 2.786; cost 13.00 / 94.00 / 6.00; Function使用 1; 時間 4.872秒。

全96 exact式を64入力で再評価し、192 unique record、progress一致、48 random Functionの費用・signature、task分離、strict JSON、source hashを監査した。Functionの使用を回路記述量・実gate数・実測速度の削減と混同しない。Router、State、Ternary ExpertはE033では評価していない。

## Roadmap

- [Done] 結果に依存しない数値／経路選択grammarを凍結し、両familyの難度とFunction伝播差を同じ探索予算でpilot評価した。
- [Done] 次の対象はno-transferのみで層別化し、pilotと独立確認を分離した。
- [Next] middleが両familyにあれば凍結した全middle taskを新規seedで評価する。どちらかにmiddleがなければ、別grammarを事前定義してpilotをやり直す。
- [Later] 費用付きFunction admission、State付き形成・分解、その後にstep 0負荷分散付きRouterと固定random経路、同一run内→別seed Expert交換へ進む。

English: Six targets were frozen from a numeric/route grammar before outcomes. This pilot reports all successes and failures, and selects any future mid-difficulty targets only from no-transfer success counts. Its family interaction is exploratory; no independent-seed confirmation is claimed.

简体中文：在观察结果前，用数值与路由规则固定了六个目标。本预实验报告所有成功与失败，并仅依据无迁移条件的成功数选择后续中等难度目标。任务族交互作用仍属探索性结果，尚未进行独立种子确认。

English / 简体中文: No task met the preregistered middle band (0/6). The next grammar must be fixed before another pilot. / 六个任务都未进入预注册的中等难度区间（0/6）；下一套任务规则必须在新预实验前固定。
[事前计划](PROTOCOL.md) / [生数据](run/results.json) / [难度分层](run/difficulty_strata.json) / [冻结Manifest](run/frozen_manifest.json) / [审计摘要](run/audit_summary.json)
