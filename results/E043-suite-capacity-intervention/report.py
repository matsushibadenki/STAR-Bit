"""Audit and report E043 frozen-suite capacity intervention."""
import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E043-suite-capacity-intervention'; OUT=HERE/'run'
sys.path.insert(0,str(ROOT/'results/E019-function-space-genesis')); import search as base
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
e043=load('e043_for_report',HERE/'main.py')
def strict(path): return json.loads(path.read_text(),parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def metric(values):
 a=np.asarray(values,float); return {'mean':None if len(a)==0 else float(a.mean()),'unbiased_variance':None if len(a)<2 else float(a.var(ddof=1)),'n':len(a)}
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

result=strict(OUT/'results.json'); frozen=strict(OUT/'frozen_manifest.json'); preflight=strict(OUT/'round1_preflight.json'); records=result['records']; settings=result['settings']; tasks=e043.e042.tasks_from_registry(); seeds=list(range(1590,1596)); conditions=['no_transfer','learned_replace','learned_add','inert_replace','inert_add','random_replace','random_add']
assert settings=={'seeds':seeds,'tasks':list(tasks),'conditions':conditions,'beam':128,'rounds':4,'max_cost':16,'suite_source':'E042'}
assert frozen['targets']=={k:str(v) for k,v in tasks.items()} and len(records)==336 and len({(r['seed'],r['task'],r['condition']) for r in records})==336
assert [json.loads(line) for line in (OUT/'progress.jsonl').read_text().splitlines()]==records
for name,digest in result['sources'].items(): assert sha(ROOT/name)==digest,name
assert len(preflight)==48; pre={(r['seed'],r['task']):r['selected'] for r in preflight}; assert all(len(x)==128 for x in pre.values())
admitted,row=e043.e039.e028.frozen(); assert frozen['admitted']==json.loads(json.dumps(row)); randoms={(r['seed'],r['task']):r for r in frozen['random_matched']}; assert len(randoms)==48 and len({r['signature'] for r in randoms.values()})==48
inputs,_=base.inputs_and_targets(); union={int(x) for values in pre.values() for x in values}
for r in randoms.values(): assert int(r['signature']) not in union and tuple(r['cost'])==admitted.cost() and e043.e039.e023.evaluate(r['expression'],inputs)==int(r['signature']) and e043.e039.e023.expression_cost(r['expression'])==admitted.cost()
by={(r['seed'],r['task'],r['condition']):r for r in records}; verified=0; first_round=0; widths=0
for r in records:
 assert r['first_round_selected']==pre[r['seed'],r['task']] and not r['injected_collision']; first_round+=int(r['condition']!='no_transfer')
 expected=[] if r['condition']=='no_transfer' else [randoms[r['seed'],r['task']]['signature']] if r['condition'].startswith('random_') else [str(admitted.signature)]; assert r['library_signatures']==expected
 assert r['round_two_input_width']==(129 if r['condition'].endswith('_add') else 128); widths+=int(r['condition']!='no_transfer')
 if r['condition']=='no_transfer' or r['condition'].startswith('inert_'): assert not r['uses_transfer']
 if r['exact']: assert evaluate(r['expression'],inputs)==tasks[r['task']]; verified+=1

rng=np.random.default_rng(2043); kinds=('learned','inert','random'); families=('numeric','route')
summary={'by_family_condition':{},'primary_capacity':{},'family_capacity':{},'holm_family_capacity':{},'semantic':{},'holm_semantic':{},'exploratory_error':{},'capacity_gate_passed':False,'semantic_gate_passed':False,'learned_success_uses':0,'records_verified':336,'solutions_verified':verified,'first_round_pairs_verified':first_round,'post_injection_widths_verified':widths,'injection_collisions':0,'random_functions_verified':48,'analysis_source_hash':sha(HERE/'report.py')}
for family in families:
 summary['by_family_condition'][family]={}; family_tasks=[t for t in tasks if t.startswith(family+'_')]
 for condition in conditions:
  rows=[by[s,t,condition] for s in seeds for t in family_tasks]; solved=[r for r in rows if r['exact']]
  seed_rows=[[by[s,t,condition] for t in family_tasks] for s in seeds]
  summary['by_family_condition'][family][condition]={'exact':metric([sum(r['exact'] for r in group)/len(group) for group in seed_rows]),'best_error':metric([sum(r['best_error'] for r in group)/len(group) for group in seed_rows]),'elapsed_seconds':metric([sum(r['elapsed_seconds'] for r in group)/len(group) for group in seed_rows]),'generated_unique_signatures':metric([sum(r['generated_unique_signatures'] for r in group)/len(group) for group in seed_rows]),'exact_uses_transfer':sum(bool(r['exact'] and r['uses_transfer']) for r in rows),'solution_primitives':metric([r['primitives'] for r in solved]),'solution_routing_bits':metric([r['routing_bits'] for r in solved]),'solution_depth':metric([r['depth'] for r in solved])}
def exact_d(seed,task,left,right): return int(by[seed,task,left]['exact'])-int(by[seed,task,right]['exact'])
def error_d(seed,task,left,right): return int(by[seed,task,left]['best_error'])-int(by[seed,task,right]['best_error'])
primary=[sum(exact_d(s,t,f'{k}_add',f'{k}_replace') for t in tasks for k in kinds)/24 for s in seeds]; summary['primary_capacity']=paired(primary,rng); summary['capacity_gate_passed']=bool(summary['primary_capacity']['mean']>=.10 and summary['primary_capacity']['exact_signflip_p']<=.05)
for family in families:
 ft=[t for t in tasks if t.startswith(family+'_')]; summary['family_capacity'][family]=paired([sum(exact_d(s,t,f'{k}_add',f'{k}_replace') for t in ft for k in kinds)/12 for s in seeds],rng)
summary['holm_family_capacity']={k:p for k,p in zip(families,holm([summary['family_capacity'][k]['exact_signflip_p'] for k in families]))}
semantic_values={'learned-add-minus-inert-add':[sum(exact_d(s,t,'learned_add','inert_add') for t in tasks)/8 for s in seeds],'learned-add-minus-random-add':[sum(exact_d(s,t,'learned_add','random_add') for t in tasks)/8 for s in seeds]}
for k,v in semantic_values.items(): summary['semantic'][k]=paired(v,rng)
summary['holm_semantic']={k:p for k,p in zip(semantic_values,holm([summary['semantic'][k]['exact_signflip_p'] for k in semantic_values]))}
summary['learned_success_uses']=sum(bool(by[s,t,'learned_add']['exact'] and by[s,t,'learned_add']['uses_transfer']) for s in seeds for t in tasks)
summary['semantic_gate_passed']=bool(all(summary['semantic'][k]['mean']>0 and summary['holm_semantic'][k]<=.05 for k in semantic_values) and summary['learned_success_uses']>0)
error_values={'pooled:add-minus-replace':[sum(error_d(s,t,f'{k}_add',f'{k}_replace') for t in tasks for k in kinds)/24 for s in seeds],'learned-add-minus-inert-add':[sum(error_d(s,t,'learned_add','inert_add') for t in tasks)/8 for s in seeds],'learned-add-minus-random-add':[sum(error_d(s,t,'learned_add','random_add') for t in tasks)/8 for s in seeds]}
for k,v in error_values.items(): summary['exploratory_error'][k]=paired(v,rng)
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))

