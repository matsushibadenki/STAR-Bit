# E041：隣接Grammarの難度校正

実行日：2026-09-27。E040の天井／床から隣接方向へ複雑度を変えた精密数値3 task・経路選択3 taskを、Function条件なし・新規6 seedでbaseline-only探索した。各seed/taskは4 roundを一度だけ実行し、決定論的prefixから2/3/4 round予算を評価した。

| task | round | exact/6 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | 成功式 primitive / routing / depth平均 |
| --- | ---: | ---: | ---: | ---: | ---: |
| numeric_5bit_weighted_ge4 | 2 | 0/6 | 0.0000 / 0.0000 | 12.000 / 0.000 | NA |
| numeric_5bit_weighted_ge4 | 3 | 0/6 | 0.0000 / 0.0000 | 8.000 / 0.000 | NA |
| numeric_5bit_weighted_ge4 | 4 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 12.00 / 84.00 / 4.00 |
| numeric_5bit_weighted_ge5 | 2 | 0/6 | 0.0000 / 0.0000 | 6.000 / 0.000 | NA |
| numeric_5bit_weighted_ge5 | 3 | 0/6 | 0.0000 / 0.0000 | 4.000 / 0.000 | NA |
| numeric_5bit_weighted_ge5 | 4 | 0/6 | 0.0000 / 0.0000 | 2.000 / 0.000 | NA |
| numeric_4bit_weighted_ge4 | 2 | 0/6 | 0.0000 / 0.0000 | 4.000 / 0.000 | NA |
| numeric_4bit_weighted_ge4 | 3 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 32.00 / 3.00 |
| numeric_4bit_weighted_ge4 | 4 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 32.00 / 3.00 |
| route_mux_xor_bit | 2 | 0/6 | 0.0000 / 0.0000 | 16.000 / 0.000 | NA |
| route_mux_xor_bit | 3 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 4.00 / 26.00 / 3.00 |
| route_mux_xor_bit | 4 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 4.00 / 26.00 / 3.00 |
| route_mux_xnor_bit | 2 | 0/6 | 0.0000 / 0.0000 | 16.000 / 0.000 | NA |
| route_mux_xnor_bit | 3 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 4.00 / 26.00 / 3.00 |
| route_mux_xnor_bit | 4 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 4.00 / 26.00 / 3.00 |
| route_mux_conditional_flip | 2 | 0/6 | 0.0000 / 0.0000 | 16.000 / 0.000 | NA |
| route_mux_conditional_flip | 3 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 34.00 / 3.00 |
| route_mux_conditional_flip | 4 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 34.00 / 3.00 |

## 事前Feasibility判定

numeric選択: `None`。route選択: `None`。両family選択基準は未達だった。

数値は5-input threshold 4がround 4で6/6、threshold 5が0/6、4-input thresholdがround 3で6/6となった。route 3 taskは全てround 3で6/6だった。全36 runでround 2実効幅128を確認したが、各taskの結果がseed間で0/6か6/6へ分かれ、中難度設定は得られなかった。E041からFunction比較対象を選ばない。この段差は単一truth tableのseed成功率を調整し続けるより、事前固定した難度suite全体を評価単位にする方が安定することを示唆する。

## Round感度（round 4−2 exact、Holm補正）

| task | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric_5bit_weighted_ge4 | +1.0000 | 0.0000 | [1.0000, 1.0000] | NA | 0.0312 | 0.1875 |
| numeric_5bit_weighted_ge5 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| numeric_4bit_weighted_ge4 | +1.0000 | 0.0000 | [1.0000, 1.0000] | NA | 0.0312 | 0.1875 |
| route_mux_xor_bit | +1.0000 | 0.0000 | [1.0000, 1.0000] | NA | 0.0312 | 0.1875 |
| route_mux_xnor_bit | +1.0000 | 0.0000 | [1.0000, 1.0000] | NA | 0.0312 | 0.1875 |
| route_mux_conditional_flip | +1.0000 | 0.0000 | [1.0000, 1.0000] | NA | 0.0312 | 0.1875 |

全30 exact式を64入力で再評価した。36 run、108 derived row、progress、strict JSON、source hash、target非衝突、Library不使用、実効幅を監査。探索CPU時間合計26.5秒。

## Roadmap

- [Done] 隣接complexityの新規6 taskをbaseline-onlyで校正し、全runで実効beam幅128を確認した。
- [Next] E040のhard taskとE041のeasy taskを結果どおり凍結し、各familyの事前固定difficulty suiteを評価単位にする設計を登録する。
- [Later] suite-level基準を独立seedで校正後、衝突なし固定幅replace/add比較へ進み、その後にState形成・分解とRouter統合を検討する。

English: E041 moved task complexity in the preregistered adjacent direction, but every task still split sharply to 0/6 or 6/6 across seeds. This suggests freezing a mixed difficulty suite as the evaluation unit instead of repeatedly tuning a single truth table. No Function condition was evaluated or selected.

简体中文：E041按预注册的相邻方向调整任务复杂度，但每个任务在不同种子上仍明显分成0/6或6/6。这表明应冻结混合难度任务组作为评估单位，而不是反复调节单个真值表。本实验未评估或选择任何函数条件。

[事前計画](../results/E041-adjacent-grammar-calibration/PROTOCOL.md) / [生データ](../results/E041-adjacent-grammar-calibration/run/results.json) / [派生行](../results/E041-adjacent-grammar-calibration/run/derived_rows.json) / [選択](../results/E041-adjacent-grammar-calibration/run/selected_settings.json) / [監査](../results/E041-adjacent-grammar-calibration/run/audit_summary.json)
