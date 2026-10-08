import hashlib,importlib.util,itertools,json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E053-reserve-calibration-completion'; OUT=HERE/'run'
spec=importlib.util.spec_from_file_location('e052',ROOT/'results/E052-one-round-reserve-calibration/main.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
r=json.loads((OUT/'results.json').read_text()); rows=r['records']; assert len(rows)<=240
assert [json.loads(s) for s in (OUT/'progress.jsonl').read_text().splitlines()]==rows
for name,h in r['sources'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
by={(x['seed'],x['task'],x['condition']):x for x in rows}; assert len(by)==len(rows)
manifest=json.loads((OUT/'manifest.json').read_text()); pre=json.loads((OUT/'preflight.json').read_text()); prior={(x['seed'],x['task']):x for x in pre}; inputs,_=m.base.inputs_and_targets(); tasks=m.e042.tasks_from_registry(); seeds=list(range(1670,1676)); conditions=['baseline','learned_standard','learned_reserve','inert_reserve','random_reserve']; verified=0; solutions=0
source={int(x['signature']) for x in manifest['source']}; union={int(s) for x in pre for s in x['round2']}; random_seen=set()
def evaluate(e):
 if e[0]=='input':return inputs[e[1]]
 sig=m.base.lut_outputs(evaluate(e[3]),evaluate(e[4]))[e[2]];assert sig==int(e[1]);return sig
for group in [manifest['source']]+[x['cohort'] for x in manifest['random']]:
 for i,c in enumerate(group):
  assert evaluate(c['expression'])==int(c['signature']); assert m.e023.expression_cost(c['expression'])==(c['primitives'],c['routing_bits'],c['depth'])
  if group is not manifest['source']:
   assert int(c['signature']) not in source|union|random_seen|set(tasks.values())|set(inputs);random_seen.add(int(c['signature']));t=manifest['source'][i];assert (c['primitives'],c['routing_bits'],c['depth'])==(t['primitives'],t['routing_bits'],t['depth'])
for x in rows:
 assert x['first_round_selected']==prior[x['seed'],x['task']]['round1'];assert x['round2_selected']==prior[x['seed'],x['task']]['round2'];assert x['input_width_history'][:3]==[6,128,192 if x['condition']=='baseline' else 200]
 if x['reserve_audit'] is not None:
  a=x['reserve_audit'];assert x['condition'].endswith('_reserve');assert len(a['protected'])<=16 and len(a['selected'])==192 and len({c['signature'] for c in a['selected']})==192;assert len(a['displaced'])<=len(a['protected']);assert set(a['protected'])<=set(c['signature'] for c in a['selected'])
  for c in a['selected']:assert evaluate(c['expression'])==int(c['signature']);assert m.e023.expression_cost(c['expression'])==(c['primitives'],c['routing_bits'],c['depth']);verified+=1
 if x['condition'] in ['baseline','inert_reserve']:assert not x['uses_transfer']
 if x['exact']:assert evaluate(x['expression'])==tasks[x['task']];solutions+=1
if not r['complete']:
 expected={(s,t,c) for s in seeds for t in tasks for c in conditions}; missing=[dict(seed=s,task=t,condition=c) for s,t,c in sorted(expected-set(by))]
 summary=dict(complete=False,records=len(rows),planned=240,missing=missing,solutions_verified=solutions,selected_verified=verified,random_verified=len(random_seen),search_seconds=r['search_seconds'],primary_status='pending: preregistered suite incomplete; no effect tests or gate',analysis_hash=hashlib.sha256((HERE/'report.py').read_bytes()).hexdigest())
 (OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False));(OUT/'remaining.json').write_text(json.dumps(missing,indent=2))
 lines=['# E053：E052一段保持枠の全条件統合・中断状態','',f"事前登録240探索のうち{len(rows)}を完了し、探索時間{r['search_seconds']:.1f}秒で事前900秒停止条件に到達した。成功・失敗を理由に停止したものではない。source/seed/task/controlsを固定したまま残り{len(missing)}探索を明示保存。",f"完了分の共通beam/幅、{solutions}成功式、{verified}保持式、source8/random{len(random_seen)}式、progress/hashを監査。",'主比較・平均差・分散・CI・多重比較検定・校正gateは全事前条件完了まで保留し、部分結果から候補やseedを変更しない。追加計算は別の時間制限付きchunkとして事前登録し、今回900秒停止を延長しない。','', '🟢 [Done] 保持枠の実装・preflight・完了分生データと未実行条件保存。','🟠 [Next] 未実行の固定条件だけを別chunkで実施し、重複実行せず全240探索を統合監査する。','🔴 [Later] 校正結果後に独立確認seedを事前固定。State/Router/Expert交換。','', 'English: The preregistered time cap stopped the incomplete calibration suite. Fixed remaining conditions are saved; effect estimation and candidate decisions are deferred until completion.','', '简体中文：预注册时间上限终止未完成的校准。已保存固定的剩余条件；完成前不估计效果，也不更改候选。']
 (HERE/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='missing'},indent=2));raise SystemExit(0)
rng=np.random.default_rng(2052)
def stats(v):
 a=np.array(v,float);sd=a.std(ddof=1);boot=a[rng.integers(0,len(a),(20000,len(a)))].mean(1);p=sum(abs(np.mean(a*np.array(s)))>=abs(a.mean())-1e-12 for s in itertools.product([-1,1],repeat=len(a)))/2**len(a)
 return dict(mean=float(a.mean()),variance=float(a.var(ddof=1)),ci95=np.quantile(boot,[.025,.975]).tolist(),dz=None if sd==0 else float(a.mean()/sd),p=float(p),values=v)
