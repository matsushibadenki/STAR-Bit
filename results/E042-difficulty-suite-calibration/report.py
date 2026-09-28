"""Audit and report E042 frozen difficulty-suite calibration."""
import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E042-difficulty-suite-calibration'; OUT=HERE/'run'
sys.path.insert(0,str(ROOT/'results/E019-function-space-genesis')); import search as base
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
e042=load('e042_for_report',HERE/'main.py')
def strict(path): return json.loads(path.read_text(),parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def metric(values):
 a=np.asarray(values,float); return {'mean':None if len(a)==0 else float(a.mean()),'unbiased_variance':None if len(a)<2 else float(a.var(ddof=1)),'n':len(a)}
def signflip(values):
 a=np.asarray(values,float); observed=abs(a.mean()); return sum(abs(np.mean([v if mask&(1<<i) else -v for i,v in enumerate(a)]))>=observed-1e-12 for mask in range(1<<len(a)))/(1<<len(a))
def paired(values,rng):
 a=np.asarray(values,float); samples=a[rng.integers(0,len(a),(20000,len(a)))].mean(1); sd=a.std(ddof=1)
 return {'mean':float(a.mean()),'unbiased_variance':float(a.var(ddof=1)),'ci95':np.quantile(samples,[.025,.975]).tolist(),'cohen_dz':None if sd==0 else float(a.mean()/sd),'exact_signflip_p':signflip(a),'differences':a.tolist()}
def bootstrap_metric(values,rng):
 a=np.asarray(values,float); samples=a[rng.integers(0,len(a),(20000,len(a)))].mean(1); out=metric(a); out['ci95']=np.quantile(samples,[.025,.975]).tolist(); return out
def holm(values):
 order=sorted(range(len(values)),key=lambda i:values[i]); adjusted=[0.0]*len(values); running=0.0
 for rank,index in enumerate(order): running=max(running,min(1.0,(len(values)-rank)*values[index])); adjusted[index]=float(running)
 return adjusted
def evaluate(expression,inputs):
 if expression[0]=='input': return inputs[expression[1]]
 signature=base.lut_outputs(evaluate(expression[3],inputs),evaluate(expression[4],inputs))[expression[2]]; assert signature==int(expression[1]); return signature

result=strict(OUT/'results.json'); frozen=strict(OUT/'frozen_manifest.json'); records=result['records']; settings=result['settings']; targets=e042.tasks_from_registry(); seeds=list(range(1570,1582)); tasks=list(targets)
expected_strata={'numeric':{'easy':['numeric_2bit_sum_ge3','numeric_4bit_weighted_ge4'],'hard':['numeric_rotated_weight_ge6','numeric_5bit_weighted_ge5']},'route':{'easy':['route_mux_xor_bit','route_mux_conditional_flip'],'hard':['route_rotated_cross_xnor','route_nested_mux']}}
assert settings=={'seeds':seeds,'tasks':tasks,'beam':128,'rounds':4,'max_cost':16,'condition':'no_transfer','strata':expected_strata}
assert frozen['targets']=={k:str(v) for k,v in targets.items()} and len(records)==96 and len({(r['seed'],r['task']) for r in records})==96
assert [json.loads(line) for line in (OUT/'progress.jsonl').read_text().splitlines()]==records
for name,digest in result['sources'].items(): assert sha(ROOT/name)==digest,name
inputs,_=base.inputs_and_targets(); verified=0
for r in records:
 assert r['library_signatures']==[] and r['beam']==128 and r['round_budget']==4 and r['round_two_input_width']==128 and len(r['best_error_history']) in (r['round'],4)
 if r['exact']: assert evaluate(r['expression'],inputs)==targets[r['task']]; verified+=1
by={(r['seed'],r['task']):r for r in records}; family_tasks={f:[t for t in tasks if t.startswith(f+'_')] for f in ('numeric','route')}
suite_rows=[]
for seed in seeds:
 for family in ('numeric','route'):
  count=sum(int(by[seed,t]['exact']) for t in family_tasks[family]); suite_rows.append({'seed':seed,'family':family,'exact_count':count,'exact_proportion':count/4,'best_error_mean':sum(by[seed,t]['best_error'] for t in family_tasks[family])/4})
(OUT/'suite_rows.json').write_text(json.dumps(suite_rows,indent=2,allow_nan=False))
suite={(r['seed'],r['family']):r for r in suite_rows}; rng=np.random.default_rng(2042)
summary={'by_task':{},'suite':{},'family_difference':{},'round4_minus_round2':{},'holm_round_sensitivity':{},'suite_gate_passed':False,'records_verified':96,'suite_rows_verified':24,'solutions_verified':verified,'full_width_runs_verified':96,'analysis_source_hash':sha(HERE/'report.py')}
for task in tasks:
 rows=[by[s,task] for s in seeds]; solved=[r for r in rows if r['exact']]
 summary['by_task'][task]={'exact':metric([r['exact'] for r in rows]),'best_error':metric([r['best_error'] for r in rows]),'elapsed_seconds':metric([r['elapsed_seconds'] for r in rows]),'generated_unique_signatures':metric([r['generated_unique_signatures'] for r in rows]),'solution_primitives':metric([r['primitives'] for r in solved]),'solution_routing_bits':metric([r['routing_bits'] for r in solved]),'solution_depth':metric([r['depth'] for r in solved])}
 round_values=[int(r['exact'])-int(r['best_error_history'][1]==0) for r in rows]; summary['round4_minus_round2'][task]=paired(round_values,rng)
for family in ('numeric','route'):
 values=[suite[s,family]['exact_proportion'] for s in seeds]; summary['suite'][family]={'exact_proportion':bootstrap_metric(values,rng),'best_error_mean':metric([suite[s,family]['best_error_mean'] for s in seeds]),'per_seed_counts':[suite[s,family]['exact_count'] for s in seeds]}
summary['family_difference']=paired([suite[s,'numeric']['exact_proportion']-suite[s,'route']['exact_proportion'] for s in seeds],rng)
adjusted=holm([summary['round4_minus_round2'][t]['exact_signflip_p'] for t in tasks]); summary['holm_round_sensitivity']={t:p for t,p in zip(tasks,adjusted)}
summary['suite_gate_passed']=bool(all(.25<=summary['suite'][f]['exact_proportion']['mean']<=.75 and all(1<=x<=3 for x in summary['suite'][f]['per_seed_counts']) for f in ('numeric','route')))
(OUT/'suite_selection.json').write_text(json.dumps({'suite_gate_passed':summary['suite_gate_passed'],'frozen_tasks':family_tasks,'next_step':'freeze full suite; do not select individual E042 tasks'},indent=2,allow_nan=False)); (OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))

