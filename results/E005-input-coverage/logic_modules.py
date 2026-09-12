"""Circuit-library discovery pilot. Source circuits supplied; no neural training."""
import collections
import hashlib
import itertools
import json
import random
from pathlib import Path

import numpy as np

from pilot import comparison, holm, summary


def apply(op, args, library):
    if op == 'AND': return args[0] & args[1]
    if op == 'OR': return args[0] | args[1]
    if op == 'XOR': return args[0] ^ args[1]
    if op == 'NOT': return ~args[0]
    entry = library[op]
    index = sum(a.astype(int) << i for i, a in enumerate(args))
    return np.asarray(entry['table'], dtype=bool)[index]


def evaluate(expr, inputs, library):
    if isinstance(expr, str): return inputs[expr]
    return apply(expr[0], [evaluate(c, inputs, library) for c in expr[1:]], library)


def nodes(expr):
    if isinstance(expr, tuple):
        yield expr
        for child in expr[1:]: yield from nodes(child)


def cut(expr):
    """Two operation levels; arbitrary boundary subexpressions become ports."""
    ports = []
    def visit(e, depth):
        if depth == 0 or isinstance(e, str):
            if e not in ports: ports.append(e)
            return f'p{ports.index(e)}'
        return (e[0], *(visit(c, depth-1) for c in e[1:]))
    pattern = visit(expr, 2)
    return pattern, ports


def signature(pattern, arity, library):
    inputs = {f'p{i}': ((np.arange(2**arity) >> i) & 1).astype(bool) for i in range(arity)}
    return tuple(int(v) for v in evaluate(pattern, inputs, library))


def discover(programs, library, mode, rng):
    candidates = {}
    for task_id, program in enumerate(programs):
        for expr in nodes(program):
            pattern, ports = cut(expr)
            n = len(list(nodes(pattern)))
            if not 2 <= n or not 1 <= len(ports) <= 4: continue
            table = signature(pattern, len(ports), library)
            key = (len(ports), table) if mode != 'syntax' else pattern
            c = candidates.setdefault(key, dict(pattern=pattern, table=table, arity=len(ports), count=0, tasks=set(), size=n))
            c['count'] += 1
            c['tasks'].add(task_id)
    # Description symbols only: definition cost + one name per call. This is
    # neither a bit-accurate code length nor a physical area estimate.
    ranked = []
    for key, c in candidates.items():
        c['gain'] = c['count'] * (c['size']-1) - c['size']
        if c['gain'] > 0 and len(c['tasks']) >= 2: ranked.append((key, c))
    if mode == 'random': rng.shuffle(ranked)
    else: ranked.sort(key=lambda item: (-item[1]['gain'], repr(item[0])))
    selected = ranked[:8]
    lookup = {}
    for key, c in selected:
        name = f'M{len(library):03d}'
        library[name] = {k: v for k, v in c.items() if k != 'tasks'}
        library[name]['task_count'] = len(c['tasks'])
        library[name]['level'] = 1 + max([library[e[0]]['level'] for e in nodes(c['pattern']) if e[0] in library] or [0])
        lookup[key] = name
    return lookup


def rewrite(expr, lookup, library, mode):
    if isinstance(expr, str): return expr
    pattern, ports = cut(expr)
    key = pattern if mode == 'syntax' else (len(ports), signature(pattern, len(ports), library)) if len(ports) <= 4 else None
    if key in lookup:
        return (lookup[key], *(rewrite(p, lookup, library, mode) for p in ports))
    return (expr[0], *(rewrite(c, lookup, library, mode) for c in expr[1:]))


def substitute(expr, values):
    if isinstance(expr, str): return values[expr]
    return (expr[0], *(substitute(c, values) for c in expr[1:]))


def expand(expr, library):
    if isinstance(expr, str): return expr
    args = tuple(expand(c, library) for c in expr[1:])
    if expr[0] in library:
        return expand(substitute(library[expr[0]]['pattern'], {f'p{i}': a for i, a in enumerate(args)}), library)
    return (expr[0], *args)


def live_library(programs, library):
    live = set()
    def mark(expr):
        for node in nodes(expr):
            op = node[0]
            if op in library and op not in live:
                live.add(op)
                mark(library[op]['pattern'])
    for program in programs: mark(program)
    return {k: v for k, v in library.items() if k in live}


def description(programs, library):
    return sum(len(list(nodes(p))) for p in programs) + sum(len(list(nodes(v['pattern']))) for v in library.values())


def workload(seed, task, count, width):
    rng = random.Random(seed)
    result = []
    for _ in range(count):
        variables = [f'x{i}' for i in range(2*width+1)]
        rng.shuffle(variables)
        if task == 'numeric':
            # Ripple-carry exact bit addition. Representation variants make
            # syntax and Boolean equivalence distinct; no labels given miner.
            carry = variables[-1]
            for a, b in zip(variables[:width], variables[width:2*width]):
                ab = ('XOR', a, b)
                result.append(('XOR', ab, carry))
                carry = ('OR', ('AND', a, b), ('AND', ab, carry))
            result.append(carry)
        else:
            value = variables[-1]
            for i in range(width):
                s, a = variables[i], variables[width+i]
                if rng.random() < .5:
                    value = ('OR', ('AND', s, a), ('AND', ('NOT', s), value))
                else:
                    value = ('XOR', value, ('AND', s, ('XOR', a, value)))
            result.append(value)
    return result


