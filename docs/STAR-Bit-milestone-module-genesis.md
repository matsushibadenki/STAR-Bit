# STAR-Bit Milestone 3：Module GenesisとTransferの境界

実行期間：2026-09-12〜2026-09-22。E017〜E037は、primitive論理演算から中間Functionを形成し、Libraryへ昇格・選別・移植できるかを段階的に検証した。

## 到達した結論

| 段階 | 実験 | 結果 | 現在の判定 |
| --- | --- | --- | --- |
| 入出力からhard circuit形成 | E017–E018 | parity/muxは安定、comparator/carryは不安定 | 探索がボトルネック |
| Function-spaceと同値統合 | E019 | 同値mergeだけでは不十分。人手affine保持でparity回復 | 良い中間Function保持が効く |
| 中間Function価値の自動学習 | E020 | target-greedy比+1.25 exact target、comparator初到達 | 肯定的pilot、Library肥大 |
| 費用正規化と退役 | E021 | 台帳−46.9%、時間−5.5%、carry初到達 | 性能維持、最終beam削減基準は未達 |
| 同一task・別seed移植 | E022 | learned−random +0.5625、95% CI [0.1875, 0.9375] | 固定Function再利用を支持 |
| 別taskへの移植 | E023 | learned 27/64、primary random 27/64 | Concept再利用を支持せず |
| probe utilityと退役 | E024–E025 | 固定Libraryはno-transferを下回り、局所use判定は全候補を通過 | 無選別admissionが探索を阻害 |
| 反実仮想admission | E026–E027 | 凍結1 Functionで22/64、legacy 4/64、random 17/64 | 阻害緩和と限定的task-crossing transferを支持 |
| 直接利用と入力意味の分離 | E028 | 採用4/16、直接composition禁止2/16、入力+1置換4/16 | 直接利用の事前基準は未達 |
| beam探索軌跡の追跡 | E029 | 入力+1だけが成功した3解はFunctionを最終式に含まず、初回beam固有signatureを祖先に持つ | 予備的trajectory証人、provenance未同定 |
| provenanceと伝播barrier | E030 | 通常／one-hop barrierともdual-mux 3/16、対応差0 | 観測lineageは必要機構でない |
| task-family可搬性 | E031 | routeは採用2/24、random 3/24。numeric sumは採用0/8、barrier 6/8 | 広い可搬性を支持せず、深い伝播の阻害仮説 |
| 伝播barrierの独立確認 | E032 | numeric sumは通常2/16、barrier12/16、inert8/16。route XNORは通常4/16、barrier2/16 | 無制限伝播の阻害は再現。一段固有の利益は未証明 |
| 生成Grammarの難度pilot | E033 | baselineの数値8/8・0/8・0/8、route 8/8・8/8・1/8 | 中難度0/6、family交互作用のpilot基準未達 |
| 固定Grammarの探索予算校正 | E034 | 6 task×3 round予算×6 seedのbaseline 108探索 | 中難度はroute `cross_and`の4 roundで3/6のみ。数値familyに候補なし |
| 重み付き数値Grammarの難度校正 | E035 | 6 task×6 seedのbaseline 36探索 | 全task exact 0/6。数値familyの中難度候補なし |
| 数値Beam幅の難度校正 | E036 | 1 task×4 beam幅×6 seedのbaseline 24探索 | beam256で2/6。routeとnumericの中難度pilot候補が揃った |
| 凍結候補の独立Function比較 | E037 | 2 task×5条件×新規6 seedの60探索 | family交互作用の事前基準未達。数値barrier・inert・移植なしは各2/6 |

現在支持される限定的な主張は次である。

$$
\boxed{\text{因果的probeで選別した部分Functionは、特定の別task・seedで探索を助けうる}}
$$

現在も支持されない主張は次である。

$$
\boxed{\text{広いtask族で役立つ汎用Conceptが自律形成された}}
$$

