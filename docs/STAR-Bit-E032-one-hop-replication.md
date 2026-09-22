# E032：one-hop伝播の独立seed確認とinert-slot対照

実行日：2026-09-22。E031で探索的に見つけた数値`unsigned_sum_ge6`のbarrier差を、新規16 seedで条件付き独立確認した。route対照はE031で定義済みのdual-mux XNOR。各taskで移植なし・採用Function・one-hop barrier・inert slot・同一費用randomの5条件、計160探索を事前固定した。

| task | no transfer | admitted | one-hop barrier | inert slot | random matched |
| --- | ---: | ---: | ---: | ---: | ---: |
| numeric_unsigned_sum_ge6 | 8/16 | 2/16 | 12/16 | 8/16 | 7/16 |
| route_dual_mux_xnor | 1/16 | 4/16 | 2/16 | 1/16 | 1/16 |

| paired exact/seed | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| --- | ---: | ---: | --- | ---: | ---: |
| numeric_unsigned_sum_ge6: one_hop_barrier−admitted | +0.6250 | 0.2500 | [0.3750, 0.8750] | 1.250 | 0.00195 |
| numeric_unsigned_sum_ge6: one_hop_barrier−inert_slot | +0.2500 | 0.4667 | [-0.0625, 0.5625] | 0.366 | 0.28906 |
| numeric_unsigned_sum_ge6: one_hop_barrier−no_transfer | +0.2500 | 0.4667 | [-0.0625, 0.5625] | 0.366 | 0.28906 |
| numeric_unsigned_sum_ge6: one_hop_barrier−random_matched | +0.3125 | 0.4958 | [-0.0625, 0.6250] | 0.444 | 0.17969 |
| numeric_unsigned_sum_ge6: admitted−inert_slot | -0.3750 | 0.3833 | [-0.6875, -0.0625] | -0.606 | 0.07031 |
| numeric_unsigned_sum_ge6: admitted−random_matched | -0.3125 | 0.3625 | [-0.5625, 0.0000] | -0.519 | 0.12500 |
| numeric_unsigned_sum_ge6: inert_slot−no_transfer | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.00000 |
| route_dual_mux_xnor: one_hop_barrier−admitted | -0.1250 | 0.2500 | [-0.3750, 0.1250] | -0.250 | 0.62500 |
| route_dual_mux_xnor: one_hop_barrier−inert_slot | +0.0625 | 0.0625 | [0.0000, 0.1875] | 0.250 | 1.00000 |
| route_dual_mux_xnor: one_hop_barrier−no_transfer | +0.0625 | 0.0625 | [0.0000, 0.1875] | 0.250 | 1.00000 |
| route_dual_mux_xnor: one_hop_barrier−random_matched | +0.0625 | 0.1958 | [-0.1250, 0.2500] | 0.141 | 1.00000 |
| route_dual_mux_xnor: admitted−inert_slot | +0.1875 | 0.1625 | [0.0000, 0.3750] | 0.465 | 0.25000 |
| route_dual_mux_xnor: admitted−random_matched | +0.1875 | 0.2958 | [-0.0625, 0.4375] | 0.345 | 0.37500 |
| route_dual_mux_xnor: inert_slot−no_transfer | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.00000 |

## 判定

事前登録した数値のbarrier−admitted再現基準は達成。
one-hop固有機構のbarrier−inert追加基準は未達。
Primaryはbarrier−admitted +0.6250 exact/seed、95% CI [0.3750, 0.8750]、exact p=0.00195。barrier−inertは+0.2500、95% CI [-0.0625, 0.5625]、exact p=0.28906。

主効果は新seedでも再現したが、barrierがinert/no-transferより明確に良いとは言えない。数値でinert slotとno-transferは全16 seedでexact・best errorが一致した。barrierの数値成功12式はいずれも最終式でFunctionを使わず、直接部品としての再利用は観測されなかった。したがって、今回の強い対比は『無制限にFunctionを伝播させると探索が悪化しうる』であり、『一段使うこと自体が必要』とは示されていない。

inert条件は同じtruth signatureのFunction-free再生成も親利用を禁止する保守的な対照である。このtaskでは移植なしと同じexact・best errorだったが、他taskでも無害とは限らない。

