"""Publication audit: proves the public sources carry no copied game text or files.

Checks patches/ and original/ (not private/) against the player's Data.rwd:
  * any file byte-identical to a game file
  * in our text (patch '+' lines and original text files), any run of RUN or more
    consecutive non-trivial lines that also appears contiguously in one game file,
    compared with indentation and line endings ignored. Shorter coincidences are
    individual settings (e.g. "[View]" / "health = 220") rather than copied text.

    py -3 tools/audit_public.py [--data-rwd "<game>/Data.rwd"]
Exit code 1 if anything is found.
"""

import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb       # noqa: E402
import bbpatch  # noqa: E402
import rwd      # noqa: E402

RUN = 4


def norm(body):
    return body.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-rwd")
    args = ap.parse_args()
    path = args.data_rwd or os.path.join(bb.find_game() or "", "Data.rwd")
    arc = rwd.Archive(path)

    game_hashes = {}
    where = {}          # normalized line -> [(file index, line index)]
    files = []
    for e in arc.entries:
        data = arc.read(e)
        game_hashes[hashlib.sha256(data).digest()] = e.name
        if os.path.splitext(e.name)[1].lower() not in (".tgi", ".txt"):
            continue
        lines = [norm(b) for b in bbpatch.split(data)[1]]
        fi = len(files)
        files.append(lines)
        for li, ln in enumerate(lines):
            if bbpatch.is_substantive(ln):
                lst = where.setdefault(ln, [])
                if len(lst) < 5000:
                    lst.append((fi, li))

    def copied_runs(lines):
        """Runs of >= RUN of our consecutive lines found contiguously in a single game file."""
        out = []
        i = 0
        while i < len(lines):
            best = 0
            for fi, li in where.get(lines[i], ()) if bbpatch.is_substantive(lines[i]) else ():
                src = files[fi]
                n = 0
                while i + n < len(lines) and li + n < len(src) and src[li + n] == lines[i + n]:
                    n += 1
                best = max(best, n)
            subst = sum(1 for x in lines[i:i + best] if bbpatch.is_substantive(x))
            if subst >= RUN:
                out.append((i, best))
                i += best
            else:
                i += 1
        return out

    problems = []
    repo = bb.REPO
    for top in ("patches", "original"):
        for rel, full in bb.walk(os.path.join(repo, top)).items():
            data = open(full, "rb").read()
            if hashlib.sha256(data).digest() in game_hashes:
                problems.append(f"{top}/{rel}: identical to game file {game_hashes[hashlib.sha256(data).digest()]}")
                continue
            if rel.endswith(".bbpatch"):
                _, hunks = bbpatch.parse(data.decode("utf-8"))
                for h in hunks:
                    ours = [norm(x[1:].encode("utf-8")) for x in h["body"] if x.startswith("+")]
                    for start, n in copied_runs(ours):
                        problems.append(f"{top}/{rel}: {n} consecutive lines match game text near hunk @{h['start']}")
            elif os.path.splitext(rel)[1].lower() in (".tgi", ".txt"):
                ours = [norm(b) for b in bbpatch.split(data)[1]]
                for start, n in copied_runs(ours):
                    problems.append(f"{top}/{rel}: {n} consecutive lines match game text at line {start + 1}")
    for p in problems:
        print(p)
    print(f"audit: {len(problems)} finding(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
