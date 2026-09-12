import json
from pathlib import Path

def main():
    root=Path(__file__).resolve().parent
    r=json.loads((root/'run/results.json').read_text())
    lines=['# E007：全入力学習と最適化予算の診断', '', '2026-09-11。', '',
           '**訓練例不足だけでは、現在のゲート網に残る誤差を説明できない。** 全64入力を学習し1600step更新しても、階層型lut4の平均hard一致率は加算67.19%、選択45.41%だった。直接LUT6の陽性対照は全32runで100%だった。', '',
           'これは全真理値表への適合診断であり、full64条件の数値をtest精度・未知問題への汎化として扱わない。配線上の表現不能と、勾配学習が解を見つけられないことはまだ分離できていない。', '',
           'English: Errors remained after training on the entire truth table and increasing optimization steps. A direct LUT6 fitted all examples exactly. This diagnoses fitting limits, not held-out generalization; representability and optimization failure remain unresolved.', '',
           '简体中文：使用完整真值表并增加训练步数后，分层网络仍有误差；直接LUT6则完全拟合全部样本。这是拟合能力诊断，不是泛化评估，尚未区分表示限制与优化失败。', '',
           '## 事前設計と条件', '',
           '- seed500–515、2task×2architecture×2data量＝128訓練trajectory。各trajectoryの400/1600stepを観測し、独立runとして重複計上しない。追加の直接LUT6陽性対照32runを含め計160訓練run。',
           '- 主architectureはE006のgate2／lut4。6入力、hidden32→32、出力4、coverage固定配線。同seedのhalf/fullは完全に同じ初期値・配線。',
           '- half32はsplit7001の32例、full64は全64例。numericは3bit整数2個の4bit和、selectionは2bit制御の4bit循環シフト。',
           '- NumPy、CPU一thread、Adam0.03、温度1、full batch、全runを1600stepまで実行。400stepの結果で延長可否を選ばない。',
           '- full64は同更新数のhalf32に対して2倍の例を処理する。1600stepは400stepの4倍の更新数。データ被覆と計算量を完全に独立化した比較ではない。',
           '- 直接LUT6は生6入力をそのままアドレスとする4出力×64表項の256logitを学習。hiddenなし、full64、400step。全表の暗記を許す別設計であり公平なアーキテクチャ優劣の対照ではない。', '',
           '## 全64入力に対する一致率', '',
           'スコア0〜1、4bit全体の一致。各行16seed、不偏分散、seed bootstrap 10,000回の点ごとの95% CI。half条件では学習例と未学習例を混ぜた全領域スコア、full条件では全て学習例である。', '',
           '| task | architecture | 学習例数 | step | soft平均 | hard平均 | hard分散 | hard 95% CI | 全入力hard完全一致run |',
           '| --- | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |']
    for a in r['aggregates']:
        d=a['metrics']['hard_all_exact'];s=a['metrics']['soft_all_exact']
        lines.append(f"| {a['task']} | {a['condition']} | {a['training']} | {a['step']} | {s['mean']:.6f} | {d['mean']:.6f} | {d['variance']:.6f} | [{d['ci95'][0]:.6f}, {d['ci95'][1]:.6f}] | {a['perfect_hard_runs']}/16 |")
    lines+=['', '加算lut4は全入力学習で全例を解けるseedが1個あった。少なくともその配線には正解を実装できる一方、他のseedの固定配線でも可能かはこの結果から分からない。', '',
            '## 未学習例の評価（half32だけ）', '',
            'full64に未学習例は存在しないため、unseen指標をnullとして保存している。次の表だけはhalf32条件の未学習32例の精度。', '',
            '| task | architecture | step | soft unseen平均 | hard unseen平均 | hard unseen分散 |',
            '| --- | --- | ---: | ---: | ---: | ---: |']
    for a in r['aggregates']:
        if a['unseen'] is None:continue
        u=a['unseen'];d=u['hard_unseen_exact']
        lines.append(f"| {a['task']} | {a['condition']} | {a['step']} | {u['soft_unseen_exact']['mean']:.6f} | {d['mean']:.6f} | {d['variance']:.6f} |")
    lines+=['', '## 事前指定の10比較', '',
            '全領域hard exact-matchの対応差。全65,536符号の両側検定、10比較Holm補正。400/1600は同じ訓練trajectoryの対応比較。', '',
            '| task | architecture | 比較 | 平均差 | 差の分散 | 95% CI | Holm p |',
            '| --- | --- | --- | ---: | ---: | --- | ---: |']
    for a in r['contrasts']:
        lines.append(f"| {a['task']} | {a['condition']} | {a['contrast']} | {a['mean']:.6f} | {a['variance']:.6f} | [{a['ci95'][0]:.6f}, {a['ci95'][1]:.6f}] | {a['p_holm']:.6f} |")
    lines+=['', '加算lut4はfull1600−half1600が+17.87 points（Holm p=0.024902）。ただしこれは未学習例を訓練へ含めた全領域適合の改善で、汎化改善ではない。full400→full1600の差はどちらのtask・architectureでも補正後有意でない。4倍の更新数だけでは解決しなかった。', '',
            'full1600ではlut4−gate2が加算+23.44 points、選択+18.95 pointsで補正後有意。ただし容量・接続数が違うため、同ハードウェア費用での優位性とは解釈しない。', '',
            '## 直接LUT6陽性対照', '',
            '2task×16seedの全32runでsoft/hard全領域exact-matchが100%。hard分散0。全入力が既知で、入力ごとに独立した表項を学ぶため暗記を許す対照である。小さい6bit領域では可能だが、入力bit数nに対して各出力の表容量が2^nとなり、大規模問題の解決策とはみなさない。', '',
            'この対照は、データの正解ラベルに整合する学習が可能であることを示す。階層型モデルの固定配線に正解が存在することや、その勾配学習に失敗がないことまで保証しない。', '',
            '## 検証と保存', '',
            '- 主128trajectoryの400/1600両checkpointで全64入力のhard推論を独立評価器と照合。256checkpointを保存。陽性対照32checkpointと合わせ288個。',
            '- full条件の未学習指標はnull。全split、更新数、提示例総数、loss曲線、解析勾配の初期検査、source/protocol hashを保存。',
            f"- NumPy {r['numpy']}、総実行記録時間 {r['elapsed_seconds']:.3f}秒。機器速度の反復benchmarkではない。",
            '- Router/Expertは含まない。MoE統合時の初期負荷分散、固定ランダム経路、同一ランから別seedの交換という既存条件は引き続き必要。', '',
            '## 次の改善案', '',
            '次は学習率をさらに試す前に、同じ固定配線・同じゲート集合で全入力の正解回路を構成できるかを、Boolean制約として検査する。見つかった解は全入力で再評価し、勾配学習の結果と比べる。解が見つからない場合は、証明された不可能と計算時間切れを必ず区別する。', '',
            'これにより、表現可能なのに学習が失敗している配線と、配線変更が必要なケースを分けやすくなる。その後、接続学習・初期化・重み共有のどれを優先するかを決める。複数splitによる汎化検証は別の後続段階として維持する。', '',
            '## 再現', '', '```bash', 'python3 results/E007-full-domain/run_diagnostic.py', 'python3 results/E007-full-domain/report.py', '```', '',
            '既存runがあると訓練は停止して上書きしない。新訓練は別実験IDへソースと設計をコピーする。report.pyは保存結果を再集計する。', '',
            '[事前設計](../results/E007-full-domain/PROTOCOL.md)、[生結果とhash](../results/E007-full-domain/run/results.json)。', '']
    text='\n'.join(lines)
    (root/'REPORT.md').write_text(text)
    (root.parents[1]/'docs/STAR-Bit-E007-full-domain.md').write_text(text)

if __name__=='__main__':main()
