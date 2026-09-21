"""E030 provenance-aware E026 search and one-hop propagation barrier."""
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
OUT = Path(os.environ.get('E030_OUT', str(HERE / 'run')))
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


e028 = load('e028_for_e030', E028 / 'main.py')
base = e028.base
features = e028.features
e023 = e028.e023
e024 = e028.e024
e026 = e028.e026


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expression_contains(expression, signature):
    return expression[0] != 'input' and (int(expression[1]) == signature or expression_contains(expression[3], signature) or expression_contains(expression[4], signature))


def provenance_search(seed, target, library, barrier=False, beam_size=128, rounds=6, max_cost=16):
    inputs, _ = base.inputs_and_targets()
    module_signature = None if not library else library[0].signature
    library_signatures = {candidate.signature for candidate in library}
    beam = [base.Candidate(signature, 0, 0, 0, ('input', index)) for index, signature in enumerate(inputs)] + list(library)
    credit, partners, last = {}, {}, {}
    solution = None
    best = 64
    history = []
    trace = []
    generated = len(beam)
    started = time.monotonic()
    for round_index in range(1, rounds + 1):
        before = {candidate.signature for candidate in beam}
        tainted = {candidate.signature: module_signature is not None and expression_contains(candidate.expression, module_signature) for candidate in beam}
        pool = {candidate.signature: candidate for candidate in beam}
        generators = {}
        edges = []
        for left_index, left in enumerate(beam):
            for right in beam[left_index:]:
                parent_tainted = tainted[left.signature] or tainted[right.signature]
                if barrier and round_index >= 2 and parent_tainted:
                    continue
                primitives = left.primitives + right.primitives + 1
                if primitives > max_cost:
                    continue
                routing = left.routing_bits + right.routing_bits + 2 * math.ceil(math.log2(6 + max(1, primitives)))
                depth = max(left.depth, right.depth) + 1
                for code, signature in enumerate(base.lut_outputs(left.signature, right.signature)):
                    provenance = generators.setdefault(signature, {'tainted': False, 'clean': False})
                    provenance['tainted' if parent_tainted else 'clean'] = True
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
        for signature in [signature for signature, value in last.items() if round_index - value > 2]:
            credit.pop(signature, None)
            partners.pop(signature, None)
            last.pop(signature, None)
        selected = e026.select(pool, target, beam_size, seed, round_index, credit, partners, last)
        details = []
        for candidate in selected:
            provenance = generators.get(candidate.signature, {'tainted': False, 'clean': False})
            details.append({
                'signature': str(candidate.signature),
                'selected_contains_module': module_signature is not None and expression_contains(candidate.expression, module_signature),
                'tainted_generator_available': provenance['tainted'],
                'clean_generator_available': provenance['clean'],
                'carried_from_prior': candidate.signature in before,
                'primitives': candidate.primitives,
                'routing_bits': candidate.routing_bits,
                'depth': candidate.depth,
                'credit': credit.get(candidate.signature, 0),
                'partner_count': len(partners.get(candidate.signature, set())),
            })
        trace.append({'round': round_index, 'selected': details})
        beam = selected
    used = [] if solution is None else sorted(e023.expression_signatures(solution.expression) & library_signatures)
    return {
        'exact': solution is not None,
        'round': None if solution is None else round_index,
        'best_error': best,
        'best_error_history': history,
        'uses_transfer': bool(used),
        'used_signatures': [str(signature) for signature in used],
        'expression': None if solution is None else solution.expression,
        'primitives': None if solution is None else solution.primitives,
        'routing_bits': None if solution is None else solution.routing_bits,
        'depth': None if solution is None else solution.depth,
        'generated_unique_signatures': generated,
        'elapsed_seconds': time.monotonic() - started,
        'trace': trace,
    }


def metric(values):
    array = np.asarray(values, float)
    return {'mean': float(array.mean()), 'variance': None if len(array) < 2 else float(array.var(ddof=1))}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    admitted, frozen_row = e028.frozen()
    inputs, _ = base.inputs_and_targets()
    expression = e028.rotate(admitted.expression, 1, inputs)
    rotated = base.Candidate(e023.evaluate(expression, inputs), *admitted.cost(), expression)
    assert e023.expression_cost(expression) == admitted.cost() == rotated.cost()
    _, _, _, evaluations = e024.select_libraries()
    tasks = ('eval_dual_mux_xor', 'eval_threshold2')
    (OUT / 'frozen_library.json').write_text(json.dumps({'admitted': frozen_row, 'rotate1': {'signature': str(rotated.signature), 'expression': rotated.expression, 'cost': rotated.cost()}}, indent=2))
    target = evaluations['eval_dual_mux_xor']
    smoke = provenance_search(1429, target, [rotated], rounds=3)
    baseline = e026.search(1429, target, [rotated], 128, 3, save_expression=True)
    keys = ('exact', 'round', 'best_error_history', 'generated_unique_signatures', 'expression', 'uses_transfer')
    for key in keys:
        assert smoke[key] == baseline[key], key
    (OUT / 'smoke.json').write_text(json.dumps({'seed': 1429, 'rounds': 3, 'matched_keys': list(keys)}, indent=2))
    conditions = ('no_transfer', 'rotate1', 'one_hop_barrier')
    records = []
    started = time.monotonic()
    with (OUT / 'progress.jsonl').open('w') as progress:
        for seed in range(1430, 1446):
            for task in tasks:
                target = evaluations[task]
                for condition in conditions:
                    library = [] if condition == 'no_transfer' else [rotated]
                    row = provenance_search(seed, target, library, barrier=condition == 'one_hop_barrier')
                    row.update({'seed': seed, 'task': task, 'condition': condition, 'library_signatures': [str(candidate.signature) for candidate in library]})
                    records.append(row)
                    progress.write(json.dumps(row) + '\n')
                    progress.flush()
                    print(seed, task, condition, int(row['exact']), row['round'], flush=True)
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
        'settings': {'seeds': list(range(1430, 1446)), 'tasks': list(tasks), 'conditions': list(conditions), 'beam': 128, 'rounds': 6, 'max_cost': 16},
        'elapsed_seconds': time.monotonic() - started,
        'sources': {str(path.relative_to(ROOT)): sha(path) for path in sources},
    }
    (OUT / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({'aggregate': aggregate, 'elapsed_seconds': result['elapsed_seconds']}, indent=2))


if __name__ == '__main__':
    main()
