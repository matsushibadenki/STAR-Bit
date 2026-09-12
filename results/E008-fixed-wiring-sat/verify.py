"""Validate encoding fixtures and witness functions without new synthesis budgets."""
import json
from pathlib import Path
import numpy as np
import z3
from solve import build,evaluate,data

def fixtures():
    x=(np.arange(16)[:,None]>>np.arange(4))&1
    truth=((0xCA61>>np.arange(16))&1)
    ctx,s,t=build(x,truth[:,None],[[0,1,2,3]],[4])
    for b,value in zip(t[0],truth):s.add(b==bool(value))
    assert s.check()==z3.sat
    assert np.array_equal(evaluate(x,[[0,1,2,3]],[truth],[4]),truth[:,None])
    ctx,s,t=build(x,x[:,3:4],[[0,1,2,2]],[4])
    assert s.check()==z3.unsat
    return dict(fixed_nonsymmetric_lut4_sat=True,lut4_missing_input_unsat=True)

def main():
    root=Path(__file__).resolve().parent
    tests=fixtures()
    old=root.parent/'E007-full-domain/run'
    prior=json.loads((old/'results.json').read_text())
    known=[]
    for r in prior['records']:
        if r['training']!='full64':continue
        if r['observations']['1600']['hard_all']['exact']!=1.:continue
        name=f"{r['task']}-{r['seed']}-{r['condition']}"
        saved=np.load(old/f'{name}-full64-1600.npz')
        wires=saved['pair0'].tolist()+saved['pair1'].tolist()+saved['head'].tolist()
        tables=[]
        for layer in (0,1):
            tables.extend([((int(k)>>np.arange(4))&1).tolist() for k in saved[f'w{layer}'].argmax(1)])
        if r['condition']=='gate2':tables.extend([((int(k)>>np.arange(4))&1).tolist() for k in saved['w2'].argmax(1)])
        else:tables.extend((saved['w2']>=0).astype(int).tolist())
        x,y=data(r['task']);outputs=[70,71,72,73]
        assert np.array_equal(evaluate(x,wires,tables,outputs),y)
        known.append(dict(name=name,task=r['task'],seed=r['seed'],condition=r['condition'],exact=1.))
        (root/'run'/f'{name}-prior-witness.json').write_text(json.dumps(dict(wires=wires,tables=tables,outputs=outputs),indent=2))
    (root/'run/additional_checks.json').write_text(json.dumps(dict(fixtures=tests,known_trained_witnesses=known),indent=2)+'\n')
    print(tests,'Prior independently validated witnesses:',known)

if __name__=='__main__':main()
