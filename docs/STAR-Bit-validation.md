# STAR-Bit：研究テーマの検証と改訂実験計画

検証日：2026-09-09。対象は `docs/STAR-Bit.md`（指定された `doc/` は存在しない）。

## 判定

**検証可能な研究仮説として成立する。ただし「低ビット化で失う能力を構造で回復できる」「通常MoEを超える新規性がある」は、現時点では未証明。** 原案の76%、82%、83%、85%は説明用の仮定値であり、実測値ではない。

本リポジトリには当初、構想文書だけが存在した。今回追加したCPU予備実験は、小さなMLPで三値重み・疎なExpert選択・タスク種別差を検査する。Transformer、言語理解、多段の動的接続、BitNet b1.58全仕様、DLGN、Memoryの検証ではない。実測結果は [予備実験レポート](STAR-Bit-pilot-results.md) に分離する。

English: The hypothesis is testable, but neither precision-loss recovery nor novelty beyond ordinary MoE is established. The CPU pilot tests small MLP routing mechanisms, not Transformer language ability or dynamic topology.

简体中文：该假设可以实验检验，但尚未证明结构能够补偿低比特精度损失，也未证明其超越普通MoE的创新性。CPU预实验仅检验小型MLP的路由机制，不代表Transformer语言能力或动态拓扑验证。

## 1. 一次資料による点検

