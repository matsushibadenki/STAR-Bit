# E053：E052一段保持枠の全条件統合

新規calibration seed1670–1675、固定全8task、総beam192、round3だけ最大16枠をtarget非依存の費用/hash順で新規cohort子候補に割り当てた。保持枠分だけ通常候補を減らす。独立確認ではない。

| family | condition | exact/24 | seed mean/variance | error mean/variance | cohort成功使用 | 保護個数/排除個数 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| numeric | baseline | 12/24 | 0.5000/0.0000 | 1.0000/0.0000 | 0 | 0/0 |
| numeric | learned_standard | 12/24 | 0.5000/0.0000 | 1.0000/0.0000 | 0 | 0/0 |
| numeric | learned_reserve | 12/24 | 0.5000/0.0000 | 1.0000/0.0000 | 0 | 192/192 |
| numeric | inert_reserve | 12/24 | 0.5000/0.0000 | 1.0000/0.0000 | 0 | 0/0 |
| numeric | random_reserve | 12/24 | 0.5000/0.0000 | 1.0000/0.0000 | 0 | 192/192 |
| route | baseline | 21/24 | 0.8750/0.0437 | 0.3333/0.3667 | 0 | 0/0 |
| route | learned_standard | 21/24 | 0.8750/0.0437 | 0.3333/0.3667 | 0 | 0/0 |
| route | learned_reserve | 21/24 | 0.8750/0.0437 | 0.3333/0.3667 | 0 | 192/192 |
| route | inert_reserve | 21/24 | 0.8750/0.0437 | 0.3333/0.3667 | 0 | 0/0 |
| route | random_reserve | 21/24 | 0.8750/0.0437 | 0.3333/0.3667 | 0 | 192/192 |

| learned reserve − control | mean | variance | 95% CI | dz | p | Holm p |
| --- | ---: | ---: | --- | ---: | ---: | ---: |
| learned_standard | +0.0000 | 0.00000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| inert_reserve | +0.0000 | 0.00000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| random_reserve | +0.0000 | 0.00000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:learned_standard | +0.0000 | 0.00000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:inert_reserve | +0.0000 | 0.00000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| numeric:random_reserve | +0.0000 | 0.00000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:learned_standard | +0.0000 | 0.00000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:inert_reserve | +0.0000 | 0.00000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |
| route:random_reserve | +0.0000 | 0.00000 | [0.0, 0.0] | None | 1.00000 | 1.00000 |

校正gate=False、learned reserve成功使用0、240探索915.7秒、preflight 45.0秒。165成功式、13824保持式、source8/random384式の全入力/費用、progress/hashと幅を監査。
成功使用はsignatureの構文的出現であり学習provenance保証ではない。記号式cost16と記述量・物理DAG・実行性能は別。

🟢 [Done] 通常候補の排除費用を含め、固定容量で一段保持枠を校正した。
🟠 [Next] 同じcohortの保護候補が残り一段で解へ合成できるかを機構診断し、費用優先rankが必要な情報を落としているかを調べる。保持枠数の事後探索やseed追加を先行しない。
🔴 [Later] 独立意味確認後にState/Router/Expert交換と物理費用。

English: A target-independent one-round reserve was calibrated at fixed total beam width192, including displaced ordinary candidates. Calibration is separate from independent confirmation.

简体中文：在总beam宽度192固定下校准目标无关的单轮保留槽，并计入被挤出的普通候选。校准与独立确认分开。

2026-10-09。E052の停止済み233条件は変更せず、E053の別chunkで残り7条件を完了した。全240条件でnumeric12/24、route21/24。主3差と副次6差は全て0、Holm p=1、learned reserve成功使用0、gate未達。learnedの保護384枠と通常候補の排除384件は実際に発生したが精度利益を確認できなかった。枝刈りで失われた候補を保持するだけでは、このpolicyで改善しない。

English: Completing the seven fixed conditions left all five conditions equal: numeric12/24 and routing21/24. All preregistered exact contrasts were zero (Holm p=1), with zero successful learned reserve use. Protecting384 learned candidate slots displaced384 ordinary entries but did not improve exact accuracy.

简体中文：完成7个固定剩余条件后，5种条件均为数值12/24、路由21/24。预注册exact差全部为0（Holm p=1），学习保留候选成功使用为0。384个学习保护槽挤出384个普通候选，但没有提高exact准确率。

⭕️ [Pending] 物理PE/GPU実デバイス性能はCPU記号探索では未検証。
