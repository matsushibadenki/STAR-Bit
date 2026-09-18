"""Audit E029 and report the prespecified trajectory indicators."""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / 'run'
sys.path.insert(0, str(ROOT / 'results/E019-function-space-genesis'))
import search as base


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def targets():
    functions = {
        'eval_dual_mux_xor': lambda b: (b[1] if b[0] else b[2]) ^ (b[4] if b[3] else b[5]),
        'eval_threshold2': lambda b: sum(b) >= 2,
    }
    result = {}
    for name, function in functions.items():
        signature = 0
        for row in range(64):
            signature |= int(function([(row >> index) & 1 for index in range(6)])) << row
        result[name] = signature
    return result


def evaluate(expression, inputs):
    if expression[0] == 'input':
        return inputs[expression[1]]
    signature = base.lut_outputs(evaluate(expression[3], inputs), evaluate(expression[4], inputs))[expression[2]]
    assert signature == int(expression[1])
    return signature


def signatures(expression):
    if expression[0] == 'input':
        return set()
    return {int(expression[1])} | signatures(expression[3]) | signatures(expression[4])


def signflip(differences):
    observed = abs(float(np.mean(differences)))
    extreme = 0
    total = 2 ** len(differences)
    for mask in range(total):
        mean = np.mean([value * (1 if mask & (1 << index) else -1) for index, value in enumerate(differences)])
        extreme += abs(mean) >= observed - 1e-12
    return extreme / total


def paired(values, rng):
    array = np.asarray(values, float)
    bootstrap = array[rng.integers(0, len(array), (20000, len(array)))].mean(1)
    sd = array.std(ddof=1)
    return {
        'mean': float(array.mean()),
        'unbiased_variance': float(array.var(ddof=1)),
        'ci95': np.quantile(bootstrap, [.025, .975]).tolist(),
        'cohen_dz': None if sd == 0 else float(array.mean() / sd),
        'exact_signflip_p': signflip(array),
        'differences': array.tolist(),
    }


def metric(values):
    array = np.asarray(values, float)
    return {'mean': None if len(array) == 0 else float(array.mean()), 'unbiased_variance': None if len(array) < 2 else float(array.var(ddof=1)), 'n': len(array)}


def mcnemar(left, right):
    a = sum(x and not y for x, y in zip(left, right))
    b = sum(y and not x for x, y in zip(left, right))
    n = a + b
    p = 1.0 if not n else min(1.0, 2 * sum(math.comb(n, k) for k in range(min(a, b) + 1)) / 2 ** n)
    return p, a, b


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