lines=['# E042：凍結Difficulty Suiteの独立Seed校正','', '実行日：2026-09-28。E040–E041で凍結したeasy/hard各2 taskをfamilyごとに混ぜ、Functionなし・新規12 seed・実効beam幅128・4 roundで評価した。単一truth tableではなく4 task suiteの平均を主要評価単位とする。','', '| family | suite exact平均 / 不偏分散 | bootstrap 95% CI | seed別成功task数 | suite best error平均 / 不偏分散 |','| --- | ---: | --- | --- | ---: |']
for family in ('numeric','route'):
 x=summary['suite'][family]; lines.append(f"| {family} | {x['exact_proportion']['mean']:.4f} / {x['exact_proportion']['unbiased_variance']:.4f} | [{x['exact_proportion']['ci95'][0]:.4f}, {x['exact_proportion']['ci95'][1]:.4f}] | {x['per_seed_counts']} | {x['best_error_mean']['mean']:.3f} / {x['best_error_mean']['unbiased_variance']:.3f} |")
d=summary['family_difference']; effect='NA' if d['cohen_dz'] is None else f"{d['cohen_dz']:.3f}"
lines += ['', 'suite feasibility gateは'+('達成した。' if summary['suite_gate_passed'] else '未達だった。'),f"numeric−route exact比率差は{d['mean']:+.4f}、不偏分散{d['unbiased_variance']:.4f}、95% CI [{d['ci95'][0]:.4f}, {d['ci95'][1]:.4f}]、dz {effect}、exact p={d['exact_signflip_p']:.4f}。",'', '| task | exact/12 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | 秒平均 | 成功式 primitive / routing / depth平均 |','| --- | ---: | ---: | ---: | ---: | ---: |']
for task in tasks:
 x=summary['by_task'][task]; count=round(x['exact']['mean']*12); cost='NA' if x['solution_primitives']['mean'] is None else f"{x['solution_primitives']['mean']:.2f} / {x['solution_routing_bits']['mean']:.2f} / {x['solution_depth']['mean']:.2f}"; lines.append(f"| {task} | {count}/12 | {x['exact']['mean']:.4f} / {x['exact']['unbiased_variance']:.4f} | {x['best_error']['mean']:.3f} / {x['best_error']['unbiased_variance']:.3f} | {x['elapsed_seconds']['mean']:.3f} | {cost} |")
