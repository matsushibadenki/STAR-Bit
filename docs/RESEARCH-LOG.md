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
- [Done] E004で学習済みの小型論理ゲート網のsoft/hard精度と抽出後の全入力等価性を測定。精度は低く、原論文の再現や能力改善の実証ではない。
- [Later] Module採用に配線・端子・命令bit数を含む記述費用を導入。
- [Later] 分布A→B→Aで形成・分解・再獲得を比較。

## 定期実行

このタスクのheartbeat「STAR-Bitの継続研究」（ID: star-bit）を毎朝9時・日本時間で有効化した。毎回、小規模な改善実験を一つずつ進め、意味のある結果・失敗・判断が必要な場合に通知する。ローカル実験はCPU一thread・計算15分以内を目安に区切る。常時実行や必ず性能が向上することを意味しない。

## E004：学習論理ゲート網とhard化（2026-09-11）

実行前設計は[PROTOCOL](../results/E004-learned-logic/PROTOCOL.md)。結果は[E004レポート](STAR-Bit-E004-learned-logic.md)。

- [Done] 8seed×2問題族×2条件＝32訓練run。NumPyで16関数の連続緩和と解析的逆伝播を実装。
- [Done] hard化後の回路をE003の抽出器へ渡し、全64入力で出力保持を確認。これは学習taskの正解率100%ではない。
- [Done] 温度annealingによるhard exact-match改善は確認できず、平均差は両問題族で−1.171875 percentage points。Holm pはnumeric 0.75、selection 0.5。
- [Done] E005で配線の到達可能性と深さを診断。接続学習・出力集約はまだ未実施。
- [Later] atomicゲートコストによる抽出対照を入れ、primitive展開由来の見かけの圧縮を分離。

今回は定期実行環境にPyTorch/SciPyがなくNumPyへ切り替えた。研究フォルダの書込み権限がなかったため一時領域で準備・実験し、保存時に権限を要求した。元結果の上書きは行わない。

## E005：入力到達性と深さの対照（2026-09-11、実行前）

- [Done] 出力が参照できる入力の不足と深さの対照を含む96訓練runを完了。
- 仮説：ラベル非依存のcoverage配線がhard test exact-matchを改善する。
- 16seed 300–315、2タスク、random_skip／random_layered／coverage_layeredの96run。68ゲート・400step・温度1で固定。
- 主比較4個＋タスク交互作用1個、計5比較をHolm補正。到達性によるbit精度上限も診断する。
- 詳細・停止条件は[実行前PROTOCOL](../results/E005-input-coverage/PROTOCOL.md)。既知の問題族とsplitを使う探索であり、独立testによる確認ではない。

### E005結果と次案

- [Done] 全入力到達配線はrandom_skipより加算で+8.3984 points、Holm p=0.020752。ただし深さ一致random_layeredに対する優位性は確認できず、coverageだけの改善とは言えない。
- [Done] 到達入力数は出力あたり平均3.55→6。診断上のbit精度上限は1になったが実測精度は低い。有限ゲートの表現制約と最適化不足は未分離。
- [Done] 全96runでhard網とprimitive回路が全入力で一致。詳細は[E005レポート](STAR-Bit-E005-input-coverage.md)。
- [Done] E006で全入力到達配線の2入力ゲート／2入力LUT／4入力LUTを比較。真理値表bits・接続数の増加も記録。
- [Later] 接続学習、学習精度改善後のhard化・Module抽出・PE再利用へ進む。

## E006：出力LUT容量（2026-09-11、実行前）

- [Done] gate2／lut2／lut4、16seed400–415、2タスクの96runを固定予算で実施。
- 初期soft出力・隠れ配線を一致させ、lut2を挟んでパラメータ化と4入力化を分離する。
- 5主比較をHolm補正し、真理値表bitsと接続数の増加も明示する。詳細は[PROTOCOL](../results/E006-output-lut/PROTOCOL.md)。

