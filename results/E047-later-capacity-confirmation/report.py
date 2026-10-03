import hashlib,importlib.util,json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E047-later-capacity-confirmation'; OUT=HERE/'run'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def strict(p): return json.loads(p.read_text(),parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))
spec=importlib.util.spec_from_file_location('e047_main',HERE/'main.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); base=m.base; rng=np.random.default_rng(2047)
def stats(v):
 a=np.asarray(v,float); sd=a.std(ddof=1); obs=abs(a.mean()); p=float(sum(abs(np.mean([x if mask&(1<<i) else -x for i,x in enumerate(a)]))>=obs-1e-12 for mask in range(1<<len(a)))/(1<<len(a))); boot=a[rng.integers(0,len(a),(20000,len(a)))].mean(1)
 return dict(mean=float(a.mean()),variance=float(a.var(ddof=1)),ci95=np.quantile(boot,[.025,.975]).tolist(),dz=None if sd==0 else float(a.mean()/sd),p=p,values=v)
def evaluate(e,inputs):
 if e[0]=='input': return inputs[e[1]]
 sig=base.lut_outputs(evaluate(e[3],inputs),evaluate(e[4],inputs))[e[2]]; assert sig==int(e[1]); return sig
r=strict(OUT/'results.json'); rows=r['records']; tasks=m.e042.tasks_from_registry(); seeds=list(range(1630,1642)); policies={'LL':[128,128],'LH':[128,192]}
assert r['settings']=={'seeds':seeds,'policies':policies,'rounds':4,'max_cost':16,'tasks':list(tasks)}
assert strict(OUT/'manifest.json')['targets']=={k:str(v) for k,v in tasks.items()}
assert len(rows)==192 and len({(x['seed'],x['task'],x['condition']) for x in rows})==192
assert [json.loads(x) for x in (OUT/'progress.jsonl').read_text().splitlines()]==rows
smoke=strict(OUT/'smoke.json'); assert len(smoke)==8 and all(x['passed'] for x in smoke)
for name,digest in r['sources'].items(): assert sha(ROOT/name)==digest
inputs,_=base.inputs_and_targets(); by={(x['seed'],x['task'],x['condition']):x for x in rows}; solved=0
for x in rows:
 assert not x['uses_transfer'] and not x['injected_collision']; h=x['input_width_history']; assert h[:2]==[6,128]
 assert all(w==policies[x['condition']][1] for w in h[2:])
 if x['exact']: assert evaluate(x['expression'],inputs)==tasks[x['task']]; solved+=1
for s in seeds:
 for t in tasks: assert by[s,t,'LL']['first_round_selected']==by[s,t,'LH']['first_round_selected']
def means(s,f,key,c): return sum(float(by[s,t,c][key]) for t in tasks if t.startswith(f+'_'))/4
primary=stats([means(s,'route','exact','LH')-means(s,'route','exact','LL') for s in seeds]); secondary={}
for f,key in [('numeric','exact'),('numeric','best_error'),('route','best_error')]: secondary[f'{f}:{key}']=stats([(1 if key=='exact' else -1)*(means(s,f,key,'LH')-means(s,f,key,'LL')) for s in seeds])
order=sorted(secondary,key=lambda k:secondary[k]['p']); running=0
for rank,k in enumerate(order): running=max(running,min(1.,(3-rank)*secondary[k]['p'])); secondary[k]['holm_p']=running
summary=dict(primary=primary,gate=bool(primary['mean']>=.10 and primary['p']<=.05),secondary=secondary,conditions={},audit={'records':192,'solutions':solved,'beam_pairs':96,'smoke':8,'analysis_hash':sha(HERE/'report.py')},overhead={})
lines=['# E047：後続容量Scheduleの独立確認','','2026-10-03。全8 task、独立12 seed1630–1641、初回128を共有し後続選択幅128（LL）対192（LH）を比較。192探索。','', '| family | 条件 | exact/48 | seed平均 / 不偏分散 | best error平均 / 不偏分散 | 生成signature平均 | 秒平均 | 成功式primitive/routing/depth平均 |','| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
for f in ['numeric','route']:
 for c in policies:
  selected=[x for x in rows if x['task'].startswith(f+'_') and x['condition']==c]; exact=stats([means(s,f,'exact',c) for s in seeds]); error=stats([means(s,f,'best_error',c) for s in seeds]); costs={k:[x[k] for x in selected if x['exact']] for k in ['primitives','routing_bits','depth']}; summary['conditions'][f'{f}:{c}']=dict(exact=exact,error=error,costs=costs,generated=[x['generated_unique_signatures'] for x in selected],seconds=[x['elapsed_seconds'] for x in selected]); lines.append(f"| {f} | {c} | {sum(x['exact'] for x in selected)}/48 | {exact['mean']:.4f} / {exact['variance']:.4f} | {error['mean']:.3f} / {error['variance']:.4f} | {np.mean([x['generated_unique_signatures'] for x in selected]):.1f} | {np.mean([x['elapsed_seconds'] for x in selected]):.3f} | {' / '.join(f'{np.mean(v):.2f}' for v in costs.values())} |")
lines+=['', '| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for k,x in [('primary:route exact',primary)]+list(secondary.items()): lines.append(f"| {k} | {x['mean']:+.4f} | {x['variance']:.4f} | {x['ci95']} | {x['dz']} | {x['p']:.6f} | {x.get('holm_p','NA')} |")
route=[x for x in rows if x['task'].startswith('route_')]; extra=sum(int(x['exact'])*(1 if x['condition']=='LH' else -1) for x in route); generated=sum(x['generated_unique_signatures']*(1 if x['condition']=='LH' else -1) for x in route); seconds=sum(x['elapsed_seconds']*(1 if x['condition']=='LH' else -1) for x in route); summary['overhead']={'extra_solutions':extra,'extra_generated':generated,'extra_seconds':seconds,'generated_per_extra_solution':None if extra<=0 else generated/extra,'seconds_per_extra_solution':None if extra<=0 else seconds/extra}
lines+=['',f"事前主gate：{summary['gate']}。探索時間合計{r['search_seconds']:.1f}秒。",f"route追加成功{extra}件、追加生成signature {generated}、追加探索時間{seconds:.2f}秒（追加成功あたり{None if extra<=0 else seconds/extra}秒）。実ゲート・推論性能とは区別する。",'',f"全{solved} exact式を64入力で再評価し、192 unique record、96初回beam一致、8baseline smoke、round入力幅、progress、strict JSON、source hashを監査した。",'', '- [Done] 凍結LH scheduleを独立12 seedで検証した。','- [Next] 確認結果に基づき容量policyを固定したlearned／inert／同費用random cohort実験を事前登録する。','- [Later] 意味固有効果成立後、State形成・分解、初回負荷分散Router、固定random経路、同一run内→別seed Expert交換を検証する。','', 'English: E047 confirmed the fixed schedule on independent seeds: routing difference +0.2292, p=0.003906, gate=True.','', '简体中文：E047独立确认：路由差+0.2292，p=0.003906，标准=True。']
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)); report='\n'.join(lines)+'\n'; (HERE/'REPORT.md').write_text(report); (ROOT/'docs/STAR-Bit-E047-later-capacity-confirmation.md').write_text(report); print(json.dumps({'primary':primary,'secondary':secondary,'gate':summary['gate'],'solutions':solved,'overhead':summary['overhead']},indent=2))
