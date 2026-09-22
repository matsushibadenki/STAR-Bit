# STAR-Bit：研究構想

> **2026-09-22 数値Grammar校正追記**：E035では新しい重み付き和の6タスクを、移植なし・新規6 seedで評価しました。すべてexact 0/6となり、数値の中難度候補はまだありません。最も近い`numeric_symmetric_ge5`は全seedで誤り1/64でした。次はこのtaskのbeam幅をbaselineのみで校正します。[E035レポート](STAR-Bit-E035-numeric-grammar.md)。
>
> English: Six new weighted-sum targets remained at 0/6 exact; the closest target had one error in 64 inputs on every seed. No Function efficacy was evaluated.
>
> 简体中文：六个新的加权求和目标均为0/6精确成功；最接近的目标在每个种子上只错64个输入中的1个。本实验未评价学习函数。

> **2026-09-22 探索予算校正追記**：E034ではFunctionを使わず、E033の6タスクのround上限だけ4/6/8に変えました。経路選択`cross_and`はround 4で3/6の中難度になりましたが、数値側は中難度0件で、両familyの確認実験へ進む基準を満たしませんでした。数値の`sum_ge5`は全予算0/6、`sum_ge7`は最大1/6で、roundを増やすだけでは床効果を解消できません。[E034レポート](STAR-Bit-E034-budget-calibration.md)。
>
> English: A baseline-only round-budget sweep produced one mid-difficulty routing task and no mid-difficulty numeric task. Function-policy confirmation remains pending.
>
> 简体中文：仅用基线进行的搜索轮数校准得到一个中等难度路由任务，却没有中等难度数值任务；函数策略的确认实验仍待进行。

> **2026-09-22 生成Grammar Pilot追記**：E033では結果を見る前に数値3・経路選択3タスクを固定し、8 seed・4条件の192探索を完了しました。移植なしの成功率で定義した中難度taskは0/6で、family interactionも+0.125（95% CI [−0.0417, 0.2917]、p=0.375）とpilot基準未達です。Function条件を見て都合のよい確認対象を選ばず、新しいgrammarを先に定義します。[E033レポート](STAR-Bit-E033-grammar-pilot.md)。
>
> English: E033's frozen six-task grammar produced no mid-difficulty target under the baseline-only rule. The exploratory family interaction failed its pilot gate; the next grammar will be fixed before testing.
>
> 简体中文：E033预先固定的六任务规则未产生中等难度目标，探索性的任务族交互作用也未达标。下一套任务规则将在测试前固定。

> **2026-09-22 Function伝播の独立確認**：E032でE031の数値`unsigned_sum_ge6`の結果を新規16 seedで確認しました。通常Functionは2/16、one-hop barrierは12/16で、対応差+0.625（95% CI [0.375, 0.875]、exact p=0.001953）です。一方、barrier対inert slotは12/16対8/16で有意ではなく、一段のFunction使用が必要とは示されません。route XNORでは通常4/16、barrier 2/16と方向が逆です。[E032レポート](STAR-Bit-E032-one-hop-replication.md)。
>
> English: E032 independently replicated harm from unrestricted Function propagation on one numeric task, but did not establish a benefit over an inert slot. The route comparator moved in the opposite direction.
>
> 简体中文：E032在一个数值任务上独立复现了无限制函数传播的不利影响，但未证明一跳屏障优于惰性槽。路由对照任务呈相反方向。

> **2026-09-21 Task-family可搬性追記**：E031では1つのdual-mux XORへの反復を止め、事前定義した新規route 3 task・numeric 2 taskを新規8 seedで比較しました。固定Functionはrouteで2/24、同一費用randomは3/24、primary差は−0.125 task/seed（95% CI [−0.375, 0]）で、広い可搬性は支持されませんでした。数値`unsigned_sum_ge6`では固定Function 0/8に対してone-hop barrier 6/8でしたが、Holm補正後p=0.09375です。次は生成grammarとinert-slot対照で床効果と初期候補数の交絡を分離します。[E031レポート](STAR-Bit-E031-route-family-portability.md)。
>
> English: E031 did not reproduce the dual-mux benefit across three preregistered routing targets: the frozen Function solved 2/24 versus 3/24 for equal-cost random controls. A one-hop barrier helped one numeric target, but the contrast did not survive Holm correction.
>
> 简体中文：E031未在三个预注册路由目标上复现dual-mux收益：冻结函数成功2/24，同成本随机对照为3/24。一跳屏障改善了一个数值目标，但差异未通过Holm校正。

