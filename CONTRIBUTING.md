# Contributing

## Setup

1. Kohan II: Kings of War v1.2.3 (Steam), default install at
   `C:\Program Files (x86)\Steam\steamapps\common\Kohan II` (both tools take a
   `-GameDir` override).
2. The game loads loose files in `Data\` over the `Data.rwd` archive, no repack needed.
   To browse vanilla data, extract `Data.rwd` with `tools/third_party/K2ExtractRWD.zip`
   into a `Data (Backup)\` folder next to the game's `Data\` - `collect.ps1` uses it as
   the diff baseline.

## Workflow

1. Edit files in the repo and run `tools\deploy.ps1`, or edit in the game's `Data\` /
   `Data (Mod)\` folders and run `tools\collect.ps1` to pull changes back.
2. Test in-game before committing gameplay changes.
3. Update `CHANGELOG.md` under `[Unreleased]` in the same commit.
4. Push. Pull requests and issues live on GitHub; the GitLab remote is a mirror.

## Rules

- **Only new or modified override files.** Never commit unmodified game data, the
  `.rwd` archives, or the game executable.
- **Stay in scope.** Display and modern-Windows compatibility files (`UI/`, `Fonts/`,
  `AVars.tgi`, `UVars.tgi`, `strings_rtse_ui.tgi`) belong in the
  [kohan2-widescreen](https://github.com/Ensrick/kohan2-widescreen) repo; `collect.ps1`
  skips them here.
- When changing a vanilla value in a `.tgi`, keep the original as a trailing comment
  (existing style: `int Entries = 1240 ;; 120`).
- New/renamed strings go through `Localization/_BB_Strings.tgi` with the `bb_` prefix;
  new properties through `Properties/_BB_Properties.tgi`.
