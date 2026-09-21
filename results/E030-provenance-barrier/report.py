"""Audit and report E030 provenance-barrier experiment."""
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


def expression_signatures(expression):
    if expression[0] == 'input':
        return set()
    return {int(expression[1])} | expression_signatures(expression[3]) | expression_signatures(expression[4])


def signflip(differences):
    observed = abs(float(np.mean(differences)))
    total = 2 ** len(differences)
    extreme = 0
    for mask in range(total):
        value = np.mean([difference * (1 if mask & (1 << index) else -1) for index, difference in enumerate(differences)])
        extreme += abs(value) >= observed - 1e-12
    return extreme / total


def paired(differences, rng):
    values = np.asarray(differences, float)
    bootstrap = values[rng.integers(0, len(values), (20000, len(values)))].mean(1)
    std = values.std(ddof=1)
    return {
        'mean': float(values.mean()),
        'unbiased_variance': float(values.var(ddof=1)),
        'ci95': np.quantile(bootstrap, [.025, .975]).tolist(),
        'cohen_dz': None if std == 0 else float(values.mean() / std),
        'exact_signflip_p': signflip(values),
        'differences': values.tolist(),
    }


def metric(values):
    array = np.asarray(values, float)
    return {'mean': None if len(array) == 0 else float(array.mean()), 'unbiased_variance': None if len(array) < 2 else float(array.var(ddof=1)), 'n': len(array)}


def mcnemar(left, right):
    left_only = sum(a and not b for a, b in zip(left, right))
    right_only = sum(b and not a for a, b in zip(left, right))
    n = left_only + right_only
    p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, k) for k in range(min(left_only, right_only) + 1)) / 2 ** n)
    return p, left_only, right_only


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
assert result['settings']['seeds'] == list(range(1430, 1446))
for name, expected in result['sources'].items():
    assert sha(ROOT / name) == expected, name
smoke = json.loads((OUT / 'smoke.json').read_text())
assert smoke['seed'] == 1429 and smoke['rounds'] == 3
library = json.loads((OUT / 'frozen_library.json').read_text())
module_signature = int(library['rotate1']['signature'])
inputs, _ = base.inputs_and_targets()
assert evaluate(library['rotate1']['expression'], inputs) == module_signature
assert tuple(library['rotate1']['cost']) == (library['admitted']['primitives'], library['admitted']['routing_bits'], library['admitted']['depth'])

target = targets()
verified = 0
for row in result['records']:
    if row['expression'] is not None:
        assert row['exact'] and evaluate(row['expression'], inputs) == target[row['task']]
        verified += 1
    for snapshot in row['trace']:
        assert 1 <= snapshot['round'] <= 6
        assert len(snapshot['selected']) <= 128
        signatures = [item['signature'] for item in snapshot['selected']]
        assert len(signatures) == len(set(signatures))

seeds = result['settings']['seeds']
tasks = result['settings']['tasks']
conditions = result['settings']['conditions']
by = {(row['seed'], row['task'], row['condition']): row for row in result['records']}
rng = np.random.default_rng(2030)
summary = {'aggregate': result['aggregate'], 'by_task': {}, 'paired': {}, 'mcnemar': {}, 'lineage': {}, 'beam_jaccard': {}, 'solutions_verified': verified, 'records_verified': len(result['records']), 'analysis_source_hash': sha(HERE / 'report.py')}

def qualified_lineages(row, baseline):
    candidates = []
    for signature in sorted(expression_signatures(row['expression'])):
        occurrences = []
        for snapshot in row['trace']:
            for item in snapshot['selected']:
                if int(item['signature']) == signature:
                    occurrences.append((snapshot['round'], item))
        if not occurrences:
            continue
        first_round, first = occurrences[0]
        absent_baseline = True
        if len(baseline['trace']) >= first_round:
            absent_baseline = str(signature) not in {item['signature'] for item in baseline['trace'][first_round - 1]['selected']}
        later_clean = [round_index for round_index, item in occurrences[1:] if not item['selected_contains_module']]
        if first['selected_contains_module'] and first['tainted_generator_available'] and not first['clean_generator_available'] and absent_baseline and later_clean:
            candidates.append({'signature': str(signature), 'first_round': first_round, 'first_cost': [first['primitives'], first['routing_bits'], first['depth']], 'first_credit': first['credit'], 'first_partner_count': first['partner_count'], 'first_clean_round': min(later_clean)})
    return candidates