> **2026-09-20 Provenance Barrier追記**：E030ではFunction由来の式をround 2以降の親に使わせないone-hop barrierを新規16 seedで比較しました。dual-mux XORは通常入力置換とbarrierがともに3/16、対応差0（95% CI [−0.25, 0.25]、exact p=1）で、伝播機構の事前基準は未達でした。通常条件だけが成功した2件ではFunction由来signatureが次roundにFunction-free式へ置換されましたが、barrierだけが成功した2件には同じlineageがありません。E029の軌跡は観測できるものの、成功に必要な共通機構ではありません。[E030レポート](STAR-Bit-E030-provenance-barrier.md)。
>
> English: A one-hop provenance barrier matched normal rotated-Function search at 3/16 dual-mux solutions; the paired difference was zero. Function-to-clean signature replacement appeared in two normal-only successes but not in barrier-only successes, so it is not a necessary common mechanism.
>
> 简体中文：一跳来源屏障与普通旋转函数搜索在dual-mux上均成功3/16，配对差为零。函数来源签名向无函数等价式的替换只出现在两个普通条件成功例中，屏障条件的成功例没有该轨迹，因此它不是必要的共同机制。

> **2026-09-18 Beam探索軌跡の追跡**：E029では新規16 seedで、採用Function・入力+1置換・移植なしのbeamとcreditを同じ探索アルゴリズムのまま記録しました。dual-mux XOR exactは順に4/16、3/16、2/16で、対応差は有意ではありません。一方、入力置換だけが成功した3件はすべて最終式に置換Functionを含まず、初回beamで置換条件だけに残った「直接子として生成可能なsignature」を最終式の祖先に持ちました。事前指定した予備的trajectory基準は満たしましたが、同一signatureの別経路生成があるため、Module由来の因果的な媒介は未証明です。[E029レポート](STAR-Bit-E029-beam-trajectory.md)。
>
> English: E029 found three preliminary beam-trajectory witnesses with a frozen input-rotated Function, but no significant paired exact advantage. Equivalent signatures may be regenerated, so their provenance is not yet causal proof.
>
> 简体中文：E029发现3个初步beam轨迹证据，但配对精确成功率没有显著优势。等价签名可能由其他路径重新生成，因此尚不能证明其因果来源。

> **2026-09-17 転移機構のAblation**：E028ではE027の採用Functionを凍結し、別の16 seedで直接composition禁止と同費用の入力置換2種を比較しました。dual-mux XORで採用Functionは4/16、composition禁止は2/16でしたが、対応差+0.125（95% CI [−0.125, 0.375]、exact p=0.625）で事前基準を満たしませんでした。入力置換+1も4/16でしたが最終式で当該Functionは0回使用。E027の限定的transfer信号は残る一方、直接再利用可能なModuleが効果を生むという機構は未証明です。[E028レポート](STAR-Bit-E028-module-causal-ablation.md)。
>
> English: In 16 new seeds, the admitted Function solved dual-mux XOR in 4/16 versus 2/16 with composition vetoed, but the paired criterion failed (exact p=0.625). A cost-matched input rotation also solved 4/16 without appearing in final circuits. Direct Module reuse remains unproven.
>
> 简体中文：在16个新seed中，原函数于dual-mux XOR成功4/16，禁止组合后为2/16，但配对标准未达成（精确p=0.625）。同成本的输入旋转也成功4/16，却未出现在最终电路中。直接复用模块的因果机制仍未证实。

> **2026-09-16 Counterfactual Admission独立確認**：E026で選ばれた1 Functionを再選別せず凍結し、新規16 seed・4 held-out task・4条件の256探索を実施しました。counterfactual 22/64、legacy 4/64、no-transfer 20/64、構造同費用random 17/64でした。legacyとの差は+1.125 task/seed（95% CI [0.75, 1.50]）、randomとの差は+0.3125（95% CI [0.125, 0.5625]）。dual-mux XORのlearned-only成功4件はすべて凍結Functionを実使用し、事前登録した阻害緩和とtask-crossing transferの両基準を満たしました。効果は経路選択タスクに集中し、数値thresholdでは確認できていません。[E027レポート](STAR-Bit-E027-counterfactual-admission-confirmation.md)。
>
> English: Freezing the single E026 Function and testing 16 new seeds yielded 22/64 exact solutions versus legacy 4/64, no-transfer 20/64, and structurally matched random 17/64. Both preregistered criteria passed; the learned-only benefit was concentrated in dual-mux XOR, not numeric thresholds.
>
> 简体中文：冻结E026选出的单个函数并在16个新seed上验证后，反事实准入达到22/64，旧Library为4/64，无迁移为20/64，结构匹配随机对照为17/64。两项预注册标准均达成，但收益集中在dual-mux XOR路径选择任务，数值阈值任务没有显示收益。

> **2026-09-15 Counterfactual Admission追記**：E026では45 Functionを、決定的tie-breakを共有するprobe探索のwith/without差で選別し、1 Functionだけを採用しました。新規4 seedでlegacy 8個投入2/16に対しcounterfactualは5/16、移植なしとrandom同費用は各4/16でした。探索阻害の緩和基準は満たしましたが、randomとの差は+1件だけでtransfer基準は未達です。反実仮想admissionは安全なLibrary形成候補ですが、task横断Conceptの証拠ではありません。[E026レポート](STAR-Bit-E026-counterfactual-admission.md)。
>
> English: Counterfactual probe admission selected 1 of 45 Functions and improved discovery from legacy 2/16 to 5/16; no-transfer and random matched each reached 4/16. It mitigated harmful admission but did not meet the transfer criterion.
>
> 简体中文：反事实probe准入从45个函数中选出1个，将成功数从旧方案2/16提高到5/16；无迁移和随机匹配均为4/16。它缓解了有害准入，但未达到迁移标准。

