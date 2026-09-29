# E043：凍結Suiteでの衝突なし遅延Admission介入

実行日：2026-09-29。E042の全8 taskを固定し、新規6 seedで移植なしと、learned／inert／同費用randomのround 1後replace/addを比較した。randomは48 seed/taskすべてで全round 1 beamとのsignature衝突を事前除外した。計336探索。

| family | 条件 | exact/24 | seed別exact平均 / 不偏分散 | seed別best error平均 / 不偏分散 | Function使用成功/成功数 | 秒平均 | 成功式 primitive / routing / depth平均 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| numeric | no_transfer | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 0/12 | 1.032 | 5.00 / 33.00 / 3.00 |
| numeric | learned_replace | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 0/12 | 1.030 | 5.00 / 33.00 / 3.00 |
| numeric | learned_add | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 0/12 | 1.050 | 5.00 / 33.00 / 3.00 |
| numeric | inert_replace | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 0/12 | 1.053 | 5.00 / 33.00 / 3.00 |
| numeric | inert_add | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 0/12 | 1.082 | 5.00 / 33.00 / 3.00 |
| numeric | random_replace | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 0/12 | 1.066 | 5.00 / 33.00 / 3.00 |
| numeric | random_add | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.000 | 0/12 | 1.038 | 5.00 / 33.00 / 3.00 |
| route | no_transfer | 12/24 | 0.5000 / 0.0000 | 3.333 / 0.442 | 0/12 | 1.142 | 4.50 / 30.00 / 3.00 |
| route | learned_replace | 12/24 | 0.5000 / 0.0000 | 3.375 / 0.494 | 0/12 | 1.228 | 4.50 / 30.00 / 3.00 |
| route | learned_add | 12/24 | 0.5000 / 0.0000 | 3.375 / 0.494 | 0/12 | 1.130 | 4.50 / 30.00 / 3.00 |
| route | inert_replace | 12/24 | 0.5000 / 0.0000 | 3.333 / 0.442 | 0/12 | 1.161 | 4.50 / 30.00 / 3.00 |
| route | inert_add | 12/24 | 0.5000 / 0.0000 | 3.333 / 0.442 | 0/12 | 1.140 | 4.50 / 30.00 / 3.00 |
| route | random_replace | 12/24 | 0.5000 / 0.0000 | 3.375 / 0.544 | 0/12 | 1.077 | 4.50 / 30.00 / 3.00 |
| route | random_add | 12/24 | 0.5000 / 0.0000 | 3.333 / 0.442 | 0/12 | 1.147 | 4.50 / 30.00 / 3.00 |

## 事前主指標：add−replace exact差

平均差 +0.0000、不偏分散 0.0000、bootstrap 95% CI [0.0000, 0.0000]、dz NA、exact p=1.0000。容量基準は未達。

| family | 平均差 | 95% CI | exact p | Holm p |
| --- | ---: | --- | ---: | ---: |
| numeric | +0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |
| route | +0.0000 | [0.0000, 0.0000] | 1.0000 | 1.0000 |

## 学習意味の副次Gate

| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| learned-add-minus-inert-add | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| learned-add-minus-random-add | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |

学習意味基準は未達。learned-add成功式でFunction使用0件。

## 探索的best-error差（負が左条件有利）

| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p |
| --- | ---: | ---: | --- | ---: | ---: |
| pooled:add-minus-replace | -0.0069 | 0.0003 | [-0.0208, 0.0000] | -0.408 | 1.0000 |
| learned-add-minus-inert-add | +0.0208 | 0.0026 | [0.0000, 0.0625] | 0.408 | 1.0000 |
| learned-add-minus-random-add | +0.0208 | 0.0026 | [0.0000, 0.0625] | 0.408 | 1.0000 |

全条件・familyのexact率は0.5で一致し、add−replace差も学習意味差も0だった。E042のsuite平均headroomはeasyの天井とhardの床を混ぜた集約上のheadroomであり、局所介入に反応する感度を保証しなかった。今後は独立calibration seedで意味を持たないperturbationへの局所応答またはbest error近接性を確認し、その後に別seedでlearned意味を検証する。

全168 exact式を64入力で再評価した。336 record、48 random Function、288 first-round照合、288幅検証、衝突0、strict JSON、progress、source hashを監査。探索CPU時間合計369.0秒。物理ゲート数・推論速度・Router学習は未測定。

## Roadmap

- [Done] 凍結suiteで衝突なしreplace/add介入を完了し、集約headroomだけでは局所感度を保証しないことを確認した。
- [Next] calibration seedでinert/random perturbationへの局所応答とbest-error近接性を事前基準化し、確認seedを分離する。
- [Later] learned固有効果と直接使用が成立後、State形成・分解、Logic/Ternary Router、総物理費用へ進む。

English: E043 found identical 0.50 exact rates for every condition and family. The frozen suite had aggregate headroom but no local sensitivity to delayed replacement or addition; no successful expression used the learned Function.

简体中文：E043中所有条件和任务族的exact率都为0.50。冻结任务组具有聚合层面的空间，却对延迟替换或增加容量没有局部敏感性；成功表达式均未使用学习函数。

[事前計画](../results/E043-suite-capacity-intervention/PROTOCOL.md) / [生データ](../results/E043-suite-capacity-intervention/run/results.json) / [凍結設定](../results/E043-suite-capacity-intervention/run/frozen_manifest.json) / [Round 1照合](../results/E043-suite-capacity-intervention/run/round1_preflight.json) / [監査](../results/E043-suite-capacity-intervention/run/audit_summary.json)
