# E038：Functionの投入時刻を変える機構Pilot

実行日：2026-09-22。E037で結果を見た2 taskをそのまま用いる探索的な機構実験。新規6 seedで移植なし／初回学習Function／初回探索後の学習Function・inert・同費用randomを比較した。各task内のbeamとround上限は固定し、遅延投入では選択済みbeamの最後の1枠を置換した。計60探索。新taskでの独立確認ではない。

| task | 条件 | exact/6 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | Function使用成功/成功数 | 秒/探索平均 | 成功式 primitive / routing bits / depth平均 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| numeric_symmetric_ge5 | no_transfer | 2/6 | 0.3333 / 0.2667 | 0.667 / 0.267 | 0/2 | 14.64 | 13.00 / 94.00 / 5.00 |
| numeric_symmetric_ge5 | early_learned | 0/6 | 0.0000 / 0.0000 | 1.000 / 0.000 | 0/0 | 15.52 | NA |
| numeric_symmetric_ge5 | late_learned | 2/6 | 0.3333 / 0.2667 | 0.667 / 0.267 | 0/2 | 14.20 | 15.00 / 106.00 / 6.00 |
| numeric_symmetric_ge5 | late_inert | 2/6 | 0.3333 / 0.2667 | 0.667 / 0.267 | 0/2 | 16.87 | 14.00 / 100.00 / 5.50 |
| numeric_symmetric_ge5 | late_random | 2/6 | 0.3333 / 0.2667 | 0.667 / 0.267 | 0/2 | 12.91 | 14.00 / 100.00 / 5.50 |
| route_cross_and | no_transfer | 4/6 | 0.6667 / 0.2667 | 0.667 / 1.067 | 0/4 | 2.23 | 11.00 / 78.00 / 4.00 |
| route_cross_and | early_learned | 3/6 | 0.5000 / 0.3000 | 1.167 / 1.767 | 0/3 | 3.43 | 11.00 / 78.00 / 4.00 |
| route_cross_and | late_learned | 4/6 | 0.6667 / 0.2667 | 0.667 / 1.067 | 0/4 | 2.17 | 11.00 / 78.00 / 4.00 |
| route_cross_and | late_inert | 4/6 | 0.6667 / 0.2667 | 0.667 / 1.067 | 0/4 | 1.91 | 11.00 / 78.00 / 4.00 |
| route_cross_and | late_random | 4/6 | 0.6667 / 0.2667 | 0.667 / 1.067 | 0/4 | 2.07 | 11.00 / 78.00 / 4.00 |

## 事前主指標：両task平均の遅延−初回exact差

平均差 +0.2500、不偏分散 0.1750、bootstrap 95% CI [0.0000, 0.5833]、Cohen dz 0.598、two-sided exact sign-flip p=0.5000。方向性pilot基準（平均≥+0.25かつp≤0.05）は未達。

## 副次exact比較（4比較Holm補正）

| 比較 | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric:late-minus-early | +0.3333 | 0.2667 | [0.0000, 0.6667] | 0.645 | 0.5000 | 1.0000 |
| route:late-minus-early | +0.1667 | 0.1667 | [0.0000, 0.5000] | 0.408 | 1.0000 | 1.0000 |
| pooled:late-learned-minus-inert | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| pooled:late-learned-minus-random | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |

学習Function固有の利益基準（遅延学習−遅延inertが正でHolm p≤0.05、かつ学習signatureを使う成功式≥1）は未達。
遅延条件36対の初回beamとbest errorを移植なしと照合した。実際のround 2投入は36/36、signature衝突は7件。

生成unique signature数（平均 / 不偏分散）：

- numeric_symmetric_ge5 / no_transfer: 334119.2 / 838934422.6。
- numeric_symmetric_ge5 / early_learned: 329924.7 / 17561763.1。
- numeric_symmetric_ge5 / late_learned: 339783.8 / 40732609.8。
- numeric_symmetric_ge5 / late_inert: 336805.5 / 581423684.7。
- numeric_symmetric_ge5 / late_random: 339727.2 / 481327411.4。
- route_cross_and / no_transfer: 72491.3 / 2157351.5。
- route_cross_and / early_learned: 88649.3 / 3481071.5。
- route_cross_and / late_learned: 73418.7 / 4688351.1。
- route_cross_and / late_inert: 72628.7 / 5039848.7。
- route_cross_and / late_random: 72586.8 / 2934367.8。

全27件のexact式を64入力で再評価した。60 unique record、progress一致、strict JSON、source hash、12 random Functionの費用・signature、別seed smokeを監査した。54件後の実行session中断から凍結設定を変えず残り6件を再開し、探索ごとのCPU時間合計は515.8秒だった。探索時間やsignature数は推論の実測速度や物理ゲート数ではない。

## Roadmap

- [Done] 投入時刻を変え、同時刻inert・randomとの違いを新シードで探索的に測った。
- [Next] timing効果の有無と最終式のFunction使用を分け、新しいtaskを事前固定して移植性を確認する。
- [Later] 費用付きLibrary形成・分解とState、負荷分散Router、固定random経路、Expert交換へ進む。

English: E038 is an exploratory timing study on two previously inspected tasks. A timing change alone does not establish transferable learned-Function benefit; the matched inert and random controls and final-expression usage separate those mechanisms.

简体中文：E038是在两个先前已检视任务上的探索性投入时序实验。仅改变时序不能证明学习函数的可迁移收益；同时间的惰性和随机对照及最终表达式使用情况用于区分机制。

[事前計画](PROTOCOL.md) / [生データ](run/results.json) / [凍結設定](run/frozen_manifest.json) / [監査](run/audit_summary.json)
