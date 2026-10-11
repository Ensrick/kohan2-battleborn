"""Battleborn patch format: a game data file described as "the player's own copy of a
TimeGate file, plus only our changes". Patches never contain TimeGate text: removed
lines are recorded as a count and a hash, and any block we reuse from a game file is a
reference (file + line range) resolved from the player's Data.rwd at build time.

Format (UTF-8 text, LF line endings, one directive per line):

    # comment
    base <Data-relative path> sha256=<hex>       (omitted for files with no base)
    ref <Data-relative path> sha256=<hex>        (one per extra game file referenced by '=')
    result sha256=<hex> bytes=<n>                (checked after applying)
    bom yes|no                                   (UTF-8 byte-order mark on the result)
    eol crlf | eol lf | eol crlf*120 lf*3 none*1 (line endings of the result, run-length)

    @@ <line> -<count>[:<hash8>] +<count> @@ <section path, informational>
    +<text>                   one of our lines
    = <path> <first>-<last>   lines first..last (1-based, inclusive) of a game file

Text is compared without line endings or the byte-order mark; the result's endings come
from the 'eol' runs. <line> is the 1-based base line where a hunk starts; '-count' base
lines are dropped there (their hash guards against a different base), then '+count'
lines are added.
"""

import difflib
import hashlib
import re

BOM = b"\xef\xbb\xbf"
TERMS = {b"\r\n": "crlf", b"\n": "lf", b"": "none"}
TERM_BYTES = {v: k for k, v in TERMS.items()}
MIN_REF_RUN = 3            # shortest reused block written as a reference instead of text
HEADER_RE = re.compile(rb"^\s*\[\s*([A-Za-z_]\w*)")
IDS_RE = re.compile(rb"^\s*IDS\s*=\s*([^\s;]+)", re.I)


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def split(data):
    """bytes -> (has_bom, [body], [terminator]); bodies exclude line endings and the BOM."""
    bom = data.startswith(BOM)
    if bom:
        data = data[3:]
    bodies, terms = [], []
    start = 0
    while start < len(data):
        nl = data.find(b"\n", start)
        if nl < 0:
            bodies.append(data[start:])
            terms.append(b"")
            break
        line = data[start:nl]
        if line.endswith(b"\r"):
            bodies.append(line[:-1])
            terms.append(b"\r\n")
        else:
            bodies.append(line)
            terms.append(b"\n")
        start = nl + 1
    return bom, bodies, terms


def is_substantive(body):
    s = body.strip()
    return len(s) > 3 and s not in (b"{", b"}")


def section_paths(bodies):
    """For each line index, a readable path like '[Unit bowman] > [BodyComponent]'."""
    paths = []
    stack = []              # labels of open { } scopes
    loose = {}              # depth -> label of a brace-less section open at that depth
    pending = None
    for body in bodies:
        s = body.split(b";", 1)[0].strip()
        depth = len(stack)
        cur = list(stack)
        if depth in loose:
            cur.append(loose[depth])
        paths.append(" > ".join(cur))
        if not s:
            continue
        m = HEADER_RE.match(s)
        if m:
            pending = "[" + m.group(1).decode("ascii", "replace") + "]"
            loose[depth] = pending
        m = IDS_RE.match(s)
        if m:
            name = m.group(1).decode("utf-8", "replace")
            if depth in loose and " " not in loose[depth]:
                loose[depth] = loose[depth][:-1] + " " + name + "]"
            elif stack and " " not in stack[-1]:
                stack[-1] = stack[-1][:-1] + " " + name + "]"
        for ch in s:
            if ch == ord("{"):
                stack.append(loose.pop(len(stack), pending or "{}"))
                pending = None
            elif ch == ord("}"):
                loose.pop(len(stack), None)
                if stack:
                    stack.pop()
    return paths


