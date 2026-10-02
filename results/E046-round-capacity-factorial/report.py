import ast,hashlib,importlib.util,json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E046-round-capacity-factorial'; OUT=HERE/'run'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def strict(p): return json.loads(p.read_text(),parse_constant=lambda x:(_ for _ in()).throw(ValueError(x)))
def load(name,p):
 spec=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
m=load('e046_report_main',HERE/'main.py'); base=m.base; rng=np.random.default_rng(2046)
def stats(v):
 a=np.array(v,float); sd=a.std(ddof=1); obs=abs(a.mean()); p=float(sum(abs(np.mean([x if mask&(1<<i) else -x for i,x in enumerate(a)]))>=obs-1e-12 for mask in range(1<<len(a)))/(1<<len(a))); boot=a[rng.integers(0,len(a),(20000,len(a)))].mean(1)
 return dict(mean=float(a.mean()),variance=float(a.var(ddof=1)),ci95=np.quantile(boot,[.025,.975]).tolist(),dz=None if sd==0 else float(a.mean()/sd),p=p,values=v)
def evaluate(e,inputs):
 if e[0]=='input': return inputs[e[1]]
 sig=base.lut_outputs(evaluate(e[3],inputs),evaluate(e[4],inputs))[e[2]]; assert sig==int(e[1]); return sig
r=strict(OUT/'results.json'); rows=r['records']; manifest=strict(OUT/'manifest.json'); tasks=m.e042.tasks_from_registry(); seeds=list(range(1620,1626)); policies={'LL':[128,128],'HL':[164,128],'LH':[128,192],'HH':[164,192]}
assert r['settings']=={'seeds':seeds,'policies':policies,'rounds':4,'max_cost':16,'tasks':list(tasks)}
assert manifest['targets']=={k:str(v) for k,v in tasks.items()}
assert len(rows)==192 and len({(x['seed'],x['task'],x['condition']) for x in rows})==192
assert [json.loads(x) for x in (OUT/'progress.jsonl').read_text().splitlines()]==rows
assert len(strict(OUT/'smoke.json'))==16 and all(x['passed'] for x in strict(OUT/'smoke.json'))
for name,digest in r['sources'].items(): assert sha(ROOT/name)==digest
inputs,_=base.inputs_and_targets(); by={(x['seed'],x['task'],x['condition']):x for x in rows}; solutions=0
for x in rows:
 assert not x['uses_transfer'] and not x['injected_collision']
 initial,later=policies[x['condition']]; h=x['input_width_history']; assert h[0]==6 and h[1]==initial
 for w in h[2:]: assert w==later
 if x['exact']: assert evaluate(x['expression'],inputs)==tasks[x['task']]; solutions+=1
for s in seeds:
 for t in tasks:
  assert by[s,t,'LL']['first_round_selected']==by[s,t,'LH']['first_round_selected']
  assert by[s,t,'HL']['first_round_selected']==by[s,t,'HH']['first_round_selected']
  assert by[s,t,'LL']['first_round_selected']==by[s,t,'HH']['first_round_selected'][:128]
def means(s,f,key):
 ts=[t for t in tasks if t.startswith(f+'_')]; return {c:sum(int(by[s,t,c][key]) for t in ts)/4 for c in policies}
primary=stats([means(s,'route','exact')['LH']-means(s,'route','exact')['HL'] for s in seeds]); contrasts={}
for family in ['numeric','route']:
 for key in ['exact','best_error']:
  for effect in ['initial','later','interaction']:
   values=[]
   for s in seeds:
    a=means(s,family,key); v=((a['HL']-a['LL'])+(a['HH']-a['LH']))/2 if effect=='initial' else ((a['LH']-a['LL'])+(a['HH']-a['HL']))/2 if effect=='later' else a['HH']-a['HL']-a['LH']+a['LL']; values.append(v)
   contrasts[f'{family}:{key}:{effect}']=stats(values)
