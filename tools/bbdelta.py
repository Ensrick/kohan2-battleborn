"""Binary deltas for art painted over a game texture.

A .bbdelta stores our file XOR-ed against the bytes of the game file it was made from
(repeated to length), zlib-compressed. Without the player's own Data.rwd the delta is
noise; with it, the build reproduces our file exactly. The game texture itself is never
stored. Layout:

    BBDELTA1\\n
    {"base": "<Data-relative path>", "base_sha256": "...", "result_sha256": "...", "bytes": n}\\n
    <zlib stream>

Version 2 (BBDELTA2) compresses our file first and XORs the zlib stream against the game
file. A full recolour changes every byte, so the version 1 XOR is incompressible noise
(169 KB for a 256x256 terrain TGA); version 2 stays near our file's own zlib size (75 KB).
make() writes whichever is smaller.
"""

import hashlib
import json
import zlib

MAGIC = b"BBDELTA1\n"
MAGIC2 = b"BBDELTA2\n"


def _mask(data, key):
    if not key:
        raise ValueError("empty base file")
    if not data:
        return b""
    reps = len(data) // len(key) + 1
    k = (key * reps)[:len(data)]
    return (int.from_bytes(data, "little") ^ int.from_bytes(k, "little")).to_bytes(len(data), "little")


def make(base_name, base, mod):
    """The smaller of version 1 and version 2. Both need the game file to decode."""
    meta = {
        "base": base_name,
        "base_sha256": hashlib.sha256(base).hexdigest(),
        "result_sha256": hashlib.sha256(mod).hexdigest(),
        "bytes": len(mod),
    }
    head = json.dumps(meta, sort_keys=True).encode() + b"\n"
    v1 = MAGIC + head + zlib.compress(_mask(mod, base), 9)
    v2 = MAGIC2 + head + _mask(zlib.compress(mod, 9), base)
    return v1 if len(v1) <= len(v2) else v2


def read_meta(blob):
    magic = blob[:len(MAGIC)]
    if magic not in (MAGIC, MAGIC2):
        raise ValueError("not a Battleborn delta")
    nl = blob.index(b"\n", len(MAGIC))
    meta = json.loads(blob[len(MAGIC):nl])
    meta["version"] = 2 if magic == MAGIC2 else 1
    return meta, blob[nl + 1:]


def apply(blob, get_file, label="delta"):
    meta, payload = read_meta(blob)
    base = get_file(meta["base"])
    if base is None:
        raise ValueError(f"{label}: game file {meta['base']} not found in Data.rwd")
    if hashlib.sha256(base).hexdigest() != meta["base_sha256"]:
        raise ValueError(f"{label}: game file {meta['base']} differs from the retail version this delta targets")
    if meta["version"] == 2:
        out = zlib.decompress(_mask(payload, base))
    else:
        out = _mask(zlib.decompress(payload), base)
    if len(out) != meta["bytes"] or hashlib.sha256(out).hexdigest() != meta["result_sha256"]:
        raise ValueError(f"{label}: result does not match the expected file")
    return out
