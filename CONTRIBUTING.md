# Contributing

## Setup

1. Kohan II: Kings of War on Steam (the retail `Data.rwd` is the base every patch targets).
2. Python 3.8+ for the developer tools (standard library only). Players need only
   `Install-Battleborn.ps1`.

## Workflow

1. `py -3 tools/bb.py work` - writes full, editable files to `work/`.
2. Edit in `work/`. Keep vanilla values you change as a trailing comment
   (existing style: `health = 220 ;; lich 80`).
3. `py -3 tools/bb.py diff` - turns the edits back into `patches/` and `original/`.
4. `py -3 tools/bb.py install` and test in-game.
5. `py -3 tools/audit_public.py` must report 0 findings.
6. Update `CHANGELOG.md` under `[Unreleased]` in the same commit, then push (one push
   updates GitHub and GitLab).

## Rules

- **Never commit game files or anything built from them.** `work/`, `build/`, `wip/` and
  `private/` are git-ignored for that reason. The sources are patches (our lines only),
  deltas (art painted over a game texture) and files that are entirely ours.
- **Art painted over a game texture** ships as a delta: `bb.py derive <path> <game texture>`.
- **Third-party images** (stock icons, downloaded pictures) need a licence that allows
  redistribution under this repo's terms. Until that is confirmed, keep the asset in
  `private/`.
- **Stay in scope.** Display and modern-Windows compatibility work (`UI/`, `Fonts/`,
  `AVars.tgi`, `UVars.tgi`, `strings_rtse_ui.tgi`) belongs in the
  [kohan2-widescreen](https://github.com/Ensrick/kohan2-widescreen) repo.
- New strings use the `bb_` prefix; new properties go in `Properties/_BB_Properties.tgi`.