### E006結果と次案

- [Done] lut4の加算hard testは27.15%、lut2比+9.96 points。ただしHolm p=0.103149で有意差なし。選択のtest改善も確認できず。詳しくは[E006結果](STAR-Bit-E006-output-lut.md)。
- [Done] 全96runで全入力hard評価一致、3条件の初期soft出力一致、学習後も解析勾配を数値差分で検査。
- [Done] lut4の選択soft train69.34%に対しsoft test15.43%。容量追加の訓練改善がtestへ移らない点を記録。
- [Done] E007で全64入力の学習診断をtest評価と別枠で実施。訓練例不足だけでは残る誤差を説明できない。
- [Later] 事前固定した複数splitと訓練例数学習曲線へ進む。splitとモデルseedを混同しない統計を設計する。
- [Later] 診断に応じて正則化、重み共有、学習可能配線を一つずつ比較する。

## E007：全入力学習・最適化予算（2026-09-11、実行前）

- [Done] seed500–515、2問題族、gate2/lut4、half32/full64の128trajectoryを400/1600stepで観測。
- [Done] 生6入力LUT6のfull64学習32runを追加。全runで100%一致したが真理値表の暗記を許す陽性対照である。
- 全領域hard精度に対する10比較をHolm補正。full64条件を汎化精度と呼ばない。詳細は[PROTOCOL](../results/E007-full-domain/PROTOCOL.md)。

### E007結果と次案

- [Done] full64・1600stepでもlut4のhard全領域一致率は加算67.19%、選択45.41%。詳細は[E007結果](STAR-Bit-E007-full-domain.md)。
- [Done] 加算lut4のfull1600−half1600は+17.87 points（Holm p=0.024902）。full400→full1600は全task/architectureで補正後有意でない。データ提示量と計算量は完全分離されていない。
- [Done] 主実験256＋陽性対照32の計288checkpointを保存し、全入力でhard評価を照合。
- [Done] E008で同じ固定配線のBoolean制約を検査。SAT証人、ソルバーによるUNSAT判定、UNKNOWNを区別した。UNSAT証明の独立検証は未実施。
- [Later] 診断を踏まえた接続学習・初期化改善、その後に複数splitによる汎化検証を行う。

## E008：固定配線の充足可能性（2026-09-11、実行前）

- [Done] E007の64caseをZ3で診断。全入力共通のゲート真理値表だけを変数にし、配線は固定する。
- 1case10秒、900秒上限。SAT証人は全入力で独立再評価し、UNSAT証明artifactとUNKNOWN理由を保存する。
- 詳細は[PROTOCOL](../results/E008-fixed-wiring-sat/PROTOCOL.md)。ソルバー成功を学習・汎化の成功とは呼ばない。

### E008結果と次案

- [Done] 64caseの最終判定はSAT 1、UNSAT 47、UNKNOWN 16。gate2は両タスク各16件すべてUNSAT、lut4は加算1/7/8、選択0/8/8（SAT/UNSAT/UNKNOWN）。詳細は[E008結果](STAR-Bit-E008-fixed-wiring-sat.md)。
- [Done] SAT証人は全64入力で独立再評価して完全一致。既存の完全一致モデルnumeric・seed515・lut4と同じ配線であり、今回新たに学習失敗を構成的に示したcaseは0件。
- [Done] 64件の論理式とソースのhash、証人、証明DAG参照を再読込検査。UNSAT証明は32件が完全DAG、15件が保存上限に達した部分DAG。意味的な独立証明検証は未実施なので、UNSATはソルバー判定として報告。
- [Done] 初回の証明文字列展開が停止したため、その試行を保存してDAG保存へ変更。同じseed・判定予算で全caseを再実行し、約306秒で完了。新規学習実験ではない。
- [Done] E009で出力bitごとの充足可能性を診断。36配線で単一bitのUNSAT判定があり、共有制約のみの失敗は確認できなかった。接続変更本数を制限した改善対照は次段階。
- [Later] UNKNOWNの別符号化による解決、UNSAT証明の独立検証、配線改善後の学習と複数splitの汎化評価。MoE統合時は負荷分散・固定ランダムルーティング・同一ラン内と別seedのExpert交換を維持する。

