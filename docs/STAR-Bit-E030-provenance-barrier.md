# E030：Function由来Signatureの置換と伝播Barrier

実行日：2026-09-20。E026の採用Functionを入力+1置換した固定Functionについて、新規16 seed × 経路選択／数値各1 task × 3条件の96探索を実施した。one-hop barrierはround 1の子生成を許し、round 2以降はFunctionを式木に含む候補を親として使わない。同じsignatureを持つFunction-free式は利用できる。

## 結果

| task | condition | exact /16 | 成功率平均 | 不偏分散 | best error平均 | 時間平均秒 | Function使用 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| eval_dual_mux_xor | no_transfer | 1/16 | 0.0625 | 0.0625 | 3.7500 | 2.980 | 0 |
| eval_dual_mux_xor | rotate1 | 3/16 | 0.1875 | 0.1625 | 2.8125 | 2.874 | 0 |
| eval_dual_mux_xor | one_hop_barrier | 3/16 | 0.1875 | 0.1625 | 3.2500 | 2.702 | 0 |
| eval_threshold2 | no_transfer | 1/16 | 0.0625 | 0.0625 | 0.9375 | 2.813 | 0 |
| eval_threshold2 | rotate1 | 2/16 | 0.1250 | 0.1167 | 0.8750 | 2.920 | 0 |
| eval_threshold2 | one_hop_barrier | 0/16 | 0.0000 | 0.0000 | 1.0000 | 2.847 | 0 |

成功解のtree cost平均（primitive / routing bits / depth）：

- eval_dual_mux_xor / no_transfer: 8.00 / 54.00 / 4.00。
- eval_dual_mux_xor / rotate1: 12.33 / 84.00 / 4.67。
- eval_dual_mux_xor / one_hop_barrier: 7.67 / 52.00 / 4.00。
- eval_threshold2 / no_transfer: 15.00 / 108.00 / 5.00。
- eval_threshold2 / rotate1: 16.00 / 114.00 / 6.00。
- eval_threshold2 / one_hop_barrier: NA。

| paired exact/seed | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| --- | ---: | ---: | --- | ---: | ---: |
| eval_dual_mux_xor: rotate1−one_hop_barrier | +0.0000 | 0.2667 | [-0.2500, 0.2500] | 0.000 | 1.0000 |
| eval_dual_mux_xor: rotate1−no_transfer | +0.1250 | 0.2500 | [-0.1250, 0.3750] | 0.250 | 0.6250 |
| eval_dual_mux_xor: one_hop_barrier−no_transfer | +0.1250 | 0.1167 | [0.0000, 0.3125] | 0.366 | 0.5000 |
| eval_threshold2: rotate1−one_hop_barrier | +0.1250 | 0.1167 | [0.0000, 0.3125] | 0.366 | 0.5000 |
| eval_threshold2: rotate1−no_transfer | +0.0625 | 0.1958 | [-0.1250, 0.2500] | 0.141 | 1.0000 |
| eval_threshold2: one_hop_barrier−no_transfer | -0.0625 | 0.0625 | [-0.1875, 0.0000] | -0.250 | 1.0000 |

## 事前判定とProvenance

事前登録したFunction-descendant伝播基準は満たさなかった。
primaryのrotate1−one-hop barrierは+0.0000 exact/seed、95% CI [-0.2500, 0.2500]、exact p=1.0000。rotate1だけが成功した2件中、事前定義したsignature置換lineageを持つものは2件だった。
- seed 1432: no-transfer exact=False、qualified lineage=2。 signature 18374966859414896640 はr1でFunction由来のみ、r2でFunction-free表現へ置換。 signature 18374966859414962175 はr1でFunction由来のみ、r2でFunction-free表現へ置換。
- seed 1440: no-transfer exact=False、qualified lineage=2。 signature 71777214294589440 はr1でFunction由来のみ、r2でFunction-free表現へ置換。 signature 71777214294654975 はr1でFunction由来のみ、r2でFunction-free表現へ置換。
このlineageは選択された代表式のprovenanceを追跡する。truth signatureの一致は機能同値を示すが、学習された概念や物理回路の同一性を意味しない。
移植なし対比では、rotate1-only 3件中qualified lineageは2件、barrier-only 2件中0件だった。barrierが通常条件と同じ3/16に達したことと合わせると、観測した置換lineageは成功に必要な共通機構ではない。

