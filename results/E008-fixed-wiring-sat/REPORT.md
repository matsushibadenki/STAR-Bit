# E008：固定配線で正解回路を構成できるか

実行日：2026-09-11。

E007の64配線を診断した。ソルバー判定はSAT 1件、UNSAT 47件、UNKNOWN 16件。既存の学習済み完全一致モデルの証人も含め、構成可能性を確認した配線は1件。

**UNSATの配線では、同じhardゲート集合・配線のまま全入力に正答することはできないというsolver判定になった。UNKNOWNは表現不能ではない。** UNSAT証明はZ3のartifactを保存したが、別のproof checkerでの検証はしていない。

English: Fixed-wiring feasibility was checked on the complete truth table. SAT witnesses are independently evaluated; UNSAT is a solver result with an archived proof artifact, not an independently checked proof. Timeouts remain unresolved.

简体中文：对固定连接进行完整真值表可满足性检验。SAT见证经过独立求值；UNSAT为求解器判定并保存证明，但未使用独立证明检查器。超时保持未判定。

## 何を検査したか

- E007 seed500–515、numeric/selection、gate2/lut4のfull64・1600step checkpoint。新しい訓練は行っていない。
- 全68ゲートの接続をcheckpointから固定し、各2入力ゲートを4bit、出力LUT4を16bitの自由な真理値表として表現する。同じ表変数を全入力で共有する。これは対応するhardモデルの関数集合と一致する。
- 全64入力×4出力を正解と一致させる。汎化ではなく、全真理値表の構成可能性の診断。ソルバーは全正解を参照するため、その成功を学習能力とは呼ばない。
- 各case10秒、solver乱数seed0、単一thread。proof生成を有効化。同じ制約と予算を全caseに適用。
- SATは得た真理値表をNumPy整数インデックスの独立評価器へ渡し、全256出力bit一致を要求する。UNSATとUNKNOWN（理由付き）を分ける。

Z3のSAT/UNSAT/UNKNOWNの意味とtimeout/proof設定は[公式コマンド説明](https://microsoft.github.io/z3guide/docs/logic/basiccommands/)と[公式パラメータ資料](https://microsoft.github.io/z3guide/programming/Parameters/)を参照した。

## 判定結果

| task | architecture | SAT | UNSAT | UNKNOWN | SATだが学習精度<100% | E007 hard平均 | 分散 | E007 hard 95% CI |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| numeric | gate2 | 0 | 16 | 0 | 0 | 0.437500 | 0.012370 | [0.387695, 0.492188] |
| numeric | lut4 | 1 | 7 | 8 | 0 | 0.671875 | 0.041895 | [0.575195, 0.766602] |
| selection | gate2 | 0 | 16 | 0 | 0 | 0.264648 | 0.001806 | [0.245117, 0.285156] |
| selection | lut4 | 0 | 8 | 8 | 0 | 0.454102 | 0.004182 | [0.423828, 0.484375] |

各行16seed。学習精度のCIはE007測定のseed bootstrapによる記述統計。ソルバー成功率と学習精度の有意差検定はしない。SATである配線だけ選んだ精度比較を全配線へ一般化しない。

ソルバーがSAT証人を得て、元の学習に誤差があったケースは0件。この件数だけが今回、同配線での学習失敗を構成的に確認できた範囲である。UNKNOWNには最適化失敗とも表現不能とも割り当てない。

## 既存の完全一致checkpoint

E007のnumeric・seed515・lut4について、学習済みhard表を改めて書き出して全入力で一致を確認した。今回のsolverがUNKNOWNでもこの配線は構成可能と分かっている。

| 既存証人 | 今回のsolver判定 | 独立全入力一致 |
| --- | --- | --- |
| numeric-515-lut4 | sat | 100% |

solverのUNKNOWN件数と、既存証人を加味した構成可能性未判定の件数は同じとは限らない。

## 判定の意味と限界

- UNSATは全入力100%の不可能性を示すsolver判定。最大可能Accuracyが何%かは測っていない。低い学習精度が全て配線のせいだと断定することもできない。
- SAT証人はゲート表だけを変えた同配線の構成。制約ソルバーに全正解を与えているため、未知の入力を推論できることや抽象概念の獲得ではない。
- 4入力LUTのUNKNOWNは10秒とproof有効設定での結果。別の符号化や長い時間で解けるかは未検証。solver速度の優劣比較でもない。
- RouterやExpertは扱っていない。MoEでの負荷分散、固定ランダム経路、Expert交換等の対照は後続統合実験で維持する。

## 保存処理の障害と修正

最初の試行は6case目のUNSAT証明をsexpr文字列へ展開する処理で停止した。プロセスを終了し、旧コードsolve_attempt1.py、旧設計PROTOCOL-attempt1.md、5件の途中結果run/progress.json、未完artifactを保存した。

最終試行では証明を共有ASTのDAGとして保存し、走査3秒／100,000node上限を設けた。対象seed・solver seed・判定timeoutは変更せず、最終結果はrun_boundedへ別保存した。よい結果を選ぶための再試行ではない。

UNSAT 47件のうち、証明DAGの保存上限に達したものは15件。これらのproof artifactは不完全であり、完全な証明ファイルを納品したとは扱わない。DAG参照の整合性検査も証明の意味的な独立検証ではない。

## 検証と再現

- 既知SATの2入力XOR、入力不足で既知UNSATのXOR、非対称4入力LUT表の固定SAT、参照できない入力を要求する4入力LUTのUNSATで符号化を検査。
- 全SAT証人を再評価し、SMT-LIB問題・証人JSON・UNSAT proof DAG・UNKNOWN理由・元checkpoint hashを保存。
- Z3 5.1.0、NumPy 1.25.2、最終試行経過 305.637秒。proof有効時の10秒制限は多少超過し得るため、実測solve_secondsも記録。

```bash
python3 -m pip install --target /private/tmp/starbit-z3 z3-solver==5.1.0.0
python3 results/E008-fixed-wiring-sat/solve.py
PYTHONPATH=/private/tmp/starbit-z3 python3 results/E008-fixed-wiring-sat/verify.py
python3 results/E008-fixed-wiring-sat/audit.py
python3 results/E008-fixed-wiring-sat/report.py
```

NumPyも必要。solve.pyは既存run_boundedがあると停止する。新しい判定実験は別実験IDで実施し、過去結果を上書きしない。

[最終生結果](../results/E008-fixed-wiring-sat/run_bounded/results.json)、[設計と修正記録](../results/E008-fixed-wiring-sat/PROTOCOL.md)。

## 次の改善案

UNSATのcaseは、ゲート表の学習率調整より先に配線や出力容量を変える必要がある。まず出力bitごとの制約診断で障害箇所を絞り、変更する接続本数を制限した対照を設ける案がある。

UNKNOWNのcaseは別枠で、共有された中間式を保つ符号化や既知証人による検証を検討する。証人が得られた配線では初期化・最適化を比較できるが、正解証人を初期値に使う場合はoracle対照とし、通常学習に混ぜない。
