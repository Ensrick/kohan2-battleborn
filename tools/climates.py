"""Climate ports: each climate's map-editor palette also offers the other two climates' terrains
and doodads, recoloured to fit (author, 2026-10-28):

    "I want different colored versions of the terrains to fit each climate. Snow is snow, so
    that's probably fine the way it is, but the wasteland and grass should look different
    depending on the climate. In the snow, have it be blue-grey, frosted for all grass and
    plants from midlands ported over and the desert to look cold and grey as well. The desert
    in the midlands should look sandy dry, and the midlands in the desert should be like
    yellowed grass and plants. ... Fall looking trees and yellowed grass in desert when placing
    the midlands terrain types."

A climate (Biome) lists the terrains its maps can paint; a doodad's [Placement] says which
terrains of which biome scatter it. For every (target, source) pair in PORTS this tool writes,
from the player's own Data.rwd:

    Terrain/<Source>/_BB_in_<target>.tgi       copies of the source terrains (bb_<target>_<id>),
                                               textures under Terrain/<Source>/_BB_<Look>/
    Terrain/<target>.tgi                       the copies, their transitions and water appended
    Doodads/_BB_<target>_<look>_<source>.tgi   copies of the source doodads, re-skinned from
                                               <model folder>/_BB_<Look>/, scattered on the copies
                                               (Doodads/ root loads after every climate folder,
                                               so the decal effects they name already exist)
    Localization/strings_data_K2.tgi           names such as "Grass (Midlands, frosted)"
    Doodads/<Climate>/<file>.tgi               the target's own doodads that scatter on every
                                               terrain they do not list (biome-wide weight) list
                                               each ported terrain at weight 0

Copies live in the SOURCE terrain folder so their relative texture paths keep working. Textures
ship as deltas (bbdelta); the .tgi files become patches through 'bb.py diff', which this tool runs.

    py -3 tools/climates.py                    regenerate work/ files + texture deltas, then diff
    py -3 tools/climates.py --preview <dir>    before/after contact sheets only
"""

import argparse
import io
import os
import re
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bb  # noqa: E402
import bbdelta  # noqa: E402

REPO = bb.REPO
FOLDER = {"temperate": "Temperate", "arctic": "Arctic", "desert": "Desert"}
PORTS = (("arctic", "temperate", "frost"), ("arctic", "desert", "cold"),
         ("desert", "temperate", "autumn"), ("desert", "arctic", None),
         ("temperate", "desert", "sandy"), ("temperate", "arctic", None))
LABEL = {"frost": "frosted", "cold": "cold", "autumn": "autumn", "sandy": "dry"}
KEEP = re.compile(r"shadow|blood")              # Shadow and blood ground keep their colours everywhere
SKIP = {"arctic": re.compile(r"butterflies")}   # no butterflies in the snow
EFFECT_TEX = re.compile(r"glow|mist|smoke|waterring|currant", re.I)
MARK_BEGIN = "\t;; Battleborn climate ports (written by tools/climates.py)"
MARK_END = "\t;; end of climate ports"
NO_SCATTER = ";; Battleborn climate ports: no native scatter on ported ground (tools/climates.py)"


# ---------------------------------------------------------------- colour looks (rgb 0..1, rows)

def _rgb2hsv(c):
    mx, mn = c.max(1), c.min(1)
    d = mx - mn
    safe = np.where(d == 0, 1, d)
    r, g, b = c[:, 0], c[:, 1], c[:, 2]
    h = np.where(mx == r, ((g - b) / safe) % 6, np.where(mx == g, (b - r) / safe + 2, (r - g) / safe + 4))
    h = np.where(d == 0, 0, h) * 60
    s = np.where(mx == 0, 0, d / np.where(mx == 0, 1, mx))
    return h, s, mx


def _hsv2rgb(h, s, v):
    h = (h % 360) / 60
    i = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p, q, t = v * (1 - s), v * (1 - s * f), v * (1 - s * (1 - f))
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], 1)


def _lum(c):
    return (c @ np.array([0.299, 0.587, 0.114]))[:, None]


def _noise(xy, cell=40.0):
    """Smooth value noise 0..1 (doodad skins only: terrain tiles must stay seamless)."""
    x, y = xy[:, 0] / cell, xy[:, 1] / cell
    x0, y0 = np.floor(x), np.floor(y)
    fx, fy = x - x0, y - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)

    def hsh(a, b):
        v = np.sin(a * 127.1 + b * 311.7) * 43758.5453
        return v - np.floor(v)
    top = hsh(x0, y0) * (1 - fx) + hsh(x0 + 1, y0) * fx
    bot = hsh(x0, y0 + 1) * (1 - fx) + hsh(x0 + 1, y0 + 1) * fx
    return top * (1 - fy) + bot * fy


