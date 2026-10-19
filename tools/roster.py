"""Battleborn roster: which units wear custom Battleborn art, and who leads each company.

Reads the built mod over the game's Data.rwd, so it always describes what ships:
  - every company unit (front, flank, support, captain) with its skin and icon, marked
    Battleborn art (a texture this mod ships), the unit's own stock art, or borrowed stock art
    (a Battleborn unit still wearing another unit's or a hero's art);
  - every company type with its front unit and default captain or sergeant, and whether the
    leader wears the same model as the troops.
bb.py build rewrites ROSTER.md from this, so the list cannot drift from the data.

    py -3 tools/roster.py [--game <Kohan II folder>]    rebuild the mod in memory and write ROSTER.md
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_fields as tf  # noqa: E402

ROLES = ("front", "flank", "support", "captain")
LOC = re.compile(r'^\s*([A-Za-z_]\w*)\s*=\s*"([^"]*)"')
ORDER = ("Human", "Drauga", "Gauri", "Haroun", "Shadow", "Undead",
         "Royalist", "Nationalist", "Council", "Ceyah", "Fallen")


def _assigns(node):
    out = {}
    for s in node.items:
        a = tf.ASSIGN.match(s)
        if a and a.group(1).lower() not in out:
            out[a.group(1).lower()] = tf._value(s)
    return out


def _word(node):
    words = node.header.split()
    return words[0].lower() if words else ""


def _resolve(folder, path):
    """Data path of a resource named in a unit file: '/Units/..' is absolute, anything else is
    relative to the unit file's folder."""
    path = path.replace("\\", "/")
    return path.lstrip("/") if path.startswith("/") else f"{folder}/{path}"


def _strings(trees_text):
    names = {}
    for data in trees_text:
        for line in tf._text(data).splitlines():
            m = LOC.match(line)
            if m:
                names[m.group(1).lower()] = m.group(2)
    return names


def collect(vanilla, mod, paths=()):
    """vanilla, mod: {data path: bytes}; paths: every data path in the game. -> (units {ids: dict}, companies [dict])."""
    files = {n.lower(): (n, d) for n, d in vanilla.items()}
    for n, d in mod.items():
        files[n.lower()] = (n, d)
    shipped = {n.lower() for n in mod if not n.lower().endswith(".tgi")}
    exists = shipped | {p.lower() for p in paths}
    loc = _strings(d for k, (n, d) in files.items()
                   if k.startswith("localization/") and "strings_data" in k and k.endswith(".tgi"))
    units, companies = {}, []
    for key, (name, data) in sorted(files.items()):
        if not (key.startswith("units/") and key.endswith(".tgi")):
            continue
        folder = name.rsplit("/", 1)[0]
        group = name.split("/")[1]
        for actor in tf.parse(data).children:
            word, a = _word(actor), _assigns(actor)
            ids = a.get("ids", "").lower()
            if not ids:
                continue
            nodes = list(tf.walk(actor))
            if word == "unit":
                view = {}
                for n in [actor] + nodes:
                    if _word(n) in ("view", "aspectnormal", "unit"):
                        for k, v in _assigns(n).items():
                            view.setdefault(k, v)
                props = {_assigns(n).get("property_ids", "").lower() for n in nodes if _word(n) == "property"}
                prefix = view.get("resource_prefix", "")
                skin = view.get("skin", "%sbase.dds")
                skin_path = _resolve(folder, skin.replace("%s", prefix)) if prefix or "%s" not in skin else ""
                icon = view.get("icon", "")
                if not icon and prefix and _resolve(folder, prefix + "Icon.tga").lower() in exists:
                    icon = prefix + "Icon.tga"          # the model's own icon when the unit names none
                units[ids] = {
                    "ids": ids, "file": name, "group": group,
                    "name": loc.get(a.get("name", "").lstrip("#").lower(), a.get("name", "")),
                    "roles": [r for r in ROLES if r in props],
                    "model": _resolve(folder, prefix).rsplit("/", 1)[-1].lower() if prefix else "",
                    "prefix": _resolve(folder, prefix).lower() if prefix else "",
                    "skin": skin_path, "skin_custom": skin_path.lower() in shipped,
                    "icon": _resolve(folder, icon) if icon else "",
                    "icon_custom": bool(icon) and _resolve(folder, icon).lower() in shipped,
                    "battleborn": ids.startswith("bb_") or "/_bb_" in key,
                }
            elif word == "thing" and (tf.template_of(actor.header) or "").endswith("company"):
                slots = [_assigns(n).get("element_ids", "null").lower() for n in nodes if _word(n) == "slot"]
                layout = next((_assigns(n)["layout_ids"] for n in [actor] + nodes
                               if "layout_ids" in _assigns(n)), "")
                companies.append({"ids": ids, "file": name, "group": group, "slots": slots, "layout": layout,
                                  "name": loc.get(a.get("name", "").lstrip("#").lower(), a.get("name", ""))})
    return units, companies


