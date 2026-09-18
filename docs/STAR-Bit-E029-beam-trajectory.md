# E029：Libraryが変えるBeam探索軌跡

実行日：2026-09-18。E026の採用FunctionとE028の入力+1置換を凍結し、新規16 seed × 2 task × 3条件の96探索を実施した。E026のbeam selectionを戻り値不変のwrapperで観測し、候補signature、Function credit、partner数、直接子候補を保存した。

## Exact到達とタスク別統計

| task | condition | exact /16 | 成功率平均 | 不偏分散 | best error平均 | 時間平均秒 | 最終式のFunction使用 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| eval_dual_mux_xor | no_transfer | 2/16 | 0.1250 | 0.1167 | 3.3750 | 2.760 | 0 |
| eval_dual_mux_xor | admitted | 4/16 | 0.2500 | 0.2000 | 3.1875 | 2.727 | 4 |
| eval_dual_mux_xor | rotate1 | 3/16 | 0.1875 | 0.1625 | 2.6250 | 2.825 | 0 |
| eval_threshold2 | no_transfer | 2/16 | 0.1250 | 0.1167 | 0.8750 | 2.651 | 0 |
| eval_threshold2 | admitted | 0/16 | 0.0000 | 0.0000 | 1.0000 | 2.841 | 0 |
| eval_threshold2 | rotate1 | 1/16 | 0.0625 | 0.0625 | 0.9375 | 2.817 | 1 |

成功解だけのtree cost平均（primitive / routing bits / depth）：

- eval_dual_mux_xor / no_transfer: 8.00 / 54.00 / 4.00。
- eval_dual_mux_xor / admitted: 9.00 / 62.00 / 6.00。
- eval_dual_mux_xor / rotate1: 15.00 / 102.00 / 5.00。
- eval_threshold2 / no_transfer: 15.00 / 108.00 / 5.00。
- eval_threshold2 / admitted: NA。
- eval_threshold2 / rotate1: 16.00 / 112.00 / 7.00。

| paired exact/seed | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| --- | ---: | ---: | --- | ---: | ---: |
| eval_dual_mux_xor: rotate1−no_transfer | +0.0625 | 0.3292 | [-0.1875, 0.3125] | 0.109 | 1.0000 |
| eval_dual_mux_xor: admitted−no_transfer | +0.1250 | 0.3833 | [-0.1875, 0.4375] | 0.202 | 0.6875 |
| eval_dual_mux_xor: admitted−rotate1 | +0.0625 | 0.3292 | [-0.1875, 0.3125] | 0.109 | 1.0000 |
| eval_threshold2: rotate1−no_transfer | -0.0625 | 0.1958 | [-0.2500, 0.1250] | -0.141 | 1.0000 |
| eval_threshold2: admitted−no_transfer | -0.1250 | 0.1167 | [-0.3125, 0.0000] | -0.366 | 0.5000 |
| eval_threshold2: admitted−rotate1 | -0.0625 | 0.0625 | [-0.1875, 0.0000] | -0.250 | 1.0000 |

## 事前指定した探索軌跡の指標

事前指定した予備的な探索軌跡witness基準（3件以上）を満たした。
rotate1-onlyのdual-mux exactは3件。そのうち最終式にrotate1 Functionがなく、round 1でrotate1条件のbeamにのみ残ったsignatureを最終式の祖先に持つものは3件。直接ペア生成したsignatureが祖先だったのは3件。
直接子祖先とは、Functionとのペア出力として生成可能で、かつno-transferのround-1 beamにはなかったsignatureを指す。同じsignatureは別経路からも生成できるため、これはtrajectoryの観測証人であり厳密な媒介効果の同定ではない。
- seed 1412: 最終Function使用=False、round1固有祖先=2、直接子祖先=2、beam Jaccard=0.8551。
- seed 1414: 最終Function使用=False、round1固有祖先=2、直接子祖先=2、beam Jaccard=0.8417。
- seed 1420: 最終Function使用=False、round1固有祖先=2、直接子祖先=2、beam Jaccard=0.8551。

roundごとのno-transferとのbeam Jaccard平均（比較可能なseedのみ）：