def schedule(programs, pe, inputs=None):
    """Unit-delay primitive gates, free wires, unlimited state; idealized."""
    unique = set(n for p in programs for n in nodes(p))
    pending, done, cycles, operations = set(unique), set(), 0, 0
    state = {} if inputs is None else dict(inputs)
    while pending:
        ready = sorted((e for e in pending if all(isinstance(c, str) or c in done for c in e[1:])), key=repr)[:pe]
        if not ready: raise AssertionError('cycle in DAG')
        if inputs is not None:
            # Each PE reads the previous cycle's state. Writes become visible
            # together at the cycle boundary; no within-cycle forwarding.
            writes = {e: apply(e[0], [state[c] for c in e[1:]], {}) for e in ready}
            state.update(writes)
        pending.difference_update(ready)
        done.update(ready)
        cycles += 1
        operations += len(ready)
    if inputs is not None:
        assert all(np.array_equal(state[p], evaluate(p, inputs, {})) for p in programs)
    return dict(pe=pe, cycles=cycles, primitive_operations=operations,
                state_bits_upper_bound=len(unique), output_bits=len(programs))


def run():
    records, comparisons = [], []
    for seed in range(16):
        for task in ('numeric', 'selection'):
            train = workload(seed, task, 12, 3)
            test = workload(seed+10000, task, 8, 5)
            inputs = {f'x{i}': ((np.arange(2**11) >> i)&1).astype(bool) for i in range(11)}
            raw = sum(len(list(nodes(p))) for p in test)
            for mode in ('syntax', 'functional', 'random'):
                library, transformed_train, transformed_test, history = {}, train, test, []
                rng = random.Random(seed+50000)
                for stage in range(3):
                    lookup = discover(transformed_train, library, mode, rng)
                    transformed_train = [rewrite(p, lookup, library, mode) for p in transformed_train]
                    transformed_test = [rewrite(p, lookup, library, mode) for p in transformed_test]
                    history.append(dict(stage=stage, modules=len(library), train_symbols=description(transformed_train, library)))
                correct = all(np.array_equal(evaluate(a, inputs, {}), evaluate(b, inputs, library)) for a, b in zip(test, transformed_test))
                assert correct
                live = live_library(transformed_test, library)
                expanded = [expand(p, library) for p in transformed_test]
                assert all(np.array_equal(evaluate(a, inputs, {}), evaluate(b, inputs, {})) for a,b in zip(test, expanded))
                # Retire everything on a distribution shift to primitive XOR.
                shifted = [('XOR', 'x0', 'x1')]
                retired = len(library)-len(live_library(shifted, library))
                records.append(dict(seed=seed, task=task, condition=mode, exact_accuracy=float(correct),
                                    raw_tree_gates=raw, description_symbols=description(transformed_test, library),
                                    amortized_symbols=description(transformed_test, live),
                                    modules=len(library), used_modules=len(live), retired_on_shift=retired,
                                    max_module_level=max([v['level'] for v in live.values()] or [0]),
                                    original_dag_gates=len(set(n for p in test for n in nodes(p))),
                                    expanded_dag_gates=len(set(n for p in expanded for n in nodes(p))),
                                    lut_truth_bits=sum(2**v['arity'] for v in library.values()),
                                    schedules=[schedule(expanded, pe, inputs) for pe in (16,32,64)],
                                    history=history, library=library))
    for task in ('numeric','selection'):
        by = {(r['seed'],r['condition']):r for r in records if r['task']==task}
        for baseline in ('syntax','random'):
            differences=[by[s,baseline]['description_symbols']-by[s,'functional']['description_symbols'] for s in range(16)]
            comparisons.append(dict(task=task,baseline=baseline,**comparison(differences)))
    holm(comparisons)
    aggregates=[]
    for task in ('numeric','selection'):
        for mode in ('syntax','functional','random'):
            rows=[r for r in records if r['task']==task and r['condition']==mode]
            aggregates.append(dict(task=task,condition=mode,metrics={key:summary([r[key] for r in rows]) for key in (
                'description_symbols','raw_tree_gates','original_dag_gates','expanded_dag_gates','modules','used_modules','max_module_level','lut_truth_bits')}))
    result=dict(seeds=16,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                records=records,aggregates=aggregates,comparisons=comparisons,
                caveat='Source circuits supplied. Exact small-cut library mining, not learning tasks from examples or semantic concepts. PE scheduling is idealized, not measured hardware.')
    Path('results/logic_modules/results.json').write_text(json.dumps(result,indent=2)+'\n')
    for row in aggregates:
        print(row['task'],row['condition'], {k:round(v['mean'],3) for k,v in row['metrics'].items()},flush=True)
    print(comparisons)


if __name__ == '__main__': run()
