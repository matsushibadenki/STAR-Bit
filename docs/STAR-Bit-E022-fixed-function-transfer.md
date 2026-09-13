# E022：Fixed Learned-Function Transfer

実行日：2026-09-13。E021のexact回路から出力Functionと生入力を除いた内部signatureを費用帯別に16個固定し、新規16 search seedへ移植した。同じ式木形状のLUTと入力だけを無作為化した同費用Library、移植なしを比較した。source seed 1280–1283と評価seed 1300–1315は分離している。

## 主要結果

| condition | exact target平均 | 不偏分散 | parity | comparator | mux | carry | 秒平均 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| no_transfer | 1.6250 | 0.5167 | 7/16 | 1/16 | 16/16 | 2/16 | 13.043 |
| random_matched | 1.8750 | 0.2500 | 12/16 | 1/16 | 16/16 | 1/16 | 12.797 |
| learned_transfer | 2.4375 | 0.5292 | 14/16 | 5/16 | 16/16 | 4/16 | 10.955 |

| learned−random matched | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |
| ---: | ---: | --- | ---: | ---: |
| +0.5625 | 0.6625 | [0.1875, 0.9375] | 0.691 | 0.031250 |

学習Libraryはランダム同費用Libraryより1 seed当たり平均0.5625個多くexact targetへ到達し、bootstrap区間は0を除いた。事前登録した+0.5基準を満たした。no-transferは初回候補数が少なく生成予算も一致しないため、参考値としてのみ扱う。

## タスク別の構造自由度

| task | learned | random matched | learnedのみ成功 | randomのみ成功 | exact McNemar p | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| parity | 14/16 | 12/16 | 4 | 2 | 0.687500 | 1.000000 |
| comparator | 5/16 | 1/16 | 4 | 0 | 0.125000 | 0.500000 |
| mux | 16/16 | 16/16 | 0 | 0 | 1.000000 | 1.000000 |
| carry | 4/16 | 1/16 | 4 | 1 | 0.375000 | 1.000000 |

comparatorは1/16から5/16、carryは1/16から4/16へ増えた。comparatorのlearnedのみ成功が4 seedで事前基準を満たしたが、4タスクのHolm補正後に有意な個別差はない。parityは12/16から14/16、既に飽和したmuxは両条件16/16だった。したがって今回の構造自由度は、簡単な経路選択muxよりも、多段の精密Boolean構成を要するcomparator/carryで到達可能性を広げる傾向を示した。

learned_transferの39/39 exact解は移植signatureを少なくとも1個含んだ。ランダムLibraryでも15解が移植signatureを使い、comparatorとcarryを各1回発見した。追加枠や固定保持だけでも探索は変わるが、費用を揃えた対応対照より学習Functionが上回った。

## 解釈の境界

事前登録したpromising基準は満たしたため、学習された中間Functionが別search seedの探索到達性を改善する証拠が得られた。これはE020/E021のarchive内昇格から、初めて固定Libraryとしての再利用へ進んだ節目である。

ただしLibraryには評価対象と同じtaskのsource回路から得た部分回路が含まれる。出力signature自体は除外したが、comparator/carryの出力一歩手前に近いtask固有Functionを含み得る。今回示したのは同一タスク・別seedのsource-informed transferであり、別タスクへ使えるConcept、自然発生的なtask-independent Module、計算量削減の証明ではない。ランダムLibraryはseedごとに異なるため、単一の対照生成分布に対する結果でもある。

## Roadmap

- [Done] sourceと評価seedを分離し、出力を除いた16 learned Functionsを固定Libraryとして移植した。
- [Done] 同じprimitive・routing・depthと式木形状を持つ固定random Libraryを対照にした。
- [Done] 16 seedで平均・不偏分散・bootstrap CI・効果量・exact検定・Holm補正を報告し、保存した95 exact解を全64入力で再検証した。
- [Done] learned−random exact target差+0.5625、95% CIが0を除き、comparatorのlearnedのみ成功4 seedという事前基準を満たした。
- [Done] E023でtarget task由来Functionを除くleave-one-task-out移植と、truth-table errorを揃える対照を実施した。task横断優位性は確認できなかった。
- [Next] 同一Libraryを複数random control Libraryと比較し、Library抽選の分散をモデルseedの分散から分離する。
- [Next] 未知probe taskへのoffspring寄与とsignature多様性からcross-task Moduleを選定する。
- [Later] task横断transferが再現した後にLibrary記述bit、物理primitive、active演算、Router・State費用を含む総費用でSTAR-Bit本体へ統合する。

English: A fixed 16-Function Library learned from separate source seeds improved exact target discovery by +0.5625 over shape- and cost-matched random Functions across 16 evaluation seeds. The preregistered pilot criterion was met, especially through comparator/carry reachability, but same-task source subcircuits were allowed; task-independent conceptual transfer remains untested.

简体中文：在16个独立评估种子中，来自分离源种子的16个固定学习函数，相比形状与成本匹配的随机函数，使精确目标发现平均提高+0.5625，并满足预注册pilot标准。提升主要来自comparator/carry，但源库允许同任务子电路，因此尚未证明任务无关的概念迁移。

[事前計画](../results/E022-fixed-function-transfer/PROTOCOL.md) / [生データ](../results/E022-fixed-function-transfer/run/results.json) / [Library](../results/E022-fixed-function-transfer/run/learned_library.json) / [監査要約](../results/E022-fixed-function-transfer/run/audit_summary.json)
