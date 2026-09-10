# STAR-Bit CPU予備実験：実測結果

この結果は小型MLPの探索的検証であり、BitNet/Transformerや動的接続の実証ではない。

選択タスクでは学習Routerが固定ランダムRouterより低い誤差を示した。一方、精密回帰のIDでは改善しなかった。選択タスクでもtotalを合わせたWide Denseが平均では学習MoEを上回った。したがって「構造が数値精度を補償した」とはまだ言えない。

English: Learned routing reduced error versus fixed random routing on the selection proxy, but not on in-distribution precision regression. No comparison survived Holm correction. This is not evidence of dynamic-topology or LLM gains.

简体中文：在选择任务中，学习路由的误差低于固定随机路由，但在分布内精密回归中没有改善。所有比较均未通过Holm校正。本结果不能证明动态拓扑或大语言模型能力提升。

## 実行条件

- 8シード（0–7）×6条件×2タスク＝96訓練run。各400更新、batch 128、Adam、学習率0.003。
- 訓練4,096例、ID/OOD各2,048例。splitは固定し、モデル初期値とbatch順序をシードで変更。
- 12次元入力、ReLU、スカラー出力。4 ExpertsからTop-2、各Expert幅16。Dense幅36、Wide幅68。
- 精密回帰：8入力と固定係数の内積。選択：4カテゴリの指定に従って8入力の先頭4要素から1つを返す。カテゴリは両タスクの入力に含める。
- ID値域[-1,1]、OODは絶対値[1,2]。多段経路・言語・未知hopへの外挿は測っていない。
- NMSE = MSE / テスト正解値の母分散。小さいほど良い。ID/OODでは分母も異なる。
- alpha=0.01の負荷分散損失を学習MoEの初回更新から適用。固定Routerでは診断のみ。
- Python 3.10.18 / PyTorch 2.10.0 / CPU / FP32。実行記録上の全所要時間 13.15秒（速度比較のbenchmarkではない）。
- STEによる三値weight-only模擬演算。活性化、潜在重み、bias、RouterはFP32。FP16実験、三値kernel、1.58-bit実格納は未実施。
- 最終stepを評価。validationでの選択・ハイパーパラメータ探索・結果を見た再訓練なし。未収束や学習率への感度は未評価。

## パラメータ予算

| 条件 | 総数 | 入力あたりactive | 学習可能数 | パラメータtensor bytes |
| --- | ---: | ---: | ---: | ---: |
| fp_dense | 505 | 505 | 505 | 2020 |
| ternary_dense | 505 | 505 | 505 | 2020 |
| ternary_wide | 953 | 953 | 953 | 3812 |
| ternary_learned | 952 | 502 | 952 | 3808 |
| ternary_fixed | 952 | 502 | 900 | 3808 |
| fp_learned | 952 | 502 | 952 | 3808 |

activeはRouterを含むパラメータ使用数でFLOPsではない。Dense 505対MoE 502、Wide 953対MoE 952という近似一致。FP32実格納bytesはoptimizer/activationを含むpeakメモリではない。固定Routerの52パラメータも総数に含める。

## NMSE：平均・分散・95% CI

不偏分散（ddof=1）、シード単位のt区間。CIは多重比較補正前の点ごとの区間であり、正規近似の妥当性を保証しない。各行n=8。

