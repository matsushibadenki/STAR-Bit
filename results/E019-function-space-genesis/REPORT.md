# E019：Function-space Module Genesis pilot

実行日：2026-09-12。回路構文ではなく64入力のtruth signatureを中間機能の識別子とし、同一機能を生成した異なる構文を即時統合した。正解への現在誤差だけで候補を残す探索と、将来のcomposition可能性を残す探索を比較した。

## 結論

**機能signatureによる同値統合は数十万件の構文重複を除去できたが、それだけでは有用な中間機能を保持できなかった。タスク非依存のaffine scaffoldを明示的に保持すると、最終parityと単体では無相関なpartial parityが残り、parity exactを0/4から4/4へ回復した。comparator/carryは未解決であり、自律的Module Genesisはまだ成立していない。**

## Pilot 1：一段lookahead

| condition | exact target平均 | parity | comparator | mux | carry | 一意signature平均 | 同値merge平均 | 秒平均 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| target_greedy | 1.0 | 0/4 | 0/4 | 4/4 | 0/4 | 138957 | 296709 | 0.665 |
| composition_pareto | 1.0 | 0/4 | 0/4 | 4/4 | 0/4 | 132146 | 332492 | 4.601 |

一段lookaheadと7次元Pareto保持を追加しても、両条件ともmuxだけ4/4だった。partial parityは完成まで複数compositionを要し、一段先のtarget errorでは価値を認識できなかった。

## Pilot 2：affine scaffold

| condition | exact target平均 | 不偏分散 | parity | comparator | mux | carry | 一意signature平均 | 同値merge平均 | 秒平均 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| target_greedy | 1.0 | 0.0 | 0/4 | 0/4 | 4/4 | 0/4 | 322656 | 1060838 | 2.348 |
| affine_scaffold | 2.0 | 0.0 | 4/4 | 0/4 | 4/4 | 0/4 | 486035 | 2076063 | 3.731 |

affine scaffoldは、6入力のXOR部分集合とその反転に対応する128 signatureを、探索中に生成された場合だけ保持する。ゲート名、task固有module、中間教師は与えていないが、affine関数族を人手で選んだ帰納バイアスである。

全4 seedでmuxはround 2、3 primitives、routing 20 bits、depth 2で発見された。affine条件のparityはround 3、5 primitives、routing 32 bits、depth 3で発見され、すべてaffine中間signatureを再利用した。これは『正解への即時相関がない踏み石を保持すれば到達可能性が変わる』という限定的な肯定結果である。

comparator/carryはbeam 256、7 round、tree cost 14でも0/4だった。affine保持はexact target数を1から2へ増やしたが、事前の全4 target 3/4 seed基準を満たさないため16-seed mainへ進めない。pilot結果に有意差検定は適用しない。

## Module Genesis Problemへの含意

E014–E016では検証済みModuleが存在すればroutingが機能した。E017–E019では、primitiveから良い中間機能を作り、将来価値が現れるまでarchiveへ残す部分がボトルネックになった。E019は同値関数mergeと踏み石保持を別々に検査し、後者がparityの到達性を変えることを示した。

次は関数族を人手指定せず、生成された上位の子候補へ複数round・複数taskで繰り返し寄与した親signatureへpromotion scoreを与える。`reuse_count`、改善したtask数、子のPareto rank、生成costを保存し、昇格・維持・削除を決める。これによりaffine scaffoldをlearned archive promotionへ置き換える。

## Roadmap

- [Done] 64-bit signatureを機能identityとして、同値構文を生成時点で統合した。
- [Done] target-greedy、一段composition lookahead、Pareto保持を同じ生成予算で比較した。
- [Done] task非依存affine scaffoldによりparity exactを0/4から4/4へ回復した。
- [Done] primitive、routing bits、depth、親expression、発見round、同値merge数を保存した。
- [Next] 子候補への寄与から親Functionを自動昇格するlearned archive promotionを実装する。
- [Next] comparator/carryを含む全task exact後に、Module定義bit・call routing bit・reuse・階層深度を測る。
- [Later] source task Libraryを別taskへ固定移植し、from-scratchとの探索予算差を16 seedで比較する。

English: Exact truth signatures removed large amounts of syntactic duplication but did not by themselves preserve useful stepping stones. A task-independent affine scaffold recovered parity in 4/4 seeds, demonstrating that intermediate retention can change reachability. Comparator and carry remain unsolved, and the scaffold is an explicit inductive bias rather than autonomous Module Genesis.

简体中文：精确真值签名消除了大量语法重复，但本身不足以保留有用的中间踏脚石。任务无关的仿射支架使parity从0/4恢复到4/4，说明中间功能保留可以改变目标可达性。comparator与carry仍未解决，该支架属于显式归纳偏置，并非自主模块生成。

[Pilot 1計画](../results/E019-function-space-genesis/PILOT-PROTOCOL.md) / [Pilot 2計画](../results/E019-function-space-genesis/PILOT2-PROTOCOL.md) / [Pilot 1生データ](../results/E019-function-space-genesis/pilot/results.json) / [Pilot 2生データ](../results/E019-function-space-genesis/pilot2/results.json)
