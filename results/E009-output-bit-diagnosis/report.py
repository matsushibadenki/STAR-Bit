import sys,json,gzip,hashlib
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'results/E008-fixed-wiring-sat'))
import solve as base
out=HERE/'run';r=json.loads((out/'results.json').read_text());rows=r['records']
assert len(rows)==256
for p,h in r['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
sat=0
for a in rows:
 stem=f"{a['task']}-{a['seed']}-{a['condition']}-bit{a['bit']}"
 assert hashlib.sha256((out/f'{stem}.smt2.gz').read_bytes()).hexdigest()==a['formula_sha256']
 if a['status']=='sat':
  w=json.loads((out/f'{stem}-witness.json').read_text());x,y=base.data(a['task'])
  assert np.array_equal(base.evaluate(x,w['wires'],w['tables'],w['outputs']),y[:,a['bit']:a['bit']+1]);sat+=1
summary=[];conflicts=[];obstructions=[]
for task in ['numeric','selection']:
 for mode in ['gate2','lut4']:
  sub=[a for a in rows if a['task']==task and a['condition']==mode]
  fractions=[]
  for seed in range(500,516):
   group=[a for a in sub if a['seed']==seed];assert len(group)==4
   fractions.append(sum(a['status']=='sat' for a in group)/4)
   if any(a['status']=='unsat' for a in group):obstructions.append([task,mode,seed])
   if all(a['status']=='sat' for a in group) and group[0]['joint_status']=='unsat':conflicts.append([task,mode,seed])
  summary.append(dict(task=task,mode=mode,sat_fraction_mean=float(np.mean(fractions)),sat_fraction_variance=float(np.var(fractions,ddof=1))))
lines=['# E009：出力bit別の固定配線診断','', '2026-09-12。16seed×2タスク×2構造×4出力＝256問。E008と同じ配線で、出力を1bitずつ独立に制約した。新規学習や汎化評価ではない。','', '| task | 構造 | bit | SAT | UNSAT | UNKNOWN |','| --- | --- | ---: | ---: | ---: | ---: |']
for task in ['numeric','selection']:
 for mode in ['gate2','lut4']:
  for bit in range(4):
   sub=[a for a in rows if (a['task'],a['condition'],a['bit'])==(task,mode,bit)]
   counts=[sum(a['status']==s for a in sub) for s in ['sat','unsat','unknown']]
   lines.append(f'| {task} | {mode} | {bit} | '+ ' | '.join(map(str,counts))+' |')
lines+=['','## seed間の記述統計','','各seedの「4bit中SATを発見できた割合」を集計する。精度や真の構成可能率ではなく、1秒の探索予算に依存する下限である。','', '| task | 構造 | 平均 | 不偏分散 |','| --- | --- | ---: | ---: |']
for a in summary:lines.append(f"| {a['task']} | {a['mode']} | {a['sat_fraction_mean']:.6f} | {a['sat_fraction_variance']:.6f} |")
lines+=['',f'少なくとも1bitがUNSATの配線は{len(obstructions)}/64。各bitはSATだがE008の同時出力がUNSATとなる配線は{len(conflicts)}/64。後者だけが、個々のbitは表現できても共有ゲート表の同時整合が妨げになるという診断に対応する。','',f'全{sat}件のSAT証人を保存後に独立評価器で再読込し、対象bitについて全64入力一致を確認。全256論理式とソースhashも確認。UNSATはZ3判定であり、本実験では証明を保存・独立検証していない。UNKNOWNは不能とは判定しない。','',f"実行時間{r['elapsed_seconds']:.1f}秒、Z3 {r['z3']}、単一thread、各問1000ms。E008は10000msなのでSAT件数差を効果量や速度改善と解釈しない。異なるbitのSAT証人はそれぞれ別のゲート表である。",'', '探索的な論理診断のため、有意差検定・学習効果量は計算しない。元の学習精度の平均・分散はE008に記載。成功seedの追加や除外は行わない。','', '## 次の改善案','','単一bitのUNSATがある出力の祖先回路を優先し、追加接続の本数を固定して、無作為追加と入力依存性を考慮した追加を比較する。ゲート数を増やす前に接続変更の効果を分離する。共有制約のみの失敗には出力別回路の複製を診断用の容量対照とする。','', 'Routerを含まない段階の実験であり、統合時の負荷分散・固定ランダム経路・Expert交換の対照は維持する。','', 'English: Per-output feasibility distinguishes individual-output obstructions from shared-gate conflicts. SAT witnesses were independently evaluated; UNKNOWN remains unresolved. This is not a training result.','', '简体中文：逐输出位检验用于区分单个位的表达限制与共享门约束。SAT见证经过独立求值，UNKNOWN仍未确定。本实验不是训练或泛化结果。','', '再現：`python3 results/E009-output-bit-diagnosis/run.py`、続いて `python3 results/E009-output-bit-diagnosis/report.py`。既存runがあると停止する。Z3 5.1.0.0を/private/tmp/starbit-z3に、NumPyをPython環境に用意する。','', '[事前計画](../results/E009-output-bit-diagnosis/PROTOCOL.md) / [生データ](../results/E009-output-bit-diagnosis/run/results.json)']
(out/'audit_summary.json').write_text(json.dumps(dict(verified_witnesses=sat,summary=summary,individual_obstructions=obstructions,shared_conflicts=conflicts),indent=2))
text='\n'.join(lines)+'\n';(HERE/'REPORT.md').write_text(text);(ROOT/'docs/STAR-Bit-E009-output-bit-diagnosis.md').write_text(text)
print(json.dumps(dict(verified_witnesses=sat,individual_obstructions=len(obstructions),shared_conflicts=len(conflicts),summary=summary),indent=2))
