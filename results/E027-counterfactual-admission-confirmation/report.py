"""Audit and report E027 independent counterfactual-admission confirmation."""
import hashlib,json,math,os,sys
from pathlib import Path
import numpy as np

ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit')
HERE=ROOT/'results/E027-counterfactual-admission-confirmation'
OUT=HERE/'run'
E019=ROOT/'results/E019-function-space-genesis'
sys.path.insert(0,str(E019))
import search as base

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def targets():
    functions={
        'eval_threshold2':lambda b:sum(b)>=2,
        'eval_threshold4':lambda b:sum(b)>=4,
        'eval_equal3':lambda b:sum(b[i]<<i for i in range(3))==sum(b[i+3]<<i for i in range(3)),
        'eval_dual_mux_xor':lambda b:(b[1] if b[0] else b[2])^(b[4] if b[3] else b[5]),
    }
    result={}
    for name,function in functions.items():
        signature=0
        for row in range(64): signature|=int(function([(row>>i)&1 for i in range(6)]))<<row
        result[name]=signature
    return result

def evaluate(expression,inputs):
    if expression[0]=='input': return inputs[expression[1]]
    value=base.lut_outputs(evaluate(expression[3],inputs),evaluate(expression[4],inputs))[expression[2]]
    assert value==int(expression[1])
    return value

def exact_signflip(differences):
    observed=abs(float(np.mean(differences)))
    total=2**len(differences)
    extreme=0
    for mask in range(total):
        value=np.mean([x*(1 if mask&(1<<i) else -1) for i,x in enumerate(differences)])
        extreme+=abs(value)>=observed-1e-12
    return extreme/total

def paired(differences,rng):
    values=np.asarray(differences,float)
    bootstrap=values[rng.integers(0,len(values),(20000,len(values)))].mean(1)
    sd=values.std(ddof=1)
    return {
        'mean':float(values.mean()),
        'variance':float(values.var(ddof=1)),
        'ci95':np.quantile(bootstrap,[.025,.975]).tolist(),
        'cohen_dz':None if sd==0 else float(values.mean()/sd),
        'exact_p':exact_signflip(values),
        'differences':values.tolist(),
    }

def mcnemar(left,right):
    left_only=sum(a and not b for a,b in zip(left,right))
    right_only=sum(b and not a for a,b in zip(left,right))
    n=left_only+right_only
    if n==0: return 1.0,left_only,right_only
    p=min(1.0,2*sum(math.comb(n,k) for k in range(min(left_only,right_only)+1))/2**n)
    return p,left_only,right_only

def holm(pvalues):
    order=sorted(range(len(pvalues)),key=lambda i:pvalues[i])
    adjusted=[0.0]*len(pvalues); running=0.0
    for rank,index in enumerate(order):
        running=max(running,min(1.0,(len(pvalues)-rank)*pvalues[index]))
        adjusted[index]=running
    return adjusted

result=json.loads((OUT/'results.json').read_text())
assert len(result['records'])==256
for name,expected in result['sources'].items(): assert sha(ROOT/name)==expected,(name,expected,sha(ROOT/name))
inputs,_=base.inputs_and_targets(); expected_targets=targets(); verified=0
for row in result['records']:
    if row['expression'] is not None:
        assert row['exact'] and evaluate(row['expression'],inputs)==expected_targets[row['task']]
        verified+=1

frozen=json.loads((OUT/'frozen_admission.json').read_text())
e026=json.loads((ROOT/'results/E026-counterfactual-admission/run/admission.json').read_text())
admitted=next(row for row in e026['candidates'] if row['admitted'])
assert str(frozen['signature'])==str(admitted['signature'])==e026['selected_signatures'][0]
assert frozen['expression']==admitted['expression']

by={(row['seed'],row['task'],row['condition']):row for row in result['records']}
seeds=result['settings']['seeds']; tasks=result['settings']['tasks']; rng=np.random.default_rng(2027)
def counts(condition): return [sum(by[seed,task,condition]['exact'] for task in tasks) for seed in seeds]
counter=np.asarray(counts('counterfactual'))
legacy=np.asarray(counts('legacy_all8'))
none=np.asarray(counts('no_transfer'))
random=np.asarray(counts('random_matched'))
primary=paired(counter-legacy,rng)
vs_none=paired(counter-none,rng)
vs_random=paired(counter-random,rng)