> **2026-09-15 Usage-gated Eviction追記**：E025ではE024のFunctionを、改善childの親になった場合だけ保護期限を更新する方式へ変更しました。usage-gated、固定保護、無保護はいずれも2/16、移植なしは5/16でした。全8 Functionが局所改善childを一度は作り、round 3で退役が起きなかったため、現在のusage判定には識別力がありません。初期Libraryとのcomposition自体がbeam軌跡を変えるため、次はwith/without Moduleの反実仮想差でadmissionします。[E025レポート](STAR-Bit-E025-usage-gated-eviction.md)。
>
> English: Usage-gated eviction did not recover search performance. Learned gated, fixed, and unprotected admission each solved 2/16 cases versus no-transfer 5/16; every Function passed the local-use test, making it non-selective.
>
> 简体中文：按使用情况退役未能恢复搜索性能。门控、固定保护和无保护学习库均成功2/16，而无迁移成功5/16；所有函数都通过了局部使用判定，因此该判定没有区分力。

> **2026-09-14 Probe Utility追記**：E024ではsource頻度・target errorに代えて、選定用probe taskでの一段composition改善とsignature多様性からFunctionを選びました。選定後に固定した4新規task×4 seedで、utility-diverseは1/16、同費用randomは2/16、移植なしは7/16でした。事前の16-seed移行基準は未達です。一段lookaheadと静的多様性でもtask横断Module価値は捉えられず、無用な固定Library枠が探索を阻害することを確認しました。[E024レポート](STAR-Bit-E024-probe-utility-diversity.md)。
>
> English: One-step probe utility plus signature diversity solved 1/16 held-out cases versus random 2/16 and no-transfer 7/16. The expansion gate failed; protected slots can harm search when Modules are not useful.
>
> 简体中文：一步probe效用加签名多样性在保留任务上成功1/16，随机库2/16，无迁移7/16。扩展标准未达成；无用模块的固定保护槽会损害搜索。

> **2026-09-13 Cross-task Transfer追記**：E023では評価task由来のsource回路を完全に除外して16 seed×4 task×4条件を比較しました。learned cross-taskとtruth-table errorを揃えたrandom対照はともに27/64で、対応差0（95% CI [−0.3125, 0.3125]、exact p=1）でした。通常のcost-matched randomは37/64でlearnedを上回り、learned条件でも移植Functionを実際に使った解は3/27だけでした。E022の別seed再利用は支持されますが、別task Concept再利用は支持されません。[E023レポート](STAR-Bit-E023-leave-one-task-out-transfer.md)。
>
> English: Leave-one-task-out evaluation removed the E022 advantage. Learned cross-task and error-matched random Libraries both solved 27/64 cases; cost-matched random solved 37/64. Cross-task conceptual reuse is unsupported.
>
> 简体中文：留一任务评估消除了E022的优势。跨任务学习库与误差匹配随机库均成功27/64，成本匹配随机库成功37/64；目前不支持跨任务概念复用。
>
> E017〜E034の統合評価は[Module Genesis Milestone 3](STAR-Bit-milestone-module-genesis.md)にまとめています。

> **2026-09-13 Learned-Function Transfer追記**：E022ではE021のsource回路から出力を除く16内部Functionを固定Library化し、新規16 seedへ移植しました。同じ式木形状・primitive・routing・depthのランダムLibraryに対し、exact target平均は1.8750から2.4375、対応差+0.5625（bootstrap 95% CI [0.1875, 0.9375]、exact sign-flip p=0.03125）でした。comparatorは1/16→5/16、carryは1/16→4/16で事前pilot基準を満たしました。ただし同一task由来の部分回路を許した別seed移植であり、task横断のConcept再利用は未証明です。[E022レポート](STAR-Bit-E022-fixed-function-transfer.md)。
>
> English: A fixed learned Function Library improved exact target discovery by +0.5625 over shape- and cost-matched random Functions across 16 held-out search seeds. Same-task source subcircuits were allowed, so task-independent transfer remains unproven.
>
> 简体中文：固定学习函数库在16个独立搜索种子上，相比形状和成本匹配的随机函数，将精确目标发现提高+0.5625。由于允许使用同任务来源的子电路，尚未证明任务无关迁移。

> **2026-09-13 Cost-normalized Promotion追記**：E021ではoffspring creditをtask間再利用と構造費用で正規化し、古いcreditを退役させました。raw promotion対照よりcredit台帳を46.9%、時間を5.5%削減しながらexact target平均を2.25から2.50へ維持し、初のcarry exactを1/4 seedで発見しました。ただし最終beam内credit付きFunctionは10.4%しか減らず、事前登録した30%基準は未達です。carryの再現性と移植効果は未確認です。[E021レポート](STAR-Bit-E021-cost-normalized-promotion.md)。
>
> English: Cost normalization and retirement reduced the credit registry by 46.9% and runtime by 5.5% while preserving target discovery, and found carry once. The preregistered final-beam reduction criterion was not met.
>
> 简体中文：成本归一化和退役机制将credit台账缩小46.9%、运行时间缩短5.5%，同时保持目标发现能力，并首次找到一次carry；但最终beam缩减的预注册标准未达成。

