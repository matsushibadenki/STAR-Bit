# E006 出力LUT比較・実行前設計（2026-09-11）

仮説：最終段の4入力LUTが2入力LUTよりhard test exact-matchを改善する。

3条件：gate2（E005 coverage）、lut2（同じ出力配線、真理値表4項をsigmoidで学習）、lut4（2本の出力配線を保持し、直前段から異なる2本を追加、16項をsigmoidで学習）。lut2によりゲートのパラメータ化変更と入力本数の効果を分ける。

- 隠れ段は32→32の16関数混合ゲート、配線はE005 coverage。初期重みと配線は同seedの条件間で一致。
- lut2はgate2の初期soft真理値表と同じ出力になるようlogitを設定。lut4はその表を追加2入力に沿って複製する。初期soft出力は3条件で一致し、hard出力は一致を要求しない。
- seed400–415、2問題族×3条件＝96run。numeric/selection、split7001、32train/32test、400step、Adam0.03、温度1、最終checkpoint。既知の小規模問題への探索である。
- 主比較はlut4−lut2とlut4−gate2を各タスクで計4比較、加えて(lut4−lut2)_selection−(lut4−lut2)_numericの交互作用、計5比較Holm補正。16seed平均・不偏分散・bootstrap CI・両側符号反転検定。
- 配線だけを追加するため正解・testは参照しない。hiddenは両条件とも同じだが学習後の値が一致するとは限らない。
- gate2=1,088学習logits、lut2=1,040、lut4=1,088。hard真理値表bits（hidden込み）は272/272/320。出力接続数は8/8/16。LUT1個を2入力ゲート1個と同じ面積として扱わない。
- hard化：hiddenはargmaxゲート、LUTは各表項のlogit>=0でbit化。全64入力で独立したhard評価器と照合する。
- 勾配を数値差分で検査し、900秒上限、途中結果保存、成功するまでのseed追加なし。Router/Expertはなく既存MoE対照の代替ではない。
