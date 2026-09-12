"""Forced-depth differentiable LUT circuit for E017 pilot 2."""
import math
from pathlib import Path
import sys

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from model import TASKS, data, metrics, split


def st_one_hot(logits, temperature):
    soft = torch.softmax(logits / temperature, -1)
    hard = F.one_hot(soft.argmax(-1), soft.shape[-1]).float()
    return hard + soft - soft.detach()


class LayeredCircuit(torch.nn.Module):
    def __init__(self, seed, initialization, layers=5, width=16):
        super().__init__()
        self.layers = layers
        self.width = width
        generator = torch.Generator().manual_seed(seed)
        self.a_logits = torch.nn.ParameterList()
        self.b_logits = torch.nn.ParameterList()
        self.table_logits = torch.nn.ParameterList()
        for layer in range(layers):
            source_count = 6 if layer == 0 else 6 + width
            self.a_logits.append(torch.nn.Parameter(torch.randn(width, source_count, generator=generator) * .05))
            self.b_logits.append(torch.nn.Parameter(torch.randn(width, source_count, generator=generator) * .05))
            if initialization == "random_tables":
                tables = torch.randn(width, 4, generator=generator) * .05
            elif initialization == "diverse_tables":
                order = torch.randperm(16, generator=generator)
                bits = ((order[:, None] >> torch.arange(4)) & 1).float()
                tables = (2 * bits - 1) * .5 + torch.randn(width, 4, generator=generator) * .02
            else:
                raise ValueError(initialization)
            self.table_logits.append(torch.nn.Parameter(tables))
        self.output_logits = torch.nn.Parameter(torch.randn(width, generator=generator) * .05)

    def forward(self, x, temperature=1., hard=False, straight_through=False):
        previous = None
        entropies = []
        softness = []
        for layer, (a_logits, b_logits, table_logits) in enumerate(zip(self.a_logits, self.b_logits, self.table_logits)):
            sources = x if layer == 0 else torch.cat((x, previous), 1)
            soft_a = torch.softmax(a_logits / temperature, -1)
            soft_b = torch.softmax(b_logits / temperature, -1)
            if hard:
                weight_a = F.one_hot(soft_a.argmax(-1), soft_a.shape[-1]).float()
                weight_b = F.one_hot(soft_b.argmax(-1), soft_b.shape[-1]).float()
            elif straight_through:
                weight_a = st_one_hot(a_logits, temperature)
                weight_b = st_one_hot(b_logits, temperature)
            else:
                weight_a, weight_b = soft_a, soft_b
            a = sources @ weight_a.T
            b = sources @ weight_b.T
            probability = torch.sigmoid(table_logits / temperature)
            if hard:
                table = (probability >= .5).float()
            elif straight_through:
                binary = (probability >= .5).float()
                table = binary + probability - probability.detach()
            else:
                table = probability
            basis = torch.stack(((1-a)*(1-b), a*(1-b), (1-a)*b, a*b), -1)
            previous = (basis * table[None]).sum(-1)
            normalizer = math.log(sources.shape[1])
            entropies.append((
                -(soft_a * soft_a.clamp_min(1e-12).log()).sum(-1).mean()
                -(soft_b * soft_b.clamp_min(1e-12).log()).sum(-1).mean()
            ) / (2 * normalizer))
            softness.append((4 * probability * (1-probability)).mean())
        output_soft = torch.softmax(self.output_logits / temperature, -1)
        if hard:
            output_weight = F.one_hot(output_soft.argmax(-1), self.width).float()
        elif straight_through:
            output_weight = st_one_hot(self.output_logits, temperature)
        else:
            output_weight = output_soft
        prediction = previous @ output_weight[:, None]
        output_entropy = -(output_soft * output_soft.clamp_min(1e-12).log()).sum() / math.log(self.width)
        return prediction, {
            "selector_entropy": torch.stack(entropies + [output_entropy]).mean(),
            "table_softness": torch.stack(softness).mean(),
        }

    def hard_spec(self):
        result = []
        for layer, (a, b, table) in enumerate(zip(self.a_logits, self.b_logits, self.table_logits)):
            result.append({
                "a": a.argmax(-1).tolist(),
                "b": b.argmax(-1).tolist(),
                "tables": (table >= 0).long().tolist(),
            })
        return {"layers": result, "output": int(self.output_logits.argmax())}


def spec_forward(spec, x):
    previous = None
    for layer_index, layer in enumerate(spec["layers"]):
        sources = x.bool() if layer_index == 0 else torch.cat((x.bool(), previous), 1)
        a = sources[:, layer["a"]]
        b = sources[:, layer["b"]]
        table = torch.tensor(layer["tables"], dtype=torch.bool)
        index = a.long() + 2 * b.long()
        previous = torch.gather(table[None].expand(len(x), -1, -1), 2, index[..., None]).squeeze(-1)
    return previous[:, spec["output"]:spec["output"]+1].float()


def live_gate_count(spec):
    needed = {spec["output"]}
    live = 0
    for layer_index in reversed(range(len(spec["layers"]))):
        layer = spec["layers"][layer_index]
        next_needed = set()
        for local in needed:
            live += 1
            for source in (layer["a"][local], layer["b"][local]):
                if layer_index > 0 and source >= 6:
                    next_needed.add(source - 6)
        needed = next_needed
        if not needed:
            break
    return live


def one_run(task, seed, initialization, restart, steps=1600):
    x, y = data(task)
    train_index, test_index = split(task, seed)
    parameter_seed = seed * 100 + TASKS.index(task) * 10 + restart
    network = LayeredCircuit(parameter_seed, initialization)
    optimizer = torch.optim.Adam(network.parameters(), lr=.02)
    curve = []
    for step in range(steps):
        temperature = 1 - .8 * step / (steps - 1)
        straight_through = step >= steps // 2
        prediction, auxiliary = network(x[train_index], temperature, False, straight_through)
        task_loss = F.binary_cross_entropy(prediction.clamp(1e-6, 1-1e-6), y[train_index])
        loss = task_loss + .002 * auxiliary["table_softness"] + .001 * auxiliary["selector_entropy"]
        optimizer.zero_grad()
        loss.backward()
        assert all(torch.isfinite(p.grad).all() for p in network.parameters() if p.grad is not None)
        optimizer.step()
        if step in (0, steps-1) or step % 400 == 0:
            curve.append({"step": step, "temperature": temperature, "straight_through": straight_through, "task_loss": float(task_loss.detach()), **{key: float(value.detach()) for key, value in auxiliary.items()}})
    with torch.no_grad():
        soft, _ = network(x, .2, False, False)
        hard, _ = network(x, .2, True, False)
        spec = network.hard_spec()
        exported = spec_forward(spec, x)
        final_train_bce = float(F.binary_cross_entropy(soft[train_index].clamp(1e-6, 1-1e-6), y[train_index]))
    assert torch.equal(hard, exported)
    return network, {
        "task": task,
        "seed": seed,
        "initialization": initialization,
        "restart": restart,
        "train_indices": train_index.tolist(),
        "test_indices": test_index.tolist(),
        "soft_train": metrics(soft[train_index], y[train_index]),
        "soft_test": metrics(soft[test_index], y[test_index]),
        "hard_train": metrics(hard[train_index], y[train_index]),
        "hard_test": metrics(hard[test_index], y[test_index]),
        "hard_full": metrics(hard, y),
        "final_train_bce": final_train_bce,
        "live_gates": live_gate_count(spec),
        "spec": spec,
        "curve": curve,
    }

