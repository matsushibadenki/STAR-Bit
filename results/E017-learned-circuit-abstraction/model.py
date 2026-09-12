"""Differentiable two-input LUT circuit with trainable source wiring."""
import math
import os

for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"

import numpy as np
import torch
import torch.nn.functional as F

torch.set_num_threads(1)


TASKS = ("parity", "comparator", "mux", "carry")


def data(task):
    x = ((np.arange(64)[:, None] >> np.arange(6)) & 1).astype(np.float32)
    if task == "parity":
        y = (x.sum(1).astype(int) % 2).astype(np.float32)
    elif task == "comparator":
        left = x[:, :3] @ np.array([1, 2, 4])
        right = x[:, 3:] @ np.array([1, 2, 4])
        y = (left > right).astype(np.float32)
    elif task == "mux":
        y = np.where(x[:, 0] > .5, x[:, 1], x[:, 2]).astype(np.float32)
    elif task == "carry":
        left = x[:, :3] @ np.array([1, 2, 4])
        right = x[:, 3:] @ np.array([1, 2, 4])
        y = (left + right >= 8).astype(np.float32)
    else:
        raise ValueError(task)
    return torch.tensor(x), torch.tensor(y[:, None])


def split(task, seed):
    task_offset = TASKS.index(task) * 10000
    order = np.random.default_rng(seed + task_offset).permutation(64)
    return order[:48], order[48:]


def straight_through_one_hot(logits, temperature):
    soft = torch.softmax(logits / temperature, dim=-1)
    hard = F.one_hot(soft.argmax(-1), soft.shape[-1]).float()
    return hard + soft - soft.detach()


class Circuit(torch.nn.Module):
    def __init__(self, seed, widths=(12, 12, 8)):
        super().__init__()
        generator = torch.Generator().manual_seed(seed)
        self.widths = tuple(widths)
        self.a_logits = torch.nn.ParameterList()
        self.b_logits = torch.nn.ParameterList()
        self.table_logits = torch.nn.ParameterList()
        bank = 6
        for width in self.widths:
            self.a_logits.append(torch.nn.Parameter(torch.randn(width, bank, generator=generator) * .05))
            self.b_logits.append(torch.nn.Parameter(torch.randn(width, bank, generator=generator) * .05))
            self.table_logits.append(torch.nn.Parameter(torch.randn(width, 4, generator=generator) * .05))
            bank += width
        self.output_logits = torch.nn.Parameter(torch.randn(bank, generator=generator) * .05)

    def forward(self, x, temperature=1., hard=False, straight_through=False):
        bank = x
        selector_entropies = []
        table_softness = []
        depth_costs = []
        for a_logits, b_logits, table_logits in zip(self.a_logits, self.b_logits, self.table_logits):
            soft_a = torch.softmax(a_logits / temperature, -1)
            soft_b = torch.softmax(b_logits / temperature, -1)
            if hard:
                a_weight = F.one_hot(soft_a.argmax(-1), soft_a.shape[-1]).float()
                b_weight = F.one_hot(soft_b.argmax(-1), soft_b.shape[-1]).float()
            elif straight_through:
                a_weight = straight_through_one_hot(a_logits, temperature)
                b_weight = straight_through_one_hot(b_logits, temperature)
            else:
                a_weight, b_weight = soft_a, soft_b
            a = bank @ a_weight.T
            b = bank @ b_weight.T
            probability = torch.sigmoid(table_logits / temperature)
            if hard:
                table = (probability >= .5).float()
            elif straight_through:
                binary = (probability >= .5).float()
                table = binary + probability - probability.detach()
            else:
                table = probability
            basis = torch.stack(((1-a)*(1-b), a*(1-b), (1-a)*b, a*b), -1)
            out = (basis * table[None]).sum(-1)
            normalizer = math.log(max(2, bank.shape[1]))
            selector_entropies.append((
                -(soft_a * soft_a.clamp_min(1e-12).log()).sum(-1).mean()
                -(soft_b * soft_b.clamp_min(1e-12).log()).sum(-1).mean()
            ) / (2 * normalizer))
            table_softness.append((4 * probability * (1-probability)).mean())
            depth = torch.linspace(0, 1, bank.shape[1], device=x.device)
            depth_costs.append(((soft_a + soft_b) * depth[None]).sum(-1).mean() / 2)
            bank = torch.cat((bank, out), 1)
        output_soft = torch.softmax(self.output_logits / temperature, -1)
        if hard:
            output_weight = F.one_hot(output_soft.argmax(-1), output_soft.shape[-1]).float()
        elif straight_through:
            output_weight = straight_through_one_hot(self.output_logits, temperature)
        else:
            output_weight = output_soft
        prediction = bank @ output_weight[:, None]
        output_entropy = -(output_soft * output_soft.clamp_min(1e-12).log()).sum() / math.log(len(output_soft))
        auxiliary = {
            "selector_entropy": torch.stack(selector_entropies + [output_entropy]).mean(),
            "table_softness": torch.stack(table_softness).mean(),
            "depth_cost": torch.stack(depth_costs).mean(),
        }
        return prediction, auxiliary

    def hard_spec(self):
        layers = []
        offset = 6
        for a, b, table in zip(self.a_logits, self.b_logits, self.table_logits):
            entries = (table >= 0).to(torch.int64)
            layers.append({
                "a": a.argmax(-1).tolist(),
                "b": b.argmax(-1).tolist(),
                "tables": entries.tolist(),
                "offset": offset,
            })
            offset += len(entries)
        return {"layers": layers, "output": int(self.output_logits.argmax())}


