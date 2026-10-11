"""Offline reference check for the Battleborn override set.

Overlays the repo's Data/ on a pristine Data.rwd extract (K2ExtractRWD output) and
reports, for Battleborn files only:

  * *_ids references that resolve to no IDS anywhere in the merged tree
  * "#key" localization references with no matching key in Localization/*.tgi
  * resource_prefix / icon / skin / texture / banner_icon / portrait paths with no file
  * top-level IDS defined twice across different files (duplicate-ID hazard)

Vanilla's own unresolved tokens are measured first and treated as baseline noise
(engine-defined IDs, dead vanilla refs), so only Battleborn-introduced problems print.

    py -3 tools/validate.py --vanilla "<path to Data (Backup)>"

Exit code 1 when any Battleborn problem is found.
"""

import argparse
import os
import re
import sys
from collections import defaultdict

HEADER = re.compile(r"^\s*\[([A-Za-z_][\w]*)")
KV = re.compile(r"^\s*([A-Za-z_][\w|]*)\s*=\s*(.*?)\s*$")
LOC_REF = re.compile(r'"#([^"\s]+)"')
PATH_KEYS = {"resource_prefix", "icon", "skin", "texture", "banner_icon", "track_texture",
             "portrait", "small_portrait", "large_portrait"}


def read_text(path):
    raw = open(path, "rb").read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8", errors="replace")


def walk(root):
    out = {}
    for dirpath, _, files in os.walk(root):
        for f in files:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root).replace("\\", "/")
            out[rel.lower()] = full
    return out


def strip_comment(line):
    in_q = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_q = not in_q
        elif not in_q and (ch == ";" or line.startswith("//", i)):
            return line[:i]
    return line


def parse(path):
    """Yield (kind, key, value, depth, top_header) for every key=value line."""
    depth = 0
    top = None
    for line in read_text(path).splitlines():
        line = strip_comment(line)
        s = line.strip()
        if not s:
            continue
        m = HEADER.match(s)
        if m and depth == 0:
            top = m.group(1)
        kv = KV.match(s) if not s.startswith("[") else None
        if kv:
            yield kv.group(1).lower(), kv.group(2), depth, top
        depth += s.count("{") - s.count("}")
        depth = max(depth, 0)


def split_ids(value):
    value = value.split('"')[0] if not value.startswith('"') else value.strip('"')
    return [t.strip().lower() for t in value.split(",") if t.strip()]


def scan(tree):
    """Return defs, toplevel defs, refs, loc refs, loc keys, path refs."""
    defs = set()
    top_defs = defaultdict(set)          # (header, id) -> {rel}
    refs = defaultdict(set)              # rel -> {(key, token)}
    loc_refs = defaultdict(set)          # rel -> {key}
    loc_keys = set()
    path_refs = defaultdict(set)         # rel -> {(key, value)}
    for rel, full in tree.items():
        if not rel.endswith(".tgi"):
            continue
        is_loc = rel.startswith("localization/")
        for key, value, depth, top in parse(full):
            if is_loc:
                loc_keys.add(key.split("|")[0])
            if key == "ids":
                for tok in split_ids(value):
                    defs.add(tok)
                    if depth <= 1 and top:
                        top_defs[(top.lower(), tok)].add(rel)
            elif key.endswith("_ids"):
                for tok in split_ids(value):
                    refs[rel].add((key, tok))
            elif key in PATH_KEYS and value and not value.startswith('"'):
                path_refs[rel].add((key, value.split()[0]))
            for m in LOC_REF.finditer(value):
                loc_refs[rel].add(m.group(1).lower())
    return defs, top_defs, refs, loc_refs, loc_keys, path_refs


def resolve_path(tree_paths, prefixes, rel, key, value):
    v = value.replace("\\", "/").lower()
    cands = [v.lstrip("/")] if v.startswith("/") else \
        [os.path.dirname(rel) + "/" + v, v]
    for c in cands:
        c = os.path.normpath(c).replace("\\", "/")
        if key == "resource_prefix":
            if c in prefixes:
                return True
        elif c in tree_paths:
            return True
    return False


def build_prefixes(tree_paths):
    out = set()
    for p in tree_paths:
        stem = p.rsplit(".", 1)[0]
        for i in range(len(stem), 0, -1):
            out.add(stem[:i])
    return out


def unresolved(rels, defs, refs, loc_refs, loc_keys, path_refs, tree_paths, prefixes):
    bad_ids, bad_loc, bad_path = defaultdict(set), defaultdict(set), defaultdict(set)
    for rel in rels:
        for key, tok in refs.get(rel, ()):
            if tok not in defs and tok not in ("none", "null", ""):
                bad_ids[rel].add((key, tok))
        for k in loc_refs.get(rel, ()):
            if k not in loc_keys:
                bad_loc[rel].add(k)
        for key, val in path_refs.get(rel, ()):
            if not resolve_path(tree_paths, prefixes, rel, key, val):
                bad_path[rel].add((key, val))
    return bad_ids, bad_loc, bad_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vanilla", required=True, help="pristine Data.rwd extract (Data (Backup))")
    ap.add_argument("--mod", default=os.path.join(os.path.dirname(__file__), "..", "Data"))
    args = ap.parse_args()

    vanilla = walk(args.vanilla)
    mod = walk(args.mod)
    merged = dict(vanilla)
    merged.update(mod)

    # baseline: vanilla alone
    vd, _, vr, vl, vk, vp = scan(vanilla)
    vpaths = set(vanilla)
    b_ids, b_loc, b_path = unresolved(vanilla, vd, vr, vl, vk, vp, vpaths, build_prefixes(vpaths))
    noise_ids = {t for s in b_ids.values() for _, t in s}
    noise_loc = {k for s in b_loc.values() for k in s}
    noise_path = {v.lower() for s in b_path.values() for _, v in s}

    md, mtop, mr, ml, mk, mp = scan(merged)
    mpaths = set(merged)
    u_ids, u_loc, u_path = unresolved(mod, md, mr, ml, mk, mp, mpaths, build_prefixes(mpaths))

    problems = 0
    print(f"vanilla files {len(vanilla)}, mod files {len(mod)}, merged ids {len(md)}, loc keys {len(mk)}")
    print(f"baseline noise: {len(noise_ids)} id tokens, {len(noise_loc)} loc keys, {len(noise_path)} paths\n")
    for title, table, noise, fmt in (
        ("Unresolved *_ids", u_ids, noise_ids, lambda x: f"{x[0]} = {x[1]}"),
        ("Missing loc keys", u_loc, noise_loc, lambda x: f"#{x}"),
        ("Missing resource paths", u_path, noise_path, lambda x: f"{x[0]} = {x[1]}"),
    ):
        rows = []
        for rel in sorted(table):
            for item in sorted(table[rel]):
                tok = item[1] if isinstance(item, tuple) else item
                if tok.lower() in noise:
                    continue
                rows.append(f"  {rel}: {fmt(item)}")
        print(f"{title}: {len(rows)}")
        print("\n".join(rows) + ("\n" if rows else ""))
        problems += len(rows)

    dupes = []
    for (hdr, tok), rels in sorted(mtop.items()):
        if len(rels) > 1 and any(r in mod for r in rels):
            dupes.append(f"  [{hdr}] {tok}: " + ", ".join(sorted(rels)))
    print(f"Duplicate top-level IDS touching mod files: {len(dupes)}")
    print("\n".join(dupes))
    problems += len(dupes)

    print(f"\nTOTAL Battleborn problems: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
