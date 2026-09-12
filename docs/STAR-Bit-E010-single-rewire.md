# E010：出力直前の1接続修正

実行日：2026-09-12。E009で単一出力bitがUNSATだった108caseについて、出力ゲートの入力接続を1本だけ生入力へ変更し、全64入力に一致するゲート表が存在するかを調べた。ゲート数は増やしていない。

`random_raw`は無作為な生入力、`dependency_raw`は正解真理値表から求めた依存入力のうち、元の出力祖先にない入力を使う。後者はoracle診断であり、学習法ではない。

## 主要結果

| 条件 | SAT/108 | seed平均 | 不偏分散 | seed bootstrap 95% CI | UNKNOWN |
| --- | ---: | ---: | ---: | --- | ---: |
| random_raw | 0 | 0.000000 | 0.000000 | [0.000000, 0.000000] | 0 |
| dependency_raw | 0 | 0.000000 | 0.000000 | [0.000000, 0.000000] | 0 |

依存入力修正−無作為修正のseed平均差は+0.000000、不偏分散0.000000、95% CI [0.000000, 0.000000]。UNKNOWNは固定1秒予算で未発見として数えた。

## 事前指定したpaired比較

| 範囲 | n | random SAT | dependency SAT | 差 | randomのみ | dependencyのみ | exact p | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| all | 108 | 0 | 0 | +0.000000 | 0 | 0 | 1 | 1 |
| numeric/gate2 | 40 | 0 | 0 | +0.000000 | 0 | 0 | 1 | 1 |
| numeric/lut4 | 1 | 0 | 0 | +0.000000 | 0 | 0 | 1 | 1 |
| selection/gate2 | 64 | 0 | 0 | +0.000000 | 0 | 0 | 1 | 1 |
| selection/lut4 | 3 | 0 | 0 | +0.000000 | 0 | 0 | 1 | 1 |

検定は二側exact McNemar、5比較をHolm補正した。同じseed内の複数bitは独立ではないため、case水準のp値は診断用であり、seed bootstrap CIを主な不確実性表示とする。

## タスク種別と構造別

| task | 構造 | 対象 | 条件 | SAT | UNSAT | UNKNOWN |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| numeric | gate2 | 40 | random_raw | 0 | 40 | 0 |
| numeric | gate2 | 40 | dependency_raw | 0 | 40 | 0 |
| numeric | lut4 | 1 | random_raw | 0 | 1 | 0 |
| numeric | lut4 | 1 | dependency_raw | 0 | 1 | 0 |
| selection | gate2 | 64 | random_raw | 0 | 64 | 0 |
| selection | gate2 | 64 | dependency_raw | 0 | 64 | 0 |
| selection | lut4 | 3 | random_raw | 0 | 3 | 0 |
| selection | lut4 | 3 | dependency_raw | 0 | 3 | 0 |

両条件が同じ接続先を偶然選んだcaseは16/108。依存入力が祖先にすべて存在したためfallbackしたcaseは108/108。
全108caseで正解bitに関係する生入力はすでに出力祖先へ到達していた。このため、事前仮説の『欠けた依存入力を1本補う』操作は一度も適用されず、dependency_rawは関連入力への直結バイパスとして働いた。到達性不足ではなく、有限幅の中間表現または出力arityを含む情報ボトルネックが候補として残る。

## 検証と限界

SAT証人は0件で、今回は再評価対象がなかった。216論理式、元checkpoint、実行ソースのhashを検査した。全判定はUNSATだったが、独立proof checkerでは検証していないためZ3の判定として扱う。

Z3 5.1.0、NumPy 1.25.2、単一thread、各問1000ms、全実行66.8秒。正解表を用いた接続選択と全入力SAT合成なので、未知入力への汎化、勾配学習、学習されたrouting、抽象化の証拠ではない。

精密数値タスクと経路選択タスクを分けて示した。構造差だけでなく、出力bitの依存変数数と回路の深さが異なるため、タスク間差を一般的な難易度差と断定しない。

## 次の改善案

依存入力への1接続修正でSATが増えるなら、次は全正解を見ない接続提案器を導入し、同じ1接続予算の固定ランダム対照と複数seedで学習精度を比較する。改善しない構造には、事前固定した2接続修正を試し、ゲート追加より先に配線自由度の寄与を分離する。

Routerをまだ扱わないため、負荷分散補助損失、固定ランダムrouting、同一ラン内から別seedへのExpert交換は後続MoE統合実験の必須対照として維持する。

English: One output wire was replaced with either a random raw input or an oracle target-dependent input. SAT witnesses were independently evaluated. This is an exact-synthesis diagnosis, not learned routing or generalization.

简体中文：将输出门的一条连接替换为随机原始输入或由目标依赖关系选择的输入。SAT见证经过独立求值。这是精确综合诊断，不代表学习路由或泛化。

[実行前計画](../results/E010-single-rewire/PROTOCOL.md) / [生データ](../results/E010-single-rewire/run/results.json)
