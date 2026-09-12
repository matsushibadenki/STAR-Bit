# E005：入力到達性・深さの比較

実行日：2026-09-11。

**出力への入力到達性は改善したが、その改善だけで高い正解率は得られなかった。** 全入力を参照するcoverage配線は、従来のrandom_skipより加算で改善した。しかし深さを揃えたrandom_layeredに対する優位性は確認できない。

English: Coverage wiring reached every input and improved numeric accuracy over the original skip-wired baseline. It did not significantly outperform depth-matched random wiring. Input reachability alone is insufficient for high task accuracy.

简体中文：覆盖型连接使输出能访问全部输入，并在数值任务上优于原跳连基线；但未显著优于深度匹配的随机连接。输入可达性本身不足以保证高任务精度。

## 設計

- seed 300–315、2問題族、3条件＝96訓練run。初期logits・train/test split・更新回数は条件間で共有。
- random_skipはE004の入力＋全過去段を参照。random_layeredは直前段の異なる2要素をランダムに参照。coverage_layeredは直前段から到達入力集合の和が最大の2要素を選び、同点なら乱数で決める。
- 後者2条件は段の深さと重複なし接続を揃えた対照。coverage規則はラベルを使わず人が設計したもので、接続学習ではない。
- 全群6入力・32→32→4の計68ゲート、1,088学習logits。16種Boolean関数のsoftmax混合、温度1。NumPy、CPU一thread、full batch32、Adam lr0.03、400step。
- numeric：3bit整数2個の和を4bit出力。selection：2bit制御による4bit循環シフト。全64入力を32train／32testに固定分割。E004と同じ問題・splitなので独立testによる確認ではなく探索。
- Router/Expertなし。従来の負荷分散・固定ランダムルーティング・Expert交換対照を置き換える実験ではない。

## Test exact-match（4bit全体の一致）

スコアは0〜1、各行16seed。不偏分散、seed percentile bootstrap 10,000回による点ごとの95% CI。

| 問題族 | 配線 | soft平均 | hard平均 | hard分散 | hard 95% CI | hard bit平均 | soft train平均 | hard train平均 |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| numeric | random_skip | 0.066406 | 0.082031 | 0.003499 | [0.056641, 0.111377] | 0.558594 | 0.263672 | 0.220703 |
| numeric | random_layered | 0.197266 | 0.199219 | 0.016781 | [0.138672, 0.261719] | 0.671387 | 0.437500 | 0.416016 |
| numeric | coverage_layered | 0.164062 | 0.166016 | 0.008427 | [0.123047, 0.210938] | 0.651855 | 0.509766 | 0.457031 |
| selection | random_skip | 0.128906 | 0.101562 | 0.003320 | [0.074219, 0.128906] | 0.551270 | 0.298828 | 0.279297 |
| selection | random_layered | 0.123047 | 0.111328 | 0.001949 | [0.089844, 0.132812] | 0.581055 | 0.414062 | 0.367188 |
| selection | coverage_layered | 0.158203 | 0.128906 | 0.001807 | [0.109375, 0.148438] | 0.583496 | 0.431641 | 0.423828 |

## 事前指定した検定

差はcoverage−baselineのhard test exact-match。interactionはcoverage−random_layeredについてselection−numeric。16seedの対応差を全65,536符号で両側検定し、5比較をHolm補正。

| 問題族 | baseline | 平均差 | 差の分散 | 95% CI | 生p | Holm p |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| numeric | random_layered | -0.033203 | 0.024540 | [-0.105469, 0.042969] | 0.434204 | 0.654785 |
| numeric | random_skip | 0.083984 | 0.009338 | [0.039062, 0.128906] | 0.004150 | 0.020752 |
| selection | random_layered | 0.017578 | 0.003772 | [-0.011719, 0.046875] | 0.327393 | 0.654785 |
| selection | random_skip | 0.027344 | 0.003369 | [-0.001953, 0.052734] | 0.105347 | 0.421387 |
| selection_minus_numeric | interaction | 0.050781 | 0.018864 | [-0.015625, 0.113281] | 0.175781 | 0.527344 |

