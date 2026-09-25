"""Audit and report E039 capacity-versus-replacement mechanism pilot."""
import hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = Path('/Users/littlebuddha/Desktop/alias/STAR-Bit')
OUT = HERE / 'run'
sys.path.insert(0, str(ROOT / 'results/E019-function-space-genesis'))
import search as base

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module
e039 = load('e039_for_report', HERE / 'main.py')
def strict_json(text): return json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def evaluate(expression, inputs):
    if expression[0] == 'input': return inputs[expression[1]]
    signature = base.lut_outputs(evaluate(expression[3], inputs), evaluate(expression[4], inputs))[expression[2]]
    assert signature == int(expression[1]); return signature
def metric(values):
    values=np.asarray(values,float); return {'mean': None if len(values)==0 else float(values.mean()), 'unbiased_variance': None if len(values)<2 else float(values.var(ddof=1)), 'n':len(values)}
def signflip(values):
    values=np.asarray(values,float); observed=abs(values.mean()); return sum(abs(np.mean([v if mask&(1<<i) else -v for i,v in enumerate(values)]))>=observed-1e-12 for mask in range(1<<len(values)))/(1<<len(values))
def paired(values,rng):
    values=np.asarray(values,float); samples=values[rng.integers(0,len(values),(20000,len(values)))].mean(axis=1); sd=values.std(ddof=1)
    return {'mean':float(values.mean()),'unbiased_variance':float(values.var(ddof=1)),'ci95':np.quantile(samples,[.025,.975]).tolist(),'cohen_dz':None if sd==0 else float(values.mean()/sd),'exact_signflip_p':signflip(values),'differences':values.tolist()}
def holm(pvalues):
    order=sorted(range(len(pvalues)),key=lambda i:pvalues[i]); adjusted=[0.0]*len(pvalues); running=0.0
    for rank,index in enumerate(order): running=max(running,min(1.0,(len(pvalues)-rank)*pvalues[index])); adjusted[index]=float(running)
    return adjusted

result=strict_json((OUT/'results.json').read_text()); frozen=strict_json((OUT/'frozen_manifest.json').read_text())
seeds=list(range(1540,1546)); numeric='numeric_rotated_weight_ge6'; route='route_cross_implies'; tasks=[numeric,route]
conditions=['no_transfer','learned_replace','learned_add','inert_replace','inert_add','random_replace','random_add']
budgets={numeric:{'beam':192,'rounds':6},route:{'beam':128,'rounds':4}}
assert result['settings']=={'seeds':seeds,'tasks':tasks,'conditions':conditions,'budgets':budgets,'max_cost':16}
assert len(result['records'])==84 and len({(r['seed'],r['task'],r['condition']) for r in result['records']})==84
assert [strict_json(line) for line in (OUT/'progress.jsonl').read_text().splitlines()]==result['records']
for name,expected in result['sources'].items(): assert sha(ROOT/name)==expected,name
assert frozen['settings']==result['settings']; targets=e039.tasks_from_grammar(); assert frozen['targets']=={k:str(v) for k,v in targets.items()}
assert frozen['positive_class_counts']=={k:v.bit_count() for k,v in targets.items()}
admitted,row=e039.e028.frozen(); assert frozen['admitted']==strict_json(json.dumps(row))
assert len(frozen['random_matched'])==12; random_by={(x['seed'],x['task']):x for x in frozen['random_matched']}; assert len(random_by)==12 and len({x['signature'] for x in frozen['random_matched']})==12
inputs,_=base.inputs_and_targets()
for item in frozen['random_matched']:
    assert tuple(item['cost'])==admitted.cost(); assert e039.e023.evaluate(item['expression'],inputs)==int(item['signature']); assert e039.e023.expression_cost(item['expression'])==admitted.cost()
