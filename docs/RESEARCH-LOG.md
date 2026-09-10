# STAR-Bit 継続研究ログ

ユーザー方針（2026-09-10）：改善案を継続的に加え、実験しながら研究を進める。

毎回、仮説→対照と評価設計→実装→実験→検証→結果と次案、の単位で完結する。改善しない結果も残し、理論的期待・コンパイラ実験・学習実験・実機測定を区別する。結果は実験ID別に保存し、過去の記録を上書きしない。

English: Continue research through bounded hypothesis–experiment–verification cycles; preserve negative results and separate exploratory findings from independent confirmation.

简体中文：通过有界的假设、实验、验证循环持续研究；保留负结果，并区分探索性发现与独立验证。

## E003：全体記述量でModule採用を判定する

設計記録日：2026-09-10。以下を実行前に固定。

- 動機：前回の局所頻度スコアは、候補の重なりと定義費用を十分扱えず、randomより良い記述を保証しなかった。
- 改善案：候補を実際に訓練回路へ適用し、ライブラリ費用込みの全体記述量が減るものだけを1個ずつ採用する。
- 仮説：従来functionalより評価回路の記述量が減る。ただし訓練側の単調改善は設計上の性質であり、汎化の証拠にしない。
- 独立seed：100–115の16個。前回の0–15を再利用しない。生成器は同じなので問題族に対する独立性はない。
- 条件：syntax、functional、random、global_accept。2問題族、合計128条件。
- 固定予算：3round、各round最大8候補。global_acceptは候補試行に余分な計算を使うので探索時間と候補評価数も記録し、同計算予算とは呼ばない。
- 主指標：評価回路の全ライブラリ定義費用込みdescription_symbols。functional−global_acceptを問題族ごとに検定し、2比較でHolm補正。
- 補助：訓練記述量、Module数、探索時間、元／展開後DAGゲート数、全2,048入力での等価性。
- 停止：16seed×2問題族×4条件で終了。結果を見てseed数・閾値・cut幅を変更しない。
- 保存先：results/E003-global-accept/。独立データでのコンパイラ比較でありDLGN学習や概念形成の検証ではない。

## 次の候補

- [Done] E003完了。評価記述の平均削減は加算8、選択57.3125 symbols。2比較のHolm補正pは各0.00006104。ただし同じ人工問題生成器での結果であり、加算の変動は退化。詳しくは[結果](STAR-Bit-E003-global-accept.md)を参照。
- [Next] 学習済みDLGNからの抽出へ進み、soft/hard精度と圧縮後精度を測る。
- [Later] Module採用に配線・端子・命令bit数を含む記述費用を導入。
- [Later] 分布A→B→Aで形成・分解・再獲得を比較。

## 定期実行

このタスクのheartbeat「STAR-Bitの継続研究」（ID: star-bit）を毎朝9時・日本時間で有効化した。毎回、小規模な改善実験を一つずつ進め、意味のある結果・失敗・判断が必要な場合に通知する。ローカル実験はCPU一thread・計算15分以内を目安に区切る。常時実行や必ず性能が向上することを意味しない。