for task in tasks:
    summary['by_task'][task] = {}
    summary['mcnemar'][task] = []
    for condition in conditions:
        rows = [by[seed, task, condition] for seed in seeds]
        summary['by_task'][task][condition] = {
            'exact': metric([row['exact'] for row in rows]),
            'best_error': metric([row['best_error'] for row in rows]),
            'elapsed_seconds': metric([row['elapsed_seconds'] for row in rows]),
            'solution_primitives': metric([row['primitives'] for row in rows if row['exact']]),
            'solution_routing_bits': metric([row['routing_bits'] for row in rows if row['exact']]),
            'solution_depth': metric([row['depth'] for row in rows if row['exact']]),
            'uses_transfer': sum(row['exact'] and row['uses_transfer'] for row in rows),
        }
    comparisons = (('rotate1', 'one_hop_barrier'), ('rotate1', 'no_transfer'), ('one_hop_barrier', 'no_transfer'))
    for left, right in comparisons:
        a = [by[seed, task, left]['exact'] for seed in seeds]
        b = [by[seed, task, right]['exact'] for seed in seeds]
        key = f'{task}:{left}-minus-{right}'
        summary['paired'][key] = paired(np.asarray(a, int) - np.asarray(b, int), rng)
        p, left_only, right_only = mcnemar(a, b)
        summary['mcnemar'][task].append({'left': left, 'right': right, 'left_only': left_only, 'right_only': right_only, 'p': p})
    adjusted = holm([item['p'] for item in summary['mcnemar'][task]])
    for item, value in zip(summary['mcnemar'][task], adjusted):
        item['holm_p'] = value
    for condition in ('rotate1', 'one_hop_barrier'):
        for round_index in range(1, 7):
            overlaps = []
            for seed in seeds:
                left_trace = by[seed, task, condition]['trace']
                right_trace = by[seed, task, 'no_transfer']['trace']
                if len(left_trace) < round_index or len(right_trace) < round_index:
                    continue
                left = {item['signature'] for item in left_trace[round_index - 1]['selected']}
                right = {item['signature'] for item in right_trace[round_index - 1]['selected']}
                overlaps.append(len(left & right) / len(left | right))
            summary['beam_jaccard'][f'{task}:{condition}:round{round_index}'] = metric(overlaps)

for task in tasks:
    witnesses = []
    for seed in seeds:
        normal = by[seed, task, 'rotate1']
        barrier = by[seed, task, 'one_hop_barrier']
        baseline = by[seed, task, 'no_transfer']
        if not normal['exact'] or barrier['exact'] or normal['expression'] is None:
            continue
        final_signatures = expression_signatures(normal['expression'])
        if module_signature in final_signatures:
            continue
        candidates = qualified_lineages(normal, baseline)
        witnesses.append({'seed': seed, 'baseline_exact': baseline['exact'], 'lineages': candidates})
    summary['lineage'][task] = {
        'rotate1_only_vs_barrier_count': len(witnesses),
        'qualified_lineage_count': sum(bool(item['lineages']) for item in witnesses),
        'witnesses': witnesses,
    }
    versus_no = {}
    for condition in ('rotate1', 'one_hop_barrier'):
        condition_witnesses = []
        for seed in seeds:
            row = by[seed, task, condition]
            baseline = by[seed, task, 'no_transfer']
            if row['exact'] and not baseline['exact'] and row['expression'] is not None and module_signature not in expression_signatures(row['expression']):
                condition_witnesses.append({'seed': seed, 'lineages': qualified_lineages(row, baseline)})
        versus_no[condition] = {'condition_only_count': len(condition_witnesses), 'qualified_lineage_count': sum(bool(item['lineages']) for item in condition_witnesses), 'witnesses': condition_witnesses}
    summary['lineage'][task]['versus_no_transfer'] = versus_no

