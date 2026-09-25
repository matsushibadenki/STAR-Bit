# E039：遅延投入の容量追加と同一幅置換を分離

実行日：2026-09-25。結果を見る前に定義した数値・経路選択2 taskを、新規6 seedで移植なしと、round 1後のlearned/inert/random各replace/add条件で比較した。計84探索。addはround 2だけbeam幅+1、replaceは選択済みbeamの最後の1枠を置換する。

| task | 条件 | exact/6 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | Function使用成功/成功数 | 秒/探索平均 | 成功式 primitive / routing / depth平均 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| numeric_rotated_weight_ge6 | no_transfer | 0/6 | 0.0000 / 0.0000 | 1.000 / 0.000 | 0/0 | 4.82 | NA |
| numeric_rotated_weight_ge6 | learned_replace | 0/6 | 0.0000 / 0.0000 | 2.000 / 0.000 | 0/0 | 4.75 | NA |
| numeric_rotated_weight_ge6 | learned_add | 0/6 | 0.0000 / 0.0000 | 1.000 / 0.000 | 0/0 | 4.77 | NA |
| numeric_rotated_weight_ge6 | inert_replace | 0/6 | 0.0000 / 0.0000 | 2.000 / 0.000 | 0/0 | 4.72 | NA |
| numeric_rotated_weight_ge6 | inert_add | 0/6 | 0.0000 / 0.0000 | 1.000 / 0.000 | 0/0 | 4.77 | NA |
| numeric_rotated_weight_ge6 | random_replace | 0/6 | 0.0000 / 0.0000 | 1.500 / 0.300 | 0/0 | 4.76 | NA |
| numeric_rotated_weight_ge6 | random_add | 0/6 | 0.0000 / 0.0000 | 1.000 / 0.000 | 0/0 | 4.77 | NA |
| route_cross_implies | no_transfer | 5/6 | 0.8333 / 0.1667 | 0.333 / 0.667 | 0/5 | 1.13 | 11.00 / 78.00 / 4.00 |
| route_cross_implies | learned_replace | 5/6 | 0.8333 / 0.1667 | 0.333 / 0.667 | 0/5 | 1.12 | 11.00 / 78.00 / 4.00 |
| route_cross_implies | learned_add | 5/6 | 0.8333 / 0.1667 | 0.333 / 0.667 | 0/5 | 1.14 | 11.00 / 78.00 / 4.00 |
| route_cross_implies | inert_replace | 5/6 | 0.8333 / 0.1667 | 0.333 / 0.667 | 0/5 | 1.21 | 11.00 / 78.00 / 4.00 |
| route_cross_implies | inert_add | 5/6 | 0.8333 / 0.1667 | 0.333 / 0.667 | 0/5 | 1.14 | 11.00 / 78.00 / 4.00 |
| route_cross_implies | random_replace | 5/6 | 0.8333 / 0.1667 | 0.333 / 0.667 | 0/5 | 1.14 | 11.00 / 78.00 / 4.00 |
| route_cross_implies | random_add | 5/6 | 0.8333 / 0.1667 | 0.333 / 0.667 | 0/5 | 1.16 | 11.00 / 78.00 / 4.00 |

## 主指標：全Module種・task平均のadd−replace exact差

平均差 +0.0000、不偏分散 0.0000、bootstrap 95% CI [0.0000, 0.0000]、Cohen dz NA、exact p=1.0000。容量保持pilot基準は未達。

## 副次比較（Holm補正）

| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric:pooled-add-minus-replace | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| route:pooled-add-minus-replace | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| pooled:learned-add-minus-inert-add | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| pooled:learned-add-minus-random-add | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |

## 探索的診断：best errorのadd−replace差（負がadd有利）

exactはnumericで床、routeでほぼ天井だったため、事前指定した主判定を置き換えずbest errorを探索的に解析した。

| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| pooled:add-minus-replace | -0.4167 | 0.0083 | [-0.4722, -0.3611] | -4.564 | 0.0312 | 0.1875 |
| numeric:pooled-add-minus-replace | -0.8333 | 0.0333 | [-0.9444, -0.7222] | -4.564 | 0.0312 | 0.1875 |
| route:pooled-add-minus-replace | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| numeric:learned-add-minus-replace | -1.0000 | 0.0000 | [-1.0000, -1.0000] | NA | 0.0312 | 0.1875 |
| numeric:inert-add-minus-replace | -1.0000 | 0.0000 | [-1.0000, -1.0000] | NA | 0.0312 | 0.1875 |
| numeric:random-add-minus-replace | -0.5000 | 0.3000 | [-0.8333, -0.1667] | -0.913 | 0.2500 | 0.5000 |

移植なしexactはnumeric 0/6、route 5/6。numericではlearned/inertの同一幅置換が全seedでbest errorを1悪化させ、容量追加は移植なしのerror=1を維持した。これは意味学習ではなく、beam枠を奪うことによる探索容量損失を支持する探索的結果である。randomはsignature衝突があり解釈を弱める。

学習Function固有基準は未達。
初回beam一致72/72、post-injection幅検証56件、signature衝突16件。numericの実効round 2幅はreplace 164、非衝突add 165（設定上限192）；routeはreplace 128、非衝突add 129。設定beam未満の実効幅となった点はprotocol deviationとして記録する。

全35 exact式を64入力で再評価した。84 record、strict JSON、progress、source hash、12 random FunctionとE038 replacement互換smokeを監査。探索CPU時間合計248.4秒。物理ゲート数や推論速度は未測定。

## Roadmap

- [Done] 新taskで容量追加と同一幅置換をlearned/inert/randomに分けて評価した。
- [Next] 衝突を除外して実効beam幅を厳密に揃え、numericの到達可能性を上げた新taskで容量損失を独立検証する。
- [Later] State形成・分解、負荷分散Router、固定random経路、Expert交換へ進む。

English: E039 prospectively separates temporary beam-capacity addition from fixed-width replacement. The preregistered exact endpoint was uninformative because the numeric task was at floor and the route task near ceiling. Exploratory best-error results show that learned and inert replacement both harmed numeric search, while addition preserved the baseline; no learned semantic advantage appeared.

简体中文：E039以前瞻方式区分临时增加beam容量与固定宽度替换。预注册的exact指标因数值任务触底、路径任务接近天花板而信息不足；探索性best-error结果显示，学习模块与惰性模块的固定宽度替换都会损害数值搜索，而增加容量保持了基线，未发现学习语义优势。

[事前計画](PROTOCOL.md) / [生データ](run/results.json) / [凍結設定](run/frozen_manifest.json) / [監査](run/audit_summary.json)
