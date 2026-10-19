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
PARENT_ARG = re.compile(r"\b(?:template|inherit)\s*=\s*([\w]+)", re.I)   # [template X inherit=Y]


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
        if s.startswith("{") and flat is not None:
            # a brace after the node's first lines still opens that node ([Animation] IDS = die1 { ... })
            stack.append(flat)
            flat = None
            s = s[1:].strip()
            if not s:
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


def _value(rhs):
    v = rhs.split("=", 1)[1].strip()
    return v.strip('"') if v.startswith('"') else v.split()[0] if v else ""


def collect_templates(trees):
    """name -> (parent, [(field, has_value, value)], node) from every
    [Template Name Template=Parent] / [template Name inherit=Parent]."""
    out = {}
    for tree in trees:
        for node in tree.children:
            words = node.header.split()
            if len(words) < 2 or words[0].lower() != "template":
                continue
            name = words[1].lower()
            m = PARENT_ARG.search(" ".join(words[2:]))
            parent = m.group(1).lower() if m else None
            fields = []
            for s in node.items:
                d = DECL.match(s)
                if d and d.group(1).lower() not in ("list",):
                    fields.append((d.group(2).lower(), d.group(3) is not None,
                                   _value(d.group(3)) if d.group(3) else None))
                    continue
                a = ASSIGN.match(s)
                if a:
                    fields.append((a.group(1).lower(), True, _value(s)))
            out[name] = (parent, fields, node)
    return out


def chain(templates, name):
    """[name, parent, grandparent, ...] as far as the templates are known."""
    out, seen = [], set()
    while name in templates and name not in seen:
        seen.add(name)
        out.append(name)
        name = templates[name][0]
    return out


def values(templates, name):
    """field -> value a node of this template gets when it does not set the field."""
    state = {}
    for t in reversed(chain(templates, name)):
        for field, has_value, value in templates[t][1]:
            state[field] = value if has_value else None
    return state


def required(templates, name, _cache={}):
    key = (id(templates), name)
    if key in _cache:
        return _cache[key]
    state = {}
    for t in reversed(chain(templates, name)):
        for field, has_value, _ in templates[t][1]:
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


def _def_name(node):
    words = [w for w in node.header.split() if "=" not in w]
    if words and words[0].lower() == "list":
        words = words[1:]
    return words[0].lower() if words else ""


def _parent_of_def(node):
    """Template a definition node builds on: [Template X Template=Y] / [template X inherit=Y] /
    [list Sub Template=Y] / [Sub Template=Y]."""
    words = node.header.split()
    rest = " ".join(words[2:]) if words and words[0].lower() == "template" else node.header
    m = PARENT_ARG.search(rest)
    return m.group(1).lower() if m else None


def _expand(templates, defs):
    out, seen, stack = [], set(), list(defs)
    while stack:
        d = stack.pop()
        if id(d) in seen:
            continue
        seen.add(id(d))
        out.append(d)
        t = _parent_of_def(d)
        if t in templates:
            stack.append(templates[t][2])
    return out


def _known_fields(defs, _cache={}):
    key = tuple(sorted(id(d) for d in defs))
    if key not in _cache:
        known = set()
        for d in defs:
            for s in d.items:
                m = DECL.match(s) or ASSIGN.match(s)
                if m:
                    known.add((m.group(2) if DECL.match(s) else m.group(1)).split("|")[0].lower())
        _cache[key] = known
    return _cache[key]


def unknown_fields(templates, files):
    """[(file, line, node path, field)] for fields that no definition of the node declares
    (the engine: "Field not found in template. Expression: '<field>'"). A node's
    definitions are its own Template= chain plus the sub-node of that name declared by its
    parent's definitions; nodes whose definition cannot be found are skipped."""
    out = []

    def visit(name, node, parent_defs, path):
        defs = []
        t = template_of(node.header)
        if t in templates:
            defs.append(templates[t][2])
        nm = _def_name(node)
        if nm in templates:             # [BodyComponent] uses [template BodyComponent]
            defs.append(templates[nm][2])
        for d in parent_defs:
            defs.extend(c for c in d.children if _def_name(c) == nm)
        defs = _expand(templates, defs)
        if not defs:
            return
        known = _known_fields(defs)
        here = f"{path}/{nm}" if path else nm
        for s in node.items:
            a = ASSIGN.match(s)
            if a and a.group(1).split("|")[0].lower() not in known:
                out.append((name, node.line, here, a.group(1)))
        for c in node.children:
            visit(name, c, defs, here)

    for name, tree in files.items():
        if name.lower().startswith("templates/"):
            continue
        for node in tree.children:
            if node.header.split()[0].lower() == "template":
                continue
            visit(name, node, [], "")
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
    vnoise = {(p, f.lower()) for _, _, p, f in unknown_fields(collect_templates(vanilla.values()), vanilla)}
    for name, line, p, f in unknown_fields(templates, {n: merged[n.lower()] for n in mod}):
        if (p, f.lower()) not in vnoise:
            problems.append(f"{name}({line}): '{f}' is not a field of {p} (a brace-less [node] owns every "
                            f"line up to the next [node], so a field placed after one lands inside it)")
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
