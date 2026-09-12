# E011：出力arityを1増やす

実行日：2026-09-12。E009で単一bitがUNSATだった108caseについて、既存配線を残して出力ゲートへ生入力を1本追加した。元gate2はLUT3、元lut4はLUT5となる。新規学習ではない。

| 条件 | SAT/108 | UNKNOWN | seed平均 | 不偏分散 | seed bootstrap 95% CI |
| --- | ---: | ---: | ---: | ---: | --- |
| random_add | 2 | 1 | 0.017857 | 0.002381 | [0.000000, 0.044643] |
| influence_add | 2 | 3 | 0.016741 | 0.002103 | [0.000000, 0.042411] |

influence−randomのseed平均差は-0.001116、不偏分散0.005122、95% CI [-0.035714, 0.033482]。UNKNOWNは固定予算内の未発見として扱った。

| 比較 | n | random SAT | influence SAT | randomのみ | influenceのみ | exact p | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 108 | 2 | 2 | 2 | 2 | 1 | 1 |
| numeric/gate2 | 40 | 0 | 2 | 0 | 2 | 0.5 | 1 |
| numeric/lut4 | 1 | 1 | 0 | 1 | 0 | 1 | 1 |
| selection/gate2 | 64 | 0 | 0 | 0 | 0 | 1 | 1 |
| selection/lut4 | 3 | 1 | 0 | 1 | 0 | 1 | 1 |

二側exact McNemarの5比較をHolm補正した。case内のbit依存があるためp値は診断用で、seed bootstrapを主な不確実性表示とする。

## タスク・元構造別

| task | 元構造 | 対象 | 条件 | SAT | UNSAT | UNKNOWN |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| numeric | gate2 | 40 | random_add | 0 | 40 | 0 |
| numeric | gate2 | 40 | influence_add | 2 | 38 | 0 |
| numeric | lut4 | 1 | random_add | 1 | 0 | 0 |
| numeric | lut4 | 1 | influence_add | 0 | 1 | 0 |
| selection | gate2 | 64 | random_add | 0 | 64 | 0 |
| selection | gate2 | 64 | influence_add | 0 | 64 | 0 |
| selection | lut4 | 3 | random_add | 1 | 1 | 1 |
| selection | lut4 | 3 | influence_add | 0 | 0 | 3 |

両条件が同じ追加元を選んだcaseは19/108。元gate2では真理値表を4→8bit、元lut4では16→32bitへ増やした。

## 判定

事前基準の10%回復には届かなかった。1接続追加だけでは大半の表現制約は残る。少数のSATは、隠れ配線全体を変更せず出力への情報経路と表容量だけを増やして回復できるcaseがあることを示す。influence条件の優位性は確認できない。

SAT証人4件を保存ファイルから独立再評価し、対象bitの全64入力一致を確認した。216論理式、checkpoint、実行ソースhashも検査した。UNSATは独立proof checker未検証のZ3判定で、UNKNOWNは不能を意味しない。

Z3 5.1.0、NumPy 1.25.2、単一thread、各問2000ms、全実行84.1秒。influence条件は全正解を読むoracleであり、学習routingや汎化の証拠ではない。

精密数値と経路選択を分けると、回復は元gate2ではnumericの2件のみ、元lut4では少数か時間切れだった。母数が大きく異なるため、タスク間の一般的な優劣とは結論しない。

事前規則に従い、次は元接続を保持した2接続追加を同じ対照で診断する。それでも不足なら出力だけでなく隠れ層のボトルネックを局所化する。

English: Adding one output input recovered only a few exact-synthesis cases and did not meet the preregistered 10% threshold. Oracle influence selection did not outperform random selection.

简体中文：增加一条输出连接只恢复了少量精确综合案例，未达到预注册的10%阈值。基于目标影响度的选择未优于随机选择。

[実行前計画](../results/E011-output-arity-plus-one/PROTOCOL.md) / [生データ](../results/E011-output-arity-plus-one/run/results.json)