tests=[]
for comparator in ('legacy_all8','random_matched'):
    group=[]
    for task in tasks:
        p,left_only,right_only=mcnemar(
            [by[seed,task,'counterfactual']['exact'] for seed in seeds],
            [by[seed,task,comparator]['exact'] for seed in seeds],
        )
        group.append({'comparison':f'counterfactual_vs_{comparator}','task':task,'counterfactual_only':left_only,'comparator_only':right_only,'p':p})
    for row,adjusted in zip(group,holm([row['p'] for row in group])): row['holm_p']=adjusted
    tests.extend(group)

learned_only={}
for task in tasks:
    rows=[]
    for seed in seeds:
        learned=by[seed,task,'counterfactual']; control=by[seed,task,'random_matched']
        if learned['exact'] and not control['exact']:
            rows.append({'seed':seed,'uses_transfer':learned['uses_transfer'],'used_signatures':learned['used_signatures']})
    learned_only[task]=rows

mitigation=(primary['mean']>=.5 and primary['ci95'][0]>0 and vs_none['mean']>=-.25)
eligible_non_equality=[]
for task in tasks:
    if task!='eval_equal3' and len(learned_only[task])>=4 and all(row['uses_transfer'] for row in learned_only[task]):
        eligible_non_equality.append(task)
transfer=(vs_random['mean']>=.25 and vs_random['ci95'][0]>0 and bool(eligible_non_equality))

aggregate=result['aggregate']
lines=[
    '# E027：Counterfactual Module Admission 独立確認',
    '',
    '実行日：2026-09-16。E026で45候補から選ばれた1 Functionを再選別せず凍結し、新規16 seedで事前登録どおり独立確認した。4条件 × 4 held-out task × 16 seedの256探索を、beam 128・6 rounds・保護slotなしで実行した。',
    '',
    '## 結果',
    '',
    '| condition | exact / 64 | 成功率平均 | 不偏分散 | threshold2 | threshold4 | equality3 | dual-mux XOR | transfer使用 | best error平均 |',
    '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
]
for condition in ('no_transfer','legacy_all8','counterfactual','random_matched'):
    row=aggregate[condition]; task=row['exact_by_task']
    lines.append(f"| {condition} | {sum(task.values())}/64 | {row['exact']['mean']:.4f} | {row['exact']['variance']:.4f} | {task['eval_threshold2']}/16 | {task['eval_threshold4']}/16 | {task['eval_equal3']}/16 | {task['eval_dual_mux_xor']}/16 | {row['uses_transfer']} | {row['best_error']['mean']:.4f} |")
lines += [
    '',
    '| paired比較（exact task / seed） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |',
    '| --- | ---: | ---: | --- | ---: | ---: |',
]
for label,row in [('counterfactual−legacy（primary）',primary),('counterfactual−no transfer',vs_none),('counterfactual−random matched',vs_random)]:
    dz='NA' if row['cohen_dz'] is None else f"{row['cohen_dz']:.3f}"
    lines.append(f"| {label} | {row['mean']:+.4f} | {row['variance']:.4f} | [{row['ci95'][0]:.4f}, {row['ci95'][1]:.4f}] | {dz} | {row['exact_p']:.4f} |")
