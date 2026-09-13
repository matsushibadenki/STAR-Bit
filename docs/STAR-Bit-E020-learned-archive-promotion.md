# E020：Learned Archive Promotion pilot

実行日：2026-09-13。E019の人手指定affine scaffoldを外し、探索中に良い子Functionを生成した親signatureへcreditを与えてarchive内で昇格させた。target-greedyと同じbeam・round・LUT生成予算で4 seed比較した。

## 主要結果

| condition | exact target平均 | 不偏分散 | parity | comparator | mux | carry | 秒平均 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| target_greedy | 1.000 | 0.000 | 0/4 | 0/4 | 4/4 | 0/4 | 3.237 |
| offspring_promotion | 2.250 | 0.250 | 3/4 | 2/4 | 4/4 | 0/4 | 26.432 |

| promotion−greedy | 差の分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| ---: | ---: | --- | ---: | ---: |
| +1.250 | 0.250 | [1.000, 1.750] | 2.500 | 0.125 |

pilotの4 seedなので検定はconfirmatory evidenceとして扱わない。promotionはexact target平均を1.00から2.25へ増やし、target-greedyで0/4だったcomparatorを2/4、parityを3/4まで回復した。carryは0/4で、事前の全4 target基準は未達。

## 自動昇格で形成された回路

comparatorはseed1260でround 7・16 primitives・routing 114 bits・depth 6、seed1262でround 5・15 primitives・108 bits・depth 5として発見された。parityは3 seedで発見されたが5–7 primitivesを要し、E019のaffine scaffoldによる5-primitive安定解より不安定だった。muxは全条件でround 2・3 primitives。

各seedで626–652個の親signatureがcreditを受け、最終beamには182–194個のpromoted Functionが残った。creditは、子が両親よりtarget errorを改善した量、非定数のままdependency supportを増やした量、異なるpartnerとのcomposition数から得る。named function familyや中間教師は使用していない。

## 解釈

手指定のaffine族がなくても、offspringへの実測寄与を使うとparityに加えて初めてcomparatorへ到達した。これは「今の出力精度」以外の中間Function価値が探索到達性を変える二つ目の肯定例であり、E019より自律的なModule Genesisに近い。

一方でpromotionは探索時間を平均3.24秒から26.43秒へ増やし、carryを形成できなかった。creditが大量のsupport拡張へ分散し、Libraryが肥大化している。自律Module形成の成立や計算効率改善はまだ主張できない。

## Roadmap

- [Done] affine function族を指定せず、offspring寄与から親Functionを自動昇格した。
- [Done] comparator exactをtarget-greedy 0/4から2/4、parityを0/4から3/4へ改善した。
- [Done] 平均・不偏分散・bootstrap CI・効果量・pilot検定、全expression、source hashを保存した。
- [Next] creditを総量ではなくtask間再利用と費用で正規化し、archive上限とretirementを導入する。
- [Next] carry向けにState付き逐次compositionを追加し、同じpromotion規則で精密数値対経路選択を比較する。
- [Later] 全4 target exact後にFunctionをModuleへ昇格し、別seed/taskへ固定移植して探索stepと総記述bitを測る。

English: Learned offspring credit, without a hand-selected function family, increased exact targets from 1.00 to 2.25 and discovered comparator circuits in 2/4 seeds. Runtime increased substantially and carry remained unsolved, so autonomous Module Genesis is promising but not established.

简体中文：无需人工指定函数族，基于子代贡献的自动晋升将精确目标数从1.00提高到2.25，并在2/4种子中发现comparator电路。运行时间明显增加，carry仍未解决，因此自主模块生成尚未成立。

[事前計画](../results/E020-learned-archive-promotion/PROTOCOL.md) / [生データ](../results/E020-learned-archive-promotion/run/results.json)
