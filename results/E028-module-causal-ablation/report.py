"""E028 source and truth-table audit plus preregistered statistics."""
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
    total = 2 ** len(differences)
    extreme = 0
    for mask in range(total):
        mean = np.mean([value * (1 if mask & (1 << index) else -1) for index, value in enumerate(differences)])
        extreme += abs(mean) >= observed - 1e-12
    return extreme / total


def paired(differences, rng):
    values = np.asarray(differences, float)
    bootstrap = values[rng.integers(0, len(values), (20000, len(values)))].mean(1)
    std = values.std(ddof=1)
    return {
        'mean': float(values.mean()),
        'variance': float(values.var(ddof=1)),
        'ci95': np.quantile(bootstrap, [.025, .975]).tolist(),
        'cohen_dz': None if std == 0 else float(values.mean() / std),
        'exact_signflip_p': signflip(values),
        'differences': values.tolist(),
    }


def mcnemar(a, b):
    left = sum(x and not y for x, y in zip(a, b))
    right = sum(y and not x for x, y in zip(a, b))
    n = left + right
    p = 1.0 if not n else min(1.0, 2 * sum(math.comb(n, k) for k in range(min(left, right) + 1)) / 2 ** n)
    return p, left, right


def holm(pvalues):
    order = sorted(range(len(pvalues)), key=lambda index: pvalues[index])
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


result = json.loads((OUT / 'results.json').read_text())
assert len(result['records']) == 160
assert result['settings']['seeds'] == list(range(1390, 1406))
for name, expected in result['sources'].items():
    assert sha(ROOT / name) == expected, name

library = json.loads((OUT / 'frozen_library.json').read_text())
frozen = library['admitted']
admission = json.loads((ROOT / 'results/E026-counterfactual-admission/run/admission.json').read_text())
assert frozen['signature'] == admission['selected_signatures'][0]
inputs, _ = base.inputs_and_targets()
target = targets()
assert evaluate(frozen['expression'], inputs) == int(frozen['signature'])
for rotation in library['rotations'].values():
    assert evaluate(rotation['expression'], inputs) == int(rotation['signature'])
    assert tuple(rotation['cost']) == (frozen['primitives'], frozen['routing_bits'], frozen['depth'])

verified = 0
for row in result['records']:
    if row['expression'] is not None:
        assert row['exact'] and evaluate(row['expression'], inputs) == target[row['task']]
        verified += 1
    if row['condition'] == 'inert_signature':
        assert not row['uses_transfer']
        if row['expression'] is not None:
            assert int(frozen['signature']) not in signatures(row['expression'])

by = {(row['seed'], row['task'], row['condition']): row for row in result['records']}
seeds = result['settings']['seeds']
conditions = result['settings']['conditions']
rng = np.random.default_rng(2028)
paired_stats = {}
task_tests = {}
admitted_only = {}
for task in result['settings']['tasks']:
    task_tests[task] = []
    admitted_only[task] = {}
    for comparator in ('inert_signature', 'rotate1', 'rotate2', 'no_transfer'):
        left = [by[seed, task, 'admitted']['exact'] for seed in seeds]
        right = [by[seed, task, comparator]['exact'] for seed in seeds]
        differences = np.asarray(left, int) - np.asarray(right, int)
        paired_stats[f'{task}:admitted-minus-{comparator}'] = paired(differences, rng)
        p, left_only, right_only = mcnemar(left, right)
        if comparator != 'no_transfer':
            task_tests[task].append({'comparator': comparator, 'admitted_only': left_only, 'comparator_only': right_only, 'mcnemar_p': p})
        admitted_only[task][comparator] = [
            {'seed': seed, 'uses_transfer': by[seed, task, 'admitted']['uses_transfer'], 'used_signatures': by[seed, task, 'admitted']['used_signatures']}
            for seed in seeds if by[seed, task, 'admitted']['exact'] and not by[seed, task, comparator]['exact']
        ]
    adjusted = holm([row['mcnemar_p'] for row in task_tests[task]])
    for row, value in zip(task_tests[task], adjusted):
        row['holm_p'] = value

primary = paired_stats['eval_dual_mux_xor:admitted-minus-inert_signature']
learned_only = admitted_only['eval_dual_mux_xor']['inert_signature']
criterion = (
    primary['mean'] >= .25
    and primary['ci95'][0] > 0
    and len(learned_only) >= 4
    and sum(item['uses_transfer'] for item in learned_only) >= 4
)

