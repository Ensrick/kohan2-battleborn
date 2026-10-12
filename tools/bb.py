"""Battleborn build tool. Standard-library Python 3.8+ only.

Battleborn ships no TimeGate files. Its sources are:
    patches/**.bbpatch   our changes to a game file (game text is referenced, never copied)
    patches/**.bbdelta   art we painted over a game texture, as a delta against it
    original/**          files that are entirely ours
The build reads the player's own Data.rwd, applies the patches, adds our files, and packs
everything into Battleborn.rwd, which the game mounts through a startup script.

    py -3 tools/bb.py build              build/Battleborn.rwd (+ build/Battleborn/ loose copy)
    py -3 tools/bb.py install [--dev]    build, then install into the game folder
    py -3 tools/bb.py uninstall          remove Battleborn from the game folder
    py -3 tools/bb.py status
    py -3 tools/bb.py work               work/<full files> to edit (never commit work/)
    py -3 tools/bb.py diff               turn edits in work/ back into patches/ + original/

Common option: --game "<Kohan II folder>" (default: found through Steam).
--dev also mounts the repo's wip/ folder as loose files above the archive, for art and
data still in progress (wip/ is git-ignored; nothing in it is packed or published).
"""

import argparse
import hashlib
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animations  # noqa: E402
import bbdelta  # noqa: E402
import bbpatch  # noqa: E402
import load_order  # noqa: E402
import rwd      # noqa: E402
import template_fields  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_ID = "97130"
MOD_DIR = "Battleborn"
ARCHIVE = "Battleborn.rwd"
STARTUP = "autoexec_battleborn.txt"
MARKER = "# Battleborn startup script"


# ---------------------------------------------------------------- locating the game