def _art(u, kind):
    path, custom = u[kind], u[kind + "_custom"]
    if not path:
        return "none"
    if custom:
        return "**Battleborn**"
    return "borrowed: " + path.rsplit("/", 1)[-1] if u["battleborn"] else "stock"


def report(units, companies):
    def group_key(g):
        return (ORDER.index(g) if g in ORDER else len(ORDER), g)

    used = {s for c in companies for s in c["slots"]}
    shown = [u for u in units.values() if u["roles"] and u["group"] in ORDER and (u["ids"] in used or u["battleborn"])]
    custom = sum(u["skin_custom"] for u in shown)
    bb_units = [u for u in shown if u["battleborn"]]
    out = ["# Battleborn roster", "",
           "Written by `tools/roster.py` on every `bb.py build`; do not edit by hand.", "",
           "## Skins", "",
           f"{len(shown)} company units, {custom} on Battleborn skins. Of the {len(bb_units)} units Battleborn "
           f"adds, {sum(not u['skin_custom'] for u in bb_units)} still wear stock art. "
           "**Battleborn** = a texture this mod ships; stock = the unit's own game art; "
           "borrowed = another unit's or a hero's game art.", ""]
    for g in sorted({u["group"] for u in shown}, key=group_key):
        out += [f"### {g}", "", "| Unit | IDS | Slots | Skin | Icon |", "|---|---|---|---|---|"]
        for u in sorted((u for u in shown if u["group"] == g), key=lambda u: (not u["battleborn"], u["ids"])):
            out.append(f"| {u['name']} | `{u['ids']}` | {', '.join(u['roles'])} | {_art(u, 'skin')} | {_art(u, 'icon')} |")
        out.append("")
    out += ["## Sergeants and captains", "",
            "Each company type's front unit and the sergeant or captain it starts with (the player can pick "
            "another in the company editor). Same model = the leader wears the troops' model, as the Infantry "
            "Sergeant (Pikeman model) leading halberdiers.", ""]
    for g in sorted({c["group"] for c in companies if c["group"] in ORDER}, key=group_key):
        rows = []
        for c in sorted((c for c in companies if c["group"] == g), key=lambda c: c["ids"]):
            front = units.get(c["slots"][0]) if c["slots"] else None
            lead = next((units[s] for s in reversed(c["slots"]) if s in units and "captain" in units[s]["roles"]), None)
            if not front or not lead or "summoned" in c["layout"]:
                continue
            same = "yes" if front["model"] and front["model"] == lead["model"] else "no"
            rows.append(f"| {c['name']} | {front['name']} | {lead['name']} (`{lead['ids']}`) | "
                        f"{lead['model'] or '?'} | {same} |")
        if rows:
            out += [f"### {g}", "", "| Company | Front unit | Sergeant or captain | Its model | Same model |",
                    "|---|---|---|---|---|"] + rows + [""]
    return "\n".join(out).rstrip() + "\n"


def write(game, files):
    """bb.py build: rewrite ROSTER.md from the built files. -> True when it changed."""
    import bb
    vanilla = {e.name: game.arc.read(e) for e in game.arc.entries
               if e.name.lower().endswith(".tgi") and e.name.lower().startswith(("units/", "localization/"))}
    text = report(*collect(vanilla, dict(files), (e.name for e in game.arc.entries)))
    path = os.path.join(bb.REPO, "ROSTER.md")
    old = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
    if old != text:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    return old != text


def main():
    import argparse
    import bb
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--game")
    args = ap.parse_args()
    game = bb.Game(bb.game_dir(args))
    changed = write(game, bb.produce(game))
    print("ROSTER.md " + ("updated" if changed else "unchanged"))


if __name__ == "__main__":
    main()
