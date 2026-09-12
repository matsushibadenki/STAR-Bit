# E007：全入力学習と最適化予算の診断（2026-09-11、実行前）

仮説：全64入力の学習と更新数増加により、E006で残った誤差が減るかを調べる。全入力を学習した条件の評価は学習領域への適合であり、test/OOD汎化ではない。

- seed500–515の16個、numeric/selection、gate2/lut4、half32/full64の計128訓練trajectory。
- 同seedのモデルはデータ量条件間で初期値・配線完全一致。half32は従来split7001のtrain、full64は全入力。新split探索は今回はしない。
- Adam0.03、温度1、full batch。400stepと1600stepで同じtrajectoryを観測する。400step結果を見て延長可否を決めず、全runを1600まで進める。
- 同更新数でもfull64はhalf32の2倍の例を処理し、1600stepは400stepの4倍の更新・計算を使う。データ量だけの因果効果を完全には分離しない。
- 主指標：全64入力でのhard exact-match。主比較はtask×architectureごとにfull1600−half1600（4比較）、full1600−full400（4比較）、taskごとにlut4−gate2のfull1600（2比較）、計10比較をHolm補正。
- 各n=16、シード対応差・不偏分散・bootstrap CI・両側符号反転。400/1600を独立runとして数えない。
- 補助：soft/hardの全領域精度、学習対象精度、half条件のみ未学習32例の精度。full条件のunseenはnullとする。全入力一致したrunの件数も報告。
- 陽性対照：生6入力を直接受ける4出力LUT6（256sigmoid logit、hiddenなし）をfull64で400step学習。16seed×2tasks＝32追加run。全真理値表を格納可能な別アーキテクチャであり、暗記可能性と実装の対照。MoE／圧縮の優位性の対照ではない。主検定familyには含めない。
- 900秒上限、CPU一thread。過去結果非上書き、全checkpointと途中結果保存、全入力で独立hard evaluator一致検査。
- 全データでも残る誤差は、未知例不足だけでは説明できないが、表現不能と局所解・最適化失敗を分離した証明にはならない。

合計160訓練run（主実験128＋陽性対照32）。Router/Expertを含まないため元のMoE5条件の代替ではない。
