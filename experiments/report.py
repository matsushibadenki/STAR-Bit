"""Render the pilot's saved measurements without re-running training."""
import json
from pathlib import Path

import numpy as np

from pilot import summary


def main():
    r = json.loads(Path('results/pilot/results.json').read_text())
    lines = ['# STAR-Bit CPU予備実験：実測結果', '',
             'この結果は小型MLPの探索的検証であり、BitNet/Transformerや動的接続の実証ではない。', '',
             '選択タスクでは学習Routerが固定ランダムRouterより低い誤差を示した。一方、精密回帰のIDでは改善しなかった。選択タスクでもtotalを合わせたWide Denseが平均では学習MoEを上回った。したがって「構造が数値精度を補償した」とはまだ言えない。', '',
             'English: Learned routing reduced error versus fixed random routing on the selection proxy, but not on in-distribution precision regression. No comparison survived Holm correction. This is not evidence of dynamic-topology or LLM gains.', '',
             '简体中文：在选择任务中，学习路由的误差低于固定随机路由，但在分布内精密回归中没有改善。所有比较均未通过Holm校正。本结果不能证明动态拓扑或大语言模型能力提升。', '',
             '## 実行条件', '',
             f"- {r['config']['seeds']}シード（0–7）×6条件×2タスク＝96訓練run。各{r['config']['steps']}更新、batch 128、Adam、学習率0.003。",
             '- 訓練4,096例、ID/OOD各2,048例。splitは固定し、モデル初期値とbatch順序をシードで変更。',
             '- 12次元入力、ReLU、スカラー出力。4 ExpertsからTop-2、各Expert幅16。Dense幅36、Wide幅68。',
             '- 精密回帰：8入力と固定係数の内積。選択：4カテゴリの指定に従って8入力の先頭4要素から1つを返す。カテゴリは両タスクの入力に含める。',
             '- ID値域[-1,1]、OODは絶対値[1,2]。多段経路・言語・未知hopへの外挿は測っていない。',
             '- NMSE = MSE / テスト正解値の母分散。小さいほど良い。ID/OODでは分母も異なる。',
             '- alpha=0.01の負荷分散損失を学習MoEの初回更新から適用。固定Routerでは診断のみ。',
             f"- Python {r['python']} / PyTorch {r['torch']} / CPU / FP32。実行記録上の全所要時間 {r['elapsed_seconds']:.2f}秒（速度比較のbenchmarkではない）。",
             '- STEによる三値weight-only模擬演算。活性化、潜在重み、bias、RouterはFP32。FP16実験、三値kernel、1.58-bit実格納は未実施。',
             '- 最終stepを評価。validationでの選択・ハイパーパラメータ探索・結果を見た再訓練なし。未収束や学習率への感度は未評価。', '',
             '## パラメータ予算', '',
             '| 条件 | 総数 | 入力あたりactive | 学習可能数 | パラメータtensor bytes |',
             '| --- | ---: | ---: | ---: | ---: |']
    for row in r['records'][:6]:
        lines.append(f"| {row['condition']} | {row['total_parameters']} | {row['active_parameters']} | {row['trainable_parameters']} | {row['parameter_bytes']} |")
    lines += ['', 'activeはRouterを含むパラメータ使用数でFLOPsではない。Dense 505対MoE 502、Wide 953対MoE 952という近似一致。FP32実格納bytesはoptimizer/activationを含むpeakメモリではない。固定Routerの52パラメータも総数に含める。', '',
              '## NMSE：平均・分散・95% CI', '',
              '不偏分散（ddof=1）、シード単位のt区間。CIは多重比較補正前の点ごとの区間であり、正規近似の妥当性を保証しない。各行n=8。', '',
              '| タスク | split | 条件 | 平均 | 分散 | 標準偏差 | 95% CI |',
              '| --- | --- | --- | ---: | ---: | ---: | --- |']
    for a in r['aggregates']:
        lines.append(f"| {a['task']} | {a['split']} | {a['condition']} | {a['mean']:.6f} | {a['variance']:.8f} | {a['sd']:.6f} | [{a['ci95'][0]:.6f}, {a['ci95'][1]:.6f}] |")
    lines += ['', '## 対応差と検定', '',
              '差 = baseline NMSE − ternary_learned NMSE。正なら学習MoEが改善。interactionはこの固定経路との差についてselection−precisionを取ったもの。256通りの符号反転、両側p。全18比較を一つのHolm familyとして補正。', '',
              '| タスク | split | baseline | 平均差 | 95% CI | 生p | Holm p |',
              '| --- | --- | --- | ---: | --- | ---: | ---: |']
    for a in r['contrasts']:
        lines.append(f"| {a['task']} | {a['split']} | {a['baseline']} | {a['mean']:.6f} | [{a['ci95'][0]:.6f}, {a['ci95'][1]:.6f}] | {a['p_signflip_two_sided']:.6f} | {a['p_holm']:.6f} |")
    lines += ['', '**Holm補正後に有意な比較はない。** 8シードでは最小両側p=0.0078125なので18比較の最初の閾値0.002778に届かない。生pだけで成功判定しない。「数値タスクには効かない」という同等性の証明にもならない。', '',
              '## Expert交換', '',
              '交換後NMSE − 無交換NMSE。正は悪化。各seedの無交換checkpointから独立に分岐し、再学習なし。同一ランは0/1を交換、別シードは次のseedのExpert 0を移植。集計は記述統計であり、donor共有を無視した有意差検定は行わない。', '',
              '| タスク | split | 介入 | 平均悪化量 | 分散 |',
              '| --- | --- | --- | ---: | ---: |']
    lookup = {(a['task'], a['seed']): a for a in r['records'] if a['condition'] == 'ternary_learned'}
    for task in ('precision', 'selection'):
        for split in ('id', 'ood'):
            for intervention in ('self', 'within_run', 'cross_seed', 'permutation_control'):
                differences = [a['metrics'][split]['nmse']-lookup[task, a['seed']]['metrics'][split]['nmse']
                               for a in r['swaps'] if a['task'] == task and a['intervention'] == intervention]
                a = summary(differences)
                lines.append(f"| {task} | {split} | {intervention} | {a['mean']:.6f} | {a['variance']:.8f} |")
    control = max(a['max_prediction_drift'] for a in r['swaps'] if a['intervention'] in ('self', 'permutation_control'))
    lines += ['', f'自己置換・対応Router置換の最大出力差は {control:.3g}（許容1e-5未満）。交換劣化は依存性を示すだけで、能力の局所移植に成功したとは解釈しない。別シードのExpert番号は機能的に整列していない。', '',
              '## ルーティング診断（ID）', '',
              '| タスク | 条件 | 平均Expert利用率 | 利用率entropy平均 | token entropy平均 | 選択pair数平均 |',
              '| --- | --- | --- | ---: | ---: | ---: |']
    for task in ('precision', 'selection'):
        for cond in ('ternary_learned', 'ternary_fixed', 'fp_learned'):
            a = [row['metrics']['id'] for row in r['records'] if row['task'] == task and row['condition'] == cond]
            usage = np.mean([m['usage'] for m in a], axis=0)
            lines.append(f"| {task} | {cond} | {', '.join(f'{u:.3f}' for u in usage)} | {np.mean([m['usage_entropy'] for m in a]):.4f} | {np.mean([m['token_entropy'] for m in a]):.4f} | {np.mean([m['used_pairs'] for m in a]):.2f} |")
    lines += ['', '利用率は選択slotの割合で総和1、entropyは自然対数で最大ln(4)。異なるseedのExpert番号には同じ意味はないため、平均利用率から専門化を判断しない。個々の利用率・カテゴリ別利用率・MAE・誤差0.01以内率はJSONに保存。pair数は1段Top-2の組合せ数であり、多段path diversityではない。', '',
              '## 解釈と次の検証', '',
              '1. この選択問題では固定ランダム経路より学習経路が有望。ただし連続混合重みも学習しているため、離散経路選択単体の効果ではない。',
              '2. 三値学習MoEは精密回帰IDで三値Denseより平均誤差が大きい。構造の追加が常に有効という説明は支持されない。',
              '3. 選択IDではWide Denseの平均誤差がさらに小さい。学習経路の改善を、容量を増やす代替案より優れたものとはまだ判断できない。',
              '4. 固定データ、2人工問題、単一学習設定、8シードに限定される。独立データ・複数問題族と検出力を確保した本実験が必要。',
              '5. [改訂計画](STAR-Bit-validation.md) に従い、通常MoEと動的接続の差を小型Transformerで検証する。', '',
              '## 再現', '', '```bash', 'python3 experiments/pilot.py --seeds 8 --steps 400 --output results/pilot', 'python3 experiments/report.py', 'python3 -m unittest discover -s experiments -p "test_*.py"', '```', '',
              '必要ライブラリ：torch、numpy、scipy。生データ：[results.json](../results/pilot/results.json)。学習MoEの16 checkpointも同ディレクトリに保存。', '',
              f"実行ソースSHA-256：`{r['source_sha256']}`。", '']
    Path('docs/STAR-Bit-pilot-results.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
