import hashlib,importlib.util,json,time
from pathlib import Path
ROOT=Path('/Users/littlebuddha/Desktop/alias/STAR-Bit'); HERE=ROOT/'results/E053-reserve-calibration-completion'; OLD=ROOT/'results/E052-one-round-reserve-calibration'; OUT=HERE/'run'
spec=importlib.util.spec_from_file_location('e052',OLD/'main.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def main():
 OUT.mkdir(); old=json.loads((OLD/'run/results.json').read_text()); manifest=json.loads((OLD/'run/manifest.json').read_text()); missing=json.loads((OLD/'run/remaining.json').read_text()); assert len(old['records'])==233 and len(missing)==7 and not old['complete']
 for name,h in old['sources'].items(): assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h
 tasks=m.e042.tasks_from_registry(); cohort=[m.base.Candidate(int(c['signature']),c['primitives'],c['routing_bits'],c['depth'],c['expression']) for c in manifest['source']]; randoms={(x['seed'],x['task']):[m.base.Candidate(int(c['signature']),c['primitives'],c['routing_bits'],c['depth'],c['expression']) for c in x['cohort']] for x in manifest['random']}; additions=[]
 with (OUT/'new_progress.jsonl').open('w') as f:
  for item in missing:
   if sum(x['elapsed_seconds'] for x in additions)>=300:break
   s,t,c=item['seed'],item['task'],item['condition']; library=[] if c=='baseline' else randoms[s,t] if c=='random_reserve' else cohort
   row=m.scheduled_search(s,tasks[t],None,128,4,'no_transfer',16,192,library,c=='inert_reserve',c.endswith('_reserve'));row.update(seed=s,task=t,condition=c,library=[str(v.signature) for v in library]);additions.append(row);f.write(json.dumps(row,allow_nan=False)+'\n');f.flush();print(s,t,c,flush=True)
 rows=old['records']+additions;assert len({(x['seed'],x['task'],x['condition']) for x in rows})==len(rows)
 paths=[HERE/'main.py',HERE/'PROTOCOL.md',OLD/'main.py',OLD/'report.py',OLD/'PROTOCOL.md',OLD/'run/results.json',OLD/'run/manifest.json',OLD/'run/preflight.json',OLD/'run/remaining.json']; hashes=dict(old['sources']);hashes.update({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
 for name in ['manifest.json','preflight.json']:(OUT/name).write_bytes((OLD/'run'/name).read_bytes())
 (OUT/'progress.jsonl').write_text(''.join(json.dumps(x,allow_nan=False)+'\n' for x in rows));(OUT/'results.json').write_text(json.dumps(dict(records=rows,complete=len(rows)==240,search_seconds=old['search_seconds']+sum(x['elapsed_seconds'] for x in additions),new_search_seconds=sum(x['elapsed_seconds'] for x in additions),sources=hashes),indent=2,allow_nan=False))
if __name__=='__main__':main()
