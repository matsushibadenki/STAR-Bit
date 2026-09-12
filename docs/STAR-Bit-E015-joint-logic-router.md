# E015：Logic Expert・schedule・Router共同最適化

実行日：2026-09-12。E014で検証したLogic PE gate表を弱い事前値として、4 ExpertのLUT表・schedule分布・入力Routerを共同最適化した。16 main seed、各32 train/32 test、800更新。

## hard test主要結果

| task | routing | exact平均 | 不偏分散 | 95% CI | bit平均 | 完全一致seed |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| numeric | fixed_hash | 0.935547 | 0.006051 | [0.896484, 0.970703] | 0.971680 | 8/16 |
| numeric | learned_balanced | 0.992188 | 0.000326 | [0.982422, 1.000000] | 0.998047 | 13/16 |
| selection | fixed_hash | 0.640625 | 0.053776 | [0.529297, 0.748047] | 0.852539 | 2/16 |
| selection | learned_balanced | 0.976562 | 0.001497 | [0.957031, 0.994141] | 0.991699 | 11/16 |

| task | learned−fixed | 差の分散 | 95% CI | Cohen dz | exact permutation p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric | +0.056641 | 0.005758 | [0.021484, 0.093750] | 0.746 | 0.01562500 | 0.01562500 |
| selection | +0.335938 | 0.045508 | [0.236328, 0.437500] | 1.575 | 0.00012207 | 0.00024414 |

16seed内のhard test exact差に二側exact sign-flip permutation testを適用し、2タスクをHolm補正した。両タスクで補正後有意だが、numeric固定hashには後述のsplit結合がある。

## 負荷分散

| task | routing | 最終soft balance loss平均 | soft train利用CV | hard full利用CV |
| --- | --- | ---: | ---: | ---: |
| numeric | fixed_hash | 0.000000 | 0.000000 | 0.000000 |
| numeric | learned_balanced | 0.000001 | 0.000532 | 0.222329 |
| selection | fixed_hash | 0.047363 | 0.197189 | 0.000000 |
| selection | learned_balanced | 0.002533 | 0.029356 | 0.142964 |

learned Routerには最初の更新から係数0.1のimportance balance損失を適用した。soft負荷はほぼ均衡したが、argmax後のhard full利用は完全均衡とは限らない。固定hashは全64入力で各Expert 16件を構造的に保証する。

## Expert介入：hard test exactの変化

交換後−無交換。負は悪化。

| task | routing | 同一run 0/1交換 | 次seed Expert 0 | zero Expert 0 | 再初期化 Expert 0 |
| --- | --- | ---: | ---: | ---: | ---: |
| numeric | fixed_hash | +0.011719 | +0.003906 | -0.238281 | -0.179688 |
| numeric | learned_balanced | -0.021484 | -0.021484 | -0.269531 | -0.205078 |
| selection | fixed_hash | +0.023438 | +0.021484 | -0.132812 | -0.056641 |
| selection | learned_balanced | -0.261719 | -0.085938 | -0.234375 | -0.134766 |

同一runではExpertだけを0/1交換し、Routerは固定した。learned selectionは平均−0.2617と大きく悪化し、ExpertとRouterの対応依存がある。次seed Expert 0移植は平均−0.0859。番号を機能整列していないため、移植失敗を知識非局在の証明とはしない。

自己置換とExpert 0/1＋Router対応の同時交換はsoft/hard全2048評価で最大出力差0。介入実装の置換対称性を確認した。cross-seed donorは事前固定した次seedで、再学習・test選択なし。循環donor共有のため交換差に有意差検定は行わず、全平均・分散・CIを生JSONへ保存した。

## 監査で判明した制約

numericではsplit permutationと固定hash lookupが同じseedから同じ乱数手順で生成され、結果として全seedのtrain割当も8/8/8/8になった。ラベルは使っていないが、対照routingとsplitが意図せず結合している。固定群を有利にし得るためnumeric差は保守的に見えるものの、独立対照としては不十分である。別seed・独立hash streamによるE016確認を行う。selectionはsplit seed+20000、hash seed+5000で分離されている。

## 判定と限界

module prior下では、learned routingは均衡固定hashよりnumeric +0.0566、selection +0.3359 hard test exact高かった。特に経路選択で構造自由度が効くという軸を支持する。一方、numericは両群が高精度で天井効果が強い。

Gate表は完全ランダムから意味を発見しておらず、pilot結果に基づく既知module priorを使う。E014候補libraryもタスク固有で、汎用的な構造発見、長さ外挿、LLM能力の証拠ではない。

64 training trajectories、384 intervention records、CPU単一thread、PyTorch 2.10.0、経過751.5秒。checkpoint・source hash、split、full-domain hash balance、自己交換と対称交換を再検査した。

English: Under a verified Logic-PE prior, jointly optimized balanced routing beat a fixed balanced hash, especially on route selection. Numeric fixed-hash generation was unintentionally coupled to the split RNG and requires independent replication.

简体中文：在已验证的Logic PE先验下，联合优化的负载均衡路由优于固定均衡哈希，尤其是在路径选择任务上。数值任务的固定哈希与数据划分随机流意外耦合，需要独立复验。

[事前計画](../results/E015-joint-logic-router/PROTOCOL.md) / [生データ](../results/E015-joint-logic-router/run/results.json)
