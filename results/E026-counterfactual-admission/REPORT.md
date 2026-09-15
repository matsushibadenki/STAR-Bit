# E026：Counterfactual Module Admission pilot

実行日：2026-09-15。45 source Functionを、signature-stableな同一tie-breakによる3-round probe探索のwith/without差で評価した。4 probeのうち2つ以上を改善し、net error減少が正の候補だけを採用して、固定保護なしで新規4 seedを評価した。

## Admission結果

45候補中1 Functionだけを採用した。signature `17361640514770759695`、2 primitives、12 routing bits、depth 2。probe error差はmajority +1、exactly-two +2、less-than 0、mixed Boolean 0で、net +3だった。評価taskはadmissionに使っていない。

## 主要結果

| condition | exact / 16 | 成功率平均 | 不偏分散 | threshold2 | threshold4 | equality3 | dual-mux XOR | transfer使用 | best error平均 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_transfer | 4/16 | 0.2500 | 0.2000 | 0/4 | 0/4 | 4/4 | 0/4 | 0 | 2.0625 |
| legacy_all8 | 2/16 | 0.1250 | 0.1167 | 0/4 | 0/4 | 2/4 | 0/4 | 1 | 5.1875 |
| counterfactual | 5/16 | 0.3125 | 0.2292 | 0/4 | 0/4 | 4/4 | 1/4 | 1 | 1.9375 |
| random_matched | 4/16 | 0.2500 | 0.2000 | 0/4 | 0/4 | 4/4 | 0/4 | 0 | 2.3125 |

| paired比較（exact task / seed） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact p |
| --- | ---: | ---: | --- | ---: | ---: |
| counterfactual−legacy（primary） | +0.750 | 0.917 | [0.000, 1.500] | 0.783 | 0.500 |
| counterfactual−no transfer | +0.250 | 0.250 | [0.000, 0.750] | 0.500 | 1.000 |
| counterfactual−random matched | +0.250 | 0.250 | [0.000, 0.750] | 0.500 | 1.000 |

counterfactual admissionはlegacy 2/16から5/16へ改善し、+0.75 task/seedだった。移植なし4/16も下回らず、事前登録した探索阻害mitigation基準を満たした。4 seedのCIは0を含みexact p=0.5なので、確証的な性能改善ではない。

random matchedは4/16でcounterfactualとの差は+0.25に留まり、transfer主張の+0.5基準は未達だった。追加のdual-mux XOR解1件は採用Functionを実際に使用したが単発である。今回支持されるのは、反実仮想screeningが有害な一括admissionを避けたことまでで、task横断Conceptの有効性ではない。

legacyのbest error平均5.1875に対しcounterfactualは1.9375、no transferは2.0625だった。45→1 Functionへの選別が探索軌跡の破壊を抑えた。tie-breakをsignatureごとに決定したため、Library追加で既存候補の乱数順位がずれる問題も除いた。全15 exact式を64入力で再評価した。

タスク別ではequality3がcounterfactual 4/4、legacy 2/4、dual-mux XORが1/4対0/4。threshold2/4は全条件0/4で、この予算では構造自由度の効果を評価できない。

## Roadmap

- [Done] with/without Moduleのpaired probe rolloutとsignature-stable tie-breakを実装した。
- [Done] 45候補を評価し、事前規則で1 Functionだけを通常beamへadmissionした。
- [Done] 新規4 seed・64探索、平均・不偏分散・bootstrap CI・効果量・exact検定・Holm補正、全15式を保存・監査した。
- [Done] legacy一括投入の阻害は緩和したが、random matchedに対するtransfer基準は未達。
- [Next] 同じadmission規則を新規16 seedで独立確認し、randomとの差ではなくまずno-transfer非劣性とlegacy改善を確認する。
- [Next] probeを2〜3段rolloutへ伸ばす場合は、追加計算量と採用安定性を先に測る。
- [Later] cross-task利益が確認された後にState付きFunctionとRouterへ統合する。

English: Counterfactual probe admission selected 1 of 45 Functions and improved held-out discovery from legacy 2/16 to 5/16, versus no-transfer and random-matched 4/16 each. The mitigation criterion passed, but the random-control transfer threshold did not; this supports safe admission, not cross-task conceptual transfer.

简体中文：反事实probe准入从45个函数中只选择1个，使成功数从旧方案2/16提高到5/16；无迁移和随机匹配均为4/16。阻害缓解标准达成，但相对随机对照的迁移标准未达成，因此只支持安全准入，不支持跨任务概念迁移。

[事前計画](../results/E026-counterfactual-admission/PROTOCOL.md) / [生データ](../results/E026-counterfactual-admission/run/results.json) / [Admission](../results/E026-counterfactual-admission/run/admission.json) / [監査要約](../results/E026-counterfactual-admission/run/audit_summary.json)
