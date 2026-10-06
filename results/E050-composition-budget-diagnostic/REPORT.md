# E050：投入直後の合成予算診断

E049と同じseed1660–1665・全8task・固定source/random cohortを再利用した機構診断。独立確認ではない。round2 beamを費用込みで復元し、cohort×beamの16 LUTを枝刈りせず列挙した。cost16の記号式予算を扱い、物理DAGゲート数を扱わない。

| family | cohort | feasible pair割合 平均/分散 | exact child有/24 | 有用child有/24 | best child error 平均/分散 | 予算外exact有/24 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| numeric | learned | 1.0000/0.000000 | 0/24 | 0/24 | 8.7500/0.150000 | 0/24 |
| numeric | random | 1.0000/0.000000 | 0/24 | 3/24 | 6.1250/0.718750 | 0/24 |
| route | learned | 1.0000/0.000000 | 0/24 | 12/24 | 16.0000/0.000000 | 0/24 |
| route | random | 1.0000/0.000000 | 1/24 | 24/24 | 11.3333/2.991667 | 0/24 |

learned−random best-child error（負がlearned有利）。seed単位bootstrap CIは条件付き記述量で、独立検証の証拠ではない。

- numeric: 平均2.6250、不偏分散0.418750、95% CI [2.2083333333333335, 3.125]、dz=4.056503898752843、p=0.03125、Holm p=0.06250
- route: 平均4.6667、不偏分散2.991667、95% CI [3.6666666666666665, 6.125]、dz=2.6980511553972075、p=0.03125、Holm p=0.06250

96記録・48beam再現・全費用再計算・source hash・progressを照合。実行21.2秒。2段合成やround3選択での保持は未評価。sourceの非衝突admissionと、その後の利用可能性を区別する。

全pairがcost16内であり、この投入時点の一段合成には予算制約が障害ではなかった。learnedのexact childは0/48、randomは1/48。有用childはlearned numeric0/24・route12/24。learnedのbest child errorはrandomよりnumeric+2.625、route+4.6667だが両Holm p=0.0625。枝刈り前の機会は既存候補との重複を含み、cohortに固有の新規解を意味しない。

- [Done] 全固定cohortの一段合成機会を枝刈り前に評価した。
- [Next] 同一cohortの有用childがround3選択で失われるかを記録し、残る一段での利用機会を診断する。
- [Later] 変更案を校正後に新規seedで意味効果確認。State/Router/Expert交換と物理費用評価。

English: This retrospective one-step diagnostic separates legal composition opportunities from admission and pruning. It is not independent confirmation or two-step reachability proof.

简体中文：本回顾性单步诊断区分合法组合机会、加入和剪枝；不属于独立验证，也未证明两步可达性。
English: All cohort–beam pairs fit cost16. Learned exact children:0/48; random:1/48. Learned best-child error was worse by2.625 (numeric) and4.6667 (routing), both Holm p=0.0625. Pruning and two-step use remain unresolved.

简体中文：全部cohort–beam组合符合cost16。学习函数exact子项0/48，随机1/48。学习函数最佳子项误差较高：数值+2.625、路由+4.6667，两者Holm p=0.0625。剪枝及两步复用仍未解决。
