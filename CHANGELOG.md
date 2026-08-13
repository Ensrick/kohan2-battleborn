# Changelog

All notable changes to the Battleborn mod. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Changed
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
