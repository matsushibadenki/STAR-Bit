import json
from pathlib import Path


def main():
    r=json.loads(Path('results/E003-global-accept/results.json').read_text())
    lines=['# E003：全体コストによるModule採用', '',
           '2026-09-10。[実行前の設計](RESEARCH-LOG.md)に従い、未使用seed 100–115で128条件を実行した。評価回路の記述量は従来functionalより減少した。ただし回路ソースが与えられるコンパイラ実験であり、学習能力や物理ゲート削減の実証ではない。', '',
           'English: Training-side global cost acceptance reduced held-out circuit description size. This is a compiler result, not evidence of learned reasoning or hardware savings.', '',
           '简体中文：基于训练侧全局成本的模块选择缩短了独立电路的描述。这是编译实验结果，不代表推理学习或硬件资源节省。', '',
           '## 改善内容', '',
           '従来方式は局所頻度で最大8候補を一度に採用する。global_acceptは同じ候補poolの各候補を訓練回路へ実際に適用し、全ライブラリ定義を含む記述量が最も減る1個を採用して繰り返す。改善がなくなれば停止する。全3round。test性能は採用判断に使わない。', '',
           'randomは従来どおり候補順の無作為化で、固定ランダムRouterではない。syntax／functional／randomは前回コードのまま。新方式は複数回候補を試すので同計算量の比較ではない。', '',
           '## 実測値', '',
           '各行16seed。不偏分散、点ごとのt区間。記述は端子・配線bit数を除いた演算symbol数＋定義費用。', '',
           '| 問題族 | 方式 | 評価記述平均 | 分散 | 95% CI | 訓練記述平均 | Module平均 | fit秒平均 | 候補試行平均 |',
           '| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |']
    for a in r['aggregates']:
        m=a['metrics'];d=m['description_symbols']
        lines.append(f"| {a['task']} | {a['condition']} | {d['mean']:.3f} | {d['variance']:.3f} | [{d['ci95'][0]:.3f}, {d['ci95'][1]:.3f}] | {m['train_symbols']['mean']:.3f} | {m['modules']['mean']:.3f} | {m['fit_seconds']['mean']:.4f} | {m['candidate_trials']['mean']:.2f} |")
    lines+=['', 'fit秒は単発のperf_counter測定で、反復・warm-upを揃えた性能benchmarkではない。旧方式の候補試行0は、この新設した全体rewrite試行をしないという意味であり、計算コスト0ではない。', '',
            '## 事前指定した対応比較', '',
            '差＝functional−global_accept。正が記述削減。65,536通りの両側符号反転検定、2比較のHolm補正。', '',
            '| 問題族 | 平均削減 | 差の分散 | 95% CI | Holm p |',
            '| --- | ---: | ---: | --- | ---: |']
    for a in r['contrasts']:
        lines.append(f"| {a['task']} | {a['mean']:.4f} | {a['variance']:.4f} | [{a['ci95'][0]:.4f}, {a['ci95'][1]:.4f}] | {a['p_holm']:.8f} |")
    lines+=['', 'この生成器に対する主比較は補正後有意。ただし加算の全seedで差8が一致しており、変数名の変更等が同じ構造を繰り返している。この退化した分散やp値を、広い数値タスクへの独立した証拠と解釈しない。選択でも問題族は一種類である。', '',
            '## 正確性と限界', '',
            '- 全128条件で11入力の全2,048通りについて、元回路・Module実行・primitive再展開の出力一致を検査した。',
            '- global_acceptの訓練記述量は各roundで非増加。これは採用規則が保証する性質で、未知問題への汎化の証拠ではない。',
            '- 元／再展開DAGゲート数は生結果に保存。記述を短くすることと、展開された回路の演算数を減らすことを分ける。',
            '- 評価回路ソースもrewrite時には利用する。入出力例だけから未知機能を獲得する実験ではない。',
            '- 実行時間と候補試行が増える。次は同じ探索時間での比較と、端子・アドレスを含むbit単位コストが必要。', '',
            '## 次の改善案', '',
            '最も近い次段階は、学習済みの小型DLGN hard回路に抽出器を接続し、soft→hard→圧縮後の精度を測ること。コンパイラだけの改善を繰り返すより、学習によって得た回路にも効果があるかを確認する。', '',
            '同時に、候補poolを作る際の局所頻度フィルタが有効な候補を落としていないか、候補の重なりを含む探索予算一定の比較を後続案として残す。', '',
            '## 再現', '', '```bash', 'python3 experiments/global_accept.py', 'python3 experiments/report_global_accept.py', '```', '',
            '実験スクリプトは結果フォルダが既存の場合に停止し、過去結果を上書きしない。既存結果のレポート再生成は2行目のみ。再実験は実験IDと保存先を明示的に分ける。', '',
            '[生データ・ソースhash](../results/E003-global-accept/results.json)。設定：16seed、2問題族、4条件、3round、各round最大8候補。', '']
    Path('docs/STAR-Bit-E003-global-accept.md').write_text('\n'.join(lines))


if __name__=='__main__':main()
