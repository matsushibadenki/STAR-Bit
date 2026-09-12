# E004：学習した論理ゲート回路の抽出と温度annealing

2026-09-11。学習からhard回路を取り出し、Module抽出後も出力を保持する一連の処理を検証した。一方、softmax温度を下げる介入による精度改善は確認できなかった。

English: Learned gate circuits were exported and modularized with exact functional preservation. Temperature annealing did not improve held-out hard accuracy. These small models have low task accuracy; this is not evidence of useful abstract reasoning.

简体中文：已验证从训练后的逻辑门网络导出并模块化电路，且保持功能完全一致。温度退火未改善独立测试的硬化精度。模型任务精度较低，不能视为有效抽象推理的证据。

## 実行条件

- seed 200–207、2タスク×2条件＝32訓練run。全結果を保存し、追加seedやtestによるcheckpoint選択は行わなかった。
- 6bit入力、固定ランダム接続、32→32→4の計68論理ゲート。各段は入力とそれまでの全段を参照できる。各ゲートは16種Boolean関数の連続緩和のsoftmax混合で、1,088個の実数logitを学習。
- CPU一thread、NumPy解析的逆伝播、全訓練32例batch、Adam lr0.03、400step。PyTorch/SciPyが今回の環境にないためNumPy実装とした。原論文の忠実再現ではない。
- fixed：温度1。annealed：1→0.2を線形に変化。hard推論は各ゲートの最大logitのBoolean関数を選ぶ。
- numeric：3bit整数2個の和を4bit出力。selection：2bit制御で4bit値を循環シフト。全64入力を固定seed7001で32訓練／32testへ重複なしで分割。OOD評価ではない。
- Module抽出はE003のglobal_acceptを学習済みhard回路へ適用する。testラベルは抽出器に渡さないが、抽出は意味学習ではなく回路構造の処理。
- RouterやExpertを持たない単体実験。負荷分散・ランダム経路・Expert交換を実装したMoE検証の代わりにはならない。後続の統合実験では元の5条件を維持する。

## 精度：平均・不偏分散・95% CI

Exact matchは4bit全体の一致。表は0〜1、各行n=8。CIはseedを再標本化したpercentile bootstrap、10,000回。少数seed・離散スコアでは被覆率が不安定なので検定結果と同一視しない。

| タスク | 条件 | soft test平均 | hard test平均 | hard分散 | hard 95% CI | hard bit精度 | hard train平均 |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| numeric | fixed | 0.164062 | 0.164062 | 0.013602 | [0.097656, 0.246094] | 0.621094 | 0.320312 |
| numeric | annealed | 0.167969 | 0.152344 | 0.015747 | [0.078125, 0.238281] | 0.625000 | 0.265625 |
| selection | fixed | 0.117188 | 0.109375 | 0.002232 | [0.078125, 0.140625] | 0.564453 | 0.242188 |
| selection | annealed | 0.121094 | 0.097656 | 0.001796 | [0.070312, 0.125000] | 0.570312 | 0.250000 |

## 主比較：annealed−fixedのhard test exact-match

256通りの両側符号反転検定。2タスクを一つのfamilyとしてHolm補正。

| タスク | 平均差 | 差の分散 | bootstrap 95% CI | 生p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: |
| numeric | -0.011719 | 0.003889 | [-0.046875, 0.031250] | 0.750000 | 0.750000 |
| selection | -0.011719 | 0.000262 | [-0.023438, -0.003906] | 0.250000 | 0.500000 |

両タスクで平均差−1.171875 percentage points。改善仮説は支持されない。ただし悪化が確定したという結果でもない。selectionのbootstrap区間は0を含まないが、少数・同点を含むseed差で符号反転検定は有意でない。区間だけを選んで有意な悪化と報告しない。

## Module抽出

| タスク | 条件 | primitive記述平均 | 抽出後記述平均 | Module平均 | primitive DAG平均 |
| --- | --- | ---: | ---: | ---: | ---: |
| numeric | fixed | 16.625 | 15.375 | 0.875 | 15.375 |
| numeric | annealed | 15.625 | 15.000 | 0.625 | 14.375 |
| selection | fixed | 17.875 | 17.000 | 0.625 | 16.625 |
| selection | annealed | 17.750 | 17.125 | 0.500 | 16.375 |

全32runで、全64入力に対するhard網・primitive式・Module抽出後の出力が完全一致した。記述短縮は小さく、出力に寄与するprimitive回路も小さい。68個という割り当てゲート数と、出力へつながる展開DAGのサイズは別指標である。

16種類のゲートをAND/OR/XOR/NOTの固定式へ展開するため、抽出したModuleはゲート符号化を再構成しているだけの場合もある。圧縮結果を抽象概念の獲得とみなさない。時間・面積・消費電力の改善は未測定。

## 検証

- 16ゲートの全真理値表を独立に照合。解析勾配と中心差分の最大絶対誤差は 2.15e-12（5パラメータを3段から検査）。
- 条件間で同じ配線・初期logit、同じtrain/test splitを使用。乱数seedを記録し、32個のcheckpointと学習曲線を保存。
- 出力の等価性は全入力で検査。これは正解率100%を意味しない。実際のtest exact-matchは約10〜16%にとどまる。
- NumPy 2.3.5。実行記録の経過時間 3.566秒。これは機器性能のbenchmark値として使わない。

## 次の改善案

まず学習誤差の大きさを解消する必要がある。次回は固定配線の到達可能性・出力ゲートの表現制約を診断し、同予算での接続学習または出力集約を事前に一つ選んで比較する。annealingの調整をtestに合わせて繰り返さない。

学習精度が十分になった段階で、soft→hardの差を抑える介入と回路抽出を再評価する。さらに元のゲートをatomicに数える圧縮対照を追加すれば、primitive展開由来の見かけの圧縮を分離できる。

## 保存物と再現

[設計](../results/E004-learned-logic/PROTOCOL.md)、[生結果](../results/E004-learned-logic/run/results.json)、同フォルダのe004.py、pilot.py統計shim、E003ソースsnapshot、32checkpoint。

NumPyが導入されたPythonでe004.pyを実行する。既存runフォルダがあると停止して過去結果を上書きしない。再実験は新しい実験IDへソースと設計をコピーして実施する。レポート再生成はreport.py。
