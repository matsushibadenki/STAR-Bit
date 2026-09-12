# E008：固定配線のBoolean充足可能性（2026-09-11、実行前）

目的：E007の同じ配線・hard関数集合で全64入力に正答できるかを検査し、勾配学習の失敗と表現不能を区別する。新たな汎化・学習実験ではない。

- E007 seed500–515、numeric/selection、gate2/lut4のfull64・1600step checkpoint計64個を対象にする。都合の良いseedを選ばない。
- 各2入力ゲートを自由な4bit真理値表、出力lut4は自由な16bit真理値表として表現。配線を変えず、全64入力の4出力を正解に一致させる。同じ表変数を全入力で共有する。
- Z3で1case最大10秒、単一thread、固定solver乱数seed0。SAT/UNSAT/UNKNOWNを別集計し、UNKNOWNのreasonを保存する。最大900秒、進捗保存。
- SATは得た表を独立NumPy評価器で全入力再評価し、全256出力bitの一致を要求する。証人表とSMT-LIB問題を保存する。
- UNSATはsolverの証明artifactも保存し、独立proof checkerは未使用であることを明示する。UNKNOWNは表現不能に分類しない。
- 既知SAT（2入力XOR）、既知UNSAT（第2入力を参照できないXOR）で符号化を検査する。E007で既に100%のcaseがUNSATなら処理を止める。
- 指標：各task/architectureのSAT・UNSAT・UNKNOWN件数、SATだがE007 hard精度<1の件数、SAT証人精度。E007全領域精度の平均・分散・CIも添える。
- 同じ配線の診断なので新規64訓練runとは数えない。solver成功率を学習能力・汎化率と呼ばず、学習済み完全一致率との有意差検定は行わない。
- 改善案の判断：SATで学習誤差が残るなら初期化・最適化・蒸留を検討。UNSATなら配線・容量変更が必要。UNKNOWNなら予算内の未判定として保留する。

参考：[Z3公式のSAT/UNSAT/UNKNOWN説明](https://microsoft.github.io/z3guide/docs/logic/basiccommands/)、[timeout/proof等の設定](https://microsoft.github.io/z3guide/programming/Parameters/)。Z3を一時ディレクトリへ隔離導入し、元環境のパッケージを変更しない。

## 保存処理の修正（最初の試行中断後、判定条件は維持）

最初の試行は6case目のUNSAT証明をsexprで展開する処理が停止したため終了した。旧コード・事前設計・5件の保存済み途中結果と未完artifactは残す。採用する最終試行はrun_boundedへ新規保存し、同じ64case・solver seed・各10秒を維持する。精度や判定結果を選ぶための再試行ではない。

証明を共有ASTのDAGとして保存し、走査3秒／100,000node上限を設ける。保存未完の場合は明示し、独立proof checker未使用という制約も維持する。E007に存在する完全一致checkpointの証人も独立再評価し、solverがUNKNOWNでも既知の構成的証拠があるcaseは区別して報告する。
