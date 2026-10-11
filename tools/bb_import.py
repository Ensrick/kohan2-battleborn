"""One-time (re-runnable) conversion of a full-file override tree into Battleborn sources:

    patches/<path>.bbpatch   game file + our changes (or a new file assembled from game blocks)
    original/<path>          files that are entirely ours (no reused game blocks)

Every result is rebuilt from the player's Data.rwd and compared byte-for-byte with the input.

    py -3 tools/bb_import.py --data-rwd "<game>/Data.rwd" --src Data --out .
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bbdelta  # noqa: E402
import bbpatch  # noqa: E402
import rwd      # noqa: E402

TEXT_EXT = {".tgi", ".txt"}
DERIVE_MIN_SIMILARITY = 0.25


def walk(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            full = os.path.join(dp, f)
            out[os.path.relpath(full, root).replace(os.sep, "/")] = full
    return out


def substantive_set(data):
    return {b.strip() for b in bbpatch.split(data)[1] if bbpatch.is_substantive(b)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-rwd", required=True)
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", default=None)
    ap.add_argument("--art-bases", default=None,
                    help="TSV of <our art path> TAB <game texture it was painted over>; unlisted art is treated as original")
    args = ap.parse_args()

    arc = rwd.Archive(args.data_rwd)
    game = {e.name.lower(): e for e in arc.entries}
    canon = {e.name.lower(): e.name for e in arc.entries}

    def get_file(name):
        e = game.get(name.lower())
        return arc.read(e) if e else None

    print("indexing game text files...")
    index = bbpatch.RefIndex()
    sets = {}
    for e in arc.entries:
        if os.path.splitext(e.name)[1].lower() in TEXT_EXT:
            data = arc.read(e)
            index.add(e.name, data)
            sets[e.name] = substantive_set(data)

    game_lines = set()
    for st in sets.values():
        game_lines |= st
    art_bases = {}
    if args.art_bases:
        for line in open(args.art_bases, encoding="utf-8"):
            if line.strip():
                ours, base_path = line.rstrip("\n").split("\t")
                art_bases[ours.lower()] = base_path
    src = walk(args.src)
    report = []
    ok = True
    for rel in sorted(src, key=str.lower):
        data = open(src[rel], "rb").read()
        ext = os.path.splitext(rel)[1].lower()
        key = rel.lower()
        if ext not in TEXT_EXT:
            base_name = art_bases.get(key)
            if base_name is None:
                dst = os.path.join(args.out, "original", *rel.split("/"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with open(dst, "wb") as f:
                    f.write(data)
                report.append(("original", rel, "", "our own art"))
                continue
            blob = bbdelta.make(canon.get(base_name.lower(), base_name), get_file(base_name), data)
            if bbdelta.apply(blob, get_file, rel) != data:
                ok = False
                report.append(("MISMATCH", rel, base_name, "delta"))
                continue
            dst = os.path.join(args.out, "patches", *rel.split("/")) + ".bbdelta"
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(blob)
            report.append(("art-delta", rel, base_name, f"{len(blob)} bytes"))
            continue
        if key in game:
            base_name = canon[key]
            kind = "override"
        else:
            mine = substantive_set(data)
            best, score = None, 0.0
            for name, s in sets.items():
                inter = len(mine & s)
                if not inter:
                    continue
                j = inter / len(mine | s)
                if j > score:
                    best, score = name, j
            base_name = best if score >= DERIVE_MIN_SIMILARITY else None
            kind = "derived" if base_name else "new"
        base = get_file(base_name) if base_name else None
        patch = bbpatch.make(base_name, base, data, index)
        meta, hunks = bbpatch.parse(patch)
        has_refs = any(item.startswith("=") for h in hunks for item in h["body"])
        if kind == "new" and not has_refs:
            dst = os.path.join(args.out, "original", *rel.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(data)
            report.append(("original", rel, "", "no game text"))
            continue
        rebuilt = bbpatch.apply(patch, get_file, rel)
        if rebuilt != data:
            ok = False
            report.append(("MISMATCH", rel, base_name or "", ""))
            continue
        ours = [item[1:] for h in hunks for item in h["body"] if item.startswith("+")]
        refd = sum(1 for h in hunks for item in h["body"] if item.startswith("="))
        echo = [t for t in ours if len(t.strip()) > 3 and t.strip().encode() in game_lines]
        dst = os.path.join(args.out, "patches", *rel.split("/")) + ".bbpatch"
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write(patch)
        report.append((kind, rel, base_name or "(none)", f"{len(hunks)} hunks, {len(ours)} our lines ({len(echo)} also in game files), {refd} refs"))

    width = max(len(r[1]) for r in report)
    lines = [f"{r[0]:9} {r[1]:{width}}  {r[2]}  {r[3]}" for r in report]
    print("\n".join(lines))
    if args.report:
        with open(args.report, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines) + "\n")
    print("ALL FILES REBUILD BYTE-IDENTICAL" if ok else "SOME FILES FAILED TO REBUILD")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
