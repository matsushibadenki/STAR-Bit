# E012：出力arityを2増やす

実行日：2026-09-12。E009で単一bitがUNSATだった108caseに、元接続を残して異なる生入力を2本追加した。元gate2はLUT4、元lut4はLUT6となる。

| 条件 | SAT/108 | UNKNOWN | seed平均 | 不偏分散 | seed bootstrap 95% CI |
| --- | ---: | ---: | ---: | ---: | --- |
| random_add2 | 9 | 0 | 0.078497 | 0.007290 | [0.037202, 0.120164] |
| influence_add2 | 13 | 0 | 0.113095 | 0.007426 | [0.071429, 0.154762] |

influence−randomのseed平均差は+0.034598、不偏分散0.003846、95% CI [0.008929, 0.066992]。

| 比較 | n | random SAT | influence SAT | randomのみ | influenceのみ | exact p | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 108 | 9 | 13 | 0 | 4 | 0.125 | 0.625 |
| numeric/gate2 | 40 | 5 | 8 | 0 | 3 | 0.25 | 1 |
| numeric/lut4 | 1 | 0 | 1 | 0 | 1 | 1 | 1 |
| selection/gate2 | 64 | 1 | 1 | 0 | 0 | 1 | 1 |
| selection/lut4 | 3 | 3 | 3 | 0 | 0 | 1 | 1 |

二側exact McNemarの5比較をHolm補正。bit間依存があるためcase水準p値は診断用で、seed bootstrap CIを優先する。

| task | 元構造 | 対象 | 条件 | SAT | UNSAT | UNKNOWN |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| numeric | gate2 | 40 | random_add2 | 5 | 35 | 0 |
| numeric | gate2 | 40 | influence_add2 | 8 | 32 | 0 |
| numeric | lut4 | 1 | random_add2 | 0 | 1 | 0 |
| numeric | lut4 | 1 | influence_add2 | 1 | 0 | 0 |
| selection | gate2 | 64 | random_add2 | 1 | 63 | 0 |
| selection | gate2 | 64 | influence_add2 | 1 | 63 | 0 |
| selection | lut4 | 3 | random_add2 | 3 | 0 | 0 |
| selection | lut4 | 3 | influence_add2 | 3 | 0 | 0 |

同じ2入力を選んだcaseは10/108。元gate2の出力表は4→16bit、元lut4は16→64bit。

## 判定

回復はrandom 9/108、influence 13/108で、事前の25%基準に届かなかった。両タスクにSATはあるが、出力表を最大4倍にしても大半の制約が残る。influence選択の優位性もHolm補正後には確認できない。規則どおり出力arityの追加を止め、隠れ層と出力接続先を診断する。

SAT証人22件を再読込し、全64入力で一致を確認。216論理式、checkpoint、ソースhashを検査した。UNSATは独立proof checker未検証のZ3判定。UNKNOWNは0件。

Z3 5.1.0、NumPy 1.25.2、単一thread、各問3000ms、全実行77.5秒。全正解を使うoracle exact synthesisであり、学習や汎化ではない。

精密数値では元gate2の回復が中心だった。経路選択では元gate2 64件中1件、元lut4 3件は全件回復した。母数が異なるため、構造自由度が経路選択一般に効かないとは結論しない。

English: Two added output inputs recovered 9 random and 13 oracle-selected cases, below the preregistered 25% milestone. Output arity expansion now stops and hidden-node routing is diagnosed next.

简体中文：增加两条输出连接后，随机条件恢复9例、目标影响度条件恢复13例，低于预注册的25%阈值。下一步停止扩大输出表，诊断隐藏节点路由。

[実行前計画](../results/E012-output-arity-plus-two/PROTOCOL.md) / [生データ](../results/E012-output-arity-plus-two/run/results.json)