> **2026-09-13 Learned Archive Promotion追記**：E020ではE019の手指定affine scaffoldを外し、良い子Functionを生成した親signatureを実測creditで自動昇格しました。target-greedyのexact target平均1.00に対しpromotionは2.25となり、parity 3/4と初のcomparator 2/4へ到達しました。carryは0/4で、時間は3.24秒から26.43秒へ増えています。中間Function価値の学習には肯定的な兆候がありますが、自律Module Genesisは未成立です。[E020レポート](STAR-Bit-E020-learned-archive-promotion.md)。
>
> English: Learned offspring credit raised exact targets from 1.00 to 2.25 and discovered comparator in 2/4 seeds without a hand-selected function family. Carry remained unsolved and runtime grew sharply.
>
> 简体中文：基于子代贡献的自动晋升在不指定函数族的情况下，将精确目标数从1.00提高到2.25，并在2/4种子中发现comparator。carry仍未解决，运行时间明显增加。

> **2026-09-12 Module Genesis追記**：E019で探索単位をGate構文から64-bit Function signatureへ変更し、同値構文を生成時に統合しました。同値統合と一段lookaheadだけではmuxしか到達しませんでしたが、タスク非依存のaffine中間signatureを保持するとparityが0/4から4/4 seedへ回復しました。これは踏み石の保持が到達可能性を変える肯定例ですが、人手でaffine族を選んだ帰納バイアスであり、自律Module Genesisではありません。次は子候補への実測寄与から親Functionを自動昇格します。[E019レポート](STAR-Bit-E019-function-space-genesis.md)。
>
> English: E019 moved from gate syntax to exact function signatures. Equivalence merging alone was insufficient, while retaining a task-independent affine scaffold recovered parity in 4/4 seeds. The next step replaces this hand-selected function family with learned archive promotion.
>
> 简体中文：E019将搜索单位从门语法改为精确功能签名。仅合并等价功能仍不够，而保留任务无关的仿射支架使parity恢复到4/4。下一步将用学习到的档案晋升替代人工选择的功能族。

> **2026-09-12 Learned Circuit Abstraction追試**：E017で学習配線DLGNを入力出力例からhard circuit化しました。parityとmuxは4/4 pilot seedで全64入力完全一致しましたが、comparator/carryは0/4でした。離散refinementはDLGN開始13/16、random開始12/16のexact到達で、全タスク基準を満たしていません。E018のCEGISもparity/muxを高速化した一方、成功数はall-row SATと同じ8/16で、Module抽象化の主比較は保留しました。[E017境界レポート](STAR-Bit-E017-learned-circuit-abstraction.md)と[E018 CEGISレポート](STAR-Bit-E018-cegis-mdl.md)を参照してください。
>
> English: Learned wiring produced exact parity and mux circuits, but comparator and carry remained unresolved. CEGIS accelerated the easy tasks without improving total synthesis success, so autonomous Module-abstraction claims remain withheld.
>
> 简体中文：学习配线生成了精确的parity与mux电路，但comparator与carry仍未解决。CEGIS加速了简单任务，却没有提高总体合成成功率，因此暂不提出自主模块抽象结论。

> **2026-09-12 Milestone 2**：検証済みLogic PE prior下で4 Expertsと入力依存Routerを共同学習し、全入力で均衡するラベル非依存fixed hash対照と16 seedで比較しました。独立hash追試のnumeric改善は+0.1035（95% CI [0.0508, 0.1602]、exact p=0.001953）、selection改善は+0.3359（Holm p=0.000244）でした。負荷分散損失はupdate 0から適用し、Expert交換は同一run内から別seedの順で実施しています。経路選択はRouter–Expert対応、精密数値はState付きmoduleへの依存が相対的に強いという分析まで到達しました。結論と限界は[Logic Routing Milestone 2](STAR-Bit-milestone-joint-routing.md)を参照してください。
>
> English: Milestone 2 isolates learned routing from a balanced fixed random hash under a verified Logic-PE prior and confirms the numeric result with independent random streams. Route selection depends more strongly on Router–Expert assignment, while numeric addition depends more on the recurrent stateful module.
>
> 简体中文：里程碑2在已验证Logic PE先验下，将学习路由与均衡固定随机哈希分离，并用独立随机流复验数值任务。路径选择更依赖Router与Expert的对应关系，数值加法更依赖递归状态模块。

