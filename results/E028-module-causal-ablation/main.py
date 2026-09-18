"""E028 frozen Function direct-use and input-semantics ablation."""
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = Path(os.environ.get('E028_OUT', str(HERE / 'run')))
E019 = ROOT / 'results/E019-function-space-genesis'
E023 = ROOT / 'results/E023-leave-one-task-out-transfer'
E024 = ROOT / 'results/E024-probe-utility-diversity'
E026 = ROOT / 'results/E026-counterfactual-admission'
sys.path.insert(0, str(E019))
import search as base
import search_v2 as features


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e023 = load('e023_e028', E023 / 'main.py')
e024 = load('e024_e028', E024 / 'main.py')
e026 = load('e026_e028', E026 / 'main.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen():
    data = json.loads((E026 / 'run/admission.json').read_text())
    assert len(data['selected_signatures']) == 1
    row = next(item for item in data['candidates'] if item['admitted'])
    assert row['signature'] == data['selected_signatures'][0]
    candidate = base.Candidate(int(row['signature']), row['primitives'], row['routing_bits'], row['depth'], row['expression'])
    return candidate, row


def rotate(expression, shift, inputs):
    if expression[0] == 'input':
        return ('input', (expression[1] + shift) % 6)
    left = rotate(expression[3], shift, inputs)
    right = rotate(expression[4], shift, inputs)
    signature = base.lut_outputs(e023.evaluate(left, inputs), e023.evaluate(right, inputs))[expression[2]]
    return ('lut', signature, expression[2], left, right)


def search_inert(seed, target, library, blocked, beam_size=128, rounds=6, max_cost=16, save_expression=True):
    """E026 search with only the blocked-signature pairwise-composition veto."""
    inputs, _ = base.inputs_and_targets()
    library_sigs = {candidate.signature for candidate in library}
    beam = [base.Candidate(signature, 0, 0, 0, ('input', index)) for index, signature in enumerate(inputs)] + list(library)
    credit, partners, last = {}, {}, {}
    solution = None
    best = 64
    history = []
    generated = len(beam)
    started = time.monotonic()
    for round_index in range(1, rounds + 1):
        pool = {candidate.signature: candidate for candidate in beam}
        edges = []
        for index, left in enumerate(beam):
            for right in beam[index:]:
                if left.signature in blocked or right.signature in blocked:
                    continue
                primitives = left.primitives + right.primitives + 1
                if primitives > max_cost:
                    continue
                routing = left.routing_bits + right.routing_bits + 2 * math.ceil(math.log2(6 + max(1, primitives)))
                depth = max(left.depth, right.depth) + 1
                for code, signature in enumerate(base.lut_outputs(left.signature, right.signature)):
                    candidate = base.Candidate(signature, primitives, routing, depth, ('lut', signature, code, left.expression, right.expression))
                    old = pool.get(signature)
                    if old is None:
                        pool[signature] = candidate
                        generated += 1
                    elif base.better(candidate, old):
                        pool[signature] = candidate
                    if signature not in (left.signature, right.signature):
                        edges.append((signature, left, right))
        best = min(best, min(base.error(signature, target) for signature in pool))
        history.append(best)
        if target in pool:
            solution = pool[target]
            break
        top = {candidate.signature for candidate in sorted(pool.values(), key=lambda candidate: (base.error(candidate.signature, target), *candidate.cost(), e026.stable(candidate.signature, seed, round_index)))[:128]}
        for signature, left, right in edges:
            novelty = max(0, features.support_mask(signature).bit_count() - max(features.support_mask(left.signature).bit_count(), features.support_mask(right.signature).bit_count())) if 0 < signature.bit_count() < 64 else 0
            for parent, other in ((left, right), (right, left)):
                amount = novelty + (max(0, min(base.error(parent.signature, target), base.error(other.signature, target)) - base.error(signature, target)) if signature in top else 0)
                if amount:
                    credit[parent.signature] = credit.get(parent.signature, 0) + amount
                    partners.setdefault(parent.signature, set()).add(other.signature)
                    last[parent.signature] = round_index
        for signature in [signature for signature, index in last.items() if round_index - index > 2]:
            credit.pop(signature, None)
            partners.pop(signature, None)
            last.pop(signature, None)
        beam = e026.select(pool, target, beam_size, seed, round_index, credit, partners, last)
    used = [] if solution is None else sorted(e023.expression_signatures(solution.expression) & library_sigs)
    return {
        'exact': solution is not None,
        'round': None if solution is None else round_index,
        'best_error': best,
        'best_error_history': history,
        'uses_transfer': bool(used),
        'used_signatures': [str(signature) for signature in used],
        'expression': None if solution is None or not save_expression else solution.expression,
        'primitives': None if solution is None else solution.primitives,
        'routing_bits': None if solution is None else solution.routing_bits,
        'depth': None if solution is None else solution.depth,
        'generated_unique_signatures': generated,
        'elapsed_seconds': time.monotonic() - started,
    }


def metric(values):
    array = np.asarray(values, float)
    return {'mean': float(array.mean()), 'variance': float(array.var(ddof=1))}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    admitted, frozen_row = frozen()
    inputs, _ = base.inputs_and_targets()
    _, _, _, evaluations = e024.select_libraries()
    tasks = ('eval_dual_mux_xor', 'eval_threshold2')
    shifts = {}
    for shift in (1, 2):
        expression = rotate(admitted.expression, shift, inputs)
        signature = e023.evaluate(expression, inputs)
        assert e023.expression_cost(expression) == admitted.cost()
        assert signature != admitted.signature and signature not in evaluations.values()
        shifts[f'rotate{shift}'] = base.Candidate(signature, *admitted.cost(), expression)
    assert shifts['rotate1'].signature != shifts['rotate2'].signature
    (OUT / 'frozen_library.json').write_text(json.dumps({
        'admitted': frozen_row,
        'rotations': {name: {'signature': str(candidate.signature), 'expression': candidate.expression, 'cost': candidate.cost()} for name, candidate in shifts.items()},
    }, indent=2))
    conditions = ('no_transfer', 'admitted', 'inert_signature', 'rotate1', 'rotate2')
    records = []
    started = time.monotonic()
    for seed in range(1390, 1406):
        for task in tasks:
            target = evaluations[task]
            for condition in conditions:
                library = [] if condition == 'no_transfer' else [shifts[condition]] if condition in shifts else [admitted]
                if condition == 'inert_signature':
                    row = search_inert(seed, target, library, {admitted.signature})
                else:
                    row = e026.search(seed, target, library, 128, 6, save_expression=True)
                row.update({'seed': seed, 'task': task, 'condition': condition, 'library_signatures': [str(item.signature) for item in library]})
                records.append(row)
                (OUT / 'progress.json').write_text(json.dumps(records, indent=2))
                print(seed, task, condition, int(row['exact']), row['round'], flush=True)
    aggregate = {}
    for condition in conditions:
        subset = [row for row in records if row['condition'] == condition]
        aggregate[condition] = {
            'exact': metric([row['exact'] for row in subset]),
            'exact_by_task': {task: sum(row['exact'] for row in subset if row['task'] == task) for task in tasks},
            'uses_transfer': sum(row['exact'] and row['uses_transfer'] for row in subset),
            'best_error': metric([row['best_error'] for row in subset]),
            'elapsed_seconds': metric([row['elapsed_seconds'] for row in subset]),
            'primitives': metric([row['primitives'] for row in subset if row['primitives'] is not None]),
        }
    sources = (HERE / 'main.py', HERE / 'PROTOCOL.md', E026 / 'main.py', E026 / 'run/admission.json', E024 / 'main.py', E023 / 'main.py', E019 / 'search.py', E019 / 'search_v2.py')
    result = {
        'records': records,
        'aggregate': aggregate,
        'settings': {'seeds': list(range(1390, 1406)), 'tasks': list(tasks), 'conditions': list(conditions), 'beam': 128, 'rounds': 6, 'max_cost': 16},
        'elapsed_seconds': time.monotonic() - started,
        'sources': {str(path.relative_to(ROOT)): sha(path) for path in sources},
    }
    (OUT / 'results.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({'aggregate': aggregate, 'elapsed_seconds': result['elapsed_seconds']}, indent=2))


if __name__ == '__main__':
    main()