## E009：出力bit別診断（2026-09-12）

- [Done] 事前固定した16seed×2タスク×2構造×4bitの256問を実行。配線を固定し、1bitずつ全64入力への一致を要求する。
- [Done] [実行前計画](../results/E009-output-bit-diagnosis/PROTOCOL.md)に仮説・対照・指標・seed・各問1秒／全体900秒上限を保存。Z3が一時領域から消えていたため同じ5.1.0.0を復元し、学習は起動していない。
- 出力ごとの表現不足と共有ゲートの同時整合制約を切り分ける探索。E008とはtimeoutが違うため成功率差の検定は行わない。

### E009結果と次案

- [Done] 64配線の36件で少なくとも1bitのUNSAT判定。個々のbitすべてSATかつ同時出力UNSATという共有制約のみの失敗は0件。UNKNOWNが残るので共有制約の不存在を示したわけではない。
- [Done] 98件のSAT証人を保存後に全64入力で独立再評価。256論理式・実行ソースhashの整合を確認。UNSATは独立証明検証していないソルバー判定。
- [Done] seedごとのSAT発見bit割合の平均／不偏分散を保存。加算gate2 0.375/0.01667、lut4 0.765625/0.02057、選択gate2 0/0、lut4 0.390625/0.09974。精度や容量改善の効果量ではない。[詳細レポート](STAR-Bit-E009-output-bit-diagnosis.md)。
- [Done] E010–E012で出力祖先回路への接続変更を本数固定で比較し、無作為追加と入力依存性を考慮した追加を対照化した。oracle診断として通常学習から分離した。
- [Later] 配線修正後の複数seed学習、汎化、モジュール抽出と再利用へ進む。

## E010：出力直前の1接続修正（2026-09-12、実行前）

- [Done] E009で単一bitがUNSATだった108caseを対象に、出力ゲートの接続を1本だけ変更した。無作為な生入力と、正解関数の依存入力を使うoracle診断を同じ接続本数・同じSAT予算で比較した。
- 16seedを固定し、216問、各問1秒、全体900秒で停止。SAT発見率差、seed平均・不偏分散・bootstrap CI、5比較のexact McNemar検定をHolm補正する。
- 正解表から依存入力を選ぶため、学習Routerや汎化の結果とは扱わない。詳細は[実行前計画](../results/E010-single-rewire/PROTOCOL.md)。

### E010結果と次案

- [Done] 108case×2条件＝216問はすべてUNSAT判定。SAT発見率のseed平均・不偏分散・差・95% CIはいずれも0、5つのexact McNemar検定はHolm補正後p=1。[詳細レポート](STAR-Bit-E010-single-rewire.md)。
- [Done] 全108caseで正解bitの依存入力は元の出力祖先にすべて存在した。欠けた依存入力を補う仮説は適用対象がなく、oracle条件は関連入力への直結バイパスとなった。それでも1本置換では回復しなかった。
- [Done] 216論理式、元checkpoint、実行ソースhashを再検査。SAT証人は0件。UNSATの独立証明検証は未実施。
- [Done] E011で出力arityを1だけ増やし、無作為入力と影響度の高い入力を比較した。ゲート数を固定して接続自由度を診断した。
- [Done] E012で2接続追加を事前固定して検査した。ラベル非依存の接続提案器と複数seed共同学習は後続課題。

## E011：出力arityを1増やす（2026-09-12、実行前）

