# Battleborn (BB) - a Kohan II: Kings of War mod

Gameplay overhaul for Kohan II: Kings of War (Steam; retail v1.2.3 data, runs on the
Modern Rebuild beta exe, which leaves `Data.rwd` untouched). Unit renames and rebalances
across all six factions, settler-company flank slots, militia companies, settlement and
town-center tuning, and reworked unit icons, portraits, and skins.

Display and modern-Windows work (3840x2160 mode, 4K UI, Win11 font crash fix) lives in
the companion repo [kohan2-widescreen](https://github.com/Ensrick/kohan2-widescreen);
that repo owns `UI/`, `Fonts/`, `AVars.tgi`, `UVars.tgi`, and `strings_rtse_ui.tgi`.

## Repo layout

| Path | What it is |
|---|---|
| `Data/` | Live loose-file override depot (gameplay files). The engine mounts it on top of `Data.rwd` (see `startup\autoexec.txt`: `adddepot data.rwd` then `adddepot data/`). This is what "ships". |
| `workbench/` | Full working tree: every gameplay file in the game's `Data (Mod)\` extract that differs from the pristine `Data (Backup)\` extract. Includes `__GIMP FILES\` art sources for icons, portraits, and skins. |
| `maps/` | Authored test maps from `Documents\Kohan2\data\Maps`. |
| `tools/collect.ps1` | Game install -> repo (skips widescreen-owned paths). Re-run after editing in the game folders, then commit. |
| `tools/deploy.ps1` | Repo `Data/` -> user depot `Documents\Kohan2\data\` (priority 1), tracked by a SHA256 manifest in `Documents\Kohan2\battleborn_manifest.txt`. Re-run after edits; `-Uninstall` removes it; `-WhatIf` previews. Stops instead of overwriting files another gameplay mod owns. |
| `tools/validate.py` | Offline reference check: overlays `Data/` on a pristine `Data.rwd` extract and reports unresolved `*_ids`, missing `#loc` keys, missing art paths, and duplicate top-level IDs. `py -3 tools/validate.py --vanilla "<Data (Backup) path>"` |
| `tools/third_party/` | `K2ExtractRWD.zip` - the community `Data.rwd` extractor (hard to find; archived here). Not game material; fan-made tool. |

`Data/` and `workbench/` overlap and had drifted apart in the game install; both were
captured verbatim at import. Reconciling them into a single source of truth is pending.

## Workflow

1. Edit in the repo's `Data/`.
2. `py -3 tools/validate.py --vanilla "<Data (Backup) path>"` - must report 0 problems.
3. `tools\deploy.ps1` to install into the user depot, then launch the game.
4. Update `CHANGELOG.md`, commit, and push (origin pushes to **both** GitHub and GitLab).

Battleborn installs into the user depot, not the Steam folder, so the install stays
byte-exact to Steam's depot. Only one gameplay mod can live in that depot at a time:
another overhaul there (for example the Immortals MP balance mod) overrides the same
town-center, unit and fort files, so uninstall it first - `deploy.ps1` refuses to mix
them. The multiplayer handshake checksums `Data.rwd`/`Music.rwd` but not the user
depot, so a gameplay-mod mismatch is not caught at connect; uninstall Battleborn
before joining games that run something else.

`tools\collect.ps1` is the legacy path (game `Data\` / `Data (Mod)\` -> repo) from
before the depot install; it is copy-only and harmless, but the repo is now the
source of truth.

## Game-side folders (not in the repo)

- `Data (Backup)\` - pristine extract of `Data.rwd` (367 MB). Regenerate with
  `K2ExtractRWD.exe`; it is the diff baseline for `collect.ps1`.
- `Data (Mod)\` - the workbench extract (`Data (Backup)` + modifications).
- `Documents\Kohan2\data\` - highest-priority user depot (`adddepot %USERDATA%/data/ 1`);
  also holds saves and preferences.

## License & content policy

Original work in this repository (scripts, docs, and authored art sources) is
MIT-licensed - see `LICENSE`.

Modified game-data files (`.tgi` overrides and textures derived from the game's art) are
derivative works of Kohan II: Kings of War, included solely so the mod functions; all
rights to the underlying game content remain with TimeGate Studios and its successors.
This repository never contains unmodified game data, the `Data.rwd` / `Music.rwd`
archives, or the game executable.

## Remotes

Mirrored for redundancy - a single `git push` updates both:

- GitHub: `github.com/Ensrick/kohan2-battleborn` (fetch + push)
- GitLab: `gitlab.com/ensrick7/kohan2-battleborn` (push mirror)
