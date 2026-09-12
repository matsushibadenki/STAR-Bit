"""Differentiable stateful Logic PE experts with schedule and input routing."""
import itertools
import math
import numpy as np
import torch


def data(task):
    x = ((np.arange(64)[:, None] >> np.arange(6)) & 1).astype(np.float32)
    if task == "numeric":
        total = x[:, :3] @ np.array([1, 2, 4]) + x[:, 3:] @ np.array([1, 2, 4])
        y = ((total.astype(int)[:, None] >> np.arange(4)) & 1).astype(np.float32)
    else:
        shift = (x[:, 0] + 2 * x[:, 1]).astype(int)
        y = np.stack([x[np.arange(64), 2 + (shift + i) % 4] for i in range(4)], axis=1)
    return torch.tensor(x), torch.tensor(y)


def route_library(task):
    if task == "numeric":
        permutations = list(itertools.permutations(range(3)))
        routes = [(left, right) for left in permutations for right in permutations]
        encoded = torch.tensor([[*left, *right] for left, right in routes], dtype=torch.long)
        oracle = routes.index(((0, 1, 2), (0, 1, 2)))
    else:
        routes = list(itertools.product(range(2), range(4), range(4), range(4), range(4)))
        encoded = torch.tensor(routes, dtype=torch.long)
        oracle = routes.index((0, 0, 1, 0, 2))
    return routes, encoded, oracle


def balanced_hash(seed):
    rng = np.random.default_rng(seed)
    order = rng.permutation(64)
    mapping = np.empty(64, dtype=np.int64)
    mapping[order] = np.arange(64) % 4
    assert np.array_equal(np.bincount(mapping, minlength=4), np.full(4, 16))
    return torch.tensor(mapping, dtype=torch.long)


def lut(a, b, table):
    basis = torch.stack(((1 - a) * (1 - b), a * (1 - b), (1 - a) * b, a * b), dim=-1)
    shape = [table.shape[0]] + [1] * (basis.ndim - 2) + [4]
    return (basis * table.reshape(shape)).sum(-1)


class LogicMixture(torch.nn.Module):
    def __init__(self, task, seed, condition):
        super().__init__()
        self.task = task
        self.condition = condition
        self.routes, encoded, self.oracle_index = route_library(task)
        self.register_buffer("route_codes", encoded)
        self.register_buffer("hash_map", balanced_hash(seed + (5000 if task == "selection" else 0)))
        generator = torch.Generator().manual_seed(seed + (1000 if task == "selection" else 0))
        gate_count = 5 if task == "numeric" else 12
        self.gate_logits = torch.nn.Parameter(torch.randn(4, gate_count, 4, generator=generator) * 0.1)
        self.schedule_logits = torch.nn.Parameter(torch.randn(4, len(self.routes), generator=generator) * 0.01)
        self.router_weight = torch.nn.Parameter(torch.randn(7, 4, generator=generator) * 0.01)

    def tables(self, temperature, hard, logits=None):
        probabilities = torch.sigmoid((self.gate_logits if logits is None else logits) / temperature)
        return (probabilities >= 0.5).float() if hard else probabilities

    def schedules(self, temperature, hard, logits=None):
        probabilities = torch.softmax((self.schedule_logits if logits is None else logits) / temperature, dim=1)
        if hard:
            indices = probabilities.argmax(1)
            return torch.nn.functional.one_hot(indices, len(self.routes)).float()
        return probabilities

    def numeric_candidates(self, x, tables):
        codes = self.route_codes
        left = x[:, codes[:, :3]].permute(1, 0, 2)
        right = x[:, 3 + codes[:, 3:]].permute(1, 0, 2)
        left = left.unsqueeze(0).expand(4, -1, -1, -1)
        right = right.unsqueeze(0).expand(4, -1, -1, -1)
        carry = torch.zeros_like(left[:, :, :, 0]); outputs = []
        for cycle in range(3):
            a, b = left[:, :, :, cycle], right[:, :, :, cycle]
            propagate = lut(a, b, tables[:, 0])
            result = lut(propagate, carry, tables[:, 1])
            generate = lut(a, b, tables[:, 2])
            carried = lut(propagate, carry, tables[:, 3])
            carry = lut(generate, carried, tables[:, 4])
            outputs.append(result)
        outputs.append(carry)
        return torch.stack(outputs, dim=-1)

    @staticmethod
    def shifted(state, offsets):
        expert, candidate, sample, lane = state.shape
        lanes = torch.arange(4, device=state.device)[None, :] + offsets[:, None]
        indices = (lanes % 4)[None, :, None, :].expand(expert, candidate, sample, lane)
        return torch.gather(state, 3, indices)

    def selection_candidates(self, x, tables):
        codes = self.route_codes
        state = x[:, 2:6][None, None].expand(4, len(codes), -1, -1)
        selector_order = torch.stack((codes[:, 0], 1 - codes[:, 0]), dim=1)
        for cycle in range(2):
            selector = x[:, selector_order[:, cycle]].T[None].expand(4, -1, -1)
            a = self.shifted(state, codes[:, 1 + 2 * cycle])
            b = self.shifted(state, codes[:, 2 + 2 * cycle])
            lanes = []
            for lane_index in range(4):
                first = lut(selector, a[:, :, :, lane_index], tables[:, lane_index * 3])
                second = lut(selector, b[:, :, :, lane_index], tables[:, lane_index * 3 + 1])
                lanes.append(lut(first, second, tables[:, lane_index * 3 + 2]))
            state = torch.stack(lanes, dim=-1)
        return state

    def candidate_outputs(self, x, temperature=1.0, hard=False, gate_logits=None):
        tables = self.tables(temperature, hard, gate_logits)
        return self.numeric_candidates(x, tables) if self.task == "numeric" else self.selection_candidates(x, tables)

    def router(self, x, hard=False, router_weight=None, hash_map=None):
        if self.condition == "fixed_hash":
            mapping = self.hash_map if hash_map is None else hash_map
            indices = (x * (2 ** torch.arange(6, device=x.device))).sum(1).long()
            return torch.nn.functional.one_hot(mapping[indices], 4).float()
        weight = self.router_weight if router_weight is None else router_weight
        logits = torch.column_stack((x, torch.ones(len(x), device=x.device))) @ weight
        probabilities = torch.softmax(logits, dim=1)
        if hard:
            return torch.nn.functional.one_hot(probabilities.argmax(1), 4).float()
        return probabilities

    def forward(self, x, temperature=1.0, hard=False, gate_logits=None, schedule_logits=None, router_weight=None, hash_map=None):
        candidates = self.candidate_outputs(x, temperature, hard, gate_logits)
        schedule = self.schedules(temperature, hard, schedule_logits)
        experts = torch.einsum("ec,ecno->eno", schedule, candidates)
        routing = self.router(x, hard, router_weight, hash_map)
        prediction = torch.einsum("ne,eno->no", routing, experts)
        return prediction, routing, schedule


