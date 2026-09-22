# E035：重み付き数値Grammarの移植なし難度校正

実行日：2026-09-22。数値truth tableの重みと閾値を事前固定した6 taskについて、移植なし・beam128・6 round・tree cost16で新規6 seedを実行した。計36探索。E034のroute候補は`route_cross_and@4`に固定したまま再選定していない。

| task | 正例/64 | exact/6 | 難度 | best error平均 ± SD | 成功式のprimitive / routing bits / depth平均 |
| --- | ---: | ---: | --- | ---: | ---: |
| numeric_symmetric_ge5 | 45 | 0/6 | floor | 1.000 ± 0.000 | NA |
| numeric_symmetric_ge6 | 37 | 0/6 | floor | 3.000 ± 0.000 | NA |
| numeric_symmetric_ge7 | 27 | 0/6 | floor | 2.667 ± 0.816 | NA |
| numeric_asymmetric_ge5 | 47 | 0/6 | floor | 2.000 ± 0.000 | NA |
| numeric_asymmetric_ge6 | 40 | 0/6 | floor | 2.500 ± 0.548 | NA |
| numeric_asymmetric_ge7 | 32 | 0/6 | floor | 2.000 ± 0.000 | NA |

## 事前選定と対照

middleは移植なしexact 2–4/6。候補はすべて凍結し、後からFunction成績で絞らない。数値候補: なし。

同じseedでのasymmetric−symmetric exact率の対応差：

| threshold | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| 5 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| 6 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| 7 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |

各taskのexact平均・不偏分散、best error平均・不偏分散、生成signature数平均・不偏分散、時間平均秒：

- numeric_symmetric_ge5: exact 0.000 / 0.000; error 1.000 / 0.000; signatures 111271.5 / 14488733.5; time 5.768秒。
- numeric_symmetric_ge6: exact 0.000 / 0.000; error 3.000 / 0.000; signatures 126004.7 / 12718425.1; time 6.140秒。
- numeric_symmetric_ge7: exact 0.000 / 0.000; error 2.667 / 0.667; signatures 128495.7 / 10589327.1; time 4.451秒。
- numeric_asymmetric_ge5: exact 0.000 / 0.000; error 2.000 / 0.000; signatures 101905.3 / 18643052.3; time 3.677秒。
- numeric_asymmetric_ge6: exact 0.000 / 0.000; error 2.500 / 0.300; signatures 113800.0 / 20176574.4; time 4.783秒。
- numeric_asymmetric_ge7: exact 0.000 / 0.000; error 2.000 / 0.000; signatures 125557.7 / 8774421.5; time 4.775秒。

exact解は0件で、全入力再評価の対象はなかった。36 unique record、progress一致、strict JSON、source hash、Function library不使用を監査した。正例数はtruth tableの構成比であり、探索難度や精度の証明ではない。

## Roadmap

- [Done] 新しい重み付き数値grammarを結果より前に凍結し、移植なしだけで6 seedの難度を測った。
- [Next] 誤り1/64まで到達した`numeric_symmetric_ge5`を候補にbeam幅のbaseline-only pilotを事前固定する。Function条件で候補を選ばない。
- [Later] 費用付きFunction admissionとState付き形成・分解を検証し、負荷分散付きRouter、均衡固定random経路、同一run内→別seed Expert交換へ進む。

English: This experiment calibrated numeric task difficulty using baseline search only; any middle-difficulty tasks are frozen for independent testing. It does not evaluate a learned Function.

简体中文：本实验仅用基线搜索校准数值任务难度；所有中等难度候选均被冻结，留待独立种子验证。本实验不评价学习函数。

[事前計画](../results/E035-numeric-grammar/PROTOCOL.md) / [生データ](../results/E035-numeric-grammar/run/results.json) / [凍結Task](../results/E035-numeric-grammar/run/frozen_tasks.json) / [選定Task](../results/E035-numeric-grammar/run/selected_numeric_tasks.json) / [監査](../results/E035-numeric-grammar/run/audit_summary.json)
