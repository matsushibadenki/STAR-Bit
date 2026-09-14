"""Audit and report E024 probe-utility pilot."""
import hashlib, itertools, json, math, os, sys
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E024-probe-utility-diversity'; OUT=HERE/'run'; E019=ROOT/'results/E019-function-space-genesis'; sys.path.insert(0,str(E019)); import search as base
REPORT_OUT=Path(os.environ.get('E024_REPORT_OUT','/tmp/E024-report.md')); AUDIT_OUT=Path(os.environ.get('E024_AUDIT_OUT','/tmp/E024-audit.json'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def evaluate(e,inputs):
    if e[0]=='input':return inputs[e[1]]
    value=base.lut_outputs(evaluate(e[3],inputs),evaluate(e[4],inputs))[e[2]];assert value==int(e[1]);return value
def signflip(d):
    observed=abs(np.mean(d));return sum(abs(np.mean([v*(1 if mask&(1<<i) else -1) for i,v in enumerate(d)]))>=observed-1e-12 for mask in range(2**len(d)))/(2**len(d))
def paired(d,rng):
    a=np.asarray(d,float);boot=a[rng.integers(0,len(a),(10000,len(a)))].mean(1);sd=a.std(ddof=1)
    return {'mean':float(a.mean()),'variance':float(a.var(ddof=1)),'ci95':np.quantile(boot,[.025,.975]).tolist(),'cohen_dz':None if sd==0 else float(a.mean()/sd),'exact_p':signflip(a),'differences':a.tolist()}
def mcnemar(a,b):
    x=sum(u and not v for u,v in zip(a,b));y=sum(v and not u for u,v in zip(a,b));n=x+y
    if not n:return 1.,x,y
    p=min(1.,2*sum(math.comb(n,k) for k in range(min(x,y)+1))/2**n);return p,x,y
def holm(ps):
    order=sorted(range(len(ps)),key=lambda i:ps[i]);out=[0.]*len(ps);run=0
    for rank,i in enumerate(order):run=max(run,min(1.,(len(ps)-rank)*ps[i]));out[i]=run
    return out
r=json.loads((OUT/'results.json').read_text());assert len(r['records'])==80
for name,expected in r['sources'].items():assert sha(ROOT/name)==expected
inputs,_=base.inputs_and_targets()
targets={
'eval_threshold2':sum(int(sum((row>>i)&1 for i in range(6))>=2)<<row for row in range(64)),
'eval_threshold4':sum(int(sum((row>>i)&1 for i in range(6))>=4)<<row for row in range(64)),
'eval_equal3':sum(int(sum(((row>>i)&1)<<i for i in range(3))==sum(((row>>(i+3))&1)<<i for i in range(3)))<<row for row in range(64)),
'eval_dual_mux_xor':sum((((((row>>1)&1) if ((row>>0)&1) else ((row>>2)&1))^(((row>>4)&1) if ((row>>3)&1) else ((row>>5)&1))))<<row for row in range(64))}
verified=0
for row in r['records']:
    if row['expression'] is not None:assert evaluate(row['expression'],inputs)==targets[row['task']];verified+=1
m=json.loads((OUT/'libraries.json').read_text());libstats={}
for name,items in m.items():
    sig=[int(x['signature']) for x in items];dist=[(a^b).bit_count() for a,b in itertools.combinations(sig,2)]
    libstats[name]={'mean_pairwise_hamming':float(np.mean(dist)),'mean_probe_utility':float(np.mean([x['utility'] for x in items])),'positive_utility_functions':sum(any(v>0 for v in x['probe_gains'].values()) for x in items)}
by={(x['seed'],x['task'],x['condition']):x for x in r['records']};seeds=r['settings']['seeds'];tasks=r['settings']['evaluation_tasks'];rng=np.random.default_rng(2024)
def counts(c):return [sum(by[s,t,c]['exact'] for t in tasks) for s in seeds]
primary=paired(np.asarray(counts('probe_utility_diverse'))-np.asarray(counts('random_matched')),rng);vs_freq=paired(np.asarray(counts('probe_utility_diverse'))-np.asarray(counts('frequency_cost')),rng);vs_none=paired(np.asarray(counts('probe_utility_diverse'))-np.asarray(counts('no_transfer')),rng)
tests=[]
for t in tasks:
    p,x,y=mcnemar([by[s,t,'probe_utility_diverse']['exact'] for s in seeds],[by[s,t,'random_matched']['exact'] for s in seeds]);tests.append({'task':t,'learned_only':x,'random_only':y,'p':p})
for item,p in zip(tests,holm([x['p'] for x in tests])):item['holm_p']=p
improved=sum(x['learned_only']>=2 for x in tests);learned_only=[by[s,t,'probe_utility_diverse'] for s in seeds for t in tasks if by[s,t,'probe_utility_diverse']['exact'] and not by[s,t,'random_matched']['exact']];all_used=bool(learned_only) and all(x['uses_transfer'] for x in learned_only);advance=primary['mean']>=.5 and improved>=2 and all_used
a=r['aggregate']; lines=['# E024：Probe Utility and Function Diversity pilot','',
'実行日：2026-09-14。E023で失敗したsource頻度・target errorに代えて、選定に使わない4 probe taskでの一段composition改善とtruth-signature多様性から8 Functionを選んだ。選定後に固定した別の4 evaluation task、4 seed、5条件の80探索で評価した。','',
'## 主要結果','',
'| condition | exact / 16 | 成功率平均 | 不偏分散 | threshold2 | threshold4 | equality3 | dual-mux XOR | transfer使用 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for c in ('no_transfer','frequency_cost','probe_utility','probe_utility_diverse','random_matched'):
    x=a[c];p=x['exact_by_task'];lines.append(f"| {c} | {sum(p.values())}/16 | {x['exact']['mean']:.4f} | {x['exact']['variance']:.4f} | {p['eval_threshold2']}/4 | {p['eval_threshold4']}/4 | {p['eval_equal3']}/4 | {p['eval_dual_mux_xor']}/4 | {x['uses_transfer']} |")
lines+=['','| paired比較（exact task / seed） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact p |','| --- | ---: | ---: | --- | ---: | ---: |']
for label,x in [('utility-diverse−random（primary）',primary),('utility-diverse−frequency',vs_freq),('utility-diverse−no transfer',vs_none)]:
    dz='NA' if x['cohen_dz'] is None else f"{x['cohen_dz']:.3f}";lines.append(f"| {label} | {x['mean']:+.3f} | {x['variance']:.3f} | [{x['ci95'][0]:.3f}, {x['ci95'][1]:.3f}] | {dz} | {x['exact_p']:.3f} |")
lines+=['',
'probe utilityだけは0/16、diversity併用は1/16、同費用randomは2/16、source頻度は1/16、移植なしは7/16だった。primary差は−0.25 task/seedで、事前の16-seed移行基準を満たさなかった。成功するまでseedを追加せず停止した。','',
'utility Libraryの平均probe scoreは%.3f、diversity併用も%.3fだった。平均pairwise Hamming距離はutility %.2f bitからdiverse %.2f bitへ増えたが、新規task探索へ移らなかった。したがって一段先のprobe改善と静的signature距離もcompositional potentialの十分な代理ではない。' % (libstats['probe_utility']['mean_probe_utility'],libstats['probe_utility_diverse']['mean_probe_utility'],libstats['probe_utility']['mean_pairwise_hamming'],libstats['probe_utility_diverse']['mean_pairwise_hamming']),'',
'固定Libraryはbeam 128の8枠を占める。全Library条件が移植なしより悪化したため、選ばれたFunctionが有用でない場合、保護枠と初期compositionが探索を阻害することも確認された。utility-diverseの唯一のexact解は移植Functionを使用したが、randomにも2解あり、肯定的な一般化証拠にはならない。','',
'## タスク軸','',
'threshold4は全条件0/4で、この予算では難しすぎた。equality3は移植なし4/4に対しutility-diverse 1/4、random 2/4。dual-mux XORは移植なしだけ1/4だった。今回の新規familyでは、構造自由度を加えること自体が精密数値・経路選択のどちらにも利益を与えなかった。','',
'## Roadmap','',
'- [Done] probe taskとevaluation taskを選定前に分離し、一段offspring utilityとsignature多様性を実装した。','- [Done] 4 seed、80探索、同費用random・frequency・no-transfer対照と平均・分散・CI・効果量・exact検定を保存した。','- [Done] 16-seed移行基準は不成立。全11 exact式を64入力で再検証した。','- [Next] 固定保護枠を廃止し、Moduleが実際に使われた場合だけ存続するusage-gated evictionを比較する。','- [Next] 一段lookaheadを止め、2〜3段のrollout utilityまたはState付き逐次utilityを小規模に診断する。','- [Later] cross-family transfer成立後にRouterへ統合し、load balance、固定random route、Expert交換、総費用を再評価する。','',
'English: One-step probe utility plus signature diversity did not transfer to four held-out task definitions. Utility-diverse solved 1/16 cases versus random 2/16 and no-transfer 7/16, so the preregistered expansion gate failed. Protected Library slots can actively harm search when Modules are not useful.','',
'简体中文：一步probe效用加签名多样性未能迁移到四个保留任务。效用加多样性成功1/16，随机库2/16，无迁移7/16，因此未达到扩展实验标准。无用模块占用固定保护槽会主动损害搜索。','',
'[事前計画](../results/E024-probe-utility-diversity/PROTOCOL.md) / [生データ](../results/E024-probe-utility-diversity/run/results.json) / [Library](../results/E024-probe-utility-diversity/run/libraries.json) / [監査要約](../results/E024-probe-utility-diversity/run/audit_summary.json)']
audit={'aggregate':a,'primary':primary,'vs_frequency':vs_freq,'vs_no_transfer':vs_none,'task_tests':tests,'library_stats':libstats,'solutions_verified':verified,'learned_only_successes':len(learned_only),'all_learned_only_use_transfer':all_used,'advance_threshold_met':advance};AUDIT_OUT.write_text(json.dumps(audit,indent=2));REPORT_OUT.write_text('\n'.join(lines)+'\n');print(json.dumps(audit,indent=2))