def correct(items):
 running=0
 for rank,k in enumerate(sorted(items,key=lambda k:items[k]['p'])):running=max(running,min(1,(len(items)-rank)*items[k]['p']));items[k]['holm_p']=running
def difference(ts,c):return [sum(by[s,t,'learned_reserve']['exact']-by[s,t,c]['exact'] for t in ts)/len(ts) for s in seeds]
controls=['learned_standard','inert_reserve','random_reserve'];primary={c:stats(difference(list(tasks),c)) for c in controls};correct(primary);secondary={f+':'+c:stats(difference([t for t in tasks if t.startswith(f+'_')],c)) for f in ['numeric','route'] for c in controls};correct(secondary)
uses=sum(x['exact'] and x['uses_transfer'] for x in rows if x['condition']=='learned_reserve');gate=all(v['mean']>0 and v['holm_p']<=.05 for v in primary.values()) and uses>0;groups={}
lines=['# E053：E052一段保持枠の全条件統合','','新規calibration seed1670–1675、固定全8task、総beam192、round3だけ最大16枠をtarget非依存の費用/hash順で新規cohort子候補に割り当てた。保持枠分だけ通常候補を減らす。独立確認ではない。','', '| family | condition | exact/24 | seed mean/variance | error mean/variance | cohort成功使用 | 保護個数/排除個数 |','| --- | --- | ---: | ---: | ---: | ---: | ---: |']
for f in ['numeric','route']:
 ts=[t for t in tasks if t.startswith(f+'_')]
 for c in conditions:
  xs=[by[s,t,c] for s in seeds for t in ts];e=stats([sum(by[s,t,c]['exact'] for t in ts)/4 for s in seeds]);err=stats([sum(by[s,t,c]['best_error'] for t in ts)/4 for s in seeds]);protect=sum(len(x['reserve_audit']['protected']) for x in xs if x['reserve_audit']);displace=sum(len(x['reserve_audit']['displaced']) for x in xs if x['reserve_audit']);groups[f+':'+c]=dict(exact=e,error=err,protected=protect,displaced=displace,success_use=sum(x['exact'] and x['uses_transfer'] for x in xs),seconds=sum(x['elapsed_seconds'] for x in xs),solution_costs={k:[x[k] for x in xs if x['exact']] for k in ['primitives','routing_bits','depth']},generated=sum(x['generated_unique_signatures'] for x in xs));lines.append(f"| {f} | {c} | {sum(x['exact'] for x in xs)}/24 | {e['mean']:.4f}/{e['variance']:.4f} | {err['mean']:.4f}/{err['variance']:.4f} | {groups[f+':'+c]['success_use']} | {protect}/{displace} |")
lines+=['','| learned reserve − control | mean | variance | 95% CI | dz | p | Holm p |','| --- | ---: | ---: | --- | ---: | ---: | ---: |']
for k,v in list(primary.items())+list(secondary.items()):lines.append(f"| {k} | {v['mean']:+.4f} | {v['variance']:.5f} | {v['ci95']} | {v['dz']} | {v['p']:.5f} | {v['holm_p']:.5f} |")
lines+=['',f"校正gate={gate}、learned reserve成功使用{uses}、240探索{r['search_seconds']:.1f}秒、preflight {sum(x['seconds'] for x in pre):.1f}秒。{solutions}成功式、{verified}保持式、source8/random384式の全入力/費用、progress/hashと幅を監査。",'成功使用はsignatureの構文的出現であり学習provenance保証ではない。記号式cost16と記述量・物理DAG・実行性能は別。','', '🟢 [Done] 通常候補の排除費用を含め、固定容量で一段保持枠を校正した。','🟠 [Next] 同じcohortの保護候補が残り一段で解へ合成できるかを機構診断し、費用優先rankが必要な情報を落としているかを調べる。保持枠数の事後探索やseed追加を先行しない。','🔴 [Later] 独立意味確認後にState/Router/Expert交換と物理費用。','', 'English: A target-independent one-round reserve was calibrated at fixed total beam width192, including displaced ordinary candidates. Calibration is separate from independent confirmation.','', '简体中文：在总beam宽度192固定下校准目标无关的单轮保留槽，并计入被挤出的普通候选。校准与独立确认分开。']
lines+=['','2026-10-09。E052の停止済み233条件は変更せず、E053の別chunkで残り7条件を完了した。全240条件でnumeric12/24、route21/24。主3差と副次6差は全て0、Holm p=1、learned reserve成功使用0、gate未達。learnedの保護384枠と通常候補の排除384件は実際に発生したが精度利益を確認できなかった。枝刈りで失われた候補を保持するだけでは、このpolicyで改善しない。', '', 'English: Completing the seven fixed conditions left all five conditions equal: numeric12/24 and routing21/24. All preregistered exact contrasts were zero (Holm p=1), with zero successful learned reserve use. Protecting384 learned candidate slots displaced384 ordinary entries but did not improve exact accuracy.','', '简体中文：完成7个固定剩余条件后，5种条件均为数值12/24、路由21/24。预注册exact差全部为0（Holm p=1），学习保留候选成功使用为0。384个学习保护槽挤出384个普通候选，但没有提高exact准确率。','', '⭕️ [Pending] 物理PE/GPU実デバイス性能はCPU記号探索では未検証。']
summary=dict(primary=primary,secondary=secondary,gate=gate,uses=uses,groups=groups,records=240,solutions=solutions,verified_selected=verified,seconds=r['search_seconds'],analysis_hash=hashlib.sha256((HERE/'report.py').read_bytes()).hexdigest());(OUT/'audit_summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False));(HERE/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(dict(primary=primary,gate=gate,uses=uses,groups={k:{'success':sum(v['exact']['values'])*4,'protect':v['protected'],'displace':v['displaced']} for k,v in groups.items()},seconds=r['search_seconds']),indent=2))
