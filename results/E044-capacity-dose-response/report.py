"""Audit and report E044 capacity dose-response."""
import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E044-capacity-dose-response'; OUT=HERE/'run'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
e044=load('e044_for_report',HERE/'main.py'); base=e044.e039.base
def strict(path): return json.loads(path.read_text(),parse_constant=lambda value:(_ for _ in ()).throw(ValueError(value)))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def metric(values):
 a=np.asarray(values,float); return {'mean':float(a.mean()),'unbiased_variance':None if len(a)<2 else float(a.var(ddof=1)),'n':len(a)}
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

result=strict(OUT/'results.json'); frozen=strict(OUT/'frozen_manifest.json'); records=result['records']; tasks=e044.e042.tasks_from_registry(); seeds=list(range(1600,1606)); widths=[64,96,128,160,192]
assert result['settings']=={'seeds':seeds,'tasks':list(tasks),'widths':widths,'rounds':4,'max_cost':16,'condition':'no_transfer','suite_source':'E042','strata':frozen['settings']['strata']}
assert frozen['targets']=={k:str(v) for k,v in tasks.items()} and len(records)==240 and len({(r['seed'],r['task'],r['width']) for r in records})==240
assert [json.loads(line) for line in (OUT/'progress.jsonl').read_text().splitlines()]==records
for name,digest in result['sources'].items(): assert sha(ROOT/name)==digest,name
by={(r['seed'],r['task'],r['width']):r for r in records}; inputs,_=base.inputs_and_targets(); verified=0; prefix_checks=0
for r in records:
 assert r['library_signatures']==[] and not r['uses_transfer'] and not r['injected_collision'] and r['injection_strategy'] is None
 expected=min(r['width'],164)
 assert len(r['first_round_selected'])==expected and r['round_two_input_width']==expected
 if r['exact']: assert evaluate(r['expression'],inputs)==tasks[r['task']]; verified+=1
for seed in seeds:
 for task in tasks:
  beams=[by[seed,task,w]['first_round_selected'] for w in widths]
  for left,right in zip(beams,beams[1:]): assert left==right[:len(left)]; prefix_checks+=1

rng=np.random.default_rng(2044); families=('numeric','route'); summary={'by_family_width':{},'primary_span':{},'family_span':{},'family_error_span':{},'holm_family_span':{},'holm_family_error_span':{},'local_span':{},'task_span':{},'holm_task_exact':{},'holm_task_error':{},'capacity_gate_passed':False,'records_verified':240,'solutions_verified':verified,'width_checks_verified':240,'prefix_checks_verified':prefix_checks,'analysis_source_hash':sha(HERE/'report.py')}
for family in families:
 ft=[t for t in tasks if t.startswith(family+'_')]; summary['by_family_width'][family]={}
 for width in widths:
  groups=[[by[s,t,width] for t in ft] for s in seeds]; solved=[r for group in groups for r in group if r['exact']]
  summary['by_family_width'][family][str(width)]={'exact':metric([sum(r['exact'] for r in g)/len(g) for g in groups]),'best_error':metric([sum(r['best_error'] for r in g)/len(g) for g in groups]),'elapsed_seconds':metric([sum(r['elapsed_seconds'] for r in g)/len(g) for g in groups]),'generated_unique_signatures':metric([sum(r['generated_unique_signatures'] for r in g)/len(g) for g in groups]),'exact_count':len(solved),'solution_primitives':metric([r['primitives'] for r in solved]) if solved else None,'solution_routing_bits':metric([r['routing_bits'] for r in solved]) if solved else None,'solution_depth':metric([r['depth'] for r in solved]) if solved else None}