数値の6つの副次比較にHolm補正を適用した。
- one_hop_barrier−no_transfer: p=0.28906、Holm p=0.86719。
- one_hop_barrier−random_matched: p=0.17969、Holm p=0.71875。
- admitted−inert_slot: p=0.07031、Holm p=0.42188。
- admitted−random_matched: p=0.12500、Holm p=0.62500。
- inert_slot−no_transfer: p=1.00000、Holm p=1.00000。
- one_hop_barrier−inert_slot: p=0.28906、Holm p=0.86719。

数値−経路選択のbarrier−admitted効果差は+0.7500、95% CI [0.3750, 1.1250]、exact p=0.00391。route側はadmitted 4/16、barrier 2/16で方向が逆だが、単一route taskでありtask-family差の確証ではない。

成功式の平均tree cost（primitive / routing bits / depth）と移植Function使用数：

- numeric_unsigned_sum_ge6 / no_transfer: 14.75 / 106.25 / 5.00; Function使用 0、best error平均 0.562、時間平均 2.326秒。
- numeric_unsigned_sum_ge6 / admitted: 15.00 / 108.00 / 5.00; Function使用 0、best error平均 1.750、時間平均 2.801秒。
- numeric_unsigned_sum_ge6 / one_hop_barrier: 14.50 / 104.50 / 5.00; Function使用 0、best error平均 0.375、時間平均 2.044秒。
- numeric_unsigned_sum_ge6 / inert_slot: 14.75 / 106.25 / 5.00; Function使用 0、best error平均 0.562、時間平均 2.269秒。
- numeric_unsigned_sum_ge6 / random_matched: 14.71 / 106.00 / 5.00; Function使用 0、best error平均 0.812、時間平均 2.460秒。
- route_dual_mux_xnor / no_transfer: 7.00 / 48.00 / 4.00; Function使用 0、best error平均 3.750、時間平均 2.826秒。
- route_dual_mux_xnor / admitted: 9.00 / 62.00 / 6.00; Function使用 4、best error平均 3.250、時間平均 2.673秒。
- route_dual_mux_xnor / one_hop_barrier: 8.00 / 54.00 / 4.00; Function使用 0、best error平均 3.500、時間平均 2.688秒。
- route_dual_mux_xnor / inert_slot: 7.00 / 48.00 / 4.00; Function使用 0、best error平均 3.750、時間平均 2.760秒。
- route_dual_mux_xnor / random_matched: 9.00 / 62.00 / 6.00; Function使用 1、best error平均 4.625、時間平均 2.874秒。

全46 exact式を64入力で再評価し、160 record、32 random Functionの費用とsignature、task、source hash、strict JSONを監査した。対象はBoolean beam探索であり、概念形成、Library記述圧縮、実gate削減、ハードウェア速度、Stateや学習Routerの効果は測っていない。

## Roadmap

- [Done] E031の数値barrier優位を新規16 seedで独立確認し、inert-slot対照で初期候補数の交絡を検査した。
- [Done] 数値対経路選択でFunctionの作用方向が異なることを同一予算で記録した。
- [Next] Functionの使用をstage/roundで制限する費用付きadmissionを、task生成grammarを先に固定したpilotで検証する。task難度の選別にはpilotだけを使い、独立seedを保持する。
- [Later] State付きFunction形成・分解とRouter統合へ進み、step 0負荷分散、固定random経路、同一run内から別seedへのExpert交換、総費用を比較する。

English: The numeric barrier advantage over unrestricted Function propagation replicated on 16 new seeds (12/16 versus 2/16, paired gain +0.625, exact p=0.00195). The barrier did not significantly beat an inert slot or no transfer (12/16 versus 8/16), so beneficial one-hop composition remains unproven. The route task showed the opposite direction (barrier 2/16, admitted 4/16).

简体中文：在16个新种子上，数值任务中一跳屏障相对无限制函数传播的优势得到复现（12/16对2/16，配对增益+0.625，精确p=0.00195）。但屏障未显著优于惰性槽或无迁移（12/16对8/16），因此尚未证明一跳组合本身有益。路由任务呈相反方向（屏障2/16，普通函数4/16）。

[事前计划](../results/E032-one-hop-replication/PROTOCOL.md) / [生数据](../results/E032-one-hop-replication/run/results.json) / [冻结Manifest](../results/E032-one-hop-replication/run/frozen_manifest.json) / [审计摘要](../results/E032-one-hop-replication/run/audit_summary.json)
