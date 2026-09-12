import json
from pathlib import Path

def main():
    root=Path(__file__).resolve().parent
    r=json.loads((root/'run/results.json').read_text())
    lines=['# E006：2入力出力ゲートと4入力LUT', '', '実行日：2026-09-11。', '',
           '**4入力LUTで加算の平均test精度は上がったが、補正後の有意差は確認できなかった。選択タスクでは訓練精度の向上がtest改善につながらなかった。** 出力容量だけで汎化の課題を解決したとは言えない。', '',
           'English: Four-input LUTs increased mean numeric test accuracy, but no comparison survived multiplicity correction. On selection, the large training improvement did not transfer to test accuracy.', '',
           '简体中文：四输入LUT提高了数值任务的平均测试精度，但多重比较校正后没有显著差异。选择任务中训练精度明显提高，却未带来测试精度改善。', '',
           '## 比較設計', '',
           '- 16seed400–415×2問題族×3条件＝96run。6入力、隠れ32→32、出力4、固定coverage配線。',
           '- gate2：従来の16関数混合による2入力ゲート。lut2：同じ2入力から4項の真理値表をsigmoidで学習。lut4：元の2入力を保持し、直前段から別の2入力を追加して16項を学習。',
           '- 全条件で隠れ部の初期重みと配線が一致する。lut2はgate2の初期soft真理値表から初期化し、lut4は追加入力の値によらないよう表を複製。全64入力で初期soft出力一致を検査した。',
           '- lut2対lut4でパラメータ化の系統を揃える。ただし表容量と学習パラメータ数が異なる。gate2対lut4は学習パラメータ数が同じだが、パラメータ化と入力数が異なる。どちらも完全に同じ資源条件ではない。',
           '- numeric＝3bit整数2個の4bit和。selection＝2bit制御の4bit循環シフト。E004/E005と同じ64入力、固定32train／32test。既知問題・既知splitに対する探索であり、独立testによる確認ではない。',
           '- NumPy、CPU一thread、full batch32、Adam0.03、400step、温度1。最終checkpointのみ。testによる選択やseed追加はしない。',
           '- 単体論理ゲート網でRouter/Expertはなく、元のMoE負荷分散・固定経路・交換実験の代用ではない。', '',
           '## 資源条件', '',
           '| 条件 | 学習実数logits | hard真理値表bits（隠れ込み） | 最終段接続本数 |',
           '| --- | ---: | ---: | ---: |',
           '| gate2 | 1088 | 272 | 8 |',
           '| lut2 | 1040 | 272 | 8 |',
           '| lut4 | 1088 | 320 | 16 |', '',
           '4入力化で出力表は4倍、全体の表bitsは約17.6%増える。配線アドレス、命令、状態、実回路面積、soft学習時の計算費用はこの表に含まれない。LUT1個を2入力ゲート1個と同じ面積とは数えない。', '',
           '## 精度', '',
           '4bit全体のExact match、0〜1。各行16seed、不偏分散、seed percentile bootstrap 10,000回の点ごとの95% CI。', '',
           '| 問題族 | 条件 | soft test平均 | hard test平均 | hard分散 | hard 95% CI | soft train平均 | hard train平均 |',
           '| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |']
    for a in r['aggregates']:
        m=a['metrics'];d=m['hard_test_exact']
        lines.append(f"| {a['task']} | {a['condition']} | {m['soft_test_exact']['mean']:.6f} | {d['mean']:.6f} | {d['variance']:.6f} | [{d['ci95'][0]:.6f}, {d['ci95'][1]:.6f}] | {m['soft_train_exact']['mean']:.6f} | {m['hard_train_exact']['mean']:.6f} |")
    lines+=['', '## 事前指定した対応比較', '',
            '差＝lut4−baselineのhard test exact-match。interaction＝(lut4−lut2)_selection−(lut4−lut2)_numeric。全65,536符号の両側検定、計5比較Holm補正。', '',
            '| 問題族 | baseline | 平均差 | 差の分散 | 95% CI | 生p | Holm p |',
            '| --- | --- | ---: | ---: | --- | ---: | ---: |']
    for a in r['contrasts']:
        lines.append(f"| {a['task']} | {a['baseline']} | {a['mean']:.6f} | {a['variance']:.6f} | [{a['ci95'][0]:.6f}, {a['ci95'][1]:.6f}] | {a['p_signflip_two_sided']:.6f} | {a['p_holm']:.6f} |")
    lines+=['', '加算はlut2比+9.9609 points、gate2比+8.7891 pointsだが、いずれもHolm p=0.103149。点ごとのCIや生pだけを選んで有意な改善と報告しない。タスク交互作用も有意ではない。', '',
            '## 解釈', '',
            '加算のlut4 hard test精度は27.15%で、依然低い。選択はlut4のsoft train精度69.34%に対しsoft test15.43%。訓練集合への適合が大きく改善してもtest改善にはつながらないという結果で、容量追加だけでは不足している。', '',
            'soft/hard両方でこの隔たりがあるため、離散化だけが主因とは考えにくい。ただし少数データ、固定split、配線制約、最適化、問題構造の影響はまだ分離できていない。過学習の単一原因を確定したとはしない。', '',
            '## 検証', '',
            '- 3条件の初期soft出力を全入力で照合。96runすべてで学習後hard推論を、整数インデックスによる独立真理値表評価器と全64入力で照合した。',
            f"- 初期状態の解析勾配と数値差分の最大誤差 {r['verification']['max_gradient_error']:.3g}。学習後checkpointでも各段の非ゼロ勾配を別途検査し、run/additional_checks.jsonに保存。",
            '- 96checkpoint、学習曲線、平均・分散・bit精度、ソースhashと事前設計hashを保存。旧実験は変更していない。',
            f"- NumPy {r['numpy']}、実行記録上の総時間 {r['elapsed_seconds']:.3f}秒。反復benchmarkではない。", '',
            '## 次の改善案', '',
            '同じ固定splitを使い続ける探索から離れ、複数の事前固定splitで結果の安定性を調べる。容量の増加が小さなtrain集合への過度な適合を促していないか、訓練例数の学習曲線と単純な正則化を別実験として設計する。testが小さいため、同じ例を独立サンプル扱いせずsplitとモデルseedの階層性を考慮する。', '',
            'まず全64入力を学習させる診断を別枠で行えば、汎化を要求しない条件でも残る表現・最適化誤差を測れる。ただしそこでの正解率をtest能力とは呼ばない。これを行ってから、重み共有や学習可能配線へ進むのが次の候補。', '',
            '## 再現', '', '```bash', 'python3 results/E006-output-lut/run_experiment.py', 'python3 results/E006-output-lut/verify.py', 'python3 results/E006-output-lut/report.py', '```', '',
            '既存runがある場合、訓練は停止して上書きしない。verify.pyとreport.pyは保存済み測定を検証・集計する。新規訓練は別の実験IDにソースと設計をコピーする。', '',
            '[事前設計](../results/E006-output-lut/PROTOCOL.md)、[生結果](../results/E006-output-lut/run/results.json)。', '']
    content='\n'.join(lines)
    (root/'REPORT.md').write_text(content)
    (root.parents[1]/'docs/STAR-Bit-E006-output-lut.md').write_text(content)

if __name__=='__main__':main()
