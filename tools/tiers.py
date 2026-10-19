"""Battleborn recruit tiers: which buildings and which town-center level each unit needs.

User design (2026-10-18/19): every unit needs a building, and the town center's level is the
tier. Human examples from the user: pikemen = blacksmith + village, swordsmen = blacksmith +
town, lancers = woodmill + village, bowmen = woodmill + town. The same rule is applied to every
race by role (cheapest melee / cheapest fast or ranged unit at village, the main melee and ranged
units at town, heavy cavalry, barracks units and siege monsters at city, supports with their
building at town). The three Council lines are race lines (Gauri cavalry, Haroun ranged, Human
melee: the Council races), so they need their race's buildings; Royalist, Nationalist and Ceyah
lines stay open to every race of the faction (base_ buildings; no town level, since the game has
no race-neutral town-center requirement that can be relied on).

A requirement on a center is met by that center and its upgrades (as the game's own settler
requirement, drauga_center_village, is met in towns and cities).

    py -3 tools/tiers.py apply    rewrite required_structures in work/ (vanilla files are copied in)
    py -3 tools/tiers.py check    report companies whose default units need more than their front unit
Run 'bb.py work' first and 'bb.py diff' afterwards.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb  # noqa: E402

REPO = bb.REPO
WORK = os.path.join(REPO, "work")


def need(race, *parts):
    """need('human', 'blacksmith', 'town') -> 'human_blacksmith,human_center_town'."""
    centers = {"village", "town", "city", "citadel"}
    return ",".join(f"{race}_center_{p}" if p in centers else f"{race}_{p}" for p in parts)


# unit IDS -> (file under Units/, required_structures)
TIERS = {}


def tier(path, ids, value):
    TIERS[ids] = (path, value)


# Human (the user's four examples, then the rest of the roster on the same rule)
H = "human"
tier("Human/pikeman.tgi", "pikeman", need(H, "blacksmith", "village"))
tier("Human/_BB_Captain_Pikeman.tgi", "bb_captain_pikeman", need(H, "blacksmith", "village"))      # Infantry Sergeant
tier("Human/_BB_Support_Pikeman.tgi", "bb_praetorian", need(H, "blacksmith", "village"))          # Praetorian: in the sheet's T1 Infantry Company
tier("Human/swordsman.tgi", "swordsman", need(H, "blacksmith", "town"))
tier("Human/_BB_Support_Swordsman.tgi", "bb_support_swordsman", need(H, "blacksmith", "town"))    # Myrmidon
tier("Human/_BB_Captain_Swordsman.tgi", "bb_captain_infantry", need(H, "blacksmith", "town"))     # Infantry Captain
tier("Human/lancer.tgi", "lancer", need(H, "woodmill", "village"))
tier("Human/_BB_Captain_Lancer.tgi", "bb_captain_lancer", need(H, "woodmill", "village"))         # Cavalry Sergeant
tier("Human/_BB_Support_Lancer.tgi", "bb_support_lancer", need(H, "woodmill", "town"))            # Lancer (T2)
tier("Human/bowman.tgi", "bowman", need(H, "woodmill", "town"))
tier("Human/_BB_Skirmisher.tgi", "bb_skirmisher", need(H, "woodmill", "town"))
tier("Human/_BB_Captain_Bowman.tgi", "bb_captain_bowman", need(H, "woodmill", "town"))            # Ranger Sergeant
tier("Human/_BB_Support_Bowman.tgi", "bb_support_bowman", need(H, "woodmill", "city"))            # Marksman (T4)
tier("Human/dragoon.tgi", "dragoon", need(H, "blacksmith", "barracks", "city"))                   # Cavalier
tier("Human/_BB_Support_Dragoon.tgi", "bb_support_dragoon", need(H, "blacksmith", "barracks", "city"))  # Cataphract
tier("Human/catapult.tgi", "catapult", need(H, "quarry", "barracks", "town"))
tier("Human/_BB_Support_Engineer.tgi", "bb_support_engineer", need(H, "quarry", "town"))          # Siege Expert
# unchanged on purpose: captain, ranger captain, pioneer and explorer (village), engineer
# (quarry), engineer sergeant (quarry + town), ranger / front ranger (woodmill + library +
# town), cleric (shrine + town), sorceress (library + town), warmage (mage college + city)

# Drauga: raider (infantry) and mauler (cavalry) are the village pair
D = "drauga"
tier("Drauga/raider.tgi", "raider", need(D, "blacksmith", "village"))
tier("Drauga/mauler.tgi", "mauler", need(D, "woodmill", "village"))
tier("Drauga/berserker.tgi", "berserker", need(D, "blacksmith", "town"))
tier("Drauga/impaler.tgi", "impaler", need(D, "woodmill", "town"))
tier("Drauga/beastrider.tgi", "beastrider", need(D, "blacksmith", "barracks", "city"))
tier("Drauga/warmonger.tgi", "warmonger", need(D, "barracks", "blacksmith", "town"))
tier("Drauga/elder.tgi", "elder", need(D, "shrine", "town"))

# Gauri: no cheap units, so anvil and spear are the village pair; hammer is heavy cavalry
G = "gauri"
tier("Gauri/anvil.tgi", "anvil", need(G, "blacksmith", "village"))
tier("Gauri/spear.tgi", "spear", need(G, "woodmill", "village"))
tier("Gauri/hammer.tgi", "hammer", need(G, "blacksmith", "barracks", "city"))
tier("Gauri/healer.tgi", "healer", need(G, "shrine", "town"))
tier("Gauri/warden.tgi", "warden", need(G, "library", "town"))
tier("Gauri/wrecker.tgi", "wrecker", need(G, "quarry", "barracks", "town"))
tier("Gauri/juggernaut.tgi", "juggernaut", need(G, "library", "blacksmith", "city"))
tier("Gauri/maelstrom.tgi", "maelstrom", need(G, "woodmill", "library", "city"))

# Haroun: mistrunner (infantry) and rainbringer (archer) are the village pair
R = "haroun"
tier("Haroun/mistrunner.tgi", "mistrunner", need(R, "blacksmith", "village"))
tier("Haroun/rainbringer.tgi", "rainbringer", need(R, "woodmill", "village"))
tier("Haroun/stonewalker.tgi", "stonewalker", need(R, "blacksmith", "town"))
tier("Haroun/windrider.tgi", "windrider", need(R, "woodmill", "barracks", "city"))
tier("Haroun/pathfinder.tgi", "pathfinder", need(R, "woodmill", "library", "town"))
tier("Haroun/moonwatcher.tgi", "moonwatcher", need(R, "shrine", "town"))
tier("Haroun/harvester.tgi", "harvester", need(R, "library", "town"))
tier("Haroun/hillstrider.tgi", "hillstrider", need(R, "barracks", "library", "city"))

# Shadow: shadeling (infantry) and fury (archer) are the village pair
S = "shadow"
tier("Shadow/shadeling.tgi", "shadeling", need(S, "blacksmith", "village"))
tier("Shadow/fury.tgi", "fury", need(S, "woodmill", "village"))
tier("Shadow/reaver.tgi", "reaver", need(S, "blacksmith", "town"))
tier("Shadow/beast.tgi", "beast", need(S, "barracks", "blacksmith", "city"))
tier("Shadow/leviathan.tgi", "leviathan", need(S, "manafocus", "barracks", "city"))
tier("Shadow/banshee.tgi", "banshee", need(S, "shrine", "town"))
tier("Shadow/fiend.tgi", "fiend", need(S, "manafocus", "town"))
tier("Shadow/warlock.tgi", "warlock", need(S, "shrine", "library", "town"))

# Undead: zombie (infantry) and bone archer are the village pair
U = "undead"
tier("Undead/zombie.tgi", "zombie", need(U, "blacksmith", "village"))
tier("Undead/bone_archer.tgi", "bonearcher", need(U, "woodmill", "village"))
tier("Undead/skeleton.tgi", "skeleton", need(U, "blacksmith", "town"))
tier("Undead/nightmare.tgi", "nightmare", need(U, "blacksmith", "barracks", "city"))
tier("Undead/lich.tgi", "lich", need(U, "shrine", "town"))
tier("Undead/revenant.tgi", "revenant", need(U, "library", "town"))
tier("Undead/_BB_Captain_Necromancer.tgi", "bb_captain_undead_necromancer", need(U, "shrine", "city"))

# Council race lines (the Council races: Gauri, Haroun, Human)
tier("Council/_BB_Front_Rune_Hammer.tgi", "bb_front_council_hammer", need(G, "blacksmith", "barracks", "city"))
tier("Council/_BB_Captain_Rune_Lord.tgi", "bb_captain_council_hammer", need(G, "blacksmith", "barracks", "city"))
tier("Council/_BB_Support_Arcane_Archer.tgi", "bb_support_council_ranger", need(R, "woodmill", "library", "city"))
tier("Council/_BB_Captain_Warder.tgi", "bb_captain_council_ranger", need(R, "woodmill", "library", "city"))
tier("Council/_BB_Support_Council_Swordsman.tgi", "bb_spellsword", need(H, "blacksmith", "library", "city"))
tier("Council/_BB_Captain_Council_Swordsman.tgi", "bb_captain_council_swordsman", need(H, "blacksmith", "library", "city"))

# Every-race faction lines: base_ buildings (any race's version)
tier("Royalist/_BB_Front_Paladin.tgi", "bb_front_paladin", "base_barracks,base_blacksmith")       # Knight
tier("Royalist/_BB_Captain_Paladin.tgi", "bb_captain_paladin", "base_barracks,base_blacksmith")   # Champion
tier("Nationalist/_BB_Front_Crusader.tgi", "bb_front_nationalist_swordsman", "base_barracks,base_blacksmith")
tier("Nationalist/_BB_Support_Warpriest.tgi", "bb_support_nationalist_swordsman", "base_barracks,base_shrine")
tier("Nationalist/_BB_Captain_Templar.tgi", "bb_captain_nationalist_swordsman", "base_barracks,base_blacksmith")
tier("Ceyah/_BB_Front_Blackguard.tgi", "bb_front_ceyah_stonewalker", "base_barracks,base_blacksmith")
tier("Ceyah/_BB_Support_Executioner.tgi", "bb_support_ceyah_stonewalker", "base_barracks,base_blacksmith")
tier("Ceyah/_BB_Captain_Harbinger.tgi", "bb_captain_ceyah_stonewalker", "base_barracks,base_blacksmith")

# Front-line units of the faction lines get a company type of their own: the company editor's
# front slot is locked to the company type, so a unit no company leads can only fill flank and
# support slots (user, 2026-10-19: "it showed them as available for the front line, but I could
# only use them in the flank and support slots").
COMPANIES = [
    # file, front unit, company template, layout, captain, name, sounds, banner
    ("Royalist/_BB_Front_Paladin.tgi", "bb_front_paladin", "K2RoyalistCompany", "company_mounted",
     "bb_captain_paladin", "Knight Company", "Paladin/Paladin", "dragoon", "CavalryIcon"),
    ("Nationalist/_BB_Front_Crusader.tgi", "bb_front_nationalist_swordsman", "K2NationalistCompany", "company_standard",
     "bb_captain_nationalist_swordsman", "Crusader Company", "/Units/Nationalist/GhalenMordecai/GhalenMordecai",
     "swordsman", "InfantryIcon"),
    ("Ceyah/_BB_Front_Blackguard.tgi", "bb_front_ceyah_stonewalker", "K2CeyahCompany", "company_standard",
     "bb_captain_ceyah_stonewalker", "Blackguard Company", "/Units/Haroun/Stonewalker/Stonewalker", "stonewalker",
     "InfantryIcon"),
    ("Council/_BB_Front_Rune_Hammer.tgi", "bb_front_council_hammer", "K2CouncilCompany", "company_mounted",
     "bb_captain_council_hammer", "Rune Hammer Company", "/Units/Gauri/Hammer/Hammer", "hammer", "CavalryIcon"),
]

COMPANY = """
;; Battleborn: a company type led by {front} (the company editor's front slot is locked to the company type)
[Thing template={template}]
{{
	IDS = company_{front}
	name = "#bb_company_{front}_name"

	[View]
	{{
		resource_prefix = {prefix}
		banner_icon = /Organizations/BannerIcons/{banner}.tga

		[WhenSelected Template=FXC_PlaySFX]
		audio_ids = {sound}_select

		[WhenCommanded Template=FXC_PlaySFX]
		audio_ids = {sound}_move

		[WhenCommandedAggressive Template=FXC_PlaySFX]
		audio_ids = {sound}_attack
	}}

	[PropertiesComponent]
	{{
		[Property]
		property_IDS = company_melee
	}}

	[OrganizationComponent]
	{{
		layout_IDS = {layout}
		entrenchment_time = 300

		[Slot]	;; front
		element_IDS = {front}

		[Slot]	;; flank
		element_IDS = null

		[Slot]	;; support
		element_IDS = null

		[Slot]	;; support
		element_IDS = null

		[Slot]	;; captain
		element_IDS = {captain}
	}}
}}
"""


def read(path):
    data = open(path, "rb").read()
    return data.decode("utf-8"), ("\r\n" if b"\r\n" in data else "\n")


def write(path, text):
    open(path, "wb").write(text.encode("utf-8"))


def work_file(rel, game):
    dst = os.path.join(WORK, "Units", *rel.split("/"))
    if not os.path.isfile(dst):
        data = game.get("Units/" + rel)
        if data is None:
            sys.exit(f"Units/{rel} is neither in work/ nor in the game's Data.rwd")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(data)
    return dst


def unit_span(lines, ids):
    """(start, end) line range of the [Unit ...] block whose IDS is ids."""
    start = block = None
    for i, line in enumerate(lines):
        if re.match(r"^\[", line):
            if start is not None:
                return start, i
            if re.match(r"^\[Unit\b", line, re.I):
                block = i
            else:
                block = None
            continue
        if block is not None and start is None and re.match(rf"^\t(?:IDS|ids)\s*=\s*{re.escape(ids)}\s*(;.*)?$", line.rstrip("\r")):
            start = block
    if start is not None:
        return start, len(lines)
    return None


def apply(game):
    changed = 0
    for ids, (rel, value) in TIERS.items():
        path = work_file(rel, game)
        text, nl = read(path)
        lines = text.split("\n")
        span = unit_span(lines, ids)
        if not span:
            sys.exit(f"{rel}: no [Unit] block with IDS = {ids}")
        for i in range(*span):
            m = re.match(r"^(\s*required_structures\s*=\s*)([^;\r]*?)\s*(;;.*?)?(\r?)$", lines[i], re.I)
            if m:
                old = m.group(2).strip()
                if old.replace(" ", "") == value:
                    break
                note = m.group(3) or ""
                if "tiers:" not in note:
                    note = f";; tiers: was {old}"
                lines[i] = f"{m.group(1)}{value} {note}{m.group(4)}"
                changed += 1
                break
        else:
            sys.exit(f"{rel}: {ids} has no required_structures line")
        write(path, "\n".join(lines))
    added = 0
    for rel, front, template, layout, captain, name, prefix, sound, banner in COMPANIES:
        path = work_file(rel, game)
        text, nl = read(path)
        if f"IDS = company_{front}" in text:
            continue
        block = COMPANY.format(front=front, template=template, layout=layout, captain=captain, prefix=prefix,
                               sound=sound, banner=banner).replace("\n", nl)
        write(path, text.rstrip("\r\n") + nl + block)
        added += 1
    loc = os.path.join(WORK, "Localization", "strings_data_K2.tgi")
    text, nl = read(loc)
    new = [f'\tbb_company_{front}_name = "{name}"' for rel, front, *_rest, in COMPANIES
           for name in [_rest[3]] if f"bb_company_{front}_name" not in text]
    if new:
        anchor = text.rstrip().rfind("}")
        text = text[:anchor].rstrip("\r\n\t ") + nl + nl + "\t;; Battleborn company types for the faction lines' front units" + nl + nl.join(new) + nl + text[anchor:]
        write(loc, text)
    print(f"{changed} requirement(s) changed, {added} company type(s) added, {len(new)} name(s) added")


def parse_units(game):
    """IDS -> required_structures (work/ first, then the game) for every unit file of the six races and factions."""
    req = {}
    names = set()
    for e in game.arc.entries:
        if e.name.startswith("Units/") and e.name.lower().endswith(".tgi"):
            names.add(e.name)
    for root, _, files in os.walk(os.path.join(WORK, "Units")):
        for f in files:
            if f.lower().endswith(".tgi"):
                names.add("Units/" + os.path.relpath(os.path.join(root, f), os.path.join(WORK, "Units")).replace(os.sep, "/"))
    companies = []
    for name in sorted(names):
        path = os.path.join(WORK, *name.split("/"))
        text = read(path)[0] if os.path.isfile(path) else (game.get(name) or b"").decode("utf-8", "replace")
        kind = ids = None
        slots = []
        for line in text.split("\n"):
            m = re.match(r"^\[(\w+)\s+template\s*=\s*(\w+)", line, re.I)
            if m:
                if kind == "company" and ids:
                    companies.append((name, ids, slots))
                kind = "unit" if m.group(1).lower() == "unit" else ("company" if m.group(2).lower().endswith("company") else None)
                ids, slots = None, []
                continue
            m = re.match(r"^\t(?:IDS|ids)\s*=\s*(\w+)", line)
            if m and ids is None:
                ids = m.group(1)
            m = re.match(r"^\s*required_structures\s*=\s*([^;\r]*)", line, re.I)
            if m and kind == "unit" and ids and ids not in req:
                req[ids] = [p.strip() for p in m.group(1).split(",") if p.strip() and p.strip().lower() != "null"]
            m = re.match(r"^\s*element_IDS\s*=\s*(\w+)", line, re.I)
            if m and kind == "company":
                slots.append(m.group(1))
        if kind == "company" and ids:
            companies.append((name, ids, slots))
    return req, companies


LEVEL = {"village": 1, "town": 2, "city": 3, "citadel": 4}


def level(reqs):
    best = 0
    for r in reqs:
        m = re.search(r"_center_(village|town|city|citadel)$", r)
        if m:
            best = max(best, LEVEL[m.group(1)])
    return best


def check(game):
    req, companies = parse_units(game)
    problems = 0
    for name, ids, slots in companies:
        if not slots or slots[0].lower() == "null" or slots[0] not in req:
            continue
        front = req[slots[0]]
        for el in slots[1:]:
            if el.lower() == "null" or el not in req:
                continue
            extra = [r for r in req[el] if r not in front and not r.endswith(("_center_village", "_center_town", "_center_city", "_center_citadel"))]
            if extra or level(req[el]) > level(front):
                problems += 1
                print(f"{ids} ({name}): default {el} needs {','.join(req[el]) or '-'}; the front {slots[0]} needs {','.join(front) or '-'}")
    print(f"{problems} default unit(s) need more than their company's front unit")


def main():
    game = bb.Game(bb.find_game())
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "apply":
        apply(game)
    check(game)


if __name__ == "__main__":
    main()
