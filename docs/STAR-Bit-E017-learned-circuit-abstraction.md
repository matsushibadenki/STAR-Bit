# E017：Learned Circuit Abstraction 境界実験

実行日：2026-09-12。入出力例からsoft DLGNを学習し、hard circuitへ離散化し、その後にModuleを発見する構想のうち、まず全タスクで正確なhard circuitを安定形成できるかを検査した。事前停止条件により、未完成回路の圧縮率を成功指標として報告することは避けた。

## 結論

**parityとmuxでは、タスク名・中間教師・手書き回路を与えず、入出力例から全64入力に一致するhard circuitが4/4 seedで形成された。comparatorとcarryでは同じ設定による完全一致が0/4 seedで、離散refinement後も全タスク3/4以上というmain移行基準を満たさなかった。したがって、学習による汎用的な自律Module形成はまだ実証されていない。**

## Pilot 1：learnable wiringだけでは深さを使わない

E004の固定ランダム配線を、全過去nodeからsoft選択する学習配線へ置き換えた。16 task/seed runのhard test平均はsoft-only 0.6016、後半straight-through 0.6055、full-domain完全一致は両条件0だった。出力が原入力や単一ゲートへ短絡し、live gate平均は0.69／0.75に崩壊した。

## Pilot 2：強制深度とタスク非依存LUT多様性

出力を第5層へ限定し、各層を原入力＋直前層へ接続した。各層に16種類の2入力LUTを一度ずつ配置するdiverse初期化は、タスク固有の意味や回路を使わない。各task/seed/条件は4 restartを走らせ、train accuracyとtrain BCEだけで1本を選択した。

| task | 初期化 | hard test平均 | 不偏分散 | hard full平均 | 完全一致seed | live gate平均 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| parity | random_tables | 1.000000 | 0.000000 | 1.000000 | 4/4 | 7.50 |
| parity | diverse_tables | 1.000000 | 0.000000 | 1.000000 | 4/4 | 10.00 |
| comparator | random_tables | 0.734375 | 0.006185 | 0.867188 | 0/4 | 5.00 |
| comparator | diverse_tables | 0.734375 | 0.006185 | 0.882812 | 0/4 | 7.75 |
| mux | random_tables | 0.656250 | 0.003906 | 0.750000 | 0/4 | 1.00 |
| mux | diverse_tables | 1.000000 | 0.000000 | 1.000000 | 4/4 | 8.50 |
| carry | random_tables | 0.890625 | 0.003581 | 0.906250 | 0/4 | 6.50 |
| carry | diverse_tables | 0.890625 | 0.008789 | 0.941406 | 0/4 | 8.25 |

全16対応runでdiverse−randomのhard test差は平均+0.085938、不偏分散0.027018。これは設定選択pilotなので有意差検定をconfirmatory evidenceとして使用しない。diverse条件の総平均0.90625は0.90基準を超えたが、comparator/carryの完全一致が0件だったため、事前規則どおりmainへ進めなかった。

## Pilot 3：離散refinement

complete truth tableを使う回路同定段階として、100,000提案の離散配線・LUT探索を実施した。ここでは全64行を学習に使うため、予測汎化は主張しない。

| 開始状態 | exact run | parity | comparator | mux | carry | 初期誤り平均 | 最終誤り平均 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dlgn_start | 13/16 | 4/4 | 2/4 | 4/4 | 3/4 | 2.812 | 0.375 |
| random_start | 12/16 | 4/4 | 2/4 | 4/4 | 2/4 | 31.062 | 0.812 |

DLGN開始は初期誤りをrandom開始31.06から2.81へ減らしたが、exact到達は13/16対12/16に留まった。良い初期精度が探索しやすい回路構造を保証しない。comparatorは両条件2/4で、main移行に必要な3/4へ届かなかった。

## SAT診断

