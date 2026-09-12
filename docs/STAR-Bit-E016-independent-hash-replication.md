# E016：独立hashによるnumeric確認実験

実行日：2026-09-12。E015のnumeric対照で見つかったsplit/hash乱数流の結合を解消し、新しい16 seedで事前登録どおり追試した。Logic PEの弱い検証済みmodule prior、4 Experts、800更新、温度、最適化設定はE015から変更していない。

## 主要結果

| routing | hard test exact平均 | 不偏分散 | 95% CI | bit平均 | 完全一致seed |
| --- | ---: | ---: | --- | ---: | ---: |
| fixed_hash | 0.875000 | 0.012630 | [0.820312, 0.927734] | 0.940918 | 4/16 |
| learned_balanced | 0.978516 | 0.003219 | [0.947266, 1.000000] | 0.989746 | 13/16 |

| learned−fixed | 差の不偏分散 | 95% CI | Cohen dz | exact permutation p | seed符号 + / 0 / − |
| ---: | ---: | --- | ---: | ---: | ---: |
| +0.103516 | 0.013896 | [0.050781, 0.160156] | 0.878 | 0.00195312 | 10 / 5 / 1 |

16 seed内のhard test exact差に二側exact sign-flip permutation testを適用した。事前登録した追試は1比較なので多重性補正は不要である。p≤0.05かつ95% CIが正方向で0を除く確認基準を満たした。

## 独立性と負荷分散の監査

splitはseed 800–815、固定hashはそれぞれseed+40000から生成した。固定hashは全64入力を各Expert 16件へ割り当てる一方、train内の割当は4–12件、完全な8/8/8/8は0/16 seedだった。E015で起きた全seed完全均衡は再現せず、乱数流の分離を確認した。

| routing | 最終soft balance loss平均 | soft train利用CV平均 | hard full利用CV平均 |
| --- | ---: | ---: | ---: |
| fixed_hash | 0.047363 | 0.202469 | 0.000000 |
| learned_balanced | 0.000001 | 0.000565 | 0.169792 |

learned Routerにはupdate 0から係数0.1のimportance balance補助損失を適用した。固定hashのbalance値は学習項として機能しない定数で、train subsetの自然な偏りを示す診断値である。固定hashはfull domainで完全均衡する。soft負荷の均衡とhard argmax後の利用均衡は区別して報告した。

## E015との再現性

E015 numericのlearned−fixed差は+0.056641（Holm p=0.015625）だった。独立乱数流・新seedのE016でも差は+0.103516となり、方向と事前確認基準を再現した。二実験の統合検定は事前登録していないため行わない。

## 解釈と限界

精密数値タスクでも、検証済みmodule priorの下では入力依存の学習Routerがラベル非依存の固定均衡hashより高い未見入力精度を示した。固定群にも高いseedがあり、改善幅はE015のselectionより小さい。これはcarry計算自体をroutingが新しく発見した証拠ではなく、既知Logic Expert群を入力に応じて割り当てる効果である。

Gate表は完全ランダムから意味を発見しておらず、E014由来の弱い初期priorを使う。評価は固定6入力Boolean全領域の32/32分割であり、bit幅・系列長の外挿、Transformer、実ハードウェア面積や速度を検証していない。

32 training trajectories、CPU単一thread、PyTorch 2.10.0、経過45.4秒。checkpoint、source hash、split、独立hash再生成、full-domain均衡を監査した。

English: With independent split and fixed-hash random streams, learned balanced routing again improved numeric hard test exact accuracy under the verified Logic-PE prior. The preregistered replication criterion was met.

简体中文：在数据划分与固定哈希使用独立随机流后，负载均衡的学习路由在已验证Logic PE先验下再次提高了数值任务的硬化测试精确率，并满足预注册复验标准。

[事前計画](../results/E016-independent-hash-replication/PROTOCOL.md) / [生データ](../results/E016-independent-hash-replication/run/results.json)