by={(r['seed'],r['task'],r['condition']):r for r in result['records']}; verified=0; first_round_verified=0; width_verified=0; collisions=0
for record in result['records']:
    assert record['beam']==budgets[record['task']]['beam'] and record['round_budget']==budgets[record['task']]['rounds']
    expected=[] if record['condition']=='no_transfer' else [random_by[record['seed'],record['task']]['signature']] if record['condition'].startswith('random_') else [str(admitted.signature)]
    assert record['library_signatures']==expected
    if record['condition'].startswith('inert_') or record['condition']=='no_transfer': assert not record['uses_transfer']
    if record['expression'] is not None: assert record['exact'] and evaluate(record['expression'],inputs)==targets[record['task']]; verified+=1
assert verified==sum(int(r['exact']) for r in result['records'])
for seed in seeds:
  for task in tasks:
    reference=by[seed,task,'no_transfer']
    for condition in conditions[1:]:
        record=by[seed,task,condition]; assert record['first_round_selected']==reference['first_round_selected']; assert record['best_error_history'][0]==reference['best_error_history'][0]; first_round_verified+=1
        if not record['injected_collision']:
            expected_width=reference['round_two_input_width']+(1 if condition.endswith('_add') else 0); assert record['round_two_input_width']==expected_width; width_verified+=1
        collisions+=int(record['injected_collision'])

summary={'by_task_condition':{},'primary':{},'secondary':{},'holm_secondary':{},'exploratory_error':{},'holm_exploratory_error':{},'capacity_gate_passed':False,'learned_semantic_gate_passed':False,'records_verified':84,'solutions_verified':verified,'first_round_pairs_verified':first_round_verified,'post_injection_widths_verified':width_verified,'injection_collisions':collisions,'analysis_source_hash':sha(HERE/'report.py')}
for task in tasks:
  summary['by_task_condition'][task]={}
  for condition in conditions:
    rows=[by[s,task,condition] for s in seeds]
    summary['by_task_condition'][task][condition]={'exact':metric([r['exact'] for r in rows]),'best_error':metric([r['best_error'] for r in rows]),'generated_unique_signatures':metric([r['generated_unique_signatures'] for r in rows]),'elapsed_seconds':metric([r['elapsed_seconds'] for r in rows]),'round_two_input_width':metric([r['round_two_input_width'] for r in rows if r['round_two_input_width'] is not None]),'solution_primitives':metric([r['primitives'] for r in rows if r['exact']]),'solution_routing_bits':metric([r['routing_bits'] for r in rows if r['exact']]),'solution_depth':metric([r['depth'] for r in rows if r['exact']]),'exact_uses_transfer':sum(bool(r['exact'] and r['uses_transfer']) for r in rows)}
rng=np.random.default_rng(2039)
def d(seed,task,left,right): return int(by[seed,task,left]['exact'])-int(by[seed,task,right]['exact'])
types=('learned','inert','random')
primary_values=[sum(d(seed,task,f'{kind}_add',f'{kind}_replace') for task in tasks for kind in types)/6 for seed in seeds]
summary['primary']=paired(primary_values,rng); summary['capacity_gate_passed']=bool(summary['primary']['mean']>=.20 and summary['primary']['exact_signflip_p']<=.05)
values={
 'numeric:pooled-add-minus-replace':[sum(d(s,numeric,f'{k}_add',f'{k}_replace') for k in types)/3 for s in seeds],
 'route:pooled-add-minus-replace':[sum(d(s,route,f'{k}_add',f'{k}_replace') for k in types)/3 for s in seeds],
 'pooled:learned-add-minus-inert-add':[sum(d(s,t,'learned_add','inert_add') for t in tasks)/2 for s in seeds],
 'pooled:learned-add-minus-random-add':[sum(d(s,t,'learned_add','random_add') for t in tasks)/2 for s in seeds],
}
for key,x in values.items(): summary['secondary'][key]=paired(x,rng)
summary['holm_secondary']={k:v for k,v in zip(values,holm([summary['secondary'][k]['exact_signflip_p'] for k in values]))}

