"""E029 instrumented replay of the E026 signature-stable beam search."""
import hashlib
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get('E029_OUT', str(HERE / 'run')))
E019 = ROOT / 'results/E019-function-space-genesis'
E023 = ROOT / 'results/E023-leave-one-task-out-transfer'
E024 = ROOT / 'results/E024-probe-utility-diversity'
E026 = ROOT / 'results/E026-counterfactual-admission'
E028 = ROOT / 'results/E028-module-causal-ablation'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e028 = load('e028_for_e029', E028 / 'main.py')
base = e028.base
e023 = e028.e023
e024 = e028.e024
e026 = e028.e026


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_search(seed, target, library, rounds=6):
    module = None if not library else library[0]
    inputs, _ = base.inputs_and_targets()
    prior = [base.Candidate(signature, 0, 0, 0, ('input', index)) for index, signature in enumerate(inputs)] + list(library)
    snapshots = []
    original_select = e026.select

    def traced_select(pool, selection_target, beam_size, selection_seed, round_index, credit, partners, last):
        nonlocal prior
        assert selection_target == target and selection_seed == seed
        selected = original_select(pool, selection_target, beam_size, selection_seed, round_index, credit, partners, last)
        before = {candidate.signature for candidate in prior}
        direct = set()
        module_present = module is not None and module.signature in before
        if module_present:
            for other in prior:
                if module.primitives + other.primitives + 1 <= 16:
                    direct.update(base.lut_outputs(module.signature, other.signature))
        selected_signatures = {candidate.signature for candidate in selected}
        selected_direct = sorted((selected_signatures & direct) - before)
        contained = 0 if module is None else sum(module.signature in e023.expression_signatures(candidate.expression) for candidate in selected)
        snapshots.append({
            'round': round_index,
            'selected_signatures': [str(candidate.signature) for candidate in selected],
            'selected_direct_child_signatures': [str(signature) for signature in selected_direct],
            'module_in_prior_beam': module_present,
            'module_survives': module is not None and module.signature in selected_signatures,
            'module_credit': 0 if module is None else credit.get(module.signature, 0),
            'module_partner_count': 0 if module is None else len(partners.get(module.signature, set())),
            'selected_expression_contains_module': contained,
            'pool_best_error': min(base.error(signature, target) for signature in pool),
            'pool_size': len(pool),
        })
        prior = selected
        return selected

    e026.select = traced_select
    try:
        result = e026.search(seed, target, library, 128, rounds, save_expression=True)
    finally:
        e026.select = original_select
    result['trace'] = snapshots
    return result


def metric(values):
    array = np.asarray(values, float)
    return {'mean': float(array.mean()), 'variance': None if len(array) < 2 else float(array.var(ddof=1))}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    admitted, frozen_row = e028.frozen()
    inputs, _ = base.inputs_and_targets()
    expression = e028.rotate(admitted.expression, 1, inputs)
    rotated = base.Candidate(e023.evaluate(expression, inputs), *admitted.cost(), expression)
    assert rotated.signature != admitted.signature
    assert e023.expression_cost(expression) == admitted.cost() == rotated.cost()
    _, _, _, evaluations = e024.select_libraries()
    tasks = ('eval_dual_mux_xor', 'eval_threshold2')
    (OUT / 'frozen_library.json').write_text(json.dumps({
        'admitted': frozen_row,
        'rotate1': {'signature': str(rotated.signature), 'expression': rotated.expression, 'cost': rotated.cost()},
    }, indent=2))
    smoke_traced = trace_search(1409, evaluations['eval_dual_mux_xor'], [], rounds=2)
    smoke_base = e026.search(1409, evaluations['eval_dual_mux_xor'], [], 128, 2, save_expression=True)
    for key in ('exact', 'round', 'best_error_history', 'generated_unique_signatures', 'expression'):
        assert smoke_traced[key] == smoke_base[key], key
    (OUT / 'smoke.json').write_text(json.dumps({'seed': 1409, 'rounds': 2, 'matched_keys': ['exact', 'round', 'best_error_history', 'generated_unique_signatures', 'expression']}, indent=2))
    records = []
    started = time.monotonic()
    with (OUT / 'progress.jsonl').open('w') as progress:
        for seed in range(1410, 1426):
            for task in tasks:
                target = evaluations[task]
                for condition, library in (('no_transfer', []), ('admitted', [admitted]), ('rotate1', [rotated])):
                    row = trace_search(seed, target, library)
                    row.update({'seed': seed, 'task': task, 'condition': condition, 'library_signatures': [str(candidate.signature) for candidate in library]})
                    records.append(row)
                    progress.write(json.dumps(row) + '\n')
                    progress.flush()
                    print(seed, task, condition, int(row['exact']), row['round'], flush=True)
    conditions = ('no_transfer', 'admitted', 'rotate1')
    aggregate = {}
    for condition in conditions:
        rows = [row for row in records if row['condition'] == condition]
        aggregate[condition] = {
            'exact_by_task': {task: sum(row['exact'] for row in rows if row['task'] == task) for task in tasks},
            'exact': metric([row['exact'] for row in rows]),
            'best_error': metric([row['best_error'] for row in rows]),
            'elapsed_seconds': metric([row['elapsed_seconds'] for row in rows]),
            'uses_transfer': sum(row['exact'] and row['uses_transfer'] for row in rows),
        }
    sources = (HERE / 'main.py', HERE / 'PROTOCOL.md', E028 / 'main.py', E026 / 'main.py', E026 / 'run/admission.json', E024 / 'main.py', E023 / 'main.py', E019 / 'search.py', E019 / 'search_v2.py')
    result = {
        'records': records,
        'aggregate': aggregate,
        'settings': {'seeds': list(range(1410, 1426)), 'tasks': list(tasks), 'conditions': list(conditions), 'beam': 128, 'rounds': 6, 'max_cost': 16},
        'elapsed_seconds': time.monotonic() - started,
        'sources': {str(path.relative_to(ROOT)): sha(path) for path in sources},
    }
    (OUT / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({'aggregate': aggregate, 'elapsed_seconds': result['elapsed_seconds']}, indent=2))


if __name__ == '__main__':
    main()