加算のcoverage対random_skipは+8.3984 percentage points、Holm p=0.020752。ただしcoverage対random_layeredは−3.3203 pointsで有意でない。したがって最初の差をcoverage規則だけの利点とは扱えない。タスク間の交互作用も有意ではない。

## 配線から診断できる上限

出力bitが到達できる入力の値で全64例を群分けし、各群のラベル多数派を選んだAccuracyを計算する。これがその入力集合しか見えない予測器のbit精度上限。4bit上限の平均はbit Accuracyの上限、最小値はexact-matchの緩い上限となる。ゲート数やBoolean合成構造の制約を無視しているので達成できる保証はない。

この診断だけは全64入力の正解を使うが、配線生成・学習・モデル選択には返さない。比較するfull精度にもtrain例が含まれるためtest成績と区別する。

| 問題族 | 配線 | 到達入力数平均／出力 | 上流ゲート数平均 | bit上限平均 | exact上限平均 | hard full bit精度 | primitive DAG平均 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| numeric | random_skip | 3.5469 | 15.4375 | 0.661133 | 0.500000 | 0.625488 | 19.0625 |
| numeric | random_layered | 4.8594 | 23.1250 | 0.817383 | 0.562500 | 0.738281 | 23.4375 |
| numeric | coverage_layered | 6.0000 | 22.9375 | 1.000000 | 1.000000 | 0.732910 | 26.8125 |
| selection | random_skip | 3.5469 | 15.4375 | 0.718750 | 0.667969 | 0.637695 | 20.5000 |
| selection | random_layered | 4.8594 | 23.1250 | 0.837891 | 0.750000 | 0.677734 | 29.6875 |
| selection | coverage_layered | 6.0000 | 22.9375 | 1.000000 | 1.000000 | 0.692627 | 31.0000 |

random_skipでは出力あたり平均3.55入力しか届かず、配線による情報制約が存在する。coverageでは全出力・全seedで6入力に届き、この診断上限は1になったが、実測精度は低いままだった。

上限が1というだけでは、固定の2入力ゲート合成で目的関数を表せるとは限らない。出力の手前で情報が2本に圧縮される制約と、連続緩和の最適化不足はこの実験では分離できていない。

同じ68ゲートを訓練で実行しても、出力に寄与する上流ゲート数は約15→23へ増える。hard化後のprimitive DAGの費用も異なるため、推論計算量まで完全一致とは主張しない。実機の面積・遅延・消費電力は未測定。

## 検証と保存

- E004の16ゲート真理値表と勾配検査を再実行。最大勾配誤差 2.15e-12。
- 配線変更が初期logitsを変えないこと、全入力可視の場合の診断上限1、入力なしでは多数派予測になることを検査。
- 全96runのhard網とprimitive回路を全64入力で照合。全体実測精度が診断上限以下であることも検査。
- 各seedのcheckpoint、到達入力集合、学習曲線、生指標、全ソースhashと設計hashを保存。未実行の結果や欠損runなし。
- NumPy 1.25.2、全処理の記録時間 8.319秒。時間は反復benchmarkではなく実行記録。

## 次の改善案

次は全入力が届く配線を固定し、出力の情報圧縮を一つの軸として検証する。候補は最終2入力ゲートを4入力LUTへ置換する方法。配線、入力符号化、学習量を揃え、真理値表bitsと出力への接続数の増加を明示する。同じゲート1個という数え方だけで同予算とはしない。

別案は入出力例から接続そのものを学ぶ方法だが、今回は未実施。LUTによる出力容量の検証と一度に混ぜない。学習精度が上がった段階でhard化、Module抽出、PE再利用の効果へ戻る。

## 再現

```bash
python3 results/E005-input-coverage/experiment.py
python3 results/E005-input-coverage/report.py
```

runが既存の場合は停止する。新しい訓練は別実験IDへソース・設計をコピーして行い、旧結果を上書きしない。report.pyのみの再実行は保存済み測定からレポートを再生成する。NumPy依存。

[事前設計](../results/E005-input-coverage/PROTOCOL.md)、[生結果とhash](../results/E005-input-coverage/run/results.json)。