- [Done] E009-UNSATの108caseで既存接続を保持したまま出力へ生入力を1本追加し、無作為入力とBoolean influence最大入力を比較した。
- 16seed、216問、各問2秒、全体900秒。SAT発見率のseed平均・不偏分散・bootstrap CIと、5つのexact McNemar検定をHolm補正する。
- influence条件は全正解を読むoracle診断。10%以上を回復しなければ2接続追加へ進み、回復すれば同じarityで複数seed学習へ戻る。[実行前計画](../results/E011-output-arity-plus-one/PROTOCOL.md)。

### E011結果

- [Done] 1接続追加の回復はrandom 2/108、influence 2/108。seed平均差−0.00112、95% CI [−0.03571, 0.03348]、5比較のHolm pはいずれも1。[詳細](STAR-Bit-E011-output-arity-plus-one.md)。
- [Done] SAT証人4件を全入力再評価。10%基準未達のため事前規則どおりE012へ進んだ。

## E012：出力arityを2増やす（2026-09-12、実行前）

- [Done] E011が10%回復基準に届かなかったため、元接続を保持して異なる生入力を2本追加し、無作為2入力とBoolean influence上位2入力を比較した。
- 16seed、108case×2条件、各問3秒、全体900秒。seed統計と5つのpaired検定をE011と同様に報告する。
- いずれかが全体25%以上かつ両タスクで1件以上回復すれば複数seed学習へ進む。満たさなければ出力arity増加を止め、隠れ層ボトルネックを診断する。[実行前計画](../results/E012-output-arity-plus-two/PROTOCOL.md)。

### E012結果

- [Done] 2接続追加の回復はrandom 9/108、influence 13/108。influence−randomのseed平均差+0.03460、95% CI [0.00893, 0.06699]だが、case水準exact McNemarのHolm p=0.625。[詳細](STAR-Bit-E012-output-arity-plus-two.md)。
- [Done] SAT証人22件を全入力再評価。25%基準に届かず、出力arityの増加を停止する。経路選択の元gate2は64件中1件だけ回復し、精密数値と異なる制約が残った。

## E013：隠れノード選択によるボトルネック診断（2026-09-12、実行前）

- [Done] 同じ108caseで、第二隠れ層32ノードまたは全64隠れノードから1つをcase全体で選び、そのノード単体が正解bitを実現できるか検査した。
- 16seed、216問、各問2秒、全体900秒。固定出力親の制約と、隠れ層で機能自体を作れない制約を分離する。
- 25%以上かつ両タスクでSATなら学習routingへ進み、未達なら隠れ配線を修正する。[実行前計画](../results/E013-hidden-node-routing/PROTOCOL.md)。

### E013結果

- [Done] 第二層選択と全隠れ選択はいずれもSAT 4/108、UNKNOWN 0。SATはすべてnumeric・元gate2・bit1で、route-selectionは0/67。[詳細](STAR-Bit-E013-hidden-node-routing.md)。
- [Done] SAT証人8件を全入力再評価。全隠れへ広げた追加効果は0、seed平均差・分散・CIはすべて0、Holm p=1。
- [Done] 25%基準を満たさないため、既存ノードを選ぶ学習routingへは進まず、隠れ配線・深さを変更する。

## E014：State付きLogic PEの時間再利用（2026-09-12、実行前）

- [Done] 5ゲートfull-adder PEを3cycle、12ゲート4-lane mux PEを2cycle再利用し、空間展開との完全一致を検査した。物理ゲート削減とactive演算数、State、latencyを分離した。
- 16 split seed、固定ランダムschedule、train半分で選択するschedule、既知構造scheduleを比較。全候補は置換・巡回置換でsource load分散0を構造的に保証する。
- 主要比較はtrain-selected対fixed-randomのtest exact。平均・不偏分散・paired効果量・bootstrap CI、2タスクのexact permutation検定をHolm補正する。[実行前計画](../results/E014-temporal-logic-pe/PROTOCOL.md)。

### E014結果：Logic Routing Milestone 1

