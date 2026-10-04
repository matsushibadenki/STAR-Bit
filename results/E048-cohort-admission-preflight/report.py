import json,hashlib,importlib.util
from pathlib import Path
import numpy as np
R=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); D=R/'results/E048-cohort-admission-preflight'; O=D/'run'
spec=importlib.util.spec_from_file_location('e048audit',D/'main.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
r=json.loads((O/'results.json').read_text()); rows=r['records']; seeds=list(range(1650,1656)); assert r['settings']['seeds']==seeds and len(rows)==48 and len({(x['seed'],x['task']) for x in rows})==48
assert [json.loads(x) for x in (O/'progress.jsonl').read_text().splitlines()]==rows
for name,digest in r['sources'].items(): assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest
inputs,_=m.m.base.inputs_and_targets(); cohort={int(x['signature']):x for x in r['source_cohort']}; union={int(s) for x in rows for s in x['round2_selected']}; admitted=set(map(int,r['admitted'])); tasks=m.m.e042.tasks_from_registry(); assert admitted==set(cohort)-union-set(tasks.values())
for sig,x in cohort.items(): assert m.m.e023.evaluate(x['expression'],inputs)==sig and m.lib.expression_cost(x['expression'])==(x['primitives'],x['routing_bits'],x['depth'])
used=set(); count=0
for group in r['random_controls']:
 assert len(group['cohort'])==len(admitted)
 for x in group['cohort']:
  sig=int(x['signature']); assert sig not in union|set(tasks.values())|set(cohort)|used; used.add(sig); template=cohort[int(x['template'])]; assert tuple(x['cost'])==(template['primitives'],template['routing_bits'],template['depth'])==m.lib.expression_cost(x['expression']); assert m.m.e023.evaluate(x['expression'],inputs)==sig; count+=1
for x in rows: assert len(x['round2_selected'])==192 and set(map(int,x['available']))==set(cohort)-set(map(int,x['round2_selected']))-{tasks[x['task']]}
a=np.array([sum(len(x['available']) for x in rows if x['seed']==s)/8 for s in seeds]); rng=np.random.default_rng(2048); ci=np.quantile(a[rng.integers(0,6,(20000,6))].mean(1),[.025,.975]); diff=8-a; obs=abs(diff.mean()); p=sum(abs(np.mean([v if mask&(1<<i) else -v for i,v in enumerate(diff)]))>=obs-1e-12 for mask in range(64))/64
summary={'gate':len(admitted)>=4,'admitted':len(admitted),'availability_mean':float(a.mean()),'availability_variance':float(a.var(ddof=1)),'availability_ci95':ci.tolist(),'availability_seed_means':a.tolist(),'loss_mean':float(diff.mean()),'loss_variance':float(diff.var(ddof=1)),'loss_dz':None if diff.std(ddof=1)==0 else float(diff.mean()/diff.std(ddof=1)),'loss_p':float(p),'records':48,'random_verified':count,'source_verified':8,'analysis_hash':hashlib.sha256((D/'report.py').read_bytes()).hexdigest()}
report=f'''# E048：固定CohortのAdmission事前監査

2026-10-04。凍結8 task、6 calibration seed、初回128・後続192で48組を2回照合した。sourceはE022の既存learned Functionsのうちprimitive>=4の全8件。学習条件の結果を使わずsignature衝突だけでadmissionを決定した。

事前feasibility gate：{summary['gate']}。全beam・taskとの衝突なし採用は{len(admitted)}/8。seed別利用可能数の平均{a.mean():.4f}、不偏分散{a.var(ddof=1):.4f}、bootstrap 95% CI {ci.tolist()}。8件からの利用可能数損失は平均{diff.mean():.4f}、分散{diff.var(ddof=1):.4f}、dz={summary['loss_dz']}、exact sign-flip p={p:.5f}。検定は1つで多重補正なし。

source8式とrandom{count}式の64入力signature・primitive/routing/depth費用を再評価した。48 unique record、progress、全round2幅192、source hashを監査。探索時間{r['search_seconds']:.1f}秒。今回の採用は機械的admission feasibilityであり、学習された意味の利益や精度向上は未評価。

改善案：cohortをsourceから固定した上で、全calibration beamとの衝突除外を先に完了し、次の意味比較で候補数や費用の不一致を避ける。確認seedは今回と分離する。

- [Done] source-frozen cohortと同費用random対照を監査して保存した。
- [Next] 採用cohortを固定し、learned／composition不能inert／同費用randomとbaselineを新規seedで比較する。
- [Later] 意味固有効果成立後、State形成・分解、負荷分散Router、固定random経路、Expert交換へ進む。

English: E048 audited a source-frozen cohort before semantic comparison; admitted {len(admitted)}/8 Functions and verified {count} collision-free, cost-matched random controls. This establishes admission feasibility only.

简体中文：E048在语义比较之前审计冻结source cohort，采用{len(admitted)}/8个函数，并验证{count}个无冲突同成本随机对照；这仅验证加入机制的可行性。
'''
(O/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)); (D/'REPORT.md').write_text(report); (R/'docs/STAR-Bit-E048-cohort-admission-preflight.md').write_text(report); print(json.dumps(summary,indent=2))