taskごとに3つのexact McNemar比較をHolm補正した。

- eval_dual_mux_xor: rotate1 vs one_hop_barrier、left-only 2、right-only 2、p=1.0000、Holm p=1.0000。
- eval_dual_mux_xor: rotate1 vs no_transfer、left-only 3、right-only 1、p=0.6250、Holm p=1.0000。
- eval_dual_mux_xor: one_hop_barrier vs no_transfer、left-only 2、right-only 0、p=0.5000、Holm p=1.0000。
- eval_threshold2: rotate1 vs one_hop_barrier、left-only 2、right-only 0、p=0.5000、Holm p=1.0000。
- eval_threshold2: rotate1 vs no_transfer、left-only 2、right-only 1、p=1.0000、Holm p=1.0000。
- eval_threshold2: one_hop_barrier vs no_transfer、left-only 0、right-only 1、p=1.0000、Holm p=1.0000。

no-transferとのbeam Jaccard平均：

- eval_dual_mux_xor / rotate1: r1=0.844(n=16)、r2=0.626(n=16)、r3=0.476(n=16)、r4=0.491(n=14)、r5=0.475(n=12)、r6=0.463(n=12)。
- eval_dual_mux_xor / one_hop_barrier: r1=0.844(n=16)、r2=0.805(n=16)、r3=0.772(n=16)、r4=0.746(n=13)、r5=0.699(n=13)、r6=0.695(n=13)。
- eval_threshold2 / rotate1: r1=0.610(n=16)、r2=0.442(n=16)、r3=0.369(n=16)、r4=0.373(n=16)、r5=0.407(n=15)、r6=0.421(n=13)。
- eval_threshold2 / one_hop_barrier: r1=0.610(n=16)、r2=0.651(n=16)、r3=0.568(n=16)、r4=0.561(n=16)、r5=0.507(n=15)、r6=0.520(n=15)。

全10 exact式を64入力で再評価し、96 record、source hash、固定Functionの費用、通常searchとのsmoke一致を監査した。結果はBoolean探索機構に限り、学習抽象化、記述圧縮、実gate削減、速度、Router効果を示さない。

## Roadmap

- [Done] 選択された代表式についてFunction由来／Function-free生成と同一signatureへの置換をround単位で記録した。
- [Done] 一段だけFunction由来候補を許すbarrierを、移植なし・通常Functionと新規16 seedで比較した。
- [Next] 複数の経路選択task familyで同じbarrierを独立確認し、task固有軌跡への過適合を調べる。
- [Later] 床効果のない数値taskとState付きFunctionへ拡張し、十分な機構証拠が得られてからRouterへ統合する。

English: Normal rotation and the one-hop barrier both solved dual-mux XOR in 3/16 seeds, with a paired difference of zero. Two normal-only solutions showed Function-derived signatures replaced by Function-free equivalents, but barrier-only solutions showed no such lineage. The preregistered propagation criterion failed, so the observed lineage is not a necessary common mechanism.

简体中文：普通输入旋转和一跳屏障在dual-mux XOR上均成功3/16，配对差为零。两个仅普通条件成功的解出现了函数来源签名被无函数等价表达式替换的轨迹，但仅屏障条件成功的解没有这种轨迹。预注册传播标准未达成，因此该轨迹不是成功所必需的共同机制。

[事前计划](../results/E030-provenance-barrier/PROTOCOL.md) / [生数据](../results/E030-provenance-barrier/run/results.json) / [冻结Library](../results/E030-provenance-barrier/run/frozen_library.json) / [审计摘要](../results/E030-provenance-barrier/run/audit_summary.json)
