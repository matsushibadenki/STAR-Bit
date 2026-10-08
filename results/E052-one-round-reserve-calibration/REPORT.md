# E052：一段保持枠の校正・中断状態

事前登録240探索のうち233を完了し、探索時間900.1秒で事前900秒停止条件に到達した。成功・失敗を理由に停止したものではない。source/seed/task/controlsを固定したまま残り7探索を明示保存。
完了分の共通beam/幅、158成功式、12864保持式、source8/random384式、progress/hashを監査。
主比較・平均差・分散・CI・多重比較検定・校正gateは全事前条件完了まで保留し、部分結果から候補やseedを変更しない。追加計算は別の時間制限付きchunkとして事前登録し、今回900秒停止を延長しない。

- [Done] 保持枠の実装・preflight・完了分生データと未実行条件保存。
- [Next] 未実行の固定条件だけを別chunkで実施し、重複実行せず全240探索を統合監査する。
- [Later] 校正結果後に独立確認seedを事前固定。State/Router/Expert交換。

English: The preregistered time cap stopped the incomplete calibration suite. Fixed remaining conditions are saved; effect estimation and candidate decisions are deferred until completion.

简体中文：预注册时间上限终止未完成的校准。已保存固定的剩余条件；完成前不估计效果，也不更改候选。