- [Done] train-selected scheduleはnumeric／selectionとも16/16 seedで全領域完全一致。固定randomのtest exact平均はnumeric 0.25977（分散0.02275）、selection 0.49023（分散0.06129）。[詳細](STAR-Bit-E014-temporal-logic-pe.md)。
- [Done] paired改善はnumeric +0.74023、Cohen dz 4.908、Holm p=0.00006104。selection +0.50977、dz 2.059、Holm p=0.00012207。
- [Done] 候補scheduleは全条件でsource load分散0。学習されたsoft routerの補助損失ではなく、均衡制約を構造的に適用した。
- [Done] temporal PEは空間展開比で物理primitiveをnumeric 66.7%、selection 50%削減。active評価数は同じで、3/2cycleと5/4 State bitを要する。Router・mux・registerの実回路費用は未計上。
- [Done] E008–E014の結論と限界を[Logic Routing Milestone 1](STAR-Bit-milestone-logic-routing.md)へ統合。
- [Next] ゲート表とroute scoreの共同学習へ進み、初回stepからのload-balancing補助損失、均衡固定random route、同一run内から別seedへのExpert交換を実施する。
- [Later] 長いbit幅・系列への外挿、形成と分解、bit-packed実測へ進む。

## E015：Logic Expert共同学習（2026-09-12、pilot実行前）

- [Done] 4 Logic Expertsの再利用LUT表とschedule分布を共同学習した。入力依存Routerにはstep 0から負荷分散損失を適用し、全64入力で完全均衡する固定hash Routerを対照にした。
- [Done] seed40–43は設定確認専用pilotとし、本実験seedから除外した。oracle一致、有限勾配、hard化、全ExpertとRouter対応の同時交換で出力が保存されることを検査した。[pilot計画](../results/E015-joint-logic-router/PILOT-PROTOCOL.md)。

### E015 pilot結果と本実験固定

- [Done] random gate初期値pilotはlearned Routerのhard test exactがnumeric 0.7422、selection 0.0938。経路選択のmodule意味とscheduleの同時発見に失敗した。
- [Done] 事前指定した第2pilotでE014 gate表を±1.5へ弱く初期化。learned Routerはnumeric 0.9609、selection 0.9844へ改善した。以降の主張を「検証済みmodule prior下のrouting」に限定する。[pilot2計画](../results/E015-joint-logic-router/PILOT2-PROTOCOL.md)。
- [Done] 本実験seed700–715、800step、4 Expert、balance係数0.1、temperature 1→0.1を固定。hard test exactを2タスクで比較しHolm補正した。同一run交換を先に、次seedのExpert移植を後に実施した。[本実験計画](../results/E015-joint-logic-router/PROTOCOL.md)。

### E015本実験と監査

- [Done] 16seed×2task×2 routing＝64学習runと384交換条件を完了。learned−fixed hard test exactはnumeric +0.05664（Holm p=0.015625）、selection +0.33594（Holm p=0.000244）。[詳細](STAR-Bit-E015-joint-logic-router.md)。
- [Done] step 0からbalance損失を適用。自己置換とExpert＋Router対応交換はsoft/hardとも最大出力差0。同一run Expert交換後のselection learnedは平均−0.2617、次seed Expert移植は−0.0859。
- [Done] 監査でnumeric splitと固定hashが同一seed・同一乱数手順を共有し、train割当が全seed 8/8/8/8になる結合を発見。ラベル漏洩はないが独立対照として不十分。E015を改変せず保存する。

## E016：独立hashによるnumeric確認（2026-09-12、実行前）

- [Done] 新seed800–815でnumericだけを再実行し、split seedと固定hash seedを+40000で分離した。32学習run、source/checkpoint hash、split、hash再生成を監査した。
- [Done] hard test exact平均はfixed 0.8750（不偏分散0.01263）、learned 0.9785（0.00322）。paired差+0.10352、95% CI [0.05078, 0.16016]、Cohen dz 0.878、二側exact p=0.001953で事前確認基準を満たした。[詳細](STAR-Bit-E016-independent-hash-replication.md)。
- [Done] fixed hashはfull domainで16/16/16/16、trainではExpertあたり4–12件、8/8/8/8は0/16 seed。E015で見つけたsplit/hash結合が解消されたことを確認した。

