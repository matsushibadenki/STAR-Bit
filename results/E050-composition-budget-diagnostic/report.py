import json,hashlib,itertools,importlib.util
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E050-composition-budget-diagnostic'; out=HERE/'run'
r=json.loads((out/'results.json').read_text()); rows=r['records']; assert r['complete'] and len(rows)==96
assert [json.loads(s) for s in (out/'progress.jsonl').read_text().splitlines()]==rows
for name,h in r['sources'].items(): assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
assert len({(x['seed'],x['task'],x['condition']) for x in rows})==96
for x in rows:
 assert x['pairs']==1536
 assert sum(a+b+1<=16 for a in x['source_costs'] for b in x['beam_costs'])==x['feasible_pairs']
 assert x['best_child_error']>=x['unconstrained_best_child_error']
 assert x['legal_unique_children']<=x['unique_children']
spec=importlib.util.spec_from_file_location('e050_main',HERE/'main.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
manifest=json.loads((ROOT/'results/E049-frozen-cohort-semantics/run/manifest.json').read_text()); randoms={(x['seed'],x['task']):x['cohort'] for x in manifest['random']}; targets=m.m.e042.tasks_from_registry()
for x in rows:
 group=manifest['source'] if x['condition']=='learned' else randoms[x['seed'],x['task']]
 x['direct_cohort_error']=min(m.m.base.error(int(c['signature']),targets[x['task']]) for c in group)
 x['direct_minus_beam_error']=x['direct_cohort_error']-x['beam_best_error']
rng=np.random.default_rng(2050)
def stats(v):
 a=np.array(v,float); sd=a.std(ddof=1); boot=a[rng.integers(0,len(a),(20000,len(a)))].mean(1); p=sum(abs(np.mean(a*np.array(s)))>=abs(a.mean())-1e-12 for s in itertools.product([-1,1],repeat=len(a)))/2**len(a)
 return dict(mean=float(a.mean()),variance=float(a.var(ddof=1)),ci95=np.quantile(boot,[.025,.975]).tolist(),dz=None if sd==0 else float(a.mean()/sd),p=float(p),values=v)
by={(x['seed'],x['task'],x['condition']):x for x in rows}; seeds=list(range(1660,1666)); tasks=sorted({x['task'] for x in rows}); groups={}; comparisons={}
lines=['# E050：投入直後の合成予算診断','','E049と同じseed1660–1665・全8task・固定source/random cohortを再利用した機構診断。独立確認ではない。round2 beamを費用込みで復元し、cohort×beamの16 LUTを枝刈りせず列挙した。cost16の記号式予算を扱い、物理DAGゲート数を扱わない。','', '| family | cohort | feasible pair割合 平均/分散 | exact child有/24 | 有用child有/24 | best child error 平均/分散 | 予算外exact有/24 |','| --- | --- | ---: | ---: | ---: | ---: | ---: |']
for fam in ['numeric','route']:
 ts=[t for t in tasks if t.startswith(fam+'_')]
 for c in ['learned','random']:
  xs=[by[s,t,c] for s in seeds for t in ts]; metrics={k:stats([sum(by[s,t,c][k] for t in ts)/4 for s in seeds]) for k in ['feasible_fraction','best_child_error','unconstrained_best_child_error','direct_cohort_error','direct_minus_beam_error']}; [v.pop(k) for v in metrics.values() for k in ['p','dz']]; metrics.update(exact_beams=sum(x['exact_children']>0 for x in xs),useful_beams=sum(x['useful_legal_children']>0 for x in xs),rejected_exact_beams=sum(x['rejected_exact_children']>0 for x in xs)); groups[fam+':'+c]=metrics; a=metrics['feasible_fraction']; b=metrics['best_child_error']; lines.append(f"| {fam} | {c} | {a['mean']:.4f}/{a['variance']:.6f} | {metrics['exact_beams']}/24 | {metrics['useful_beams']}/24 | {b['mean']:.4f}/{b['variance']:.6f} | {metrics['rejected_exact_beams']}/24 |")
 comparisons[fam]=stats([sum(by[s,t,'learned']['best_child_error']-by[s,t,'random']['best_child_error'] for t in ts)/4 for s in seeds])
order=sorted(comparisons,key=lambda k:comparisons[k]['p']); running=0
for i,k in enumerate(order): running=max(running,min(1,(2-i)*comparisons[k]['p'])); comparisons[k]['holm_p']=running
lines+=['','learned−random best-child error（負がlearned有利）。seed単位bootstrap CIは条件付き記述量で、独立検証の証拠ではない。','']
for k,v in comparisons.items(): lines.append(f"- {k}: 平均{v['mean']:.4f}、不偏分散{v['variance']:.6f}、95% CI {v['ci95']}、dz={v['dz']}、p={v['p']:.5f}、Holm p={v['holm_p']:.5f}")
lines+=['',f"96記録・48beam再現・全費用再計算・source hash・progressを照合。実行{r['seconds']:.1f}秒。2段合成やround3選択での保持は未評価。sourceの非衝突admissionと、その後の利用可能性を区別する。",'', '全pairがcost16内であり、この投入時点の一段合成には予算制約が障害ではなかった。learnedのexact childは0/48、randomは1/48。有用childはlearned numeric0/24・route12/24。learnedのbest child errorはrandomよりnumeric+2.625、route+4.6667だが両Holm p=0.0625。枝刈り前の機会は既存候補との重複を含み、cohortに固有の新規解を意味しない。', '', '- [Done] 全固定cohortの一段合成機会を枝刈り前に評価した。','- [Next] 同一cohortの有用childがround3選択で失われるかを記録し、残る一段での利用機会を診断する。','- [Later] 変更案を校正後に新規seedで意味効果確認。State/Router/Expert交換と物理費用評価。','', 'English: This retrospective one-step diagnostic separates legal composition opportunities from admission and pruning. It is not independent confirmation or two-step reachability proof.','', '简体中文：本回顾性单步诊断区分合法组合机会、加入和剪枝；不属于独立验证，也未证明两步可达性。']
lines += ['English: All cohort–beam pairs fit cost16. Learned exact children:0/48; random:1/48. Learned best-child error was worse by2.625 (numeric) and4.6667 (routing), both Holm p=0.0625. Pruning and two-step use remain unresolved.\n\n简体中文：全部cohort–beam组合符合cost16。学习函数exact子项0/48，随机1/48。学习函数最佳子项误差较高：数值+2.625、路由+4.6667，两者Holm p=0.0625。剪枝及两步复用仍未解决。']
summary=dict(groups=groups,comparisons=comparisons,records=96,seconds=r['seconds'],analysis_hash=hashlib.sha256((HERE/'report.py').read_bytes()).hexdigest()); (out/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)); (HERE/'REPORT.md').write_text('\n'.join(lines)+'\n'); print(json.dumps(summary,ensure_ascii=False,indent=2))
