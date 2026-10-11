"""Template-field check: every node must give the fields its template leaves without a value.

A template declares fields as "<type> <name> [= default]"; a later template can declare a
field again without a default, which makes it required (template_animation.tgi:
"[Template AbilityAnimation Template=Animation] { type = ABILITY / fixed key_ratio }").
A node that uses such a template and does not set the field stops the game at startup:
log-247, "Field 'key_ratio' missing from node using strict template:
Units/Undead/_BB_Captain_Necromancer.tgi/Unit/CharacterComponent/Animation".

Vanilla's own misses are measured first and ignored (not every template is strict), so
only fields the retail data always sets are reported.

    py -3 tools/template_fields.py [<mod.rwd>] [--game <Kohan II folder>]
"""

import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate  # noqa: E402

HEADER = re.compile(r"^\[\s*([^\]]*?)\s*\]\s*(\{)?\s*$")
DECL = re.compile(r"^([A-Za-z_]\w*)\s+([A-Za-z_][\w|]*)\s*(=.*)?$")
ASSIGN = re.compile(r"^([A-Za-z_][\w|]*)\s*=")
TEMPLATE_ARG = re.compile(r"\btemplate\s*=\s*([\w]+)", re.I)


BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def _text(data):
    if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
        text = data.decode("utf-16")
    else:
        text = (data[3:] if data.startswith(b"\xef\xbb\xbf") else data).decode("latin-1")
    # /* ... */ blocks hold banners and usage examples ("[Animation Template=AbilityAnimation]")
    return BLOCK_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)


class Node:
    __slots__ = ("header", "line", "items", "children", "parent")

    def __init__(self, header, line, parent):
        self.header, self.line, self.items, self.children, self.parent = header, line, [], [], parent


def parse(data):
    """Tree of nodes. A header followed by '{' owns the braced block; a header without one
    owns the key lines after it up to the next header or closing brace."""
    root = Node("", 0, None)
    stack = [root]          # braced scopes
    flat = None             # current brace-less node in the innermost scope
    pending = None          # header waiting to see whether '{' follows
    for no, raw in enumerate(_text(data).splitlines(), 1):
        s = validate.strip_comment(raw).strip()
        if not s:
            continue
        if pending is not None:
            node, opened = pending
            pending = None
            if s.startswith("{"):
                stack.append(node)
                flat = None
                s = s[1:].strip()
                if not s:
                    continue
            else:
                flat = node
        m = HEADER.match(s)
        if m:
            parent = stack[-1]
            node = Node(m.group(1), no, parent)
            parent.children.append(node)
            if m.group(2):
                stack.append(node)
                flat = None
            else:
                pending = (node, False)
            continue
        if s.startswith("}"):
            if len(stack) > 1:
                stack.pop()
            flat = None
            continue
        (flat or stack[-1]).items.append(s)
    return root


def walk(node):
    for c in node.children:
        yield c
        yield from walk(c)


def template_of(header):
    m = TEMPLATE_ARG.search(header)
    return m.group(1).lower() if m else None


def collect_templates(trees):
    """name -> (parent, [(field, has_value)]) from every [Template Name Template=Parent]."""
    out = {}
    for tree in trees:
        for node in tree.children:
            words = node.header.split()
            if len(words) < 2 or words[0].lower() != "template":
                continue
            name = words[1].lower()
            parent = template_of(" ".join(words[2:]))
            fields = []
            for s in node.items:
                d = DECL.match(s)
                if d and d.group(1).lower() not in ("list",):
                    fields.append((d.group(2).lower(), d.group(3) is not None))
                    continue
                a = ASSIGN.match(s)
                if a:
                    fields.append((a.group(1).lower(), True))
            out[name] = (parent, fields)
    return out


def required(templates, name, _cache={}):
    key = (id(templates), name)
    if key in _cache:
        return _cache[key]
    chain, seen = [], set()
    while name in templates and name not in seen:
        seen.add(name)
        chain.append(name)
        name = templates[name][0]
    state = {}
    for t in reversed(chain):
        for field, has_value in templates[t][1]:
            state[field] = has_value
    _cache[key] = {f for f, v in state.items() if not v}
    return _cache[key]


def misses(templates, files):
    """[(file, line, template, field)] for nodes that leave a required field unset."""
    out = []
    for name, tree in files.items():
        if name.lower().startswith("templates/"):
            continue
        for node in walk(tree):
            if node.header.split()[0].lower() == "template":
                continue
            t = template_of(node.header)
            if t is None or t not in templates:
                continue
            given = {ASSIGN.match(s).group(1).lower() for s in node.items if ASSIGN.match(s)}
            for field in sorted(required(templates, t) - given):
                out.append((name, node.line, t, field))
    return out


def _trees(entries):
    return {name: parse(data) for name, data in entries if name.lower().endswith(".tgi")}


def check(game_arc, mod_files):
    """Problems (strings) for mod_files [(name, bytes)] layered over the game's Data.rwd."""
    vanilla = _trees((e.name, game_arc.read(e)) for e in game_arc.entries if e.name.lower().endswith(".tgi"))
    mod = _trees(mod_files)
    merged = {n.lower(): t for n, t in vanilla.items()}
    names = {n.lower(): n for n in vanilla}
    for n, t in mod.items():
        merged[n.lower()] = t
        names[n.lower()] = n
    noise = {(t, f) for _, _, t, f in misses(collect_templates(vanilla.values()), vanilla)}
    templates = collect_templates(merged.values())
    problems = []
    for name, line, t, f in misses(templates, {n: merged[n.lower()] for n in mod}):
        if (t, f) not in noise:
            problems.append(f"{name}({line}): [{t}] node does not set '{f}', which that template requires")
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
    print(f"template fields: {len(problems)} problem(s) in {args.archive}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
