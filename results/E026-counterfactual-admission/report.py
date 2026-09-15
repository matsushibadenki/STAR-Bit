"""Audit and report E026 counterfactual admission pilot."""
import hashlib,json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit');HERE=Path(__file__).resolve().parent;OUT=HERE/'run';E019=ROOT/'results/E019-function-space-genesis';sys.path.insert(0,str(E019));import search as base
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def targets():
 d={};f={'eval_threshold2':lambda b:sum(b)>=2,'eval_threshold4':lambda b:sum(b)>=4,'eval_equal3':lambda b:sum(b[i]<<i for i in range(3))==sum(b[i+3]<<i for i in range(3)),'eval_dual_mux_xor':lambda b:(b[1] if b[0] else b[2])^(b[4] if b[3] else b[5])}
 for name,fn in f.items():
  s=0
  for row in range(64):s|=int(fn([(row>>i)&1 for i in range(6)]))<<row
  d[name]=s
 return d
def evaluate(e,inputs):
 if e[0]=='input':return inputs[e[1]]
 v=base.lut_outputs(evaluate(e[3],inputs),evaluate(e[4],inputs))[e[2]];assert v==int(e[1]);return v
def signflip(d):
 o=abs(np.mean(d));return sum(abs(np.mean([v*(1 if mask&(1<<i) else -1) for i,v in enumerate(d)]))>=o-1e-12 for mask in range(2**len(d)))/(2**len(d))
def paired(d,rng):
 a=np.asarray(d,float);boot=a[rng.integers(0,len(a),(10000,len(a)))].mean(1);sd=a.std(ddof=1);return {'mean':float(a.mean()),'variance':float(a.var(ddof=1)),'ci95':np.quantile(boot,[.025,.975]).tolist(),'cohen_dz':None if sd==0 else float(a.mean()/sd),'exact_p':signflip(a),'differences':a.tolist()}
def mcnemar(a,b):
 x=sum(u and not v for u,v in zip(a,b));y=sum(v and not u for u,v in zip(a,b));n=x+y
 return (1.,x,y) if not n else (min(1.,2*sum(math.comb(n,k) for k in range(min(x,y)+1))/2**n),x,y)
def holm(ps):
 order=sorted(range(len(ps)),key=lambda i:ps[i]);out=[0.]*len(ps);run=0
 for rank,i in enumerate(order):run=max(run,min(1.,(len(ps)-rank)*ps[i]));out[i]=run
 return out
r=json.loads((OUT/'results.json').read_text());assert len(r['records'])==64
for name,expected in r['sources'].items():assert sha(ROOT/name)==expected
inputs,_=base.inputs_and_targets();target=targets();verified=0
for row in r['records']:
 if row['expression'] is not None:assert evaluate(row['expression'],inputs)==target[row['task']];verified+=1
admission=json.loads((OUT/'admission.json').read_text());selected=set(admission['selected_signatures']);assert len(selected)==r['settings']['admitted_count']==1
admitted_rows=[x for x in admission['candidates'] if x['admitted']];assert len(admitted_rows)==1 and all(x['net']>0 and x['positive_tasks']>=2 for x in admitted_rows)
by={(x['seed'],x['task'],x['condition']):x for x in r['records']};seeds=r['settings']['seeds'];tasks=r['settings']['tasks'];rng=np.random.default_rng(2026)
def counts(c):return [sum(by[s,t,c]['exact'] for t in tasks) for s in seeds]
primary=paired(np.asarray(counts('counterfactual'))-np.asarray(counts('legacy_all8')),rng);vs_none=paired(np.asarray(counts('counterfactual'))-np.asarray(counts('no_transfer')),rng);vs_random=paired(np.asarray(counts('counterfactual'))-np.asarray(counts('random_matched')),rng)
tests=[]
for t in tasks:
 p,x,y=mcnemar([by[s,t,'counterfactual']['exact'] for s in seeds],[by[s,t,'legacy_all8']['exact'] for s in seeds]);tests.append({'task':t,'counterfactual_only':x,'legacy_only':y,'p':p})
