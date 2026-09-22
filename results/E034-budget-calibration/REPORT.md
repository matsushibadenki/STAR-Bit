# E034：移植なし条件だけで探索Round予算を校正

実行日：2026-09-22。E033で事前固定した6 taskを変えず、移植なし・beam128・tree cost16でround上限4/6/8を新規6 seedで比較した。合計108探索。Functionの成績で予算を選んでいない。

| family / task | 4 round | 6 round | 8 round | 選定予算 |
| --- | ---: | ---: | ---: | ---: |
| numeric / numeric_sum_ge4 | 6/6 (ceiling) | 6/6 (ceiling) | 6/6 (ceiling) | なし |
| numeric / numeric_sum_ge5 | 0/6 (floor) | 0/6 (floor) | 0/6 (floor) | なし |
| numeric / numeric_sum_ge7 | 0/6 (floor) | 1/6 (floor) | 1/6 (floor) | なし |
| route / route_cross_and | 3/6 (middle) | 6/6 (ceiling) | 6/6 (ceiling) | 4 |
| route / route_cross_or | 6/6 (ceiling) | 6/6 (ceiling) | 6/6 (ceiling) | なし |
| route / route_cross_xnor | 0/6 (floor) | 0/6 (floor) | 0/6 (floor) | なし |

## 事前選定基準

middleは移植なしexact 2–4/6。複数予算が該当するときは同じtaskの最小roundを採用した。両familyに候補があるという実行前feasibility基準は満たさなかった。

- 選定されたtask–budget: route_cross_and@4。
- 確認用の別seedでFunction条件を比較するまでは、構造自由度や一段barrierの一般化効果を主張しない。

family平均exact率の対応差（seed単位）：

| family / rounds | 平均差 | 不偏分散 | bootstrap 95% CI | Cohen dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| numeric:6-minus-4 | +0.0556 | 0.0185 | [0.0000, 0.1667] | 0.408 | 1.0000 | 1.0000 |
| numeric:8-minus-6 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |
| route:6-minus-4 | +0.1667 | 0.0333 | [0.0556, 0.2778] | 0.913 | 0.2500 | 1.0000 |
| route:8-minus-6 | +0.0000 | 0.0000 | [0.0000, 0.0000] | NA | 1.0000 | 1.0000 |

各task/予算のexact平均・不偏分散、best error平均・不偏分散、生成signature数平均、成功解tree cost平均（primitive / routing bits / depth）、時間平均秒：

- numeric_sum_ge4 / r4: exact 1.000 / 0.000; error 0.000 / 0.000; signatures 69890.3; cost 9.00 / 62.00 / 4.00; time 2.477秒。
- numeric_sum_ge4 / r6: exact 1.000 / 0.000; error 0.000 / 0.000; signatures 69890.3; cost 9.00 / 62.00 / 4.00; time 2.420秒。
- numeric_sum_ge4 / r8: exact 1.000 / 0.000; error 0.000 / 0.000; signatures 69890.3; cost 9.00 / 62.00 / 4.00; time 2.548秒。
- numeric_sum_ge5 / r4: exact 0.000 / 0.000; error 2.000 / 0.000; signatures 65864.0; cost NA; time 3.399秒。
- numeric_sum_ge5 / r6: exact 0.000 / 0.000; error 1.500 / 0.300; signatures 106983.0; cost NA; time 5.418秒。
- numeric_sum_ge5 / r8: exact 0.000 / 0.000; error 1.500 / 0.300; signatures 147161.0; cost NA; time 7.305秒。
- numeric_sum_ge7 / r4: exact 0.000 / 0.000; error 2.000 / 0.000; signatures 79403.0; cost NA; time 3.706秒。
- numeric_sum_ge7 / r6: exact 0.167 / 0.167; error 1.667 / 0.667; signatures 129823.0; cost 15.00 / 110.00 / 6.00; time 5.993秒。
- numeric_sum_ge7 / r8: exact 0.167 / 0.167; error 1.667 / 0.667; signatures 164909.3; cost 15.00 / 110.00 / 6.00; time 6.893秒。
- route_cross_and / r4: exact 0.500 / 0.300; error 1.000 / 1.200; signatures 75325.7; cost 11.00 / 78.00 / 4.00; time 2.996秒。
- route_cross_and / r6: exact 1.000 / 0.000; error 0.000 / 0.000; signatures 87779.7; cost 12.00 / 85.00 / 4.50; time 3.132秒。
- route_cross_and / r8: exact 1.000 / 0.000; error 0.000 / 0.000; signatures 87779.7; cost 12.00 / 85.00 / 4.50; time 3.023秒。
- route_cross_or / r4: exact 1.000 / 0.000; error 0.000 / 0.000; signatures 74635.0; cost 11.00 / 78.00 / 4.00; time 2.395秒。
- route_cross_or / r6: exact 1.000 / 0.000; error 0.000 / 0.000; signatures 74635.0; cost 11.00 / 78.00 / 4.00; time 2.451秒。
- route_cross_or / r8: exact 1.000 / 0.000; error 0.000 / 0.000; signatures 74635.0; cost 11.00 / 78.00 / 4.00; time 2.550秒。
- route_cross_xnor / r4: exact 0.000 / 0.000; error 7.000 / 6.000; signatures 83352.3; cost NA; time 3.703秒。
- route_cross_xnor / r6: exact 0.000 / 0.000; error 3.333 / 1.067; signatures 132896.5; cost NA; time 5.596秒。
- route_cross_xnor / r8: exact 0.000 / 0.000; error 3.333 / 1.067; signatures 168905.2; cost NA; time 6.836秒。

全53 exact式を64入力で再評価し、108 unique record、progress一致、budget間のprefix・exact/error単調性、strict JSON、source hashを監査した。計測時間はCPU探索時間であり、推論速度やハードウェア効率ではない。

## Roadmap

- [Done] E033の6 taskを固定したまま、移植なし条件だけでround予算4/6/8の難度曲線を測った。
- [Done] middleの選定をbaseline exactだけに限定し、Function条件の結果を見る前にtask–budget候補を凍結した。
- [Next] 数値grammarまたはbeam幅をbaselineのみのpilotで校正し、両familyに中難度候補を確保する。確認用seedは独立に確保する。
- [Later] State付き形成・分解、費用付きadmission、負荷分散付きRouterと固定random経路、同一run内→別seed Expert交換へ進む。

English: E034 varied only the baseline search-round budget across six frozen tasks. Mid-difficulty task–budget pairs, if any, were chosen solely from baseline exact counts. No learned-Function efficacy was evaluated here.

简体中文：E034只改变六个固定任务的基线搜索轮数预算。中等难度的任务–预算组合仅依据基线精确成功数选定；本实验未评价学习函数的效果。

English: Only route_cross_and at four rounds met the middle band (3/6); numeric had none, so the two-family confirmation gate failed.
简体中文：只有四轮的route_cross_and进入中等难度（3/6）；数值任务没有候选，因此双任务族确认门槛未通过。
[事前计划](PROTOCOL.md) / [生数据](run/results.json) / [冻结Task](run/frozen_tasks.json) / [选定Task–Budget](run/selected_task_budgets.json) / [审计摘要](run/audit_summary.json)
