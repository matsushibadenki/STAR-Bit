# STAR-Bit

低ビット重みを構造・経路の自由度で補えるかを検証する研究用リポジトリ。

- [研究構想](docs/STAR-Bit.md)
- [検証・改訂実験計画](docs/STAR-Bit-validation.md)
- [CPU予備実験の実測結果](docs/STAR-Bit-pilot-results.md)
- [Logic PE・モジュール発見の実測結果](docs/STAR-Bit-logic-modules-results.md)
- [E003：全体コストによるModule採用](docs/STAR-Bit-E003-global-accept.md)
- [E004：学習論理ゲートとhard化](docs/STAR-Bit-E004-learned-logic.md)
- [E005：入力到達性と深さの比較](docs/STAR-Bit-E005-input-coverage.md)
- [E006：2入力ゲートと4入力LUT](docs/STAR-Bit-E006-output-lut.md)
- [E007：全入力学習と最適化予算](docs/STAR-Bit-E007-full-domain.md)
- [E008：固定配線のSAT診断と表現制約](docs/STAR-Bit-E008-fixed-wiring-sat.md)
- [E009：出力bit別の表現制約](docs/STAR-Bit-E009-output-bit-diagnosis.md)
- [E010：出力直前の1接続修正](docs/STAR-Bit-E010-single-rewire.md)
- [E011：出力arityを1増やす](docs/STAR-Bit-E011-output-arity-plus-one.md)
- [E012：出力arityを2増やす](docs/STAR-Bit-E012-output-arity-plus-two.md)
- [E013：隠れノード選択によるボトルネック診断](docs/STAR-Bit-E013-hidden-node-routing.md)
- [E014：State付きLogic PEとschedule選択](docs/STAR-Bit-E014-temporal-logic-pe.md)
- [E015：Logic Expert・schedule・Router共同最適化](docs/STAR-Bit-E015-joint-logic-router.md)
- [E016：独立hashによるnumeric確認](docs/STAR-Bit-E016-independent-hash-replication.md)
- [E017：Learned Circuit Abstraction境界実験](docs/STAR-Bit-E017-learned-circuit-abstraction.md)
- [E018：CEGIS exact circuit形成pilot](docs/STAR-Bit-E018-cegis-mdl.md)
- [E019：Function-space Module Genesis pilot](docs/STAR-Bit-E019-function-space-genesis.md)
- [E020：Learned Archive Promotion pilot](docs/STAR-Bit-E020-learned-archive-promotion.md)
- [E021：Cost-normalized Promotion and Retirement pilot](docs/STAR-Bit-E021-cost-normalized-promotion.md)
- [E022：Fixed Learned-Function Transfer](docs/STAR-Bit-E022-fixed-function-transfer.md)
- [E023：Leave-one-task-out Function Transfer](docs/STAR-Bit-E023-leave-one-task-out-transfer.md)
- [E024：Probe Utility and Function Diversity pilot](docs/STAR-Bit-E024-probe-utility-diversity.md)
- [E025：Usage-gated Module Eviction pilot](docs/STAR-Bit-E025-usage-gated-eviction.md)
- [E026：Counterfactual Module Admission pilot](docs/STAR-Bit-E026-counterfactual-admission.md)
- [E027：Counterfactual Module Admission 独立確認](docs/STAR-Bit-E027-counterfactual-admission-confirmation.md)
- [E028：転移Functionの直接寄与と入力意味のAblation](docs/STAR-Bit-E028-module-causal-ablation.md)
- [E029：Libraryが変えるBeam探索軌跡](docs/STAR-Bit-E029-beam-trajectory.md)
- [Module Genesis Milestone 3](docs/STAR-Bit-milestone-module-genesis.md)
- [Logic Routing Milestone 1](docs/STAR-Bit-milestone-logic-routing.md)
- [Logic Routing Milestone 2](docs/STAR-Bit-milestone-joint-routing.md)
- [継続研究ログと次の実験](docs/RESEARCH-LOG.md)

English: Research on whether routing and structure can compensate for low-bit weights. The current implementation is an exploratory CPU MLP pilot, not a Transformer or full BitNet implementation.

简体中文：研究路由与结构能否补偿低比特权重。当前实现是探索性的CPU MLP预实验，并非Transformer或完整BitNet实现。

## 再現 / Reproduce / 复现

Python 3.10、PyTorch 2.10.0、NumPy 1.25.2、SciPy 1.9.3で実行。CPU、FP32、単一thread。依存関係の導入が必要な環境では `python3 -m pip install -r experiments/requirements.txt` を使う。

```bash
python3 experiments/pilot.py --seeds 8 --steps 400 --output results/pilot
python3 experiments/report.py
python3 -m unittest discover -s experiments -p 'test_*.py'
```

標準実行は96訓練runとExpert交換評価。再実行すると出力先のJSON・checkpoint・レポートを上書きする。別条件は `--output` で別ディレクトリに保存する（レポート生成は標準出力先を読む）。

初期MLP pilotの制約：固定データ・二つの人工問題・8モデルシードで、補正後の有意差なし。後続のLogic Routing実験では16 seed、固定均衡hash対照、開始時からの負荷分散損失、Expert交換、独立追試を追加した。モデルtensorはFP32格納であり、低ビットの実メモリ・速度改善は主張しない。

## 回路モジュール発見（2026-09-10）

```bash
python3 experiments/logic_modules.py
python3 experiments/report_logic_modules.py
```

16シード×2問題族×3抽出方式。全11入力の真理値表で等価性を検査し、16/32/64 PEによる時分割実行も照合する。これは与えられた回路ソースからのライブラリ発見であり、入出力例からのDLGN学習ではない。標準出力先results/logic_modulesは再実行で上書きされる。