def frost(c, xy=None, plant=False):
    """Midlands in the Frozen Reaches: blue-grey, lifted toward frost; a little of each surface's
    own tint stays so grass, dirt and forest floor remain tellable apart."""
    L = _lum(c)
    lc = np.clip(0.5 + (L - 0.5) * 1.25, 0, 1)
    lf = 1 - (1 - lc) * (0.70 if plant else 0.66)
    return lf * np.array([0.84, 0.91, 1.0]) + 0.15 * (c - L)


def cold(c, xy=None, plant=False):
    """Barrens in the Frozen Reaches: cold grey."""
    L = _lum(c)
    return 0.96 * (0.16 + 0.80 * L) * np.array([0.90, 0.94, 1.0]) + 0.04 * c


def autumn(c, xy=None, plant=False):
    """Midlands in the Barrens: yellowed grass; plants and trees in fall colours."""
    h, s, v = _rgb2hsv(c)
    w = np.clip((1 - np.abs(h - 105) / 70) * 1.8, 0, 1)            # greens
    if plant == "conifer":                                         # evergreens go dry olive, not orange
        n = _noise(xy) if xy is not None else 0.5
        th, ts, tv = 52 + 14 * n, s * 0.75, v * 0.95
    elif plant:
        n = _noise(xy) if xy is not None else 0.5
        th, ts, tv = 14 + 36 * n, np.clip(s * 1.1 + 0.08, 0, 1), v * 1.02
    else:
        th, ts, tv = 44.0, s * 0.78, v * 0.98
    u = np.clip(1 - np.abs(h - 38) / 20, 0, 1) * (1 - w)           # tan dirt warms toward the Barrens
    h2 = h + w * (th - h) - 6 * u
    s2 = np.clip(s + w * (ts - s) + 0.15 * u * s, 0, 1)
    v2 = np.clip(v + w * (tv - v), 0, 1)
    return _hsv2rgb(h2, s2, v2)


def sandy(c, xy=None, plant=False):
    """Barrens in the Midlands: red-orange ground turns to dry tan sand."""
    h, s, v = _rgb2hsv(c)
    hh = np.where(h > 300, h - 360, h)
    w = np.clip((1 - np.abs(hh - 22) / 34) * 1.5, 0, 1)            # reds and oranges
    h2 = hh + w * (36 - hh)
    s2 = s + w * (0.58 * s - s)
    v2 = np.clip(v + w * (np.minimum(1, 1.08 * v + 0.03) - v), 0, 1)
    return _hsv2rgb(h2, s2, v2)


LOOKS = {"frost": frost, "cold": cold, "autumn": autumn, "sandy": sandy}


# ---------------------------------------------------------------- texture recolouring