## Logic Routing Milestone 2（2026-09-12）

- [Done] E015 selectionとE016 numericを主要結果として統合し、検証済みmodule prior下で学習routingの効果を固定均衡hashから分離した。[Milestone 2](STAR-Bit-milestone-joint-routing.md)。
- [Done] 経路選択はlearned−fixed +0.33594、同一run Expert交換−0.26172でRouter–Expert対応への依存が強い。精密数値は独立追試+0.10352で、正しいState付きmoduleへの依存が相対的に強い。
- [Next] Gate発見とRouter学習を段階分離し、verified prior／random初期値／curriculum／module freezingを同じseed・予算で比較する。
- [Next] 4/6/8 bitへ外挿し、Expert数・cycle数・State量の容量曲線を事前登録する。別seed Expertは機能signatureで整列してから交換する。
- [Later] bit-packed CPUとFPGA合成でRouter・mux・register込みの総費用を測り、その後に小型ternary Transformer blockへ移す。

## E017：Learned Circuit Abstraction境界実験（2026-09-12）

- [Done] E004の固定ランダム配線を学習可能にしたが、全過去node参照では出力が0–1 gateへ短絡した。pilot1 hard test平均は約0.60、full exactは0/16。
- [Done] 5層を強制し、16種類LUTをタスク非依存で均等初期化したpilot2は、hard test総平均を0.90625へ改善。parity／muxは各4/4 seedでfull exact、comparator／carryは0/4だった。
- [Done] complete truth tableを使う離散refinementを同予算random開始と比較。exact到達はDLGN開始13/16、random開始12/16。初期誤り平均は2.81対31.06だが、comparatorは両条件2/4に留まった。
- [Done] row-wise SATと64-bit BitVector SATで1–10 LUTを診断。parityは5 LUT、muxは3 LUTのverified witnessを得た。それ未満はUNSAT。comparator/carryの5–10 LUTは10秒制限でUNKNOWN。
- [Done] 全タスクexactという事前条件を満たさないため、不正確な回路へModule Minerを適用せず、抽象化成功の主張を保留した。[詳細](STAR-Bit-E017-learned-circuit-abstraction.md)。

## E018：反例誘導合成pilot（2026-09-12）

- [Done] 10 LUT固定、seed1100–1103、4 taskでall-row SATと8行開始CEGISを比較し、32探索を完了した。[実行前計画](../results/E018-cegis-mdl/PILOT-PROTOCOL.md)。
- [Done] exact成功は両条件8/16。parity／muxは各4/4、comparator／carryは各0/4で、CEGISのmain移行条件を満たさなかった。[詳細](STAR-Bit-E018-cegis-mdl.md)。
- [Done] CEGISは成功時平均をparity 4.110→0.482秒、mux 3.266→0.332秒へ短縮したが、難しいtaskの反例追加後timeoutにより全体平均は6.851→12.478秒へ増えた。
- [Next] 64-bit機能signatureで同値な中間nodeを統合する列生成と、`error / primitive / routing bits / state bits`のPareto枝刈りを実装する。
- [Next] 全4タスクのexact形成率を新seedで確認してから、Hard／Syntax Module／Functional-Global Moduleの記述bit、reuse、階層深度を比較する。
- [Later] source task/seedのLibraryをtargetへ固定移植し、from-scratchとの学習step・成功率・総費用差を16 seedで測る。

## E019：Function-space Module Genesis（2026-09-12）