def hard_spec_forward(spec, x):
    bank = x.bool()
    for layer in spec["layers"]:
        a = bank[:, layer["a"]]
        b = bank[:, layer["b"]]
        tables = torch.tensor(layer["tables"], dtype=torch.bool)
        index = a.long() + 2 * b.long()
        out = torch.gather(tables[None].expand(len(x), -1, -1), 2, index[..., None]).squeeze(-1)
        bank = torch.cat((bank, out), 1)
    return bank[:, spec["output"]:spec["output"]+1].float()


def live_gate_count(spec):
    offsets = [layer["offset"] for layer in spec["layers"]]
    needed = {spec["output"]}
    live = set()
    for layer_index in reversed(range(len(spec["layers"]))):
        layer = spec["layers"][layer_index]
        for node in list(needed):
            local = node - offsets[layer_index]
            if 0 <= local < len(layer["tables"]):
                live.add(node)
                needed.add(layer["a"][local])
                needed.add(layer["b"][local])
    return len(live)


def metrics(prediction, target):
    bits = prediction >= .5
    return {"accuracy": float((bits == target.bool()).float().mean())}


def train(task, seed, mode, steps=1200):
    x, y = data(task)
    train_index, test_index = split(task, seed)
    network = Circuit(seed + TASKS.index(task) * 100000)
    optimizer = torch.optim.Adam(network.parameters(), lr=.03)
    curve = []
    for step in range(steps):
        temperature = 1 - .85 * step / (steps - 1)
        straight_through = mode == "st_second_half" and step >= steps // 2
        prediction, auxiliary = network(x[train_index], temperature, False, straight_through)
        task_loss = F.binary_cross_entropy(prediction.clamp(1e-6, 1-1e-6), y[train_index])
        loss = task_loss + .01 * auxiliary["table_softness"] + .005 * auxiliary["selector_entropy"] + .001 * auxiliary["depth_cost"]
        optimizer.zero_grad()
        loss.backward()
        assert all(torch.isfinite(p.grad).all() for p in network.parameters() if p.grad is not None)
        optimizer.step()
        if step in (0, steps-1) or step % 200 == 0:
            curve.append({"step": step, "temperature": temperature, "straight_through": straight_through, "task_loss": float(task_loss.detach()), **{key: float(value.detach()) for key, value in auxiliary.items()}})
    with torch.no_grad():
        soft, _ = network(x, .15, False, False)
        hard, _ = network(x, .15, True, False)
        spec = network.hard_spec()
        exported = hard_spec_forward(spec, x)
    assert torch.equal(hard, exported)
    return network, {
        "task": task,
        "seed": seed,
        "mode": mode,
        "train_indices": train_index.tolist(),
        "test_indices": test_index.tolist(),
        "soft_train": metrics(soft[train_index], y[train_index]),
        "soft_test": metrics(soft[test_index], y[test_index]),
        "soft_full": metrics(soft, y),
        "hard_train": metrics(hard[train_index], y[train_index]),
        "hard_test": metrics(hard[test_index], y[test_index]),
        "hard_full": metrics(hard, y),
        "live_gates": live_gate_count(spec),
        "export_equivalent": True,
        "spec": spec,
        "curve": curve,
    }

