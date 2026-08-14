# Battleborn feature checklist

**Design doc:** Google Sheet ["Kohan II Kings of War modding"](https://docs.google.com/spreadsheets/d/1OGjwstadLcFT5Wg6ehIgD23KLH5CQd4L6ZH0dnD2jfw/edit)
(Oct 2024) - goals, tiered unit-design table with per-unit status, town-center target
values, known bugs, to-do list. Section 12 below summarizes it. Art references marked
"AW" = the Arcane Wars mod (`D:\Game Mods\Kohan II Kings of War\Arcane_Wars_0.82beta.rar`).

Status inventory built 2026-08-13 by diffing `workbench/` and `Data/` against the pristine
`Data (Backup)` extract. Two dimensions per item: authored (checkbox) and **[SHIPPED]** =
present in the live `Data/` depot. Only the settler-flank slice + `_BB_Strings.tgi` ever
shipped; everything else is workbench-only.

Legend: **BROKEN** = dangling reference, will misbehave if deployed as-is. **STUB** =
placeholder copy, no real content. **VERIFY** = looks intentional but worth an in-game check.

## 1. Settler flank slots [SHIPPED]

- [x] `bb_settler_flank` property (`_BB_Properties.tgi`) + `company_settler` layout: 4 front / 2 flank / 2 support / locked captain, all 3 formations
- [x] Human pioneer, Gauri founder, Undead boneweaver, Haroun pilgrim (Data only), Drauga settler (Data only)
- [ ] **Drift:** Drauga `settler.tgi` exists only in `Data/`, missing from workbench
- [ ] **Drift:** Haroun `pilgrim.tgi` workbench copy lacks the flank slot that shipped in `Data/`
- [ ] **Drift:** Gauri founder cost discount (gold 2 / stone 0.5) is workbench-only; shipped copy has vanilla 5/1. Pilgrim gold 3 discount is Data-only. Pick intended costs and sync
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
- [ ] **Decide the mechanism.** Base-key renames (Halberdier/Hobilar/Cavalier, abilities, colors) only work via the full-file override; _BB-only keys (Footman, Explorer, settler-flank names) must be merged into it (or kept additive alongside). Then delete the loser
- [ ] **BROKEN key mismatches** (unit files reference keys no file defines): `#captain_cavalry_name` (captain.tgi), `#bb_pikeman_praetorian_name`, `#zombie_militia_zombie_name`, `#lancer_militia_name`, and all 5 siege-militia names (`#juggernaut_militia_name` etc.; loc defines `bb_`-prefixed variants)
- [ ] `bb_front_swordsman_Name` capital-N key in _BB_Strings (works only if lookups are case-insensitive: **VERIFY** or fix)
- [ ] Lancer -> Hobilar rename vs new `bb_support_lancer` "Lancer": under the additive mechanism both would display "Lancer"

## 3. Human roster overhaul

- [x] Cost/upkeep rebalance: bowman 12->6, dragoon 20->10, lancer 6->1, pikeman 8->2, pioneer 5->2, swordsman 16->8, plus upkeep cuts
- [x] Tech-tree shift to town centers: catapult, cleric, ranger, sorceress (town), dragoon, warmage (city), swordsman (town), bowman (+blacksmith)
- [x] Company rewiring: flank slots filled (bowman/dragoon/pikeman/swordsman), custom captains/supports as defaults
- [x] `bb_support_dragoon` "Cataphract" and `bb_support_swordsman` "Myrmidon": complete, loc OK (picker-only, no default slot)
- [x] `bb_praetorian` "Praetorian" wired into pikeman support slots, art exists, but: [ ] **BROKEN** name ref `#bb_pikeman_praetorian_name`
- [ ] `bb_captain_infantry` "Infantry Captain": unit + skin + icon done; **BROKEN** portrait 3 ways (skin path names nonexistent folder/file, `portrait_ids` given a file path, defined portrait ids never referenced)
- [ ] `bb_captain_ranger` "Ranger Captain": unit + skin + icon done; **BROKEN** both portrait refs dangling
- [ ] `bb_captain_pikeman` "Infantry Sergeant": stats done; **BROKEN** icon `bb_SergeantPikemanIcon.tga` + skin `bb_sergeant_pikeman.dds` missing (folder has `bb_sergeant_infantry.dds` under the wrong name)
- [ ] `bb_captain_pioneer` "Explorer": unit done but **BROKEN** orphan: pioneer.tgi's captain slot points at nonexistent `bb_pioneer_captain` (typo'd ID); its custom art folder also unreferenced. Shipped pioneer fell back to vanilla `captain`
- [ ] `bb_captain_lancer`: mid-conversion **STUB**: no `captain` property, duplicates `company_lancer`/`militia_lancer` IDs vs lancer.tgi
- [ ] Captain/Support Bowman ("Ranger Sergeant"/"Marksman"): **STUB** byte-identical copies of bowman.tgi (would triple-define `bowman` if deployed); names already staged in loc
- [ ] Captain/Support Engineer: **STUB** untouched vanilla engineer copies
- [ ] captain.tgi rework (hp 360, melee 38, agile) done but **BROKEN** name key (see section 2). **Also contradicts the design doc:** "The original captain is to remain untouched to keep the campaign intact" (only removed from the recruit pool) - decide which wins
- [ ] lancer.tgi adds `militia_lancer` (duplicate vs _BB_Captain_Lancer + missing name key)