E022ではsourceの最終出力signatureを除外し、評価seedも分離した。16 learned Functionsは同じ式木形状・primitive・routing・depthのランダムFunctionよりexact targetを平均+0.5625増やし、comparatorを1/16から5/16、carryを1/16から4/16へ増やした。これは単なるArchive内保持から、固定Library移植へ進んだ肯定的な節目である。

E023ではさらに評価taskと同じsource taskをLibraryから除外した。その結果、learned cross-taskとerror-matched randomはともに27/64となり、cost-matched randomの37/64も下回った。learned条件の27解中、移植Functionを最終回路で使ったのは3解だけだった。E022の改善は汎用Conceptよりtask固有の有用な部分回路に強く依存していた。

E024–E026では、Library全体を入れること自体が探索を壊す問題を分離した。一段utilityや局所usageでは有害候補を選別できなかったが、with/without probe探索の反実仮想差は45候補から1 Functionだけを採用した。E027はそのFunctionを凍結し、新規16 seedでcounterfactual 22/64、legacy 4/64、random matched 17/64を得た。counterfactual−randomは+0.3125 task/seed、95% CI [0.125, 0.5625]で、dual-mux XORのlearned-only 4解は全て採用Functionを実使用した。これによりE023の否定結果を捨てず、選別された1 Functionに限るtask-crossing transferの肯定例が加わった。

## タスク種別による違い

経路選択taskのmuxはE022・E023の全主要条件で16/16に達し、Library差を検出できない。parityは中間affine構造や一部Libraryで改善するが、cross-task条件では不安定だった。comparatorとcarryは同一task transferで改善した一方、leave-one-task-outでは改善しなかった。

E027では経路選択型dual-mux XORだけがcounterfactual 4/16、random 0/16、no-transfer 1/16へ改善した。精密数値型threshold2はcounterfactual 2/16、random 1/16、no-transfer 3/16で優位性がなく、threshold4は全条件0/16だった。E031の新規route 3 taskでは採用2/24、random 3/24となり、この肯定例はtask familyへ移らなかった。数値`unsigned_sum_ge6`では採用0/8、barrier 6/8であり、構造追加の有無より伝播範囲が探索を左右する兆候が出た。必要なのはtaskに合うFunctionの選別と、作用範囲の制御である。

## 次の研究仮説

truth-table error、source内頻度、構造費用のどれか一つではcross-task Moduleを選べなかった。次はFunctionの価値を、選定に使っていないprobe task群で子Functionを改善した因果的寄与として測る。

$$
V(F)=\alpha\,\Delta_{\mathrm{probe}}(F)+\beta\,D(F)-\lambda_p C_{\mathrm{primitive}}-\lambda_r C_{\mathrm{routing}}-\lambda_s C_{\mathrm{state}}
$$

ここで $\Delta_{\mathrm{probe}}$ は複数の未知probe taskでのoffspring改善、$D$ はLibrary内のsignature多様性である。選定後に新しいtask familyを固定し、source選定への過適合を分離する。最終式で使われないFunctionには、beamを変えた間接効果と実際の部品再利用を分けてcreditを与える。


## E024追試

一段probe utilityとsignature多様性を組み合わせても、選定後に固定した新規taskではutility-diverse 1/16、同費用random 2/16、移植なし7/16だった。Functionを固定保護すること自体がbeamを阻害した。cross-task価値の推定だけでなく、使用されないModuleを解放する形成・分解機構が必要である。[E024詳細](STAR-Bit-E024-probe-utility-diversity.md)。

## E025追試

局所改善childを作ったFunctionだけ保護を延長したが、8/8 Functionが判定を通り、round 3まで退役しなかった。usage-gated、fixed、unprotectedはいずれも2/16で、no transfer 5/16を下回った。初期Library投入が探索軌跡を変えるため、形成・分解には局所useではなくwith/without Moduleの反実仮想差が必要である。[E025詳細](STAR-Bit-E025-usage-gated-eviction.md)。

## E026追試

signature-stableなpaired probe探索で45候補をwith/without比較し、1 Functionだけを採用した。counterfactual 5/16はlegacy 2/16を上回り、no transfer・random matched各4/16と同程度だった。安全なadmission候補は得たが、randomを明確に上回らずtask横断transferは未成立である。[E026詳細](STAR-Bit-E026-counterfactual-admission.md)。

