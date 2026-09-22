# E036：数値タスクの移植なしBeam幅校正

実行日：2026-09-22。E035でbest error 1/64だった`numeric_symmetric_ge5`を固定し、移植なし・6 round・tree cost16でbeam幅64/128/192/256を新規6 seedで比較した。24探索。E034のroute候補は`route_cross_and@4`のまま固定した。

| beam | exact/6 | 難度 | best error平均 ± SD | signature数平均 | 秒/探索平均 | 成功式 primitive / routing bits / depth平均 |
| ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 64 | 0/6 | floor | 2.667 ± 0.816 | 41224.7 | 1.512 | NA |
| 128 | 0/6 | floor | 1.000 ± 0.000 | 110442.3 | 5.000 | NA |
| 192 | 0/6 | floor | 1.000 ± 0.000 | 217632.7 | 9.771 | NA |
| 256 | 2/6 | middle | 0.667 ± 0.516 | 345359.0 | 18.336 | 15.00 / 106.00 / 6.00 |

各幅のexact平均・不偏分散、およびbest error平均・不偏分散：

- beam64: exact 0.0000 / 0.0000; best error 2.6667 / 0.6667。
- beam128: exact 0.0000 / 0.0000; best error 1.0000 / 0.0000。
- beam192: exact 0.0000 / 0.0000; best error 1.0000 / 0.0000。
- beam256: exact 0.3333 / 0.2667; best error 0.6667 / 0.2667。

## 対応比較と選定

事前の中難度規則は移植なしexact 2–4/6。複数該当時は最小beam幅を採用する。選定結果：`numeric_symmetric_ge5@beam256`。

幅を変えるとbeam軌跡も変わるため、seed内の成功やbest errorが単調に改善するとは仮定しない。下のbest error差は`大きい幅−小さい幅`で、負値が改善を表す。

### exact率の対応差

| 幅の差 | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| 128-minus-64 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| 192-minus-128 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| 256-minus-192 | +0.3333 | 0.2667 | [0.0000, 0.6667] | 0.645 | 0.5000 | 1.0000 |

### best errorの対応差

| 幅の差 | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| 128-minus-64 | -1.6667 | 0.6667 | [-2.0000, -1.0000] | -2.041 | 0.0625 | 0.1875 |
| 192-minus-128 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| 256-minus-192 | -0.3333 | 0.2667 | [-0.6667, 0.0000] | -0.645 | 0.5000 | 1.0000 |

全2件のexact式を64入力で再評価した。24 unique record、progress一致、strict JSON、source hash、Function library不使用を監査した。計測時間とsignature数は探索の計算量であり、推論速度や物理ゲート数を示さない。

## Roadmap

- [Done] E035で選んだ近接数値タスクを固定し、beam幅だけをbaseline-onlyで校正した。
- [Next] 凍結した数値task/幅とE034のroute候補を、新規独立seedで移植なし／通常Function／一段barrier／同費用random／inertを各task内の同一予算で比較する。
- [Later] 費用付きFunction admission、State付き形成・分解、初回負荷分散Router・均衡固定random経路・Expert交換を検証する。

English: E036 changed only the beam width of a baseline numeric search. The selected width, if any, is a pilot difficulty setting and does not establish learned-Function value.

简体中文：E036仅调整数值任务基线搜索的beam宽度。即使选出宽度，它也只是预实验的难度设置，不能证明学习函数的价值。

[事前計画](PROTOCOL.md) / [生データ](run/results.json) / [固定設定](run/frozen_settings.json) / [選定結果](run/selected_numeric_width.json) / [監査](run/audit_summary.json)
