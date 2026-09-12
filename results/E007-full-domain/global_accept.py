"""E003: training-description acceptance; protocol in docs/RESEARCH-LOG.md."""
import copy
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np

import logic_modules as lm
from pilot import comparison, holm, summary


def fit(train, mode, seed):
    library, stages, history = {}, [], []
    rng = random.Random(seed + 50000)
    trials = 0
    for _ in range(3):
        before = lm.description(train, library)
        if mode != 'global_accept':
            lookup = lm.discover(train, library, mode, rng)
            train = [lm.rewrite(p, lookup, library, mode) for p in train]
            stages.append(lookup)
        else:
            proposals = copy.deepcopy(library)
            lookup = lm.discover(train, proposals, 'functional', rng)
            pool = [(key, proposals[name]) for key, name in lookup.items()]
            while pool:
                best = None
                cost = lm.description(train, library)
                for index, (key, entry) in enumerate(pool):
                    name = f'N{len(library):03d}'
                    trial_library = {**library, name: entry}
                    trial_lookup = {key: name}
                    trial_train = [lm.rewrite(p, trial_lookup, trial_library, 'functional') for p in train]
                    trial_cost = lm.description(trial_train, trial_library)
                    trials += 1
                    if trial_cost < cost:
                        cost = trial_cost
                        best = index, trial_library, trial_lookup, trial_train
                if best is None: break
                index, library, step, train = best
                stages.append(step)
                pool.pop(index)
        after = lm.description(train, library)
        if mode == 'global_accept': assert after <= before
        history.append(dict(before=before, after=after))
    return library, stages, history, trials


def run():
    out = Path('results/E003-global-accept')
    out.mkdir(parents=True, exist_ok=False)
    rows = []
    for seed in range(100,116):
        for task in ('numeric','selection'):
            train = lm.workload(seed,task,12,3)
            test = lm.workload(seed+10000,task,8,5)
            inputs = {f'x{i}': ((np.arange(2048)>>i)&1).astype(bool) for i in range(11)}
            for mode in ('syntax','functional','random','global_accept'):
                start = time.perf_counter()
                library, stages, history, trials = fit(train,mode,seed)
                seconds = time.perf_counter()-start
                compiled = test
                for lookup in stages:
                    compiled=[lm.rewrite(p,lookup,library,'syntax' if mode=='syntax' else 'functional') for p in compiled]
                expanded=[lm.expand(p,library) for p in compiled]
                assert all(np.array_equal(lm.evaluate(a,inputs,{}),lm.evaluate(b,inputs,library)) for a,b in zip(test,compiled))
                assert all(np.array_equal(lm.evaluate(a,inputs,{}),lm.evaluate(b,inputs,{})) for a,b in zip(test,expanded))
                rows.append(dict(seed=seed,task=task,condition=mode,
                                 description_symbols=lm.description(compiled,library),train_symbols=history[-1]['after'],
                                 modules=len(library),fit_seconds=seconds,candidate_trials=trials,history=history,
                                 original_dag_gates=len(set(n for p in test for n in lm.nodes(p))),
                                 expanded_dag_gates=len(set(n for p in expanded for n in lm.nodes(p))),
                                 exact_accuracy=1.,library=library))
    contrasts=[]
    for task in ('numeric','selection'):
        by={(r['seed'],r['condition']):r for r in rows if r['task']==task}
        contrasts.append(dict(task=task,**comparison([by[s,'functional']['description_symbols']-by[s,'global_accept']['description_symbols'] for s in range(100,116)])))
    holm(contrasts)
    aggregate=[]
    for task in ('numeric','selection'):
        for mode in ('syntax','functional','random','global_accept'):
            group=[r for r in rows if r['task']==task and r['condition']==mode]
            aggregate.append(dict(task=task,condition=mode,metrics={k:summary([r[k] for r in group]) for k in ('description_symbols','train_symbols','modules','fit_seconds','candidate_trials','expanded_dag_gates')}))
    sources={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('experiments/global_accept.py','experiments/logic_modules.py','experiments/pilot.py')}
    result=dict(seeds=list(range(100,116)),records=rows,aggregates=aggregate,contrasts=contrasts,source_hashes=sources)
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(contrasts,indent=2))


if __name__=='__main__': run()
