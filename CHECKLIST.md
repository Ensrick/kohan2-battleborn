# Battleborn feature checklist

**Design doc:** Google Sheet ["Kohan II Kings of War modding"](https://docs.google.com/spreadsheets/d/1OGjwstadLcFT5Wg6ehIgD23KLH5CQd4L6ZH0dnD2jfw/edit)
(Oct 2024). Part II below reproduces its full contents, organized and annotated with
current file status. Art references marked "AW" = the Arcane Wars mod
(`D:\Game Mods\Kohan II Kings of War\Arcane_Wars_0.82beta.rar`).

Status inventory built 2026-08-13 by diffing `workbench/` and `Data/` against the pristine
`Data (Backup)` extract. **2026-08-13 fix pass:** workbench is now the single source of
truth and `Data/` was rebuilt as the curated deployable superset (stubs + orphaned art
excluded, all references verified to resolve against Data/ + vanilla). Historically only
the settler-flank slice + `_BB_Strings.tgi` had shipped. `Data/` is NOT yet deployed to
the game install (game folder is at vanilla baseline for the widescreen work).

Legend: **BROKEN** = dangling reference, will misbehave if deployed as-is. **STUB** =
placeholder copy, no real content. **VERIFY** = looks intentional but worth an in-game check.

---

# Part I - Implementation status (what is in the files)

## 1. Settler flank slots [SHIPPED]

- [x] `bb_settler_flank` property (`_BB_Properties.tgi`) + `company_settler` layout: 4 front / 2 flank / 2 support / locked captain, all 3 formations
- [x] Human pioneer, Gauri founder, Undead boneweaver, Haroun pilgrim (Data only), Drauga settler (Data only)
- [x] ~~Drift~~ FIXED 2026-08-13: Drauga settler copied into workbench; pilgrim flank slot + gold 3 merged into workbench; founder keeps the discount (settler-discount pattern) and Data/ rebuilt from workbench
- [ ] Shadow uses `horde_shadowsettler`, untouched: confirm intentionally exempt

## 2. Localization (two competing mechanisms, must be reconciled)

`Data/` ships additive `_BB_Strings.tgi` (own table, can only ADD keys); workbench carries a
full-file override of `strings_data_K2.tgi` (can rewrite vanilla keys). They drifted: 10 keys
only in _BB, 2 only in workbench, and identical captains use different key names
(`bb_captain_cavalry_name`/`bb_captain_infantry_name` in workbench vs
`bb_captain_dragoon_name`/`bb_captain_swordsman_name` in _BB).

- [x] Vanilla renames (workbench override only): Pikeman -> Halberdier (incl. company/militia/sounds/tutorial), Lancer -> Hobilar, Dragoon -> Cavalier, Poleaxe -> Masterwork Poleaxe, Pike -> Halberd, Lance -> Couched Lance
- [x] Kingdom color renames (workbench `strings_rtse_data.tgi`): Ochre/Saffron/Indigo/Teal/Mint/Khaki/Azure/Umber/White - pairs with the `kingdom_colors.tgi` value retune (ship both together)
- [x] New-unit name strings staged in both files (Storm Guard line, sergeants, militias, etc.)
- [x] FIXED 2026-08-13: full-file override adopted as the mechanism; all 10 `_BB`-only keys merged into it (capital-N key normalized; `_Slot_name` casing kept to match its references); `_BB_Strings.tgi` retired from `Data/`; added `bb_zombie_militia_name` + `bb_lancer_militia_name` ("Hobilar Militia")
- [x] FIXED 2026-08-13: all key mismatches resolved by pointing units at the defined `bb_`-prefixed keys (captain, praetorian, zombie, lancer, 5 siege militias)
- [x] Lancer/Hobilar name collision moot under the override mechanism (base lancer displays "Hobilar")

## 3. Human roster overhaul

- [x] Cost/upkeep rebalance: bowman 12->6, dragoon 20->10, lancer 6->1, pikeman 8->2, pioneer 5->2, swordsman 16->8, plus upkeep cuts
- [x] Tech-tree shift to town centers: catapult, cleric, ranger, sorceress (town), dragoon, warmage (city), swordsman (town), bowman (+blacksmith)
- [x] Company rewiring: flank slots filled (bowman/dragoon/pikeman/swordsman), custom captains/supports as defaults
- [x] `bb_support_dragoon` "Cataphract" and `bb_support_swordsman` "Myrmidon": complete, loc OK (picker-only, no default slot)
- [x] `bb_praetorian` "Praetorian" wired into pikeman support slots, art exists; name ref FIXED 2026-08-13 (`#bb_support_pikeman_name`)
- [x] `bb_captain_infantry` "Infantry Captain": portrait FIXED 2026-08-13 (skin path corrected to `_BB_Captain_Infantry/bb_captain_infantry_portrait.dds`, `portrait_ids` -> defined id `captain_infantry_portrait`)
- [x] `bb_captain_ranger` "Ranger Captain": portrait FIXED 2026-08-13 (skin path -> `_BB_Captain_Ranger/bb_captain_ranger_portrait.dds`, `portrait_ids` -> defined id `captain_ranger_portrait`)
- [x] `bb_captain_pikeman` "Infantry Sergeant": art refs FIXED 2026-08-13 (skin -> existing `bb_sergeant_infantry.dds`; icon -> vanilla PikemanIcon for now). [ ] Custom sergeant icon still owed (design: gold armor recolor)
- [x] `bb_captain_pioneer` "Explorer": FIXED 2026-08-13 - pioneer.tgi captain slot now points at `bb_captain_pioneer`. [ ] Its custom art folder still unreferenced (unit uses default Pioneer skin; decide whether to wire `bb_captain_pioneer.dds`)
- [x] `bb_captain_lancer` "Cavalry Sergeant" BUILT 2026-08-14: proper unit-only definition (hp 260, melee 24, recon/archer_foe support props, captain), duplicate company/militia blocks removed. Art debt (section 10)
- [x] `bb_captain_bowman` "Ranger Sergeant" BUILT 2026-08-14: bowman-based captain on the Aethan Farhyd hero skin/portrait/icon per design (hp 240, ranged 26, swift). Art debt: gold recolor
- [x] `bb_support_bowman` "Marksman" BUILT 2026-08-14: elite ranged support (hp 240, ranged 26, town-tier requirement). Art debt
- [x] `bb_captain_engineer` "Engineer Sergeant" + `bb_support_engineer` "Siege Expert" BUILT 2026-08-14: engineer-line captain/support with builder + boosted repair (12/14) and siege damage (10/14); new loc names added. Art debts
- [x] `bb_front_paladin` "Knight" + `bb_captain_paladin` "Champion" BUILT 2026-08-14 (Royalist line around the playtested Paladin support): Knight = martial front/flank (hp 400, melee 32, 20g), Champion = captain (hp 520, magic 46, morale 13, 36g), both gated on faction_royalist+good like vanilla Paladin. Art debts
- [ ] **VERIFY in-game:** new captains/supports appear in the company picker (captain/support property + requirements is the assumed mechanism); Knight selectable in front/flank slots
- [ ] captain.tgi rework (hp 360, melee 38, agile): name key FIXED 2026-08-13 (`#bb_captain_cavalry_name`), but it still **contradicts the design doc:** "The original captain is to remain untouched to keep the campaign intact" (only removed from the recruit pool) - decide which wins
- [x] lancer.tgi `militia_lancer` name key FIXED 2026-08-13 (`#bb_lancer_militia_name` = "Hobilar Militia"); duplicate-ID stub `_BB_Captain_Lancer.tgi` excluded from `Data/`

## 4. Council

- [x] Eben Baruch: custom skin (`EbenBaruchBase.dds`) + ranger bow/arrow VFX
- [x] `bb_captain_council_swordsman` "Storm Lord": complete (Ghalen Mordecai model, lightning casts, xp-gated)
- [x] `bb_spellsword` "Eldritch Warrior" support: complete (storm shield casts); [ ] **VERIFY** blur-VFX outer-id rename with vanilla inner ids (opposite convention from Infantry Captain's fully-renamed set; one of the two is likely wrong)
- [ ] Both require `bb_base_center_city` + blacksmith + library: only reachable once section 6's base city ships
- [x] "Rune Lord" (`bb_captain_council_hammer`) BUILT 2026-08-14: Council cavalry captain on the Gauri Hammer ram-rider (hp 420, melee 34, morale 14). The orphaned BB_Runelord art stays unwired until its target model is confirmed (section 10a)
- [ ] "Storm Guard" front unit (`bb_front_council_swordsman`): loc string only; BB_Stormguard folder is 100% placeholder copies of Spellsword art - not started

## 5. Militia companies

- [x] `company_siege_militia` layout (1 locked slot, `siege` property) [layout file workbench-only]
- [x] Siege militia orgs wired: juggernaut, maelstrom, hillstrider, leviathan, bone_golem (+ denizen_type props)
- [x] `militia_zombie` (standard layout, MonsterIcon)
- [x] `militia_pikeman` added to fort + outpost
- [x] Militia name keys FIXED 2026-08-13: all 7 units now reference the `bb_`-prefixed loc keys
- [ ] Siege layout reuses `#company_militia_company_short_militia_name` for display: **VERIFY** intended

## 6. Settlements, town centers, structures

- [x] All 6 settlements: `max_structures` flattened to 7 at every tier
- [x] All 24 center files: health x2, base militia x2-3, cost x5, `unit_limit_provided` -> 7/8/9/10
- [x] Elite garrisons at city/citadel: berserker x8/x16, juggernaut+maelstrom, hillstrider, swordsman x8/x16, leviathan x1/x2, zombie x60 all tiers + bone golem
- [x] FIXED 2026-08-13: `undead_center_village` unit_limit_provided 2 -> 7 (design target)
- [x] FIXED 2026-08-13: Haroun city hillstrider count 24 -> 1 (design target; citadel stays 2)
- [ ] Sync remaining center values against the design target tables in section 15 (e.g. Undead citadel design adds bone archer/skeleton x18)
- [ ] **VERIFY:** Undead village bonearcher/skeleton militia+inventory fully commented out (zombie-only garrison), asymmetric vs town/city - but matches the design table, which gives Undead villages zombies only
- [ ] `bb_base_center_city` faction-choice structure: defined, upgrades into all 6 faction cities, loc OK; placeholder art (Drauga model + generic upgrade icon); nothing can build it yet - decide entry point
- [ ] Cosmetic: stray indent in undead citadel, missing `;;` old-value annotations (shadow citadel cost, stale human citadel comment)

## 7. Buildings (out-of-town economy outposts)

**Design intent (user, 2026-08-13/14): every faction gets these expensive outpost structures -
buildable economic output outside towns, enabling defensive/turtle play.** Formula: 3x
in-town cost, 2/3 output, capturable + razable. **Guard doctrine (user 2026-08-14):** guards
are weaker units, thematically suited to the structure (wood structures = the faction's
hunter/ranged unit x8 + its workers, parity with the playtested Human pilot); military
outposts/forts stay strictly stronger so economy outposts never replace them. Building HP at
in-town parity for now - the tanky-x2 doctrine was deliberately NOT applied here pending
playtest. Random names via DEDICATED per-structure lists (user 2026-08-14: never reuse the fort
lists): `namelist_bb_<faction>_{woodmill,sawmill,woodmarket}`, 18 lists x 50 names each
(fort-list parity) in `NameLists/namelist_bb_<faction>_wood.tgi` + 918 `bb_namelist_*` loc keys.
Naming policy (user 2026-08-14): generated generic random pools like these are fine;
unit TYPES, heroes, and unique things are named by the user - never invent those (all
current unit names come from the user's design sheet). To tweak namelist values: edit the
`;; BB wood-outpost namelists` block at the tail of `Localization/strings_data_K2.tgi`,
or edit the pools in `tools/gen_namelists.ps1` and rerun.
Builder units per faction (vanilla `BuilderComponent` carriers): Human engineer, Drauga
crafter, Gauri forge, Haroun caretaker, Shadow nightbringer, Undead boneweaver.

- [x] Fort + outpost: health x2, captureable, cost 100->250, bigger garrisons, `unit_limit_provided` 3/2 (matches the design targets in section 15 exactly)
- [x] `bb_human_woodmill_outpost` chain COMPLETED 2026-08-13: engineer.tgi override adds it to the `BuilderComponent` build list (vanilla out-of-town build mechanism); upgrades `bb_human_sawmill_outpost` (285g, wood 8) and `bb_human_woodmarket_outpost` (285g, gold 12 + wood 3) authored on the 3x-cost / 2/3-output formula, vanilla sawmill/woodexport art + names, capturable + razable, same worker/bowman garrison. **VERIFY in-game:** build via engineer, upgrade paths, and whether the AI ever builds it (design-doc caution)
- [ ] Out-of-town sawmill/woodmarket intentionally DROP the in-town versions' ranged-tech research trees (reduced efficacy) - revisit if they should carry research
- [ ] Outpost/fort passes for the other five factions: design tables have Human-only rows filled, Drauga/Haroun/Gauri/Undead/Shadow left blank - not started
- [x] Economy-outpost wood chains COMPLETED for all six factions 2026-08-13 (guards + namelists retuned 2026-08-14): `bb_<faction>_{woodmill,sawmill,woodmarket}_outpost` x6 on the 3x-cost / 2/3-output formula, faction-correct art/names/HP (woodmarket = each faction's export or mana-convert variant); builder overrides add the BuildActor. Guards per doctrine: bowman (Human), impaler (Drauga), spear (Gauri), rainbringer (Haroun, workerless like its outpost), fury (Shadow), bone archer (Undead), x8 + workers x4. **VERIFY in-game per faction:** build button, upgrades, random names, AI usage
- [ ] Playtest knobs deliberately left open: guard counts (8 vs "large amount"), building HP (in-town parity vs the mod's x2-tanky doctrine)
- [ ] Beyond wood: decide which other in-town producers get outpost versions (quarry, foundry, market, library chains exist for all six factions in vanilla)

## 8. Game variables

- [x] `EconomyLimitedResourceMax` 20 -> 40
- [x] Kingdom color values retuned (all 16) - pairs with the loc renames in section 2

## 9. Political-faction captains (staging only)

- [ ] CUSTOM_PROPHET_CAPTAIN (Ceyah), CUSTOM_DREADLORD_CAPTAIN (Fallen), CUSTOM_ZEALOT_CAPTAIN (Nationalist), CUSTOM_PALADIN_CAPTAIN (Royalist): every file hash-identical to vanilla, no tgi, no references - staging of the politics-faction support-unit models for the tiered lines in section 13 (Fallen/Dreadlord has no designed line yet), work not started
- [x] Royalist Paladin retexture (`Paladinbase.dds` differs from vanilla, loads via vanilla path) - the sheet's "Paladin: Done (Needs Work)"

## 10. Art status

- [x] Wired + custom: BB_Spellsword, _BB_Captain_Infantry, _BB_Captain_Ranger, _BB_Praetorian, EbenBaruch skins/icons
- [x] Vanilla-path retextures: PikemanIcon, PioneerIcon, SwordsmanIcon (` - Copy` files are vanilla backups)
- [ ] **VERIFY:** PikemanIcon.tga (2.1 MB) and PioneerIcon.tga (2.2 MB) are ~300x the size of vanilla icons - likely saved at wrong dimensions/uncompressed
- [ ] Orphaned: BB_Runelord (unique art, no unit), _BB_Captain_Pioneer art (unit uses default skin), _BB_Sergeant_Pikeman dds (wrong filename), BB_Stormguard (pure placeholder)
- [ ] GIMP sources without exported game art: SKIN Haroun Stonewalker (= the Ceyah melee "Blackguard" line base, section 13), SKIN Ranger Model, SKIN Swordsman Model (started, never exported)
- [ ] Banner icons (Archer/Cavalry/Infantry/Monster/Siege): present + GIMP sources; not diffed vs vanilla - **VERIFY** which are actually reworked

## 10a. TEXTURE MAP DEBTS (units shipping on placeholder/vanilla art)

Every unit below is functional but waiting on custom textures:

- [ ] `bb_captain_bowman` Ranger Sergeant - gold-armor recolor of `AethanFarhydBase.dds` + own icon (ships with Aethan Farhyd's skin/portrait/icon)
- [ ] `bb_support_bowman` Marksman - gold-trim bowman skin + own icon (ships with default bowman art)
- [ ] `bb_captain_lancer` Cavalry Sergeant - gold armor on white horse + own icon (ships with default lancer art)
- [ ] `bb_captain_engineer` Engineer Sergeant - gold-recolor engineer skin + own icon
- [ ] `bb_support_engineer` Siege Expert - recolored engineer skin + own icon
- [ ] `bb_front_paladin` Knight - silver-only paladin skin + own icon (ships with the BB Paladinbase retexture)
- [ ] `bb_captain_paladin` Champion - gold paladin skin + all-gold captain portrait + own icon (`GIMP_Royalist_Files/BB_Champion_Paladin_Knight.xcf` source exists)
- [ ] `bb_captain_pikeman` Infantry Sergeant - own icon (borrows vanilla PikemanIcon; custom skin `bb_sergeant_infantry.dds` already exists)
- [ ] `bb_captain_pioneer` Explorer - decide whether to wire the existing `bb_captain_pioneer.dds`
- [ ] `bb_base_center_city` - placeholder Drauga city model + generic upgrade icon
- [ ] Storm Guard (Council) - BB_Stormguard folder is placeholder copies; full skin/icon/portrait needed before the unit is authored
- [ ] `bb_captain_nationalist_swordsman` Templar - dark iron w/ gold trim Ghalen skin + own icon (ships with default Ghalen art + his portrait)
- [ ] `bb_captain_ceyah_stonewalker` Harbinger - black/gold stonewalker skin + own icon + lich-hero portrait (SKIN xcf started in GIMP sources)
- [ ] `bb_captain_council_ranger` Warder - AW Sharpshooter-style skin + icon + portrait (ships with default Ranger art)
- [ ] `bb_captain_council_hammer` Rune Lord - the orphaned `BB_Runelord/BB_Runelord.dds` + `BB_Runelord_Portrait.dds` exist but their target model is unverified vs the Hammer ram-rider; confirm in-game, then wire or redo
- [ ] `bb_captain_council_magelord` Mage Lord - own skin recolor + icon (ships with Ravid Sakeri's art + portrait)
- [ ] `bb_captain_undead_necromancer` Necromancer - own skin recolor + icon + portrait (ships with default Lich art)

## 11. Repo / pipeline hygiene

- [x] FIXED 2026-08-13: workbench = single source of truth; `Data/` rebuilt as curated superset (95 files), reference-verified. Future promotions: edit workbench, re-copy to `Data/`
- [x] Duplicate-ID hazard RESOLVED 2026-08-14: all five former stubs are now real units shipped in `Data/`; verified no unit-level ID collisions remain
- [ ] Prune junk: `workbench/UI/3840/UNFINISHED Game/**/Thumbs.db` (widescreen-owned path, Thumbs.db only), ` - Copy` vanilla backups
- [x] `tools/collect.ps1` / `tools/deploy.ps1` sync scripts; 3 test maps (`BB_Test_2`, `TEST`, `Trial Map Human`)

---

# Part II - Design doc (Oct 2024 Google Sheet, organized)

The sheet's own statuses are stale in places; each item below is annotated with where the
files actually are as of 2026-08-13.

## 12. Goals

### New units and captains

- [ ] Make alternatives to Captains which are standard units - underway (Cataphract, Myrmidon, Praetorian done; see section 13)
- [ ] Make Captains into new units - underway (Infantry/Ranger Captains authored, portraits broken)
- [ ] Sergeants concept: weaker captains for lesser units, gold-recolored armor, with higher-tier captains gated late-game - underway (Infantry Sergeant authored; Cavalry/Ranger Sergeants stubs)
- [ ] Keep the ORIGINAL Captain untouched for campaign integrity, only remove it from the recruit pool - **currently violated** (captain.tgi buffed, section 3) and the recruit-pool removal is not done either
- [ ] Make a Xander Kerai copy as a recruitable Kohan hero - not started
- [ ] Make Heroes very durable - not started
- Sheet's HUMAN CAPTAINS progress list: Cavalry Captain, Ranger Captain, Infantry Captain (no ticks recorded)

### More troops, bigger battles

- [x] Increase units hireable from buildings that provide unit cap - done (`unit_limit_provided` bumps, sections 6-7)
- [x] Reduce upkeep of troops (or mainly weaker troops) - done for Human roster (section 3)
- [x] Increase innate structure defenders - done (garrison bumps, sections 6-7)
- [ ] Consider increasing the Health of all units - not started (only structures got HP x2)
- [ ] Change default troop hiring groups into bigger ones - not started (company layouts unchanged apart from settler/siege)
- [x] ~~Allow special unit slots to contain regular units~~ - **abandoned: crashes the AI** (section 18)
- [ ] Higher-tier units require higher-tier towns AND structures - done for Human (tech shifts, section 3); other factions not started

### Structures

- [ ] Out-of-town buildable versions of all structures, higher cost / lower efficacy (needs AI testing) - pilot chain DONE 2026-08-13 (woodmill -> sawmill/woodmarket, buildable via engineer; section 7); remaining structures + other factions open. Recipe: clone as K2HumanBuilding, 3x cost / 2/3 output, add one `[BuildActor]` line to the builder unit
- [ ] Most structures innately repair themselves - not started
- [ ] Towns require more buildings and higher cost to upgrade - partial (cost x5 done; extra building requirements not started)
- [ ] Out-of-town buildings always capturable + self-repairing (unless lair) - partial (fort/outpost/woodmill captureable done; self-repair not started)

### Companies, militia, town centers

- [ ] New companies - partial (settler flank + Siege Militia done; per-line companies of section 13 not started)
- [ ] Bigger militia units - partial (garrisons yes; militia company sizes unchanged)
- [x] Town centers changed for all six factions (sheet recorded only Human + Drauga as Done - files finished all six; remaining value syncs in section 6)
  - Target changes: much more militia (Human as the proportionality reference), double health, 5x cost, bigger unit cap each upgrade

## 13. Planned unit roster (the sheet's Unit Stats table)

Tier scheme: 1-3 = line troops with Sergeants as budget captains; 4-6 = elite
front/support/captain lines gated by politics faction. "Sheet status" is the doc's own;
"Files now" is current reality.

### Human

| Line | Tier | Name | Base unit | Role | Sheet status | Files now | Appearance plan |
|---|---|---|---|---|---|---|---|
| Infantry | 1 | Halberdier | Pikeman (rename) | Front/Flank | Original | Rename done (loc override) | - |
| Infantry | 2 | Praetorian | Pikeman | Support | Not Implemented | Done + wired; name key broken | Silver armor, gold trim, auburn hair |
| Infantry | 3 | Infantry Sergeant | Pikeman | Captain | Not Implemented | Done; icon+skin filenames broken | Gold armor, blonde hair |
| Infantry | 5 | Infantry Captain | Swordsman | Captain | (goals list) | Done; portrait broken 3 ways | - |
| Cavalry | 1 | Hobilar | Lancer (rename) | Front/Flank | Original | Rename done (loc override) | - |
| Cavalry | 2 | Lancer | Lancer | Support | Not Implemented | Loc string only | Silver w/ gold trim, black horse |
| Cavalry | 3 | Cavalry Sergeant | Lancer | Captain | Not Implemented | Done 2026-08-14; art debt | Gold armor, white horse |
| Cavalry | 3 | Cavalier | Dragoon (rename) | Front/Flank | Original; cost 10 / wood 0.5 / iron 0.5 | Rename + exact costs done | Silver, no gold |
| Cavalry | 4 | Cataphract | Dragoon | Support | (blank) | Done | - |
| Cavalry | 5 | Cavalry Captain | Captain (rename) | Captain | Original | Reworked (violates untouched rule); name key broken | - |
| Ranged | 2 | Bowman | - | Front/Flank | Original; cost 6 / wood 0.5 | Exact costs done | - |
| Ranged | 2 | Skirmisher | Bowman | Support | Not Implemented | Nothing | Gold trim on armor |
| Ranged | 3 | Ranger Sergeant | Bowman | Captain | Not Implemented | Done 2026-08-14 on Aethan skin; gold recolor owed | Aethyn Farhyd model, gold armor |
| Ranged | 3 | Ranger | Ranger | Front/Flank | Not Implemented | Nothing | AW Royal Court Hunter |
| Ranged | 4 | Marksman | Ranger (rename) | Support | Original | Done 2026-08-14 as bowman-based support; art debt | Ranger |
| Ranged | 5 | Ranger Captain | Ranger | Captain | (blank) | Done; portraits broken | - |
| Melee | 2 | Swordsman | - | Front/Flank | Original | Rebalanced | - |
| Siege | 1 | Engineer | - | - | (blank) | Modified (woodmill BuildActor) | - |
| Siege | 2 | Siege Expert | Engineer | Support | (blank) | Done 2026-08-14; art debt | - |
| Siege | 3 | Engineer Sergeant | Engineer | Captain | (blank) | Done 2026-08-14; art debt | - |

**Commander cost model (2026-08-14):** vanilla native captains (Captain/Warlord/Leader/
Guide/Reaper) are FREE; Shadow's five specials are 10g + mana upkeep with auras/spells;
politics supports run 26-28g + mana 3. Politics commanders are therefore priced at
politics-support gold tier + captain premium, with mana upkeep scaling to casting power:
Harbinger 26g, Templar 28g, Storm Lord 28g+mana 2 (was 24+1), Warder 30g, Rune Lord 32g,
Mage Lord 32g+mana 2, Necromancer 30g+mana 3 (summoner tax), Champion 36g (ceiling).
Open idea (sheet + user): signature company auras per commander, Shadow-style - needs a
SupportProperty mapping pass.

### Politics-faction lines (Royalist / Nationalist / Ceyah)

| Line | Tier | Name | Base unit | Role | Sheet status | Files now | Appearance plan |
|---|---|---|---|---|---|---|---|
| Royalist cavalry | 4 | Knight | Paladin | Front/Flank | Not Implemented | Done 2026-08-14; art debt | - |
| Royalist cavalry | 5 | Paladin | Paladin | Support | Done (Needs Work) | Retexture done (Paladinbase.dds) | Silver w/ gold trim |
| Royalist cavalry | 6 | Champion | Paladin | Captain | Not Implemented | Done 2026-08-14; art debt (xcf exists) | Gold; portrait: Captain all gold |
| Nationalist infantry | 4 | Crusader | Swordsman | Front/Flank | Not Implemented | Nothing | Ghalen model, silver only |
| Nationalist infantry | 5 | Warpriest | Swordsman | Support | Not Implemented | Nothing | Ghalen, silver w/ gold trim |
| Nationalist infantry | 6 | Templar | Swordsman | Captain | Not Implemented | Done 2026-08-14; art debt | Ghalen, dark iron w/ gold trim |
| Nationalist support | - | Zealot | - | Support | Original | Staging folder only | - |
| Ceyah ranged | 4 | Stalker | - | Front/Flank | Not Implemented | Nothing | - |
| Ceyah ranged | 5 | Shadow Hunter | - | Support | Not Implemented | Nothing | - |
| Ceyah ranged | 6 | (Masked Outcast) | - | Captain | Not Implemented | Nothing | - |
| Ceyah melee | 4 | Blackguard | Stonewalker | Front/Flank | Not Implemented | Stonewalker skin xcf started | Black armor |
| Ceyah melee | 5 | Slayer | Stonewalker | Support | Not Implemented | Nothing | Black armor, red trim |
| Ceyah melee | 6 | Harbinger | Stonewalker | Captain | Not Implemented | Done 2026-08-14; art debt | Black armor, gold trim; portrait: the lich hero |
| Ceyah support | - | Prophet | - | Support | Original ("See Lore") | Staging folder only | - |
| Ceyah support | - | Macabre | - | Support | Not Implemented | Nothing | - |

(The CUSTOM_DREADLORD_CAPTAIN staging folder implies a Fallen line the sheet never designed.)

### Council lines

| Line | Tier | Name | Base unit | Role | Sheet status | Files now | Appearance plan |
|---|---|---|---|---|---|---|---|
| Ranged (Haroun) | 4 | Sentry | - | Front/Flank | Not Implemented | Nothing | AW Sharpshooter |
| Ranged (Haroun) | 5 | Arcane Archer | Ranger | Support | Not Implemented | Nothing | Ranger (white) |
| Ranged (Haroun) | 6 | Warder | Ranger | Captain | Not Implemented | Done 2026-08-14; AW art debt | AW Sharpshooter |
| Melee (Human) | 4 | Storm Guard | Swordsman | Front/Flank | Not Implemented | Loc string + placeholder art | Swordsman, silver/grey w/ black trim |
| Melee (Human) | 5 | Eldritch Warrior | Swordsman | Support | UNFINISHED: needs custom spell; cost 24 / iron 1 / mana 1; skin made; needs custom swing effect + ability | Done as `bb_spellsword` (storm shield); swing-VFX rename **VERIFY** (section 4) | Blue/purple trim silver armor |
| Melee (Human) | 6 | Storm Lord | Swordsman | Captain | Not Implemented | **Done** (`bb_captain_council_swordsman`) | Ghalen, gold w/ blue/purple trim |
| Cavalry (Gauri) | 4 | Rune Hammer | Hammer | Front/Flank | (blank) | Nothing | - |
| Cavalry (Gauri) | 5 | Warmage | - | Support | (blank) | Nothing | - |
| Cavalry (Gauri) | 6 | Rune Lord | Hammer | Captain | (blank) | Done 2026-08-14; art debt | - |
| Special | 6 | Mage Lord | Ravid Sakeri | Captain | Not Implemented | Done 2026-08-14 on Ravid art; protection spells | - |

### Other

| Faction | Tier | Name | Base unit | Role | Sheet status | Files now |
|---|---|---|---|---|---|---|
| Undead | 5 | Necromancer | Lich | Captain | Not Implemented | Done 2026-08-14 on Lich model; summon_undead spells; art debt |
| ? | - | Vanguard | - | - | (name only) | Nothing |

### Roster additions from existing units

- [ ] Drauga: Fire Wyrm - [ ] Gauri: Mana Construct - [ ] Ceyah: Lightning Dragon - [ ] Fallen: Spiders (all not started)

## 13a. COMMANDER NAMING WORKSHEET (user to fill - user names all unit types)

Vanilla gives each faction its own commander type: Human **Captain**, Drauga **Warlord**,
Gauri **Leader**, Haroun **Guide**, Undead **Reaper**, Shadow has five (**Banshee, Brute,
Fiend, Shade, Warlock**); politics factions use heroes. The Human pattern (budget
"Sergeant" tier + elite line captains + elite supports) has no named equivalents for the
factions below. Fill in names and I build them:

| Faction | Native commander | Needs names for |
|---|---|---|
| Drauga | Warlord | budget commander ("sergeant" tier), elite melee commander (raider line), elite ranged commander (impaler line), elite supports |
| Gauri | Leader | budget commander, elite commanders/supports (anvil / spear / hammer lines) |
| Haroun | Guide | budget commander, elite commanders/supports (mistrunner / rainbringer / stonewalker lines) |
| Shadow | Banshee/Brute/Fiend/Shade/Warlock | budget commander tier (if wanted - Shadow already has five commander types) |
| Undead | Reaper | budget commanders (skeleton / bone archer lines); Necromancer now exists as the elite captain |
| Fallen | (heroes) | the Dreadlord-model commander the CUSTOM_DREADLORD_CAPTAIN staging folder was made for |
| Ceyah ranged | - | confirm or replace the sheet's tentative "(Masked Outcast)" captain name; Stalker/Shadow Hunter fronts are named |

## 14. Company compositions (sheet's Companies table)

Only one row was designed:

| Company | Renames | Captain | Front | Flank | Support |
|---|---|---|---|---|---|
| Infantry Company (T1, Human) | was Pikeman Company | Infantry Sergeant | Halberdier | Halberdier | Praetorian |

- [ ] Design + implement compositions for the remaining custom lines (also a sheet To Do item, section 18)

## 15. Target value tables (town centers, outposts, forts)

Design targets; **bold** = files currently deviate. Denizen counts are per-center garrisons.

### Village halls (all: unit limit 7)

| Faction | Cost | Health | Garrison |
|---|---|---|---|
| Human | 500 | 2600 | Bowman 12, Pikeman 18 |
| Drauga | 500 | 2400 | Impaler 12, Raider 24 |
| Haroun | 625 | 2600 | Rainbringer 16, Mistrunner 18 |
| Gauri | 500 | 3000 | Spear 12, Anvil 18 |
| Undead | 450 | 2400 | Zombie 60 (**files: unit limit still 2**) |
| Shadow | 400 | 2800 | Fury 12, Reaver 18 |

### Town halls (all: unit limit 8)

| Faction | Cost | Health | Garrison |
|---|---|---|---|
| Human | 600 | 5200 | Bowman 18, Pikeman 24 |
| Drauga | 550 | 4800 | Impaler 18, Raider 32 |
| Haroun | 0 | 4200 | Rainbringer 24, Mistrunner 24 |
| Gauri | 550 | 6000 | Spear 18, Anvil 24 |
| Undead | 500 | 4800 | Bone Archer 6, Skeleton 12, Zombie 60 |
| Shadow | 500 | 5600 | Fury 18, Reaver 24 |

### City halls (unit limit 9; sheet has Drauga at 8, likely a typo)

| Faction | Cost | Health | Garrison |
|---|---|---|---|
| Human | 1200 | 10400 | Bowman 24, Pikeman 24, Swordsman 8 |
| Drauga | 1100 | 9600 | Impaler 30, Raider 30, Berserker 10 |
| Haroun | 0 | 7800 | Rainbringer 30, Mistrunner 24, Hillstrider 1 (**files: 24**) |
| Gauri | 1100 | 12000 | Spear 24, Anvil 24, Juggernaut 1 |
| Undead | 900 | 9600 | Bone Archer 12, Skeleton 12, Zombie 60 |
| Shadow | 800 | 11200 | Fury 24, Reaver 24, Leviathan 1 |

### Citadels (all: unit limit 10)

| Faction | Cost | Health | Garrison |
|---|---|---|---|
| Human | 1800 | 15000 | Bowman 24, Pikeman 24, Swordsman 16 |
| Drauga | 1650 | 14400 | Impaler 30, Raider 38, Berserker 16 |
| Haroun | 0 | 10400 | Rainbringer 30, Mistrunner 30, Hillstrider 2 |
| Gauri | 1800 | 16000 | Spear 24, Anvil 24, Juggernaut 1, Maelstrom 1 |
| Undead | 1500 | 14400 | Bone Archer 18, Skeleton 18, Zombie 60, Bone Golem 1 |
| Shadow | 1200 | 14000 | Fury 24, Reaver 30, Leviathan 2 |

### Outposts and forts (capturable + razable, stone upkeep)

| Building | Faction | Cost | Unit limit | Health | Garrison | Stone upkeep |
|---|---|---|---|---|---|---|
| Outpost | Human | 250 | 2 | 2600 | Pikeman 18, Bowman 18, Swordsman 12 | 4 |
| Fort | Human | 250 | 3 | 3900 | Pikeman 24, Bowman 24, Swordsman 18 | 6 |

Files match the Human rows exactly. All five other factions' rows were left blank - not designed yet (section 7).

## 16. Ideas backlog (sheet's IDEAS blocks)

- [ ] Unique support unit per company, lightly reskinned with an ability (Praetorian is the pilot; extend to other companies)
- [ ] Captains restricted to their assigned unit type, OR cost unique resources with unique bonuses (like Shadow captains)
- [ ] Reskin-faction concept, set A: Human -> Darklanders (undead-allied humans), Haroun -> Dark Elves, Gauri -> Normalish Dwarves, Drauga -> Human Barbarians, Undead -> Wizards (ivory white good town), Shadow -> Fiery Red Demons
- [ ] Reskin-faction concept, set B: Human -> Northern Human Domain (less advanced, greater numbers, iron/wood structures, mail over plate), Haroun -> Snow Elves, Gauri -> Advanced Middle-Eastern Kingdom, Drauga -> Corrupt Shadow Drauga, Undead -> Dark Dwarves, Shadow -> Winter Demons

## 17. Engine research notes (sheet's Key Values)

Extractor: K2ExtractRWD (archived in `tools/third_party/`).

| File | Key | Value | Note |
|---|---|---|---|
| game/world_rules_k2.tgi | Starting resources? | 500 | |
| game/world_rules.tgi | Starting resources? | 1000 | possibly overrides others |
| game/Svars.tgi | Starting resources, new + random maps | 500 | |
| game/SVars_k2.tgi | EconomyLimitedResourceMax | 40 | max unit count - **implemented** (section 8) |
| game/kingdom_colors.tgi | kingdom colors | | **implemented** (section 8) |
| Settlements/ | per-tier max structures | | **implemented** (section 6) |

## 18. Known bugs + To Do (sheet's Bugs / To Do tabs)

- **KNOWN CRASH:** putting regular units in support slots crashes when the AI hires them - two errors (invalid layout per source, memory access violation). The "regular units in special slots" goal was abandoned for this reason; keep support slots on support-property units only
- [x] Custom skins for heroes: Eben Baruch (marked Done in the sheet too)
- [ ] Weapon names for custom units (partially covered: Khaldunite Sword, Fine Steel Halberd strings exist)
- [ ] Ability names for custom units
- [ ] Company compositions for custom units (section 14)
- [ ] Create the spellsword ability (matches Eldritch Warrior UNFINISHED status, section 13)
- [ ] Denizen icons for the siege item, maybe (siege militia currently reuses vanilla banner icons)
- [ ] May need a new denizen type in `game/denizen_types` (files so far reuse `denizen_type_melee`/`denizen_type_ranged`)
- [ ] Captain restrictions (section 16)
