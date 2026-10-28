"""Simple Battleborn retextures: recolour a game skin by material, keep its team-colour alpha.

Each recipe in RECIPES names the game texture a unit borrows and a list of steps. A step picks
pixels by material, measured on the ORIGINAL texture (steel = grey, gold = brass/gold, leather,
green, red, copper, any), optionally only inside or outside boxes, and only the
interior or the edge of each patch (edge = the 1-pixel rim, which reads as trim in game), and
maps their brightness through a palette. Alpha (where the player's colour shows) is never
touched. The result is written as the uncompressed 32-bit DDS with mipmaps that the hand-made
Battleborn skins use, to work/<path>, and shipped as a delta against the game texture.

    py -3 tools/recolor.py [ids ...] [--preview <folder>]   write work/ textures (+ before/after PNGs)
Then: bb.py derive <path> <base> for a new file, bb.py diff, bb.py build.
"""

import io
import os
import struct
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb  # noqa: E402

PALETTES = {
    "gold": [(0, (35, 20, 0)), (.35, (140, 90, 15)), (.7, (230, 175, 50)), (1, (255, 245, 180))],
    "silver": [(0, (25, 28, 34)), (.5, (150, 158, 170)), (1, (250, 252, 255))],
    "dark_iron": [(0, (10, 10, 12)), (.6, (70, 72, 80)), (1, (150, 155, 165))],
    "black": [(0, (5, 5, 6)), (.7, (45, 45, 50)), (1, (110, 110, 120))],
    "pale": [(0, (95, 95, 100)), (.5, (210, 210, 214)), (1, (255, 255, 255))],
    "white": [(0, (30, 30, 34)), (.25, (120, 120, 126)), (.6, (205, 205, 210)), (1, (255, 255, 255))],
    "red": [(0, (30, 0, 0)), (.5, (150, 20, 15)), (1, (255, 120, 100))],
    "purple": [(0, (15, 5, 25)), (.5, (85, 40, 120)), (1, (200, 160, 240))],
    "blue": [(0, (5, 10, 30)), (.5, (40, 70, 150)), (1, (170, 200, 255))],
    "slate": [(0, (10, 14, 22)), (.5, (70, 90, 125)), (1, (190, 210, 240))],
    "bronze": [(0, (30, 15, 5)), (.5, (150, 95, 45)), (1, (250, 210, 150))],
    "forest": [(0, (5, 15, 5)), (.5, (40, 90, 40)), (1, (160, 210, 140))],
    "charcoal": [(0, (8, 10, 14)), (.6, (40, 46, 58)), (1, (120, 130, 150))],
}

# face, hands and skin areas (x0, y0, x1, y1 in texture pixels) that no step may touch
FACES = {
    "Units/Human/Lancer/Lancerbase.dds": [(0, 0, 40, 30), (40, 20, 64, 32)],
    "Units/Human/Engineer/Engineerbase.dds": [(0, 0, 40, 22), (40, 26, 52, 40)],
    "Units/Human/Pioneer/Pioneerbase.dds": [(0, 0, 40, 22), (112, 26, 128, 40)],
    "Units/Nationalist/AethanFarhyd/AethanFarhydBase.dds": [(0, 0, 30, 30)],
    "Units/Council/RavidSakeri/RavidSakeribase.dds": [(12, 0, 52, 30)],
    "Units/Human/Ranger/Rangerbase.dds": [(52, 64, 72, 90)],
}

L, B, D, G = "Units/Human/Lancer/Lancerbase.dds", "Units/Human/Bowman/Bowmanbase.dds", \
    "Units/Human/Dragoon/Dragoonbase.dds", "Units/Nationalist/GhalenMordecai/GhalenMordecaibase.dds"
E, R, S = "Units/Human/Engineer/Engineerbase.dds", "Units/Human/Ranger/Rangerbase.dds", \
    "Units/Haroun/Stonewalker/Stonewalkerbase.dds"
H = "Units/Gauri/Hammer/Hammerbase.dds"
HORSE = [(160, 34, 256, 128), (128, 52, 160, 128), (128, 0, 200, 34)]

