# E023：Leave-one-task-out Function Transfer

実行日：2026-09-13。各評価taskについて、そのtaskのsource回路を完全に除外し、残る3 taskから費用帯別に8内部Functionを固定移植した。新規16 seed、4 task、4条件の256探索を事前固定した設定で実行した。

## 主要結果

| condition | exact / 64 | 成功率平均 | 不偏分散 | parity | comparator | mux | carry | 秒平均 / task |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_transfer | 34/64 | 0.5312 | 0.2530 | 16/16 | 2/16 | 16/16 | 0/16 | 2.183 |
| random_cost_matched | 37/64 | 0.5781 | 0.2478 | 16/16 | 0/16 | 16/16 | 5/16 | 2.009 |
| random_error_matched | 27/64 | 0.4219 | 0.2478 | 8/16 | 2/16 | 16/16 | 1/16 | 2.082 |
| learned_cross_task | 27/64 | 0.4219 | 0.2478 | 10/16 | 0/16 | 16/16 | 1/16 | 2.217 |

| paired比較（1 seed当たりexact task数） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| --- | ---: | ---: | --- | ---: | ---: |
| learned−error-matched random（primary） | +0.0000 | 0.4000 | [-0.3125, 0.3125] | 0.000 | 1.000000 |
| learned−cost-matched random | -0.6250 | 0.2500 | [-0.8750, -0.3750] | -1.250 | 0.001953 |
| learned−no transfer | -0.4375 | 0.5292 | [-0.8125, -0.0625] | -0.601 | 0.062500 |

primaryのlearned cross-taskとerror-matched randomはいずれも27/64で、対応平均差は0だった。通常のcost-matched randomは37/64、移植なしは34/64で、learned cross-taskの27/64を上回った。事前登録したtask-crossing transfer基準は不成立である。

## タスク別結果

| task | learned | error-matched random | learnedのみ成功 | controlのみ成功 | exact McNemar p | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| parity | 10/16 | 8/16 | 4 | 2 | 0.687500 | 1.000000 |
| comparator | 0/16 | 2/16 | 0 | 2 | 0.500000 | 1.000000 |
| mux | 16/16 | 16/16 | 0 | 0 | 1.000000 | 1.000000 |
| carry | 1/16 | 1/16 | 1 | 1 | 1.000000 | 1.000000 |

learned cross-taskはparity 10/16、comparator 0/16、mux 16/16、carry 1/16だった。経路選択muxは全条件16/16で飽和し、構造追加の差を測れない。精密Boolean側ではcomparator/carryへのtask横断再利用は確認できず、E022で増えた難タスク到達は同一task由来Functionへの依存が強かったと解釈するのが妥当である。

error-matched controlの512スロットにおけるlearned Functionとのtruth-table誤差差は平均0.033 bit、中央値0.0、最大2で、完全一致率は97.7%だった。それでも通常のcost-matched randomより成功が少ないため、単体のtarget errorを揃えることは良い踏み石を作る十分条件ではない。error類似Functionへの集中が機能多様性を失わせた可能性がある。

learned条件のexact 27解のうち、移植signatureを最終式に含んだのは3解だけだった。Libraryは固定枠を占めて探索軌跡を変えたものの、多くの解で計算部品として再利用されていない。保存した全125 exact式は64入力で再評価した。

## 結論と次の改善

E022が示したのは同一task・別seedへの部分回路transferであり、E023では別taskへ持ち出せるConceptを確認できなかった。Module Genesisの現在のボトルネックは、Functionを保存することから、複数taskで因果的に役立つFunctionを選ぶことへ移った。

次はsource task名ではなく、Functionが未知のprobe task群で生む改善量をcreditにする。Library slotを占めるだけのFunctionと実際に式へ組み込まれるFunctionを分離し、cross-task offspring utility、機能多様性、費用を同時に最適化する。新しいtask familyをsource選定後に生成し、選定用taskへの過適合も分離する。

## Roadmap

- [Done] target task由来Functionを完全に除外したleave-one-task-out Libraryを4 task別に構成した。
- [Done] 16 seed、256探索でcost-matched random、error-matched oracle random、移植なしを比較した。
- [Done] 平均・不偏分散・bootstrap CI・効果量・exact検定・Holm補正と全125式の再評価を完了した。
- [Done] task-crossing transfer基準は不成立。learnedとprimary controlは27/64で同率、learned Function使用は3/27解だった。
- [Next] 未知probe taskでのoffspring改善を使うcross-task utility creditと、signature多様性制約を追加する。
- [Next] source選定後に固定した新規task familyで、Library selectionへの過適合を測る。
- [Later] task横断再利用が成立してからSTAR-Bit Routerへ統合し、load balance、固定random route、Expert交換、総回路費用を再評価する。

English: Removing every same-task source circuit eliminated the E022 transfer advantage. Learned cross-task Functions and the error-matched random control both solved 27/64 cases, while cost-matched random Functions solved 37/64. Only 3/27 learned-condition solutions actually used a transferred Function. Cross-seed reuse is supported; cross-task conceptual reuse is not.

简体中文：完全排除同任务源电路后，E022的迁移优势消失。跨任务学习函数与误差匹配随机对照均成功27/64，而成本匹配随机函数成功37/64；学习条件中只有3/27个解实际使用了迁移函数。目前支持跨种子复用，但不支持跨任务概念复用。

[事前計画](../results/E023-leave-one-task-out-transfer/PROTOCOL.md) / [生データ](../results/E023-leave-one-task-out-transfer/run/results.json) / [Library](../results/E023-leave-one-task-out-transfer/run/cross_task_libraries.json) / [監査要約](../results/E023-leave-one-task-out-transfer/run/audit_summary.json)
