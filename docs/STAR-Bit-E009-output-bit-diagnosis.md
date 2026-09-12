# E009：出力bit別の固定配線診断

2026-09-12。16seed×2タスク×2構造×4出力＝256問。E008と同じ配線で、出力を1bitずつ独立に制約した。新規学習や汎化評価ではない。

| task | 構造 | bit | SAT | UNSAT | UNKNOWN |
| --- | --- | ---: | ---: | ---: | ---: |
| numeric | gate2 | 0 | 16 | 0 | 0 |
| numeric | gate2 | 1 | 8 | 8 | 0 |
| numeric | gate2 | 2 | 0 | 16 | 0 |
| numeric | gate2 | 3 | 0 | 16 | 0 |
| numeric | lut4 | 0 | 16 | 0 | 0 |
| numeric | lut4 | 1 | 16 | 0 | 0 |
| numeric | lut4 | 2 | 14 | 1 | 1 |
| numeric | lut4 | 3 | 3 | 0 | 13 |
| selection | gate2 | 0 | 0 | 16 | 0 |
| selection | gate2 | 1 | 0 | 16 | 0 |
| selection | gate2 | 2 | 0 | 16 | 0 |
| selection | gate2 | 3 | 0 | 16 | 0 |
| selection | lut4 | 0 | 9 | 1 | 6 |
| selection | lut4 | 1 | 7 | 0 | 9 |
| selection | lut4 | 2 | 4 | 0 | 12 |
| selection | lut4 | 3 | 5 | 2 | 9 |

## seed間の記述統計

各seedの「4bit中SATを発見できた割合」を集計する。精度や真の構成可能率ではなく、1秒の探索予算に依存する下限である。

| task | 構造 | 平均 | 不偏分散 |
| --- | --- | ---: | ---: |
| numeric | gate2 | 0.375000 | 0.016667 |
| numeric | lut4 | 0.765625 | 0.020573 |
| selection | gate2 | 0.000000 | 0.000000 |
| selection | lut4 | 0.390625 | 0.099740 |

少なくとも1bitがUNSATの配線は36/64。各bitはSATだがE008の同時出力がUNSATとなる配線は0/64。後者だけが、個々のbitは表現できても共有ゲート表の同時整合が妨げになるという診断に対応する。

全98件のSAT証人を保存後に独立評価器で再読込し、対象bitについて全64入力一致を確認。全256論理式とソースhashも確認。UNSATはZ3判定であり、本実験では証明を保存・独立検証していない。UNKNOWNは不能とは判定しない。

実行時間139.5秒、Z3 5.1.0、単一thread、各問1000ms。E008は10000msなのでSAT件数差を効果量や速度改善と解釈しない。異なるbitのSAT証人はそれぞれ別のゲート表である。

探索的な論理診断のため、有意差検定・学習効果量は計算しない。元の学習精度の平均・分散はE008に記載。成功seedの追加や除外は行わない。

## 次の改善案

単一bitのUNSATがある出力の祖先回路を優先し、追加接続の本数を固定して、無作為追加と入力依存性を考慮した追加を比較する。ゲート数を増やす前に接続変更の効果を分離する。共有制約のみの失敗には出力別回路の複製を診断用の容量対照とする。

Routerを含まない段階の実験であり、統合時の負荷分散・固定ランダム経路・Expert交換の対照は維持する。

English: Per-output feasibility distinguishes individual-output obstructions from shared-gate conflicts. SAT witnesses were independently evaluated; UNKNOWN remains unresolved. This is not a training result.

简体中文：逐输出位检验用于区分单个位的表达限制与共享门约束。SAT见证经过独立求值，UNKNOWN仍未确定。本实验不是训练或泛化结果。

再現：`python3 results/E009-output-bit-diagnosis/run.py`、続いて `python3 results/E009-output-bit-diagnosis/report.py`。既存runがあると停止する。Z3 5.1.0.0を/private/tmp/starbit-z3に、NumPyをPython環境に用意する。

[事前計画](../results/E009-output-bit-diagnosis/PROTOCOL.md) / [生データ](../results/E009-output-bit-diagnosis/run/results.json)
