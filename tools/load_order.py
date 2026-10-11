"""Load-order check: a mod file must not use an ID that only a later-loaded file defines,
where the game resolves that kind of reference while the file loads.

k2.exe loads TGI files in the order index_k2.lst (and the .lst files it includes) lists
them. A wildcard line such as Units/Human/*.tgi takes every matching file from all depots,
and _BB_ files load before the stock files of their folder: log-246 died on
_BB_Front_Ranger.tgi "Could not find vfx data: ranger_sword_effect", an effect defined in
ranger.tgi, and warned "Object bb_captain_bowman could not find portrait
aethan_farhyd_portrait" (defined in Units/Nationalist, which loads after Units/Human).
The exact sort rule is not pinned down, so both lower- and upper-case name orders are run.

Which references are resolved at load time is taken from the retail data itself: a
forward reference is reported only when vanilla never makes one of that kind (same
*_ids key from the same top-level folder). Vanilla forward-references effects and
portraits only from Templates/ and Audio/Speech/, never from unit files.

    py -3 tools/load_order.py [<mod.rwd>] [--game <Kohan II folder>]
"""

import fnmatch
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate  # noqa: E402

ORDERS = (("lower-case", str.lower), ("upper-case", str.upper))


def _text(data):
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        return data.decode("utf-16")
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    return data.decode("latin-1")


def _scan(data):
    """(ids defined, [(key, id) referenced]) for one TGI file."""
    defs, refs = set(), []
    for line in _text(data).splitlines():
        s = validate.strip_comment(line).strip()
        if not s or s.startswith("["):
            continue
        kv = validate.KV.match(s)
        if not kv:
            continue
        key = kv.group(1).lower()
        if key == "ids":
            defs.update(validate.split_ids(kv.group(2)))
        elif key.endswith("_ids"):
            refs.extend((key, t) for t in validate.split_ids(kv.group(2)))
    return defs, refs


class _Tree:
    def __init__(self, files):
        self.files = files                      # lower name -> (name, bytes)
        self.by_dir = defaultdict(list)
        for low, (name, _) in files.items():
            if low.endswith(".tgi"):
                self.by_dir[os.path.dirname(low)].append(low)
        self._info = {}

    def info(self, low):
        if low not in self._info:
            self._info[low] = _scan(self.files[low][1])
        return self._info[low]

    def order(self, keyf):
        seen, out = set(), []

        def run(lst, depth=0):
            entry = self.files.get(lst.lower())
            if entry is None or depth > 8:
                return
            for line in _text(entry[1]).splitlines():
                s = line.split(";")[0].strip()
                if not s:
                    continue
                if s.lower().endswith(".lst"):
                    run(s, depth + 1)
                    continue
                pat = s.replace("\\", "/").lower()
                hits = [n for n in self.by_dir.get(os.path.dirname(pat), ()) if fnmatch.fnmatchcase(n, pat)]
                for n in sorted(hits, key=lambda n: keyf(self.files[n][0])):
                    if n not in seen:
                        seen.add(n)
                        out.append(n)
        run("index_k2.lst")
        return out

    def forward(self, seq):
        """[(file, key, id, defining file)] for ids defined only in later files."""
        pos = {n: i for i, n in enumerate(seq)}
        first = {}
        for n in seq:
            for t in self.info(n)[0]:
                first.setdefault(t, pos[n])
        out = []
        for n in seq:
            defs, refs = self.info(n)
            for key, tok in refs:
                if tok in ("none", "null", "") or tok in defs or tok not in first:
                    continue
                if first[tok] > pos[n]:
                    out.append((n, key, tok, seq[first[tok]]))
        return out


def _texts(entries):
    return {name.lower(): (name, data) for name, data in entries
            if name.lower().endswith((".tgi", ".lst"))}


def check(game_arc, mod_files):
    """Problems (strings) for mod_files [(name, bytes)] layered over the game's Data.rwd."""
    vanilla = _texts((e.name, game_arc.read(e)) for e in game_arc.entries
                     if e.name.lower().endswith((".tgi", ".lst")))
    mod = _texts(mod_files)
    merged = dict(vanilla)
    merged.update(mod)
    vt, mt = _Tree(vanilla), _Tree(merged)
    problems = set()
    for label, keyf in ORDERS:
        lazy = {(n.split("/")[0], key) for n, key, _, _ in vt.forward(vt.order(keyf))}
        for n, key, tok, at in mt.forward(mt.order(keyf)):
            if n in mod and (n.split("/")[0], key) not in lazy:
                problems.add(f"{mod[n][0]}: {key} = {tok} is defined only in "
                             f"{merged[at][0]}, which loads later")
    return sorted(problems)


def main():
    import argparse
    import bb
    import rwd
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("archive", nargs="?", default=os.path.join(bb.REPO, "build", "public", bb.ARCHIVE))
    ap.add_argument("--game")
    args = ap.parse_args()
    game = bb.Game(bb.game_dir(args))
    arc = rwd.Archive(args.archive)
    problems = check(game.arc, [(e.name, arc.read(e)) for e in arc.entries])
    for p in problems:
        print("  " + p)
    print(f"load order: {len(problems)} problem(s) in {args.archive}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
