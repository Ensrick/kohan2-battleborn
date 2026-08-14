# Changelog

All notable changes to the Battleborn mod. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Out-of-town economy pilot completed: the woodmill outpost is now buildable
  (engineer `BuilderComponent` override) and upgrades into new
  `bb_human_sawmill_outpost` / `bb_human_woodmarket_outpost` (3x cost, 2/3 output,
  capturable + razable, no research trees).

### Fixed
- All dangling references (2026-08-13 breakage pass): pioneer's captain slot typo
  (`bb_pioneer_captain` -> `bb_captain_pioneer`), Infantry/Ranger Captain portrait wiring
  (skin paths + `portrait_ids`), Infantry Sergeant art refs, Praetorian/captain/militia
  name keys re-pointed at defined `bb_` loc keys (+ new "Zombie Militia"/"Hobilar
  Militia" strings), Haroun city hillstrider 24 -> 1 and Undead village unit cap 2 -> 7
  (per design-doc targets).

### Changed
- `workbench/` is now the single source of truth; `Data/` rebuilt as the curated
  deployable superset (95 files, reference-verified; stub units and orphaned art
  excluded). Reconciled bidirectional drift (Drauga settler, pilgrim flank + costs).
- Localization consolidated on the full-file `strings_data_K2.tgi` override;
  `_BB_Strings.tgi` retired with its 10 unique keys merged in.
- Split display/compat work (UI, Fonts, AVars/UVars, strings_rtse_ui.tgi, UI GIMP
  sources, CE table) into the companion
  [kohan2-widescreen](https://github.com/Ensrick/kohan2-widescreen) repo; `collect.ps1`
  now skips those paths.

## [0.1.0] - 2026-08-13

Initial import of the October 2024 working files from the game install.

### Added
- Unit renames via `_BB_Strings.tgi` (Cavalry Captain/Cataphract/Cavalier, Myrmidon,
  Footman, Praetorian, Halberdier, Storm Guard line, and more) across Human, Council,
  and militia rosters.
- Settler-company flank slot (`bb_settler_flank` property, `company_settler` layout)
  and Siege Militia company.
- Unit stat tweaks across all factions (settlers/founders/pilgrims/pioneers/boneweavers,
  Human roster, Undead zombie/bone golem, Gauri juggernaut/maelstrom, Haroun
  hillstrider, Shadow leviathan, Council eben_baruch).
- Settlement, town-center (village/town/city/citadel for all six factions), fort, and
  outpost tuning; kingdom colors; scenario/RTSE string edits.
- Reworked banner icons, unit icons, portraits, and skins with GIMP sources in
  `workbench/__GIMP FILES/`.
- Authored test maps (`BB_Test_2`, `TEST`, `Trial Map Human`).
- `tools/collect.ps1` / `tools/deploy.ps1` sync scripts.
