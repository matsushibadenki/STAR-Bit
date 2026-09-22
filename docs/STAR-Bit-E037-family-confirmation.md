# E037：凍結した数値・経路候補でFunction条件を独立シード確認

実行日：2026-09-22。E034のroute`cross_and@beam128/4round`とE036のnumeric`symmetric_ge5@beam256/6round`を凍結し、新規6 seedで5条件を各task内同一予算で比較した。計60探索。FunctionもE026の採用1件を再学習せず凍結した。

| task | 条件 | exact/6 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | 使用した成功式/成功数 | 秒/探索平均 | 成功式 primitive / routing bits / depth平均 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| numeric_symmetric_ge5 | no_transfer | 2/6 | 0.3333 / 0.2667 | 0.667 / 0.267 | 0/2 | 10.03 | 14.00 / 100.00 / 5.50 |
| numeric_symmetric_ge5 | admitted | 0/6 | 0.0000 / 0.0000 | 1.000 / 0.000 | 0/0 | 10.83 | NA |
| numeric_symmetric_ge5 | one_hop_barrier | 2/6 | 0.3333 / 0.2667 | 0.667 / 0.267 | 0/2 | 10.67 | 13.00 / 94.00 / 5.00 |
| numeric_symmetric_ge5 | inert_slot | 2/6 | 0.3333 / 0.2667 | 0.667 / 0.267 | 0/2 | 10.53 | 14.00 / 100.00 / 5.50 |
| numeric_symmetric_ge5 | random_matched | 1/6 | 0.1667 / 0.1667 | 0.833 / 0.167 | 1/1 | 9.72 | 15.00 / 108.00 / 7.00 |
| route_cross_and | no_transfer | 3/6 | 0.5000 / 0.3000 | 1.000 / 1.200 | 0/3 | 2.00 | 11.00 / 78.00 / 4.00 |
| route_cross_and | admitted | 3/6 | 0.5000 / 0.3000 | 1.000 / 1.200 | 0/3 | 2.09 | 11.00 / 78.00 / 4.00 |
| route_cross_and | one_hop_barrier | 4/6 | 0.6667 / 0.2667 | 0.667 / 1.067 | 0/4 | 1.85 | 11.00 / 78.00 / 4.00 |
| route_cross_and | inert_slot | 3/6 | 0.5000 / 0.3000 | 1.000 / 1.200 | 0/3 | 1.90 | 11.00 / 78.00 / 4.00 |
| route_cross_and | random_matched | 3/6 | 0.5000 / 0.3000 | 1.000 / 1.200 | 0/3 | 1.90 | 11.00 / 78.00 / 4.00 |

## 事前主仮説

主指標は`(barrier−admitted)_numeric − (barrier−admitted)_route`のseed対応exact差。タスク別の探索費用が異なるため、これは凍結設定での比較であり、一般的な数値対経路の因果差とは解釈しない。

平均差 +0.1667、不偏分散 0.5667、bootstrap 95% CI [-0.3333, 0.6667]、Cohen dz 0.221、two-sided exact sign-flip p=1.0000。事前の方向性確認基準（平均≥+0.25、p≤0.05）は未達。

## 副次比較（4比較Holm補正）

| 比較 | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric_symmetric_ge5:one_hop_barrier-minus-admitted | +0.3333 | 0.2667 | [0.0000, 0.6667] | 0.645 | 0.5000 | 1.0000 |
| numeric_symmetric_ge5:one_hop_barrier-minus-inert_slot | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| route_cross_and:one_hop_barrier-minus-admitted | +0.1667 | 0.1667 | [0.0000, 0.5000] | 0.408 | 1.0000 | 1.0000 |
| route_cross_and:admitted-minus-random_matched | +0.0000 | 0.4000 | [-0.5000, 0.5000] | 0.000 | 1.0000 | 1.0000 |

one-hop固有の利益判定（数値barrier−inertが正かつHolm p≤0.05）は未達。

数値taskではbarrierとinert、inertと移植なしが、どちらも6/6 seedでexact・best error一致。学習Functionを含む成功式は0件で、Functionの直接部品再利用は確認できない。
各条件の生成unique signature数（平均 / 不偏分散）：

- numeric_symmetric_ge5 / no_transfer: 339822.3 / 476988735.1。
- numeric_symmetric_ge5 / admitted: 330392.7 / 33387261.9。
- numeric_symmetric_ge5 / one_hop_barrier: 331412.8 / 659420956.2。
- numeric_symmetric_ge5 / inert_slot: 339822.3 / 476988735.1。
- numeric_symmetric_ge5 / random_matched: 298665.7 / 228498577.1。
- route_cross_and / no_transfer: 75280.0 / 12991587.2。
- route_cross_and / admitted: 89752.7 / 7358796.3。
- route_cross_and / one_hop_barrier: 83986.2 / 13209299.8。
- route_cross_and / inert_slot: 75056.0 / 11678916.4。
- route_cross_and / random_matched: 77971.3 / 28309487.5。

全23件のexact式を64入力で再評価した。60 unique record、progress一致、strict JSON、source hash、12 random Functionの費用・signatureを監査した。

## Roadmap

- [Done] baselineだけで凍結した両taskを独立seedと同task内同予算で5条件比較した。
- [Next] 結果の原因を、Functionの直接使用、beam摂動、inertとの違い、探索計算量から分けて検討する。
- [Later] 複数taskへの拡張後、費用付きadmission、State形成・分解、負荷分散Routerへ進む。

English: E037 compares five Function controls on fresh seeds for two frozen task/budget settings. Any interaction is limited to those settings because compute budgets differ across task families.

简体中文：E037在新种子上比较两个冻结任务／预算设置的五个函数对照。由于任务族间计算预算不同，交互作用的解释仅限这些设置。

[事前計画](../results/E037-family-confirmation/PROTOCOL.md) / [生データ](../results/E037-family-confirmation/run/results.json) / [凍結設定](../results/E037-family-confirmation/run/frozen_manifest.json) / [監査](../results/E037-family-confirmation/run/audit_summary.json)
