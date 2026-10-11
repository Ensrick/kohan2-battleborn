# Battleborn (BB) - a Kohan II: Kings of War mod

Gameplay overhaul for Kohan II: Kings of War (Steam; retail data, runs on the Modern
Rebuild exe). Unit renames and rebalances across all six factions, settler-company flank
slots, militia companies, settlement and town-center tuning, out-of-town economy outposts,
new captains and commanders, and reworked unit icons, portraits, and skins.

**This repository contains no TimeGate game files.** Battleborn is stored as *changes*:
the installer reads your own copy of the game's `Data.rwd`, applies Battleborn's changes,
and packs the result into `Battleborn.rwd`, which the game loads as a mod.

## Install

1. Download this repository (or a release zip) anywhere.
2. Double-click `Install-Battleborn.cmd` (or right-click `Install-Battleborn.ps1` >
   *Run with PowerShell*). It finds Kohan II through Steam; pass
   `-GameDir "<folder with Data.rwd>"` if it cannot.
3. Start Kohan II through Steam as usual.

It writes two files into the game folder: `Battleborn\Battleborn.rwd` and
`startup\autoexec_battleborn.txt`. Uninstall with `Install-Battleborn.ps1 -Uninstall`
(or delete those two files). Nothing else in the install is touched, and Windows
PowerShell 5.1 (built into Windows) is all it needs.

**Multiplayer:** the game loads Battleborn with its own `addmod` command, so the archive
joins the connection checksums and the mods list - players with a different Battleborn
build (or none) are refused at connect instead of desyncing mid-game. Every player needs
the same Battleborn version.

**Other gameplay mods:** files in `Documents\Kohan2\data` override everything, so a
second overhaul installed there (for example Immortals) will override Battleborn file by
file. Use one at a time.

## How the mod is stored

| Path | What it is |
|---|---|
| `patches/**.bbpatch` | Our changes to a game file, or a new file built from a game file. Contains only Battleborn's own lines; game text is *referenced* (`= Units/Haroun/windrider.tgi 104-106`), never copied, and removed lines appear only as a count and a hash. Each patch is pinned to the SHA-256 of the retail file it targets. |
| `patches/**.bbdelta` | Art painted over a game texture, stored as a delta against that texture. Unreadable without your own `Data.rwd`. |
| `original/` | Files that are entirely ours (namelists, the Battleborn properties file). |
| `mod.json` | Name, version and rules (incompatible with Immortals) for the Kohan II Mod Manager package. |
| `maps/` | Authored test maps (`.RMP`). |
| `Install-Battleborn.ps1` / `.cmd` | Player installer (PowerShell only). |
| `tools/bb.py` | Developer tool: build, install, `work` / `diff` editing workflow. |
| `tools/rwd.py` | Reader/writer for Kohan II `.rwd` archives (format notes in the file). |
| `tools/bbpatch.py`, `tools/bbdelta.py` | The patch and delta formats. |
| `tools/validate.py` | Reference check of a build: unresolved IDs, missing strings and art, duplicate IDs. |
| `tools/load_order.py` | Load-order check, run by every build: no ID used before the file that defines it loads. |
| `tools/audit_public.py` | Publication check: no file or run of 4+ lines matches game data. |
| `tools/bb_import.py` | Converts full-file overrides into patches (used once to migrate). |

## Developing

Requires Python 3.8+ (standard library only).

```
py -3 tools/bb.py work                # work/ = full, editable files (never commit work/)
  ... edit files in work/ ...
py -3 tools/bb.py diff                # turn your edits back into patches/ and original/
py -3 tools/bb.py install             # build + install into the game
py -3 tools/bb.py install --dev       # same, plus wip/ mounted as loose files on top
py -3 tools/bb.py package             # build/battleborn-<version>.k2mod for the Kohan II Mod Manager
py -3 tools/validate.py --vanilla "<Data.rwd extract>" --mod build/Battleborn
py -3 tools/audit_public.py           # before every push
```

- New art painted over a game texture: put it in `work/`, then
  `py -3 tools/bb.py derive <path> <game texture path>` so it ships as a delta.
  New art drawn from scratch goes to `original/` automatically on `diff`.
- `wip/` (git-ignored) is for work in progress: with `install --dev` its loose files
  override the archive, so unfinished art and data can be tried in-game without packing.
  Move them into the sources when ready.
- `private/` (git-ignored) uses the same `patches/` + `original/` layout for material
  that must not be published (for example art containing third-party images whose
  licence is unconfirmed). `bb.py` includes it in local builds; `bb.py build --public`
  shows what a release contains.

## How the game loads it (reverse-engineered from k2.exe)

- The exe runs every `startup/autoexec*.txt` at launch, in name order, after
  `autoexec.txt` has mounted `Data.rwd`.
- `addmod <path>` is `adddepot` plus the engine's mod flag. Depots are ranked by priority,
  and at equal priority the later one wins, so `Battleborn.rwd` (priority 0) overrides
  `Data.rwd`; `Documents\Kohan2\data` (priority 1) overrides both.
- The multiplayer handshake lists every priority-0 depot with the stamp in its archive
  header, and separately the mod depots; a mismatch disconnects with "bad depot
  checksums" / "wrong mods".

## License & content policy

Everything in this repository is original work, MIT-licensed - see `LICENSE`. It contains
no TimeGate game data: no `.tgi` or texture copies, no `.rwd` archives, no executable.
Patches reference the player's own game files, which remain the property of TimeGate
Studios and its successors.

## Remotes

Mirrored for redundancy - a single `git push` updates both:

- GitHub: `github.com/Ensrick/kohan2-battleborn` (fetch + push)
- GitLab: `gitlab.com/ensrick7/kohan2-battleborn` (push mirror)