任意2入力LUTを逐次接続し、全64行との一致だけを制約した。row-wise encodingと64-bit truth-vector encodingを同じ1–10 LUT、各10秒で比較した。両方式ともparityは5 LUT、muxは3 LUTでSAT witnessを得て独立評価器で完全一致を確認した。それ未満はUNSATだった。comparatorは1–4 LUT、carryは1–4 LUTがUNSATで、5–10 LUTはtimeoutによるUNKNOWNだった。UNKNOWNを表現不能とは扱わない。

BitVector化により小さい問は高速化したが、難しい問のstatusは変わらなかった。DLGN最適化の失敗と、5–10 LUTでの表現不能は分離できていない。SATはModule抽出や汎化の結果ではない。

## なぜModule Minerをまだ適用しないか

不正確なhard circuitでも、意味のない定数・恒等・冗長部分が繰り返されれば記述量は短くできる。その値を『学習による抽象構造』と呼ぶと、タスクを解けなかった事実と圧縮を混同する。E017では全タスクのexact回路を事前条件にしたため、Syntax／Functional／Global Moduleの主比較は未実施である。

parityとmuxのexact回路は、自律形成の肯定的な限定例として保存する。ただしpilot条件選択に使ったseedなので、Module再利用やtransferのconfirmatory evidenceには使わない。

## 次の改善

次はCEGIS（反例誘導合成）で少数行から始め、候補回路の反例だけを追加する。探索空間にはLUT、配線、Stateを残し、目的を `task error + λ1 primitive + λ2 library + λ3 routing + λ4 state` のPareto frontとして事前登録する。単一λを結果後に選ばず、精度制約を満たす解の総費用を比較する。

Module Libraryは、各moduleの真理値signature、定義bit、call-site配線bitを含めて課金する。source seedで形成したLibraryをtarget seed・別タスクへ固定移植し、学習step短縮、解到達率、総記述bitをfrom-scratch対照と比較する。

## Roadmap

- [Done] 固定配線を学習配線へ置き換え、soft→hard→独立exportの機能一致を検査した。
- [Done] parityとmuxで4/4 seedのfull-domain exact hard circuitを入力出力例から形成した。
- [Done] comparator/carryの失敗をstraight-through、タスク非依存LUT多様性、離散refinement、2種類のSAT encodingで診断した。
- [Done] DLGN開始と同予算random開始を比較し、初期誤りと最終exact到達を分離した。
- [Next] CEGISと機能signature重複除去を組み合わせ、全4タスクのexact circuit形成率を新seedで確認する。
- [Next] exact到達後にHard、Syntax Module、Functional/Global Moduleの記述bit、primitive DAG、再利用、階層深度を比較する。
- [Next] source task/seed Libraryを固定して別task/seedへ移植し、from-scratchとの学習予算差を測る。
- [Later] routing・library・state費用を含むPareto frontをLogic Expertとternary Expertの混合へ拡張する。

English: E017 established exact learned hard circuits for parity and mux, but not for comparator and carry under the same training setup. Discrete refinement reached 13/16 exact runs from DLGN starts versus 12/16 from random starts, missing the preregistered all-task threshold. Module-mining claims were therefore withheld. The next step is counterexample-guided synthesis with explicit library, routing, and state costs.

简体中文：E017在parity与mux上形成了精确的学习硬电路，但相同设置未能稳定解决comparator与carry。离散优化从DLGN开始达到13/16，从随机开始达到12/16，未满足预注册的全任务门槛，因此没有提出模块抽象成功的结论。下一步是引入反例引导合成，并显式计入模块库、路由与状态成本。

[Pilot 1計画](../results/E017-learned-circuit-abstraction/PILOT-PROTOCOL.md) / [Pilot 2計画](../results/E017-learned-circuit-abstraction/PILOT2-PROTOCOL.md) / [離散refinement計画](../results/E017-learned-circuit-abstraction/PILOT3-PROTOCOL.md) / [SAT計画](../results/E017-learned-circuit-abstraction/SAT-PROBE-PROTOCOL.md) / [BitVector SAT計画](../results/E017-learned-circuit-abstraction/SAT-BV-PROTOCOL.md)
