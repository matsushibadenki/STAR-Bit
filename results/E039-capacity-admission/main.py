"""E039 delayed admission: fixed-width replacement versus temporary capacity addition."""
import hashlib
import importlib.util
import json
import math
import os
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('/Users/littlebuddha/Desktop/alias/STAR-Bit')
OUT = Path(os.environ.get('E039_OUT', str(HERE / 'run')))
E019 = ROOT / 'results/E019-function-space-genesis'
E023 = ROOT / 'results/E023-leave-one-task-out-transfer'
E024 = ROOT / 'results/E024-probe-utility-diversity'
E026 = ROOT / 'results/E026-counterfactual-admission'
E028 = ROOT / 'results/E028-module-causal-ablation'
E031 = ROOT / 'results/E031-route-family-portability'
E033 = ROOT / 'results/E033-grammar-pilot'
E035 = ROOT / 'results/E035-numeric-grammar'
E038 = ROOT / 'results/E038-timed-admission'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


e038 = load('e038_for_e039', E038 / 'main.py')
e031 = e038.e031
e026 = e038.e026
e028 = e038.e028
e024 = e038.e024
e023 = e038.e023
base = e038.base
features = e038.features


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tasks_from_grammar():
    def route_pair(bits):
        return (bits[2] if bits[0] else bits[4]), (bits[5] if bits[3] else bits[1])
    functions = {
        'numeric_rotated_weight_ge6': lambda b: sum(x * w for x, w in zip(b, (3, 1, 2, 1, 3, 2))) >= 6,
        'route_cross_implies': lambda b: (not route_pair(b)[0]) or route_pair(b)[1],
    }
    return {name: e031.signature(function) for name, function in functions.items()}


