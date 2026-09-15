# E025：Usage-gated Module Eviction pilot

実行日：2026-09-15。E024の8 Functionを初期投入し、top-128 childのtarget errorを両親より改善したときだけ保護期限を更新するusage-gated evictionを、固定保護・無保護・同費用random・移植なしと新規4 seedで比較した。

## 主要結果

| condition | exact / 16 | 成功率平均 | 不偏分散 | threshold2 | threshold4 | equality3 | dual-mux XOR | round 3保護数 | 最終保護数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_transfer | 5/16 | 0.3125 | 0.2292 | 0/4 | 0/4 | 4/4 | 1/4 | 0.00 | 0.00 |
| fixed_protected | 2/16 | 0.1250 | 0.1167 | 0/4 | 0/4 | 2/4 | 0/4 | 8.00 | 8.00 |
| unprotected | 2/16 | 0.1250 | 0.1167 | 0/4 | 0/4 | 2/4 | 0/4 | 0.00 | 0.00 |
| usage_gated | 2/16 | 0.1250 | 0.1167 | 0/4 | 0/4 | 2/4 | 0/4 | 8.00 | 3.25 |
| random_usage_gated | 1/16 | 0.0625 | 0.0625 | 0/4 | 0/4 | 1/4 | 0/4 | 7.25 | 1.44 |

| paired比較（exact task / seed） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact p |
| --- | ---: | ---: | --- | ---: | ---: |
| usage−fixed（primary） | +0.000 | 0.000 | [0.000, 0.000] | NA | 1.000 |
| usage−no transfer | -0.750 | 0.917 | [-1.500, 0.000] | -0.783 | 0.500 |
| usage−unprotected | +0.000 | 0.000 | [0.000, 0.000] | NA | 1.000 |
| usage−random gated | +0.250 | 0.250 | [0.000, 0.750] | 0.500 | 1.000 |

usage-gated、fixed、unprotectedはいずれも2/16で、primary差は0だった。移植なしは5/16、random usage-gatedは1/16。事前登録したmitigation基準は不成立で、16-seedへ拡張しない。

usage-gatedではround 3時点でも平均8/8 Functionが保護され、最終的には3.25まで減った。全Library Functionが少なくとも一度「改善childの親」になったため、現在のcausal-use判定は識別力がない。遅いevictionは初期3 roundで既に変わったbeam軌跡を回復できなかった。

無保護条件もfixedと同じ2/16だったことから、E024の悪化は固定slotだけでは説明できない。初期Libraryとの大量compositionと、それに伴うtarget quota・credit・乱数選択の変化自体が探索を別のbasinへ移している。Moduleの形成と分解は「使われたか」ではなく、反実仮想的にそのModuleを除いたときの改善差で判断する必要がある。

精密数値側のthreshold2/4は全Library条件0、経路選択を複合したdual-mux XORもLibrary条件0だった。equality3だけ2/4であり、今回も構造追加による一般的補償は確認できない。全12 exact式を64入力で再評価した。

## Roadmap

- [Done] fixed protection、unprotected admission、usage-gated learned、usage-gated random、no-transferを同一予算で比較した。
- [Done] 新規4 seed・80探索、平均・不偏分散・bootstrap CI・効果量・exact検定・Holm補正を保存した。
- [Done] usage判定が8/8 Functionを更新し、evictionが探索性能を回復しない負の結果を確認した。
- [Done] E026でpaired rolloutによるwith/without Moduleの反実仮想admissionとsignature-stable tie-breakを実装した。
- [Next] E026のadmission規則を新規16 seedで独立確認する。
- [Later] 独立確認後にState付きmulti-step utilityへ進み、その後Router統合を再検討する。

English: Usage-gated eviction did not mitigate the fixed-Library harm. Usage-gated, fixed, and unprotected learned admission each solved 2/16 cases versus no-transfer 5/16. Every imported Function produced at least one locally improving child, so the causal-use rule had no selectivity and eviction came too late.

简体中文：按使用情况退役未能缓解固定函数库的负面影响。使用门控、固定保护和无保护学习库均成功2/16，而无迁移成功5/16。每个导入函数都至少生成过一个局部改进子代，因此当前使用判定没有区分力，退役发生得太晚。

[事前計画](../results/E025-usage-gated-eviction/PROTOCOL.md) / [生データ](../results/E025-usage-gated-eviction/run/results.json) / [Library](../results/E025-usage-gated-eviction/run/library.json) / [監査要約](../results/E025-usage-gated-eviction/run/audit_summary.json)
