# E040：実効幅128での新規Task難度校正

実行日：2026-09-26。Function条件を見ず、事前固定した精密数値3 task・経路選択3 taskを新規6 seedでbaseline-only探索した。各seed/taskは5 roundを一度だけ実行し、決定論的prefixから3/4/5 round予算を評価した。

| task | round | exact/6 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | 成功式 primitive / routing / depth平均 |
| --- | ---: | ---: | ---: | ---: | ---: |
| numeric_2bit_sum_ge3 | 3 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 34.00 / 3.00 |
| numeric_2bit_sum_ge3 | 4 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 34.00 / 3.00 |
| numeric_2bit_sum_ge3 | 5 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 34.00 / 3.00 |
| numeric_2bit_absdiff_ge2 | 3 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 7.00 / 48.00 / 3.00 |
| numeric_2bit_absdiff_ge2 | 4 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 7.00 / 48.00 / 3.00 |
| numeric_2bit_absdiff_ge2 | 5 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 7.00 / 48.00 / 3.00 |
| numeric_2bit_product_ge3 | 3 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 34.00 / 3.00 |
| numeric_2bit_product_ge3 | 4 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 34.00 / 3.00 |
| numeric_2bit_product_ge3 | 5 | 6/6 | 1.0000 / 0.0000 | 0.000 / 0.000 | 5.00 / 34.00 / 3.00 |
| route_rotated_cross_xor | 3 | 0/6 | 0.0000 / 0.0000 | 16.000 / 0.000 | NA |
| route_rotated_cross_xor | 4 | 1/6 | 0.1667 / 0.1667 | 7.333 / 13.867 | 9.00 / 60.00 / 4.00 |
| route_rotated_cross_xor | 5 | 1/6 | 0.1667 / 0.1667 | 3.333 / 2.667 | 9.00 / 60.00 / 4.00 |
| route_rotated_cross_xnor | 3 | 0/6 | 0.0000 / 0.0000 | 16.000 / 0.000 | NA |
| route_rotated_cross_xnor | 4 | 0/6 | 0.0000 / 0.0000 | 7.667 / 0.667 | NA |
| route_rotated_cross_xnor | 5 | 0/6 | 0.0000 / 0.0000 | 4.000 / 0.000 | NA |
| route_nested_mux | 3 | 0/6 | 0.0000 / 0.0000 | 6.000 / 4.800 | NA |
| route_nested_mux | 4 | 0/6 | 0.0000 / 0.0000 | 4.667 / 4.667 | NA |
| route_nested_mux | 5 | 0/6 | 0.0000 / 0.0000 | 2.167 / 1.367 | NA |

## 事前Feasibility判定

numeric選択: `None`。route選択: `None`。両family選択基準は未達だった。

数値3 taskはすべてround 3で6/6の天井、routeは最大でもrotated cross XORのround 4/5で1/6だった。全36 runでround 2実効幅128を確認し、E039の幅上限未充足は解消したが、中難度設定は得られなかった。E040からFunction比較対象を選ばない。

## Round感度（round 5−3 exact、Holm補正）

| task | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric_2bit_sum_ge3 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| numeric_2bit_absdiff_ge2 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| numeric_2bit_product_ge3 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| route_rotated_cross_xor | +0.1667 | 0.1667 | [0.0000, 0.5000] | 0.408 | 1.0000 | 1.0000 |
| route_rotated_cross_xnor | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| route_nested_mux | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |

全19 exact式を64入力で再評価した。36 run、108 derived row、progress、strict JSON、source hash、target非衝突、Library不使用、実効幅を監査。探索CPU時間合計44.4秒。

## Roadmap

- [Done] 新規6 taskをbaseline-onlyで校正し、全runで実効beam幅128を確認した。
- [Next] 数値側を4〜5入力へ難化し、route側を1段浅くした隣接grammarを、同じbaseline-only選択規則で校正する。
- [Later] 両familyの中難度設定を独立seedで固定幅replace/add比較し、その後にState形成・分解とRouter統合へ進む。

English: E040 restored a fully populated 128-entry beam but found no middle-difficulty setting: all three numeric tasks reached 6/6 by round 3, while routing tasks reached at most 1/6. No Function condition was evaluated or selected.

简体中文：E040恢复了完整的128项beam，但没有得到中等难度设置：三个数值任务均在第3轮达到6/6，路由任务最高仅1/6。本实验未评估或选择任何函数条件。

[事前計画](../results/E040-full-width-calibration/PROTOCOL.md) / [生データ](../results/E040-full-width-calibration/run/results.json) / [派生行](../results/E040-full-width-calibration/run/derived_rows.json) / [選択](../results/E040-full-width-calibration/run/selected_settings.json) / [監査](../results/E040-full-width-calibration/run/audit_summary.json)