# Exact recovery was at the numeric floor and near the route ceiling.  Preserve the
# preregistered exact analysis, then quantify best-error changes as explicitly
# exploratory diagnostics; negative add-minus-replace values favor capacity addition.
def error_d(seed,task,left,right): return int(by[seed,task,left]['best_error'])-int(by[seed,task,right]['best_error'])
error_values={
 'pooled:add-minus-replace':[sum(error_d(s,t,f'{k}_add',f'{k}_replace') for t in tasks for k in types)/6 for s in seeds],
 'numeric:pooled-add-minus-replace':[sum(error_d(s,numeric,f'{k}_add',f'{k}_replace') for k in types)/3 for s in seeds],
 'route:pooled-add-minus-replace':[sum(error_d(s,route,f'{k}_add',f'{k}_replace') for k in types)/3 for s in seeds],
 'numeric:learned-add-minus-replace':[error_d(s,numeric,'learned_add','learned_replace') for s in seeds],
 'numeric:inert-add-minus-replace':[error_d(s,numeric,'inert_add','inert_replace') for s in seeds],
 'numeric:random-add-minus-replace':[error_d(s,numeric,'random_add','random_replace') for s in seeds],
}
for key,x in error_values.items(): summary['exploratory_error'][key]=paired(x,rng)
summary['holm_exploratory_error']={k:v for k,v in zip(error_values,holm([summary['exploratory_error'][k]['exact_signflip_p'] for k in error_values]))}
summary['numeric_baseline_exact']=sum(int(by[s,numeric,'no_transfer']['exact']) for s in seeds)
summary['route_baseline_exact']=sum(int(by[s,route,'no_transfer']['exact']) for s in seeds)
learned_uses=sum(summary['by_task_condition'][t][c]['exact_uses_transfer'] for t in tasks for c in ('learned_replace','learned_add'))
summary['learned_success_uses']=learned_uses
# Compatibility smoke: replacement must reproduce E038's delayed learned behavior.
_, smoke_targets=e039.e038.e024.task_signatures(); smoke_target=smoke_targets['eval_dual_mux_xor']
old_smoke=e039.e038.timed_search(19001,smoke_target,admitted,64,2,'late_learned')
new_smoke=e039.scheduled_search(19001,smoke_target,admitted,64,2,'learned_replace')
smoke_keys=('exact','round','best_error_history','generated_unique_signatures','expression','uses_transfer','first_round_selected','injected_collision','slot_replaced_signature')
assert all(old_smoke[key]==new_smoke[key] for key in smoke_keys)
summary['replacement_smoke']={'seed':19001,'beam':64,'rounds':2,'matched_keys':list(smoke_keys)}
keys=('pooled:learned-add-minus-inert-add','pooled:learned-add-minus-random-add')
summary['learned_semantic_gate_passed']=bool(all(summary['secondary'][k]['mean']>0 and summary['holm_secondary'][k]<=.05 for k in keys) and learned_uses>0)
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False))

