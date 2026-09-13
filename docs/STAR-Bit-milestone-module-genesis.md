# STAR-Bit Milestone 3：Module GenesisとTransferの境界

実行期間：2026-09-12〜2026-09-13。E017〜E023は、primitive論理演算から中間Functionを形成し、Libraryへ昇格・移植できるかを段階的に検証した。

## 到達した結論

| 段階 | 実験 | 結果 | 現在の判定 |
| --- | --- | --- | --- |
| 入出力からhard circuit形成 | E017–E018 | parity/muxは安定、comparator/carryは不安定 | 探索がボトルネック |
| Function-spaceと同値統合 | E019 | 同値mergeだけでは不十分。人手affine保持でparity回復 | 良い中間Function保持が効く |
| 中間Function価値の自動学習 | E020 | target-greedy比+1.25 exact target、comparator初到達 | 肯定的pilot、Library肥大 |
| 費用正規化と退役 | E021 | 台帳−46.9%、時間−5.5%、carry初到達 | 性能維持、最終beam削減基準は未達 |
| 同一task・別seed移植 | E022 | learned−random +0.5625、95% CI [0.1875, 0.9375] | 固定Function再利用を支持 |
| 別taskへの移植 | E023 | learned 27/64、primary random 27/64 | Concept再利用を支持せず |

現在支持される主張は次である。

$$
\boxed{\text{学習した部分Functionは、同一taskの別search seedで探索を助ける}}
$$

現在支持されない主張は次である。

$$
\boxed{\text{別taskでも役立つ再利用可能Conceptが自律形成された}}
$$

E022ではsourceの最終出力signatureを除外し、評価seedも分離した。16 learned Functionsは同じ式木形状・primitive・routing・depthのランダムFunctionよりexact targetを平均+0.5625増やし、comparatorを1/16から5/16、carryを1/16から4/16へ増やした。これは単なるArchive内保持から、固定Library移植へ進んだ肯定的な節目である。

E023ではさらに評価taskと同じsource taskをLibraryから除外した。その結果、learned cross-taskとerror-matched randomはともに27/64となり、cost-matched randomの37/64も下回った。learned条件の27解中、移植Functionを最終回路で使ったのは3解だけだった。E022の改善は汎用Conceptよりtask固有の有用な部分回路に強く依存していた。

## タスク種別による違い

経路選択taskのmuxはE022・E023の全主要条件で16/16に達し、Library差を検出できない。parityは中間affine構造や一部Libraryで改善するが、cross-task条件では不安定だった。comparatorとcarryは同一task transferで改善した一方、leave-one-task-outでは改善しなかった。

この範囲では、構造自由度は飽和した単純経路選択より、多段の精密Boolean構成で探索到達性を変える。ただし必要なのは任意の構造追加ではなく、対象taskに適した中間Functionである。構造自由度だけを増やしても能力は補償されない。

## 次の研究仮説

truth-table error、source内頻度、構造費用のどれか一つではcross-task Moduleを選べなかった。次はFunctionの価値を、選定に使っていないprobe task群で子Functionを改善した因果的寄与として測る。

$$
V(F)=\alpha\,\Delta_{\mathrm{probe}}(F)+\beta\,D(F)-\lambda_p C_{\mathrm{primitive}}-\lambda_r C_{\mathrm{routing}}-\lambda_s C_{\mathrm{state}}
$$

ここで $\Delta_{\mathrm{probe}}$ は複数の未知probe taskでのoffspring改善、$D$ はLibrary内のsignature多様性である。選定後に新しいtask familyを固定し、source選定への過適合を分離する。最終式で使われないFunctionには、beamを変えた間接効果と実際の部品再利用を分けてcreditを与える。

## Roadmap

- [Done] hard circuit形成、Function-space統合、learned promotion、retirementを段階分離した。
- [Done] 同一task・別seed移植を16 seedと同費用random対照で確認した。
- [Done] leave-one-task-out 256探索により、task横断Concept transferが未成立であることを確認した。
- [Done] 平均・不偏分散、bootstrap CI、効果量、exact検定、多重比較補正、全expression再評価を各段階で保存した。
- [Next] 未知probe taskへのoffspring寄与とsignature多様性を使うModule選定を事前登録する。
- [Next] 選定後に生成する新規task familyでcross-family transferを評価する。
- [Later] cross-task再利用成立後、Ternary ExpertとLogic ModuleをRouterへ統合する。step 0からのload-balancing損失、均衡固定random Router、同一run内から別seedへのExpert交換を維持する。
- [Later] Library記述bit、物理primitive、active演算、Router、register、State、latencyを含む総費用で低ビット補償を再判定する。

English: Milestone 3 supports reuse of learned partial Functions across search seeds for the same task, but not autonomous task-independent concepts. Leave-one-task-out transfer removed the E022 advantage. The next bottleneck is learning causal cross-task utility rather than merely storing more Functions.

简体中文：里程碑3支持在同一任务的不同搜索种子之间复用已学习的部分函数，但不支持自主形成任务无关概念。留一任务迁移消除了E022的优势。下一瓶颈是学习跨任务的因果效用，而不是继续增加函数数量。

[E022：同一task・別seed移植](STAR-Bit-E022-fixed-function-transfer.md) / [E023：leave-one-task-out](STAR-Bit-E023-leave-one-task-out-transfer.md) / [研究ログ](RESEARCH-LOG.md)
