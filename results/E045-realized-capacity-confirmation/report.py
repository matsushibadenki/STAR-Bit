import ast,hashlib,importlib.util,json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E045-realized-capacity-confirmation'; OUT=HERE/'run'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def strict(p): return json.loads(p.read_text(),parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
m=load('e045',HERE/'main.py'); base=m.e039.base
rng=np.random.default_rng(2045)
def stats(v):
 a=np.array(v,float); sd=a.std(ddof=1); obs=abs(a.mean()); p=sum(abs(np.mean([x if mask&(1<<i) else -x for i,x in enumerate(a)]))>=obs-1e-12 for mask in range(1<<len(a)))/(1<<len(a)); boot=a[rng.integers(0,len(a),(20000,len(a)))].mean(1)
 return dict(mean=float(a.mean()),variance=float(a.var(ddof=1)),ci95=np.quantile(boot,[.025,.975]).tolist(),dz=None if sd==0 else float(a.mean()/sd),p=float(p),values=v)
def evaluate(e,inputs):
 if e[0]=='input': return inputs[e[1]]
 sig=base.lut_outputs(evaluate(e[3],inputs),evaluate(e[4],inputs))[e[2]]; assert sig==int(e[1]); return sig
r=strict(OUT/'results.json'); rows=r['records']; frozen=strict(OUT/'frozen_manifest.json'); tasks=m.e042.tasks_from_registry(); seeds=list(range(1610,1616)); widths=[128,164,192]
assert len(rows)==144 and len({(x['seed'],x['task'],x['width']) for x in rows})==144
assert r['settings']['seeds']==seeds and r['settings']['widths']==widths and r['settings']['tasks']==list(tasks)
assert frozen['targets']=={k:str(v) for k,v in tasks.items()}
assert [json.loads(x) for x in (OUT/'progress.jsonl').read_text().splitlines()]==rows
for name,digest in r['sources'].items(): assert sha(ROOT/name)==digest
inputs,_=base.inputs_and_targets(); by={(x['seed'],x['task'],x['width']):x for x in rows}; solutions=0
for x in rows:
 assert not x['uses_transfer'] and x['library_signatures']==[]
 assert len(x['first_round_selected'])==min(x['width'],164)==x['round_two_input_width']
 if x['exact']: assert evaluate(x['expression'],inputs)==tasks[x['task']]; solutions+=1
for s in seeds:
 for t in tasks:
  assert by[s,t,128]['first_round_selected']==by[s,t,164]['first_round_selected'][:128]
  assert by[s,t,164]['first_round_selected']==by[s,t,192]['first_round_selected']
def diff(s,f,hi,lo,metric):
 ts=[t for t in tasks if t.startswith(f+'_')]
 return sum((int(by[s,t,hi][metric])-int(by[s,t,lo][metric])) for t in ts)/len(ts)
primary=stats([diff(s,'route',164,128,'exact') for s in seeds]); numeric=stats([-diff(s,'numeric',164,128,'best_error') for s in seeds]); later=stats([diff(s,'route',192,164,'exact') for s in seeds]); vals=[numeric['p'],later['p']]; order=sorted(range(2),key=lambda i:vals[i]); adj=[0.,0.]; running=0
for rank,i in enumerate(order): running=max(running,min(1.,(2-rank)*vals[i])); adj[i]=running
summary=dict(primary=primary,numeric_error=numeric,later_width_effect=later,holm_secondary=adj,gate=bool(primary['mean']>=.10 and primary['p']<=.05),records=144,solutions=solutions,prefix_checks=96,source_hash=sha(HERE/'report.py'),conditions={})
lines=['# E045：全Round実効幅の独立確認','', '2026-10-01。凍結8 task、新規6 seed、幅上限128/164/192、144探索。192条件は最初の2 roundのみ164、以降は上限192。','', '| family | 幅上限 | exact/24 | seed平均 | 不偏分散 | best error平均 | error不偏分散 | 生成signature平均 | 秒平均 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for f in ['numeric','route']:
 for w in widths:
  ts=[t for t in tasks if t.startswith(f+'_')]; groups=[[by[s,t,w] for t in ts] for s in seeds]; exact=stats([sum(x['exact'] for x in g)/4 for g in groups]); error=stats([sum(x['best_error'] for x in g)/4 for g in groups]); selected=[x for g in groups for x in g]; count=sum(x['exact'] for x in selected)
  costs={key:[x[key] for x in selected if x['exact']] for key in ['primitives','routing_bits','depth']}
  summary['conditions'][f'{f}:{w}']=dict(exact=exact,error=error,solution_costs=costs,seconds=[x['elapsed_seconds'] for x in selected],generated=[x['generated_unique_signatures'] for x in selected])
  lines.append(f"| {f} | {w} | {count}/24 | {exact['mean']:.4f} | {exact['variance']:.4f} | {error['mean']:.4f} | {error['variance']:.4f} | {np.mean([x['generated_unique_signatures'] for x in selected]):.1f} | {np.mean([x['elapsed_seconds'] for x in selected]):.3f} |")
lines+=['','| 比較 | 平均差 | 不偏分散 | bootstrap 95% CI | dz | exact p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for label,x,h in [('主指標route exact164−128',primary,None),('numeric error128−164',numeric,adj[0]),('route exact192−164',later,adj[1])]: lines.append(f"| {label} | {x['mean']:+.4f} | {x['variance']:.4f} | {x['ci95']} | {x['dz']} | {x['p']:.5f} | {h} |")
lines+=['',f"事前主gate：{summary['gate']}。探索時間合計{r['search_seconds']:.1f}秒。全{solutions} exact式を64入力で再評価し、144 record、実効初回幅、96 prefix、progress、strict JSON、source hashを監査した。",'', '事前主gateは未達。route exactは128の13/24から164の17/24、192の20/24へ増えたが、164−128のp=0.125。numeric exactは全幅12/24で、error改善+0.25はHolm p=0.0625。初回幅164でも後続roundの上限192が結果を変えるため、初回幅だけで容量policyを代表できない。改善案は投入するroundごとの容量効果を先に校正すること。','', '- [Done] 164固定policyと192上限policyを独立seedで比較した。','- [Next] round別容量ablationを新規calibration seedで事前登録し、初回候補保持と後続探索幅を分離する。','- [Later] 意味固有効果成立後、State形成・分解、負荷分散Router、固定random経路、Expert交換を検証する。','', 'English: Independent seeds compare fixed width 164 against caps 128 and 192. The primary gate tests routing exact at 164 versus 128; the 192-versus-164 control isolates later-round capacity.','', '简体中文：独立种子比较固定宽度164与上限128和192。主要标准检验164相对128的路由exact；192与164的对照分离后续轮次容量。']
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)); report='\n'.join(lines)+'\n'; (HERE/'REPORT.md').write_text(report); (ROOT/'docs/STAR-Bit-E045-realized-capacity-confirmation.md').write_text(report); print(json.dumps({k:summary[k] for k in ['primary','numeric_error','later_width_effect','holm_secondary','gate','solutions']},indent=2))