| タスク | split | 条件 | 平均 | 分散 | 標準偏差 | 95% CI |
| --- | --- | --- | ---: | ---: | ---: | --- |
| precision | id | fp_dense | 0.001855 | 0.00000006 | 0.000237 | [0.001657, 0.002053] |
| precision | id | ternary_dense | 0.004975 | 0.00000472 | 0.002173 | [0.003158, 0.006792] |
| precision | id | ternary_wide | 0.003646 | 0.00000068 | 0.000823 | [0.002957, 0.004334] |
| precision | id | ternary_learned | 0.006622 | 0.00000081 | 0.000903 | [0.005867, 0.007376] |
| precision | id | ternary_fixed | 0.005478 | 0.00000204 | 0.001430 | [0.004283, 0.006674] |
| precision | id | fp_learned | 0.001113 | 0.00000011 | 0.000325 | [0.000841, 0.001384] |
| precision | ood | fp_dense | 0.025702 | 0.00005849 | 0.007648 | [0.019308, 0.032095] |
| precision | ood | ternary_dense | 0.047419 | 0.00001371 | 0.003703 | [0.044324, 0.050515] |
| precision | ood | ternary_wide | 0.031649 | 0.00001184 | 0.003441 | [0.028772, 0.034526] |
| precision | ood | ternary_learned | 0.025944 | 0.00029954 | 0.017307 | [0.011475, 0.040414] |
| precision | ood | ternary_fixed | 0.034036 | 0.00002607 | 0.005106 | [0.029767, 0.038305] |
| precision | ood | fp_learned | 0.010656 | 0.00000909 | 0.003014 | [0.008136, 0.013176] |
| selection | id | fp_dense | 0.006566 | 0.00000150 | 0.001225 | [0.005542, 0.007590] |
| selection | id | ternary_dense | 0.073707 | 0.00026295 | 0.016216 | [0.060150, 0.087264] |
| selection | id | ternary_wide | 0.055811 | 0.00014096 | 0.011873 | [0.045886, 0.065737] |
| selection | id | ternary_learned | 0.065163 | 0.00019645 | 0.014016 | [0.053446, 0.076881] |
| selection | id | ternary_fixed | 0.154485 | 0.00208016 | 0.045609 | [0.116355, 0.192615] |
| selection | id | fp_learned | 0.010578 | 0.00002495 | 0.004995 | [0.006402, 0.014754] |
| selection | ood | fp_dense | 0.181933 | 0.00006414 | 0.008009 | [0.175238, 0.188628] |
| selection | ood | ternary_dense | 0.348797 | 0.00075617 | 0.027499 | [0.325808, 0.371787] |
| selection | ood | ternary_wide | 0.313094 | 0.00008224 | 0.009069 | [0.305513, 0.320676] |
| selection | ood | ternary_learned | 0.325262 | 0.00173918 | 0.041703 | [0.290397, 0.360127] |
| selection | ood | ternary_fixed | 0.472227 | 0.00239260 | 0.048914 | [0.431334, 0.513121] |
| selection | ood | fp_learned | 0.197042 | 0.00158848 | 0.039856 | [0.163722, 0.230362] |

## 対応差と検定

差 = baseline NMSE − ternary_learned NMSE。正なら学習MoEが改善。interactionはこの固定経路との差についてselection−precisionを取ったもの。256通りの符号反転、両側p。全18比較を一つのHolm familyとして補正。

| タスク | split | baseline | 平均差 | 95% CI | 生p | Holm p |
| --- | --- | --- | ---: | --- | ---: | ---: |
| precision | id | ternary_fixed | -0.001143 | [-0.002820, 0.000533] | 0.148438 | 1.000000 |
| precision | id | ternary_dense | -0.001647 | [-0.003441, 0.000147] | 0.070312 | 0.632812 |
| precision | id | ternary_wide | -0.002976 | [-0.003935, -0.002017] | 0.007812 | 0.140625 |
| precision | id | fp_dense | -0.004767 | [-0.005594, -0.003939] | 0.007812 | 0.140625 |
| precision | ood | ternary_fixed | 0.008091 | [-0.007361, 0.023544] | 0.234375 | 1.000000 |
| precision | ood | ternary_dense | 0.021475 | [0.006659, 0.036291] | 0.031250 | 0.312500 |
| precision | ood | ternary_wide | 0.005705 | [-0.007040, 0.018450] | 0.289062 | 1.000000 |
| precision | ood | fp_dense | -0.000243 | [-0.018170, 0.017684] | 0.984375 | 1.000000 |
| selection | id | ternary_fixed | 0.089322 | [0.055201, 0.123442] | 0.007812 | 0.140625 |
| selection | id | ternary_dense | 0.008544 | [-0.006992, 0.024080] | 0.250000 | 1.000000 |
| selection | id | ternary_wide | -0.009352 | [-0.024160, 0.005457] | 0.187500 | 1.000000 |
| selection | id | fp_dense | -0.058597 | [-0.069691, -0.047503] | 0.007812 | 0.140625 |
| selection | ood | ternary_fixed | 0.146966 | [0.096701, 0.197230] | 0.007812 | 0.140625 |
| selection | ood | ternary_dense | 0.023536 | [-0.018602, 0.065673] | 0.218750 | 1.000000 |
| selection | ood | ternary_wide | -0.012168 | [-0.043354, 0.019019] | 0.382812 | 1.000000 |
| selection | ood | fp_dense | -0.143329 | [-0.176854, -0.109804] | 0.007812 | 0.140625 |
| selection_minus_precision | id | interaction | 0.090465 | [0.055306, 0.125624] | 0.007812 | 0.140625 |
| selection_minus_precision | ood | interaction | 0.138874 | [0.090249, 0.187500] | 0.007812 | 0.140625 |

