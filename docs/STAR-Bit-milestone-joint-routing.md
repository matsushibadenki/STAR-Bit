# STAR-Bit Logic Routing Milestone 2

更新日：2026-09-12。

## 到達点

小型Boolean課題と検証済みLogic PE事前知識の範囲で、**学習された入力依存routingの効果を、ラベル非依存の固定ランダムroutingから分離した**。E015と独立追試E016を合わせて96学習runを実施し、全条件を16 seedで評価した。

- 精密数値タスクの独立追試では、learned routingがfixed hashをhard test exactで+0.1035上回った。
- 経路選択タスクでは、learned routingがfixed hashを+0.3359上回った。
- 学習Routerには最初の更新からload-balancing補助損失を入れた。
- 固定hashは全64入力を4 Expertsへ16件ずつ割り当て、学習せず、ラベルも参照しない。
- Expert介入は自己置換、同一run内交換、対応Router交換、別seed移植、破壊対照の順で実施した。

この結果は、既知の低bit論理モジュールをどの入力へ割り当てるかという自由度が、未見入力の正解率を改善できることを示す。Gate意味のゼロからの発見、長いbit幅への外挿、言語モデルでの有効性はまだ実証していない。

## 主要結果

| タスク | 実験 | fixed hard test exact 平均（不偏分散） | learned 平均（不偏分散） | paired差、95% CI | 検定 |
| --- | --- | ---: | ---: | --- | --- |
| 精密数値 | E016独立追試 | 0.8750（0.01263） | 0.9785（0.00322） | +0.1035 [0.0508, 0.1602] | dz=0.878、exact p=0.001953 |
| 経路選択 | E015 | 0.6406（0.05378） | 0.9766（0.00150） | +0.3359 [0.2363, 0.4375] | dz=1.575、Holm p=0.000244 |

各行は16 seed、各seed 32 train／32 testである。E016は1つの事前登録比較なので補正なし、E015は2タスクの検定をHolm補正した。E016のseed符号は改善10、同値5、悪化1で、事前登録したp≤0.05かつ95% CIが正方向で0を除く確認基準を満たした。

E015 numericでも差は+0.0566、Holm p=0.015625だったが、splitとfixed hashが同一乱数流を共有していた。この値を改変せず監査記録に残し、乱数流を分離した新seed 800–815のE016をnumericの主要値に採用した。E016のfixed hash train割当はExpertあたり4–12件で、E015のような全seed 8/8/8/8にはならなかった。full domainでは計画どおり常に16/16/16/16である。

## 負荷分散とhard化

learned Routerの損失は、task lossに係数0.1のimportance balance損失をupdate 0から加えた。E016 numericの最終soft balance loss平均は0.000001、soft train利用CVは0.000565だった。E015 selectionではそれぞれ0.002533、0.029356だった。

soft確率の均衡は、離散化したhard argmaxの均衡を保証しない。hard full利用CVはnumeric 0.1698、selection 0.1430だった。固定hashは構造的にfull利用CV=0である。この差がある状態でもlearned側が高精度だったため、結果を単なる均衡化の効果とは解釈しない。現段階で分離できたのは、**同じExpert予算での学習routingと固定均衡hashの差**である。

## Expert交換が示す対応依存

E015では全64runへ6介入、計384記録を保存した。自己置換とExpert＋Routerラベルの対応交換はsoft/hardとも最大出力差0で、介入実装の対称性を確認した。

| タスク・routing | 同一run Expert 0/1交換 | 次seed Expert 0移植 | zero Expert 0 | 再初期化 Expert 0 |
| --- | ---: | ---: | ---: | ---: |
| numeric fixed | +0.0117 | +0.0039 | −0.2383 | −0.1797 |
| numeric learned | −0.0215 | −0.0215 | −0.2695 | −0.2051 |
| selection fixed | +0.0234 | +0.0215 | −0.1328 | −0.0566 |
| selection learned | **−0.2617** | **−0.0859** | −0.2344 | −0.1348 |

値はhard test exactの介入後−基準平均である。同一runではExpertsだけを先に交換し、Routerは保持した。selection learnedの大幅低下は、Routerの入力分割とExpert機能の対応が学習されたことを示す。続いて行った別seed移植でも低下したが、Expert番号を機能で整列していないため、差の一部にはpermutation ambiguityが含まれる。交換系列は探索的介入として扱い、有意差検定は主結果へ含めていない。

## どのタスクで構造的自由度が効くか

