# E021：Cost-normalized Promotion and Retirement pilot

実行日：2026-09-13。E020のoffspring creditを、task間再利用、composition partner数、primitive・routing・depth費用で正規化し、2 round更新されないcreditを退役させた。新規4 seedを同一seedのraw promotion対照と比較した。

## 主要結果

| condition | exact target平均 | 不偏分散 | parity | comparator | mux | carry | 最終beam内credit付きFunction | credit台帳 | 秒平均 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| raw_promotion | 2.250 | 0.250 | 4/4 | 1/4 | 4/4 | 0/4 | 195.50 | 627.50 | 19.019 |
| normalized_retired | 2.500 | 0.333 | 4/4 | 1/4 | 4/4 | 1/4 | 175.25 | 333.00 | 17.966 |

| paired指標（normalized−raw） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| --- | ---: | ---: | --- | ---: | ---: |
| exact targets | +0.250 | 0.250 | [0.000, 0.750] | 0.500 | 1.000 |
| 最終beam内credit付きFunction | -20.250 | 10.917 | [-23.250, -18.000] | -6.129 | 0.125 |
| credit台帳 | -294.500 | 73.000 | [-302.500, -289.000] | -34.469 | 0.125 |
| 実行秒 | -1.053 | 0.032 | [-1.176, -0.879] | -5.868 | 0.125 |

credit台帳は平均46.9%縮小し、実行時間は5.5%短縮した。exact target平均は2.25から2.50へ低下せず、seed 1282でcarryを初めて発見した。一方、事前登録した主指標の『最終beam内credit付きFunctionを30%以上削減』は10.4%削減に留まり、総合viability判定は不成立だった。target別上位枠にcredit済みFunctionが再流入するため、promotion専用枠を64へ減らしても最終beamのcredit付き総数は64に制限されない。

4 seedのpilotでexact targets差は[0, 0, 1, 0]、exact sign-flip p=1.000であり、carry 1/4は発見事実であって再現性の証拠ではない。多重検定を伴う確証的主張は行わない。

## 発見回路と構造費用

normalized_retiredのcarryはseed 1282・round 8で15 primitives、106 routing bits、depth 7だった。comparatorはseed 1283でrawの16 primitives・114 bitsから13 primitives・92 bitsへ改善し、同じround 7で到達した。parityは全seed、muxも全seedで完全一致した。保存した全expressionをtruth table全64行で再評価し、全19解を検証した。

carry到達は、古いcreditを捨てることが単なる省メモリ化ではなく、beamの競合を変えて新しい探索経路を開く場合があることを示す。ただし条件差には正規化、枠数、退役の三要因が含まれるため、どの要因がcarryに寄与したかはまだ分離できない。

## 判定と次段階

E021はarchive台帳と時間を減らしながら探索性能を維持したが、事前登録した最終beam 30%削減基準を満たさなかった。したがって『効率的な自律Module Genesisが成立した』とは判定しない。carryが少なくとも1 seedで見つかったため、事前計画どおり次は発見Functionの固定移植を16 seedで評価できる。移植元と評価先を分離し、同一run由来、別seed由来、ランダム同費用Functionを比較して、学習された中間Functionの効果を分離する。

## Roadmap

- [Done] creditをtask再利用と構造費用で正規化し、stale credit retirementを実装した。
- [Done] 新規4 seedの対応比較で平均・不偏分散・bootstrap CI・効果量・exact sign-flip検定を報告した。
- [Done] carry exactを初めて1/4 seedで発見し、全19回路を64入力で再検証した。
- [Done] E022で移植元と評価seedを分離し、学習Function対ランダム同費用Functionを16 seedで比較した。
- [Next] promotion枠由来とtarget枠への再流入を別々に記録し、正規化・枠数・retirementの要因を分解する。
- [Next] E022の同一task transferを、target task由来Functionを除くleave-one-task-out条件へ進める。
- [Later] task横断transfer後にFunctionを固定Moduleへ昇格し、別タスク学習step、総記述bit、primitive実行数を測る。

English: Cost normalization and retirement reduced the credit registry by 46.9% and runtime by 5.5% without lowering mean target discovery. Carry was found for the first time in one of four seeds, but the preregistered 30% reduction in credited functions remaining in the final beam was not met, and the pilot is too small for a confirmatory claim.

简体中文：成本归一化与退役机制使credit台账缩小46.9%，运行时间缩短5.5%，且平均目标发现数没有下降。首次在4个种子中的1个找到carry，但最终beam内带credit函数减少30%的预注册标准未达成，因此不能作确认性结论。

[事前計画](../results/E021-cost-normalized-promotion/PROTOCOL.md) / [生データ](../results/E021-cost-normalized-promotion/run/results.json) / [監査要約](../results/E021-cost-normalized-promotion/run/audit_summary.json)
