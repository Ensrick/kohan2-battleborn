# Harvests the Battleborn mod out of the Kohan II install into this repo.
#
#   Data/       <- game "Data\" folder verbatim (the live loose-file override depot the game loads)
#   workbench/  <- every file in "Data (Mod)\" that differs from the pristine "Data (Backup)\"
#                  extract (new files, size changes, and content changes at equal size),
#                  including __GIMP FILES art sources
#   maps/       <- authored .RMP maps from Documents\Kohan2\data\Maps
#
# Copy-only: never deletes. If you delete a file in the game folders, remove it from the
# repo manually so git records the deletion.

param(
    [string]$GameDir = "C:\Program Files (x86)\Steam\steamapps\common\Kohan II",
    [string]$UserDataDir = "$env:USERPROFILE\Documents\Kohan2"
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent

# Paths owned by the kohan2-widescreen repo (display/compat concerns) - never collected here.
function Test-WidescreenOwned {
    param([string]$Rel)
    if ($Rel -like 'UI\*' -or $Rel -like 'Fonts\*') { return $true }
    if ($Rel -in @('AVars.tgi', 'UVars.tgi', 'Localization\strings_rtse_ui.tgi')) { return $true }
    if ($Rel -in @('__GIMP FILES\mainmenubackground.xcf', '__GIMP FILES\SplashScreen-enhanced.xcf',
                   '__GIMP FILES\UI - Arrows.xcf', '__GIMP FILES\__GIMP FILES - Units\CatchingUp.xcf',
                   '__GIMP FILES\__GIMP FILES - Units\TileCorners.xcf')) { return $true }
    return $false
}

function Copy-Rel {
    param([string]$SrcRoot, [string]$Rel, [string]$DstRoot)
    $dst = Join-Path $DstRoot $Rel
    $dstDir = Split-Path $dst -Parent
    if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Force $dstDir | Out-Null }
    Copy-Item (Join-Path $SrcRoot $Rel) $dst -Force
}

# --- 1) Live override depot ---
$liveSrc = Join-Path $GameDir 'Data'
$liveCount = 0
Get-ChildItem $liveSrc -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($liveSrc.Length + 1)
    if (Test-WidescreenOwned $rel) { return }
    Copy-Rel $liveSrc $rel (Join-Path $repo 'Data')
    $liveCount++
}
Write-Host "Data/: $liveCount files"

# --- 2) Workbench diff: Data (Mod) vs Data (Backup) ---
$modRoot = Join-Path $GameDir 'Data (Mod)'
$bakRoot = Join-Path $GameDir 'Data (Backup)'
$bak = @{}
Get-ChildItem $bakRoot -Recurse -File | ForEach-Object {
    $bak[$_.FullName.Substring($bakRoot.Length + 1)] = $_
}
$wbCount = 0
Get-ChildItem $modRoot -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($modRoot.Length + 1)
    if (Test-WidescreenOwned $rel) { return }
    $take = $false
    if (-not $bak.ContainsKey($rel)) { $take = $true }
    elseif ($bak[$rel].Length -ne $_.Length) { $take = $true }
    else {
        $h1 = (Get-FileHash $_.FullName -Algorithm MD5).Hash
        $h2 = (Get-FileHash $bak[$rel].FullName -Algorithm MD5).Hash
        if ($h1 -ne $h2) { $take = $true }
    }
    if ($take) { Copy-Rel $modRoot $rel (Join-Path $repo 'workbench'); $wbCount++ }
}
Write-Host "workbench/: $wbCount files"

# --- 3) Authored maps ---
$mapSrc = Join-Path $UserDataDir 'data\Maps'
$mapCount = 0
if (Test-Path $mapSrc) {
    Get-ChildItem $mapSrc -File | ForEach-Object {
        Copy-Rel $mapSrc $_.Name (Join-Path $repo 'maps')
        $mapCount++
    }
}
Write-Host "maps/: $mapCount files"
Write-Host 'Collect complete.'