def exact_diff(seed,ts,hi,lo): return sum(int(by[seed,t,hi]['exact'])-int(by[seed,t,lo]['exact']) for t in ts)/len(ts)
def error_gain(seed,ts,hi,lo): return sum(int(by[seed,t,lo]['best_error'])-int(by[seed,t,hi]['best_error']) for t in ts)/len(ts)
all_tasks=list(tasks); summary['primary_span']=paired([exact_diff(s,all_tasks,192,64) for s in seeds],rng); summary['capacity_gate_passed']=bool(summary['primary_span']['mean']>=.10 and summary['primary_span']['exact_signflip_p']<=.05)
summary['local_span']=paired([exact_diff(s,all_tasks,160,96) for s in seeds],rng)
for family in families:
 ft=[t for t in tasks if t.startswith(family+'_')]; summary['family_span'][family]=paired([exact_diff(s,ft,192,64) for s in seeds],rng); summary['family_error_span'][family]=paired([error_gain(s,ft,192,64) for s in seeds],rng)
summary['holm_family_span']={k:p for k,p in zip(families,holm([summary['family_span'][k]['exact_signflip_p'] for k in families]))}; summary['holm_family_error_span']={k:p for k,p in zip(families,holm([summary['family_error_span'][k]['exact_signflip_p'] for k in families]))}
for task in tasks:
 summary['task_span'][task]={'exact':paired([exact_diff(s,[task],192,64) for s in seeds],rng),'best_error_gain':paired([error_gain(s,[task],192,64) for s in seeds],rng)}
summary['holm_task_exact']={k:p for k,p in zip(tasks,holm([summary['task_span'][k]['exact']['exact_signflip_p'] for k in tasks]))}; summary['holm_task_error']={k:p for k,p in zip(tasks,holm([summary['task_span'][k]['best_error_gain']['exact_signflip_p'] for k in tasks]))}
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))