# ids: (work path, base texture, look, [(material, palette, {options})])
RECIPES = {
    "bb_captain_lancer": ("Units/Human/_BB_Captain_Lancer/bb_captain_lancer.dds", L, "gold armour, white horse",
                          [("steel", "gold", {"outside": HORSE}), ("leather", "pale", {"inside": HORSE})]),
    "bb_support_lancer": ("Units/Human/_BB_Support_Lancer/bb_support_lancer.dds", L, "silver, grey leather, black horse",
                          [("steel", "silver", {}), ("leather", "black", {"inside": HORSE})]),
    "bb_captain_engineer": ("Units/Human/_BB_Captain_Engineer/bb_captain_engineer.dds", E, "gold armour",
                            [("steel", "gold", {})]),
    "bb_support_engineer": ("Units/Human/_BB_Support_Engineer/bb_support_engineer.dds", E, "dark iron (my pick)",
                            [("steel", "dark_iron", {})]),
    "bb_captain_bowman": ("Units/Human/_BB_Captain_Bowman/bb_captain_bowman.dds",
                          "Units/Nationalist/AethanFarhyd/AethanFarhydBase.dds", "Aethan Farhyd in gold armour",
                          [("steel", "gold", {"vmin": .1})]),
    "bb_skirmisher": ("Units/Human/_BB_Skirmisher/bb_skirmisher.dds", B, "gold trim",
                      [("steel", "gold", {})]),
    "bb_support_bowman": ("Units/Human/_BB_Support_Bowman/bb_support_bowman.dds", B, "ranger green (my pick)",
                          [("warm", "forest", {"outside": [(56, 52, 80, 112)]}), ("steel", "silver", {})]),
    "bb_support_dragoon": ("Units/Human/_BB_Support_Dragoon/bb_support_dragoon.dds", D,
                           "dark iron, gold trim (my pick)", [("steel", "dark_iron", {})]),
    "bb_support_swordsman": ("Units/Human/_BB_Support_Swordsman/bb_support_swordsman.dds",
                             "Units/Human/Swordsman/Swordsmanbase.dds", "bronze (my pick)",
                             [("steel", "bronze", {"outside": [(112, 0, 128, 96)]})]),
    "bb_captain_pioneer": ("Units/Human/_BB_Captain_Pioneer/bb_captain_pioneer.dds",
                           "Units/Human/Pioneer/Pioneerbase.dds", "blue coat, gold buckles (my pick)",
                           [("steel", "blue", {"vmin": .4})]),
    "bb_front_ranger": ("Units/Human/_BB_Front_Ranger/bb_front_ranger.dds", R,
                        "crimson cloak (stand-in for the Royal Court Hunter look)", [("green", "red", {})]),
    "bb_captain_undead_necromancer": ("Units/Undead/_BB_Captain_Necromancer/bb_captain_necromancer.dds",
                                      "Units/Undead/Lich/Lichbase.dds", "purple robes, dark iron (my pick)",
                                      [("green", "purple", {}), ("steel", "dark_iron", {})]),
    "bb_front_nationalist_swordsman": ("Units/Nationalist/_BB_Front_Crusader/bb_front_crusader.dds", G,
                                       "Ghalen in silver only", [("gold", "silver", {}), ("leather", "silver", {})]),
    "bb_support_nationalist_swordsman": ("Units/Nationalist/_BB_Support_Warpriest/bb_support_warpriest.dds", G,
                                         "Ghalen in silver, gold trim",
                                         [("gold", "silver", {"part": "interior"}), ("leather", "silver", {"part": "interior"})]),
    "bb_captain_nationalist_swordsman": ("Units/Nationalist/_BB_Captain_Templar/bb_captain_templar.dds", G,
                                         "Ghalen in dark iron, gold trim",
                                         [("gold", "dark_iron", {"part": "interior"}), ("leather", "dark_iron", {"part": "interior"})]),
    "bb_front_ceyah_stonewalker": ("Units/Ceyah/_BB_Front_Blackguard/bb_front_blackguard.dds", S, "black armour",
                                   [("green", "black", {})]),
    "bb_support_ceyah_stonewalker": ("Units/Ceyah/_BB_Support_Executioner/bb_support_executioner.dds", S,
                                     "black armour, red trim",
                                     [("green", "black", {"part": "interior"}),
                                      ("green", "red", {"part": "edge", "smin": .45}), ("green", "black", {}),
                                      ("gold", "red", {})]),
    "bb_captain_ceyah_stonewalker": ("Units/Ceyah/_BB_Captain_Harbinger/bb_captain_harbinger.dds", S,
                                     "black armour, gold trim",
                                     [("green", "black", {"part": "interior"}),
                                      ("green", "gold", {"part": "edge", "smin": .45}), ("green", "black", {})]),
    "bb_front_council_hammer": ("Units/Council/_BB_Front_Rune_Hammer/bb_front_rune_hammer.dds", H,
                                "Council slate-blue armour (my pick)", [("copper", "slate", {"outside": [(128, 32, 256, 128)]})]),
    "bb_captain_council_hammer": ("Units/Council/_BB_Captain_Rune_Lord/bb_captain_rune_lord.dds", H,
                                  "gold armour (my pick)", [("copper", "gold", {"outside": [(128, 32, 256, 128)]})]),
    "bb_captain_council_magelord": ("Units/Council/_BB_Captain_Mage_Lord/bb_captain_mage_lord.dds",
                                    "Units/Council/RavidSakeri/RavidSakeribase.dds", "Ravid in Council blue (my pick)",
                                    [("red", "blue", {})]),
    "bb_captain_council_ranger": ("Units/Council/_BB_Captain_Warder/bb_captain_warder.dds", R,
                                  "charcoal cloak (stand-in for the Sharpshooter look)", [("green", "charcoal", {})]),
    "bb_support_council_ranger": ("Units/Council/_BB_Support_Arcane_Archer/bb_support_arcane_archer.dds", R,
                                  "white cloak", [("green", "white", {})]),
}


