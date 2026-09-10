"""CPU mechanism pilot; NOT a BitNet/Transformer or dynamic-topology benchmark."""
import argparse
import copy
import hashlib
import itertools
import json
import platform
import time
from pathlib import Path

import numpy as np
import torch
from scipy import stats
from torch import nn
from torch.nn import functional as F

CONDITIONS = ('fp_dense', 'ternary_dense', 'ternary_wide',
              'ternary_learned', 'ternary_fixed', 'fp_learned')
TASKS = ('precision', 'selection')


class Linear(nn.Linear):
    def __init__(self, n, m, ternary):
        super().__init__(n, m)
        self.ternary = ternary

    def forward(self, x):
        w = self.weight
        if self.ternary:
            scale = w.detach().abs().mean().clamp_min(1e-8)
            q = (w / scale).round().clamp(-1, 1) * scale
            w = w + (q - w).detach()  # identity straight-through gradient
        return F.linear(x, w, self.bias)


def expert(width, ternary):
    return nn.Sequential(Linear(12, width, ternary), nn.ReLU(), Linear(width, 1, ternary))


class Model(nn.Module):
    def __init__(self, condition):
        super().__init__()
        self.sparse = condition.endswith(('learned', 'fixed'))
        self.fixed = condition.endswith('fixed')
        ternary = condition.startswith('ternary')
        if self.sparse:
            self.experts = nn.ModuleList([expert(16, ternary) for _ in range(4)])
            self.router = nn.Linear(12, 4)
            if self.fixed:
                self.router.requires_grad_(False)
        else:
            # 2 active experts = 450 weights; router = 52. Dense 36 = 505.
            # 4 total experts + router = 952. Dense 68 = 953.
            self.dense = expert(68 if condition.endswith('wide') else 36, ternary)

    def forward(self, x):
        if not self.sparse:
            return self.dense(x).squeeze(-1), x.new_zeros(()), None
        p = self.router(x).softmax(-1)
        weights, ids = p.topk(2, dim=-1)
        weights = weights / weights.sum(-1, keepdim=True)
        out = x.new_zeros(len(x))
        # Execute only selected experts; fixed router consumes raw input, so
        # the upstream representation cannot learn to change the frozen route.
        for i, module in enumerate(self.experts):
            rows, slots = torch.where(ids == i)
            if len(rows):
                out = out.index_add(0, rows, module(x[rows]).squeeze(-1) * weights[rows, slots])
        f = F.one_hot(ids, 4).float().mean((0, 1))
        aux = 4 * (f.detach() * p.mean(0)).sum()
        return out, aux, (ids, p)


def data(seed, n, task, ood=False):
    g = torch.Generator().manual_seed(seed)
    z = torch.rand(n, 8, generator=g) * 2 - 1
    if ood:
        z = z.sign() * (1 + z.abs())  # magnitude [1,2], train [-1,1]
    category = torch.randint(4, (n,), generator=g)
    x = torch.cat((z, F.one_hot(category, 4).float()), dim=-1)
    if task == 'precision':
        coefficients = torch.tensor([.13, -.71, .37, 1.11, -.29, .53, -.89, .19])
        y = z @ coefficients
    else:
        y = z.gather(1, category[:, None]).squeeze(1)
    return x, y, category


@torch.no_grad()
def evaluate(model, dataset):
    x, y, category = dataset
    prediction, aux, routing = model(x)
    error = prediction - y
    result = {'nmse': (error.square().mean() / y.var(unbiased=False)).item(),
              'mae': error.abs().mean().item(),
              'within_001': (error.abs() <= .01).float().mean().item()}
    if routing is not None:
        ids, p = routing
        usage = F.one_hot(ids, 4).float().mean((0, 1))
        result.update(usage=usage.tolist(), load_balance=aux.item(),
                      usage_entropy=(-(usage * usage.clamp_min(1e-12).log()).sum()).item(),
                      token_entropy=(-(p * p.clamp_min(1e-12).log()).sum(-1).mean()).item(),
                      used_pairs=len(torch.unique(ids.sort(-1).values, dim=0)),
                      usage_by_category=[F.one_hot(ids[category == c], 4).float().mean((0, 1)).tolist() for c in range(4)])
    return result


def summary(values):
    a = np.asarray(values, dtype=float)
    mean, sd = float(a.mean()), float(a.std(ddof=1))
    delta = stats.t.ppf(.975, len(a) - 1) * sd / np.sqrt(len(a))
    return dict(n=len(a), mean=mean, variance=float(a.var(ddof=1)), sd=sd,
                ci95=[mean - delta, mean + delta])


def comparison(values):
    a = np.asarray(values)
    signs = np.array(list(itertools.product((-1, 1), repeat=len(a))))
    p = float((np.abs((signs * a).mean(1)) >= abs(a.mean()) - 1e-12).mean())
    return {**summary(a), 'p_signflip_two_sided': p}


def holm(items):
    ordered = sorted(items, key=lambda item: item['p_signflip_two_sided'])
    previous = 0.
    for i, item in enumerate(ordered):
        previous = max(previous, min(1., (len(ordered)-i) * item['p_signflip_two_sided']))
        item['p_holm'] = previous