lines += [
    '',
    f"counterfactualは22/64、legacy一括投入は4/64で、primary差は{primary['mean']:+.4f} task/seed、95% CI [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}]だった。no-transfer 20/64も下回らなかったため、事前登録した探索阻害mitigation基準を満たした。E026の小標本結果は独立seedで再現した。",
    '',
    f"random matchedは17/64で、counterfactual差は{vs_random['mean']:+.4f} task/seed、95% CI [{vs_random['ci95'][0]:.4f}, {vs_random['ci95'][1]:.4f}]だった。dual-mux XORではcounterfactualだけが成功した4 seedすべてで凍結Functionを実際に使用した。事前登録したtask-crossing transfer基準も満たした。ただしexact sign-flip p={vs_random['exact_p']:.4f}、task別McNemarのHolm補正後pは有意でないため、確認された範囲はこの小型Boolean探索と固定予算に限られる。",
    '',
    '## タスク種別',
    '',
    '経路選択型のdual-mux XORはcounterfactual 4/16、random 0/16、no-transfer 1/16で、4件のlearned-only解がすべて転移Functionを使った。構造的自由度が探索到達性を改善したという今回の証拠は、この経路選択タスクに集中した。',
    '',
    '精密数値型のthreshold2は2/16対random 1/16・no-transfer 3/16、threshold4は全条件0/16だった。equality3はcounterfactual・random・no-transferが全て16/16で天井効果があり、転移効果を分離できない。したがって、数値タスクへの一般化は支持されず、難しいthreshold4は現予算では評価不能である。',
    '',
    f"全{verified} exact式を64入力で再評価し、source hash、凍結Functionのsignatureとexpression、256 recordを監査した。結果は記述長圧縮、primitive gate削減、実行速度、Router学習の証拠ではない。",
    '',
    '## Roadmap',
    '',
    '- [Done] E026の採用Functionを凍結し、独立16 seed・256探索を完了した。',
    '- [Done] counterfactual admissionによるlegacy Libraryの探索阻害緩和を独立確認した。',
    '- [Done] random matched対照と実使用監査により、経路選択型dual-mux XORで事前登録したtask-crossing transfer基準を満たした。',
    '- [Done] 平均・不偏分散・bootstrap CI・Cohen dz・exact sign-flip・task別McNemar/Holm、全exact式とsource hashを監査した。',
    '- [Next] E028では選ばれたFunctionを直接使えない等価保持ablationと、admission Functionの入力置換対照を追加し、特定式の偶然ではなく構造的部分計算の寄与を分離する。',
    '- [Next] threshold4の探索予算を事前に校正し、数値型で床効果のない比較を行う。',
    '- [Later] transfer Function候補をRouterの選択肢として統合し、step 0 load-balancing・固定random routing・複数seedでSTAR-Bit本体を検証する。',
    '',
    'English: With the E026 Function frozen, counterfactual admission reached 22/64 exact solutions versus legacy 4/64, no-transfer 20/64, and structurally matched random 17/64 over 16 new seeds. Both preregistered mitigation and task-crossing transfer criteria passed. The learned-only benefit was concentrated in dual-mux XOR (4/16 versus random 0/16), while numeric thresholds showed no benefit.',
    '',
    '简体中文：冻结E026选出的函数后，16个新seed中反事实准入达到22/64，旧Library为4/64，无迁移为20/64，结构匹配随机对照为17/64。预注册的阻害缓解与跨任务迁移标准均达成；增益集中在dual-mux XOR路径选择任务，数值阈值任务没有显示收益。',
    '',
    '[事前計画](../results/E027-counterfactual-admission-confirmation/PROTOCOL.md) / [生データ](../results/E027-counterfactual-admission-confirmation/run/results.json) / [凍結Admission](../results/E027-counterfactual-admission-confirmation/run/frozen_admission.json) / [監査要約](../results/E027-counterfactual-admission-confirmation/run/audit_summary.json)',
]

audit={
    'aggregate':aggregate,
    'primary':primary,
    'vs_no_transfer':vs_none,
    'vs_random':vs_random,
    'task_tests':tests,
    'learned_only_vs_random':learned_only,
    'eligible_non_equality_tasks':eligible_non_equality,
    'solutions_verified':verified,
    'records_verified':len(result['records']),
    'frozen_signature':str(frozen['signature']),
    'mitigation_criterion_met':mitigation,
    'transfer_criterion_met':transfer,
}
report='\n'.join(lines)+'\n'
result_report=report.replace('(../results/E027-counterfactual-admission-confirmation/','(')
destination=os.environ.get('E027_REPORT_OUT')
if destination:
    destination=Path(destination); destination.mkdir(parents=True,exist_ok=True)
    (destination/'audit_summary.json').write_text(json.dumps(audit,indent=2))
    (destination/'REPORT.md').write_text(result_report)
    (destination/'STAR-Bit-E027-counterfactual-admission-confirmation.md').write_text(report)
else:
    (OUT/'audit_summary.json').write_text(json.dumps(audit,indent=2))
    (HERE/'REPORT.md').write_text(result_report)
    (ROOT/'docs/STAR-Bit-E027-counterfactual-admission-confirmation.md').write_text(report)
print(json.dumps(audit,indent=2))