## E027独立確認

E026の1 Functionを凍結し、新規16 seed・256探索で確認した。counterfactual 22/64はlegacy 4/64とrandom matched 17/64を上回り、no-transfer 20/64も下回らなかった。阻害緩和とtask-crossing transferの事前基準を満たした。random比較のexact sign-flip pは0.0625、task別Holm補正は非有意で、効果はdual-mux XORに限られる。[E027詳細](STAR-Bit-E027-counterfactual-admission-confirmation.md)。

## E028機構Ablation

別の16 seedで採用Functionのcompositionを禁止してもbeam内には残す対照と、同費用の入力巡回置換を比較した。dual-mux XORでは採用4/16、禁止2/16、入力+1置換4/16。採用−禁止は+0.125 exact/seed、95% CI [−0.125, 0.375]、exact p=0.625で事前基準未達だった。採用onlyの3解は凍結signatureを含む一方、入力+1の4解は置換signatureを一度も使用しなかった。E027の探索到達性の信号を「抽象Moduleの直接再利用」と同一視できない。Libraryがbeamとcreditの軌跡を変える間接効果を分離する必要がある。[E028詳細](STAR-Bit-E028-module-causal-ablation.md)。

## E029軌跡トレース

新規16 seedで採用Function、入力+1置換、移植なしを同じ探索コードで比較し、各roundのbeam・credit・直接子候補を観測した。dual-mux XOR exactは4/16、3/16、2/16で、対応差は有意でない。入力+1だけが成功した3 seedは、最終式で置換Functionを使わないが、初回beamで入力+1条件だけに存在し、Functionとの直接ペア出力として生成可能な中間signatureを祖先に持った。事前指定した3件の予備的trajectory基準を満たす一方、同じsignatureを別経路から再生成できるため、Library由来の因果的な媒介とまでは言えない。[E029詳細](STAR-Bit-E029-beam-trajectory.md)。

## E030 provenance barrier

Function由来の代表式とFunction-freeな同一signatureをroundごとに区別し、round 2以降のFunction由来候補を親利用できないbarrierを追加した。新規16 seedのdual-mux XORは通常入力+1とbarrierがともに3/16、対応差0、95% CI [−0.25, 0.25]だった。通常だけが成功した2件ではround1のFunction由来signatureがround2でFunction-free式へ置換されたが、barrierだけが成功した例には同じlineageがない。E029の軌跡は実在するものの、成功に必要な共通機構という事前仮説は棄却された。[E030詳細](STAR-Bit-E030-provenance-barrier.md)。

## E031 task-family portability

E026のFunctionを固定したまま、結果を見る前にroute 3 taskとnumeric 2 taskを新規定義し、移植なし・通常Function・one-hop barrier・同一費用randomを8 seedで比較した。routeの通常Function−randomは−0.125 task/seed、95% CI [−0.375, 0]で可搬性基準を満たさなかった。`numeric_unsigned_sum_ge6`は通常0/8、barrier 6/8で、深いdescendant伝播が探索を妨げる仮説が生じたが、task内Holm p=0.09375である。route taskの2/3はほぼ床だったため、次は生成grammarを凍結して難度を層別化し、別seedで確認する。[E031詳細](STAR-Bit-E031-route-family-portability.md)。

## E032 one-hop replication

E031の数値taskを固定し、新規16 seedで無制限Function、一段barrier、composition不能なinert slot、移植なし、同一費用randomを比較した。barrier−通常は+0.625 exact/seed、95% CI [0.375, 0.875]、exact p=0.001953で事前再現基準を満たした。barrier−inertは+0.25、95% CI [−0.0625, 0.5625]、exact p=0.2891で一段固有の利益は未確認。inertと移植なしは全16 seedでexact・best errorが一致した。route XNORでは通常4/16、barrier2/16と作用方向が逆である。この段階の因果解釈は「特定の数値taskでは無制限伝播が探索を妨げる」に留める。[E032詳細](STAR-Bit-E032-one-hop-replication.md)。