> **2026-09-12 Milestone 1**：固定ランダム論理配線の表現制約をSATで診断し、State付きLogic PEを時間再利用するprototypeまで進めました。16 split seedでtrain-selected scheduleは固定ランダムscheduleをnumeric +0.7402、selection +0.5098 test exact上回り、Holm補正後も有意でした。物理primitive数は空間展開比で66.7%／50%減りましたが、active演算数は減らず、強いmodule事前知識を使う小型Boolean実験です。結論と限界は[Logic Routing Milestone 1](STAR-Bit-milestone-logic-routing.md)を参照してください。

> **2026-09-10追記**：ゲート数増大への対策と自律的なモジュール形成のアイデアを追加し、[回路モジュール発見・Logic PE再利用の実験](STAR-Bit-logic-modules-results.md)を実施しました。記述の圧縮と実行ゲート削減を分け、構想の追加仕様は[改訂計画](STAR-Bit-validation.md)第11節に記録しています。

> **2026-09-09 検証追記**：以下は当初の構想であり、本文のAccuracy 76%・82%・83%・85%等は仮定値です。研究仮説は検証可能ですが、精度回復や通常MoEを超える新規性は未証明です。現在の実験仕様・判断基準は [研究検証と改訂計画](STAR-Bit-validation.md) を優先してください。
>
> 追加された5条件（複数シードと統計、初期からの負荷分散補助損失、固定ランダム経路、同一ラン内→別シードのExpert交換、精密数値と経路選択の比較）を含む小型MLPの96訓練runを実施しました。[予備実験の実測結果](STAR-Bit-pilot-results.md) を参照してください。これはTransformer・動的接続の本検証ではなく、多重比較補正後の有意差は確認できていません。
>
> English: Original proposal; illustrative scores are not measurements. See the revised protocol and CPU pilot report. Precision recovery and dynamic-topology benefits remain unproven.
>
> 简体中文：下文为原始构想，示例分数并非实测结果。请参阅修订方案和CPU预实验报告；精度补偿和动态拓扑收益尚未得到证明。

最も安く検証するなら、最初から「新しいLLM」を作る必要はありません。確認すべきなのは、もっと狭い仮説です。

$$
\boxed{\text{Weight Precisionを減らした分をTopology / Routing / Memoryへ移すと能力が戻るか}}
$$

この一点だけを切り出して比較します。仮に実験系を「STAR-Bit」と呼びます。Structural Topology Augmented Routing for BitNet の略です。

考え方は、通常のニューラルネットワークを大雑把に

$$
C=f(N,P)
$$

と見たとき、\(N\) をパラメータ数、\(P\) をパラメータ精度として、これを

$$
\boxed{
C=f(N,P,T,R,M)
}
$$

へ拡張することです。

ここで、\(P\) は Weight Precision、\(T\) は Topology、\(R\) は Routing、\(M\) は Memory、\(N\) は Parameter Count です。

BitNet化では

$$
P\downarrow
$$

します。その代わりに、

$$
T,R,M\uparrow
$$

を許す。つまり今回のテーマは、

$$
\boxed{
\text{数値的自由度}
\rightarrow
\text{構造的自由度}
}
$$

という置き換えが成立するかどうかです。

