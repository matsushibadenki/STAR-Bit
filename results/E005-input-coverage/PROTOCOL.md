# E005：入力到達性と深さを分離する（実行前設計、2026-09-11）

E004では学習精度自体が低かった。改善仮説は、学習前に出力から参照できる入力集合を広げることで、hard test exact-matchが改善する、というもの。配線はラベルを見ずに作る。

## 条件

1. random_skip：E004と同じ、入力と全過去段からのランダム配線。
2. random_layered：直前段のみから重複しない2接続をランダム選択。
3. coverage_layered：直前段のみから、参照入力集合の和集合が最大になる重複しない2接続を選択。同点は乱数で選択。

random_layeredを入れ、深い経路を必ず通る効果と入力範囲を広げる効果を分離する。coverageは人が設計した配線規則であり、接続を学習する実験ではない。

- 16seed 300–315、2タスク、3条件＝96訓練run。seedの結果による追加なし。
- 同一seedの初期logitsは全条件で完全一致。配線生成の乱数は独立系列。
- E004同様6入力、32→32→4、68ゲート、1,088logits。全段を実行する訓練予算を揃える。到達するゲート数やhard化後の演算数が同じとは主張しない。
- numeric＝3bit整数2個の4bit和、selection＝2bit制御の4bit循環シフト。固定split7001、32train/32testをE004から維持。新しい問題や独立testの確認実験ではなく、既知の小さな問題族に対する探索。
- NumPy、CPU一thread、全train batch、Adam lr0.03、400step、温度1固定、最終checkpoint。
- 主比較：各タスクでcoverage−random_layered、coverage−random_skipのhard test exact-match。追加の交互作用：(coverage−random_layered)_selection − (coverage−random_layered)_numeric。計5比較をHolm補正。
- 平均、不偏分散、16seed対応差、seed percentile bootstrap 95% CI、全65,536符号の両側検定を記録。
- 補助：soft/hard train/test精度、出力ごとの到達入力数、soft配線の上流ゲート数、hard回路のprimitive DAGゲート数、学習時間。
- 到達性に基づく上限：全64入力を到達入力の値で群分けし、各群の多数派ラベルから各出力bitの最良Accuracyを計算。平均はbit精度上限、最小値はexact-matchの緩い上限。有限のゲート表現・最適化制約を無視するため達成可能性の保証ではない。このラベル付き診断は配線生成にもモデル選択にも使わない。
- 全64入力でNumPy hard推論とprimitive回路の出力一致を検査。Module抽出法は今回変更しない。
- 900秒で未完なら進捗を保存して停止。旧実験フォルダを上書きしない。

この単体ゲート実験にRouter/Expertはない。負荷分散・固定ランダム経路・同一ラン/別seed交換を伴うMoE統合検証の代わりとはしない。
