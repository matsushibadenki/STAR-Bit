# STAR-Bit：研究構想

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