| 原案の主張 | 判定と修正 |
| --- | --- |
| 三値化すれば必ず精度が落ちる | 前提にしない。BitNet b1.58は一定条件で同規模の高精度モデルに匹敵すると報告している。まずA−Bを測る。[BitNet b1.58](https://arxiv.org/html/2402.17764v1) |
| `round/clip(W)` だけでBitNetを検証できる | 重みスケール、STE、正規化、活性化精度を明記する。今回のweight-only三値MLPはBitNet再現と呼ばない。同論文参照。 |
| Expert選択そのものが新しい構造表現 | 通常MoEも入力依存の条件付き計算を行う。Phase 1はMoEベースラインであり、新規性の証明ではない。[Switch Transformers](https://jmlr.org/papers/v23/21-0998.html) |
| 学習Routerが有利 | 自明ではない。学習不要のハッシュ経路にも競争力が報告されている。[Hash Layers](https://arxiv.org/abs/2106.04426) |
| 可変経路を導入すれば独自性がある | 深さ方向の計算配分にも先行研究がある。接続先・順序の学習という具体的な差分と対照群が必要。[Mixture-of-Depths](https://arxiv.org/abs/2404.02258) |
| DLGNにAND等を渡せば推移律を扱える | 論理ゲートの学習法は存在するが、関係の符号化・変数束縛・反復計算・未知長への汎化は別の設計問題。[DLGN](https://arxiv.org/abs/2210.08277) |
| 別モデルのExpert交換で局所知識を判定できる | 表現座標・Expert番号は別シードで揃うとは限らない。交換失敗は非局所性の証明にならない。置換対称性はモデル整列研究でも扱われる。[Git Re-Basin](https://arxiv.org/abs/2209.04836) |

上記は代表的な先行研究との照合であり、新規性の網羅的調査ではない。

`16P4 = 43,680` は算術的に正しい。ただし、利用可能経路数は有効な表現容量や汎化能力の下限を与えない。Routerも重みを持ち、経路は入力と学習済み重みから決まるため、「知識が重みから離れた」とは結論できない。`D_W + D_T + D_R + D_M` は現状、単位・独立性・測定法が未定義の概念図として扱う。

同じactive parameter数も同じFLOPs・遅延を意味しない。再利用したExpertを複数回通ればユニークパラメータ数は同じでも計算が増える。Router、dispatch、共有Attention、KV cache、embedding、出力層も計測対象にする。Routerが1〜2%、全体の98%が三値という比率は実装後に実数で確認する。

## 2. 反証可能な仮説と対照群

高いほど良いスコアをSとし、主仮説を分離する。

- H1：三値学習MoEが三値固定ランダムMoEを上回る（学習されたルーティング方式の総効果）。
- H2：その改善量はタスク種別によって異なる（モデル方式×タスク種別の交互作用）。
- H3：同じ計算予算で、三値学習MoEが三値Denseの不足分を回復する。
- H4：動的接続が、通常の学習MoEを上回る。これはPhase 2で初めて検証する。

| ID | 条件 | 主な役割 |
| --- | --- | --- |
| A | 高精度Dense | 精度低下が存在するか |
| B | 三値Dense・active予算合わせ | 疎な容量拡張との比較 |
| C | 三値Wide Dense・total予算合わせ | 総容量の交絡を点検 |
| D | 三値・学習Top-k MoE | 通常MoEによる改善 |
| E | 三値・固定ランダムTop-k MoE | 学習経路の対照 |
| F | 高精度・学習Top-k MoE | 低精度固有の効果か、一般的MoE効果か |
| G | 三値・動的接続 | 接続先／順序を変える追加効果 |
| H | 三値・固定ランダム接続 | Gと同じ許可グラフ、同じ実行回数の対照 |

Phase 0–1はA–F、Phase 2はD–Hを含める。G−Bだけで動的接続が効いたと判定しない。予算は「total合わせ」「active合わせ」を別の比較表にし、さらに実測FLOPs・メモリ・時間でPareto比較する。同時に全予算が一致するかのように書かない。

量子化による不足 `S_A−S_B` が正の場合だけ、回復率 `(S_D−S_B)/(S_A−S_B)` を補助指標として報告する。分母が小さい場合は不安定なので差分とCIを優先する。低精度固有の利点は `(S_D−S_B)−(S_F−S_A)` も評価する。

## 3. 複数シードと統計

各条件で同じシード集合、訓練例、例の順序、データ量、更新回数、評価例、checkpoint選択規則を使う。互換部分の初期値も可能な限り対応させる。データ生成、初期化、batch順序、固定経路は独立した乱数系列にする。予備実験では固定データに対するモデル・batch乱数の変動を測り、データ生成の不確実性は含めない。

本実験はまず独立pilotで分散・実行時間を推定し、最小検出差と検出力に基づいてシード数を事前固定する。目安は10〜20以上だが、数だけで十分とはしない。成功するまでシードを追加しない。失敗・NaN・崩壊runを除外せず件数と規則を記録する。

各タスク・ID/OOD別に `n、平均、不偏分散、標準偏差、95% CI` を記載する。差はシード単位の対応差とCIで報告する。テストの何千例を独立した訓練runとして数えない。シードとデータセットの両方を変える場合は階層bootstrap等で依存性を扱う。

主検定はD−Eおよびタスク種別との交互作用を事前指定する。対応のあるt検定なら差の分布仮定を確認し、小規模pilotでは差の符号反転による両側検定を補助的に使う（帰無下で符号が交換可能という仮定がある）。複数の主比較にはHolm補正を行う。CIは点ごとのものか同時CIかを明示する。

今回のpilotは8シード、18比較を一つのHolm familyとした探索的分析。符号反転検定の最小両側pは `2/2^8 = 0.0078125` なので、最小pが最初の閾値 `0.05/18` を下回れず、補正後有意にはなり得ない。したがって効果量・ばらつき・次回の設計に使い、本検証成功とは扱わない。

「有意差なし」は「効かない」の証明ではない。本実験で効かないと主張するなら、実用上の同等性幅（例：Accuracy ±1 percentage point、タスク固有の許容誤差）を事前に定め、同等性検定またはCI全体が幅内に収まることを求める。

## 4. Load-balancing補助損失を初回更新から適用

各routing段階で、paddingを除くT個のtoken、E個のExpert、重複なしTop-k集合K(x)に対し、

\[
p_i(x)=\operatorname{softmax}(r(x))_i,\quad
f_i=\frac{1}{Tk}\sum_x\mathbf{1}[i\in K(x)],\quad
P_i=\frac{1}{T}\sum_xp_i(x)
\]

\[
L=L_{task}+\alpha\frac{1}{L_r}\sum_{\ell=1}^{L_r}
E\sum_i\operatorname{stopgrad}(f_{\ell i})P_{\ell i}.
\]

`alpha=0.01` を初期値とし、全学習Routerでstep 0から有効にする。Top-kでfの和が1になる正規化を明示する。この形は [Megatron CoreのTop-k実装説明](https://docs.nvidia.com/megatron-core/developer-guide/latest/apidocs/core/core.transformer.moe.moe_utils.html) と整合する。係数を探索する場合はvalidationだけで同じ探索予算を使い、testを見て選ばない。

硬い選択fに微分は流さずsoftmax確率Pに流す。固定経路群では補助損失を診断値として記録し、学習不能なRouterに改善効果があるようには扱わない。Denseには付けない。D−Eは負荷分散を含む学習方式全体の差である。経路学習単体と正則化の差をさらに分離するには、追加の係数アブレーションが必要。

平均利用率、未使用Expert、負荷のCV、soft確率のentropy、硬い選択頻度のentropy、経路数、タスク条件付き利用率、drop率を区別する。利用率のentropyが高いだけでは専門化の証拠にならない。最初はdroplessを使い、capacity制限を入れる場合は全群の制限を揃える。

## 5. 固定ランダムルーティングの定義

毎step抽選する経路ではなく、入力から同じ経路を再現する、seedで固定した写像を使う。ラベル、正解、train/test区分を写像に入れない。D/EのExpert数、Top-k、形状、初期重み、訓練例、更新回数、dispatch方式を揃える。

pilotは生入力への固定ランダム線形射影からTop-2を選ぶ。D/Eとも選択softmax重みを再正規化して合成する。これは経路選択と合成重みをまとめた学習効果であり、選択そのものだけの効果ではない。追加実験では両者とも1/k合成にする群を設ける。

Transformerの隠れ状態に単に固定Routerを置くと、上流が学習して経路が変わる。完全な固定経路の対照には入力token等の不変特徴のハッシュを使う。別途、凍結ランダムRouterを置く群は「Router重み非学習」と呼び分ける。固定ハッシュの負荷偏りがDの優位を作らないか、訓練データだけで構成したbalanced hash群でも確認する。

## 6. Expert交換の順序と解釈

「同一ラン」と「別シード」は別条件として実施する。交換時は共有部、Router、残りのExpertを固定し、まず再学習なしで測る。

1. 自己置換：同じExpertを書き戻し、出力が保存されることを確認。
2. 同一ラン内：同じ段のExpert 0/1を交換する。Routerを固定した影響を測る。
3. 置換対称性対照：Expert 0/1とRouterの対応行を同時に交換する。出力が保存されるべきで、壊れれば実装不良。
4. 別シード：同じ設計・データ・訓練予算のモデルから同じ段のExpertを1個移植。
5. 本実験ではtrain/validationのみで機能をマッチングした別シードExpertも試す。testで都合のよいdonorを選ばない。
6. 別アーキテクチャや別データの移植、交換後のRouterのみの再適応は後段の別実験。

pilotの移植先はExpert 0、donorは次のseed（循環）で事前固定し、番号一致を機能一致とはみなさない。同一ラン交換も複数Expertや複数位置への一般化は未検証。donorを循環利用するため交換差を独立標本と仮定した有意差検定はしない。

タスク別・カテゴリ別の性能差と非対象能力の保持率を本実験の主要指標とする。交換で成績が落ちることはモジュール依存性を示すが、「特定知識だけが局所化した」という証明ではない。無交換、ランダム再初期化、ゼロ化の対照も追加する。

## 7. タスク種別を明示した分析

| 軸 | 精密数値 | 経路選択／関係処理 |
| --- | --- | --- |
| pilot | 固定した不均一係数による連続線形回帰 | カテゴリで指定された入力要素を選択するmultiplexer |
| 本実験 | 桁数制御した演算、近接値比較、許容誤差付き回帰 | 分岐規則、到達可能性、多段pointer chasing |
| ID | 学習と同じ数値幅、別の例 | 2–3 hop、未知のグラフ |
| OOD | 桁数・小数精度・値域を独立に変更 | 4/5/6 hopを個別集計、分岐数・未知構成 |
| 指標 | Exact match、MAE、相対誤差、閾値内率 | Accuracy、hop別Accuracy、経路別失敗率 |

pilotのselectionは1段の選択であり、グラフ探索ではない。数値回帰は厳密な筆算やLLMの数値処理ではない。両pilotのOODは値域外であってhop外挿ではない。

本実験ではタスク種別ごとに複数の独立した問題族を用意する。長さ、訓練例数、ラベル分布、出力形式、難易度を揃え、テンプレート暗記や解答語彙からの漏洩を防ぐ。グラフは同型・名前変更を含めたsplitを検討し、trainの部分問題がtestの正解を直接露出しないようにする。論理合成では未学習演算そのものと未学習の組合せを区別する。

`(D−E)_selection − (D−E)_precision` とCIを報告し、一方だけ有意だったことを交互作用の証明にしない。異なるスコア尺度の差を直接引かない。pilotは共通のNMSEで探索的に比較するが、二つの人工問題だけから「タスク種別一般」に外挿しない。

言語化した本実験はEnglish・日本語・简体中文を同じ意味構造から生成し、言語別にも集計する。pilotは言語に依存しない数値tensorのみを扱う。

## 8. 実装・計算予算上の注意

訓練時の潜在重み、勾配、optimizer stateは高精度のまま保持する。三値模擬matmulのtensorもFP32/FP16であり、理論上の1.58 bits/weightを実メモリと記載しない。bias、scale、Routerなどの非三値部分を加算する。

MacBook Air M4/32GBで10–30Mモデルが収まるかと、全条件×複数シードを実用時間で訓練できるかは別問題。今回のPython環境ではPyTorch 2.10.0、MPS利用不可でCPUを使用。小規模測定から見積もり、本実験では精度型、batch、context、時間上限を記録する。CPUのFP32対照をFP16と表記しない。

本実験の保存物は設定、source hash、ライブラリ版、全シードの生指標、学習曲線、checkpoint、データ生成seed/hash、集計コードとする。遅延はwarm-up後の反復と同期を行い、中央値・分位点を報告する。Perplexityは言語モデルでのみ計測し、回帰誤差から作らない。

## 9. Roadmap

- [Done] 一次資料との照合、仮説・交絡・成功条件をこの文書に整理。
- [Done] CPU予備実験に三値STE、初回からのload-balancing、固定ランダム経路、複数seed、二つのタスク族、Expert交換対照を実装。
- [Next] 予備実験の分散を用いて検出力と本実験のシード数・主要比較を事前固定。
- [Next] 小型TransformerのA–F、BitNet仕様、言語別・hop別評価、実測計算予算合わせを実装・実行。
- [Next] 固定balanced hash、均等合成、複数問題族、機能整列したExpert移植を追加。
- [Later] 通常MoEとの差を固定したG/Hの動的接続検証。
- [Later] 再現性のある効果が確認された段階でDLGN、Memory、SNNを個別追加。

Phase 2へ進む条件は、事前指定した比較で実用的な効果と不確実性を確認し、容量増加・負荷偏り・訓練量の説明を排除できること。有意差だけを進行条件にせず、負の結果も研究成果として残す。

## 10. 追加参考：論理ゲートAIをどう位置づけるか

ユーザー指定の [手羽先氏の記事「2026年は論理ゲート式ニューラルネットワークが爆発的に進化する」](https://zenn.dev/teba_eleven/articles/68955053ed75be)（2025-12-31公開、2026-01-02更新）を参考資料に追加した。発展予測は仮説として扱い、技術的な根拠は記事が参照する一次資料と照合する。

**STAR-BitのLogic Expertは、手書きの論理規則を実行する部品に限定しない。学習可能な論理回路による表現学習・系列処理の候補として扱う。** 原案の「BitNet＝意味、DLGN＝比較・条件」という分担は実験上の出発点であり、論理ゲートNNの能力上限ではない。また、先の三値MLP実験には論理ゲートが含まれないため、その結果からDLGNの有効性を否定も肯定もできない。

### 一次資料から確認できる範囲

| 系統 | 確認した内容 | STAR-Bitへの示唆 |
| --- | --- | --- |
| DDLGN / 本文でのDLGN | 連続緩和でゲート選択を学び、離散回路へ変換する。[原論文](https://arxiv.org/abs/2210.08277) | 三値重みの量子化とは別の学習・実行方式として比較する。 |
| Convolutional DLGN | 論理ゲート木による畳み込み、OR pooling、残差的初期化を導入。CIFAR-10で86.29%を報告。[原論文](https://arxiv.org/abs/2411.04732) | 構造により帰納バイアスを与えられる。Boolean表現だから汎化不能とは言えない。ただし画像での結果を言語へ直接外挿しない。 |
| RDDLGN | 再帰的論理ゲートによる系列変換を検証。WMT'14英独翻訳でsoft側BLEU 5.00、離散推論4.39、比較GRU 5.41を報告。[原論文v1](https://arxiv.org/html/2508.06097v1) | 系列処理の可能性を示す一方、一般にGRUやLLMを超えたとの根拠にはしない。離散化による性能差を独立に測る。 |
| Differentiable Logic CA | 論理ゲートを用いた局所更新によるセルオートマトンを扱う。[Google Researchの研究ページ](https://google-research.github.io/self-organising-systems/difflogic-ca/) | 共有された局所規則と反復状態の設計を参考にできる。長い反復での安定性を評価軸にする。 |

記事中のLDDLGN、LUT系、独自学習法については、この照合だけで仕様や優位性を確定しない。採用時に対応論文・公開実装・評価条件を個別に特定する。

### Phase 3の検証仕様を具体化

以下は追加の提案であり、まだ実装・実行していない。

1. **学習時と実行時を分ける。** まず固定配線の2入力ゲートを用意し、16種のBoolean関数の連続緩和をsoftmaxで混合して学習する。argmaxで離散化した同じcheckpointを評価し、soft score、hard score、その差を保存する。ゲート種別の学習と配線の学習は別の自由度として扱う。
2. **表現変換の交絡を除く。** 同じ入力符号化・出力復号を持つ三値MLPとLogic Expertを比較する。次に固定符号化と学習可能なbinary adapterを比較し、adapterのパラメータ・精度・計算も予算に含める。前段に正解の推論結果を与えない。
3. **単体評価から混合へ進む。** Logic Expert単体、同じadapter付き三値Expert、BitNet＋Logic Expertの固定混合、学習混合を順に比較する。全群を同じデータ・複数seedで評価し、学習Routerには初回から負荷分散損失を付ける。ゲート離散化用の正則化はRouterの負荷分散損失と区別する。
4. **構造の効果を分離する。** 固定ランダム配線を基準とし、接続学習、重み共有、再帰状態を一つずつ追加する。再帰なしの同計算量対照を含め、反復回数増加そのものによる改善と区別する。
5. **二つのタスク軸を維持する。** 数値側では入力bit数、固定小数点精度、carry長、誤差許容幅を変更する。選択側ではmultiplexerからpointer chasing・到達可能性へ進み、訓練外hopと反復長を測る。論理ゲートなら精密演算が不得意とも、関係推論が得意とも事前に断定しない。
6. **交換対照を継承する。** 同一ラン内、同設計の別seedの順でLogic Expertも交換する。soft/hardの両方で測り、配線、入出力の符号規約、状態初期化が一致する条件を記録する。機能整列にはtestを使わない。

### 推論効率の判定

「1層を1クロックで処理できる」という実装条件だけではGPUに対する速度倍率は決まらない。STAR-Bitでは回路の深さ・幅、配線、達成クロック、面積、メモリ転送、batch、入出力変換を含めて評価する方針とする。学習時の浮動小数点演算も、離散推論のコストと別に報告する。

最初はCPUのbit-packed推論でhard回路の正確性とend-to-end遅延を測る。FPGAに進む場合は合成見積もりと実機測定を区別し、LUT/FF/BRAM使用量、達成周波数、latency、throughput、消費電力と精度を併記する。Logic Expert単体の高速化と、BitNetやadapterを含むシステム全体の高速化を分ける。

English: Logic-gate networks are trainable representation models, not only hand-written rule engines. Planned evaluation separates encoding, gate learning, wiring, recurrence, discretization loss, and measured end-to-end efficiency.

简体中文：逻辑门网络是可训练的表征模型，不仅是手写规则引擎。后续实验将分别检验编码、门类型学习、连接结构、递归状态、离散化损失及端到端实测效率。

## 11. 2026-09-10追記：回路規模の増大と自律的モジュール化

ユーザー提示の会話を、研究の追加仮説として取り入れる。中心は「ゲートの空間展開を、時間再利用・条件付き実行・状態・記憶へ配分すること」と「意味を事前指定しないモジュールの形成・再利用・分解」である。

今回実装した範囲と実測値は [Logic PE・モジュール発見の結果](STAR-Bit-logic-modules-results.md) に記録した。16seed×2問題族×3方式で検証したが、**学習済みDLGNからの抽出ではなく、与えられた回路ソースのコンパイル実験**である。2026-09-09の三値MLP実験と混同しない。

### 研究上の修正

任意のBoolean関数は巨大な表現を要し得るが、「複雑な処理なら必ず指数的にゲート数が増える」とは限らない。加算のように規則的な構造を持つ関数と、構造の乏しい真理値表を分ける。G・T・R・M・Sの倍率を掛けた値を能力倍率とみなす理論的根拠も、現状はない。

同じ入力を使う共通部分式はDAG共有で計算を省ける。一方、異なる入力に同じ関数を適用する場合は、定義共有だけでは計算を省けず、時間多重化や複数回実行が必要になる。全ゲート数、1cycleの同時稼働数、推論全体のゲート演算回数、PE数、state bits、configuration bitsを別々に記録する。

モジュール発見・ライブラリ拡張には [DreamCoderの著者資料](https://people.csail.mit.edu/asolar/papers/EllisWNSMHCST21.pdf)、構造共有・小入力回路の真理値表に基づく最適化には [ABCの公式資料](https://people.eecs.berkeley.edu/~alanmi/abc/abc.htm) という先行研究がある。この方向全体を新規発明とは扱わず、低ビット／論理回路の学習とオンラインの形成・再利用・分解をどう統合し、何が改善するかに研究差分を置く。今回のコードはこれらの再現実装ではない。

### アイデア別の実験対応

| 会話のアイデア | 今回の状態／次の対照 |
| --- | --- |
| 名前を与えない中間モジュール | [Done] primitiveからM000等を生成、Moduleを含むModuleも抽出。回路ソースからの発見であり、概念理解は未検証。 |
| 機能の一致による統合 | [Done] 最大4入力の全真理値表で一致を確認。構造一致・random候補順との比較で優位性なし。 |
| 16〜64 Logic PE＋State | [Done] primitiveを16/32/64 PEへ時分割し、全入力で状態更新後の出力を検査。物理実装は未実施。 |
| 共通部分式・DAG共有 | [Done] 同じ演算・同じ入力を共有したゲート数を基準に採用。モジュール化後の追加削減なし。 |
| LUT化 | [Done] 小入力Moduleを真理値表で実行しprimitive展開と照合。LUT/ゲートの面積換算や学習可能LUTは未実施。 |
| 不要モジュールの分解 | [Done] inliningと未使用定義除去の機能を検証。利用率から学習する分解・再獲得は未実施。 |
| 条件付き実行・学習Router | [Next] 同じPE／State予算で固定・ランダム・学習経路を比較。初回更新から負荷分散を適用。 |
| F/U/G/C/Kによる採用スコア | [Next] 頻度＋記述節約という今回の代理指標を、独立タスクへの再利用とvalidation改善を含むものへ拡張。 |
| 学習によるゲート削除・近似論理 | [Later] lambda sweepとhard剪定後の精度を比較し、精密数値と経路選択のPareto曲線を分ける。 |
| Boolean–ternary hybrid | [Later] 同じ符号化と予算の純Logic／純ternary対照を入れ、adapterコストも計上。 |
| 中間結果Memory／cache | [Later] 容量・検索費用・miss時の計算を含める。testラベルを保存せず、cold/warmと分布変化を別評価。 |

### 次の段階の成功基準

1. **学習由来の発見**：人工的に用意した完成回路ではなく、訓練例から得たDLGNのhard回路へ同じ抽出器を適用する。ゲート種の学習、配線学習、抽出器の効果を分離する。
2. **機能と意味の区別**：小入力の全真理値表一致は機能同値の証拠になるが、「因果」「概念」の獲得とは呼ばない。分布上の近似一致を使う場合はtrainで候補を作り、validationと独立testで誤差を確認する。
3. **階層の選択**：最大round／最大Module数は安全な計算上限として固定し、各階層を使うかは費用に基づいて選ぶ。固定階層数の同予算対照も置く。
4. **採用スコアのリーク防止**：Gはvalidationでの改善量であり、test性能を候補採用に用いない。F/U/G/C/Kは単位が違うため正規化と係数を事前固定する。頻出だけで大きな候補を選ぶと、重複候補の干渉で悪化し得る。
5. **形成→固定化→分解→再獲得**：タスク分布A→B→Aを事前固定し、維持コスト、忘却、再適応に必要な更新数を比較する。固定ライブラリ、未使用定義除去だけの方式、同数random削除を対照にする。
6. **従来の5条件を維持**：学習実験では全条件複数seed、負荷分散の初期適用、固定ランダム経路、同一ラン内→別seed移植、精密数値対経路選択を引き継ぐ。今回のrandom候補抽出を固定ランダムルーティングの代わりとはしない。

English: The new pilot separates library compression, DAG sharing, and time-multiplexed PEs. Learning modules from trained circuits, adaptive routing, and continual formation/pruning remain the next research stages.

简体中文：新增预实验区分了库描述压缩、DAG计算共享与PE时间复用。训练电路中的模块发现、自适应路由及持续形成／剪枝仍需后续检验。

## 12. 2026-09-21追記：固定Functionのtask-family可搬性

E031では、E027の肯定例が1つのdual-mux XORに偏っていたため、そのtruth tableへの反復を止めた。結果を見る前に経路選択3 taskと精密数値2 taskを定義し、E026の固定Function、移植なし、one-hop barrier、同一費用random Functionを新規8 seedで比較した。[詳細](STAR-Bit-E031-route-family-portability.md)。

routeの採用Function−randomは−0.125 exact task/seed、bootstrap 95% CI [−0.375, 0]で、task-family可搬性は支持されなかった。数値の`unsigned_sum_ge6`では採用0/8に対しbarrier 6/8となり、Functionを後段まで伝播させることが探索を妨げる可能性が出た。ただしHolm補正後p=0.09375であり、3 route task中2つにも床効果があった。

この結果から、次の評価ではtaskを成功率で選別しない生成grammarを先に凍結し、pilotは難度層の定義だけに使い、独立seedを確認用に分離する。さらに、Function条件だけ初期候補が1つ増える交絡を避けるため、no-transfer側にも同数・同費用だがcomposition不能なinert slotを置く。Functionの価値は「直接部品」「一段の探索摂動」「深いdescendant伝播」に分けて測る。

English: E031 did not replicate the earlier dual-mux benefit across three new routing targets. The learned Function trailed equal-cost random controls, while a one-hop barrier unexpectedly helped one numeric target; this is an unconfirmed search-dynamics hypothesis after multiplicity correction.

简体中文：E031未能在三个新路由目标上复现此前的dual-mux收益。学习函数落后于同成本随机对照，而一跳屏障意外改善了一个数值任务；经多重比较校正后，这仍只是关于搜索动力学的未确认假设。