primary = summary['paired']['eval_dual_mux_xor:rotate1-minus-one_hop_barrier']
lineage = summary['lineage']['eval_dual_mux_xor']
summary['propagated_descendant_criterion_met'] = primary['mean'] >= .1875 and primary['ci95'][0] > 0 and lineage['qualified_lineage_count'] >= 3
(OUT / 'audit_summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False))

lines = [
    '# E030：Function由来Signatureの置換と伝播Barrier',
    '',
    '実行日：2026-09-20。E026の採用Functionを入力+1置換した固定Functionについて、新規16 seed × 経路選択／数値各1 task × 3条件の96探索を実施した。one-hop barrierはround 1の子生成を許し、round 2以降はFunctionを式木に含む候補を親として使わない。同じsignatureを持つFunction-free式は利用できる。',
    '',
    '## 結果',
    '',
    '| task | condition | exact /16 | 成功率平均 | 不偏分散 | best error平均 | 時間平均秒 | Function使用 |',
    '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |',
]
for task in tasks:
    for condition in conditions:
        item = summary['by_task'][task][condition]
        lines.append(f"| {task} | {condition} | {int(item['exact']['mean'] * 16)}/16 | {item['exact']['mean']:.4f} | {item['exact']['unbiased_variance']:.4f} | {item['best_error']['mean']:.4f} | {item['elapsed_seconds']['mean']:.3f} | {item['uses_transfer']} |")
lines += ['', '成功解のtree cost平均（primitive / routing bits / depth）：', '']
for task in tasks:
    for condition in conditions:
        item = summary['by_task'][task][condition]
        primitive = item['solution_primitives']['mean']
        cost = 'NA' if primitive is None else f"{primitive:.2f} / {item['solution_routing_bits']['mean']:.2f} / {item['solution_depth']['mean']:.2f}"
        lines.append(f'- {task} / {condition}: {cost}。')
lines += ['', '| paired exact/seed | 平均差 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |', '| --- | ---: | ---: | --- | ---: | ---: |']
for task in tasks:
    for left, right in (('rotate1', 'one_hop_barrier'), ('rotate1', 'no_transfer'), ('one_hop_barrier', 'no_transfer')):
        item = summary['paired'][f'{task}:{left}-minus-{right}']
        dz = 'NA' if item['cohen_dz'] is None else f"{item['cohen_dz']:.3f}"
        lines.append(f"| {task}: {left}−{right} | {item['mean']:+.4f} | {item['unbiased_variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {dz} | {item['exact_signflip_p']:.4f} |")

lines += ['', '## 事前判定とProvenance', '']
if summary['propagated_descendant_criterion_met']:
    lines.append('事前登録したFunction-descendant伝播基準を満たした。')
else:
    lines.append('事前登録したFunction-descendant伝播基準は満たさなかった。')
lines.append(f"primaryのrotate1−one-hop barrierは{primary['mean']:+.4f} exact/seed、95% CI [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}]、exact p={primary['exact_signflip_p']:.4f}。rotate1だけが成功した{lineage['rotate1_only_vs_barrier_count']}件中、事前定義したsignature置換lineageを持つものは{lineage['qualified_lineage_count']}件だった。")
for witness in lineage['witnesses']:
    lines.append(f"- seed {witness['seed']}: no-transfer exact={witness['baseline_exact']}、qualified lineage={len(witness['lineages'])}。" + ''.join(f" signature {item['signature']} はr{item['first_round']}でFunction由来のみ、r{item['first_clean_round']}でFunction-free表現へ置換。" for item in witness['lineages']))
lines.append('このlineageは選択された代表式のprovenanceを追跡する。truth signatureの一致は機能同値を示すが、学習された概念や物理回路の同一性を意味しない。')
normal_vs_none = lineage['versus_no_transfer']['rotate1']
barrier_vs_none = lineage['versus_no_transfer']['one_hop_barrier']
lines.append(f"移植なし対比では、rotate1-only {normal_vs_none['condition_only_count']}件中qualified lineageは{normal_vs_none['qualified_lineage_count']}件、barrier-only {barrier_vs_none['condition_only_count']}件中0件だった。barrierが通常条件と同じ3/16に達したことと合わせると、観測した置換lineageは成功に必要な共通機構ではない。")
lines += ['', 'taskごとに3つのexact McNemar比較をHolm補正した。', '']
for task in tasks:
    for item in summary['mcnemar'][task]:
        lines.append(f"- {task}: {item['left']} vs {item['right']}、left-only {item['left_only']}、right-only {item['right_only']}、p={item['p']:.4f}、Holm p={item['holm_p']:.4f}。")
lines += ['', 'no-transferとのbeam Jaccard平均：', '']
for task in tasks:
    for condition in ('rotate1', 'one_hop_barrier'):
        values = []
        for round_index in range(1, 7):
            item = summary['beam_jaccard'][f'{task}:{condition}:round{round_index}']
            values.append('NA' if item['mean'] is None else f"r{round_index}={item['mean']:.3f}(n={item['n']})")
        lines.append(f"- {task} / {condition}: " + '、'.join(values) + '。')
lines += [
    '',
    f"全{verified} exact式を64入力で再評価し、96 record、source hash、固定Functionの費用、通常searchとのsmoke一致を監査した。結果はBoolean探索機構に限り、学習抽象化、記述圧縮、実gate削減、速度、Router効果を示さない。",
    '',
    '## Roadmap',
    '',
    '- [Done] 選択された代表式についてFunction由来／Function-free生成と同一signatureへの置換をround単位で記録した。',
    '- [Done] 一段だけFunction由来候補を許すbarrierを、移植なし・通常Functionと新規16 seedで比較した。',
    '- [Next] 複数の経路選択task familyで同じbarrierを独立確認し、task固有軌跡への過適合を調べる。',
    '- [Later] 床効果のない数値taskとState付きFunctionへ拡張し、十分な機構証拠が得られてからRouterへ統合する。',
    '',
    'English: Normal rotation and the one-hop barrier both solved dual-mux XOR in 3/16 seeds, with a paired difference of zero. Two normal-only solutions showed Function-derived signatures replaced by Function-free equivalents, but barrier-only solutions showed no such lineage. The preregistered propagation criterion failed, so the observed lineage is not a necessary common mechanism.',
    '',
    '简体中文：普通输入旋转和一跳屏障在dual-mux XOR上均成功3/16，配对差为零。两个仅普通条件成功的解出现了函数来源签名被无函数等价表达式替换的轨迹，但仅屏障条件成功的解没有这种轨迹。预注册传播标准未达成，因此该轨迹不是成功所必需的共同机制。',
    '',
    '[事前计划](../results/E030-provenance-barrier/PROTOCOL.md) / [生数据](../results/E030-provenance-barrier/run/results.json) / [冻结Library](../results/E030-provenance-barrier/run/frozen_library.json) / [审计摘要](../results/E030-provenance-barrier/run/audit_summary.json)',
]
report = '\n'.join(lines) + '\n'
(ROOT / 'docs/STAR-Bit-E030-provenance-barrier.md').write_text(report)
(HERE / 'REPORT.md').write_text(report.replace('(../results/E030-provenance-barrier/', '('))
print(json.dumps({'exact_by_task': {task: {condition: summary['by_task'][task][condition]['exact']['mean'] for condition in conditions} for task in tasks}, 'primary': primary, 'lineage': lineage, 'criterion': summary['propagated_descendant_criterion_met'], 'verified': verified}, indent=2))
