# Changelog

All notable changes to the Battleborn mod. Format follows
[Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Fixed
- **Startup crash (0.2.1-dev, 2026-10-11):** "`_BB_Front_Ranger.tgi`: Could not find vfx
  data: ranger_sword_effect" (log-246, first in-game run of the archive). The game reads
  `_BB_` files before the stock files of the same folder, so the Front Ranger used the
  ranger effects before `ranger.tgi` defined them. It now has its own copies
  (`bb_front_ranger_*_effect`). Same cause, warning only: the Ranger Sergeant, Mage Lord
  and Templar captains referenced hero portraits defined in later-loaded files and showed
  none; each now defines its own portrait entry on the same game art.
- **Startup crash (0.2.2-dev, 2026-10-11):** "Field 'key_ratio' missing from node using
  strict template: `_BB_Captain_Necromancer.tgi`/.../Animation" (log-247). The
  Necromancer's cast animation (AbilityAnimation, which declares `key_ratio` without a
  default) lost the `key_ratio = 0.6` the stock Lich sets.
- **Startup crash (0.2.3-dev):** "Unknown idle animation 'idlecast' loading actor
  'bb_captain_council_swordsman'" (log-248). Its lightning spells (K2SpellInstantLocal)
  play `cast` and idle on `idlecast`, which the unit never defined; the Spellsword support
  (storm_shield spells) had the same gap. Both now define Ghalen Mordecai's cast and
  idlecast animations, whose model they use.
- **Startup crash (0.2.4-dev):** "Field not found in template. Expression: 'can_raze'"
  (log-250, Drauga woodmill outpost). In all six woodmill outposts `can_raze = true` sat
  after the brace-less `[Upgrade]` entries, so the game read it as part of the last
  `[Upgrade]`. It now comes first in `[ConstructionComponent]`.
- **0.2.4-dev reaches the main menu** with Battleborn loaded (log-251, log-252); its new
  warnings are display-name duplicates only (the outposts reuse stock building names).

### Changed
- **No game files in the repository any more (2026-10-10).** Battleborn is now stored
  as changes: `patches/*.bbpatch` hold only our lines (game text is referenced by file
  and line range, removed lines appear as a count and hash, each patch is pinned to the
  retail file's SHA-256), `patches/*.bbdelta` hold art painted over game textures as
  deltas, and `original/` holds files that are entirely ours. All 155 previous override
  files rebuild byte-identical from the retail `Data.rwd`. The old `Data/` and
  `workbench/` copies were removed from the repository (kept locally).
- **Installs as an archive the game loads as a mod.** `Battleborn\Battleborn.rwd` plus
  `startup\autoexec_battleborn.txt` (`addmod Battleborn/Battleborn.rwd`). Reverse-
  engineered from k2.exe: startup scripts glob `startup/autoexec*.txt`; `addmod` is a
  mod-flagged depot; equal-priority depots resolve last-added-wins; the multiplayer
  handshake checksums priority-0 depots by archive stamp and compares mod lists, so a
  Battleborn mismatch is refused at connect. Builds are deterministic, so every player's
  archive (and stamp) is identical.
- High-resolution icon and portrait art (banner icons, Pikeman/Pioneer/Swordsman
  icons, Infantry/Ranger Captain icons and portraits) moved out of Battleborn into a
  separate, unpublished art project (2026-10-11). The two captains now use the game's
  Ghalen Mordecai and Eben Baruch icon and portrait under their own file names, so a
  later art pack can replace them without touching Battleborn's data.
- `tools/deploy.ps1` (loose-file install) and `tools/collect.ps1` (harvested full
  copies) retired; `tools/gen_namelists.ps1` moved out of the repository because it
  embedded name pools harvested from the game's namelists.

### Added
- `tools/load_order.py`, run by every `bb.py build` (2026-10-11): fails the build when a mod
  file uses an effect, portrait or other load-time ID that only a later-loaded file defines
  (game load order simulated from `index_k2.lst`, vanilla's own forward references as
  baseline).
- `tools/template_fields.py`, also run by every `bb.py build`: fails when a node leaves out
  a field its template declares without a default, or sets a field no definition of that
  node declares (schema = the node's template chain, the same-named component template and
  the sub-node its parent's definitions declare; vanilla: 4 such fields, 0 required misses).
- `tools/animations.py`, also run by every build: every animation an ability plays or idles
  on (including template defaults) must exist on the actor (vanilla: 0 misses).
- `mod.json` and `bb.py package`: builds `build/battleborn-<version>.k2mod` for the Kohan II
  Mod Manager (public sources only, deterministic). The manager rebuilds it byte-identical
  to `bb.py build --public`.
- `Install-Battleborn.ps1` / `.cmd` (2026-10-10): player installer needing only Windows
  PowerShell 5.1; builds the same archive byte-for-byte as the developer tools.
- `tools/bb.py` (build / install / uninstall / status / work / diff / derive),
  `tools/rwd.py` (`.rwd` reader/writer, verified by rebuilding Data.rwd, Music.rwd and
  Warchest.rwd byte-for-byte), `tools/bbpatch.py`, `tools/bbdelta.py`,
  `tools/audit_public.py` (fails on any file or 4+ line run matching game data),
  `tools/bb_import.py` (full-file overrides -> patches).
- `tools/validate.py` offline reference checker (2026-10-10): unresolved `*_ids`,
  missing loc keys, missing art paths and duplicate top-level IDs against a
  pristine `Data.rwd` extract, with vanilla's own dead references as baseline.
  Full build (155 files): 0 problems.
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

### Added
- Nine sheet-named units (2026-08-15), completing every named non-art-gated
  roster row: Human Skirmisher (T2 bowman support, archer_foe aura), Lancer
  support (T2 cavalry, recon+archer_foe), Ranger front/flank (T3, magic bow);
  Nationalist Crusader (T4 front) + Warpriest (T5 support) on the Ghalen
  model; Ceyah Blackguard (T4 front) + Slayer (T5 support) on the Stonewalker
  model; Council Rune Hammer (T4 ram-rider front) + Arcane Archer (T5 ranger
  support). Politics tiers priced under their commanders (fronts 18-22g,
  supports 22-26g). All on placeholder art (CHECKLIST 10a). The Ceyah support
  was renamed Slayer -> Executioner (user, 2026-08-15) since vanilla Shadow
  already has a Slayer.
- Fort/outpost passes for the five non-Human factions (2026-08-14, derived -
  the design sheet's rows were blank): Human transformation applied to all 10
  vanilla files. Health x2, captureable, cost x2.5, unit limit 2/3, faction
  upkeep untouched. Garrisons: core pair 18/18 outpost / 24/24 fort using each
  faction's center mix (Shadow gains fury), elite melee 12/18 (Drauga
  berserker), city siege beast x1 at fort only (Gauri juggernaut, Haroun
  hillstrider, Shadow leviathan). Value table in CHECKLIST section 15;
  in-game verify + user sign-off owed.

### Changed
- Garrison audit (2026-08-14): all 24 town-center files + Human fort/outpost
  diffed against the design-doc target tables (cost, health, unit limit, every
  garrison count). Sole deviation found and fixed: Drauga city berserker
  8 -> 10. Files now match every design table row exactly; stale deviation
  markers cleared from CHECKLIST section 15.
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