- eval_dual_mux_xor / admitted: r1=0.820 (n=16)、r2=0.603 (n=16)、r3=0.379 (n=16)、r4=0.327 (n=10)、r5=0.326 (n=10)、r6=0.327 (n=10)。
- eval_dual_mux_xor / rotate1: r1=0.845 (n=16)、r2=0.621 (n=16)、r3=0.465 (n=16)、r4=0.452 (n=14)、r5=0.423 (n=11)、r6=0.410 (n=11)。
- eval_threshold2 / admitted: r1=0.612 (n=16)、r2=0.452 (n=16)、r3=0.375 (n=16)、r4=0.381 (n=16)、r5=0.406 (n=14)、r6=0.425 (n=14)。
- eval_threshold2 / rotate1: r1=0.613 (n=16)、r2=0.455 (n=16)、r3=0.378 (n=16)、r4=0.379 (n=16)、r5=0.408 (n=13)、r6=0.427 (n=13)。

## creditと多重比較

- eval_dual_mux_xor / admitted: round1 credit平均 54.00、partner平均 4.00、Function生存 16/16、直接子beam保持平均 23.88。
- eval_dual_mux_xor / rotate1: round1 credit平均 30.00、partner平均 3.00、Function生存 16/16、直接子beam保持平均 23.44。
- eval_threshold2 / admitted: round1 credit平均 572.00、partner平均 7.00、Function生存 16/16、直接子beam保持平均 37.12。
- eval_threshold2 / rotate1: round1 credit平均 572.00、partner平均 7.00、Function生存 16/16、直接子beam保持平均 37.25。
- eval_dual_mux_xor: rotate1 vs no_transfer、left-only 3、right-only 2、exact McNemar p=1.0000、Holm p=1.0000。
- eval_dual_mux_xor: admitted vs no_transfer、left-only 4、right-only 2、exact McNemar p=0.6875、Holm p=1.0000。
- eval_dual_mux_xor: admitted vs rotate1、left-only 3、right-only 2、exact McNemar p=1.0000、Holm p=1.0000。
- eval_threshold2: rotate1 vs no_transfer、left-only 1、right-only 2、exact McNemar p=1.0000、Holm p=1.0000。
- eval_threshold2: admitted vs no_transfer、left-only 0、right-only 2、exact McNemar p=0.5000、Holm p=1.0000。
- eval_threshold2: admitted vs rotate1、left-only 0、right-only 1、exact McNemar p=1.0000、Holm p=1.0000。

全12 exact式を64入力で再評価し、96 record、凍結Function、費用一致、source hash、wrapperの事前smoke一致を監査した。これは固定予算のBoolean探索であり、学習抽象化・実gate数・実測速度・Routerの効果は示さない。

## Roadmap

- [Done] E026の選択関数を変更せずbeam/credit/親候補のsignature単位トレースを実装した。
- [Done] 16新規seed・96探索とpaired統計、Holm補正、全exact式、source hashを監査した。
- [Next] 祖先signatureの再生成経路を追跡し、Library由来と独立生成を識別するprovenance付き探索を検討する。
- [Later] 複数の経路選択task familyと床効果のない数値taskを比較し、十分な証拠が得られてからRouter統合へ進む。

English: On 16 fresh seeds, dual-mux XOR solved 2/16 without transfer, 4/16 with the admitted Function, and 3/16 with its input rotation; paired exact differences were not significant. All three rotation-only solutions omitted the rotated Function yet contained first-round beam signatures absent without transfer and compatible with direct offspring. This supports a preliminary trajectory witness, not causal provenance or a performance claim.

简体中文：16个新seed的dual-mux XOR结果为无迁移2/16、原函数4/16、输入旋转3/16；配对成功率差异不显著。3个仅旋转条件成功的电路都未使用旋转函数，却包含无迁移条件首轮beam所没有、且可由该函数直接生成的中间签名。这是初步轨迹证据，并非因果来源或性能优势的证明。

[事前計画](../results/E029-beam-trajectory/PROTOCOL.md) / [生データ](../results/E029-beam-trajectory/run/results.json) / [凍結Library](../results/E029-beam-trajectory/run/frozen_library.json) / [監査要約](../results/E029-beam-trajectory/run/audit_summary.json)