lines=['# E043：凍結Suiteでの衝突なし遅延Admission介入','', '実行日：2026-09-29。E042の全8 taskを固定し、新規6 seedで移植なしと、learned／inert／同費用randomのround 1後replace/addを比較した。randomは48 seed/taskすべてで全round 1 beamとのsignature衝突を事前除外した。計336探索。','', '| family | 条件 | exact/24 | seed別exact平均 / 不偏分散 | seed別best error平均 / 不偏分散 | Function使用成功/成功数 | 秒平均 | 成功式 primitive / routing / depth平均 |','| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
for family in families:
 for condition in conditions:
  x=summary['by_family_condition'][family][condition]; count=round(x['exact']['mean']*24); cost='NA' if x['solution_primitives']['mean'] is None else f"{x['solution_primitives']['mean']:.2f} / {x['solution_routing_bits']['mean']:.2f} / {x['solution_depth']['mean']:.2f}"; lines.append(f"| {family} | {condition} | {count}/24 | {x['exact']['mean']:.4f} / {x['exact']['unbiased_variance']:.4f} | {x['best_error']['mean']:.3f} / {x['best_error']['unbiased_variance']:.3f} | {x['exact_uses_transfer']}/{count} | {x['elapsed_seconds']['mean']:.3f} | {cost} |")
p=summary['primary_capacity']; effect='NA' if p['cohen_dz'] is None else f"{p['cohen_dz']:.3f}"; lines += ['', '## 事前主指標：add−replace exact差','',f"平均差 {p['mean']:+.4f}、不偏分散 {p['unbiased_variance']:.4f}、bootstrap 95% CI [{p['ci95'][0]:.4f}, {p['ci95'][1]:.4f}]、dz {effect}、exact p={p['exact_signflip_p']:.4f}。容量基準は"+('達成。' if summary['capacity_gate_passed'] else '未達。'),'', '| family | 平均差 | 95% CI | exact p | Holm p |','| --- | ---: | --- | ---: | ---: |']
for family,x in summary['family_capacity'].items(): lines.append(f"| {family} | {x['mean']:+.4f} | [{x['ci95'][0]:.4f}, {x['ci95'][1]:.4f}] | {x['exact_signflip_p']:.4f} | {summary['holm_family_capacity'][family]:.4f} |")
lines += ['', '## 学習意味の副次Gate','', '| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for key,x in summary['semantic'].items():
 effect='NA' if x['cohen_dz'] is None else f"{x['cohen_dz']:.3f}"; lines.append(f"| {key} | {x['mean']:+.4f} | {x['unbiased_variance']:.4f} | [{x['ci95'][0]:.4f}, {x['ci95'][1]:.4f}] | {effect} | {x['exact_signflip_p']:.4f} | {summary['holm_semantic'][key]:.4f} |")
lines += ['',f"学習意味基準は{'達成' if summary['semantic_gate_passed'] else '未達'}。learned-add成功式でFunction使用{summary['learned_success_uses']}件。",'', '## 探索的best-error差（負が左条件有利）','', '| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p |','| --- | ---: | ---: | --- | ---: | ---: |']
for key,x in summary['exploratory_error'].items():
 effect='NA' if x['cohen_dz'] is None else f"{x['cohen_dz']:.3f}"; lines.append(f"| {key} | {x['mean']:+.4f} | {x['unbiased_variance']:.4f} | [{x['ci95'][0]:.4f}, {x['ci95'][1]:.4f}] | {effect} | {x['exact_signflip_p']:.4f} |")
lines += ['', '全条件・familyのexact率は0.5で一致し、add−replace差も学習意味差も0だった。E042のsuite平均headroomはeasyの天井とhardの床を混ぜた集約上のheadroomであり、局所介入に反応する感度を保証しなかった。今後は独立calibration seedで意味を持たないperturbationへの局所応答またはbest error近接性を確認し、その後に別seedでlearned意味を検証する。','',f"全{verified} exact式を64入力で再評価した。336 record、48 random Function、288 first-round照合、288幅検証、衝突0、strict JSON、progress、source hashを監査。探索CPU時間合計{result['search_seconds']:.1f}秒。物理ゲート数・推論速度・Router学習は未測定。",'', '## Roadmap','', '- [Done] 凍結suiteで衝突なしreplace/add介入を完了し、集約headroomだけでは局所感度を保証しないことを確認した。','- [Next] calibration seedでinert/random perturbationへの局所応答とbest-error近接性を事前基準化し、確認seedを分離する。','- [Later] learned固有効果と直接使用が成立後、State形成・分解、Logic/Ternary Router、総物理費用へ進む。','', 'English: E043 found identical 0.50 exact rates for every condition and family. The frozen suite had aggregate headroom but no local sensitivity to delayed replacement or addition; no successful expression used the learned Function.','', '简体中文：E043中所有条件和任务族的exact率都为0.50。冻结任务组具有聚合层面的空间，却对延迟替换或增加容量没有局部敏感性；成功表达式均未使用学习函数。','', '[事前計画](../results/E043-suite-capacity-intervention/PROTOCOL.md) / [生データ](../results/E043-suite-capacity-intervention/run/results.json) / [凍結設定](../results/E043-suite-capacity-intervention/run/frozen_manifest.json) / [Round 1照合](../results/E043-suite-capacity-intervention/run/round1_preflight.json) / [監査](../results/E043-suite-capacity-intervention/run/audit_summary.json)']
report='\n'.join(lines)+'\n'; (ROOT/'docs/STAR-Bit-E043-suite-capacity-intervention.md').write_text(report); (HERE/'REPORT.md').write_text(report.replace('(../results/E043-suite-capacity-intervention/','(')); print(json.dumps({'capacity_gate_passed':summary['capacity_gate_passed'],'semantic_gate_passed':summary['semantic_gate_passed'],'verified':verified,'search_seconds':result['search_seconds']},indent=2))