def hsv(rgb):
    r, g, b = (rgb[..., i] / 255.0 for i in range(3))
    mx, mn = np.max(rgb, -1) / 255.0, np.min(rgb, -1) / 255.0
    d = mx - mn
    h = np.zeros_like(mx)
    safe = np.where(d == 0, 1, d)
    h = np.where(mx == r, ((g - b) / safe) % 6, h)
    h = np.where(mx == g, (b - r) / safe + 2, h)
    h = np.where(mx == b, (r - g) / safe + 4, h)
    h = np.where(d == 0, 0, h) * 60
    s = np.where(mx == 0, 0, d / np.where(mx == 0, 1, mx))
    return h, s, mx


def material(name, h, s, v, vmin):
    if name == "steel":                     # grey, and the blue-tinted steel of the Human models
        return ((s < .25) | ((h >= 180) & (h <= 250) & (s < .42) & (v >= .4))) & (v >= vmin)
    if name == "gold":
        return (h >= 30) & (h <= 62) & (s >= .35) & (v >= .3)
    if name == "leather":
        return (h >= 8) & (h < 40) & (s >= .3) & (v >= .08) & ~((h >= 30) & (s >= .35) & (v >= .3))
    if name == "warm":
        return (h >= 5) & (h < 65) & (s >= .25) & (v >= .08)
    if name == "copper":
        return (h >= 8) & (h < 32) & (s >= .45) & (v >= .12)
    if name == "green":
        return (h >= 65) & (h <= 175) & (s >= .18) & (v >= .1)
    if name == "red":
        return ((h < 15) | (h >= 335)) & (s >= .35) & (v >= .08)
    if name == "any":
        return v >= vmin
    raise ValueError(name)