## 4. Council

- [x] Eben Baruch: custom skin (`EbenBaruchBase.dds`) + ranger bow/arrow VFX
- [x] `bb_captain_council_swordsman` "Storm Lord": complete (Ghalen Mordecai model, lightning casts, xp-gated)
- [x] `bb_spellsword` "Eldritch Warrior" support: complete (storm shield casts); [ ] **VERIFY** blur-VFX outer-id rename with vanilla inner ids (opposite convention from Infantry Captain's fully-renamed set; one of the two is likely wrong)
- [ ] Both require `bb_base_center_city` + blacksmith + library: only reachable once section 6's base city ships
- [ ] "Rune Lord" (`bb_captain_council_hammer`): loc string + BB_Runelord art only, **no unit tgi** - not started
- [ ] "Storm Guard" front unit (`bb_front_council_swordsman`): loc string only; BB_Stormguard folder is 100% placeholder copies of Spellsword art - not started

## 5. Militia companies

- [x] `company_siege_militia` layout (1 locked slot, `siege` property) [layout file workbench-only]
- [x] Siege militia orgs wired: juggernaut, maelstrom, hillstrider, leviathan, bone_golem (+ denizen_type props)
- [x] `militia_zombie` (standard layout, MonsterIcon)
- [x] `militia_pikeman` added to fort + outpost
- [ ] **BROKEN:** all 6 militia name keys unprefixed vs `bb_`-prefixed loc definitions (section 2)
- [ ] Siege layout reuses `#company_militia_company_short_militia_name` for display: **VERIFY** intended

## 6. Settlements, town centers, structures

- [x] All 6 settlements: `max_structures` flattened to 7 at every tier
- [x] All 24 center files: health x2, base militia x2-3, cost x5, `unit_limit_provided` -> 7/8/9/10
- [x] Elite garrisons at city/citadel: berserker x8/x16, juggernaut+maelstrom, hillstrider, swordsman x8/x16, leviathan x1/x2, zombie x60 all tiers + bone golem
- [ ] **Bug:** `undead_center_village` unit_limit_provided left at 2 (design doc: 7 for all six factions)
- [ ] **Bug (copy-paste):** Haroun city hillstrider count 24 vs citadel 2 (design doc: city 1, citadel 2 - the 24 is a typo)
- [ ] Sync remaining center values against the design doc's target tables (per-faction cost/unit-limit/health/denizen counts; e.g. Undead citadel design adds bone archer/skeleton x18, Gauri citadel spear/anvil x24)
- [ ] **VERIFY:** Undead village bonearcher/skeleton militia+inventory fully commented out (zombie-only garrison), asymmetric vs town/city
- [ ] `bb_base_center_city` faction-choice structure: defined, upgrades into all 6 faction cities, loc OK; placeholder art (Drauga model + generic upgrade icon); nothing can build it yet - decide entry point
- [ ] Cosmetic: stray indent in undead citadel, missing `;;` old-value annotations (shadow citadel cost, stale human citadel comment)

## 7. Buildings (Human)

- [x] Fort + outpost: health x2, captureable, cost 100->250, bigger garrisons, `unit_limit_provided` 3/2
- [ ] `bb_human_woodmill_outpost`: defined (hp 500, wood +4, capturable) but **unbuildable** - zero references, no build list entry; commented [Upgrade] targets `bb_human_sawmill_outpost`/`bb_human_woodmarket_outpost` don't exist. Economy-outpost chain not started
- [ ] Outpost/fort passes for the other five factions: design doc tables have Human-only rows filled, Drauga/Haroun/Gauri/Undead/Shadow left blank - not started

## 8. Game variables

- [x] `EconomyLimitedResourceMax` 20 -> 40
- [x] Kingdom color values retuned (all 16) - pairs with the loc renames in section 2

## 9. Political-faction captains (staging only)

- [ ] CUSTOM_PROPHET_CAPTAIN (Ceyah), CUSTOM_DREADLORD_CAPTAIN (Fallen), CUSTOM_ZEALOT_CAPTAIN (Nationalist), CUSTOM_PALADIN_CAPTAIN (Royalist): every file hash-identical to vanilla, no tgi, no references - staging for the design doc's politics-faction unit lines (section 12), work not started
- [x] Royalist Paladin retexture (`Paladinbase.dds` differs from vanilla, loads via vanilla path)

## 10. Art status

- [x] Wired + custom: BB_Spellsword, _BB_Captain_Infantry, _BB_Captain_Ranger, _BB_Praetorian, EbenBaruch skins/icons
- [x] Vanilla-path retextures: PikemanIcon, PioneerIcon, SwordsmanIcon (` - Copy` files are vanilla backups)
- [ ] **VERIFY:** PikemanIcon.tga (2.1 MB) and PioneerIcon.tga (2.2 MB) are ~300x the size of vanilla icons - likely saved at wrong dimensions/uncompressed
- [ ] Orphaned: BB_Runelord (unique art, no unit), _BB_Captain_Pioneer art (unit uses default skin), _BB_Sergeant_Pikeman dds (wrong filename), BB_Stormguard (pure placeholder)
- [ ] GIMP sources without exported game art: SKIN Haroun Stonewalker, SKIN Ranger Model, SKIN Swordsman Model (started, never exported)
- [ ] Banner icons (Archer/Cavalry/Infantry/Monster/Siege): present + GIMP sources; not diffed vs vanilla - **VERIFY** which are actually reworked

## 11. Repo / pipeline hygiene

- [ ] Reconcile `Data/` vs `workbench/` into one source of truth (README pending item; drift documented in sections 1-2)
- [ ] Duplicate-ID hazard when promoting workbench to `Data/`: bowman x3, engineer x2, lancer company/militia x2 - stubs must be excluded or completed first
- [ ] Prune junk: `workbench/UI/3840/UNFINISHED Game/**/Thumbs.db` (widescreen-owned path, Thumbs.db only), ` - Copy` vanilla backups
- [x] `tools/collect.ps1` / `tools/deploy.ps1` sync scripts; 3 test maps (`BB_Test_2`, `TEST`, `Trial Map Human`)

## 12. Design-doc plans not yet in any file (from the Google Sheet)

Tier scheme: 1-3 = line troops + Sergeants (weaker captains, gold-recolored armor),
4-6 = elite front/support/captain lines gated by politics faction. Statuses below are
the sheet's own.

- [ ] **Royalist cavalry line** (Paladin model): Knight (front) / Paladin (support, "Done (Needs Work)" - the Paladinbase.dds retexture in section 9) / Champion (captain, all-gold)
- [ ] **Nationalist infantry line** (Ghalen Mordecai model): Crusader (front) / Warpriest (support) / Templar (captain)
- [ ] **Ceyah ranged line**: Stalker / Shadow Hunter / Masked Outcast; **Ceyah melee line** (Stonewalker model, black armor): Blackguard / Slayer / Harbinger (lich-hero portrait); Macabre support
- [ ] **Council ranged line** (AW Sharpshooter art): Sentry / Arcane Archer / Warder
- [ ] **Council Gauri line** (Hammer model): Rune Hammer / Warmage / Rune Lord (partially covered by section 4's Rune Lord strings/art)
- [ ] **Council Mage Lord** captain (from Ravid Sakeri); **Undead Necromancer** captain; **Human Skirmisher** support + **Ranger Sergeant** captain (Aethyn Farhyd model); **Engineer line**: Siege Expert / Engineer Sergeant; "Vanguard" (unspecified)
- [ ] Roster additions from existing units: Drauga Fire Wyrm, Gauri Mana Construct, Ceyah Lightning Dragon, Fallen Spiders
- [ ] Xander Kerai copy as a recruitable Kohan hero; make heroes very durable
- [ ] Structures: out-of-town buildable versions of all structures (needs AI testing), innate self-repair, towns needing more buildings + higher cost to upgrade
- [ ] Higher-tier units gated behind higher-tier towns + structures
- [ ] To-do items from the sheet: spellsword custom ability (matches section 4's Eldritch Warrior "UNFINISHED: Needs Custom Spell"), weapon names + ability names + company compositions for custom units, denizen icons for siege, possibly a new denizen type, captain restrictions by assigned unit type
- [ ] Long-term reskin-faction ideas (two alternative sets, e.g. Human -> Darklanders or Northern Domain)
- **KNOWN CRASH (sheet's Bugs tab):** putting regular units in support slots crashes when the AI hires them (invalid layout + memory access violation) - the "allow special slots to contain regular units" goal was abandoned for this reason; keep support slots on support-property units only