DLGNについては、実数値の緩和を使って学習し、その後に離散的な論理ゲートへ落とす方法がすでに示されています。またMoEでは、入力ごとに一部の経路だけを選択することで、総パラメータ量と実際に使う演算量を分離できます。今回の実験では、この2つを低ビットTransformerに追加できる「別の自由度」として考えます。([arxiv.org](https://arxiv.org/abs/2210.08277?utm_source=chatgpt.com))

ただし、最初からBitNet、DLGN、SNN、Memory、Dynamic Routing、Structural Plasticityを全部載せるのは避けます。そうすると、結果が良くても悪くても原因が分からなくなるからです。

最初の構成はこれだけで十分です。

```text id="77nk93"
Token
  │
  ▼
Embedding
  │
  ▼
BitNet Block
  │
  ▼
Structural Router
  │
 ┌┴───────────────┐
 ▼                ▼
Expert A         Expert B
BitNet           BitNet
 └───────┬────────┘
         ▼
      BitNet Block
         │
         ▼
       Output
```

つまり、最初に試すのは

$$
\boxed{\text{BitNet + Sparse Structural Routing}}
$$

です。

ここで普通のMoEとの差を意識します。単にExpertを複数用意するのではなく、「どの接続を通ったか」そのものを情報として扱います。

たとえば8個の小モジュール、

```text id="dk8v7j"
A B C D E F G H
```

を用意します。Denseモデルなら毎回、

```text id="kgr9ui"
A → B → C → D → E → F → G → H
```

を通ります。

STAR-Bitでは入力によって、

```text id="ad3rfc"
質問1

A → C → F → H
```

あるいは、

```text id="z7qcnm"
質問2

A → B → E → G → H
```

のように経路を変えます。

つまり、重みだけでなく

$$
\text{Path}
$$

も潜在表現になります。

この発想でなぜ自由度が増えるのかは、組合せを考えると分かりやすいです。8モジュールのうち4個を選ぶだけなら、

$$
{8 \choose 4}=70
$$

通りあります。

順番も自由にすると、

$$
P(8,4)=8\times7\times6\times5=1680
$$

通りです。

16個から4個を選び、順序も考えるなら、

$$
P(16,4)=43,680
$$

通りになります。

もちろん、「43,680通りあるからその分だけ知能が増える」という意味ではありません。確認したいのは、

$$
\boxed{\text{Topology自体が追加の自由度になる}}
$$

かどうかです。

モデルサイズは大きくする必要がありません。最初は10〜30Mパラメータ程度で十分です。たとえば、

```text id="o0cxsc"
Vocabulary        8k〜16k
Embedding         256
Layers            6
Attention heads   4
Context            256〜512
Expert modules     8
Active experts     2
```

程度で始められます。

MacBook Air M4 / 32GBでも十分実験対象になる規模です。目的は高性能な言語モデルを作ることではなく、

$$
\text{Architecture A > Architecture B?}
$$

を確かめることだからです。

比較モデルは4系統に分けます。

```text id="vdi41w"
A: FP16 Dense
B: Ternary Dense
C: Ternary + More Parameters
D: Ternary + Structural Routing
```

整理すると、

| モデル |  Weight | Structure      |
| --- | ------: | -------------- |
| A   |    FP16 | Dense          |
| B   | ternary | Dense          |
| C   | ternary | Dense / wider  |
| D   | ternary | Dynamic sparse |

です。

Cを入れる理由は重要です。Dの成績が良かった場合に、「構造が効いたのではなく、単に総パラメータ数が増えただけではないか」という反論を分離するためです。

さらに比較条件は2種類用意します。

一つは、

$$
\boxed{\text{同じ総パラメータ数}}
$$

です。

もう一つは、

$$
\boxed{\text{同じActive Parameter数}}
$$

です。

たとえばDense BitNetが、

```text id="gh6r8v"
Dense BitNet

Total = 20M
Active = 20M
```

であるのに対し、STAR-Bitを、

```text id="0q5262"
STAR-Bit

Total = 50M
Active = 20M
```

にします。

この条件でSTAR-Bitが強ければ、「1トークン当たりに動かす演算量を大きく増やさず、構造によって総容量を増やせる」可能性が出てきます。

これはMoEですでに使われている考え方に近く、Switch Transformerではスパースルーティングによって、大きな総パラメータ数と比較的一定のトークン当たり計算量を両立しています。([jmlr.org](https://www.jmlr.org/beta/papers/v23/21-0998.html?utm_source=chatgpt.com))

Routerは最初から低ビット化しない方がよいです。ここだけはFP16で構いません。

```text id="qfskm9"
Input
  ↓
FP16 Router ← ここだけ高精度
  ↓
Ternary Experts
```

Routerをモデル全体の1〜2%程度に抑えれば、

$$
98\%:\ ternary
$$

に対して、

$$
2\%:\ high\ precision
$$

で全体の経路選択を制御できます。

つまり、少量の高精度部分で大量の低精度回路を制御する設計です。

8 Expertの場合、Routerは例えば、

$$
R(x)=[r_1,\ldots,r_8]
$$

を出します。

```text id="d20rqm"
[0.04, 0.71, 0.02, 0.01,
 0.18, 0.01, 0.02, 0.01]

      ↓

Expert 2
Expert 5
```

というようにTop-2だけを有効化します。

Switch TransformerではTop-1 routingによる疎な計算が使われており、この方式自体は出発点として十分実績があります。([jmlr.org](https://www.jmlr.org/beta/papers/v23/21-0998.html?utm_source=chatgpt.com))

その次に、普通のMoEより一段進めます。Expertを選ぶだけでなく、Layer間の接続先もRouterに選ばせます。

```text id="je39j5"
Layer 1
 A B C

Layer 2
 D E F

Layer 3
 G H I
```

ある入力では、

```text id="yvp86e"
Input
  │
  A
 / \
D   E
|   |
H   I
```

別の入力では、

```text id="n2go8m"
Input
  │
  C
 / \
D   F
 \ /
  G
```

というように、実行グラフそのものが変わります。

ここで初めて、

$$
\boxed{\text{Dynamic Computational Graph}}
$$

になります。

この段階で効果が見えたら、次にDLGNを加えます。最初からExpert全体をDLGNへ置き換える必要はありません。

```text id="80sf32"
               ┌→ BitNet Expert
Input → Router ┤
               └→ Logic Expert
```

という並列構造にします。

> 2026-09-09追記：Logic Expertは手書き規則に限定せず、学習可能な論理回路として扱います。ユーザー指定の[論理ゲートAI解説記事](https://zenn.dev/teba_eleven/articles/68955053ed75be)と、その参照する畳み込み・再帰型の一次資料を踏まえた[追加検証仕様](STAR-Bit-validation.md#10-追加参考論理ゲートaiをどう位置づけるか)を参照してください。以下の役割分担は設計案であり、DLGNの能力を比較・条件処理だけに限定するものではありません。

Logic Expertでは、

```text id="fdwd0o"
AND
OR
XOR
NAND
NOR
XNOR
```

などを学習させます。

Deep Differentiable Logic Gate Networksでは、訓練時に連続的な緩和を使い、最後に離散論理回路へ変換する方式が示されています。([arxiv.org](https://arxiv.org/abs/2210.08277?utm_source=chatgpt.com))

役割分担は明確にします。

```text id="k14alx"
BitNet
意味・曖昧性・言語

DLGN
比較・条件・離散関係
```

たとえば、

```text id="4wo245"
Alice > Bob
Bob > Carol
```

という自然言語入力をBitNetで関係表現へ変換し、

```text id="68iarq"
Alice > Bob
Bob > Carol
```

をDLGNへ渡します。

DLGN側は、

```text id="ksycjm"
A > B
AND
B > C

→ A > C
```

のような処理を担当する、という分業です。

学習データも安く作れます。半分程度を合成データにしてよいです。

例えば、

```text id="yfq75m"
A is older than B.
B is older than C.

Who is oldest?
```

や、

```text id="cw4bml"
A → B
B → C
C → D

Can A reach D?
```

あるいは、

```text id="pjsx31"
If A then B.
A is true.

Is B true?
```

です。

これはPythonだけで大量生成できます。LLM APIを使う必要はありません。

ただし、学習データと同じ形式をそのまま解けただけでは評価になりません。そこで、訓練時には、

```text id="a1g5uj"
2-hop relation
3-hop relation
```

だけを与えます。

テストでは、

```text id="s7lczr"
4-hop
5-hop
6-hop
```

を出します。

ここで、

```text id="bd3pao"
Dense BitNet  <  Structural BitNet
```

になれば、「構造化によって低ビットネットワークの外挿能力が改善した」可能性が見えてきます。

もう一つはCompositionです。

訓練では、

```text id="j1dfgk"
A AND B
A XOR B
```

を別々に学習させます。

テストでは、

```text id="nzmsno"
(A XOR B) AND C
```

を出します。

ここでDLGN hybridが優位なら、

$$
\boxed{\text{Compositional Generalization}}
$$

に構造化が寄与している可能性があります。

Memoryはさらに後です。そこまでで効果が確認できた場合だけ追加します。

```text id="l968ws"
             ┌─────────────┐
             │ Memory Bank │
             └──────▲──────┘
                    │
Input → BitNet → Router
                    │
         ┌──────────┴───────┐
         ▼                  ▼
       BitNet             DLGN
```

最初は単純なKey-Value Memoryで十分です。1万件程度ならFAISSすら必要なく、

$$
QK^T
$$

で検索しても小規模実験では問題ありません。

さらにMemory key自体を、

```text id="w2iyfa"
101101001...
```

のような64〜256bitのbinary codeにして、

$$
d_H(q,k)
$$

つまりHamming distanceで近傍検索する方法もあります。

そうすると、

```text id="2x5fvq"
BitNet
+
Binary Memory
+
Logic Network
```

という、かなり低精度寄りのシステムになります。

最終形は概念的には次のようになります。

```text id="99xxb0"
                    Input
                      │
                      ▼
              Token Embedding
                      │
                      ▼
               BitNet Encoder
                      │
                ┌─────┴─────┐
                │   Router  │
                └─────┬─────┘
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
       BitNet       BitNet       DLGN
       Expert       Expert       Expert
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
                Memory Lookup
                      │
                      ▼
               BitNet Decoder
                      │
                      ▼
                    Output
```

評価ではAccuracyだけを見るのでは不十分です。少なくとも、

$$
\text{Accuracy}
$$

$$
\text{Perplexity}
$$

$$
\text{Active Parameters/token}
$$

$$
\text{Total Parameters}
$$

$$
\text{Memory footprint}
$$

$$
\text{Latency/token}
$$

を記録します。

今回の研究固有の指標としては、例えば、

$$
SE=
\frac{\text{Task Score}}
{\text{Active Parameters}}
$$

というStructural Efficiencyを置けます。

より実用的には、

$$
SE=
\frac{\text{Accuracy}}
{\text{Inference FLOPs}}
$$

でもよいです。

さらに、

$$
\boxed{
\text{Structural Gain}
=
Score_{structural}
-
Score_{dense}
}
$$

も測ります。

Routerが本当に構造自由度を使っているか確認するために、Routing Entropyも必須です。

$$
H(R)=-\sum_i p_i\log p_i
$$

を測ります。

Expertが8個あっても、

```text id="85k0zr"
Expert utilization
Path diversity
Path specialization
```

が低く、実際には1つしか使われていないなら、構造自由度は機能していません。

逆に、学習後に、

```text id="z3ulhs"
Expert A → arithmetic
Expert B → comparison
Expert C → temporal
Expert D → spatial
```

のような専門化が自然に生じれば、

$$
\boxed{\text{knowledgeがweightだけでなくstructureにも移った}}
$$

可能性を示す材料になります。

さらに面白いのは、学習後にExpertを一部だけ交換する実験です。

```text id="tl5ngp"
Expert C
```

だけ別モデル由来のものへ入れ替えます。

その結果、

```text id="namuj0"
全体を再学習しなくても
特定能力だけ変わる
```

のであれば、知識が巨大なweight space全体へ完全に分散しているのではなく、

```text id="5teslj"
Knowledge
 ↓
Modules
 ↓
Topology
```

へある程度局所化できている可能性があります。

実装は、まずPyTorchだけで十分です。構成は例えば次のようにできます。

```text id="77fero"
/star-bit/
├── README.md
├── configs/
│   ├── dense_fp16.yaml
│   ├── dense_ternary.yaml
│   └── structural_ternary.yaml
│
├── src/
│   ├── model/
│   │   ├── transformer.py
│   │   ├── bitlinear.py
│   │   ├── router.py
│   │   ├── expert.py
│   │   ├── structural_block.py
│   │   └── logic_expert.py
│   │
│   ├── data/
│   │   ├── logic.py
│   │   ├── relations.py
│   │   └── language.py
│   │
│   ├── train.py
│   ├── evaluate.py
│   └── metrics.py
│
├── experiments/
│   ├── baseline/
│   ├── routing/
│   ├── logic/
│   └── memory/
│
└── results/
```

Python 3.10 + PyTorchで始められます。NumPyが必要なら、

```bash id="w24s9d"
pip install "numpy<2.0"
```

で固定してよいです。

BitLinearについても、初期段階では本物の1.58-bit専用kernelを作る必要はありません。訓練時に、

$$
W_q=\mathrm{round/clip}(W)
$$

として、

$$
W_q\in\{-1,0,+1\}
$$

をシミュレーションすれば十分です。

実際のmatmulはFP16/BF16のままで構いません。最初の目的は高速化ではなく、構造として能力差が出るかを確かめることだからです。専用ternary kernelは、アーキテクチャ上の効果が確認できてからでよいです。

BitNet b1.58自体も三値重み \(\{-1,0,1\}\) を使うモデルとして提案されています。([microsoft.com](https://www.microsoft.com/en-us/research/publication/the-era-of-1-bit-llms-all-large-language-models-are-in-1-58-bits/?utm_source=chatgpt.com))

実験は段階的に進めます。

```text id="k0v2s2"
Phase 0
FP16 Dense
vs
Ternary Dense

       ↓

Phase 1
Ternary Dense
vs
Ternary + Router

       ↓

Phase 2
Ternary Router
+ Dynamic topology

       ↓

Phase 3
+ Logic Expert

       ↓

Phase 4
+ Associative Memory

       ↓

Phase 5
+ Recurrent/Event State
```

SNNは最後で構いません。

最初の成功条件も単純でよいです。例えば、

```text id="30dq2u"
Ternary Dense
Accuracy 76%
Active 20M

STAR-Bit
Accuracy 82%
Active 20M
Total 50M
```

となれば成功とみなせます。

FP16 Denseが、

```text id="h81ami"
FP16 Dense
Accuracy 83%
Active 20M
```

なら、

```text id="0zbk3f"
FP16       83%
STAR-Bit   82%
BitNet     76%
```

です。

これは、

$$
\text{precision loss}
$$

のかなりの部分を、

$$
\text{structural freedom}
$$

で取り戻したことを意味します。

さらに、

```text id="kila3l"
FP16 Dense       83%
STAR-Bit         85%
```

まで行けば話は変わります。

$$
\boxed{
\text{構造自由度が数値自由度を補っただけではなく上回った}
}
$$

可能性が出てきます。この段階なら独立した研究テーマとして十分強くなります。

最終的には、自由度そのものを予算として考えるのも面白いです。

$$
D_{\mathrm{total}}
=
D_W+D_T+D_R+D_M
$$

と置き、

* \(D_W\): Weight freedom
* \(D_T\): Topology freedom
* \(D_R\): Routing freedom
* \(D_M\): Memory freedom

とします。

通常Transformerは概念的には、

```text id="thwtc1"
DW ████████████████████
DT █
DR █
DM █
```

に近い。

今回の提案では、

```text id="nqqgn7"
DW ███
DT ██████
DR █████
DM ██████
```

のように配分を変えます。

この「自由度の再配分」こそが研究の中心です。

実験コストを最小にするなら、実際に最初に作るべきなのはPhase 0〜2だけです。

$$
\boxed{
\text{FP16 Dense}
\quad vs\quad
\text{Ternary Dense}
\quad vs\quad
\text{Ternary Dynamic-Topology}
}
$$

この3つを同じactive parameter budgetで比較すれば、「低ビット化で削った数値自由度を構造自由度へ移せるか」という核心を、追加GPU購入なし・巨大データセットなし・DLGN実装なしでかなり検証できます。

そこで有意差が出てからDLGNへ進むのが最も低コストです。

なお、スパースルーティングそのものが自動的に能力向上を保証するわけではありません。負荷の偏りやルーティング不安定性は既知の問題なので、Expert utilizationとPath diversityは必須指標にします。([jmlr.org](https://www.jmlr.org/beta/papers/v23/21-0998.html?utm_source=chatgpt.com))
