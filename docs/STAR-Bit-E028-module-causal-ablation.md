# E028：転移Functionの直接寄与と入力意味のAblation

実行日：2026-09-17。E027で採用した2-gate Functionを凍結し、16新規seed × 経路選択／数値各1 task × 5条件の160探索を事前登録どおり実施した。inert条件は同じFunctionをbeamに置く一方、そのtruth-table signatureを親とするcompositionだけを禁止する。rotate1/2は入力indexを巡回置換し、gate種・式木・primitive/routing/depth費用を維持する。

## Exact到達

| condition | dual-mux XOR /16 | threshold2 /16 | 全32例の平均 | 不偏分散 | transfer使用 | best error平均 | 時間平均秒 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_transfer | 2/16 | 1/16 | 0.0938 | 0.0877 | 0 | 2.0938 | 2.737 |
| admitted | 4/16 | 0/16 | 0.1250 | 0.1129 | 4 | 2.1250 | 2.791 |
| inert_signature | 2/16 | 1/16 | 0.0938 | 0.0877 | 0 | 2.0938 | 2.739 |
| rotate1 | 4/16 | 1/16 | 0.1562 | 0.1361 | 0 | 1.6250 | 2.789 |
| rotate2 | 0/16 | 1/16 | 0.0312 | 0.0312 | 1 | 2.5625 | 2.927 |

各taskのexact成功率、不偏分散、成功解だけのtree cost（primitive / routing bits / depth）を分けて示す。

| task | condition | 成功率平均 | 不偏分散 | 解cost平均 |
| --- | --- | ---: | ---: | --- |
| eval_dual_mux_xor | no_transfer | 0.1250 | 0.1167 | 8.50 / 57.00 / 4.00 |
| eval_dual_mux_xor | admitted | 0.2500 | 0.2000 | 9.00 / 62.00 / 6.00 |
| eval_dual_mux_xor | inert_signature | 0.1250 | 0.1167 | 8.50 / 57.00 / 4.00 |
| eval_dual_mux_xor | rotate1 | 0.2500 | 0.2000 | 15.00 / 102.00 / 5.00 |
| eval_dual_mux_xor | rotate2 | 0.0000 | 0.0000 | NA |
| eval_threshold2 | no_transfer | 0.0625 | 0.0625 | 15.00 / 108.00 / 5.00 |
| eval_threshold2 | admitted | 0.0000 | 0.0000 | NA |
| eval_threshold2 | inert_signature | 0.0625 | 0.0625 | 15.00 / 108.00 / 5.00 |
| eval_threshold2 | rotate1 | 0.0625 | 0.0625 | 15.00 / 108.00 / 5.00 |
| eval_threshold2 | rotate2 | 0.0625 | 0.0625 | 16.00 / 114.00 / 7.00 |

| task / admittedとの差 | 平均 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| --- | ---: | ---: | --- | ---: | ---: |
| eval_dual_mux_xor − inert_signature | +0.1250 | 0.2500 | [-0.1250, 0.3750] | 0.250 | 0.6250 |
| eval_dual_mux_xor − rotate1 | +0.0000 | 0.2667 | [-0.2500, 0.2500] | 0.000 | 1.0000 |
| eval_dual_mux_xor − rotate2 | +0.2500 | 0.2000 | [0.0625, 0.5000] | 0.559 | 0.1250 |
| eval_dual_mux_xor − no_transfer | +0.1250 | 0.2500 | [-0.1250, 0.3750] | 0.250 | 0.6250 |
| eval_threshold2 − inert_signature | -0.0625 | 0.0625 | [-0.1875, 0.0000] | -0.250 | 1.0000 |
| eval_threshold2 − rotate1 | -0.0625 | 0.0625 | [-0.1875, 0.0000] | -0.250 | 1.0000 |
| eval_threshold2 − rotate2 | -0.0625 | 0.0625 | [-0.1875, 0.0000] | -0.250 | 1.0000 |
| eval_threshold2 − no_transfer | -0.0625 | 0.0625 | [-0.1875, 0.0000] | -0.250 | 1.0000 |

## 判定