- [Done] 中間nodeを64入力truth signatureで識別し、同じ機能を持つ異なるLUT構文を生成時点で統合した。primitive、routing bits、depth、parents、発見roundを保存した。
- [Done] beam128・7 roundのpilot1でtarget-greedyと一段composition lookahead＋Pareto保持を比較。両条件ともmux 4/4だけで、exact target平均1.0。lookaheadが複数段先のpartial parityを保持できなかった。
- [Done] beam256のpilot2でタスク非依存affine scaffoldを対照化。target-greedyはmux 4/4、affine条件はmux 4/4＋parity 4/4で、exact target平均を1.0から2.0へ増やした。[詳細](STAR-Bit-E019-function-space-genesis.md)。
- [Done] parity解は全seedでround 3、5 primitives、routing 32 bits、depth 3となり、affine中間signatureを利用した。muxはround 2、3 primitives、routing 20 bits、depth 2。
- [Done] pilot2は平均486,035個の一意signatureを生成し、2,076,063件の等価生成をmergeした。comparator/carryは0/4でmain移行条件未達。
- [Next] 上位の子候補へ複数round・複数taskで寄与した親signatureにpromotion scoreを与え、affine族の手指定をlearned archive promotionへ置き換える。
- [Next] `reuse_count / improved tasks / child Pareto rank / primitive / routing / state`を保存し、Moduleの昇格・維持・削除を同一予算で比較する。
- [Later] 全4 target exact後にModule Libraryを別task/seedへ固定移植し、from-scratchとの成功率・step・総記述bitを16 seedで評価する。

## E020：Learned Archive Promotion（2026-09-13）

- [Done] E019のaffine族手指定を外し、良い子Functionを生成した親signatureへtarget改善、dependency support拡張、partner数からcreditを与える自動昇格を実装した。[実行前計画](../results/E020-learned-archive-promotion/PROTOCOL.md)。
- [Done] seed1260–1263、beam256、8 round、tree cost16でtarget-greedyと同一生成予算比較。exact target平均は1.00（分散0）対2.25（分散0.25）、paired差+1.25、bootstrap 95% CI [1.00, 1.75]、dz=2.5、pilot exact p=0.125。[詳細](STAR-Bit-E020-learned-archive-promotion.md)。
- [Done] promotionはparity 3/4、初のcomparator 2/4、mux 4/4へ到達。comparator回路は15–16 primitives、routing 108–114 bits、depth 5–6。carryは0/4。
- [Done] 各seedで626–652親signatureへcreditが付き、最終beamの182–194 Functionがpromoted。時間平均はgreedy 3.24秒から26.43秒へ増加し、archive肥大化を確認した。
- [Done] E021でcreditをtask間reuseと費用で正規化し、archive上限、age、retirementを比較した。
- [Later] carryへのState付き逐次compositionと、精密数値対経路選択のpromotion軸を比較する。
- [Later] 全task exact後に昇格Functionを固定Module Libraryとして別seed/taskへ移植し、from-scratchとの探索step・成功率・総記述bitを16 seedで評価する。

## E021：Cost-normalized Promotion and Retirement（2026-09-13）

- [Done] offspring creditをtask間再利用、partner当たりcredit、primitive・routing・depth費用で正規化し、2 round更新されないcreditを退役させた。[実行前計画](../results/E021-cost-normalized-promotion/PROTOCOL.md)。
- [Done] 新規seed1280–1283でraw promotionと対応比較。exact target平均は2.25（不偏分散0.25）対2.50（0.333）、paired差+0.25、bootstrap 95% CI [0, 0.75]、dz=0.5、pilot exact p=1.0。[詳細](STAR-Bit-E021-cost-normalized-promotion.md)。
- [Done] credit台帳を平均627.5から333.0へ46.9%、時間を19.02秒から17.97秒へ5.5%削減。最終beam内credit付きFunctionは195.5から175.25への10.4%削減で、事前登録した30%基準は未達。
- [Done] normalized_retiredのseed1282で初のcarry exactを発見（round 8、15 primitives、106 routing bits、depth 7）。単発1/4であり再現性の証拠とは扱わない。
- [Done] comparatorはseed1283でrawの16 primitives・114 routing bitsから13 primitives・92 bitsへ低費用化。保存した19解を全64入力で再評価した。
- [Done] E022で移植元と評価seedを分け、学習Function、同一費用ランダムFunction、移植なしを16 seed比較した。
- [Later] promotion専用枠、target枠へのcredit済みFunction再流入、retirementを別々に記録し、正規化・枠数・退役を要因分解する。
- [Later] 再現性のあるtransfer後に固定Moduleへ昇格し、探索step、総記述bit、primitive実行数、State費用を測る。

