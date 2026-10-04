# E048：固定CohortのAdmission事前監査

2026-10-04。凍結8 task、6 calibration seed、初回128・後続192で48組を2回照合した。sourceはE022の既存learned Functionsのうちprimitive>=4の全8件。学習条件の結果を使わずsignature衝突だけでadmissionを決定した。

事前feasibility gate：True。全beam・taskとの衝突なし採用は8/8。seed別利用可能数の平均8.0000、不偏分散0.0000、bootstrap 95% CI [8.0, 8.0]。8件からの利用可能数損失は平均0.0000、分散0.0000、dz=None、exact sign-flip p=1.00000。検定は1つで多重補正なし。

source8式とrandom384式の64入力signature・primitive/routing/depth費用を再評価した。48 unique record、progress、全round2幅192、source hashを監査。探索時間40.9秒。今回の採用は機械的admission feasibilityであり、学習された意味の利益や精度向上は未評価。

改善案：cohortをsourceから固定した上で、全calibration beamとの衝突除外を先に完了し、次の意味比較で候補数や費用の不一致を避ける。確認seedは今回と分離する。

- [Done] source-frozen cohortと同費用random対照を監査して保存した。
- [Next] 採用cohortを固定し、learned／composition不能inert／同費用randomとbaselineを新規seedで比較する。
- [Later] 意味固有効果成立後、State形成・分解、負荷分散Router、固定random経路、Expert交換へ進む。

English: E048 audited a source-frozen cohort before semantic comparison; admitted 8/8 Functions and verified 384 collision-free, cost-matched random controls. This establishes admission feasibility only.

简体中文：E048在语义比较之前审计冻结source cohort，采用8/8个函数，并验证384个无冲突同成本随机对照；这仅验证加入机制的可行性。