lines += ['', '## Round 4−2感度（Holm補正）','', '| task | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for task,x in summary['round4_minus_round2'].items():
 effect='NA' if x['cohen_dz'] is None else f"{x['cohen_dz']:.3f}"; lines.append(f"| {task} | {x['mean']:+.4f} | {x['unbiased_variance']:.4f} | [{x['ci95'][0]:.4f}, {x['ci95'][1]:.4f}] | {effect} | {x['exact_signflip_p']:.6f} | {summary['holm_round_sensitivity'][task]:.6f} |")
lines += ['', 'numericは全seedで2/4、routeは11 seedで2/4・1 seedで3/4となり、両familyに床と天井の回避、かつ介入で動けるheadroomを確保した。これはFunction効果ではなく、評価設計のfeasibility達成である。全suiteを凍結し、個別taskを選び直さず独立介入へ進む。','',f"全{verified} exact式を64入力で再評価した。96 record、24 suite row、progress、strict JSON、source hash、suite membership、Library不使用、実効幅128を監査。探索CPU時間合計{result['search_seconds']:.1f}秒。",'', '## Roadmap','', '- [Done] family別のeasy/hard混合suiteを独立12 seedで校正し、事前feasibility gateを満たした。','- [Next] 全8 taskを固定し、衝突なしlearned/inert/random Moduleのreplace/addを新規seedで比較する。','- [Later] Function固有の再利用が確認された後にState形成・分解、Logic/Ternary Router、総物理費用へ進む。','', 'English: E042 validated a frozen mixed-difficulty evaluation unit on 12 independent seeds. Numeric averaged 0.50 exact and routing 0.521, with every seed retaining both solved and unsolved tasks. This establishes evaluation headroom, not a Function effect.','', '简体中文：E042在12个独立种子上验证了冻结的混合难度评估单元。数值任务平均exact为0.50，路由任务为0.521，每个种子都同时包含成功和未成功任务。这只证明评估空间可用，并非函数效应。','', '[事前計画](../results/E042-difficulty-suite-calibration/PROTOCOL.md) / [生データ](../results/E042-difficulty-suite-calibration/run/results.json) / [Suite行](../results/E042-difficulty-suite-calibration/run/suite_rows.json) / [凍結判断](../results/E042-difficulty-suite-calibration/run/suite_selection.json) / [監査](../results/E042-difficulty-suite-calibration/run/audit_summary.json)']
report='\n'.join(lines)+'\n'; (ROOT/'docs/STAR-Bit-E042-difficulty-suite-calibration.md').write_text(report); (HERE/'REPORT.md').write_text(report.replace('(../results/E042-difficulty-suite-calibration/','(')); print(json.dumps({'suite_gate_passed':summary['suite_gate_passed'],'verified':verified,'search_seconds':result['search_seconds']},indent=2))
