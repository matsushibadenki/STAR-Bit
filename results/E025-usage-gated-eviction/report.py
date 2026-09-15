"""Audit and report E025 usage-gated eviction pilot."""
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
r=json.loads((OUT/'results.json').read_text());assert len(r['records'])==80
for name,expected in r['sources'].items():assert sha(ROOT/name)==expected
inputs,_=base.inputs_and_targets();target=targets();verified=0
for row in r['records']:
 if row['expression'] is not None:assert evaluate(row['expression'],inputs)==target[row['task']];verified+=1
by={(x['seed'],x['task'],x['condition']):x for x in r['records']};seeds=r['settings']['seeds'];tasks=r['settings']['tasks'];rng=np.random.default_rng(2025)
def counts(c):return [sum(by[s,t,c]['exact'] for t in tasks) for s in seeds]
primary=paired(np.asarray(counts('usage_gated'))-np.asarray(counts('fixed_protected')),rng);vs_none=paired(np.asarray(counts('usage_gated'))-np.asarray(counts('no_transfer')),rng);vs_unprotected=paired(np.asarray(counts('usage_gated'))-np.asarray(counts('unprotected')),rng);vs_random=paired(np.asarray(counts('usage_gated'))-np.asarray(counts('random_usage_gated')),rng)
tests=[]
for t in tasks:
 p,x,y=mcnemar([by[s,t,'usage_gated']['exact'] for s in seeds],[by[s,t,'fixed_protected']['exact'] for s in seeds]);tests.append({'task':t,'usage_only':x,'fixed_only':y,'p':p})
for x,p in zip(tests,holm([x['p'] for x in tests])):x['holm_p']=p
a=r['aggregate'];viable=primary['mean']>=.5 and np.mean(counts('usage_gated'))>=np.mean(counts('no_transfer'))-.25 and a['usage_gated']['active_round3']['mean']<=4
lines=['# E025：Usage-gated Module Eviction pilot','',
'実行日：2026-09-15。E024の8 Functionを初期投入し、top-128 childのtarget errorを両親より改善したときだけ保護期限を更新するusage-gated evictionを、固定保護・無保護・同費用random・移植なしと新規4 seedで比較した。','',
'## 主要結果','',
'| condition | exact / 16 | 成功率平均 | 不偏分散 | threshold2 | threshold4 | equality3 | dual-mux XOR | round 3保護数 | 最終保護数 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for c in ('no_transfer','fixed_protected','unprotected','usage_gated','random_usage_gated'):
 x=a[c];p=x['exact_by_task'];lines.append(f"| {c} | {sum(p.values())}/16 | {x['exact']['mean']:.4f} | {x['exact']['variance']:.4f} | {p['eval_threshold2']}/4 | {p['eval_threshold4']}/4 | {p['eval_equal3']}/4 | {p['eval_dual_mux_xor']}/4 | {x['active_round3']['mean']:.2f} | {x['final_active']['mean']:.2f} |")
lines+=['','| paired比較（exact task / seed） | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact p |','| --- | ---: | ---: | --- | ---: | ---: |']
for label,x in [('usage−fixed（primary）',primary),('usage−no transfer',vs_none),('usage−unprotected',vs_unprotected),('usage−random gated',vs_random)]:
 dz='NA' if x['cohen_dz'] is None else f"{x['cohen_dz']:.3f}";lines.append(f"| {label} | {x['mean']:+.3f} | {x['variance']:.3f} | [{x['ci95'][0]:.3f}, {x['ci95'][1]:.3f}] | {dz} | {x['exact_p']:.3f} |")
lines+=['',
'usage-gated、fixed、unprotectedはいずれも2/16で、primary差は0だった。移植なしは5/16、random usage-gatedは1/16。事前登録したmitigation基準は不成立で、16-seedへ拡張しない。','',
'usage-gatedではround 3時点でも平均8/8 Functionが保護され、最終的には3.25まで減った。全Library Functionが少なくとも一度「改善childの親」になったため、現在のcausal-use判定は識別力がない。遅いevictionは初期3 roundで既に変わったbeam軌跡を回復できなかった。','',
'無保護条件もfixedと同じ2/16だったことから、E024の悪化は固定slotだけでは説明できない。初期Libraryとの大量compositionと、それに伴うtarget quota・credit・乱数選択の変化自体が探索を別のbasinへ移している。Moduleの形成と分解は「使われたか」ではなく、反実仮想的にそのModuleを除いたときの改善差で判断する必要がある。','',
'精密数値側のthreshold2/4は全Library条件0、経路選択を複合したdual-mux XORもLibrary条件0だった。equality3だけ2/4であり、今回も構造追加による一般的補償は確認できない。全12 exact式を64入力で再評価した。','',
'## Roadmap','',
'- [Done] fixed protection、unprotected admission、usage-gated learned、usage-gated random、no-transferを同一予算で比較した。','- [Done] 新規4 seed・80探索、平均・不偏分散・bootstrap CI・効果量・exact検定・Holm補正を保存した。','- [Done] usage判定が8/8 Functionを更新し、evictionが探索性能を回復しない負の結果を確認した。','- [Done] E026でpaired rolloutによるwith/without Moduleの反実仮想admissionとsignature-stable tie-breakを実装した。','- [Next] E026のadmission規則を新規16 seedで独立確認する。','- [Later] 独立確認後にState付きmulti-step utilityへ進み、その後Router統合を再検討する。','',
'English: Usage-gated eviction did not mitigate the fixed-Library harm. Usage-gated, fixed, and unprotected learned admission each solved 2/16 cases versus no-transfer 5/16. Every imported Function produced at least one locally improving child, so the causal-use rule had no selectivity and eviction came too late.','',
'简体中文：按使用情况退役未能缓解固定函数库的负面影响。使用门控、固定保护和无保护学习库均成功2/16，而无迁移成功5/16。每个导入函数都至少生成过一个局部改进子代，因此当前使用判定没有区分力，退役发生得太晚。','',
'[事前計画](../results/E025-usage-gated-eviction/PROTOCOL.md) / [生データ](../results/E025-usage-gated-eviction/run/results.json) / [Library](../results/E025-usage-gated-eviction/run/library.json) / [監査要約](../results/E025-usage-gated-eviction/run/audit_summary.json)']
audit={'aggregate':a,'primary':primary,'vs_no_transfer':vs_none,'vs_unprotected':vs_unprotected,'vs_random':vs_random,'task_tests':tests,'solutions_verified':verified,'viable_threshold_met':viable};(OUT/'audit_summary.json').write_text(json.dumps(audit,indent=2));text='\n'.join(lines)+'\n';(HERE/'REPORT.md').write_text(text);(ROOT/'docs/STAR-Bit-E025-usage-gated-eviction.md').write_text(text);print(json.dumps(audit,indent=2))