def oracle_parameters(model):
    tables = torch.zeros_like(model.gate_logits)
    xor, and_gate, or_gate = [-10, 10, 10, -10], [-10, -10, -10, 10], [-10, 10, 10, 10]
    if model.task == "numeric":
        template = torch.tensor([xor, xor, and_gate, and_gate, or_gate], dtype=torch.float32)
    else:
        first, second = [-10, -10, 10, -10], and_gate
        template = torch.tensor([value for _ in range(4) for value in (first, second, or_gate)], dtype=torch.float32)
    tables[:] = template
    schedules = torch.full_like(model.schedule_logits, -10.0); schedules[:, model.oracle_index] = 10.0
    return tables, schedules


def metrics(prediction, target):
    bits = prediction >= 0.5
    return dict(exact=float((bits == target.bool()).all(1).float().mean()), bit_accuracy=float((bits == target.bool()).float().mean()))


def train(task, seed, condition, steps, learning_rate, temperature_floor, discrete_weight, balance_weight):
    x, y = data(task); split_rng = np.random.default_rng(seed + (20000 if task == "selection" else 0)); order = split_rng.permutation(64); train_indices, test_indices = order[:32], order[32:]
    model = LogicMixture(task, seed, condition); optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate); curve = []
    for step in range(steps):
        temperature = 1 - (1 - temperature_floor) * step / max(1, steps - 1)
        prediction, routing, schedule = model(x[train_indices], temperature, False)
        clipped = prediction.clamp(1e-6, 1 - 1e-6)
        task_loss = torch.nn.functional.binary_cross_entropy(clipped, y[train_indices])
        importance = routing.mean(0); balance = 4 * (importance.square().sum()) - 1
        schedule_entropy = -(schedule * schedule.clamp_min(1e-12).log()).sum(1).mean() / math.log(schedule.shape[1])
        table_prob = torch.sigmoid(model.gate_logits / temperature); table_softness = (4 * table_prob * (1 - table_prob)).mean()
        loss = task_loss + balance_weight * balance + discrete_weight * (schedule_entropy + table_softness)
        optimizer.zero_grad(); loss.backward(); optimizer.step()
        if step in (0, steps - 1) or step % 100 == 0:
            assert all(torch.isfinite(parameter.grad).all() for parameter in model.parameters() if parameter.grad is not None)
            curve.append(dict(step=step, temperature=temperature, loss=float(loss), task_loss=float(task_loss), balance_loss=float(balance), schedule_entropy=float(schedule_entropy), table_softness=float(table_softness)))
    evaluations = {}
    with torch.no_grad():
        for hard in (False, True):
            pred, routing, schedule = model(x, temperature_floor, hard)
            label = "hard" if hard else "soft"
            evaluations[label] = dict(train=metrics(pred[train_indices], y[train_indices]), test=metrics(pred[test_indices], y[test_indices]), full=metrics(pred, y), utilization_train=routing[train_indices].mean(0).tolist(), utilization_test=routing[test_indices].mean(0).tolist(), utilization_full=routing.mean(0).tolist(), selected_schedules=schedule.argmax(1).tolist())
    return model, dict(task=task, seed=seed, condition=condition, train_indices=train_indices.tolist(), test_indices=test_indices.tolist(), evaluations=evaluations, curve=curve)
