"""Audit and report E040 full-width baseline calibration."""
import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E040-full-width-calibration'; OUT=HERE/'run'
sys.path.insert(0,str(ROOT/'results/E019-function-space-genesis')); import search as base
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
e040=load('e040_for_report',HERE/'main.py')
def strict(path): return json.loads(path.read_text(),parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def metric(values):
 a=np.asarray(values,float); return {'mean':None if len(a)==0 else float(a.mean()),'unbiased_variance':float(a.var(ddof=1)) if len(a)>1 else None,'n':len(a)}
def signflip(values):
 a=np.asarray(values,float); observed=abs(a.mean()); return sum(abs(np.mean([v if mask&(1<<i) else -v for i,v in enumerate(a)]))>=observed-1e-12 for mask in range(1<<len(a)))/(1<<len(a))
def paired(values,rng):
 a=np.asarray(values,float); samples=a[rng.integers(0,len(a),(20000,len(a)))].mean(1); sd=a.std(ddof=1)
 return {'mean':float(a.mean()),'unbiased_variance':float(a.var(ddof=1)),'ci95':np.quantile(samples,[.025,.975]).tolist(),'cohen_dz':None if sd==0 else float(a.mean()/sd),'exact_signflip_p':signflip(a),'differences':a.tolist()}
def holm(values):
 order=sorted(range(len(values)),key=lambda i:values[i]); adjusted=[0.0]*len(values); running=0.0
 for rank,index in enumerate(order): running=max(running,min(1.0,(len(values)-rank)*values[index])); adjusted[index]=float(running)
 return adjusted
def evaluate(expression,inputs):
 if expression[0]=='input': return inputs[expression[1]]
 signature=base.lut_outputs(evaluate(expression[3],inputs),evaluate(expression[4],inputs))[expression[2]]; assert signature==int(expression[1]); return signature

result=strict(OUT/'results.json'); frozen=strict(OUT/'frozen_manifest.json'); records=result['records']; settings=result['settings']
assert settings=={'seeds':list(range(1550,1556)),'tasks':list(e040.tasks_from_grammar()),'round_budgets':[3,4,5],'beam':128,'max_rounds':5,'max_cost':16,'condition':'no_transfer'}
assert len(records)==36 and len({(r['seed'],r['task']) for r in records})==36
assert [json.loads(line) for line in (OUT/'progress.jsonl').read_text().splitlines()]==records
for name,digest in result['sources'].items(): assert sha(ROOT/name)==digest,name
targets=e040.tasks_from_grammar(); assert frozen['targets']=={k:str(v) for k,v in targets.items()}; assert not(set(targets.values())&e040.prior_signatures())
inputs,_=base.inputs_and_targets(); verified=0
for r in records:
 assert r['library_signatures']==[] and r['beam']==128 and r['round_two_input_width']==128 and len(r['best_error_history']) in (r['round'],5)
 if r['exact']:
  assert r['round'] is not None and evaluate(r['expression'],inputs)==targets[r['task']]; verified+=1

derived=[]
for r in records:
 for budget in settings['round_budgets']:
  exact=bool(r['exact'] and r['round']<=budget); error=0 if exact else r['best_error_history'][budget-1]
  derived.append({'seed':r['seed'],'task':r['task'],'family':r['family'],'round_budget':budget,'exact':exact,'best_error':error,'round_two_input_width':r['round_two_input_width']})
assert len(derived)==108
(OUT/'derived_rows.json').write_text(json.dumps(derived,indent=2,allow_nan=False))
by={(r['seed'],r['task'],r['round_budget']):r for r in derived}; tasks=list(targets); seeds=settings['seeds']; budgets=settings['round_budgets']
summary={'by_task_budget':{},'round5_minus_round3':{},'holm_round_sensitivity':{},'selected_settings':{},'feasibility_gate_passed':False,'records_verified':36,'derived_rows_verified':108,'solutions_verified':verified,'full_width_runs_verified':36,'analysis_source_hash':sha(HERE/'report.py')}
for task in tasks:
 summary['by_task_budget'][task]={}
 source=[r for r in records if r['task']==task]
 for budget in budgets:
  rows=[by[s,task,budget] for s in seeds]; solved=[r for r in source if r['exact'] and r['round']<=budget]
  summary['by_task_budget'][task][str(budget)]={'exact':metric([r['exact'] for r in rows]),'best_error':metric([r['best_error'] for r in rows]),'solution_primitives':metric([r['primitives'] for r in solved]),'solution_routing_bits':metric([r['routing_bits'] for r in solved]),'solution_depth':metric([r['depth'] for r in solved])}
 summary['by_task_budget'][task]['max_run_elapsed_seconds']=metric([r['elapsed_seconds'] for r in source]); summary['by_task_budget'][task]['max_run_generated_signatures']=metric([r['generated_unique_signatures'] for r in source])
rng=np.random.default_rng(2040)
for task in tasks: summary['round5_minus_round3'][task]=paired([int(by[s,task,5]['exact'])-int(by[s,task,3]['exact']) for s in seeds],rng)
adjusted=holm([summary['round5_minus_round3'][t]['exact_signflip_p'] for t in tasks]); summary['holm_round_sensitivity']={t:p for t,p in zip(tasks,adjusted)}
for family in ('numeric','route'):
 eligible=[]
 for budget in budgets:
  for task in [t for t in tasks if t.startswith(family+'_')]:
   exact=sum(by[s,task,budget]['exact'] for s in seeds); full=all(by[s,task,budget]['round_two_input_width']==128 for s in seeds)
   if 2<=exact<=4 and full: eligible.append({'task':task,'round_budget':budget,'exact_count':exact,'beam':128})
 summary['selected_settings'][family]=eligible[0] if eligible else None
summary['feasibility_gate_passed']=all(summary['selected_settings'].values())
(OUT/'selected_settings.json').write_text(json.dumps({'selection_rule':'fewest rounds, then preregistered task order','selected_settings':summary['selected_settings'],'feasibility_gate_passed':summary['feasibility_gate_passed']},indent=2,allow_nan=False))
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))