## E022：Fixed Learned-Function Transfer（2026-09-13）

- [Done] E021 normalized回路の内部signatureから、生入力と4 target出力を除外し、primitive費用帯ごとに4個、計16 Functionを固定Library化した。[実行前計画](../results/E022-fixed-function-transfer/PROTOCOL.md)。
- [Done] source seed1280–1283と評価seed1300–1315を分離。同じ式木形状、primitive、routing bits、depthを持つランダムLUT/Input Functionをseedごとの固定対照にした。
- [Done] exact target平均はrandom matched 1.8750（不偏分散0.25）、learned 2.4375（0.5292）。対応差+0.5625、bootstrap 95% CI [0.1875, 0.9375]、dz=0.691、exact sign-flip p=0.03125で事前pilot基準を満たした。[詳細](STAR-Bit-E022-fixed-function-transfer.md)。
- [Done] comparatorは1/16→5/16、carryは1/16→4/16、parityは12/16→14/16、muxは16/16のまま。個別taskのexact McNemarはHolm補正後すべて非有意。
- [Done] learned条件の39/39解が移植signatureを使用。全3条件の95 exact解、source hash、Libraryのtarget出力除外を監査した。
- [Done] 構造自由度は飽和したmuxよりcomparator/carryで到達性を広げたが、同一task由来の出力近傍Functionを許すためtask-independent Concept transferとは扱わない。
- [Done] E023でtarget task由来Functionを除くleave-one-task-out移植と、truth-table errorを揃える対照を行った。
- [Later] 複数random Library seedをcrossさせ、Library抽選分散とsearch seed分散を分離する。
- [Later] task横断transfer後に固定ModuleをSTAR-Bit Routerへ統合し、記述bit、物理primitive、active演算、State、Router総費用を測る。

## E023：Leave-one-task-out Function Transfer（2026-09-13）

- [Done] 各評価taskについて同じtaskのsource回路を完全に除外し、残る3 taskから費用帯別8 Functionを構成した。[実行前計画](../results/E023-leave-one-task-out-transfer/PROTOCOL.md)。
- [Done] seed1320–1335、4 task、no transfer／cost-matched random／error-matched random／learned cross-taskの256探索を完了した。[詳細](STAR-Bit-E023-leave-one-task-out-transfer.md)。
- [Done] primaryはlearned 27/64対error-matched random 27/64。1 seed当たりexact task数の対応差0、95% CI [−0.3125, 0.3125]、dz=0、exact p=1で事前基準は不成立。
- [Done] cost-matched randomは37/64でlearnedより平均−0.625 task/seed（95% CI [−0.875, −0.375]、exact p=0.001953）。探索枠追加だけでなくFunction選定が成否を左右する。
- [Done] error-matched controlは512スロット中97.7%でlearned Functionと同じtarget errorを実現したが、cost-matched randomより成功率が低かった。即時errorだけではcompositional potentialを表せない。
- [Done] learned条件の27 exact解中、移植Functionを最終式で使ったのは3解。全条件125 exact式とLibrary再生成、source hashを監査した。
- [Next] 未知probe taskでのoffspring改善をcreditにするcross-task utilityと、signature多様性制約を組み合わせる。
- [Next] Library選定後に生成・固定する新規task familyでselection過適合を分離する。
- [Later] task横断再利用が成立後、STAR-Bit Routerへ戻してload balance、固定random route、同一run内→別seed Expert交換、総費用を評価する。