for x,p in zip(tests,holm([x['p'] for x in tests])):x['holm_p']=p
a=r['aggregate'];viable=primary['mean']>=.5 and np.mean(counts('counterfactual'))>=np.mean(counts('no_transfer'))-.25 and all(x['net']>0 for x in admitted_rows);transfer_gate=vs_random['mean']>=.5
chosen=admitted_rows[0]
lines=['# E026：Counterfactual Module Admission pilot','',
'実行日：2026-09-15。45 source Functionを、signature-stableな同一tie-breakによる3-round probe探索のwith/without差で評価した。4 probeのうち2つ以上を改善し、net error減少が正の候補だけを採用して、固定保護なしで新規4 seedを評価した。','',
'## Admission結果','',
f"45候補中1 Functionだけを採用した。signature `{chosen['signature']}`、2 primitives、12 routing bits、depth 2。probe error差はmajority +1、exactly-two +2、less-than 0、mixed Boolean 0で、net +3だった。評価taskはadmissionに使っていない。",'',
'## 主要結果','',
'| condition | exact / 16 | 成功率平均 | 不偏分散 | threshold2 | threshold4 | equality3 | dual-mux XOR | transfer使用 | best error平均 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for c in ('no_transfer','legacy_all8','counterfactual','random_matched'):
 x=a[c];p=x['exact_by_task'];lines.append(f"| {c} | {sum(p.values())}/16 | {x['exact']['mean']:.4f} | {x['exact']['variance']:.4f} | {p['eval_threshold2']}/4 | {p['eval_threshold4']}/4 | {p['eval_equal3']}/4 | {p['eval_dual_mux_xor']}/4 | {x['uses_transfer']} | {x['best_error']['mean']:.4f} |")
lines+=['','| paired比較（exact task / seed） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact p |','| --- | ---: | ---: | --- | ---: | ---: |']
for label,x in [('counterfactual−legacy（primary）',primary),('counterfactual−no transfer',vs_none),('counterfactual−random matched',vs_random)]:
 dz='NA' if x['cohen_dz'] is None else f"{x['cohen_dz']:.3f}";lines.append(f"| {label} | {x['mean']:+.3f} | {x['variance']:.3f} | [{x['ci95'][0]:.3f}, {x['ci95'][1]:.3f}] | {dz} | {x['exact_p']:.3f} |")
lines+=['',
'counterfactual admissionはlegacy 2/16から5/16へ改善し、+0.75 task/seedだった。移植なし4/16も下回らず、事前登録した探索阻害mitigation基準を満たした。4 seedのCIは0を含みexact p=0.5なので、確証的な性能改善ではない。','',
'random matchedは4/16でcounterfactualとの差は+0.25に留まり、transfer主張の+0.5基準は未達だった。追加のdual-mux XOR解1件は採用Functionを実際に使用したが単発である。今回支持されるのは、反実仮想screeningが有害な一括admissionを避けたことまでで、task横断Conceptの有効性ではない。','',
'legacyのbest error平均5.1875に対しcounterfactualは1.9375、no transferは2.0625だった。45→1 Functionへの選別が探索軌跡の破壊を抑えた。tie-breakをsignatureごとに決定したため、Library追加で既存候補の乱数順位がずれる問題も除いた。全15 exact式を64入力で再評価した。','',
'タスク別ではequality3がcounterfactual 4/4、legacy 2/4、dual-mux XORが1/4対0/4。threshold2/4は全条件0/4で、この予算では構造自由度の効果を評価できない。','',
'## Roadmap','',
'- [Done] with/without Moduleのpaired probe rolloutとsignature-stable tie-breakを実装した。','- [Done] 45候補を評価し、事前規則で1 Functionだけを通常beamへadmissionした。','- [Done] 新規4 seed・64探索、平均・不偏分散・bootstrap CI・効果量・exact検定・Holm補正、全15式を保存・監査した。','- [Done] legacy一括投入の阻害は緩和したが、random matchedに対するtransfer基準は未達。','- [Next] 同じadmission規則を新規16 seedで独立確認し、randomとの差ではなくまずno-transfer非劣性とlegacy改善を確認する。','- [Next] probeを2〜3段rolloutへ伸ばす場合は、追加計算量と採用安定性を先に測る。','- [Later] cross-task利益が確認された後にState付きFunctionとRouterへ統合する。','',
'English: Counterfactual probe admission selected 1 of 45 Functions and improved held-out discovery from legacy 2/16 to 5/16, versus no-transfer and random-matched 4/16 each. The mitigation criterion passed, but the random-control transfer threshold did not; this supports safe admission, not cross-task conceptual transfer.','',
'简体中文：反事实probe准入从45个函数中只选择1个，使成功数从旧方案2/16提高到5/16；无迁移和随机匹配均为4/16。阻害缓解标准达成，但相对随机对照的迁移标准未达成，因此只支持安全准入，不支持跨任务概念迁移。','',
'[事前計画](../results/E026-counterfactual-admission/PROTOCOL.md) / [生データ](../results/E026-counterfactual-admission/run/results.json) / [Admission](../results/E026-counterfactual-admission/run/admission.json) / [監査要約](../results/E026-counterfactual-admission/run/audit_summary.json)']
audit={'aggregate':a,'primary':primary,'vs_no_transfer':vs_none,'vs_random':vs_random,'task_tests':tests,'admitted_count':len(selected),'admitted':chosen,'solutions_verified':verified,'mitigation_threshold_met':viable,'transfer_threshold_met':transfer_gate};(OUT/'audit_summary.json').write_text(json.dumps(audit,indent=2));text='\n'.join(lines)+'\n';(HERE/'REPORT.md').write_text(text);(ROOT/'docs/STAR-Bit-E026-counterfactual-admission.md').write_text(text);print(json.dumps(audit,indent=2))