result = json.loads((OUT / 'results.json').read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
assert len(result['records']) == 96
assert result['settings']['seeds'] == list(range(1410, 1426))
for name, expected in result['sources'].items():
    assert sha(ROOT / name) == expected, name

library = json.loads((OUT / 'frozen_library.json').read_text())
smoke = json.loads((OUT / 'smoke.json').read_text())
assert smoke['seed'] == 1409 and smoke['rounds'] == 2
assert set(smoke['matched_keys']) == {'exact', 'round', 'best_error_history', 'generated_unique_signatures', 'expression'}
admitted = library['admitted']
rotate1 = library['rotate1']
assert admitted['signature'] == json.loads((ROOT / 'results/E026-counterfactual-admission/run/admission.json').read_text())['selected_signatures'][0]
inputs, _ = base.inputs_and_targets()
assert evaluate(admitted['expression'], inputs) == int(admitted['signature'])
assert evaluate(rotate1['expression'], inputs) == int(rotate1['signature'])
assert tuple(rotate1['cost']) == (admitted['primitives'], admitted['routing_bits'], admitted['depth'])
target = targets()
verified = 0
for row in result['records']:
    if row['expression'] is not None:
        assert row['exact'] and evaluate(row['expression'], inputs) == target[row['task']]
        verified += 1
    for snapshot in row['trace']:
        assert 1 <= snapshot['round'] <= 6
        assert len(snapshot['selected_signatures']) <= 128
        assert set(snapshot['selected_direct_child_signatures']) <= set(snapshot['selected_signatures'])

by = {(row['seed'], row['task'], row['condition']): row for row in result['records']}
seeds = result['settings']['seeds']
conditions = result['settings']['conditions']
tasks = result['settings']['tasks']
rng = np.random.default_rng(2029)
summary = {'aggregate': result['aggregate'], 'by_task': {}, 'paired': {}, 'mcnemar': {}, 'trajectory': {}, 'beam_jaccard': {}, 'module_trace': {}, 'solutions_verified': verified, 'records_verified': len(result['records']), 'report_sha256': sha(HERE / 'report.py')}

for task in tasks:
    summary['by_task'][task] = {}
    summary['mcnemar'][task] = []
    for condition in conditions:
        rows = [by[seed, task, condition] for seed in seeds]
        exact = metric([row['exact'] for row in rows])
        summary['by_task'][task][condition] = {
            'exact': exact,
            'best_error': metric([row['best_error'] for row in rows]),
            'elapsed_seconds': metric([row['elapsed_seconds'] for row in rows]),
            'solution_primitives': metric([row['primitives'] for row in rows if row['exact']]),
            'solution_routing_bits': metric([row['routing_bits'] for row in rows if row['exact']]),
            'solution_depth': metric([row['depth'] for row in rows if row['exact']]),
            'uses_transfer': sum(row['exact'] and row['uses_transfer'] for row in rows),
        }
        if condition != 'no_transfer':
            summary['module_trace'][f'{task}:{condition}'] = {
                'round1_credit': metric([row['trace'][0]['module_credit'] for row in rows if row['trace']]),
                'round1_partner_count': metric([row['trace'][0]['module_partner_count'] for row in rows if row['trace']]),
                'round1_survives': sum(bool(row['trace']) and row['trace'][0]['module_survives'] for row in rows),
                'round1_direct_child_selected': metric([len(row['trace'][0]['selected_direct_child_signatures']) for row in rows if row['trace']]),
                'round1_selected_expression_contains_module': metric([row['trace'][0]['selected_expression_contains_module'] for row in rows if row['trace']]),
            }
    comparisons = (('rotate1', 'no_transfer'), ('admitted', 'no_transfer'), ('admitted', 'rotate1'))
    for left, right in comparisons:
        left_exact = [by[seed, task, left]['exact'] for seed in seeds]
        right_exact = [by[seed, task, right]['exact'] for seed in seeds]
        key = f'{task}:{left}-minus-{right}'
        summary['paired'][key] = paired(np.asarray(left_exact, int) - np.asarray(right_exact, int), rng)
        p, left_only, right_only = mcnemar(left_exact, right_exact)
        summary['mcnemar'][task].append({'left': left, 'right': right, 'left_only': left_only, 'right_only': right_only, 'p': p})
    adjusted = holm([item['p'] for item in summary['mcnemar'][task]])
    for item, value in zip(summary['mcnemar'][task], adjusted):
        item['holm_p'] = value
    for condition in ('admitted', 'rotate1'):
        for round_index in range(1, 7):
            overlaps = []
            for seed in seeds:
                left = by[seed, task, condition]['trace']
                right = by[seed, task, 'no_transfer']['trace']
                if len(left) < round_index or len(right) < round_index:
                    continue
                a = set(left[round_index-1]['selected_signatures'])
                b = set(right[round_index-1]['selected_signatures'])
                overlaps.append(len(a & b) / len(a | b))
            summary['beam_jaccard'][f'{task}:{condition}:round{round_index}'] = metric(overlaps)

for task in tasks:
    witnesses = []
    for seed in seeds:
        rotated = by[seed, task, 'rotate1']
        baseline = by[seed, task, 'no_transfer']
        if not rotated['exact'] or baseline['exact']:
            continue
        final = signatures(rotated['expression'])
        first_rotated = set(rotated['trace'][0]['selected_signatures']) if rotated['trace'] else set()
        first_baseline = set(baseline['trace'][0]['selected_signatures']) if baseline['trace'] else set()
        exclusive = {int(signature) for signature in first_rotated - first_baseline}
        direct = {int(signature) for signature in rotated['trace'][0]['selected_direct_child_signatures']} if rotated['trace'] else set()
        ancestors = sorted(final & exclusive)
        direct_ancestors = sorted(final & direct & exclusive)
        witnesses.append({
            'seed': seed,
            'final_uses_rotated_function': int(rotate1['signature']) in final,
            'round1_exclusive_ancestors': [str(signature) for signature in ancestors],
            'round1_direct_child_ancestors': [str(signature) for signature in direct_ancestors],
            'round1_beam_jaccard': None if not first_rotated or not first_baseline else len(first_rotated & first_baseline) / len(first_rotated | first_baseline),
        })
    trajectory_count = sum(not item['final_uses_rotated_function'] and bool(item['round1_exclusive_ancestors']) for item in witnesses)
    summary['trajectory'][task] = {
        'rotate1_only_exact_count': len(witnesses),
        'no_final_function_but_round1_exclusive_ancestor_count': trajectory_count,
        'direct_child_ancestor_count': sum(not item['final_uses_rotated_function'] and bool(item['round1_direct_child_ancestors']) for item in witnesses),
        'witnesses': witnesses,
    }
summary['trajectory_criterion_met'] = summary['trajectory']['eval_dual_mux_xor']['no_final_function_but_round1_exclusive_ancestor_count'] >= 3
(OUT / 'audit_summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False))

lines = [
    '# E029：Libraryが変えるBeam探索軌跡',
    '',
    '実行日：2026-09-18。E026の採用FunctionとE028の入力+1置換を凍結し、新規16 seed × 2 task × 3条件の96探索を実施した。E026のbeam selectionを戻り値不変のwrapperで観測し、候補signature、Function credit、partner数、直接子候補を保存した。',
    '',
    '## Exact到達とタスク別統計',
    '',
    '| task | condition | exact /16 | 成功率平均 | 不偏分散 | best error平均 | 時間平均秒 | 最終式のFunction使用 |',
    '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |',
]
for task in tasks:
    for condition in conditions:
        item = summary['by_task'][task][condition]
        lines.append(f"| {task} | {condition} | {int(item['exact']['mean'] * 16)}/16 | {item['exact']['mean']:.4f} | {item['exact']['unbiased_variance']:.4f} | {item['best_error']['mean']:.4f} | {item['elapsed_seconds']['mean']:.3f} | {item['uses_transfer']} |")
lines += ['', '成功解だけのtree cost平均（primitive / routing bits / depth）：', '']
for task in tasks:
    for condition in conditions:
        item = summary['by_task'][task][condition]
        p = item['solution_primitives']['mean']
        r = item['solution_routing_bits']['mean']
        d = item['solution_depth']['mean']
        cost = 'NA' if p is None else f'{p:.2f} / {r:.2f} / {d:.2f}'
        lines.append(f'- {task} / {condition}: {cost}。')
lines += ['', '| paired exact/seed | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |', '| --- | ---: | ---: | --- | ---: | ---: |']
for task in tasks:
    for left, right in (('rotate1', 'no_transfer'), ('admitted', 'no_transfer'), ('admitted', 'rotate1')):
        item = summary['paired'][f'{task}:{left}-minus-{right}']
        dz = 'NA' if item['cohen_dz'] is None else f"{item['cohen_dz']:.3f}"
        lines.append(f"| {task}: {left}−{right} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {dz} | {item['exact_signflip_p']:.4f} |")

primary = summary['trajectory']['eval_dual_mux_xor']
lines += ['', '## 事前指定した探索軌跡の指標', '']
if summary['trajectory_criterion_met']:
    lines.append('事前指定した予備的な探索軌跡witness基準（3件以上）を満たした。')
else:
    lines.append('事前指定した予備的な探索軌跡witness基準（3件以上）は満たさなかった。')
lines.append(f"rotate1-onlyのdual-mux exactは{primary['rotate1_only_exact_count']}件。そのうち最終式にrotate1 Functionがなく、round 1でrotate1条件のbeamにのみ残ったsignatureを最終式の祖先に持つものは{primary['no_final_function_but_round1_exclusive_ancestor_count']}件。直接ペア生成したsignatureが祖先だったのは{primary['direct_child_ancestor_count']}件。")
lines.append('直接子祖先とは、Functionとのペア出力として生成可能で、かつno-transferのround-1 beamにはなかったsignatureを指す。同じsignatureは別経路からも生成できるため、これはtrajectoryの観測証人であり厳密な媒介効果の同定ではない。')
for item in primary['witnesses']:
    lines.append(f"- seed {item['seed']}: 最終Function使用={item['final_uses_rotated_function']}、round1固有祖先={len(item['round1_exclusive_ancestors'])}、直接子祖先={len(item['round1_direct_child_ancestors'])}、beam Jaccard={item['round1_beam_jaccard']:.4f}。")
lines += ['', 'roundごとのno-transferとのbeam Jaccard平均（比較可能なseedのみ）：', '']
for task in tasks:
    for condition in ('admitted', 'rotate1'):
        parts = []
        for round_index in range(1, 7):
            item = summary['beam_jaccard'][f'{task}:{condition}:round{round_index}']
            parts.append(f"r{round_index}={item['mean']:.3f} (n={item['n']})" if item['mean'] is not None else f'r{round_index}=NA')
        lines.append(f"- {task} / {condition}: " + '、'.join(parts) + '。')
lines += ['', '## creditと多重比較', '']
for task in tasks:
    for condition in ('admitted', 'rotate1'):
        item = summary['module_trace'][f'{task}:{condition}']
        lines.append(f"- {task} / {condition}: round1 credit平均 {item['round1_credit']['mean']:.2f}、partner平均 {item['round1_partner_count']['mean']:.2f}、Function生存 {item['round1_survives']}/16、直接子beam保持平均 {item['round1_direct_child_selected']['mean']:.2f}。")
for task in tasks:
    for item in summary['mcnemar'][task]:
        lines.append(f"- {task}: {item['left']} vs {item['right']}、left-only {item['left_only']}、right-only {item['right_only']}、exact McNemar p={item['p']:.4f}、Holm p={item['holm_p']:.4f}。")
lines += [
    '',
    f"全{verified} exact式を64入力で再評価し、96 record、凍結Function、費用一致、source hash、wrapperの事前smoke一致を監査した。これは固定予算のBoolean探索であり、学習抽象化・実gate数・実測速度・Routerの効果は示さない。",
    '',
    '## Roadmap',
    '',
    '- [Done] E026の選択関数を変更せずbeam/credit/親候補のsignature単位トレースを実装した。',
    '- [Done] 16新規seed・96探索とpaired統計、Holm補正、全exact式、source hashを監査した。',
    '- [Next] 祖先signatureの再生成経路を追跡し、Library由来と独立生成を識別するprovenance付き探索を検討する。',
    '- [Later] 複数の経路選択task familyと床効果のない数値taskを比較し、十分な証拠が得られてからRouter統合へ進む。',
    '',
    'English: On 16 fresh seeds, dual-mux XOR solved 2/16 without transfer, 4/16 with the admitted Function, and 3/16 with its input rotation; paired exact differences were not significant. All three rotation-only solutions omitted the rotated Function yet contained first-round beam signatures absent without transfer and compatible with direct offspring. This supports a preliminary trajectory witness, not causal provenance or a performance claim.',
    '',
    '简体中文：16个新seed的dual-mux XOR结果为无迁移2/16、原函数4/16、输入旋转3/16；配对成功率差异不显著。3个仅旋转条件成功的电路都未使用旋转函数，却包含无迁移条件首轮beam所没有、且可由该函数直接生成的中间签名。这是初步轨迹证据，并非因果来源或性能优势的证明。',
    '',
    '[事前計画](../results/E029-beam-trajectory/PROTOCOL.md) / [生データ](../results/E029-beam-trajectory/run/results.json) / [凍結Library](../results/E029-beam-trajectory/run/frozen_library.json) / [監査要約](../results/E029-beam-trajectory/run/audit_summary.json)',
]
report = '\n'.join(lines) + '\n'
(ROOT / 'docs/STAR-Bit-E029-beam-trajectory.md').write_text(report)
(HERE / 'REPORT.md').write_text(report.replace('(../results/E029-beam-trajectory/', '('))
print(json.dumps({'exact_by_task': {task: {condition: summary['by_task'][task][condition]['exact']['mean'] for condition in conditions} for task in tasks}, 'primary_trajectory': primary, 'criterion': summary['trajectory_criterion_met'], 'solutions_verified': verified}, indent=2))