| 分析軸 | 精密数値 | 経路選択 |
| --- | --- | --- |
| 固定ランダム二層配線 | 一部の低位bitは作れるが、carryを含む上位bitで表現制約 | E013の対象67caseは任意隠れnode選択でも0件回復 |
| State付き時間再利用 | full-adder PEを3 cycle再利用して完全一致 | mux-stage PEを2 cycle再利用して完全一致 |
| 学習routing対fixed hash | E016で+0.1035、両群とも高精度で天井効果あり | E015で+0.3359、固定群の分散と誤差が大きい |
| 同一run Expert交換 | learned平均−0.0215 | learned平均−0.2617 |

経路選択タスクでは、条件に応じて処理系列を切り替える必要があり、routingとExpertの対応が性能を強く左右した。精密数値タスクではcarryという時間Stateの構造が中心で、module priorが合えば固定hashでも平均0.8750まで到達した。したがって、この規模では**経路選択は入力依存routingの自由度に強く反応し、精密数値は正しい再帰moduleとStateの自由度に強く反応する**。これはタスク間の記述的比較であり、差の差を事前登録した直接検定ではない。

## ゲート爆発への回答の現在地

Milestone 1では、full-adderを3 cycle再利用して空間展開15 primitiveに対し物理primitiveを5へ、mux-stageを2 cycle再利用して24から12へ減らした。Milestone 2では、その再利用PEを4 Expertsへ拡張し、固定hashではなく入力依存Routerで割り当てる利点を確認した。

物理primitiveの削減はactive gate評価数の削減ではない。Router、配線mux、State register、configuration memory、clock、通信の面積・電力・遅延をまだ計上していない。現時点の成果はアルゴリズム上の構成可能性と汎化差であり、ハードウェア効率の実証ではない。

## まだ証明していないこと

- 完全ランダムなGate表から、意味のあるLogic Expertを安定して発見できること。
- タスク固有候補を使わずに、階層module、共有DAG、LUT、条件実行を自律形成できること。
- 3 bit加算／4 lane選択を超えたbit幅、系列長、構成回数への外挿。
- 1-bit／ternary weightのTransformerで、同じrouting効果が品質・計算量・メモリの総費用を改善すること。
- 実FPGA／ASICで、RouterとStateを含む面積・遅延・電力が空間展開より小さいこと。
- 別seed Expertを機能対応で整列した後にも移植低下が残ること。

## Roadmap

- [Done] 複数seedで平均、不偏分散、bootstrap CI、効果量、exact検定を報告した。
- [Done] load-balancing補助損失を学習開始時から組み込み、soft利用とhard利用を分けて監査した。
- [Done] 全入力で均衡する固定ランダムhash対照を追加し、独立乱数流でnumeric結果を追試した。
- [Done] Expert介入を同一run内交換から別seed移植の順で実施し、対称性対照と破壊対照を保存した。
- [Done] 精密数値と経路選択を明示的に比較し、routing依存とState/module依存の違いを整理した。
- [Next] Gate発見をRouter学習から段階分離する。既知module prior、random初期値、curriculum、module freezingを同じseedと予算で比較する。
- [Next] 4/6/8 bitへの長さ外挿と、Expert数・cycle数・State量を変えた容量曲線を事前登録する。
- [Next] 別seed Expertsを真理値表または機能signatureで整列してから交換し、permutation ambiguityを除く。
- [Later] bit-packed CPU benchmarkとFPGA論理合成で、Router・mux・register込みの面積、速度、電力を測る。
- [Later] 小型ternary Transformer blockへ移し、同一総パラメータ・同一active演算・同一メモリ条件で検証する。

English: Milestone 2 isolates learned input-dependent routing from a balanced label-independent random hash under a verified Logic-PE prior. Across 16 seeds, the independently replicated gain was +0.1035 for numeric addition and +0.3359 for route selection. Route selection showed much stronger Router–Expert assignment dependence, while numeric addition relied more on the correct recurrent stateful module. General module discovery, length extrapolation, Transformer quality, and hardware efficiency remain open.

简体中文：第二个里程碑在已验证Logic PE先验下，将学习到的输入依赖路由与标签无关的均衡随机哈希进行了分离。16个种子中，独立复验的数值加法提升为+0.1035，路径选择提升为+0.3359。路径选择更依赖Router与Expert的对应关系，而数值加法更依赖正确的递归状态模块。通用模块发现、长度外推、Transformer效果与硬件效率仍待验证。

詳細：[E015共同学習](STAR-Bit-E015-joint-logic-router.md)、[E016独立追試](STAR-Bit-E016-independent-hash-replication.md)、[Milestone 1](STAR-Bit-milestone-logic-routing.md)、[継続ログ](RESEARCH-LOG.md)。