def run(args):
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    records, swaps, models = [], [], {}
    start = time.time()
    for task in TASKS:
        # One fixed split per task, shared across model seeds: inference is
        # conditional on this dataset, not uncertainty over new datasets.
        train = data(10001, 4096, task)
        tests = {'id': data(20001, 2048, task), 'ood': data(30001, 2048, task, True)}
        for seed in range(args.seeds):
            g = torch.Generator().manual_seed(40000 + seed)
            batches = torch.randint(4096, (args.steps, 128), generator=g)
            for condition in CONDITIONS:
                torch.manual_seed(seed)
                model = Model(condition)
                opt = torch.optim.Adam(model.parameters(), lr=.003)
                tick = time.time()
                for batch in batches:
                    opt.zero_grad(set_to_none=True)
                    pred, aux, _ = model(train[0][batch])
                    loss = F.mse_loss(pred, train[1][batch])
                    if model.sparse and not model.fixed:
                        loss = loss + .01 * aux  # from first update
                    loss.backward()
                    opt.step()
                model.eval()
                count = sum(p.numel() for p in model.parameters())
                record = dict(task=task, seed=seed, condition=condition,
                              total_parameters=count, active_parameters=502 if model.sparse else count,
                              trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
                              parameter_bytes=sum(p.numel()*p.element_size() for p in model.parameters()),
                              train_seconds=time.time()-tick,
                              metrics={key: evaluate(model, d) for key, d in tests.items()})
                records.append(record)
                print(task, seed, condition, round(record['metrics']['id']['nmse'], 5), flush=True)
                if condition == 'ternary_learned':
                    models[task, seed] = copy.deepcopy(model)
                    torch.save(model.state_dict(), output / f'{task}_seed{seed}.pt')
        # First within-run exchange, then cyclic donor from another seed.
        for seed in range(args.seeds):
            base = models[task, seed]
            donor_seed = (seed + 1) % args.seeds
            for intervention in ('self', 'within_run', 'cross_seed', 'permutation_control'):
                model = copy.deepcopy(base)
                if intervention == 'within_run':
                    model.experts[0], model.experts[1] = model.experts[1], model.experts[0]
                elif intervention == 'cross_seed':
                    model.experts[0].load_state_dict(models[task, donor_seed].experts[0].state_dict())
                elif intervention == 'self':
                    model.experts[0].load_state_dict(base.experts[0].state_dict())
                else:
                    model.experts[0], model.experts[1] = model.experts[1], model.experts[0]
                    with torch.no_grad():
                        model.router.weight[:] = base.router.weight[[1, 0, 2, 3]]
                        model.router.bias[:] = base.router.bias[[1, 0, 2, 3]]
                metrics = {key: evaluate(model, d) for key, d in tests.items()}
                with torch.no_grad():
                    drift = (model(tests['id'][0])[0]-base(tests['id'][0])[0]).abs().max().item()
                if intervention in ('self', 'permutation_control'):
                    assert drift < 1e-5, (intervention, drift)
                swaps.append(dict(task=task, seed=seed, donor_seed=donor_seed if intervention == 'cross_seed' else seed,
                                  intervention=intervention, metrics=metrics, max_prediction_drift=drift))
    aggregates, contrasts = [], []
    lookup = {(r['task'], r['seed'], r['condition']): r for r in records}
    def values(task, cond, split):
        return np.array([lookup[task, s, cond]['metrics'][split]['nmse'] for s in range(args.seeds)])
    for task in TASKS:
        for split in ('id', 'ood'):
            for cond in CONDITIONS:
                aggregates.append(dict(task=task, split=split, condition=cond, **summary(values(task, cond, split))))
            for baseline in ('ternary_fixed', 'ternary_dense', 'ternary_wide', 'fp_dense'):
                # Positive means learned ternary has smaller error.
                contrasts.append(dict(task=task, split=split, baseline=baseline,
                                      **comparison(values(task, baseline, split)-values(task, 'ternary_learned', split))))
    for split in ('id', 'ood'):
        interaction = ((values('selection', 'ternary_fixed', split)-values('selection', 'ternary_learned', split))
                       -(values('precision', 'ternary_fixed', split)-values('precision', 'ternary_learned', split)))
        contrasts.append(dict(task='selection_minus_precision', split=split, baseline='interaction', **comparison(interaction)))
    holm(contrasts)  # one family, including ID/OOD and interactions (18 tests)
    report = dict(config=vars(args), python=platform.python_version(), torch=torch.__version__,
                  device='cpu', dtype='float32', source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  elapsed_seconds=time.time()-start, records=records, aggregates=aggregates,
                  contrasts=contrasts, swaps=swaps)
    (output/'results.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, default=8)
    parser.add_argument('--steps', type=int, default=400)
    parser.add_argument('--output', default='results/pilot')
    args = parser.parse_args()
    if not 2 <= args.seeds <= 16 or args.steps < 1:
        parser.error('seeds must be 2..16; steps must be positive')
    run(args)
