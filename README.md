# Battleborn (BB) - a Kohan II: Kings of War mod

Gameplay and UI overhaul for Kohan II: Kings of War v1.2.3 (Steam). Unit renames and
rebalances across all six factions, settler-company flank slots, militia companies, and a
4K (3840x2160) UI rebuild with hand-upscaled interface assets.

## Repo layout

| Path | What it is |
|---|---|
| `Data/` | The live loose-file override depot. Mirrors the game's `Data\` folder, which the engine mounts on top of `Data.rwd` (see `startup\autoexec.txt`: `adddepot data.rwd` then `adddepot data/`). This is what "ships". |
| `workbench/` | Full working tree: every file in the game's `Data (Mod)\` extract that differs from the pristine `Data (Backup)\` extract - new files, size changes, and equal-size content changes. Includes `__GIMP FILES\` art sources for the 4K UI work. |
| `maps/` | Authored test maps from `Documents\Kohan2\data\Maps`. |
| `ce/` | Cheat Engine table (`k2.exe`-relative addresses): render scaling, camera zoom, minimap colors, plus unidentified probes. From `D:\Game Mods\Kohan II Kings of War\`. |
| `tools/third_party/` | `K2ExtractRWD.zip` - the community `Data.rwd` extractor (hard to find; archived here). |
| `tools/collect.ps1` | Game install -> repo. Re-run after editing in the game folders, then commit. |
| `tools/deploy.ps1` | Repo `Data/` -> game `Data\`. Copy-only, never deletes. |
| `docs/WIDESCREEN.md` | State of the 4K/widescreen effort and engine findings. |

`Data/` and `workbench/` overlap (e.g. `UI/resolution.tgi` exists in both) and had drifted
apart in the game install; both were captured verbatim at import. Reconciling them into a
single source of truth is pending.

## Workflow

1. Edit in the game install (either `Data\` directly or `Data (Mod)\` workbench).
2. `tools\collect.ps1` to pull changes into the repo.
3. Commit and push (origin pushes to **both** GitHub and GitLab).

Or edit in the repo and run `tools\deploy.ps1` to push `Data/` into the game.

## Game-side folders (not in the repo)

- `Data (Backup)\` - pristine extract of `Data.rwd` (367 MB). Regenerate with the game's
  `K2ExtractRWD.exe`; it is the diff baseline for `collect.ps1`.
- `Data (Mod)\` - the workbench extract (`Data (Backup)` + modifications).
- `Documents\Kohan2\data\` - highest-priority user depot (`adddepot %USERDATA%/data/ 1`);
  also holds saves and preferences.

## Remotes

Mirrored for redundancy - a single `git push` updates both:

- GitHub: `github.com/Ensrick/kohan2-battleborn` (fetch + push)
- GitLab: `gitlab.com/ensrick7/kohan2-battleborn` (push mirror)
