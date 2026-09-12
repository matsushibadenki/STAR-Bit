"""Readback checks on final SAT witnesses and proof-DAG completeness."""
import gzip,hashlib,json
from pathlib import Path
from solve import data,evaluate
import numpy as np

def main():
    root=Path(__file__).resolve().parent;out=root/'run_bounded'
    r=json.loads((out/'results.json').read_text());counts={'witnesses':0,'complete_proof_dags':0,'partial_proof_dags':0}
    assert len(r['records'])==64
    for row in r['records']:
        name=f"{row['task']}-{row['seed']}-{row['condition']}"
        assert hashlib.sha256((out/f'{name}.smt2.gz').read_bytes()).hexdigest()==row['formula_sha256']
        if row['status']=='sat':
            witness=json.loads((out/f'{name}-witness.json').read_text())
            x,y=data(row['task'])
            assert np.array_equal(evaluate(x,witness['wires'],witness['tables'],witness['outputs']),y)
            counts['witnesses']+=1
        elif row['status']=='unsat':
            with gzip.open(out/f'{name}-proof-dag.json.gz','rt') as f:proof=json.load(f)
            assert proof['complete']==row['proof_export_complete']
            if proof['complete']:
                assert str(proof['root_id']) in proof['nodes']
                for node in proof['nodes'].values():
                    assert all(str(child) in proof['nodes'] for child in node['children'])
                    assert all(str(param['ast_id']) in proof['nodes'] for param in node['params'] if isinstance(param,dict))
                counts['complete_proof_dags']+=1
            else:counts['partial_proof_dags']+=1
        else:assert row['reason_unknown']
    for name,digest in r['sources'].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
    assert hashlib.sha256((root/'PROTOCOL.md').read_bytes()).hexdigest()==r['protocol_sha256']
    (out/'readback_audit.json').write_text(json.dumps(counts,indent=2)+'\n')
    print(counts,'Note: DAG integrity is not independent UNSAT proof validation.')

if __name__=='__main__':main()
