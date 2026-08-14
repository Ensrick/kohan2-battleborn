# Changelog

All notable changes to the Battleborn mod. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Six faction commanders from the design sheet (2026-08-14): Templar
  (Nationalist, Ghalen model), Harbinger (Ceyah, Stonewalker), Warder
  (Council ranged), Rune Lord (Council, Gauri Hammer ram-rider), Mage Lord
  (Council, Ravid Sakeri model with protection spells), Necromancer (Undead,
  Lich model with summon_undead spells). All on placeholder art (CHECKLIST
  10a); unnamed faction commander tiers await the naming worksheet
  (CHECKLIST 13a).
- Seven new/completed units (2026-08-14): Ranger Sergeant (bowman captain on
  the Aethan Farhyd hero skin), Marksman (elite ranged support), Cavalry
  Sergeant (rebuilt from the broken stub), Engineer Sergeant + Siege Expert
  (engineer-line captain/support with builder and boosted repair/siege), and
  the Royalist Knight (front/flank) + Champion (captain) around the Paladin.
  All ship on placeholder/vanilla art - see CHECKLIST section 10a for the
  texture-map debt tracker.
- Out-of-town economy outposts for ALL SIX factions: buildable woodmill outpost
  upgrading into sawmill / woodmarket variants (3x in-town cost, 2/3 output,
  capturable + razable, faction outpost-style garrisons, no research trees).
  Builder overrides: Human engineer, Drauga crafter, Gauri forge, Haroun
  caretaker, Shadow nightbringer, Undead boneweaver. Guards follow the
  structure-flavor doctrine: each faction's hunter/ranged unit x8 (bowman /
  impaler / spear / rainbringer / fury / bone archer) + its workers, staying
  strictly weaker than military outposts and forts. All 18 buildings draw
  random names from dedicated new per-structure namelists (18 lists x 50
  names, matching the fort lists' size, in each faction's naming style -
  e.g. Gauri "Torg" markets, Haroun "Minshar" sawmills, Undead "Bonesaw
  Mill" / "Ashen Tithe"; built from the vanilla outpost/settlement name
  pools plus authored additions).

### Fixed
- All dangling references (2026-08-13 breakage pass): pioneer's captain slot typo
  (`bb_pioneer_captain` -> `bb_captain_pioneer`), Infantry/Ranger Captain portrait wiring
  (skin paths + `portrait_ids`), Infantry Sergeant art refs, Praetorian/captain/militia
  name keys re-pointed at defined `bb_` loc keys (+ new "Zombie Militia"/"Hobilar
  Militia" strings), Haroun city hillstrider 24 -> 1 and Undead village unit cap 2 -> 7
  (per design-doc targets).

### Changed
- Commander cost balance (2026-08-14): politics commanders priced at the
  politics-support gold tier plus a captain premium, with mana upkeep
  scaling to casting power (native captains are free in vanilla; Shadow
  specials set the unique-resource precedent). Storm Lord 24->28g +mana 2,
  Templar 28g, Warder 30g, Rune Lord 32g, Mage Lord 32g +mana 2,
  Necromancer mana 3 summoner tax.
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