class RefIndex:
    """Index of game-file lines, used to turn reused blocks into references.

    Blocks are found with indentation ignored, so a block we re-indented or whose blank
    lines carry different whitespace is still recognised; inside such a block, lines that
    match exactly become references and only whitespace-different lines stay literal.
    """

    def __init__(self):
        self.files = {}         # name -> (sha256, [body], [normalized body])
        self.by_norm = {}       # normalized body -> [(name, idx)]

    def add(self, name, data, cap=4000):
        _, bodies, _ = split(data)
        norms = [b.strip() for b in bodies]
        self.files[name] = (sha256(data), bodies, norms)
        for i, nb in enumerate(norms):
            if is_substantive(nb):
                lst = self.by_norm.setdefault(nb, [])
                if len(lst) < cap:
                    lst.append((name, i))

    def longest_run(self, added, k, prefer):
        """-> (length, game file, start index, substantive lines) of the best indentation-blind match."""
        target = [b.strip() for b in added]
        best = (0, None, 0, 0)
        for name, idx in self.by_norm.get(target[k], ()):
            norms = self.files[name][2]
            n = subst = 0
            while k + n < len(added) and idx + n < len(norms) and norms[idx + n] == target[k + n]:
                subst += is_substantive(target[k + n])
                n += 1
            if subst > best[3] or (subst == best[3] and name == prefer and best[1] != prefer):
                best = (n, name, idx, subst)
        return best


def eol_spec(terms):
    runs = []
    for t in terms:
        name = TERMS[t]
        if runs and runs[-1][0] == name:
            runs[-1][1] += 1
        else:
            runs.append([name, 1])
    if len(runs) == 1:
        return runs[0][0]
    if len(runs) == 2 and runs[1] == ["none", 1]:
        return f"{runs[0][0]} none*1"
    return " ".join(f"{n}*{c}" for n, c in runs)


def eol_expand(spec, count):
    parts = spec.split()
    if len(parts) == 1 and "*" not in parts[0]:
        return [TERM_BYTES[parts[0]]] * count
    out = []
    for i, p in enumerate(parts):
        if "*" in p:
            name, c = p.split("*")
            out.extend([TERM_BYTES[name]] * int(c))
        else:                          # leading bare name fills everything not covered after it
            rest = sum(int(q.split("*")[1]) for q in parts[i + 1:])
            out.extend([TERM_BYTES[p]] * (count - len(out) - rest))
    return out


def make(base_name, base, mod, index=None, comment=None):
    """Build patch text that turns `base` (bytes, or None for a file with no base) into `mod`."""
    _, b_bodies, _ = split(base) if base is not None else (False, [], [])
    m_bom, m_bodies, m_terms = split(mod)
    paths = section_paths(b_bodies + [b""])
    sm = difflib.SequenceMatcher(None, b_bodies, m_bodies, autojunk=False)
    hunks, refs = [], {}
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        added = m_bodies[j1:j2]
        body = []
        k = 0
        while k < len(added):
            if index is not None and is_substantive(added[k]):
                n, name, idx, subst = index.longest_run(added, k, base_name)
                if subst >= MIN_REF_RUN:
                    src = index.files[name][1]
                    j = 0
                    while j < n:
                        if added[k + j] != src[idx + j]:          # whitespace-only difference
                            body.append("+" + added[k + j].decode("utf-8"))
                            j += 1
                            continue
                        e = j
                        while e < n and added[k + e] == src[idx + e]:
                            e += 1
                        body.append(f"= {name} {idx + j + 1}-{idx + e}")
                        j = e
                    if name != base_name:
                        refs[name] = index.files[name][0]
                    k += n
                    continue
            body.append("+" + added[k].decode("utf-8"))
            k += 1
        removed = b"\n".join(b_bodies[i1:i2])
        rm = f"-{i2 - i1}" + (f":{sha256(removed)[:8]}" if i2 > i1 else "")
        hunks.append(f"@@ {i1 + 1} {rm} +{j2 - j1} @@ {paths[i1]}".rstrip())
        hunks.extend(body)
    out = ["# Battleborn patch - only Battleborn's own lines; game text is referenced, never copied."]
    if comment:
        out.append("# " + comment)
    if base is not None:
        out.append(f"base {base_name} sha256={sha256(base)}")
    for name in sorted(refs):
        out.append(f"ref {name} sha256={refs[name]}")
    out.append(f"result sha256={sha256(mod)} bytes={len(mod)}")
    out.append("bom " + ("yes" if m_bom else "no"))
    out.append("eol " + eol_spec(m_terms))
    out.append("")
    out.extend(hunks)
    return "\n".join(out) + "\n"


