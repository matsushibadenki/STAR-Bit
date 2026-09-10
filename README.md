# STAR-Bit

低ビット重みを構造・経路の自由度で補えるかを検証する研究用リポジトリ。

- [研究構想](docs/STAR-Bit.md)
- [検証・改訂実験計画](docs/STAR-Bit-validation.md)
- [CPU予備実験の実測結果](docs/STAR-Bit-pilot-results.md)
- [Logic PE・モジュール発見の実測結果](docs/STAR-Bit-logic-modules-results.md)

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

結果の制約：固定データ・二つの人工問題・8モデルシード。補正後の有意差なし。モデルtensorはFP32格納であり、低ビットの実メモリ・速度改善は主張しない。

## 回路モジュール発見（2026-09-10）

```bash
python3 experiments/logic_modules.py
python3 experiments/report_logic_modules.py
```

16シード×2問題族×3抽出方式。全11入力の真理値表で等価性を検査し、16/32/64 PEによる時分割実行も照合する。これは与えられた回路ソースからのライブラリ発見であり、入出力例からのDLGN学習ではない。標準出力先results/logic_modulesは再実行で上書きされる。