summary = {
    'aggregate': result['aggregate'],
    'paired': paired_stats,
    'task_tests': task_tests,
    'admitted_only': admitted_only,
    'frozen_signature': frozen['signature'],
    'candidate_error': {task: {
        'admitted': base.error(int(frozen['signature']), target[task]),
        **{name: base.error(int(item['signature']), target[task]) for name, item in library['rotations'].items()},
    } for task in target},
    'records_verified': len(result['records']),
    'solutions_verified': verified,
    'direct_composition_criterion_met': criterion,
    'analysis_source_hashes': {
        'report.py': sha(HERE / 'report.py'),
        'normalize.py': sha(HERE / 'normalize.py'),
    },
}
summary['by_task'] = {}
for task in result['settings']['tasks']:
    summary['by_task'][task] = {}
    for condition in conditions:
        rows = [by[seed, task, condition] for seed in seeds]
        exact = np.asarray([row['exact'] for row in rows], float)
        summary['by_task'][task][condition] = {
            'exact_mean': float(exact.mean()),
            'exact_unbiased_variance': float(exact.var(ddof=1)),
            'best_error_mean': float(np.mean([row['best_error'] for row in rows])),
            'solution_primitives_mean': None if not any(row['exact'] for row in rows) else float(np.mean([row['primitives'] for row in rows if row['exact']])),
            'solution_routing_bits_mean': None if not any(row['exact'] for row in rows) else float(np.mean([row['routing_bits'] for row in rows if row['exact']])),
            'solution_depth_mean': None if not any(row['exact'] for row in rows) else float(np.mean([row['depth'] for row in rows if row['exact']])),
        }
summary['inert_vs_no_transfer_matching_cases'] = {
    field: sum(by[seed, task, 'inert_signature'][field] == by[seed, task, 'no_transfer'][field]
               for task in result['settings']['tasks'] for seed in seeds)
    for field in ('exact', 'round', 'best_error_history', 'expression', 'generated_unique_signatures')
}
(OUT / 'audit_summary.json').write_text(json.dumps(summary, indent=2))

lines = [
    '# E028：転移Functionの直接寄与と入力意味のAblation',
    '',
    '実行日：2026-09-17。E027で採用した2-gate Functionを凍結し、16新規seed × 経路選択／数値各1 task × 5条件の160探索を事前登録どおり実施した。inert条件は同じFunctionをbeamに置く一方、そのtruth-table signatureを親とするcompositionだけを禁止する。rotate1/2は入力indexを巡回置換し、gate種・式木・primitive/routing/depth費用を維持する。',
    '',
    '## Exact到達',
    '',
    '| condition | dual-mux XOR /16 | threshold2 /16 | 全32例の平均 | 不偏分散 | transfer使用 | best error平均 | 時間平均秒 |',
    '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
]
for condition in conditions:
    item = result['aggregate'][condition]
    counts = item['exact_by_task']
    lines.append(f"| {condition} | {counts['eval_dual_mux_xor']}/16 | {counts['eval_threshold2']}/16 | {item['exact']['mean']:.4f} | {item['exact']['variance']:.4f} | {item['uses_transfer']} | {item['best_error']['mean']:.4f} | {item['elapsed_seconds']['mean']:.3f} |")

lines += ['', '各taskのexact成功率、不偏分散、成功解だけのtree cost（primitive / routing bits / depth）を分けて示す。', '',
          '| task | condition | 成功率平均 | 不偏分散 | 解cost平均 |',
          '| --- | --- | ---: | ---: | --- |']
for task in result['settings']['tasks']:
    for condition in conditions:
        item = summary['by_task'][task][condition]
        cost = 'NA' if item['solution_primitives_mean'] is None else f"{item['solution_primitives_mean']:.2f} / {item['solution_routing_bits_mean']:.2f} / {item['solution_depth_mean']:.2f}"
        lines.append(f"| {task} | {condition} | {item['exact_mean']:.4f} | {item['exact_unbiased_variance']:.4f} | {cost} |")

lines += [
    '',
    '| task / admittedとの差 | 平均 | 差の不偏分散 | bootstrap 95% CI | Cohen dz | exact sign-flip p |',
    '| --- | ---: | ---: | --- | ---: | ---: |',
]
for task in result['settings']['tasks']:
    for comparator in ('inert_signature', 'rotate1', 'rotate2', 'no_transfer'):
        item = paired_stats[f'{task}:admitted-minus-{comparator}']
        dz = 'NA' if item['cohen_dz'] is None else f"{item['cohen_dz']:.3f}"
        lines.append(f"| {task} − {comparator} | {item['mean']:+.4f} | {item['variance']:.4f} | [{item['ci95'][0]:.4f}, {item['ci95'][1]:.4f}] | {dz} | {item['exact_signflip_p']:.4f} |")

lines += ['', '## 判定', '']
if criterion:
    lines.append('経路選択taskのadmitted−inertは事前登録した直接composition基準を満たした。beam内の占有やランキング変化だけでは今回の差を説明できず、このtruth-table Functionを親として使えることが探索到達に寄与した。')
else:
    lines.append('経路選択taskのadmitted−inertは事前登録した直接composition基準を満たさなかった。beam内の占有／選択軌跡変化とFunctionの直接再利用をまだ分離できない。')