def scheduled_search(seed, target, module, beam_size, rounds, condition, max_cost=16):
    assert condition in ('no_transfer', 'learned_replace', 'learned_add', 'inert_replace', 'inert_add', 'random_replace', 'random_add')
    assert (module is None) == (condition == 'no_transfer')
    inputs, _ = base.inputs_and_targets()
    beam = [base.Candidate(signature, 0, 0, 0, ('input', index)) for index, signature in enumerate(inputs)]
    library_signatures = set() if module is None else {module.signature}
    credit, partners, last = {}, {}, {}
    solution = None
    best, history, generated = 64, [], len(beam)
    first_round_selected = []
    injection_strategy = None if condition == 'no_transfer' else condition.rsplit('_', 1)[1]
    inert = condition.startswith('inert_')
    injected_collision = False
    slot_replaced_signature = None
    round_two_input_width = None
    started = time.monotonic()
    for round_index in range(1, rounds + 1):
        if round_index == 2:
            round_two_input_width = len(beam)
        pool = {candidate.signature: candidate for candidate in beam}
        edges = []
        for index, left in enumerate(beam):
            for right in beam[index:]:
                if inert and (left.signature == module.signature or right.signature == module.signature):
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
        for signature in [signature for signature, last_seen in last.items() if round_index - last_seen > 2]:
            credit.pop(signature, None); partners.pop(signature, None); last.pop(signature, None)
        beam = e026.select(pool, target, beam_size, seed, round_index, credit, partners, last)
        if round_index == 1 and module is not None:
            first_round_selected = [str(candidate.signature) for candidate in beam]
            collision_index = next((index for index, candidate in enumerate(beam) if candidate.signature == module.signature), None)
            injected_collision = collision_index is not None
            if collision_index is not None:
                slot_replaced_signature = str(beam[collision_index].signature)
                beam[collision_index] = module
            elif injection_strategy == 'replace':
                slot_replaced_signature = str(beam[-1].signature)
                beam[-1] = module
                generated += 1
            else:
                beam.append(module)
                generated += 1
        elif round_index == 1:
            first_round_selected = [str(candidate.signature) for candidate in beam]
    used = [] if solution is None else sorted(e023.expression_signatures(solution.expression) & library_signatures)
    return {'exact': solution is not None, 'round': None if solution is None else round_index, 'best_error': best, 'best_error_history': history, 'uses_transfer': bool(used), 'used_signatures': [str(signature) for signature in used], 'expression': None if solution is None else solution.expression, 'primitives': None if solution is None else solution.primitives, 'routing_bits': None if solution is None else solution.routing_bits, 'depth': None if solution is None else solution.depth, 'generated_unique_signatures': generated, 'elapsed_seconds': time.monotonic() - started, 'first_round_selected': first_round_selected, 'injection_strategy': injection_strategy, 'injected_collision': injected_collision, 'slot_replaced_signature': slot_replaced_signature, 'round_two_input_width': round_two_input_width}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    targets = tasks_from_grammar()
    old = set(e038.e037.e035.tasks_from_grammar()[1].values()) | set(e038.e037.e035.e033.tasks_from_grammar().values()) | set(e031.task_signatures().values())
    assert len(set(targets.values())) == 2 and not (set(targets.values()) & old)
    budgets = {'numeric_rotated_weight_ge6': {'beam': 192, 'rounds': 6}, 'route_cross_implies': {'beam': 128, 'rounds': 4}}
    admitted, frozen_function = e028.frozen()
    inputs, old_targets = base.inputs_and_targets(); probes, evaluations = e024.task_signatures()
    forbidden = set(inputs) | set(old_targets.values()) | set(probes.values()) | set(evaluations.values()) | old | set(targets.values()) | {admitted.signature}
    seeds = list(range(1540, 1546))
    conditions = ['no_transfer', 'learned_replace', 'learned_add', 'inert_replace', 'inert_add', 'random_replace', 'random_add']
    random_libraries, random_manifest, used_random = {}, [], set()
    for seed in seeds:
        for task_index, task in enumerate(targets):
            candidate, draws = e031.random_matched(admitted, seed * 59 + task_index, forbidden | used_random)
            assert candidate.signature not in used_random and candidate.cost() == admitted.cost()
            used_random.add(candidate.signature); random_libraries[seed, task] = candidate
            random_manifest.append({'seed': seed, 'task': task, 'signature': str(candidate.signature), 'expression': candidate.expression, 'cost': candidate.cost(), 'draws': draws})
    settings = {'seeds': seeds, 'tasks': list(targets), 'conditions': conditions, 'budgets': budgets, 'max_cost': 16}
    (OUT / 'frozen_manifest.json').write_text(json.dumps({'settings': settings, 'targets': {task: str(target) for task, target in targets.items()}, 'positive_class_counts': {task: target.bit_count() for task, target in targets.items()}, 'admitted': frozen_function, 'random_matched': random_manifest}, indent=2, allow_nan=False))
    records, started = [], time.monotonic()
    with (OUT / 'progress.jsonl').open('w') as progress:
        for seed in seeds:
            for task, target in targets.items():
                budget = budgets[task]
                for condition in conditions:
                    if sum(row['elapsed_seconds'] for row in records) >= 900:
                        (OUT / 'incomplete.json').write_text(json.dumps({'completed': len(records), 'expected': 84, 'search_seconds': sum(row['elapsed_seconds'] for row in records)}, indent=2)); return
                    module = None if condition == 'no_transfer' else random_libraries[seed, task] if condition.startswith('random_') else admitted
                    row = scheduled_search(seed, target, module, budget['beam'], budget['rounds'], condition)
                    row.update({'seed': seed, 'task': task, 'family': 'numeric' if task.startswith('numeric_') else 'route', 'condition': condition, 'beam': budget['beam'], 'round_budget': budget['rounds'], 'library_signatures': [] if module is None else [str(module.signature)]})
                    records.append(row); progress.write(json.dumps(row, allow_nan=False) + '\n'); progress.flush()
                    print(seed, task, condition, int(row['exact']), row['best_error'], flush=True)
    assert len(records) == 84
    sources = (HERE / 'main.py', HERE / 'PROTOCOL.md', E038 / 'main.py', E038 / 'run/results.json', E035 / 'main.py', E033 / 'main.py', E031 / 'main.py', E028 / 'main.py', E026 / 'main.py', E026 / 'run/admission.json', E024 / 'main.py', E023 / 'main.py', E019 / 'search.py', E019 / 'search_v2.py')
    result = {'records': records, 'settings': settings, 'elapsed_seconds': time.monotonic() - started, 'search_seconds': sum(row['elapsed_seconds'] for row in records), 'sources': {str(path.relative_to(ROOT)): sha(path) for path in sources}}
    (OUT / 'results.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps({'completed': len(records), 'search_seconds': result['search_seconds'], 'elapsed_seconds': result['elapsed_seconds']}, indent=2))


if __name__ == '__main__':
    main()
