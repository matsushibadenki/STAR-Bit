# E004 実行前設計（2026-09-11）

今回の環境にはPyTorch/SciPyがないため、既存NumPyで16種の2入力Boolean関数を連続緩和し、解析的な逆伝播を実装する。原論文の再現とは呼ばない。研究フォルダは読み取り専用のため、一時領域に実験一式を用意して最後に保存権限を要求する。

仮説：softmax温度を1→0.2へ下げることで、温度1固定よりhard化後のtest exact-matchが改善する。ゲート抽出と符号化の正確性は全入力で独立に検査する。

- 2条件：温度1固定／1→0.2線形annealing。ゲート選択以外は固定。Router/MoEはなく負荷分散やExpert交換は適用対象外であり、従来の対照群の代用とはしない。
- seed 200–207の8個、2問題族、32訓練run。学習配線と初期logitsを条件間で共有。
- 6入力、32→32→4ゲート、各段は全過去の入力を参照する固定ランダム配線。計68ゲート、各ゲート16logits。最終4ゲートを4bit出力とする。
- numeric：3bit整数2個の和を4bit出力。selection：2bit制御と4bit入力の循環シフト。どちらも6入力64通り。
- 固定seed7001で64例を32訓練／32testへ分割。train/testに同じ入力はない。問題族は各1つ、OODではない。
- 全訓練集合batch、Adam lr0.03、400step、最終checkpoint。途中test選択なし。CPU一thread、時間上限900秒。
- 主比較：hard test exact-matchのannealed−fixed差を問題族ごとに符号反転検定、2比較Holm補正。平均、不偏分散、seed bootstrap percentile CIを報告。
- 副指標：soft test exact-match、hard bit accuracy、train exact-match、hard-soft差、モジュール化記述量、全64入力でのhard回路と抽出回路の一致。
- Module抽出はE003のglobal_acceptを再利用。NumPyのみで使える統計shimを用意し、E003本体は改変しない。16種ゲートを固定primitive式へ展開するため、ゲート辞書の符号化の冗長性も圧縮に含まれ、概念形成と呼ばない。
- 結果を見てseed、温度、step数、接続方式を変更しない。学習失敗・負の結果も記録。

[Next] 実装と勾配・真理値表検査。[Next] 固定32runと抽出。[Next] 研究フォルダへ保存。
