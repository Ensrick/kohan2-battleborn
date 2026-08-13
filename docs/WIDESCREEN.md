# 4K / widescreen state (imported 2026-08-13)

Goal: run Kohan II at 3840x2160 fullscreen with a usable UI.

## What the engine already supports (verified in game files)

- **The resolution list is data-driven.** `UI/resolution.tgi` declares `[Resolution]`
  blocks; the mod already adds `IDS = 3840x2160` alongside the vanilla `IDS = 0x0` entry.
  Each declared width expects a matching `UI/<width>/` asset folder - vanilla ships
  `UI/800/` and `UI/1280/`; the mod adds `UI/3840/` (624 hand-upscaled files: arrows,
  panels, list boxes, drop-downs, CSD icons, main-menu background, splash screen).
- **Engine resolution vars** (`UVars.tgi`, `[UserVariables]`):
  - `int ResolutionX = 1024` / `int ResolutionY = 768`
  - `flag ResolutionWindowed` (code default false)
  - `flag ResolutionCoopFullscreenMode = false` - per the inline comment, `true` runs the
    game in a borderless window at the desktop resolution without a mode change,
    ignoring ResolutionX/Y. A native borderless-fullscreen path already in the engine.
  - `int OptionsAcceptNewResolutionTimeout = 10`
- **Depot order** (`startup\autoexec.txt`): `data.rwd` -> `data/` -> `%USERDATA%/data/ 1`,
  so loose files and Documents\Kohan2 override the archive.
- `UI/Menus/main.tgi` is also overridden in the live Data set (menu layout tweaks).

## Unknowns / next steps

1. **In-game verification** (needs a manual launch): does 3840x2160 appear in the options
   dropdown, does the mode apply, and what breaks (HUD layout, minimap, cursor, zoom)?
2. If the engine rejects the mode or clamps it, go binary: `k2.exe` is a 32-bit D3D
   executable, 8,089,600 bytes, and `k2 - Copy.exe` is a byte-identical backup - no patch
   has been applied yet. Cheat Engine / x32dbg entry points: the options-menu mode
   enumeration (EnumDisplaySettings / D3D EnumAdapterModes), the ResolutionX/Y var
   read, and any hardcoded clamp.
3. `ResolutionCoopFullscreenMode = true` in `Documents\Kohan2\data\User\` (user depot
   wins) may be the cheapest full-res path - worth testing before any exe patching.
4. Localization: `#resolution_3840x2160_name` needs a string entry (check whether
   `_BB_Strings.tgi` or the vanilla string tables define it - not found in the BB strings
   file at import time).