**Holm補正後に有意な比較はない。** 8シードでは最小両側p=0.0078125なので18比較の最初の閾値0.002778に届かない。生pだけで成功判定しない。「数値タスクには効かない」という同等性の証明にもならない。

## Expert交換

交換後NMSE − 無交換NMSE。正は悪化。各seedの無交換checkpointから独立に分岐し、再学習なし。同一ランは0/1を交換、別シードは次のseedのExpert 0を移植。集計は記述統計であり、donor共有を無視した有意差検定は行わない。

| タスク | split | 介入 | 平均悪化量 | 分散 |
| --- | --- | --- | ---: | ---: |
| precision | id | self | 0.000000 | 0.00000000 |
| precision | id | within_run | 0.187887 | 0.05068020 |
| precision | id | cross_seed | 0.038461 | 0.00205653 |
| precision | id | permutation_control | -0.000000 | 0.00000000 |
| precision | ood | self | 0.000000 | 0.00000000 |
| precision | ood | within_run | 0.192033 | 0.00879270 |
| precision | ood | cross_seed | 0.053140 | 0.00457900 |
| precision | ood | permutation_control | 0.000000 | 0.00000000 |
| selection | id | self | 0.000000 | 0.00000000 |
| selection | id | within_run | 0.489239 | 0.06631660 |
| selection | id | cross_seed | 0.190162 | 0.02309331 |
| selection | id | permutation_control | 0.000000 | 0.00000000 |
| selection | ood | self | 0.000000 | 0.00000000 |
| selection | ood | within_run | 0.287967 | 0.01154379 |
| selection | ood | cross_seed | 0.099428 | 0.00653441 |
| selection | ood | permutation_control | 0.000000 | 0.00000000 |

自己置換・対応Router置換の最大出力差は 4.77e-07（許容1e-5未満）。交換劣化は依存性を示すだけで、能力の局所移植に成功したとは解釈しない。別シードのExpert番号は機能的に整列していない。

## ルーティング診断（ID）

| タスク | 条件 | 平均Expert利用率 | 利用率entropy平均 | token entropy平均 | 選択pair数平均 |
| --- | --- | --- | ---: | ---: | ---: |
| precision | ternary_learned | 0.298, 0.240, 0.246, 0.216 | 1.2940 | 1.2874 | 5.75 |
| precision | ternary_fixed | 0.347, 0.282, 0.213, 0.159 | 1.2696 | 1.3349 | 6.00 |
| precision | fp_learned | 0.292, 0.238, 0.244, 0.226 | 1.3595 | 1.3278 | 5.88 |
| selection | ternary_learned | 0.208, 0.222, 0.278, 0.292 | 1.3553 | 1.1770 | 6.00 |
| selection | ternary_fixed | 0.347, 0.282, 0.213, 0.159 | 1.2696 | 1.3349 | 6.00 |
| selection | fp_learned | 0.271, 0.242, 0.267, 0.221 | 1.3653 | 1.2440 | 6.00 |

利用率は選択slotの割合で総和1、entropyは自然対数で最大ln(4)。異なるseedのExpert番号には同じ意味はないため、平均利用率から専門化を判断しない。個々の利用率・カテゴリ別利用率・MAE・誤差0.01以内率はJSONに保存。pair数は1段Top-2の組合せ数であり、多段path diversityではない。

## 解釈と次の検証

1. この選択問題では固定ランダム経路より学習経路が有望。ただし連続混合重みも学習しているため、離散経路選択単体の効果ではない。
2. 三値学習MoEは精密回帰IDで三値Denseより平均誤差が大きい。構造の追加が常に有効という説明は支持されない。
3. 選択IDではWide Denseの平均誤差がさらに小さい。学習経路の改善を、容量を増やす代替案より優れたものとはまだ判断できない。
4. 固定データ、2人工問題、単一学習設定、8シードに限定される。独立データ・複数問題族と検出力を確保した本実験が必要。
5. [改訂計画](STAR-Bit-validation.md) に従い、通常MoEと動的接続の差を小型Transformerで検証する。

## 再現

```bash
python3 experiments/pilot.py --seeds 8 --steps 400 --output results/pilot
python3 experiments/report.py
python3 -m unittest discover -s experiments -p "test_*.py"
```

必要ライブラリ：torch、numpy、scipy。生データ：[results.json](../results/pilot/results.json)。学習MoEの16 checkpointも同ディレクトリに保存。

実行ソースSHA-256：`64287d1d6384998ed6a489fbf3af0eed995648c3281f9f1a7379ed98aa914c8f`。
