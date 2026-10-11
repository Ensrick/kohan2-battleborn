# Installs the repo's Data/ override set into the Kohan II user depot
# (Documents\Kohan2\data, mounted by the game at priority 1 over Data.rwd and the
# install folder's data\), so the Steam install itself stays byte-exact to the depot.
#
# Manifest-driven: every installed file is recorded with its SHA256 in
# Documents\Kohan2\battleborn_manifest.txt (outside data\, so the engine never scans it).
#
#   Install / update:  .\deploy.ps1            (re-run after every edit; drops files removed from Data/)
#   Preview:           .\deploy.ps1 -WhatIf
#   Uninstall:         .\deploy.ps1 -Uninstall
#
# Safety: never overwrites a depot file Battleborn does not own (another gameplay mod such
# as Immortals, or your own edits) - it stops and lists the conflicts instead. On removal,
# a file is deleted only if it is still byte-identical to what was installed; a file you
# changed in the depot is moved to Documents\Kohan2\battleborn_backup\<timestamp>\ instead.
# Saves, films, maps, screenshots and settings are never touched.

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$UserDir = (Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'Kohan2'),
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$src = Join-Path $repo 'Data'
$depot = Join-Path $UserDir 'data'
$manifestPath = Join-Path $UserDir 'battleborn_manifest.txt'
$backupRoot = Join-Path $UserDir ('battleborn_backup\' + (Get-Date -Format 'yyyyMMdd-HHmmss'))

function Read-Manifest {
    $m = @{}
    if (Test-Path -LiteralPath $manifestPath) {
        foreach ($line in Get-Content -LiteralPath $manifestPath) {
            if ($line -match '^([0-9A-F]{64})\t(.+)$') { $m[$Matches[2]] = $Matches[1] }
        }
    }
    return $m
}

function Get-Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }

# Removes one installed file: delete if unchanged, otherwise move it to the backup folder.
function Remove-Owned([string]$Rel, [string]$Hash) {
    $target = Join-Path $depot $Rel
    if (-not (Test-Path -LiteralPath $target)) { return 'absent' }
    if ((Get-Sha $target) -eq $Hash) {
        if ($PSCmdlet.ShouldProcess($target, 'Remove file')) { Remove-Item -LiteralPath $target -Force }
        Remove-EmptyParents (Split-Path $target -Parent)
        return 'removed'
    }
    $bak = Join-Path $backupRoot $Rel
    if ($PSCmdlet.ShouldProcess($target, "Move changed file to $bak")) {
        New-Item -ItemType Directory -Force (Split-Path $bak -Parent) | Out-Null
        Move-Item -LiteralPath $target $bak
    }
    Remove-EmptyParents (Split-Path $target -Parent)
    return 'backed-up'
}

