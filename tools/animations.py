"""Animation check: every animation an actor's abilities play must exist on that actor.

An [Ability] names the animations it plays (animation1..5) and the one the actor idles on
afterwards (idle_animation); the ability's template supplies them when the node does not
(K2SpellInstantLocal: animation1 = cast, idle_animation = idlecast). The actor must define
each as an [Animation] IDS in its own [CharacterComponent], or the game stops at startup:
log-248, "Unknown idle animation 'idlecast' loading actor 'bb_captain_council_swordsman'"
(engine also has "Unknown ability animation '%s' loading actor '%s'").

Vanilla is measured first; only kinds of miss it never has are reported.

    py -3 tools/animations.py [<mod.rwd>] [--game <Kohan II folder>]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_fields as tf  # noqa: E402

FIELDS = ("animation1", "animation2", "animation3", "animation4", "animation5", "idle_animation")


def _assigns(node):
    out = {}
    for s in node.items:
        a = tf.ASSIGN.match(s)
        if a:
            out[a.group(1).lower()] = tf._value(s)
    return out


def _first_word(node):
    words = node.header.split()
    return words[0].lower() if words else ""


def misses(templates, files):
    """[(file, line, actor, ability template, field, animation)]"""
    out = []
    for name, tree in files.items():
        if name.lower().startswith("templates/"):
            continue
        for actor in tree.children:
            if _first_word(actor) == "template":
                continue
            nodes = list(tf.walk(actor))
            anims = {_assigns(n).get("ids", "").lower() for n in nodes if _first_word(n) == "animation"}
            if not anims - {""}:
                continue                    # not a character (buildings, effects ...)
            actor_id = _assigns(actor).get("ids", "?")
            for n in nodes:
                if _first_word(n) != "ability":
                    continue
                t = tf.template_of(n.header)
                if t is None:
                    continue
                vals = tf.values(templates, t)
                vals.update(_assigns(n))
                for field in FIELDS:
                    v = (vals.get(field) or "").lower()
                    if v and v not in ("null", "none") and v not in anims:
                        out.append((name, n.line, actor_id, t, field, v))
    return out


def check(game_arc, mod_files):
    vanilla = tf._trees((e.name, game_arc.read(e)) for e in game_arc.entries if e.name.lower().endswith(".tgi"))
    mod = tf._trees(mod_files)
    merged = {n.lower(): t for n, t in vanilla.items()}
    for n, t in mod.items():
        merged[n.lower()] = t
    noise = {(t, f, v) for _, _, _, t, f, v in misses(tf.collect_templates(vanilla.values()), vanilla)}
    templates = tf.collect_templates(merged.values())
    problems = []
    for name, line, actor, t, f, v in misses(templates, {n: merged[n.lower()] for n in mod}):
        if (t, f, v) not in noise:
            problems.append(f"{name}({line}): actor {actor}: [{t}] {f} = {v}, but the actor has no '{v}' animation")
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
    print(f"animations: {len(problems)} problem(s) in {args.archive}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