order=sorted(contrasts,key=lambda k:contrasts[k]['p']); running=0
for rank,k in enumerate(order): running=max(running,min(1.,(12-rank)*contrasts[k]['p'])); contrasts[k]['holm_p']=running
summary=dict(primary=primary,gate=bool(primary['mean']>=.10 and primary['p']<=.05),contrasts=contrasts,conditions={},records=192,solutions=solutions,beam_checks=144,smoke_checks=16,analysis_hash=sha(HERE/'report.py'))
lines=['# E046：Round別容量の2×2校正','', '2026-10-02。凍結8 task、新規6 seed、初回選択幅128/164と後続選択幅128/192を交差。LL/HL/LH/HHの初文字は初回幅、後文字は後続幅。192探索。','', '| family | policy | exact/24 | seed平均 / 不偏分散 | best error平均 / 不偏分散 | 秒平均 |','| --- | --- | ---: | ---: | ---: | ---: |']
for f in ['numeric','route']:
 for c in policies:
  ts=[t for t in tasks if t.startswith(f+'_')]; selected=[by[s,t,c] for s in seeds for t in ts]; exact=stats([means(s,f,'exact')[c] for s in seeds]); error=stats([means(s,f,'best_error')[c] for s in seeds]); summary['conditions'][f'{f}:{c}']=dict(exact=exact,error=error,costs={k:[x[k] for x in selected if x['exact']] for k in ['primitives','routing_bits','depth']},generated=[x['generated_unique_signatures'] for x in selected],seconds=[x['elapsed_seconds'] for x in selected]); lines.append(f"| {f} | {c} | {sum(x['exact'] for x in selected)}/24 | {exact['mean']:.4f} / {exact['variance']:.4f} | {error['mean']:.3f} / {error['variance']:.4f} | {np.mean([x['elapsed_seconds'] for x in selected]):.3f} |")
lines+=['',f"主指標route exact(LH)−exact(HL)：平均{primary['mean']:+.4f}、不偏分散{primary['variance']:.4f}、95% CI {primary['ci95']}、dz={primary['dz']}、exact p={primary['p']:.5f}。事前gate：{summary['gate']}。",'', '| 比較 | 平均差 | 不偏分散 | 95% CI | dz | exact p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for k,x in contrasts.items(): lines.append(f"| {k} | {x['mean']:+.4f} | {x['variance']:.4f} | {x['ci95']} | {x['dz']} | {x['p']:.5f} | {x['holm_p']:.5f} |")
lines+=['','後続拡張LH/HHはroute19/24、初回だけ拡張HLとbaseline LLは12/24。主指標は事前gateを達成した。numeric exactは全条件12/24のまま、error改善は後続拡張でのみ観測された。12副次比較のHolm補正後は全て非有意（最小p=0.375）。best_error差は負が改善。この校正は学習Moduleの効果を評価していない。', '',f"探索時間{r['search_seconds']:.1f}秒。全{solutions} exact式を64入力で再評価。192 record、144初回beam照合、16別seed互換smoke、round入力幅、progress、strict JSON、source hashを監査した。",'', '- [Done] 初回保持と後続選択幅を2×2で分離して評価した。','- [Next] 主指標と副次補正の結果から容量policyの確認計画を凍結し、確認seedを分離する。','- [Later] learned／inert／同費用random cohort比較、State形成・分解、初回負荷分散Router、固定random経路、Expert交換へ進む。','', 'English: Later expansion solved 19/24 routing cases versus 12/24 for initial-only expansion. The preregistered primary gate passed (difference +0.292, p=0.03125); all12 secondary contrasts remained nonsignificant after Holm correction.','', '简体中文：后续扩容的路由成功为19/24，仅初始扩容为12/24。预注册主要标准达成（差+0.292，p=0.03125），但12项次要比较经Holm校正后均不显著。']
(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)); report='\n'.join(lines)+'\n'; (HERE/'REPORT.md').write_text(report); (ROOT/'docs/STAR-Bit-E046-round-capacity-factorial.md').write_text(report); print(json.dumps({k:summary[k] for k in ['primary','gate','solutions']},indent=2))
