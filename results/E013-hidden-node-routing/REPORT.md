# E013：隠れノード選択によるボトルネック診断

実行日：2026-09-12。E009-UNSATの108出力bitで、固定出力親を外し、第二層32ノードまたは全64隠れノードからcase全体で1ノードを選んだ。選択ノードを出力へ恒等接続するoracle exact synthesisである。

| 選択範囲 | SAT/108 | UNKNOWN | seed平均 | 不偏分散 | seed bootstrap 95% CI |
| --- | ---: | ---: | ---: | ---: | --- |
| layer1_select | 4 | 0 | 0.035714 | 0.004082 | [0.008929, 0.062500] |
| all_hidden_select | 4 | 0 | 0.035714 | 0.004082 | [0.008929, 0.071429] |

全隠れ−第二層のseed平均差は+0.000000、不偏分散0.000000、95% CI [0.000000, 0.000000]。

| 比較 | n | 第二層 SAT | 全隠れ SAT | 第二層のみ | 全隠れのみ | exact p | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 108 | 4 | 4 | 0 | 0 | 1 | 1 |
| numeric/gate2 | 40 | 4 | 4 | 0 | 0 | 1 | 1 |
| numeric/lut4 | 1 | 0 | 0 | 0 | 0 | 1 | 1 |
| selection/gate2 | 64 | 0 | 0 | 0 | 0 | 1 | 1 |
| selection/lut4 | 3 | 0 | 0 | 0 | 0 | 1 | 1 |

二側exact McNemarの5比較をHolm補正。両範囲の判定は全caseで一致した。

## SATとなったcase

| task | seed | 元構造 | bit | 第二層node |
| --- | ---: | --- | ---: | ---: |
| numeric | 503 | gate2 | 1 | 59 |
| numeric | 506 | gate2 | 1 | 66 |
| numeric | 509 | gate2 | 1 | 65 |
| numeric | 514 | gate2 | 1 | 69 |

## 判定

SATは4/108で事前の25%基準に届かず、すべてnumeric・元gate2・bit1だった。全隠れへ広げても追加SATはなく、第一層だけを直接読む利点も確認できない。経路選択67caseはすべてUNSAT判定だった。固定された出力親だけでなく、単一隠れノードが必要な多入力機能を作れないことが主要な制約である。

二入力ゲートの第二層ノードが直接依存できる葉は最大4個であり、6入力に依存する出力には構造上不足し得る。元gate2の出力まで含めれば理論上8葉へ届くが、固定された部分木の組合せが対象関数に合っていない。次は隠れ配線または時間再利用で深さを与える。

SAT証人8件を再読込し全64入力一致を確認。216論理式、checkpoint、ソースhashも検査した。UNSATは独立proof checker未検証のZ3判定。UNKNOWNは0件。

Z3 5.1.0、NumPy 1.25.2、単一thread、各問2000ms、全実行95.2秒。

学習されたroutingや汎化の結果ではない。精密数値と経路選択で差は明瞭だが、この二つの人工関数族を越えて一般化しない。

English: Selecting any existing hidden node recovered only four numeric bit-1 cases and no routing-task case. The main bottleneck lies inside fixed hidden wiring, not only in output parent choice.

简体中文：从任意隐藏节点中选择，只恢复了4个数值任务bit-1案例，路径选择任务没有恢复。主要瓶颈位于固定隐藏连接内部。

[実行前計画](../results/E013-hidden-node-routing/PROTOCOL.md) / [生データ](../results/E013-hidden-node-routing/run/results.json)
