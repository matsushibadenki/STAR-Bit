# E051：枝刈りと同一関数の式置換

E049同seed1660–1665・全8task・固定source/randomを再現した回顧的診断。96探索。探索policy変更なし。round3で完全解が見つかった条件は選択処理がないため保持率から除外。有用child＝round2 beam最良より誤差が小さいsignature。

| family | cohort | terminal/24 | 有用child有/非terminal | poolの有用child数 | うちcohort式 | 選択保持signature | 選択保持cohort式 | round4完全解 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| numeric | learned | 12/24 | 0/12 | 0 | 0 | 0 | 0 | 0 |
| numeric | random | 12/24 | 3/12 | 4 | 3 | 4 | 3 | 0 |
| route | learned | 13/24 | 5/11 | 170 | 170 | 0 | 0 | 7 |
| route | random | 13/24 | 11/11 | 847 | 771 | 23 | 16 | 7 |

seed単位保持率は、有用childが存在する非terminal taskだけの条件付き平均。欠損を0とせず、6seed全てに分母がある比較のみ検定し、事前2比較をHolmのfamily sizeに維持。

- numeric:learned/selected_useful_signatures: 分母欠損、推定しない。
- numeric:learned/selected_useful_provenance: 分母欠損、推定しない。
- numeric:random/selected_useful_signatures: 分母欠損、推定しない。
- numeric:random/selected_useful_provenance: 分母欠損、推定しない。
- route:learned/selected_useful_signatures: 分母欠損、推定しない。
- route:learned/selected_useful_provenance: 分母欠損、推定しない。
- route:random/selected_useful_signatures: 平均0.145513、不偏分散0.014935、95% CI [0.062368102236901986, 0.23950461769373455]
- route:random/selected_useful_provenance: 平均0.080637、不偏分散0.003966、95% CI [0.03499214137037509, 0.12692307692307692]
- numeric:learned/useful_signatures count per seed: 平均0.0000、不偏分散0.0000、95% CI [0.0, 0.0]
- numeric:learned/selected_useful_signatures count per seed: 平均0.0000、不偏分散0.0000、95% CI [0.0, 0.0]
- numeric:learned/selected_useful_provenance count per seed: 平均0.0000、不偏分散0.0000、95% CI [0.0, 0.0]
- numeric:random/useful_signatures count per seed: 平均0.6667、不偏分散1.4667、95% CI [0.0, 1.6666666666666667]
- numeric:random/selected_useful_signatures count per seed: 平均0.6667、不偏分散1.4667、95% CI [0.0, 1.6666666666666667]
- numeric:random/selected_useful_provenance count per seed: 平均0.5000、不偏分散0.7000、95% CI [0.0, 1.1666666666666667]
- route:learned/useful_signatures count per seed: 平均28.3333、不偏分散212.6667、95% CI [16.166666666666668, 36.666666666666664]
- route:learned/selected_useful_signatures count per seed: 平均0.0000、不偏分散0.0000、95% CI [0.0, 0.0]
- route:learned/selected_useful_provenance count per seed: 平均0.0000、不偏分散0.0000、95% CI [0.0, 0.0]
- route:random/useful_signatures count per seed: 平均141.1667、不偏分散4280.5667、95% CI [87.33333333333333, 179.33333333333334]
- route:random/selected_useful_signatures count per seed: 平均3.8333、不偏分散0.5667、95% CI [3.3333333333333335, 4.333333333333333]
- route:random/selected_useful_provenance count per seed: 平均2.6667、不偏分散1.4667、95% CI [2.0, 3.6666666666666665]
- learned−random/numeric: 分母欠損、検定しない。
- learned−random/route: 分母欠損、検定しない。

全96探索のE049完全解・誤差・式・費用・初回/round2 beam・入力幅を一致確認。8832選択式を64入力と費用で再評価。実行261.7秒。
cohort式の判定はcohort signatureの構文的出現であり、学習由来の実行provenanceを保証しない。canonical poolは同じ真理値関数の最安式を保持する。保持signatureとcohort式の差を切り分け、完全な二段到達性や物理費用の効果へ拡張しない。

- [Done] 枝刈りとcanonical式の置換を区別して再現診断した。
- [Next] 総beam幅192のままtarget非依存の新規cohort子候補に一段の保持枠を設ける案を、新規calibration seedでbaseline/learned/inert/randomと比較する。固定枠分だけ通常候補が減る費用も含め、確認seedを別にする。
- [Later] State形成/分解、初回負荷分散Router、固定random経路、同一run内→別seed Expert交換。

English: Retrospective pruning diagnosis separates signature retention from canonical expression provenance. Terminal round3 solutions and empty useful-child denominators are explicitly excluded, not imputed.

简体中文：回顾性剪枝诊断区分signature保留与规范表达式来源。第三轮已解条件及无有用子项的分母明确排除，不填零。

結論：非terminal routeのlearned有用child170signatureは全てpoolでcohort式を保持し、選択後は0。ここでは同一関数の安価な式への置換より枝刈りが直接の消失箇所だった。ただし通常候補より価値が高いとは示しておらず、保持枠で精度が改善するかは未検証。numericは非terminal12条件で有用child0。random routeは847中23signature保持、うちcohort式16。learnedの全6seed保持率は分母欠損があり推定/対照検定を行わない。

English: All170 useful learned routing child signatures in nonterminal runs retained cohort syntax in the pool, but none survived selection. This locates loss at pruning, without proving that protecting them improves accuracy. Numeric had no useful learned children in nonterminal runs. Missing seed denominators prevent paired retention inference.

简体中文：未终止路由条件中的170个有用学习子signature在pool中保留cohort表达式，但选择后全部消失。定位到剪枝不代表保护它们会提高准确率。数值未终止条件没有有用学习子项；种子分母缺失，未进行成对保持率推断。
