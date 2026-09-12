# STAR-Bit Logic Routing Milestone 1

更新日：2026-09-12。

## 到達点

小型Boolean課題に限り、STAR-Bitの中心仮説を次の三段階に分けて検査した。

1. 固定されたランダム配線で、ゲート関数だけを学習・合成しても解けない場合が多い。
2. 出力接続だけを少数変更しても大半は回復せず、隠れ配線と深さがボトルネックになる。
3. タスクに合う再利用可能なLogic PEとschedule候補を与えると、訓練例によるschedule選択が固定ランダムscheduleを大きく上回る。

これは「低bit演算で失う自由度を構造と時間で補う」という方向に、実行可能な小規模の肯定例を与える。ただし、候補scheduleにfull-adderとbarrel-shiftの強い事前知識を与えており、汎用的な構造学習や言語モデルでの有効性はまだ示していない。

## 証拠の流れ

| 段階 | 主な結果 | 解釈 |
| --- | --- | --- |
| E008 | 固定配線64case：SAT 1、UNSAT 47、UNKNOWN 16 | 学習率だけで直せない表現制約が多数ある |
| E009 | bit別256問：36/64配線で少なくとも1bitがUNSAT | 出力間共有だけでなく単一bitにも制約がある |
| E010 | 1接続置換：両条件0/108回復 | 全依存入力は到達済みで、単純な到達性修正では足りない |
| E011 | 1接続追加：random 2、influence 2/108 | 小さな出力容量追加の効果は限定的 |
| E012 | 2接続追加：random 9、influence 13/108 | 出力表を最大4倍にしても25%基準未達 |
| E013 | 任意隠れnode選択：4/108、selectionは0/67 | 固定出力親だけでなく隠れ配線内部が主要制約 |
| E014 | train-selected test exact：両task 1.0/16seed | モジュール事前知識内ではschedule選択効果を分離できた |

E014の固定ランダムscheduleに対するtest exact改善は、numeric +0.7402（95% CI [0.6660, 0.8086]、Holm p=0.000061）、selection +0.5098（95% CI [0.3887, 0.6230]、Holm p=0.000122）。PE論理、候補集合、active gate評価数、cycle数は比較群で同じで、異なるのはtrain半分を使ったschedule選択である。

## ゲート爆発への具体的な回答

加算では5個のprimitive gateからなるfull-adder PEを3cycle再利用し、15個の空間展開に対して物理primitive数を66.7%減らした。経路選択では12-gate mux-stageを2cycle再利用し、24個の空間展開に対して50%減らした。

その代わり、active gate評価数は加算15、選択24のまま減らず、latencyは3cycle／2cycle、Stateは5bit／4bit必要になる。Router、配線mux、register、clock、configuration memoryの回路面積は未計上である。したがって現段階の結果は、実チップの面積削減ではなく、論理モジュール数と時間の交換をソフトウェア上で確認したものになる。

## タスク種別による違い

精密数値ではcarryを保持して下位bitから順に処理する時間構造が効いた。経路選択では4bit Stateに対し、selectorごとのmux-stageを2回適用する構造が効いた。両方とも構造自由度が有効だったが、再利用するStateとmoduleの意味は異なる。

固定二層網では、経路選択の単一bit 67caseが任意隠れnode選択でもすべてUNSAT判定だった。経路選択は、入力到達性よりも段階的な条件付き処理を必要とする。一方、精密数値では一部の低位bitが浅い回路でも構成可能で、上位carryほど深さが必要だった。

## まだ証明していないこと

- E014のschedule候補は人手で制約した36／512候補で、汎用Routerが構造を発見した結果ではない。
- 全64入力から分けた32/32評価であり、入力bit数や系列長を伸ばす外挿ではない。
- ゲート表は手書きmoduleで、ゲート関数とrouteの共同学習ではない。
- source loadは候補構造で完全均等にしたが、soft Routerのload-balancing補助損失はまだ検証していない。
- Logic Expertの同一run内・別seed交換はまだ行っていない。従来MoE pilotでは実施済みだが、Logic PEへは移せない。
- Z3のUNSATは独立proof checkerで検証していない。

## Roadmap

- [Done] 固定配線の学習失敗と表現不能をSAT診断で分離した。
- [Done] 出力だけの1・2接続修正と任意隠れnode選択を対照化した。
- [Done] State付きLogic PEの時間再利用、固定ランダムschedule、train-selected scheduleを16seedで比較した。
- [Done] 平均・不偏分散・bootstrap CI・効果量・Holm補正検定を保存した。
- [Next] 同じPE予算でゲート表とroute scoreを共同学習する。学習Routerには初回stepからload-balancing補助損失を適用し、均衡した固定ランダムrouteを対照にする。
- [Next] 学習後、自己置換、同一run内Expert交換、Router対応交換、別seed Expert移植の順で測る。
- [Later] 入力bit数・反復回数を増やした外挿、module形成・固定化・分解・再獲得、bit-packed CPUとFPGA合成見積もりへ進む。

English: The first logic-routing milestone establishes a small constructive example of trading spatial gate count for stateful time reuse. Training-set schedule selection beats balanced fixed-random schedules on both task families, but the schedule library contains strong task-specific module priors.

简体中文：第一个逻辑路由里程碑给出了以带状态的时间复用换取空间门数量的可执行小型例子。基于训练集的调度选择在两类任务上优于负载均衡的固定随机调度，但候选调度库包含很强的任务先验。

詳細：[E014レポート](STAR-Bit-E014-temporal-logic-pe.md)、[検証方針](STAR-Bit-validation.md)、[継続ログ](RESEARCH-LOG.md)。
