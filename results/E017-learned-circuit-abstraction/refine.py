"""Bit-parallel discrete refinement for layered two-input LUT circuits."""
import copy
import random


FULL = (1 << 64) - 1


def columns_and_target(task):
    columns = []
    for bit in range(6):
        value = 0
        for row in range(64):
            value |= ((row >> bit) & 1) << row
        columns.append(value)
    target = 0
    for row in range(64):
        bits = [(row >> bit) & 1 for bit in range(6)]
        if task == "parity":
            answer = sum(bits) % 2
        elif task == "comparator":
            answer = sum(bits[i] << i for i in range(3)) > sum(bits[i+3] << i for i in range(3))
        elif task == "mux":
            answer = bits[1] if bits[0] else bits[2]
        elif task == "carry":
            answer = sum(bits[i] << i for i in range(3)) + sum(bits[i+3] << i for i in range(3)) >= 8
        else:
            raise ValueError(task)
        target |= int(answer) << row
    return columns, target


def lut(a, b, code):
    not_a = (~a) & FULL
    not_b = (~b) & FULL
    value = 0
    if code & 1:
        value |= not_a & not_b
    if code & 2:
        value |= a & not_b
    if code & 4:
        value |= not_a & b
    if code & 8:
        value |= a & b
    return value


def from_spec(spec):
    layers = []
    for layer in spec["layers"]:
        nodes = []
        for a, b, table in zip(layer["a"], layer["b"], layer["tables"]):
            code = sum(int(value) << index for index, value in enumerate(table))
            nodes.append([int(a), int(b), code])
        layers.append(nodes)
    return {"layers": layers, "output": int(spec["output"])}


def random_genome(seed, layers=5, width=16):
    rng = random.Random(seed)
    result = []
    for layer in range(layers):
        source_count = 6 if layer == 0 else 6 + width
        result.append([[rng.randrange(source_count), rng.randrange(source_count), rng.randrange(16)] for _ in range(width)])
    return {"layers": result, "output": rng.randrange(width)}


def evaluate(genome, columns):
    previous = None
    for layer_index, layer in enumerate(genome["layers"]):
        sources = columns if layer_index == 0 else columns + previous
        previous = [lut(sources[a], sources[b], code) for a, b, code in layer]
    return previous[genome["output"]]


def live_nodes(genome):
    needed = {genome["output"]}
    live = set()
    for layer_index in reversed(range(len(genome["layers"]))):
        next_needed = set()
        for node in needed:
            live.add((layer_index, node))
            a, b, _ = genome["layers"][layer_index][node]
            if layer_index > 0:
                if a >= 6:
                    next_needed.add(a - 6)
                if b >= 6:
                    next_needed.add(b - 6)
        needed = next_needed
        if not needed:
            break
    return live


def mutate(parent, rng):
    child = copy.deepcopy(parent)
    for _ in range(rng.randint(1, 4)):
        if rng.random() < .08:
            child["output"] = rng.randrange(16)
            continue
        live = tuple(live_nodes(child))
        if live and rng.random() < .7:
            layer_index, node_index = rng.choice(live)
        else:
            layer_index, node_index = rng.randrange(5), rng.randrange(16)
        gene = child["layers"][layer_index][node_index]
        field = rng.randrange(3)
        limit = 6 if layer_index == 0 else 22
        if field < 2:
            value = rng.randrange(limit - 1)
            if value >= gene[field]:
                value += 1
            gene[field] = value
        else:
            value = rng.randrange(15)
            if value >= gene[2]:
                value += 1
            gene[2] = value
    return child


def search(task, start, seed, budget=100000):
    columns, target = columns_and_target(task)
    rng = random.Random(seed)
    current = copy.deepcopy(start)
    current_error = (evaluate(current, columns) ^ target).bit_count()
    initial_error = current_error
    best = copy.deepcopy(current)
    best_error = current_error
    exact_at = 0 if current_error == 0 else None
    for proposal in range(1, budget + 1):
        if best_error == 0:
            break
        child = mutate(current, rng)
        error = (evaluate(child, columns) ^ target).bit_count()
        if error < best_error:
            best, best_error = copy.deepcopy(child), error
            if error == 0:
                exact_at = proposal
        if error < current_error or (error == current_error and rng.random() < .1):
            current, current_error = child, error
    return best, {
        "initial_error": initial_error,
        "final_error": best_error,
        "exact": best_error == 0,
        "proposals_to_exact": exact_at,
        "proposals_budget": budget,
        "live_gates": len(live_nodes(best)),
    }

