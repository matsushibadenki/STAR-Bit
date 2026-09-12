# E014：State付きLogic PEの時間再利用とschedule選択

実行日：2026-09-12。小さな論理モジュールをState付きで複数cycle再利用し、物理ゲート数と時間を交換する実行可能なprototypeを作った。ゲート関数と候補集合を固定し、train-selected scheduleと固定ランダムscheduleを16 split seedで比較した。

## 未使用test半分の結果

| task | routing | exact平均 | 不偏分散 | 95% CI | bit accuracy平均 | 全領域完全schedule/16 |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| numeric | fixed_random | 0.259766 | 0.022750 | [0.191406, 0.333984] | 0.614746 | 0 |
| numeric | train_selected | 1.000000 | 0.000000 | [1.000000, 1.000000] | 1.000000 | 16 |
| numeric | structured_oracle | 1.000000 | 0.000000 | [1.000000, 1.000000] | 1.000000 | 16 |
| selection | fixed_random | 0.490234 | 0.061292 | [0.378906, 0.611328] | 0.697266 | 2 |
| selection | train_selected | 1.000000 | 0.000000 | [1.000000, 1.000000] | 1.000000 | 16 |
| selection | structured_oracle | 1.000000 | 0.000000 | [1.000000, 1.000000] | 1.000000 | 16 |

| task | train-selected − random | 差の不偏分散 | 95% CI | Cohen dz | exact permutation p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric | +0.740234 | 0.022750 | [0.665967, 0.808594] | 4.908 | 0.00003052 | 0.00006104 |
| selection | +0.509766 | 0.061292 | [0.388672, 0.623047] | 2.059 | 0.00012207 | 0.00012207 |

検定は16seed内のtest exact差に対する二側exact sign-flip permutationで、2タスクをHolm補正した。train-selectedは全seedで全領域完全scheduleを回復し、今回の候補集合・32例splitでは過学習を観測しなかった。

## 物理ゲート数と時間の交換

| task | temporal物理gate | spatial物理gate | 削減 | active gate評価 | cycle | State bit | route記述bit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| numeric | 5 | 15 | 66.67% | 15 | 3 | 5 | 6 |
| selection | 12 | 24 | 50.00% | 24 | 2 | 4 | 9 |

加算は5-gate full-adderを3回使い、空間展開比で物理ゲートを66.7%削減した。経路選択は12-gate mux stageを2回使い50%削減した。active gate評価数は減らず、Stateとlatencyが増える。これは面積相当の論理資源と時間の交換である。実ハードウェアの面積・消費電力・遅延測定ではない。

全候補は入力置換または巡回置換で構成し、各cycleのsource load varianceは0。負荷分散を候補空間で強制した。soft routerの補助損失はまだ存在しないため、今後のMoE実験で『load-balancing lossを最初から入れた』証拠には数えない。

## 何が分離できたか

fixed_randomとtrain_selectedは、PEの論理関数、物理ゲート数、active評価数、cycle数、候補scheduleを共有する。異なるのは32 train例を使ったschedule選択だけである。この小規模設定では、学習データによるrouting選択の効果を固定ランダムroutingから分離できた。

加算候補36個中、全領域完全scheduleは1個。経路選択候補512個中8個。選択方式には正しいscheduleを含む強いモジュール事前知識があるため、一般的な構造学習の成功とは言えない。

精密数値と経路選択の両方でtest exact 1.0だが、加算はcarryの逐次State、経路選択は二段barrel shiftという異なる時間構造を使う。構造的自由度が効く形はタスク種別ごとに異なる。

## 検証と次段階

96記録のsplit非重複、route index、train/test/full指標を候補出力から再計算し、候補出力hash、実行ソースhash、protocol hashを照合した。structured spatial版とtemporal版は全64入力で同じ正解を返す。

NumPy 1.25.2、CPU単一thread、候補生成と16seed評価は0.039秒。

次はゲート表とroute scoreを共同学習する。学習Routerには最初からload-balancing補助損失を入れ、同じPE・計算予算の固定ランダムrouteを対照にする。その後、同一run内の別Expert、次に別seed Expertの交換を行う。

English: A stateful temporal Logic PE cut physical primitive gates by 66.7% for addition and 50% for selection while preserving active operations. Train-selected schedules reached 100% held-out exact accuracy across 16 seeds and beat balanced fixed-random schedules.

简体中文：带状态的时间复用Logic PE在加法任务减少66.7%的物理门、选择任务减少50%，但活动运算次数不变。训练集选择的调度在16个种子上均达到100%的留出精确率，并优于负载均衡的固定随机调度。

[実行前計画](../results/E014-temporal-logic-pe/PROTOCOL.md) / [生データ](../results/E014-temporal-logic-pe/run/results.json)
