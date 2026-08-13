# Battleborn (BB) - a Kohan II: Kings of War mod

Gameplay overhaul for Kohan II: Kings of War v1.2.3 (Steam). Unit renames and rebalances
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
| `tools/deploy.ps1` | Repo `Data/` -> game `Data\`. Copy-only, never deletes. |
| `tools/third_party/` | `K2ExtractRWD.zip` - the community `Data.rwd` extractor (hard to find; archived here). Not game material; fan-made tool. |

`Data/` and `workbench/` overlap and had drifted apart in the game install; both were
captured verbatim at import. Reconciling them into a single source of truth is pending.

## Workflow

1. Edit in the game install (either `Data\` directly or `Data (Mod)\` workbench).
2. `tools\collect.ps1` to pull gameplay changes into the repo.
3. Update `CHANGELOG.md`, commit, and push (origin pushes to **both** GitHub and GitLab).

Or edit in the repo and run `tools\deploy.ps1` to push `Data/` into the game.

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
