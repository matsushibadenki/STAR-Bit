# E027：Counterfactual Module Admission 独立確認

実行日：2026-09-16。E026で45候補から選ばれた1 Functionを再選別せず凍結し、新規16 seedで事前登録どおり独立確認した。4条件 × 4 held-out task × 16 seedの256探索を、beam 128・6 rounds・保護slotなしで実行した。

## 結果

| condition | exact / 64 | 成功率平均 | 不偏分散 | threshold2 | threshold4 | equality3 | dual-mux XOR | transfer使用 | best error平均 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_transfer | 20/64 | 0.3125 | 0.2183 | 3/16 | 0/16 | 16/16 | 1/16 | 0 | 1.9844 |
| legacy_all8 | 4/64 | 0.0625 | 0.0595 | 0/16 | 0/16 | 4/16 | 0/16 | 2 | 5.2969 |
| counterfactual | 22/64 | 0.3438 | 0.2292 | 2/16 | 0/16 | 16/16 | 4/16 | 5 | 1.9531 |
| random_matched | 17/64 | 0.2656 | 0.1982 | 1/16 | 0/16 | 16/16 | 0/16 | 0 | 2.0781 |

| paired比較（exact task / seed） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| --- | ---: | ---: | --- | ---: | ---: |
| counterfactual−legacy（primary） | +1.1250 | 0.6500 | [0.7500, 1.5000] | 1.395 | 0.0002 |
| counterfactual−no transfer | +0.1250 | 0.3833 | [-0.1875, 0.4375] | 0.202 | 0.6875 |
| counterfactual−random matched | +0.3125 | 0.2292 | [0.1250, 0.5625] | 0.653 | 0.0625 |

counterfactualは22/64、legacy一括投入は4/64で、primary差は+1.1250 task/seed、95% CI [0.7500, 1.5000]だった。no-transfer 20/64も下回らなかったため、事前登録した探索阻害mitigation基準を満たした。E026の小標本結果は独立seedで再現した。

random matchedは17/64で、counterfactual差は+0.3125 task/seed、95% CI [0.1250, 0.5625]だった。dual-mux XORではcounterfactualだけが成功した4 seedすべてで凍結Functionを実際に使用した。事前登録したtask-crossing transfer基準も満たした。ただしexact sign-flip p=0.0625、task別McNemarのHolm補正後pは有意でないため、確認された範囲はこの小型Boolean探索と固定予算に限られる。

## タスク種別

経路選択型のdual-mux XORはcounterfactual 4/16、random 0/16、no-transfer 1/16で、4件のlearned-only解がすべて転移Functionを使った。構造的自由度が探索到達性を改善したという今回の証拠は、この経路選択タスクに集中した。

精密数値型のthreshold2は2/16対random 1/16・no-transfer 3/16、threshold4は全条件0/16だった。equality3はcounterfactual・random・no-transferが全て16/16で天井効果があり、転移効果を分離できない。したがって、数値タスクへの一般化は支持されず、難しいthreshold4は現予算では評価不能である。

全63 exact式を64入力で再評価し、source hash、凍結Functionのsignatureとexpression、256 recordを監査した。結果は記述長圧縮、primitive gate削減、実行速度、Router学習の証拠ではない。

## Roadmap

- [Done] E026の採用Functionを凍結し、独立16 seed・256探索を完了した。
- [Done] counterfactual admissionによるlegacy Libraryの探索阻害緩和を独立確認した。
- [Done] random matched対照と実使用監査により、経路選択型dual-mux XORで事前登録したtask-crossing transfer基準を満たした。
- [Done] 平均・不偏分散・bootstrap CI・Cohen dz・exact sign-flip・task別McNemar/Holm、全exact式とsource hashを監査した。
- [Next] E028では選ばれたFunctionを直接使えない等価保持ablationと、admission Functionの入力置換対照を追加し、特定式の偶然ではなく構造的部分計算の寄与を分離する。
- [Next] threshold4の探索予算を事前に校正し、数値型で床効果のない比較を行う。
- [Later] transfer Function候補をRouterの選択肢として統合し、step 0 load-balancing・固定random routing・複数seedでSTAR-Bit本体を検証する。

English: With the E026 Function frozen, counterfactual admission reached 22/64 exact solutions versus legacy 4/64, no-transfer 20/64, and structurally matched random 17/64 over 16 new seeds. Both preregistered mitigation and task-crossing transfer criteria passed. The learned-only benefit was concentrated in dual-mux XOR (4/16 versus random 0/16), while numeric thresholds showed no benefit.

简体中文：冻结E026选出的函数后，16个新seed中反事实准入达到22/64，旧Library为4/64，无迁移为20/64，结构匹配随机对照为17/64。预注册的阻害缓解与跨任务迁移标准均达成；增益集中在dual-mux XOR路径选择任务，数值阈值任务没有显示收益。

[事前計画](../results/E027-counterfactual-admission-confirmation/PROTOCOL.md) / [生データ](../results/E027-counterfactual-admission-confirmation/run/results.json) / [凍結Admission](../results/E027-counterfactual-admission-confirmation/run/frozen_admission.json) / [監査要約](../results/E027-counterfactual-admission-confirmation/run/audit_summary.json)
