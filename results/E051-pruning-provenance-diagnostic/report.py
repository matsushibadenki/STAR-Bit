import hashlib,importlib.util,itertools,json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E051-pruning-provenance-diagnostic'; OUT=HERE/'run'
r=json.loads((OUT/'results.json').read_text()); rows=r['records']; assert r['complete'] and len(rows)==96
assert [json.loads(s) for s in (OUT/'progress.jsonl').read_text().splitlines()]==rows
for name,h in r['sources'].items(): assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
assert len({(x['seed'],x['task'],x['condition']) for x in rows})==96
spec=importlib.util.spec_from_file_location('e051',HERE/'main.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); inputs,_=m.m.base.inputs_and_targets()
def evaluate(e):
 if e[0]=='input': return inputs[e[1]]
 s=m.m.base.lut_outputs(evaluate(e[3]),evaluate(e[4]))[e[2]]; assert s==int(e[1]); return s
verified=0
for x in rows:
 assert x['canonical_useful_provenance']<=x['useful_signatures']
 if x['terminal_round3']: assert x['exact'] and x['solution_round']==3 and x['selected_candidates'] is None
 else:
  assert len(x['selected_candidates'])==192
  assert x['selected_useful_provenance']<=x['selected_useful_signatures']<=x['useful_signatures']
  for c in x['selected_candidates']:
   assert evaluate(c['expression'])==int(c['signature']); assert m.m.e023.expression_cost(c['expression'])==(c['primitives'],c['routing_bits'],c['depth']); verified+=1
rng=np.random.default_rng(2051)
def stats(v):
 a=np.array(v,float); sd=a.std(ddof=1); boot=a[rng.integers(0,len(a),(20000,len(a)))].mean(1); p=sum(abs(np.mean(a*np.array(s)))>=abs(a.mean())-1e-12 for s in itertools.product([-1,1],repeat=len(a)))/2**len(a)
 return dict(mean=float(a.mean()),variance=float(a.var(ddof=1)),ci95=np.quantile(boot,[.025,.975]).tolist(),dz=None if sd==0 else float(a.mean()/sd),p=float(p),values=v)
def perseed(xs,field):
 v=[]
 for seed in range(1660,1666):
  eligible=[x for x in xs if x['seed']==seed and not x['terminal_round3'] and x['useful_signatures']>0]
  if not eligible: return None
  v.append(sum(x[field]/x['useful_signatures'] for x in eligible)/len(eligible))
 return v
summary={}; comp={}; lines=['# E051：枝刈りと同一関数の式置換','','E049同seed1660–1665・全8task・固定source/randomを再現した回顧的診断。96探索。探索policy変更なし。round3で完全解が見つかった条件は選択処理がないため保持率から除外。有用child＝round2 beam最良より誤差が小さいsignature。','', '| family | cohort | terminal/24 | 有用child有/非terminal | poolの有用child数 | うちcohort式 | 選択保持signature | 選択保持cohort式 | round4完全解 |','| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for fam in ['numeric','route']:
 for condition in ['learned','random']:
  xs=[x for x in rows if x['task'].startswith(fam+'_') and x['condition']==condition]; eligible=[x for x in xs if not x['terminal_round3']]; result=dict(terminal=sum(x['terminal_round3'] for x in xs),eligible=len(eligible),useful_beams=sum(x['useful_signatures']>0 for x in eligible),useful=sum(x['useful_signatures'] for x in eligible),pool_provenance=sum(x['canonical_useful_provenance'] for x in eligible),retained=sum(x['selected_useful_signatures'] for x in eligible),retained_provenance=sum(x['selected_useful_provenance'] for x in eligible),selected_all_provenance=sum(x['selected_all_provenance'] for x in eligible),round4_exact=sum(x['exact'] and x['solution_round']==4 for x in xs),success_use=sum(x['exact'] and x['uses_transfer'] for x in xs)); result['rates']={}
  for field in ['selected_useful_signatures','selected_useful_provenance']:
   v=perseed(xs,field); result['rates'][field]=None if v is None else stats(v)
  result['seed_count_stats']={}
  for field in ['useful_signatures','selected_useful_signatures','selected_useful_provenance']:
   count=stats([sum(x[field] for x in eligible if x['seed']==seed) for seed in range(1660,1666)]); count.pop('p'); count.pop('dz'); result['seed_count_stats'][field]=count
  for rate in result['rates'].values():
   if rate is not None: rate.pop('p'); rate.pop('dz')
  summary[fam+':'+condition]=result
  lines.append(f"| {fam} | {condition} | {result['terminal']}/24 | {result['useful_beams']}/{result['eligible']} | {result['useful']} | {result['pool_provenance']} | {result['retained']} | {result['retained_provenance']} | {result['round4_exact']} |")
 a=summary[fam+':learned']['rates']['selected_useful_signatures']; b=summary[fam+':random']['rates']['selected_useful_signatures']; comp[fam]=None if a is None or b is None else stats([x-y for x,y in zip(a['values'],b['values'])])
valid={k:v for k,v in comp.items() if v is not None}; running=0
for i,k in enumerate(sorted(valid,key=lambda k:valid[k]['p'])):
 running=max(running,min(1,(2-i)*valid[k]['p'])); valid[k]['holm_p']=running
lines+=['','seed単位保持率は、有用childが存在する非terminal taskだけの条件付き平均。欠損を0とせず、6seed全てに分母がある比較のみ検定し、事前2比較をHolmのfamily sizeに維持。','']
for key,v in summary.items():
 for field,x in v['rates'].items():
  lines.append(f"- {key}/{field}: "+('分母欠損、推定しない。' if x is None else f"平均{x['mean']:.6f}、不偏分散{x['variance']:.6f}、95% CI {x['ci95']}"))
for key,v in summary.items():
 for field,x in v['seed_count_stats'].items(): lines.append(f"- {key}/{field} count per seed: 平均{x['mean']:.4f}、不偏分散{x['variance']:.4f}、95% CI {x['ci95']}")
for key,x in comp.items(): lines.append(f"- learned−random/{key}: "+('分母欠損、検定しない。' if x is None else f"平均{x['mean']:.6f}、分散{x['variance']:.6f}、CI {x['ci95']}、dz={x['dz']}、p={x['p']:.5f}、Holm p={x['holm_p']:.5f}"))
lines+=['',f"全96探索のE049完全解・誤差・式・費用・初回/round2 beam・入力幅を一致確認。{verified}選択式を64入力と費用で再評価。実行{r['seconds']:.1f}秒。",'cohort式の判定はcohort signatureの構文的出現であり、学習由来の実行provenanceを保証しない。canonical poolは同じ真理値関数の最安式を保持する。保持signatureとcohort式の差を切り分け、完全な二段到達性や物理費用の効果へ拡張しない。','', '- [Done] 枝刈りとcanonical式の置換を区別して再現診断した。','- [Next] 総beam幅192のままtarget非依存の新規cohort子候補に一段の保持枠を設ける案を、新規calibration seedでbaseline/learned/inert/randomと比較する。固定枠分だけ通常候補が減る費用も含め、確認seedを別にする。','- [Later] State形成/分解、初回負荷分散Router、固定random経路、同一run内→別seed Expert交換。','', 'English: Retrospective pruning diagnosis separates signature retention from canonical expression provenance. Terminal round3 solutions and empty useful-child denominators are explicitly excluded, not imputed.','', '简体中文：回顾性剪枝诊断区分signature保留与规范表达式来源。第三轮已解条件及无有用子项的分母明确排除，不填零。']
lines+=['','結論：非terminal routeのlearned有用child170signatureは全てpoolでcohort式を保持し、選択後は0。ここでは同一関数の安価な式への置換より枝刈りが直接の消失箇所だった。ただし通常候補より価値が高いとは示しておらず、保持枠で精度が改善するかは未検証。numericは非terminal12条件で有用child0。random routeは847中23signature保持、うちcohort式16。learnedの全6seed保持率は分母欠損があり推定/対照検定を行わない。', '', 'English: All170 useful learned routing child signatures in nonterminal runs retained cohort syntax in the pool, but none survived selection. This locates loss at pruning, without proving that protecting them improves accuracy. Numeric had no useful learned children in nonterminal runs. Missing seed denominators prevent paired retention inference.', '', '简体中文：未终止路由条件中的170个有用学习子signature在pool中保留cohort表达式，但选择后全部消失。定位到剪枝不代表保护它们会提高准确率。数值未终止条件没有有用学习子项；种子分母缺失，未进行成对保持率推断。']
result=dict(groups=summary,comparisons=comp,records=96,verified_selected=verified,seconds=r['seconds'],analysis_hash=hashlib.sha256((HERE/'report.py').read_bytes()).hexdigest()); (OUT/'audit_summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)); (HERE/'REPORT.md').write_text('\n'.join(lines)+'\n'); print(json.dumps(result,indent=2))