def padding(rgb):
    """The flat fill around the painted parts (the most common colour, when it is not black)."""
    q = (rgb // 4).astype(np.int64)
    keys = (q[..., 0] << 12) | (q[..., 1] << 6) | q[..., 2]
    vals, counts = np.unique(keys, return_counts=True)
    k = vals[counts.argmax()]
    fill = np.array([(k >> 12) & 63, (k >> 6) & 63, k & 63]) * 4 + 2
    if counts.max() < keys.size * .03 or fill.max() < 24:
        return np.zeros(keys.shape, bool)
    return np.abs(rgb - fill).max(-1) <= 10


def boxes(shape, rects):
    m = np.zeros(shape, bool)
    for x0, y0, x1, y1 in rects:
        m[y0:y1, x0:x1] = True
    return m


def erode(m):
    out = m.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            out &= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def ramp(name, t):
    stops = PALETTES[name]
    xs = np.array([p for p, _ in stops])
    return np.stack([np.interp(t, xs, np.array([c[i] for _, c in stops], float)) for i in range(3)], -1)


def recolor(img, base, steps):
    rgba = np.asarray(img.convert("RGBA")).astype(float)
    rgb = rgba[..., :3]
    h, s, v = hsv(rgb)
    luma = (rgb @ np.array([.299, .587, .114])) / 255.0
    out = rgb.copy()
    protect = boxes(v.shape, FACES.get(base, [])) | padding(rgb)
    done = np.zeros(v.shape, bool)
    for mat, pal, opt in steps:
        m = material(mat, h, s, v, opt.get("vmin", .2)) & ~protect & ~done & (v > .03)
        if "smin" in opt:
            m &= s >= opt["smin"]
        if "inside" in opt:
            m &= boxes(v.shape, opt["inside"])
        if "outside" in opt:
            m &= ~boxes(v.shape, opt["outside"])
        if opt.get("part") == "interior":
            m &= erode(m)
        elif opt.get("part") == "edge":
            m &= ~erode(m)
        if not m.any():
            continue
        lo, hi = np.percentile(luma[m], 2), np.percentile(luma[m], 98)
        t = np.clip((luma - lo) / max(hi - lo, 1e-3), 0, 1)
        out[m] = ramp(pal, t[m])
        done |= m
    res = np.concatenate([np.clip(out, 0, 255), rgba[..., 3:]], -1).astype(np.uint8)
    return Image.fromarray(res, "RGBA")


def grey_lancer_leather(img):
    """Approved Lancer finish: desaturate rider leather and tack, preserving the coat and skin."""
    rgba = np.asarray(img.convert("RGBA")).copy()
    rgb = rgba[..., :3].astype(float)
    h, s, v = hsv(rgb)
    regions = [(0, 30, 58, 80), (60, 0, 94, 12), (0, 90, 40, 128),
               (162, 42, 180, 76), (204, 42, 213, 77), (149, 69, 244, 78),
               (185, 54, 205, 66), (190, 77, 202, 90), (228, 34, 256, 66)]
    protect = boxes(v.shape, [(0, 0, 58, 30), (40, 20, 64, 32), (58, 28, 96, 45)])
    mask = boxes(v.shape, regions) & ~protect & (h >= 5) & (h <= 82) & (s >= .16) & (v >= .12)
    luminance = rgb @ np.array([.299, .587, .114])
    grey = np.repeat((luminance * .90)[..., None], 3, axis=2)
    rgba[..., :3][mask] = np.clip(.96 * grey[mask] + .04 * rgb[mask], 0, 255).astype(np.uint8)
    return Image.fromarray(rgba)


def dds_bytes(img):
    """Uncompressed A8R8G8B8 DDS with a full mip chain (the format of the hand-made skins)."""
    w, h = img.size
    levels = [img]
    while levels[-1].size != (1, 1):
        lw, lh = levels[-1].size
        levels.append(levels[-1].resize((max(1, lw // 2), max(1, lh // 2)), Image.LANCZOS))
    head = struct.pack("<4s7I44x", b"DDS ", 124, 0x2100F, h, w, w * 4, 0, len(levels))
    head += struct.pack("<8I", 32, 0x41, 0, 32, 0xFF0000, 0xFF00, 0xFF, 0xFF000000)
    head += struct.pack("<4I4x", 0x401008, 0, 0, 0)
    body = b"".join(np.asarray(l.convert("RGBA"))[..., [2, 1, 0, 3]].tobytes() for l in levels)
    return head + body


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--preview")
    ap.add_argument("--game")
    args = ap.parse_args()
    game = bb.Game(bb.game_dir(args))
    for ids in args.ids or RECIPES:
        path, base, look, steps = RECIPES[ids]
        src = Image.open(io.BytesIO(game.get(base)))
        src.load()
        new = recolor(src, base, steps)
        if ids == "bb_support_lancer":
            new = grey_lancer_leather(new)
        dst = os.path.join(bb.REPO, "work", *path.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(dds_bytes(new))
        if args.preview:
            os.makedirs(args.preview, exist_ok=True)
            k = 3
            a, b = src.convert("RGBA"), new
            w, hh = a.size
            sheet = Image.new("RGB", (w * k * 2 + 8, hh * k), (40, 40, 40))
            sheet.paste(a.convert("RGB").resize((w * k, hh * k), Image.NEAREST), (0, 0))
            sheet.paste(b.convert("RGB").resize((w * k, hh * k), Image.NEAREST), (w * k + 8, 0))
            sheet.save(os.path.join(args.preview, ids + ".png"))
        print(f"{ids}: {path} ({look})")


if __name__ == "__main__":
    main()
