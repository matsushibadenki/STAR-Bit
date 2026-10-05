import hashlib,importlib.util,json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E049-frozen-cohort-semantics'; OUT=HERE/'run'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def strict(p): return json.loads(p.read_text(),parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))
spec=importlib.util.spec_from_file_location('e047_main',HERE/'main.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); base=m.base; rng=np.random.default_rng(2049)
def stats(v):
 a=np.asarray(v,float); sd=a.std(ddof=1); obs=abs(a.mean()); p=float(sum(abs(np.mean([x if mask&(1<<i) else -x for i,x in enumerate(a)]))>=obs-1e-12 for mask in range(1<<len(a)))/(1<<len(a))); boot=a[rng.integers(0,len(a),(20000,len(a)))].mean(1)
 return dict(mean=float(a.mean()),variance=float(a.var(ddof=1)),ci95=np.quantile(boot,[.025,.975]).tolist(),dz=None if sd==0 else float(a.mean()/sd),p=p,values=v)
def evaluate(e,inputs):
 if e[0]=='input': return inputs[e[1]]
 sig=base.lut_outputs(evaluate(e[3],inputs),evaluate(e[4],inputs))[e[2]]; assert sig==int(e[1]); return sig
r=strict(OUT/'results.json'); rows=r['records']; tasks=m.e042.tasks_from_registry(); seeds=list(range(1660,1666)); conditions=['baseline','learned','inert','random']; manifest=strict(OUT/'manifest.json'); pre=strict(OUT/'preflight.json'); inputs,_=base.inputs_and_targets()
assert len(rows)==192 and r['settings']=={'seeds':seeds,'tasks':list(tasks),'conditions':conditions}
assert len({(x['seed'],x['task'],x['condition']) for x in rows})==192 and [json.loads(x) for x in (OUT/'progress.jsonl').read_text().splitlines()]==rows
for name,digest in r['sources'].items(): assert sha(ROOT/name)==digest
source={int(x['signature']) for x in manifest['source']}; assert len(source)==8; randoms={(x['seed'],x['task']):x['cohort'] for x in manifest['random']}; preby={(x['seed'],x['task']):x for x in pre}; union={int(v) for x in pre for v in x['round2']}; used=set(); verified=0
for group in [manifest['source']]+list(randoms.values()):
 for j,x in enumerate(group):
  sig=int(x['signature']); assert evaluate(x['expression'],inputs)==sig; cost=m.old.e023.expression_cost(x['expression']); assert cost==(x['primitives'],x['routing_bits'],x['depth'])
  if group is not manifest['source']:
   template=manifest['source'][j]; assert cost==(template['primitives'],template['routing_bits'],template['depth']); assert sig not in union|source|used|set(tasks.values()); used.add(sig)
by={(x['seed'],x['task'],x['condition']):x for x in rows}; uses=0
for x in rows:
 assert x['first_round_selected']==preby[x['seed'],x['task']]['round1'] and x['round2_selected']==preby[x['seed'],x['task']]['round2']
 assert x['input_width_history'][:3]==[6,128,192 if x['condition']=='baseline' else 200]
 expected=set() if x['condition']=='baseline' else set(int(z['signature']) for z in randoms[x['seed'],x['task']]) if x['condition']=='random' else source; assert set(map(int,x['library']))==expected
 if x['condition'] in ['baseline','inert']: assert not x['uses_transfer']
 if x['exact']:
  assert evaluate(x['expression'],inputs)==tasks[x['task']]; verified+=1
  uses+=int(x['condition']=='learned' and x['uses_transfer'])
def differences(f,key,control):
 ts=list(tasks) if f=='all' else [t for t in tasks if t.startswith(f+'_')]
 return [sum(float(by[s,t,'learned'][key])-float(by[s,t,control][key]) for t in ts)/len(ts) for s in seeds]
def correct(items):
 order=sorted(items,key=lambda k:items[k]['p']); running=0
 for rank,k in enumerate(order): running=max(running,min(1.,(len(order)-rank)*items[k]['p'])); items[k]['holm_p']=running
primary={c:stats(differences('all','exact',c)) for c in ['inert','random']}; correct(primary); secondary={f'{f}:{key}:{c}':stats(differences(f,key,c)) for f in ['numeric','route'] for key in ['exact','best_error'] for c in ['inert','random']}; correct(secondary)
summary={'primary':primary,'secondary':secondary,'gate':all(x['mean']>0 and x['holm_p']<=.05 for x in primary.values()) and uses>0,'learned_success_uses':uses,'records':192,'solutions':verified,'random_verified':len(used),'conditions':{},'analysis_hash':sha(HERE/'report.py')}
lines=['# E049：固定Cohortの学習意味比較','','2026-10-05。凍結8 task・6新規seed、初回128/後続192でround2後にsource8件または同費用random8件を追加。inertはsource signatureを保持し全compositionを禁止。baselineは追加なし。','', '| family | 条件 | exact/24 | seed平均 / 不偏分散 | best error平均 / 不偏分散 | Function使用成功 | 秒平均 |','| --- | --- | ---: | ---: | ---: | ---: | ---: |']
for f in ['numeric','route']:
 ts=[t for t in tasks if t.startswith(f+'_')]
 for c in conditions:
  selected=[by[s,t,c] for s in seeds for t in ts]; exact=stats([sum(by[s,t,c]['exact'] for t in ts)/4 for s in seeds]); error=stats([sum(by[s,t,c]['best_error'] for t in ts)/4 for s in seeds]); summary['conditions'][f'{f}:{c}']={'exact':exact,'error':error,'costs':{k:[x[k] for x in selected if x['exact']] for k in ['primitives','routing_bits','depth']},'seconds':[x['elapsed_seconds'] for x in selected],'generated':[x['generated_unique_signatures'] for x in selected]}; lines.append(f"| {f} | {c} | {sum(x['exact'] for x in selected)}/24 | {exact['mean']:.4f} / {exact['variance']:.4f} | {error['mean']:.3f} / {error['variance']:.4f} | {sum(x['exact'] and x['uses_transfer'] for x in selected)} | {np.mean([x['elapsed_seconds'] for x in selected]):.3f} |")
lines+=['','| learned−対照 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for k,x in list(primary.items())+list(secondary.items()): lines.append(f"| {k} | {x['mean']:+.4f} | {x['variance']:.4f} | {x['ci95']} | {x['dz']} | {x['p']:.5f} | {x['holm_p']:.5f} |")
lines+=['',f"事前意味gate：{summary['gate']}。learned使用成功{uses}件。探索時間{r['search_seconds']:.1f}秒、preflight {sum(x['seconds'] for x in pre):.1f}秒。",f"全{verified} exact式とsource8/random{len(used)}式を64入力で再評価し、費用、192 record、共通round1/2 beam、round3幅、progress、source hashを監査。best_error差は負がlearned有利。",'', '- [Done] source-frozen cohortをinert・同費用randomと同時刻同容量で比較した。','- [Next] 固定cohortのprimitive予算内composition到達性と投入後残りround数を、accuracyに依存しない機構診断として事前登録する。','- [Later] 独立意味確認成立後、State形成・分解、初回負荷分散Router、固定random経路、Expert交換へ進む。','', 'English: E049 found zero learned-versus-inert/random exact differences (Holm p=1) and no successful cohort use. Numeric solved12/24 and routing20/24 in every condition.','', '简体中文：E049学习函数相对惰性/随机对照的exact差均为0（Holm p=1），成功表达式未使用cohort。各条件数值12/24、路由20/24。']
OUT.joinpath('audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)); report='\n'.join(lines)+'\n'; (HERE/'REPORT.md').write_text(report); (ROOT/'docs/STAR-Bit-E049-frozen-cohort-semantics.md').write_text(report); print(json.dumps({'primary':primary,'gate':summary['gate'],'uses':uses,'solutions':verified,'search_seconds':r['search_seconds']},indent=2))
