# E046：Round別容量の2×2校正

2026-10-02。凍結8 task、新規6 seed、初回選択幅128/164と後続選択幅128/192を交差。LL/HL/LH/HHの初文字は初回幅、後文字は後続幅。192探索。

| family | policy | exact/24 | seed平均 / 不偏分散 | best error平均 / 不偏分散 | 秒平均 |
| --- | --- | ---: | ---: | ---: | ---: |
| numeric | LL | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.0000 | 1.011 |
| numeric | HL | 12/24 | 0.5000 / 0.0000 | 1.250 / 0.0000 | 1.264 |
| numeric | LH | 12/24 | 0.5000 / 0.0000 | 1.000 / 0.0000 | 1.772 |
| numeric | HH | 12/24 | 0.5000 / 0.0000 | 1.000 / 0.0000 | 2.019 |
| route | LL | 12/24 | 0.5000 / 0.0000 | 3.042 / 0.4604 | 1.052 |
| route | HL | 12/24 | 0.5000 / 0.0000 | 2.875 / 0.9187 | 1.261 |
| route | LH | 19/24 | 0.7917 / 0.0104 | 0.417 / 0.0417 | 1.505 |
| route | HH | 19/24 | 0.7917 / 0.0104 | 0.417 / 0.0417 | 1.732 |

主指標route exact(LH)−exact(HL)：平均+0.2917、不偏分散0.0104、95% CI [0.25, 0.375]、dz=2.8577380332470415、exact p=0.03125。事前gate：True。

| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric:exact:initial | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:exact:later | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:exact:interaction | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:best_error:initial | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:best_error:later | -0.2500 | 0.0000 | [-0.25, -0.25] | None | 0.03125 | 0.37500 |
| numeric:best_error:interaction | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:exact:initial | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:exact:later | +0.2917 | 0.0104 | [0.25, 0.375] | 2.8577380332470415 | 0.03125 | 0.37500 |
| route:exact:interaction | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:best_error:initial | -0.0833 | 0.0479 | [-0.2708333333333333, 0.041666666666666664] | -0.3806934938134405 | 0.75000 | 1.00000 |
| route:best_error:later | -2.5417 | 0.8417 | [-3.1875, -1.8958333333333333] | -2.7704385993923952 | 0.03125 | 0.37500 |
| route:best_error:interaction | +0.1667 | 0.1917 | [-0.08333333333333333, 0.5416666666666666] | 0.3806934938134405 | 0.75000 | 1.00000 |

後続拡張LH/HHはroute19/24、初回だけ拡張HLとbaseline LLは12/24。主指標は事前gateを達成した。numeric exactは全条件12/24のまま、error改善は後続拡張でのみ観測された。12副次比較のHolm補正後は全て非有意（最小p=0.375）。best_error差は負が改善。この校正は学習Moduleの効果を評価していない。

探索時間278.8秒。全110 exact式を64入力で再評価。192 record、144初回beam照合、16別seed互換smoke、round入力幅、progress、strict JSON、source hashを監査した。

- [Done] 初回保持と後続選択幅を2×2で分離して評価した。
- [Next] 主指標と副次補正の結果から容量policyの確認計画を凍結し、確認seedを分離する。
- [Later] learned／inert／同費用random cohort比較、State形成・分解、初回負荷分散Router、固定random経路、Expert交換へ進む。

English: Later expansion solved 19/24 routing cases versus 12/24 for initial-only expansion. The preregistered primary gate passed (difference +0.292, p=0.03125); all12 secondary contrasts remained nonsignificant after Holm correction.

简体中文：后续扩容的路由成功为19/24，仅初始扩容为12/24。预注册主要标准达成（差+0.292，p=0.03125），但12项次要比较经Holm校正后均不显著。
