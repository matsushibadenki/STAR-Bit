# E049：固定Cohortの学習意味比較

2026-10-05。凍結8 task・6新規seed、初回128/後続192でround2後にsource8件または同費用random8件を追加。inertはsource signatureを保持し全compositionを禁止。baselineは追加なし。

| family | 条件 | exact/24 | seed平均 / 不偏分散 | best error平均 / 不偏分散 | Function使用成功 | 秒平均 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| numeric | baseline | 12/24 | 0.5000 / 0.0000 | 1.000 / 0.0000 | 0 | 2.893 |
| numeric | learned | 12/24 | 0.5000 / 0.0000 | 1.000 / 0.0000 | 0 | 2.935 |
| numeric | inert | 12/24 | 0.5000 / 0.0000 | 1.000 / 0.0000 | 0 | 2.615 |
| numeric | random | 12/24 | 0.5000 / 0.0000 | 1.000 / 0.0000 | 0 | 3.109 |
| route | baseline | 20/24 | 0.8333 / 0.0417 | 0.583 / 0.9417 | 0 | 2.146 |
| route | learned | 20/24 | 0.8333 / 0.0417 | 0.583 / 0.9417 | 0 | 2.378 |
| route | inert | 20/24 | 0.8333 / 0.0417 | 0.583 / 0.9417 | 0 | 2.263 |
| route | random | 20/24 | 0.8333 / 0.0417 | 0.583 / 0.9417 | 0 | 2.309 |

| learned−対照 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| inert | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| random | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:exact:inert | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:exact:random | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:best_error:inert | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:best_error:random | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:exact:inert | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:exact:random | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:best_error:inert | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:best_error:random | +0.0000 | 0.0000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |

事前意味gate：False。learned使用成功0件。探索時間495.6秒、preflight 50.9秒。
全128 exact式とsource8/random384式を64入力で再評価し、費用、192 record、共通round1/2 beam、round3幅、progress、source hashを監査。best_error差は負がlearned有利。

- [Done] source-frozen cohortをinert・同費用randomと同時刻同容量で比較した。
- [Next] 固定cohortのprimitive予算内composition到達性と投入後残りround数を、accuracyに依存しない機構診断として事前登録する。
- [Later] 独立意味確認成立後、State形成・分解、初回負荷分散Router、固定random経路、Expert交換へ進む。

English: E049 found zero learned-versus-inert/random exact differences (Holm p=1) and no successful cohort use. Numeric solved12/24 and routing20/24 in every condition.

简体中文：E049学习函数相对惰性/随机对照的exact差均为0（Holm p=1），成功表达式未使用cohort。各条件数值12/24、路由20/24。