lines=['# E040：実効幅128での新規Task難度校正','', '実行日：2026-09-26。Function条件を見ず、事前固定した精密数値3 task・経路選択3 taskを新規6 seedでbaseline-only探索した。各seed/taskは5 roundを一度だけ実行し、決定論的prefixから3/4/5 round予算を評価した。','', '| task | round | exact/6 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | 成功式 primitive / routing / depth平均 |','| --- | ---: | ---: | ---: | ---: | ---: |']
for task in tasks:
 for budget in budgets:
  x=summary['by_task_budget'][task][str(budget)]; count=round(x['exact']['mean']*6); cost='NA' if x['solution_primitives']['mean'] is None else f"{x['solution_primitives']['mean']:.2f} / {x['solution_routing_bits']['mean']:.2f} / {x['solution_depth']['mean']:.2f}"
  lines.append(f"| {task} | {budget} | {count}/6 | {x['exact']['mean']:.4f} / {x['exact']['unbiased_variance']:.4f} | {x['best_error']['mean']:.3f} / {x['best_error']['unbiased_variance']:.3f} | {cost} |")
lines += ['', '## 事前Feasibility判定','', f"numeric選択: `{summary['selected_settings']['numeric']}`。route選択: `{summary['selected_settings']['route']}`。両family選択基準は"+('達成した。' if summary['feasibility_gate_passed'] else '未達だった。'),'', '数値3 taskはすべてround 3で6/6の天井、routeは最大でもrotated cross XORのround 4/5で1/6だった。全36 runでround 2実効幅128を確認し、E039の幅上限未充足は解消したが、中難度設定は得られなかった。E040からFunction比較対象を選ばない。','', '## Round感度（round 5−3 exact、Holm補正）','', '| task | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for task,x in summary['round5_minus_round3'].items():
 effect='NA' if x['cohen_dz'] is None else f"{x['cohen_dz']:.3f}"; lines.append(f"| {task} | {x['mean']:+.4f} | {x['unbiased_variance']:.4f} | [{x['ci95'][0]:.4f}, {x['ci95'][1]:.4f}] | {effect} | {x['exact_signflip_p']:.4f} | {summary['holm_round_sensitivity'][task]:.4f} |")
lines += ['',f"全{verified} exact式を64入力で再評価した。36 run、108 derived row、progress、strict JSON、source hash、target非衝突、Library不使用、実効幅を監査。探索CPU時間合計{result['search_seconds']:.1f}秒。",'', '## Roadmap','', '- [Done] 新規6 taskをbaseline-onlyで校正し、全runで実効beam幅128を確認した。','- [Next] 数値側を4〜5入力へ難化し、route側を1段浅くした隣接grammarを、同じbaseline-only選択規則で校正する。','- [Later] 両familyの中難度設定を独立seedで固定幅replace/add比較し、その後にState形成・分解とRouter統合へ進む。','', 'English: E040 restored a fully populated 128-entry beam but found no middle-difficulty setting: all three numeric tasks reached 6/6 by round 3, while routing tasks reached at most 1/6. No Function condition was evaluated or selected.','', '简体中文：E040恢复了完整的128项beam，但没有得到中等难度设置：三个数值任务均在第3轮达到6/6，路由任务最高仅1/6。本实验未评估或选择任何函数条件。','', '[事前計画](../results/E040-full-width-calibration/PROTOCOL.md) / [生データ](../results/E040-full-width-calibration/run/results.json) / [派生行](../results/E040-full-width-calibration/run/derived_rows.json) / [選択](../results/E040-full-width-calibration/run/selected_settings.json) / [監査](../results/E040-full-width-calibration/run/audit_summary.json)']
report='\n'.join(lines)+'\n'; (ROOT/'docs/STAR-Bit-E040-full-width-calibration.md').write_text(report); (HERE/'REPORT.md').write_text(report.replace('(../results/E040-full-width-calibration/','(')); print(json.dumps({'feasibility_gate_passed':summary['feasibility_gate_passed'],'verified':verified,'search_seconds':result['search_seconds']},indent=2))