# Walks up from Dir to the depot root, removing each directory only while it is empty.
function Remove-EmptyParents([string]$Dir) {
    $root = (Resolve-Path -LiteralPath $depot).Path.TrimEnd('\')
    while ($Dir -and $Dir.TrimEnd('\') -ne $root -and $Dir.StartsWith($root, 'OrdinalIgnoreCase')) {
        if (-not (Test-Path -LiteralPath $Dir)) { $Dir = Split-Path $Dir -Parent; continue }
        if (Get-ChildItem -LiteralPath $Dir -Force) { break }
        if ($PSCmdlet.ShouldProcess($Dir, 'Remove empty directory')) { Remove-Item -LiteralPath $Dir -Force }
        $Dir = Split-Path $Dir -Parent
    }
}

$old = Read-Manifest

if ($Uninstall) {
    $stats = @{ removed = 0; 'backed-up' = 0; absent = 0 }
    foreach ($rel in $old.Keys) { $stats[(Remove-Owned $rel $old[$rel])]++ }
    if ($PSCmdlet.ShouldProcess($manifestPath, 'Remove manifest') -and (Test-Path -LiteralPath $manifestPath)) {
        Remove-Item -LiteralPath $manifestPath -Force
    }
    Write-Host "Battleborn uninstalled from ${depot}: removed $($stats.removed), backed up $($stats['backed-up']) (changed in depot), already absent $($stats.absent)"
    if ($stats['backed-up']) { Write-Host "Changed files kept in $backupRoot" }
    return
}

# --- install / update ---
$files = Get-ChildItem -LiteralPath $src -Recurse -File |
    Where-Object { $_.Name -notin @('Thumbs.db', 'Desktop.ini') }
$new = [ordered]@{}
foreach ($f in $files) { $new[$f.FullName.Substring($src.Length + 1)] = Get-Sha $f.FullName }

# Conflicts: an existing depot file that Battleborn does not own (path compare is
# case-insensitive, like the engine and NTFS).
$ownedLower = @{}; foreach ($k in $old.Keys) { $ownedLower[$k.ToLowerInvariant()] = $true }
$conflicts = @(foreach ($rel in $new.Keys) {
    $target = Join-Path $depot $rel
    if ((Test-Path -LiteralPath $target) -and -not $ownedLower[$rel.ToLowerInvariant()]) { $rel }
})
if ($conflicts.Count) {
    Write-Host "STOPPED: $($conflicts.Count) depot file(s) belong to something else (another mod or your edits):" -ForegroundColor Yellow
    $conflicts | Select-Object -First 40 | ForEach-Object { Write-Host "  $_" }
    if ($conflicts.Count -gt 40) { Write-Host "  ... and $($conflicts.Count - 40) more" }
    Write-Host "Uninstall the other gameplay mod first (two gameplay mods in one depot override each other file by file)."
    exit 1
}

$copied = 0; $same = 0
foreach ($rel in $new.Keys) {
    $target = Join-Path $depot $rel
    if ((Test-Path -LiteralPath $target) -and (Get-Sha $target) -eq $new[$rel]) { $same++; continue }
    if ((Test-Path -LiteralPath $target) -and $old.ContainsKey($rel) -and (Get-Sha $target) -ne $old[$rel]) {
        # Battleborn-owned but edited in the depot since the last deploy: keep the edit.
        $bak = Join-Path $backupRoot $rel
        if ($PSCmdlet.ShouldProcess($target, "Back up depot edit to $bak")) {
            New-Item -ItemType Directory -Force (Split-Path $bak -Parent) | Out-Null
            Copy-Item -LiteralPath $target $bak -Force
        }
    }
    if ($PSCmdlet.ShouldProcess($target, 'Install file')) {
        New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
        Copy-Item -LiteralPath (Join-Path $src $rel) $target -Force
    }
    $copied++
}

# Files Battleborn installed before but no longer ships.
$dropped = 0
foreach ($rel in @($old.Keys)) {
    if (-not $new.Contains($rel)) { Remove-Owned $rel $old[$rel] | Out-Null; $dropped++ }
}

if ($PSCmdlet.ShouldProcess($manifestPath, 'Write manifest')) {
    New-Item -ItemType Directory -Force $UserDir | Out-Null
    $new.Keys | ForEach-Object { "$($new[$_])`t$_" } | Set-Content -LiteralPath $manifestPath -Encoding ascii
}

# Verify: every manifest file present in the depot with the expected hash.
if (-not $WhatIfPreference) {
    $bad = @($new.Keys | Where-Object {
        $t = Join-Path $depot $_; -not (Test-Path -LiteralPath $t) -or (Get-Sha $t) -ne $new[$_]
    })
    if ($bad.Count) { Write-Host "VERIFY FAILED for $($bad.Count) file(s): $($bad -join ', ')" -ForegroundColor Red; exit 1 }
}
Write-Host "Battleborn deployed to ${depot}: $($new.Count) files ($copied written, $same unchanged, $dropped dropped), all hashes verified."
