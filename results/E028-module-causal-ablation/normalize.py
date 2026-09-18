"""Preserve the E028 emitted file and normalize undefined sample variances.

The completed experiment's source uses NumPy ddof=1. A condition with one exact
solution has undefined sample variance and NumPy emits NaN, which Python's
json.dumps writes as non-standard JSON. This post-run conversion changes only
non-finite aggregate metrics to JSON null; individual records are untouched.
"""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / 'run/results.original.json'
OUT = HERE / 'run/results.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean(value, location, changes):
    if isinstance(value, float) and not math.isfinite(value):
        changes.append(location)
        return None
    if isinstance(value, list):
        return [clean(item, f'{location}/{index}', changes) for index, item in enumerate(value)]
    if isinstance(value, dict):
        return {key: clean(item, f'{location}/{key}', changes) for key, item in value.items()}
    return value


data = json.loads(RAW.read_text())
changes = []
normalized = clean(data, '', changes)
assert changes == ['/aggregate/rotate2/primitives/variance'], changes
assert normalized['records'] == data['records']
OUT.write_text(json.dumps(normalized, indent=2, allow_nan=False))
manifest = {'raw_sha256': sha(RAW), 'normalized_sha256': sha(OUT), 'normalizer_sha256': sha(HERE / 'normalize.py'), 'changed_json_pointers': changes, 'reason': 'n=1 exact solution, so the unbiased sample variance is undefined; represented as null.'}
(HERE / 'run/normalization.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest, indent=2))