## E033 prospective grammar pilot

数値の加算threshold 4/5/7と経路選択のcross-mux AND/OR/XNORを事前固定し、新規8 seed・4条件で192探索した。no-transferのみで難度を分類すると、全6 taskが床または天井で、中難度は0件だった。barrier−通常Functionの数値−経路family差は+0.125、95% CI [−0.0417, 0.2917]、exact p=0.375でpilot基準に届かなかった。個別に有利な数値`sum_ge7`を事後的に選ぶことはせず、新しいgrammarを事前固定して難度校正をやり直す。[E033詳細](STAR-Bit-E033-grammar-pilot.md)。

## E034 baseline探索予算校正

E033の6 taskを固定し、Functionを投入せず、round予算4・6・8を新規6 seedで比較した。中難度の事前定義はexact 2〜4/6。経路選択の`cross_and`のみ4 roundで3/6となり、数値3 taskはいずれの予算でも床または天井だった。両familyに中難度taskを確保する事前条件を満たさないため、Function効果の確認実験には進まない。予算変更だけでは難度を十分に校正できないことが分かり、数値grammarの閾値・演算子構成またはbeam幅をbaselineのみで次に検討する。[E034詳細](STAR-Bit-E034-budget-calibration.md)。

## E035 重み付き数値Grammar校正

探索予算を固定し、対称・非対称の重み付き和と閾値5/6/7から成る新規6 taskを、移植なし・新規6 seedで評価した。全36探索がexactに失敗し、中難度候補は0件だった。最も近い`numeric_symmetric_ge5`は全seedでbest error 1/64。これは精度の改善ではなく、次に探索資源を校正する候補をbaselineだけで特定した結果である。E034で凍結したroute候補は維持する。[E035詳細](STAR-Bit-E035-numeric-grammar.md)。

## E036 数値Beam幅校正

E035の近接数値taskを固定し、Functionを入れずにbeam幅64/128/192/256を新規6 seedで比較した。exactは0/6・0/6・0/6・2/6で、事前の中難度規則により`numeric_symmetric_ge5@beam256`を選んだ。幅256−192の対応差は+0.3333 exact/seed、exact p=0.5、Holm p=1で、幅の優位が有意になったわけではない。route候補と数値候補ではbeam・round予算が異なる。次は各task内で同一予算の対照を使い、独立seedでFunction効果を判定する。[E036詳細](STAR-Bit-E036-beam-calibration.md)。

## E037 独立シードでのFunction比較

凍結した数値・経路候補で新規6 seed、5条件を比較した。数値exactは移植なし2/6、通常Function0/6、one-hop barrier2/6、inert2/6、random1/6。routeは順に3/6、3/6、4/6、3/6、3/6だった。事前の数値−経路barrier効果差は+0.1667、95% CI [−0.3333, 0.6667]、exact p=1で基準未達。数値barrierとinertは全seedでexact・best error一致し、学習Functionを含む成功式は0件。無制限admissionが特定taskの探索を妨げうる兆候は残るが、一段利用の利益や低ビット補償の証拠にはならない。[E037詳細](STAR-Bit-E037-family-confirmation.md)。

## Roadmap