def tga_recolor(data, fn):
    """Uncompressed 24/32-bit TGA, header and footer kept; None for any other kind."""
    idlen, cmtype, imtype = data[0], data[1], data[2]
    w, h = struct.unpack_from("<HH", data, 12)
    bpp = data[16]
    if cmtype != 0 or imtype != 2 or bpp not in (24, 32):
        return None
    off, n, ch = 18 + idlen, w * h, bpp // 8
    px = np.frombuffer(data, np.uint8, n * ch, off).reshape(n, ch)
    xy = np.stack([np.arange(n) % w, np.arange(n) // w], 1).astype(float)
    new = np.clip(np.rint(fn(px[:, [2, 1, 0]] / 255.0, xy) * 255), 0, 255).astype(np.uint8)
    out = px.copy()
    out[:, 0], out[:, 1], out[:, 2] = new[:, 2], new[:, 1], new[:, 0]
    return data[:off] + out.tobytes() + data[off + n * ch:]


def _dec565(c):
    c = c.astype(np.int32)
    return np.stack([((c >> 11) & 31) / 31.0, ((c >> 5) & 63) / 63.0, (c & 31) / 31.0], 1)


def _enc565(rgb):
    q = np.clip(np.rint(rgb * [31, 63, 31]), 0, [31, 63, 31]).astype(np.int32)
    return (q[:, 0] << 11) | (q[:, 1] << 5) | q[:, 2]


def _dxt1_modes(old, new, idx):
    """Keep each DXT1 block in its mode: c0 > c1 = four colours, c0 <= c1 = three + transparent."""
    four = old[:, 0] > old[:, 1]
    c0, c1 = new[:, 0].copy(), new[:, 1].copy()
    swap4, swap3 = four & (c0 < c1), ~four & (c0 > c1)
    swap = swap4 | swap3
    c0, c1 = np.where(swap, c1, c0), np.where(swap, c0, c1)
    idx = np.where(swap4, idx ^ 0x55555555, idx)                     # 0<->1, 2<->3
    idx = np.where(swap3, idx ^ (~(idx >> 1) & 0x55555555), idx)     # 0<->1; 2, 3 stay
    eq = four & (c0 == c1)
    c1 = np.where(eq & (c0 > 0), c0 - 1, c1)
    c0 = np.where(eq & (c0 == 0), 1, c0)
    return np.stack([c0, c1], 1), idx


def dds_recolor(data, fn):
    """DXT1/3/5: only the two endpoint colours of each 4x4 block change (indices and alpha stay,
    every mip level); 32-bit BGRA: per pixel. None for any other kind."""
    if data[:4] != b"DDS ":
        return None
    h, w = struct.unpack_from("<II", data, 12)
    mips = max(1, struct.unpack_from("<I", data, 28)[0])
    pf_flags, fourcc, bits = struct.unpack_from("<I4sI", data, 80)
    out, off = bytearray(data), 128
    if pf_flags & 4 and fourcc in (b"DXT1", b"DXT3", b"DXT5"):
        bs, co = (8, 0) if fourcc == b"DXT1" else (16, 8)
        for lvl in range(mips):
            lw, lh = max(1, w >> lvl), max(1, h >> lvl)
            bw, bh = (lw + 3) // 4, (lh + 3) // 4
            n = bw * bh
            if off + n * bs > len(data):
                break
            blk = np.frombuffer(data, np.uint8, n * bs, off).reshape(n, bs).copy()
            old = blk[:, co:co + 4].copy().view("<u2").reshape(n, 2).astype(np.int64)
            idx = blk[:, co + 4:co + 8].copy().view("<u4").reshape(n).astype(np.int64)
            sc = 1 << lvl
            k = np.arange(n)
            xy = np.repeat(np.stack([(k % bw) * 4 * sc + 2 * sc, (k // bw) * 4 * sc + 2 * sc], 1), 2, 0).astype(float)
            new = _enc565(fn(_dec565(old.reshape(-1)), xy)).reshape(n, 2).astype(np.int64)
            if fourcc == b"DXT1":
                new, idx = _dxt1_modes(old, new, idx)
            blk[:, co:co + 4] = new.astype("<u2").view(np.uint8).reshape(n, 4)
            blk[:, co + 4:co + 8] = (idx & 0xFFFFFFFF).astype("<u4").view(np.uint8).reshape(n, 4)
            out[off:off + n * bs] = blk.tobytes()
            off += n * bs
        return bytes(out)
    if pf_flags & 0x40 and bits == 32:
        for lvl in range(mips):
            lw, lh = max(1, w >> lvl), max(1, h >> lvl)
            n = lw * lh
            if off + n * 4 > len(data):
                break
            px = np.frombuffer(data, np.uint8, n * 4, off).reshape(n, 4).copy()
            sc = 1 << lvl
            xy = np.stack([np.arange(n) % lw * sc, np.arange(n) // lw * sc], 1).astype(float)
            new = np.clip(np.rint(fn(px[:, [2, 1, 0]] / 255.0, xy) * 255), 0, 255).astype(np.uint8)
            px[:, 0], px[:, 1], px[:, 2] = new[:, 2], new[:, 1], new[:, 0]
            out[off:off + n * 4] = px.tobytes()
            off += n * 4
        return bytes(out)
    return None


# ---------------------------------------------------------------- text helpers

def _decode(data):
    return data.decode("utf-8-sig") if data.startswith(b"\xef\xbb\xbf") else data.decode("latin-1")


def blocks(t, head):
    """(start, end) of each '[<head>...]' line plus its { } body, skipping ';;' comments."""
    out = []
    for m in re.finditer(r"^[ \t]*\[" + head, t, re.M | re.I):
        eol = t.find("\n", m.end())
        i = t.find("{", eol)
        if i < 0 or t[eol:i].strip():
            continue
        depth, j = 0, i
        while j < len(t):
            if t.startswith(";;", j):
                j = t.find("\n", j)
                j = len(t) if j < 0 else j
                continue
            depth += {"{": 1, "}": -1}.get(t[j], 0)
            if depth == 0:
                break
            j += 1
        out.append((m.start(), j + 1))
    return out


def _kv(line):
    """(indent, key, value) of a 'key = value' line, None for anything else or a comment."""
    if line.lstrip().startswith(";;"):
        return None
    m = re.match(r"^([ \t]*)(?:\w+[ \t]+)?(\w+)\s*=\s*(.*?)\s*$", line.split(";;")[0].rstrip("\r"))
    return (m.group(1), m.group(2), m.group(3)) if m else None


def terrain_lines(lines):
    """Indexes of a biome's 'terrain_IDS = x' list entries: the line after a [Terrain] item
    (WaterInfo blocks use the same key for their water terrain)."""
    out, prev = [], ""
    for i, line in enumerate(lines):
        st = line.strip()
        if not st or st.startswith(";;"):
            continue
        kv = _kv(line)
        if prev.lower().startswith("[terrain") and kv and kv[1].lower() == "terrain_ids":
            out.append(i)
        prev = st
    return out


def _first(block, key):
    for line in block.split("\n"):
        kv = _kv(line)
        if kv and kv[1].lower() == key.lower():
            return kv[2]
    return None


def _color(val, fn):
    rgb = np.array([[float(x) for x in val.split(",")]])
    if (rgb < 0).any():
        return val
    return ", ".join(f"{x:.3f}" for x in np.clip(fn(rgb), 0, 1)[0])


# ---------------------------------------------------------------- reading the game

class Climates:
    def __init__(self, game):
        self.game = game
        self.ent = {e.name.lower(): e.name for e in game.arc.entries}
        self.by_base = {}
        for low, name in self.ent.items():
            self.by_base.setdefault(os.path.basename(low), []).append(name)
        self.terrains = {}                  # id -> (file, block)
        for low, name in self.ent.items():
            if low.startswith("terrain/") and low.endswith(".tgi") and low.count("/") == 2:
                t = _decode(game.get(name))
                for s, e in blocks(t, "Terrain template="):
                    self.terrains[_first(t[s:e], "IDS").lower()] = (name, t[s:e])
        self.templates = {}                 # doodad template -> (inherit, placement)
        tt = _decode(game.get("Templates/template_doodad_k2.tgi"))
        for s, e in blocks(tt, "template "):
            m = re.match(r"\s*\[template (\w+)(?: (?:template|inherit)=(\w+))?", tt[s:e], re.I)
            self.templates[m.group(1).lower()] = ((m.group(2) or "").lower(), self.placement(tt[s:e]))
        self.doodads = {}                   # id -> (file, block, template)
        for low, name in self.ent.items():
            if low.startswith("doodads/") and low.endswith(".tgi"):
                t = _decode(game.get(name))
                for s, e in blocks(t, "Thing "):
                    m = re.match(r"\s*\[Thing Template=(\w+)\]", t[s:e], re.I)
                    ids = _first(t[s:e], "IDS")
                    if m and ids and m.group(1).lower().startswith("k2"):
                        self.doodads[ids.lower()] = (name, t[s:e], m.group(1).lower())
        self.strings = {}
        for line in _decode(game.get("Localization/strings_data_K2.tgi")).split("\n"):
            m = re.match(r'\s*(\w+)\s*=\s*"(.*)"', line)
            if m:
                self.strings[m.group(1).lower()] = m.group(2)

    def biome(self, b):
        t = _decode(self.game.get(f"Terrain/{b}.tgi"))
        ids = [t.split("\n")[i].split("=")[1].split(";;")[0].strip().lower() for i in terrain_lines(t.split("\n"))]
        trans, cur = [], None
        for line in t.split("\n"):
            if line.strip().lower().startswith("[transition]"):
                cur = {}
                trans.append(cur)
                continue
            kv = _kv(line)
            if cur is not None and kv and kv[1].lower() in ("terrain1_ids", "terrain2_ids", "variation_ids"):
                cur[kv[1].lower()] = kv[2].lower()
        water = [t[s:e] for s, e in blocks(t, "WaterInfo")]
        return t, ids, [x for x in trans if len(x) == 3], water

    @staticmethod
    def placement(block):
        """({biome: {"w": weight|None, "t": {terrain: (weight|None, primary)}}}, placement weight|None)"""
        pb = blocks(block, "Placement")
        if not pb:
            return {}, None
        biomes, pw, cur, ter = {}, None, None, None
        for line in block[pb[0][0]:pb[0][1]].split("\n"):
            st = line.strip().lower()
            if st.startswith("[biome"):
                cur, ter = {"w": None, "t": {}}, None
                continue
            if st.startswith("[terrain"):
                ter = [None, None, False]
                continue
            kv = _kv(line)
            if not kv:
                continue
            k, v = kv[1].lower(), kv[2]
            if cur is None:
                if k == "weight":
                    pw = float(v)
            elif ter is None:
                if k == "ids":
                    biomes[v.lower()] = cur
                elif k == "weight":
                    cur["w"] = float(v)
            else:
                if k == "ids":
                    ter[0] = v.lower()
                    cur["t"][ter[0]] = (None, False)
                elif k == "weight" and ter[0]:
                    cur["t"][ter[0]] = (float(v), cur["t"][ter[0]][1])
                elif k == "primary_doodad" and ter[0]:
                    cur["t"][ter[0]] = (cur["t"][ter[0]][0], v.lower() == "true")
        return biomes, pw

    def effective(self, did):
        """The doodad's placement with its template chain merged under it (same biome id: the Thing wins)."""
        _, block, tpl = self.doodads[did]
        chain, t = [], tpl
        while t in self.templates:
            chain.append(self.templates[t][1])
            t = self.templates[t][0]
        biomes, pw = {}, None
        for b, w in list(reversed(chain)) + [self.placement(block)]:
            biomes.update(b)
            pw = w if w is not None else pw
        return biomes, (-1.0 if pw is None else pw)

    def weight(self, did, biome, terrain):
        biomes, pw = self.effective(did)
        b = biomes.get(biome)
        if b is None:
            return -1.0, False
        if terrain in b["t"]:
            w, prim = b["t"][terrain]
            return (w if w is not None else b["w"] if b["w"] is not None else pw), prim
        return (b["w"] if b["w"] is not None else pw), False

    def nif_textures(self, nif):
        data = self.game.get(nif)
        if data is None:
            return []
        names = {x.decode("latin-1").replace("\\", "/").split("/")[-1].lower()
                 for x in re.findall(rb"[\w\-. /\\]{3,80}\.(?:dds|tga)", data, re.I)}
        out = []
        for n in sorted(names):
            near = f"{os.path.dirname(nif)}/{n}".lower()
            path = self.ent.get(near) or (self.by_base.get(n) or [None])[0]
            if path:
                out.append(path)
        return out


# ---------------------------------------------------------------- generation

class Output:
    def __init__(self, cl, preview=None):
        self.cl, self.preview = cl, preview
        self.files, self.deltas, self.pairs = {}, {}, []
        self.made = {}

    def texture(self, base_path, look, plant):
        new_path = f"{os.path.dirname(base_path)}/_BB_{look.capitalize()}/{os.path.basename(base_path)}"
        if new_path in self.made:
            return self.made[new_path]
        base = self.cl.game.get(base_path)
        fn = LOOKS[look]
        conv = (lambda rgb, xy: fn(rgb, xy, plant))
        new = (tga_recolor if base_path.lower().endswith(".tga") else dds_recolor)(base, conv)
        if new is None:
            print(f"  kept stock (unsupported format): {base_path}")
            self.made[new_path] = None
            return None
        self.files[new_path] = new
        self.deltas[new_path] = base_path
        self.pairs.append((look, base_path, base, new))
        self.made[new_path] = new_path
        return new_path


def _rename_terrain(block, target, tid, look, pri, tex_paths):
    out, named = [], False
    for line in block.split("\n"):
        kv = _kv(line)
        cr = "\r" if line.endswith("\r") else ""
        if not kv:
            out.append(line)
            continue
        ind, key, val = kv
        k = key.lower()
        prefix = line[:len(ind)] + line[len(ind):].split("=")[0].rstrip() + " = "
        if k == "ids":
            val = f"bb_{target}_{val.lower()}"
        elif k == "name" and not named:
            val, named = f'"#bb_{target}_{tid}_name"', True
        elif k == "base_priority":
            val = str(pri)
        elif k == "terrain_color" and look:
            val = _color(val, lambda c: LOOKS[look](c))
        elif k == "texture" and look and val.lower() in tex_paths:
            val = tex_paths[val.lower()]
        else:
            out.append(line)
            continue
        out.append(prefix + val + cr)
    return "\n".join(out)


def _rename_thing(cl, did, target, key, look, places, out):
    """Copy of a doodad Thing: generic template, new id/name, own [Placement] for the target only,
    absolute resource_prefix, and a recoloured skin per aspect where its model has one base texture."""
    src, block, tpl = cl.doodads[did]
    folder = os.path.dirname(src)
    nid = f"bb_{target}_{key}_{did}"
    t = block
    for s, e in reversed(blocks(t, "Placement")):
        ls = t.rfind("\n", 0, s) + 1
        t = t[:ls] + t[e:].lstrip(" \t\r").lstrip("\n")
    lines = t.split("\n")
    lines[0] = re.sub(r"Template=\w+", "Template=" + ("K2DynamicDoodad" if "dynamic" in tpl else "K2Doodad"), lines[0], flags=re.I)
    res, named, done_ids, prefix = [], False, False, None
    for line in lines:
        kv = _kv(line)
        cr = "\r" if line.endswith("\r") else ""
        if kv and kv[1].lower() == "resource_prefix" and not kv[2].startswith("/"):
            prefix = f"/{folder}/{kv[2]}"
            line = f"{kv[0]}resource_prefix = {prefix}{cr}"
        elif kv and kv[1].lower() == "resource_prefix":
            prefix = kv[2]
        res.append(line)
        if kv and kv[1].lower() == "ids" and not done_ids:
            res[-1] = f"{kv[0]}IDS = {nid}{cr}"
            done_ids = True
        elif kv and kv[1].lower() == "name" and not named:
            ind = kv[0]
            res[-1] = f'{ind}name = "#{nid}_name"{cr}'
            named = True
            res.append(f"{ind}[Placement]{cr}")
            res.append(f"{ind}{{{cr}")
            res.append(f"{ind}\t[Biome]{cr}")
            res.append(f"{ind}\t{{{cr}")
            res.append(f"{ind}\t\tids = {target}{cr}")
            res.append(f"{ind}\t\tweight = 0{cr}")
            for ter, (w, prim) in places:
                res.append(f"{cr}")
                res.append(f"{ind}\t\t[Terrain]{cr}")
                res.append(f"{ind}\t\tIDS = {ter}{cr}")
                res.append(f"{ind}\t\tweight = {np.format_float_positional(w, trim='-')}{cr}")
                if prim:
                    res.append(f"{ind}\t\tprimary_doodad = true{cr}")
            res.append(f"{ind}\t}}{cr}")
            res.append(f"{ind}}}{cr}")
    if not look:
        return nid, "\n".join(res)
    # aspects: [Aspect ...] then key lines up to the next '[' or '}' line
    final, i, skinned = [], 0, 0
    while i < len(res):
        line = res[i]
        if re.match(r"\s*\[Aspect\b", line, re.I):
            j = i + 1
            while j < len(res) and not re.match(r"\s*[\[}]", res[j]):
                j += 1
            asp = [x for x in res[i:j] if not (_kv(x) and _kv(x)[1].lower() == "skin")]
            model = next((_kv(x)[2] for x in asp if _kv(x) and _kv(x)[1].lower() == "model"), "%s.nif")
            nif = model.replace("%s", prefix or "").lstrip("/")
            texs = [p for p in cl.nif_textures(cl.ent.get(nif.lower(), nif)) if not EFFECT_TEX.search(os.path.basename(p))]
            kind = "conifer" if "coniferous" in did else True
            skin = out.texture(texs[0], look, kind) if len(texs) == 1 else None
            if skin:
                at = next(k for k, x in enumerate(asp) if _kv(x) and _kv(x)[1].lower() == "model") if any(
                    _kv(x) and _kv(x)[1].lower() == "model" for x in asp) else len(asp) - 1
                ind = _kv(asp[at])[0] if _kv(asp[at]) else "\t\t"
                cr = "\r" if asp[at].endswith("\r") else ""
                asp.insert(at + 1, f"{ind}skin = /{skin}{cr}")
                skinned += 1
            elif texs:
                print(f"  {did}: {os.path.basename(nif)} has {len(texs)} textures, kept stock")
            final.extend(asp)
            i = j
            continue
        final.append(line)
        i += 1
    if not skinned:
        print(f"  {did}: no aspect could be re-skinned, kept stock colours")
    return nid, "\n".join(final)


def _exclude(text, did, biome, ids):
    """The Thing did's own [Biome] block for biome, with a weight 0 [Terrain] item for each of ids."""
    for s, e in blocks(text, "Thing "):
        if (_first(text[s:e], "IDS") or "").lower() != did:
            continue
        for bs, be in blocks(text[s:e], "Biome"):
            sub = text[s + bs:s + be]
            if (_first(sub, "ids") or "").lower() != biome:
                continue
            ind = next(_kv(x)[0] for x in sub.split("\n") if _kv(x) and _kv(x)[1].lower() == "ids")
            cr = "\r" if "\r\n" in sub else ""
            add = [cr, f"{ind}{NO_SCATTER}{cr}"] + [
                x for n in ids for x in (cr, f"{ind}[Terrain]{cr}", f"{ind}ids = {n}{cr}", f"{ind}weight = 0{cr}")]
            at = s + bs + sub.rstrip().rfind("\n")      # end of the line before the block's closing brace
            return text[:at] + "".join("\n" + x for x in add) + text[at:]
    sys.exit(f"{did}: scatters on all {biome} terrain but has no [Biome] block of its own to extend")


def generate(cl, out):
    names = {}
    biome_text, bio = {}, {}
    edits = {}                          # native doodad file -> text with ported terrains excluded
    for b in FOLDER:
        bio[b] = cl.biome(b)
    for target in FOLDER:
        t, native, _, _ = bio[target]
        used = set()
        for tid in native:
            pri = int(_first(cl.terrains[tid][1], "base_priority"))
            nvar = max(1, len(re.findall(r"\[Variation\]", cl.terrains[tid][1])))
            used.update(range(pri, pri + nvar))
        new_ids, new_trans, new_water = [], [], []
        for tgt, source, look in PORTS:
            if tgt != target:
                continue
            _, ids, trans, water = bio[source]
            sname = cl.strings[f"{FOLDER[source].lower()}_name"]
            label = f", {LABEL[look]}" if look else ""
            files_text = []
            for tid in sorted(ids, key=lambda x: int(_first(cl.terrains[x][1], "base_priority"))):
                src, block = cl.terrains[tid]
                tlook = None if KEEP.search(tid) else look
                pri = int(_first(block, "base_priority"))
                nvar = max(1, len(re.findall(r"\[Variation\]", block)))
                while any(p in used for p in range(pri, pri + nvar)):
                    pri += 1
                used.update(range(pri, pri + nvar))
                tex = {}
                if tlook:
                    for line in block.split("\n"):
                        kv = _kv(line)
                        if kv and kv[1].lower() == "texture":
                            base_path = cl.ent.get(f"{os.path.dirname(src)}/{kv[2]}".lower())
                            made = out.texture(base_path, tlook, False) if base_path else None
                            if made:
                                tex[kv[2].lower()] = made[len(os.path.dirname(src)) + 1:]
                files_text.append(_rename_terrain(block, target, tid, tlook, pri, tex))
                orig = cl.strings.get(_first(block, "name").strip('"#').lower(), tid)
                names[f"bb_{target}_{tid}_name"] = f"{orig} ({sname}{label if tlook else ''})"
                new_ids.append(f"bb_{target}_{tid}")
            out.files[f"Terrain/{FOLDER[source]}/_BB_in_{target}.tgi"] = (
                f";; Battleborn: {FOLDER[source]} terrains as they appear in {FOLDER[target]} maps "
                f"(tools/climates.py)\r\n\r\n" + "\r\n\r\n".join(files_text) + "\r\n").encode("latin-1")
            for tr in trans:
                new_trans.append({k: f"bb_{target}_{v}" for k, v in tr.items()})
            for wblock in water:
                new_water.append(re.sub(r"(terrain_ids\s*=\s*)(\S+)", lambda m: m.group(1) + f"bb_{target}_{m.group(2).lower()}",
                                        wblock, count=1, flags=re.I))
            # doodads: the source folder's own, plus any doodad the source terrains scatter
            key = look or "stock"
            todo = {d for d, (f, _, _) in cl.doodads.items() if f.lower().startswith(f"doodads/{source}/")}
            for d in cl.doodads:
                if any(cl.weight(d, source, x)[0] > 0 for x in ids):
                    todo.add(d)
            things = []
            for d in sorted(todo):
                home = cl.doodads[d][0].split("/")[1].lower()
                if home == target or (target in SKIP and SKIP[target].search(d)):
                    continue
                places = []
                for x in ids:
                    w, prim = cl.weight(d, source, x)
                    if w > 0:
                        places.append((f"bb_{target}_{x}", (w, prim)))
                dlook = None if KEEP.search(d) else look
                nid, text = _rename_thing(cl, d, target, key, dlook, places, out)
                things.append(text)
                orig = cl.strings.get((_first(cl.doodads[d][1], "name") or "").strip('"#').lower(), d)
                names[f"{nid}_name"] = f"{orig} ({sname}{label if dlook else ''})"
            out.files[f"Doodads/_BB_{target}_{key}_{source}.tgi"] = (   # root folder: loads after every climate's own
                f";; Battleborn: {FOLDER[source]} doodads for {FOLDER[target]} maps (tools/climates.py)\r\n\r\n"
                + "\r\n\r\n".join(things) + "\r\n").encode("latin-1")
        # A doodad with a biome-wide weight scatters on every terrain it does not list, so the
        # target's own grass and flowers filled the ported ground (user 2026-10-29: Barrens ground
        # in Midlands placed grassy doodads). List each ported terrain at weight 0, the way vanilla
        # keeps bushes off its own lakes and roads.
        for d, (f, _, _) in sorted(cl.doodads.items()):
            biomes, pw = cl.effective(d)
            b = biomes.get(target)
            if b is not None and (b["w"] if b["w"] is not None else pw) > 0:
                edits[f] = _exclude(edits.get(f) or _decode(cl.game.get(f)), d, target, new_ids)
        # the target biome: copies after its own terrains, transitions and water
        lines = t.split("\n")
        cr = "\r" if lines[0].endswith("\r") else ""

        def last(pattern):
            return max(i for i, line in enumerate(lines) if re.match(pattern, line, re.I))
        ins = {}
        ins[terrain_lines(lines)[-1]] = [cr, f"\t;; Battleborn climate ports (tools/climates.py){cr}"] + [
            x for n in new_ids for x in (cr, f"\t[Terrain]{cr}", f"\tterrain_IDS = {n}{cr}")]
        ins[last(r"\s*variation_IDS\s*=")] = [x for tr in new_trans for x in (
            cr, f"\t[Transition]{cr}", f"\tterrain1_IDS = {tr['terrain1_ids']}{cr}",
            f"\tterrain2_IDS = {tr['terrain2_ids']}{cr}", f"\tvariation_IDS = {tr['variation_ids']}{cr}")]
        wend = t[:blocks(t, "WaterInfo")[-1][1]].count("\n")
        ins[wend] = [x for w in new_water for x in [cr] + [ln.rstrip("\r") + cr for ln in ("\t" + w.strip()).split("\n")]]
        for at in sorted(ins, reverse=True):
            lines[at + 1:at + 1] = ins[at]
        biome_text[target] = "\n".join(lines)
        out.files[f"Terrain/{target}.tgi"] = biome_text[target].encode("latin-1")
        print(f"{target}: +{len(new_ids)} terrains, +{len(new_trans)} transitions, +{len(new_water)} water")
    for f, text in edits.items():
        bom = cl.game.get(f).startswith(b"\xef\xbb\xbf")
        out.files[f] = (b"\xef\xbb\xbf" + text.encode("utf-8")) if bom else text.encode("latin-1")
    print(f"{len(edits)} native doodad file(s) keep off ported ground")
    return names


def write_strings(names):
    path = os.path.join(REPO, "work", "Localization", "strings_data_K2.tgi")
    raw = open(path, "rb").read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    lines = raw.decode("utf-8-sig").split("\n")
    if MARK_BEGIN in [x.rstrip("\r") for x in lines]:
        a = [x.rstrip("\r") for x in lines].index(MARK_BEGIN)
        b = [x.rstrip("\r") for x in lines].index(MARK_END)
        del lines[a - 1:b + 1]
    cr = "\r" if lines[0].endswith("\r") else ""
    at = max(i for i, x in enumerate(lines) if re.match(r"\tbb_\w+\s*=", x))
    block = ["" + cr, MARK_BEGIN + cr] + [f'\t{k} = "{v}"{cr}' for k, v in sorted(names.items())] + [MARK_END + cr]
    lines[at + 1:at + 1] = block
    text = "\n".join(lines)
    open(path, "wb").write((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))


def clean():
    """Remove this tool's earlier output (work/ and patches/), explicit generated names only."""
    gone = 0
    for top in ("work", "patches"):
        for sub in ("Terrain", "Doodads", "Special"):
            root = os.path.join(REPO, top, sub)
            for dirpath, dirnames, filenames in os.walk(root, topdown=False):
                rel = os.path.relpath(dirpath, root).replace("\\", "/")
                gen_dir = any(p in ("_BB_Frost", "_BB_Cold", "_BB_Autumn", "_BB_Sandy") for p in rel.split("/"))
                for f in filenames:
                    if gen_dir or re.match(r"_BB_\w+\.tgi(\.bbpatch)?$", f):
                        os.remove(os.path.join(dirpath, f))
                        gone += 1
                if gen_dir and not os.listdir(dirpath):
                    os.rmdir(dirpath)
    for dirpath, _, filenames in os.walk(os.path.join(REPO, "work", "Doodads")):
        for f in filenames:
            full = os.path.join(dirpath, f)
            if f.lower().endswith(".tgi") and NO_SCATTER.encode() in open(full, "rb").read():
                rel = os.path.relpath(full, os.path.join(REPO, "work"))
                for p in (full, os.path.join(REPO, "patches", rel) + ".bbpatch"):
                    if os.path.exists(p):
                        os.remove(p)
                        gone += 1
    return gone


def preview(out, folder):
    from PIL import Image, ImageDraw
    os.makedirs(folder, exist_ok=True)
    for look in LOOKS:
        pairs = [p for p in out.pairs if p[0] == look]
        if not pairs:
            continue
        cols, size = 6, 128
        rows = (len(pairs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * (2 * size + 12), rows * (size + 18)), (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        for i, (_, name, a, b) in enumerate(pairs):
            x, y = (i % cols) * (2 * size + 12), (i // cols) * (size + 18)
            for k, data in enumerate((a, b)):
                im = Image.open(io.BytesIO(data)).convert("RGBA")
                bg = Image.new("RGBA", im.size, (90, 90, 90, 255))
                bg.alpha_composite(im)
                sheet.paste(bg.convert("RGB").resize((size, size)), (x + k * size, y))
            d.text((x + 2, y + size + 2), os.path.basename(name)[:40], fill=(230, 230, 230))
        sheet.save(os.path.join(folder, f"{look}.png"))
        print(f"preview {look}: {len(pairs)} textures")


def main():
    ap = argparse.ArgumentParser(description="Battleborn climate ports")
    ap.add_argument("--game")
    ap.add_argument("--preview", help="write before/after contact sheets to this folder and stop")
    args = ap.parse_args()
    game = bb.Game(bb.game_dir(args))
    cl = Climates(game)
    out = Output(cl)
    names = generate(cl, out)
    # The game's fixed-point parser rejects exponent numbers ('weight = 1e-06') and stops loading
    # at that line (0.2.10-dev hidden test, 2026-10-28), so no generated value may use one.
    for rel, data in out.files.items():
        if rel.lower().endswith(".tgi"):
            bad = re.search(rb"=\s*[-+]?[0-9.]+[eE][-+]?[0-9]+\b", data)
            if bad:
                sys.exit(f"{rel}: exponent number '{bad.group().decode()}' would stop the game loading")
    if args.preview:
        preview(out, args.preview)
        return
    print(f"removed {clean()} earlier generated file(s)")
    total = 0
    for rel, data in out.files.items():
        dst = os.path.join(REPO, "work", *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(data)
        if rel in out.deltas:
            blob = bbdelta.make(game.canon(out.deltas[rel]), game.get(out.deltas[rel]), data)
            pd = os.path.join(REPO, "patches", *rel.split("/")) + ".bbdelta"
            os.makedirs(os.path.dirname(pd), exist_ok=True)
            with open(pd, "wb") as f:
                f.write(blob)
            total += len(blob)
    write_strings(names)
    print(f"{len(out.deltas)} textures ({total / 1e6:.1f} MB of deltas), {len(names)} names; running bb.py diff")
    bb.cmd_diff(args)


if __name__ == "__main__":
    main()
