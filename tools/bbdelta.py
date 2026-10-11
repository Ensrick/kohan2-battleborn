"""Binary deltas for art painted over a game texture.

A .bbdelta stores our file XOR-ed against the bytes of the game file it was made from
(repeated to length), zlib-compressed. Without the player's own Data.rwd the delta is
noise; with it, the build reproduces our file exactly. The game texture itself is never
stored. Layout:

    BBDELTA1\\n
    {"base": "<Data-relative path>", "base_sha256": "...", "result_sha256": "...", "bytes": n}\\n
    <zlib stream>
"""

import hashlib
import json
import zlib

MAGIC = b"BBDELTA1\n"


def _mask(data, key):
    if not key:
        raise ValueError("empty base file")
    reps = len(data) // len(key) + 1
    k = (key * reps)[:len(data)]
    return bytes(a ^ b for a, b in zip(data, k))


def make(base_name, base, mod):
    meta = {
        "base": base_name,
        "base_sha256": hashlib.sha256(base).hexdigest(),
        "result_sha256": hashlib.sha256(mod).hexdigest(),
        "bytes": len(mod),
    }
    return MAGIC + json.dumps(meta, sort_keys=True).encode() + b"\n" + zlib.compress(_mask(mod, base), 9)


def read_meta(blob):
    if not blob.startswith(MAGIC):
        raise ValueError("not a Battleborn delta")
    nl = blob.index(b"\n", len(MAGIC))
    return json.loads(blob[len(MAGIC):nl]), blob[nl + 1:]


def apply(blob, get_file, label="delta"):
    meta, payload = read_meta(blob)
    base = get_file(meta["base"])
    if base is None:
        raise ValueError(f"{label}: game file {meta['base']} not found in Data.rwd")
    if hashlib.sha256(base).hexdigest() != meta["base_sha256"]:
        raise ValueError(f"{label}: game file {meta['base']} differs from the retail version this delta targets")
    out = _mask(zlib.decompress(payload), base)
    if len(out) != meta["bytes"] or hashlib.sha256(out).hexdigest() != meta["result_sha256"]:
        raise ValueError(f"{label}: result does not match the expected file")
    return out