def steam_roots():
    roots = []
    try:
        import winreg
        for hive, key in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                          (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
            try:
                with winreg.OpenKey(hive, key) as k:
                    for name in ("SteamPath", "InstallPath"):
                        try:
                            roots.append(winreg.QueryValueEx(k, name)[0])
                        except OSError:
                            pass
            except OSError:
                pass
    except ImportError:
        pass
    roots.append(r"C:\Program Files (x86)\Steam")
    return [os.path.normpath(r) for r in roots]


def find_game():
    import re
    for root in steam_roots():
        vdf = os.path.join(root, "steamapps", "libraryfolders.vdf")
        libs = [root]
        if os.path.isfile(vdf):
            text = open(vdf, encoding="utf-8", errors="replace").read()
            libs += [p.replace("\\\\", "\\") for p in re.findall(r'"path"\s+"([^"]+)"', text)]
        for lib in libs:
            acf = os.path.join(lib, "steamapps", f"appmanifest_{APP_ID}.acf")
            if os.path.isfile(acf):
                m = re.search(r'"installdir"\s+"([^"]+)"', open(acf, encoding="utf-8", errors="replace").read())
                if m:
                    game = os.path.join(lib, "steamapps", "common", m.group(1))
                    if os.path.isfile(os.path.join(game, "Data.rwd")):
                        return game
    return None


def game_dir(args):
    g = args.game or find_game()
    if not g or not os.path.isfile(os.path.join(g, "Data.rwd")):
        sys.exit("Kohan II not found. Pass --game \"<folder that contains Data.rwd>\".")
    return g


# ---------------------------------------------------------------- sources

def walk(root):
    out = {}
    if not os.path.isdir(root):
        return out
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f in ("Thumbs.db", "Desktop.ini", ".gitkeep"):
                continue
            full = os.path.join(dp, f)
            out[os.path.relpath(full, root).replace(os.sep, "/")] = full
    return out


def sources(public=False):
    """-> {data path: (kind, source file)}; kind = patch | delta | original.

    private/ (git-ignored) holds assets we may not publish - e.g. art containing
    third-party images whose licence is unconfirmed. It has the same patches/ +
    original/ layout and is included unless public=True.
    """
    out = {}
    roots = [REPO] if public else [REPO, os.path.join(REPO, "private")]
    for root in roots:
        for rel, full in walk(os.path.join(root, "patches")).items():
            for ext, kind in ((".bbpatch", "patch"), (".bbdelta", "delta")):
                if rel.endswith(ext):
                    key = rel[:-len(ext)]
                    if key in out:
                        sys.exit(f"{key} has two sources - keep one")
                    out[key] = (kind, full)
        for rel, full in walk(os.path.join(root, "original")).items():
            if rel in out:
                sys.exit(f"{rel} has two sources - keep one")
            out[rel] = ("original", full)
    return out


class Game:
    def __init__(self, folder):
        self.arc = rwd.Archive(os.path.join(folder, "Data.rwd"))
        self.by_name = {e.name.lower(): e for e in self.arc.entries}

    def get(self, name):
        e = self.by_name.get(name.lower())
        return self.arc.read(e) if e else None

    def canon(self, name):
        e = self.by_name.get(name.lower())
        return e.name if e else None


def produce(game, public=False):
    """-> sorted list of (data path, bytes)."""
    files = []
    errors = []
    for rel, (kind, src) in sorted(sources(public).items(), key=lambda kv: kv[0].lower()):
        try:
            if kind == "patch":
                data = bbpatch.apply(open(src, encoding="utf-8", newline="").read(), game.get, rel)
            elif kind == "delta":
                data = bbdelta.apply(open(src, "rb").read(), game.get, rel)
            else:
                data = open(src, "rb").read()
            files.append((rel, data))
        except Exception as ex:  # report every failure, not just the first
            errors.append(f"  {rel}: {ex}")
    if errors:
        sys.exit("Build failed:\n" + "\n".join(errors))
    return files


def write_archive(files, path):
    digest = hashlib.sha256()
    for name, data in files:
        digest.update(name.lower().encode() + b"\0" + data)
    stamp = rwd.default_stamp(digest.digest())
    tmp = path + ".tmp"
    with open(tmp, "wb") as out:
        rwd.write(out, [(n, len(d), (lambda d=d: [d])) for n, d in files], stamp)
    os.replace(tmp, path)
    return stamp


# ---------------------------------------------------------------- commands

def cmd_build(args, quiet=False):
    game = Game(game_dir(args))
    public = getattr(args, "public", False)
    files = produce(game, public)
    problems = (load_order.check(game.arc, files) + template_fields.check(game.arc, files)
                + animations.check(game.arc, files))
    if problems:
        print("data problems (the game crashes or drops these at startup):")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    out_dir =os.path.join(REPO, "build", "public") if public else os.path.join(REPO, "build")
    loose = os.path.join(out_dir, MOD_DIR)
    if os.path.isdir(loose):
        for rel, full in walk(loose).items():       # clear the previous loose copy, file by file
            os.remove(full)
    for name, data in files:
        dst = os.path.join(loose, *name.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(data)
    path = os.path.join(out_dir, ARCHIVE)
    stamp = write_archive(files, path)
    if not quiet:
        print(f"built {path}: {len(files)} files, stamp {stamp:08x}")
    return path, stamp


def startup_script(dev):
    # k2.exe runs every startup/autoexec*.txt in name order, after autoexec.txt has mounted
    # Data.rwd. 'addmod' is 'adddepot' plus the engine's mod flag: at the same priority (0) the
    # later depot wins, the archive stamp joins the multiplayer depot checksums, and the depot
    # is listed in the multiplayer mods list (mismatch = "wrong mods" disconnect). The
    # Documents\Kohan2\data depot (priority 1) still overrides everything here.
    lines = [
        MARKER + " - written by kohan2-battleborn tools/bb.py; delete it (or run bb.py uninstall) to disable.",
        f"addmod {MOD_DIR}/{ARCHIVE}",
    ]
    if dev:
        # Loose work-in-progress files, mounted last at priority 0 so they override the archive
        # without becoming the game's work depot (that stays Documents\Kohan2\data).
        wip = os.path.join(REPO, "wip").replace("\\", "/").rstrip("/") + "/"
        lines += ["# Developer mode: wip/ overrides the archive (its path also makes MP checksums differ).",
                  f"adddepot {wip}"]
    return "\r\n".join(lines) + "\r\n"


def cmd_install(args):
    g = game_dir(args)
    path, stamp = cmd_build(args, quiet=True)
    dst_dir = os.path.join(g, MOD_DIR)
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copyfile(path, os.path.join(dst_dir, ARCHIVE))
    if args.dev:
        os.makedirs(os.path.join(REPO, "wip"), exist_ok=True)
    script = os.path.join(g, "startup", STARTUP)
    with open(script, "w", encoding="ascii", newline="") as f:
        f.write(startup_script(args.dev))
    a = rwd.Archive(os.path.join(dst_dir, ARCHIVE))
    print(f"installed {len(a.entries)} files into {dst_dir}\\{ARCHIVE} (stamp {stamp:08x})")
    print(f"startup script {script}" + (" (dev: wip/ mounted)" if args.dev else ""))


def cmd_uninstall(args):
    g = game_dir(args)
    script = os.path.join(g, "startup", STARTUP)
    removed = []
    if os.path.isfile(script):
        if not open(script, encoding="ascii", errors="replace").read().startswith(MARKER):
            sys.exit(f"{script} was not written by Battleborn - left alone")
        os.remove(script)
        removed.append(script)
    arc = os.path.join(g, MOD_DIR, ARCHIVE)
    if os.path.isfile(arc):
        os.remove(arc)
        removed.append(arc)
    d = os.path.join(g, MOD_DIR)
    if os.path.isdir(d) and not os.listdir(d):
        os.rmdir(d)
    print("removed:\n  " + "\n  ".join(removed) if removed else "Battleborn was not installed")


def cmd_status(args):
    g = game_dir(args)
    script = os.path.join(g, "startup", STARTUP)
    arc = os.path.join(g, MOD_DIR, ARCHIVE)
    print(f"game folder   {g}")
    print(f"startup       {'present' if os.path.isfile(script) else 'missing'}  {script}")
    if os.path.isfile(arc):
        a = rwd.Archive(arc)
        print(f"archive       {len(a.entries)} files, stamp {a.stamp:08x}  {arc}")
    else:
        print(f"archive       missing  {arc}")
    if os.path.isfile(script) and "wip/" in open(script, encoding="ascii", errors="replace").read():
        print("dev mode      wip/ mounted")


def cmd_work(args):
    game = Game(game_dir(args))
    work = os.path.join(REPO, "work")
    n = 0
    for name, data in produce(game):
        dst = os.path.join(work, *name.split("/"))
        if os.path.isfile(dst) and open(dst, "rb").read() != data and not args.force:
            print(f"kept your edited {name} (use --force to overwrite)")
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as f:
            f.write(data)
        n += 1
    print(f"work/ has {n} full files to edit; run 'bb.py diff' afterwards. Never commit work/.")


def cmd_diff(args):
    game = Game(game_dir(args))
    work = walk(os.path.join(REPO, "work"))
    src = sources()
    index = None
    changed = 0
    for rel, full in sorted(work.items(), key=lambda kv: kv[0].lower()):
        data = open(full, "rb").read()
        kind, srcfile = src.get(rel, (None, None))
        if kind == "original":
            if open(srcfile, "rb").read() != data:
                shutil.copyfile(full, srcfile)
                changed += 1
            continue
        if kind == "delta":
            meta, _ = bbdelta.read_meta(open(srcfile, "rb").read())
            if bbdelta.apply(open(srcfile, "rb").read(), game.get, rel) != data:
                with open(srcfile, "wb") as f:
                    f.write(bbdelta.make(meta["base"], game.get(meta["base"]), data))
                changed += 1
            continue
        if kind == "patch":
            old = open(srcfile, encoding="utf-8", newline="").read()
            if bbpatch.apply(old, game.get, rel) == data:
                continue
            meta, _ = bbpatch.parse(old)
            base_name = meta["base"][0] if meta["base"] else None
        else:
            base_name = game.canon(rel)
            if base_name is None and os.path.splitext(rel)[1].lower() not in (".tgi", ".txt"):
                dst = os.path.join(REPO, "original", *rel.split("/"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copyfile(full, dst)
                print(f"new original art {rel} - if it was painted over a game texture, run "
                      f"'bb.py derive {rel} <game texture>' instead")
                changed += 1
                continue
        if index is None:
            index = bbpatch.RefIndex()
            for e in game.arc.entries:
                if os.path.splitext(e.name)[1].lower() in (".tgi", ".txt"):
                    index.add(e.name, game.arc.read(e))
        base = game.get(base_name) if base_name else None
        text = bbpatch.make(base_name, base, data, index)
        dst = os.path.join(REPO, "patches", *rel.split("/")) + ".bbpatch"
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        changed += 1
    gone = [rel for rel in src if rel not in work]
    if work and gone:
        print("in patches/original but not in work/ (delete them from the repo if intended):")
        for rel in gone:
            print("  " + rel)
    print(f"{changed} source file(s) updated")


def cmd_derive(args):
    game = Game(game_dir(args))
    base = game.get(args.base)
    if base is None:
        sys.exit(f"{args.base} not in Data.rwd")
    full = os.path.join(REPO, "work", *args.path.split("/"))
    blob = bbdelta.make(game.canon(args.base), base, open(full, "rb").read())
    dst = os.path.join(REPO, "patches", *args.path.split("/")) + ".bbdelta"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as f:
        f.write(blob)
    orig = os.path.join(REPO, "original", *args.path.split("/"))
    if os.path.isfile(orig):
        os.remove(orig)
    print(f"{args.path} now ships as a delta against {args.base}")


def cmd_package(args):
    """build/<id>-<version>.k2mod for the Kohan II Mod Manager: mod.json, original/ as files/,
    patches/ as-is. Public sources only (private/ never ships). Deterministic: same sources,
    same bytes."""
    import json
    import zipfile
    meta = json.load(open(os.path.join(REPO, "mod.json"), encoding="utf-8"))
    out = os.path.join(REPO, "build", f"{meta['id']}-{meta['version']}.k2mod")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    entries = [("mod.json", os.path.join(REPO, "mod.json"))]
    entries += [("files/" + rel, full) for rel, full in sorted(walk(os.path.join(REPO, "original")).items(), key=lambda kv: kv[0].lower())]
    entries += [("patches/" + rel, full) for rel, full in sorted(walk(os.path.join(REPO, "patches")).items(), key=lambda kv: kv[0].lower())]
    tmp = out + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, full in entries:
            info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, open(full, "rb").read())
    os.replace(tmp, out)
    print(f"wrote {out}: {len(entries) - 1} files; install it with K2ModManager.exe (or k2mod install)")


def main():
    ap = argparse.ArgumentParser(description="Battleborn build tool")
    ap.add_argument("--game", help="Kohan II folder (default: found through Steam)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("build")
    p.add_argument("--public", action="store_true", help="leave out private/ (what a release would contain)")
    p = sub.add_parser("install")
    p.add_argument("--dev", action="store_true")
    sub.add_parser("uninstall")
    sub.add_parser("status")
    p = sub.add_parser("work")
    p.add_argument("--force", action="store_true")
    sub.add_parser("diff")
    p = sub.add_parser("derive", help="ship work/<path> as a delta against a game texture")
    p.add_argument("path")
    p.add_argument("base")
    sub.add_parser("package", help="build/<id>-<version>.k2mod for the Kohan II Mod Manager")
    args = ap.parse_args()
    {"build": cmd_build, "install": cmd_install, "uninstall": cmd_uninstall, "status": cmd_status,
     "work": cmd_work, "diff": cmd_diff, "derive": cmd_derive, "package": cmd_package}[args.cmd](args)


if __name__ == "__main__":
    main()