- [Done] hard circuit形成、Function-space統合、learned promotion、retirementを段階分離した。
- [Done] 同一task・別seed移植を16 seedと同費用random対照で確認した。
- [Done] leave-one-task-out 256探索により、task横断Concept transferが未成立であることを確認した。
- [Done] 平均・不偏分散、bootstrap CI、効果量、exact検定、多重比較補正、全expression再評価を各段階で保存した。
- [Done] E024で未知probe taskへの一段offspring寄与とsignature多様性を評価したが、held-out taskへ移らなかった。
- [Done] E027の独立16 seedで反実仮想admissionの阻害緩和と、dual-mux XORへの限定的task-crossing transferを確認した。
- [Done] E028で直接composition禁止と入力置換を比較し、直接再利用の事前基準未達と、最終式で未使用のFunctionが探索を変える可能性を示した。
- [Done] E029でsignature別のbeam生存・credit・親利用を計測し、3件の予備的な探索軌跡証人を記録した。
- [Done] E030で代表式provenanceとFunction-free置換を追跡し、one-hop barrierとの性能差0を確認した。
- [Done] E031で単一truth tableへの反復を止め、事前定義した新規5 taskでFunction・barrier・random対照を比較し、広い可搬性が未確認であることを示した。
- [Done] E032でE031の数値taskのbarrier差を独立16 seedで再現し、inert slot対照で一段固有の利益が未証明であることを分けた。
- [Done] E033で生成grammarを結果より前に固定し、pilotと確認を分離した。no-transfer基準では中難度0/6で、確認対象は選ばなかった。
- [Done] E034で固定Grammarのround予算をbaselineのみで校正し、routeには中難度1件が生じたが数値には生じないことを確認した。
- [Done] E035で新しい重み付き数値Grammarを試したが、6 taskすべてがexact 0/6で中難度候補を得られなかった。
- [Done] E036でbeam幅256の数値中難度候補をbaselineだけから選定し、route・numeric双方のpilot設定を凍結した。
- [Done] E037で独立seed・同task内同予算比較を完了し、family交互作用とone-hop固有利益が事前基準未達であることを確認した。
- [Next] Functionの未使用時にも生じるbeam摂動と費用を含むadmission gateを、新task群で事前固定して評価する。
- [Later] 中難度taskでFunctionのstage/round別使用制限と費用付きadmissionを比較する。
- [Later] cross-task再利用成立後、Ternary ExpertとLogic ModuleをRouterへ統合する。step 0からのload-balancing損失、均衡固定random Router、同一run内から別seedへのExpert交換を維持する。
- [Later] Library記述bit、物理primitive、active演算、Router、register、State、latencyを含む総費用で低ビット補償を再判定する。

English: E027 found a narrow cross-task search signal, while E028 did not confirm direct-composition causality. E029–E030 traced beam paths but found no necessary common lineage. E031 failed to transfer the benefit to three new routing targets. E032 replicated harm from unrestricted propagation on one numeric task without proving one-hop benefit. E033–E036 calibrated task difficulty. E037's independent seeds failed the preregistered task-family interaction and one-hop-specific gates; no successful expression used the learned Function.

简体中文：E027观察到有限的跨任务搜索信号，E028未证实直接组合因果性；E029–E030追踪了beam路径，但没有发现成功所必需的共同轨迹。E031未能将收益迁移到三个新路由目标；E032在一个数值任务上复现了无限制传播的不利影响，但未证明一跳使用本身有益。E033–E036校准了任务难度。E037的独立种子未达到预注册的任务族交互作用和一跳特有收益门槛；成功表达式均未使用学习函数。

[E022：同一task・別seed移植](STAR-Bit-E022-fixed-function-transfer.md) / [E023：leave-one-task-out](STAR-Bit-E023-leave-one-task-out-transfer.md) / [E027：独立確認](STAR-Bit-E027-counterfactual-admission-confirmation.md) / [E028：機構Ablation](STAR-Bit-E028-module-causal-ablation.md) / [E029：軌跡トレース](STAR-Bit-E029-beam-trajectory.md) / [E030：provenance barrier](STAR-Bit-E030-provenance-barrier.md) / [E031：task-family可搬性](STAR-Bit-E031-route-family-portability.md) / [E032：one-hop独立確認](STAR-Bit-E032-one-hop-replication.md) / [E033：生成Grammar pilot](STAR-Bit-E033-grammar-pilot.md) / [E034：探索予算校正](STAR-Bit-E034-budget-calibration.md) / [E035：数値Grammar校正](STAR-Bit-E035-numeric-grammar.md) / [E036：Beam幅校正](STAR-Bit-E036-beam-calibration.md) / [E037：独立Function比較](STAR-Bit-E037-family-confirmation.md) / [研究ログ](RESEARCH-LOG.md)