class PatchError(Exception):
    pass


def parse(text):
    meta = {"base": None, "refs": {}, "result": None, "bytes": None, "bom": False, "eol": "crlf"}
    hunks = []
    for line in text.split("\n"):
        if not hunks:
            if not line or line.startswith("#"):
                continue
            key, _, val = line.partition(" ")
            if key in ("base", "ref"):
                name, h = val.rsplit(" sha256=", 1)
                if key == "base":
                    meta["base"] = (name, h)
                else:
                    meta["refs"][name] = h
                continue
            if key == "result":
                m = re.match(r"sha256=([0-9a-f]{64}) bytes=(\d+)", val)
                meta["result"], meta["bytes"] = m.group(1), int(m.group(2))
                continue
            if key == "bom":
                meta["bom"] = val.strip() == "yes"
                continue
            if key == "eol":
                meta["eol"] = val.strip()
                continue
        if line.startswith("@@ "):
            m = re.match(r"@@ (\d+) -(\d+)(?::([0-9a-f]{8}))? \+(\d+) @@", line)
            if not m:
                raise PatchError(f"bad hunk header: {line}")
            hunks.append({"start": int(m.group(1)), "del": int(m.group(2)), "hash": m.group(3),
                          "add": int(m.group(4)), "body": []})
        elif hunks and line:
            hunks[-1]["body"].append(line)
    return meta, hunks


def apply(text, get_file, label="patch"):
    """Apply patch text. get_file(name) returns that game file's bytes from the player's Data.rwd."""
    meta, hunks = parse(text)
    cache = {}

    def bodies_of(name, expect):
        if name not in cache:
            data = get_file(name)
            if data is None:
                raise PatchError(f"{label}: game file {name} not found in Data.rwd")
            if expect and sha256(data) != expect:
                raise PatchError(f"{label}: game file {name} differs from the retail version this patch targets")
            cache[name] = split(data)[1]
        return cache[name]

    base = bodies_of(*meta["base"]) if meta["base"] else []
    out = []
    pos = 0
    for h in hunks:
        s = h["start"] - 1
        if s < pos or s + h["del"] > len(base):
            raise PatchError(f"{label}: hunk at line {h['start']} out of range")
        out.extend(base[pos:s])
        if h["hash"] and sha256(b"\n".join(base[s:s + h["del"]]))[:8] != h["hash"]:
            raise PatchError(f"{label}: base text at line {h['start']} is not what the patch expects")
        produced = 0
        for item in h["body"]:
            if item.startswith("="):
                name, rng = item[1:].strip().rsplit(" ", 1)
                a, b = (int(x) for x in rng.split("-"))
                if meta["base"] and name == meta["base"][0]:
                    src = base
                else:
                    src = bodies_of(name, meta["refs"].get(name))
                out.extend(src[a - 1:b])
                produced += b - a + 1
            elif item.startswith("+"):
                out.append(item[1:].encode("utf-8"))
                produced += 1
            else:
                raise PatchError(f"{label}: bad line {item[:20]!r}")
        if produced != h["add"]:
            raise PatchError(f"{label}: hunk at line {h['start']} produced {produced} lines, expected {h['add']}")
        pos = s + h["del"]
    out.extend(base[pos:])
    terms = eol_expand(meta["eol"], len(out))
    if len(terms) != len(out):
        raise PatchError(f"{label}: line-ending spec covers {len(terms)} lines, result has {len(out)}")
    result = (BOM if meta["bom"] else b"") + b"".join(b + t for b, t in zip(out, terms))
    if meta["result"] and sha256(result) != meta["result"]:
        raise PatchError(f"{label}: result does not match the expected file")
    return result
