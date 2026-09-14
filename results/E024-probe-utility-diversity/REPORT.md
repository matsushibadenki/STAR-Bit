# E024：Probe Utility and Function Diversity pilot

実行日：2026-09-14。E023で失敗したsource頻度・target errorに代えて、選定に使わない4 probe taskでの一段composition改善とtruth-signature多様性から8 Functionを選んだ。選定後に固定した別の4 evaluation task、4 seed、5条件の80探索で評価した。

## 主要結果

| condition | exact / 16 | 成功率平均 | 不偏分散 | threshold2 | threshold4 | equality3 | dual-mux XOR | transfer使用 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_transfer | 7/16 | 0.4375 | 0.2625 | 2/4 | 0/4 | 4/4 | 1/4 | 0 |
| frequency_cost | 1/16 | 0.0625 | 0.0625 | 0/4 | 0/4 | 1/4 | 0/4 | 0 |
| probe_utility | 0/16 | 0.0000 | 0.0000 | 0/4 | 0/4 | 0/4 | 0/4 | 0 |
| probe_utility_diverse | 1/16 | 0.0625 | 0.0625 | 0/4 | 0/4 | 1/4 | 0/4 | 1 |
| random_matched | 2/16 | 0.1250 | 0.1167 | 0/4 | 0/4 | 2/4 | 0/4 | 1 |

| paired比較（exact task / seed） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact p |
| --- | ---: | ---: | --- | ---: | ---: |
| utility-diverse−random（primary） | -0.250 | 0.250 | [-0.750, 0.000] | -0.500 | 1.000 |
| utility-diverse−frequency | +0.000 | 0.000 | [0.000, 0.000] | NA | 1.000 |
| utility-diverse−no transfer | -1.500 | 1.667 | [-2.500, -0.500] | -1.162 | 0.250 |

probe utilityだけは0/16、diversity併用は1/16、同費用randomは2/16、source頻度は1/16、移植なしは7/16だった。primary差は−0.25 task/seedで、事前の16-seed移行基準を満たさなかった。成功するまでseedを追加せず停止した。

utility Libraryの平均probe scoreは1.173、diversity併用も1.173だった。平均pairwise Hamming距離はutility 26.79 bitからdiverse 29.86 bitへ増えたが、新規task探索へ移らなかった。したがって一段先のprobe改善と静的signature距離もcompositional potentialの十分な代理ではない。

固定Libraryはbeam 128の8枠を占める。全Library条件が移植なしより悪化したため、選ばれたFunctionが有用でない場合、保護枠と初期compositionが探索を阻害することも確認された。utility-diverseの唯一のexact解は移植Functionを使用したが、randomにも2解あり、肯定的な一般化証拠にはならない。

## タスク軸

threshold4は全条件0/4で、この予算では難しすぎた。equality3は移植なし4/4に対しutility-diverse 1/4、random 2/4。dual-mux XORは移植なしだけ1/4だった。今回の新規familyでは、構造自由度を加えること自体が精密数値・経路選択のどちらにも利益を与えなかった。

## Roadmap

- [Done] probe taskとevaluation taskを選定前に分離し、一段offspring utilityとsignature多様性を実装した。
- [Done] 4 seed、80探索、同費用random・frequency・no-transfer対照と平均・分散・CI・効果量・exact検定を保存した。
- [Done] 16-seed移行基準は不成立。全11 exact式を64入力で再検証した。
- [Next] 固定保護枠を廃止し、Moduleが実際に使われた場合だけ存続するusage-gated evictionを比較する。
- [Next] 一段lookaheadを止め、2〜3段のrollout utilityまたはState付き逐次utilityを小規模に診断する。
- [Later] cross-family transfer成立後にRouterへ統合し、load balance、固定random route、Expert交換、総費用を再評価する。

English: One-step probe utility plus signature diversity did not transfer to four held-out task definitions. Utility-diverse solved 1/16 cases versus random 2/16 and no-transfer 7/16, so the preregistered expansion gate failed. Protected Library slots can actively harm search when Modules are not useful.

简体中文：一步probe效用加签名多样性未能迁移到四个保留任务。效用加多样性成功1/16，随机库2/16，无迁移7/16，因此未达到扩展实验标准。无用模块占用固定保护槽会主动损害搜索。

[事前計画](../results/E024-probe-utility-diversity/PROTOCOL.md) / [生データ](../results/E024-probe-utility-diversity/run/results.json) / [Library](../results/E024-probe-utility-diversity/run/libraries.json) / [監査要約](../results/E024-probe-utility-diversity/run/audit_summary.json)