経路選択taskのadmitted−inertは事前登録した直接composition基準を満たさなかった。beam内の占有／選択軌跡変化とFunctionの直接再利用をまだ分離できない。
primary差は+0.1250 exact/seed、95% CI [-0.1250, 0.3750]、exact p=0.6250。admitted-onlyは3 seed、そのうち凍結signatureを最終式に含むものは3件。
inert条件はLibraryの候補だけでなく、探索中に同じsignatureを再生成した場合もその親利用を禁止する。最終式のsignature使用は機能的な再利用を示すが、その節点がLibraryから来たのか独立合成されたのかは識別しない。
inertとno-transferは32/32 caseでexact成否、到達round、best-error履歴、最終式が一致した。生成signature数は初期候補1個の差があるため一致しない。今回のinert候補は探索結果を変えなかったが、admittedとの対応差は統計的に確証されていない。
rotate1はdual-mux XORでadmittedと同じ4/16に到達したが、4解とも置換Functionを最終式に含まなかった。固定Functionが直接部品になる経路と、Library追加によってbeam／creditの軌跡が変わる経路を分ける必要がある。

構造同費用の入力置換対照と比較すると、関数の入力配置・truth-table意味の違いを調べられる。ただし2置換だけでBoolean機能族全体の一般性は結論できない。各Functionの評価taskに対する64行Hamming errorは次のとおり。

- eval_dual_mux_xor: admitted 32、rotate1 32、rotate2 32。
- eval_threshold2: admitted 33、rotate1 33、rotate2 33。

task別のexact McNemar検定はinert／rotate1／rotate2の3比較でHolm補正した。

- eval_dual_mux_xor vs inert_signature: admitted-only 3、対照only 1、p=0.6250、Holm p=1.0000。
- eval_dual_mux_xor vs rotate1: admitted-only 2、対照only 2、p=1.0000、Holm p=1.0000。
- eval_dual_mux_xor vs rotate2: admitted-only 4、対照only 0、p=0.1250、Holm p=0.3750。
- eval_threshold2 vs inert_signature: admitted-only 0、対照only 1、p=1.0000、Holm p=1.0000。
- eval_threshold2 vs rotate1: admitted-only 0、対照only 1、p=1.0000、Holm p=1.0000。
- eval_threshold2 vs rotate2: admitted-only 0、対照only 1、p=1.0000、Holm p=1.0000。

全16 exact式を64入力で再評価し、160 record、source hash、費用が一致する入力置換式、inert解に凍結signatureが含まれないことを監査した。Function Libraryを入れた探索の到達性であり、記述長・実gate数・実行速度・Router学習の証拠ではない。

rotate2の成功解は1件だけで、不偏分散は定義できない。実行時の非標準JSON `NaN` を元ファイル `results.original.json` に保存し、正規化版 `results.json` では該当箇所だけ `null` にした。[正規化記録](../results/E028-module-causal-ablation/run/normalization.json)。個別探索recordは変更していない。

## Roadmap

- [Done] 凍結Functionの直接composition禁止と、同じ2-gate構造の2つの入力巡回置換を実装した。
- [Done] 新規16 seed・160探索、paired統計、Holm補正、全exact式とsource hash監査を完了した。
- [Next] beam候補の生存・credit・親利用をsignature単位で記録し、rotate1の「最終式で未使用なのに成功」を追跡する。
- [Next] 入力配置以外の意味対照を事前固定し、Functionの可搬性を複数の経路選択task familyで確認する。
- [Later] 数値taskの床効果を校正し、State付きFunctionとRouterへ統合する。

English: On dual-mux XOR, admitted Function search solved 4/16 versus inert composition 2/16, but the paired effect failed the preregistered criterion (CI [-0.125, 0.375], exact p=0.625). An input-rotated Function also solved 4/16 despite appearing in none of its final circuits. Thus E027 remains a narrow transfer signal; direct reusable-Module causality is not established.

简体中文：dual-mux XOR中原函数成功4/16，禁止直接组合后为2/16，但配对差未达到预注册标准（置信区间[-0.125, 0.375]，精确p=0.625）。输入旋转函数也成功4/16，却未出现在任何最终电路中。因此E027仍是范围有限的迁移信号，尚未证实可复用模块的直接因果作用。

[事前計画](../results/E028-module-causal-ablation/PROTOCOL.md) / [生データ](../results/E028-module-causal-ablation/run/results.json) / [凍結Library](../results/E028-module-causal-ablation/run/frozen_library.json) / [監査要約](../results/E028-module-causal-ablation/run/audit_summary.json)