lines.append(f"primary差は{primary['mean']:+.4f} exact/seed、95% CI [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}]、exact p={primary['exact_signflip_p']:.4f}。admitted-onlyは{len(learned_only)} seed、そのうち凍結signatureを最終式に含むものは{sum(item['uses_transfer'] for item in learned_only)}件。")
lines.append('inert条件はLibraryの候補だけでなく、探索中に同じsignatureを再生成した場合もその親利用を禁止する。最終式のsignature使用は機能的な再利用を示すが、その節点がLibraryから来たのか独立合成されたのかは識別しない。')
lines.append(f"inertとno-transferは32/32 caseでexact成否、到達round、best-error履歴、最終式が一致した。生成signature数は初期候補1個の差があるため一致しない。今回のinert候補は探索結果を変えなかったが、admittedとの対応差は統計的に確証されていない。")
lines.append('rotate1はdual-mux XORでadmittedと同じ4/16に到達したが、4解とも置換Functionを最終式に含まなかった。固定Functionが直接部品になる経路と、Library追加によってbeam／creditの軌跡が変わる経路を分ける必要がある。')
lines += ['', '構造同費用の入力置換対照と比較すると、関数の入力配置・truth-table意味の違いを調べられる。ただし2置換だけでBoolean機能族全体の一般性は結論できない。各Functionの評価taskに対する64行Hamming errorは次のとおり。', '']
for task in result['settings']['tasks']:
    lines.append(f"- {task}: admitted {summary['candidate_error'][task]['admitted']}、rotate1 {summary['candidate_error'][task]['rotate1']}、rotate2 {summary['candidate_error'][task]['rotate2']}。")
lines += ['', 'task別のexact McNemar検定はinert／rotate1／rotate2の3比較でHolm補正した。', '']
for task in result['settings']['tasks']:
    for item in task_tests[task]:
        lines.append(f"- {task} vs {item['comparator']}: admitted-only {item['admitted_only']}、対照only {item['comparator_only']}、p={item['mcnemar_p']:.4f}、Holm p={item['holm_p']:.4f}。")
lines += [
    '',
    f"全{verified} exact式を64入力で再評価し、160 record、source hash、費用が一致する入力置換式、inert解に凍結signatureが含まれないことを監査した。Function Libraryを入れた探索の到達性であり、記述長・実gate数・実行速度・Router学習の証拠ではない。",
    '',
    'rotate2の成功解は1件だけで、不偏分散は定義できない。実行時の非標準JSON `NaN` を元ファイル `results.original.json` に保存し、正規化版 `results.json` では該当箇所だけ `null` にした。[正規化記録](../results/E028-module-causal-ablation/run/normalization.json)。個別探索recordは変更していない。',
    '',
    '## Roadmap',
    '',
    '- [Done] 凍結Functionの直接composition禁止と、同じ2-gate構造の2つの入力巡回置換を実装した。',
    '- [Done] 新規16 seed・160探索、paired統計、Holm補正、全exact式とsource hash監査を完了した。',
    '- [Next] beam候補の生存・credit・親利用をsignature単位で記録し、rotate1の「最終式で未使用なのに成功」を追跡する。',
    '- [Next] 入力配置以外の意味対照を事前固定し、Functionの可搬性を複数の経路選択task familyで確認する。',
    '- [Later] 数値taskの床効果を校正し、State付きFunctionとRouterへ統合する。',
    '',
    'English: On dual-mux XOR, admitted Function search solved 4/16 versus inert composition 2/16, but the paired effect failed the preregistered criterion (CI [-0.125, 0.375], exact p=0.625). An input-rotated Function also solved 4/16 despite appearing in none of its final circuits. Thus E027 remains a narrow transfer signal; direct reusable-Module causality is not established.',
    '',
    '简体中文：dual-mux XOR中原函数成功4/16，禁止直接组合后为2/16，但配对差未达到预注册标准（置信区间[-0.125, 0.375]，精确p=0.625）。输入旋转函数也成功4/16，却未出现在任何最终电路中。因此E027仍是范围有限的迁移信号，尚未证实可复用模块的直接因果作用。',
    '',
    '[事前計画](../results/E028-module-causal-ablation/PROTOCOL.md) / [生データ](../results/E028-module-causal-ablation/run/results.json) / [凍結Library](../results/E028-module-causal-ablation/run/frozen_library.json) / [監査要約](../results/E028-module-causal-ablation/run/audit_summary.json)',
]
report = '\n'.join(lines) + '\n'
(ROOT / 'docs/STAR-Bit-E028-module-causal-ablation.md').write_text(report)
(HERE / 'REPORT.md').write_text(report.replace('(../results/E028-module-causal-ablation/', '('))
print(json.dumps({
    'exact_by_condition': {condition: result['aggregate'][condition]['exact_by_task'] for condition in conditions},
    'primary': primary,
    'criterion': criterion,
    'verified': verified,
    'task_tests': task_tests,
}, indent=2))