def effect(x): return 'NA' if x['cohen_dz'] is None else f"{x['cohen_dz']:.3f}"
lines=['# E044：凍結Suiteの容量Dose–Response校正','',f"実行日：2026-09-30。E042の8 taskを固定し、新規6 seed、要求beam幅64/96/128/160/192、Libraryなしで240探索した。探索CPU時間{result['search_seconds']:.1f}秒。初回poolは164 signatureが上限だったため、要求幅192条件のround 1/2実効幅は164（他は要求値どおり）だった。",'', '| family | 要求幅（round 2実効幅） | exact/24 | seed別exact平均 / 不偏分散 | seed別best error平均 / 不偏分散 | 生成signature平均 | 秒平均 | 成功式 primitive / routing / depth平均 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for family in families:
 for width in widths:
  x=summary['by_family_width'][family][str(width)]; cost='NA' if not x['solution_primitives'] else f"{x['solution_primitives']['mean']:.2f} / {x['solution_routing_bits']['mean']:.2f} / {x['solution_depth']['mean']:.2f}"
  lines.append(f"| {family} | {width} ({min(width,164)}) | {x['exact_count']}/24 | {x['exact']['mean']:.4f} / {x['exact']['unbiased_variance']:.4f} | {x['best_error']['mean']:.3f} / {x['best_error']['unbiased_variance']:.3f} | {x['generated_unique_signatures']['mean']:.1f} | {x['elapsed_seconds']['mean']:.3f} | {cost} |")
p=summary['primary_span']; l=summary['local_span']; lines += ['', '## 事前主指標：要求幅192−64 exact差','',f"全8 task平均差 {p['mean']:+.4f}、不偏分散 {p['unbiased_variance']:.4f}、bootstrap 95% CI [{p['ci95'][0]:.4f}, {p['ci95'][1]:.4f}]、dz {effect(p)}、exact p={p['exact_signflip_p']:.4f}。容量感度基準は"+('達成。' if summary['capacity_gate_passed'] else '未達。')+' 要求幅192のround 1/2実効幅は164であり、結果の解釈に残す。',f"局所要求幅160−96 exact差は{l['mean']:+.4f}、95% CI [{l['ci95'][0]:.4f}, {l['ci95'][1]:.4f}]、p={l['exact_signflip_p']:.4f}。",'', '| family | exact差 | 95% CI | dz | exact p | Holm p | error改善 | 95% CI | Holm p |','| --- | ---: | --- | ---: | ---: | ---: | ---: | --- | ---: |']
for family in families:
 x=summary['family_span'][family]; e=summary['family_error_span'][family]; lines.append(f"| {family} | {x['mean']:+.4f} | [{x['ci95'][0]:.4f}, {x['ci95'][1]:.4f}] | {effect(x)} | {x['exact_signflip_p']:.4f} | {summary['holm_family_span'][family]:.4f} | {e['mean']:+.3f} | [{e['ci95'][0]:.3f}, {e['ci95'][1]:.3f}] | {summary['holm_family_error_span'][family]:.4f} |")
lines += ['', '## Task別の幅192−64差','', '| task | exact差 | 95% CI | Holm p | error改善 | 95% CI | Holm p |','| --- | ---: | --- | ---: | ---: | --- | ---: |']
for task,x in summary['task_span'].items():
 a=x['exact']; e=x['best_error_gain']; lines.append(f"| {task} | {a['mean']:+.4f} | [{a['ci95'][0]:.4f}, {a['ci95'][1]:.4f}] | {summary['holm_task_exact'][task]:.4f} | {e['mean']:+.3f} | [{e['ci95'][0]:.3f}, {e['ci95'][1]:.3f}] | {summary['holm_task_error'][task]:.4f} |")
lines += ['', '全体の容量感度gateは達成したが、作用はtask種別で大きく異なった。numeric exactは全要求幅で12/24のまま、要求幅160から`numeric_rotated_weight_ge6`のerrorだけ3→2へ改善した。route exactは要求幅64の8/24から要求幅192の21/24へ増え、hard routingにも到達した。family 2比較のHolm補正後pはexact・errorとも0.0625であり、6 seedではfamily別有意差の主張には届かない。', '', 'E043の±1候補介入が不変だった一方、32〜64枠規模の要求容量差ではrouteが反応した。次は要求幅192の初回pool上限を事前に164へ明示して独立seedでrouteの164対128とnumericのerror改善を確認する。その後、同じ候補数のlearned cohort、composition不能inert cohort、同費用random cohortを追加・置換して、容量と意味を分離する。', '',f"全{verified} exact式を64入力で再評価した。240 record、240 round 1/2実効幅、{prefix_checks} prefix照合、Library使用0、strict JSON、progress、source hashを監査。物理ゲート数・推論速度・Router学習は未測定。",'', '## Roadmap','', '- [Done] frozen suiteでsemantic-freeな5段階容量responseを測定し、全体exact感度gateを達成した。','- [Next] 独立seedでroute実効幅164対128とnumeric best-error応答を固定確認し、候補cohort数を凍結する。','- [Later] learned／inert／同費用random cohortのadd/replaceを比較し、成立後にState形成・分解とLogic/Ternary Routerへ進む。','', 'English: E044 passed the preregistered overall capacity-sensitivity gate: requested width 192 improved exact by 0.271 over width 64. The round-one/two realized width was capped at 164. The response was concentrated in routing (8/24 to 21/24); numeric stayed at 12/24 exact, with only one hard task improving from error 3 to 2. Family-level Holm-adjusted p-values were 0.0625.','', '简体中文：E044达到预注册的整体容量敏感性标准：请求宽度192相对64的exact提高0.271，但前两轮的实际宽度上限为164。变化集中在路由任务（8/24升至21/24）；数值任务维持12/24，仅一个困难任务的误差从3降至2。任务族层面的Holm校正p值为0.0625。','', '[事前計画](../results/E044-capacity-dose-response/PROTOCOL.md) / [生データ](../results/E044-capacity-dose-response/run/results.json) / [凍結設定](../results/E044-capacity-dose-response/run/frozen_manifest.json) / [監査](../results/E044-capacity-dose-response/run/audit_summary.json)']
report='\n'.join(lines)+'\n'; (ROOT/'docs/STAR-Bit-E044-capacity-dose-response.md').write_text(report); (HERE/'REPORT.md').write_text(report.replace('(../results/E044-capacity-dose-response/','(')); print(json.dumps({'capacity_gate_passed':summary['capacity_gate_passed'],'primary':summary['primary_span'],'verified':verified,'search_seconds':result['search_seconds']},indent=2))