lines=['# E039：遅延投入の容量追加と同一幅置換を分離','', '実行日：2026-09-25。結果を見る前に定義した数値・経路選択2 taskを、新規6 seedで移植なしと、round 1後のlearned/inert/random各replace/add条件で比較した。計84探索。addはround 2だけbeam幅+1、replaceは選択済みbeamの最後の1枠を置換する。','', '| task | 条件 | exact/6 | exact平均 / 不偏分散 | best error平均 / 不偏分散 | Function使用成功/成功数 | 秒/探索平均 | 成功式 primitive / routing / depth平均 |','| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
for task in tasks:
  for condition in conditions:
    item=summary['by_task_condition'][task][condition]; count=round(item['exact']['mean']*6); cost='NA' if item['solution_primitives']['mean'] is None else f"{item['solution_primitives']['mean']:.2f} / {item['solution_routing_bits']['mean']:.2f} / {item['solution_depth']['mean']:.2f}"
    lines.append(f"| {task} | {condition} | {count}/6 | {item['exact']['mean']:.4f} / {item['exact']['unbiased_variance']:.4f} | {item['best_error']['mean']:.3f} / {item['best_error']['unbiased_variance']:.3f} | {item['exact_uses_transfer']}/{count} | {item['elapsed_seconds']['mean']:.2f} | {cost} |")
p=summary['primary']; effect='NA' if p['cohen_dz'] is None else f"{p['cohen_dz']:.3f}"
lines += ['', '## 主指標：全Module種・task平均のadd−replace exact差','',f"平均差 {p['mean']:+.4f}、不偏分散 {p['unbiased_variance']:.4f}、bootstrap 95% CI [{p['ci95'][0]:.4f}, {p['ci95'][1]:.4f}]、Cohen dz {effect}、exact p={p['exact_signflip_p']:.4f}。容量保持pilot基準は"+('達成。' if summary['capacity_gate_passed'] else '未達。'),'','## 副次比較（Holm補正）','', '| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for key,item in summary['secondary'].items():
    effect='NA' if item['cohen_dz'] is None else f"{item['cohen_dz']:.3f}"; lines.append(f"| {key} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {effect} | {item['exact_signflip_p']:.4f} | {summary['holm_secondary'][key]:.4f} |")
lines += ['', '## 探索的診断：best errorのadd−replace差（負がadd有利）','', 'exactはnumericで床、routeでほぼ天井だったため、事前指定した主判定を置き換えずbest errorを探索的に解析した。','', '| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for key,item in summary['exploratory_error'].items():
    effect='NA' if item['cohen_dz'] is None else f"{item['cohen_dz']:.3f}"; lines.append(f"| {key} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {effect} | {item['exact_signflip_p']:.4f} | {summary['holm_exploratory_error'][key]:.4f} |")
lines += ['',f"移植なしexactはnumeric {summary['numeric_baseline_exact']}/6、route {summary['route_baseline_exact']}/6。numericではlearned/inertの同一幅置換が全seedでbest errorを1悪化させ、容量追加は移植なしのerror=1を維持した。これは意味学習ではなく、beam枠を奪うことによる探索容量損失を支持する探索的結果である。randomはsignature衝突があり解釈を弱める。",'', '学習Function固有基準は'+('達成。' if summary['learned_semantic_gate_passed'] else '未達。'),f"初回beam一致{first_round_verified}/72、post-injection幅検証{width_verified}件、signature衝突{collisions}件。numericの実効round 2幅はreplace 164、非衝突add 165（設定上限192）；routeはreplace 128、非衝突add 129。設定beam未満の実効幅となった点はprotocol deviationとして記録する。",'',f"全{verified} exact式を64入力で再評価した。84 record、strict JSON、progress、source hash、12 random FunctionとE038 replacement互換smokeを監査。探索CPU時間合計{result['search_seconds']:.1f}秒。物理ゲート数や推論速度は未測定。",'', '## Roadmap','', '- [Done] 新taskで容量追加と同一幅置換をlearned/inert/randomに分けて評価した。','- [Next] 衝突を除外して実効beam幅を厳密に揃え、numericの到達可能性を上げた新taskで容量損失を独立検証する。','- [Later] State形成・分解、負荷分散Router、固定random経路、Expert交換へ進む。','', 'English: E039 prospectively separates temporary beam-capacity addition from fixed-width replacement. The preregistered exact endpoint was uninformative because the numeric task was at floor and the route task near ceiling. Exploratory best-error results show that learned and inert replacement both harmed numeric search, while addition preserved the baseline; no learned semantic advantage appeared.','', '简体中文：E039以前瞻方式区分临时增加beam容量与固定宽度替换。预注册的exact指标因数值任务触底、路径任务接近天花板而信息不足；探索性best-error结果显示，学习模块与惰性模块的固定宽度替换都会损害数值搜索，而增加容量保持了基线，未发现学习语义优势。','', '[事前計画](../results/E039-capacity-admission/PROTOCOL.md) / [生データ](../results/E039-capacity-admission/run/results.json) / [凍結設定](../results/E039-capacity-admission/run/frozen_manifest.json) / [監査](../results/E039-capacity-admission/run/audit_summary.json)']
report='\n'.join(lines)+'\n'; (ROOT/'docs/STAR-Bit-E039-capacity-admission.md').write_text(report); (HERE/'REPORT.md').write_text(report.replace('(../results/E039-capacity-admission/','('))
print(json.dumps({'capacity_gate_passed':summary['capacity_gate_passed'],'learned_semantic_gate_passed':summary['learned_semantic_gate_passed'],'verified':verified,'search_seconds':result['search_seconds']},indent=2))
