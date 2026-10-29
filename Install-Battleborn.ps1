# Battleborn installer for Kohan II: Kings of War - needs only Windows PowerShell (no Python).
#
# Battleborn ships no game files. This script reads YOUR copy of the game's Data.rwd,
# applies Battleborn's changes (patches/, original/), packs the result into
# <game>\Battleborn\Battleborn.rwd and adds a one-line startup script so the game loads it.
#
#   Install / update:  right-click Install-Battleborn.ps1 > Run with PowerShell
#                      (or double-click Install-Battleborn.cmd)
#   Uninstall:         .\Install-Battleborn.ps1 -Uninstall
#   Other game folder: .\Install-Battleborn.ps1 -GameDir "D:\Games\Kohan II"
#
# Produces the same archive, byte for byte, as the developer tool tools/bb.py.

[CmdletBinding()]
param(
    [string]$GameDir,
    [switch]$Uninstall,
    [switch]$NoPause,
    [string]$OutFile      # build only: write the archive here instead of installing
)

$ErrorActionPreference = 'Stop'
$ModDir = 'Battleborn'
$Archive = 'Battleborn.rwd'
$Startup = 'autoexec_battleborn.txt'
$Marker = '# Battleborn startup script'
$Root = $PSScriptRoot
$Latin1 = [Text.Encoding]::GetEncoding(28591)    # bytes <-> chars 1:1, keeps every byte exact
$Utf8 = New-Object Text.UTF8Encoding($false)

function Finish([int]$code) {
    if (-not $NoPause -and $Host.Name -eq 'ConsoleHost' -and -not $OutFile) { Read-Host 'Press Enter to close' | Out-Null }
    exit $code
}

# ------------------------------------------------------------------ game folder
function Find-Game {
    $roots = @()
    foreach ($k in 'HKCU:\Software\Valve\Steam', 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam') {
        $p = Get-ItemProperty $k -ErrorAction SilentlyContinue
        if ($p.SteamPath) { $roots += $p.SteamPath }
        if ($p.InstallPath) { $roots += $p.InstallPath }
    }
    $roots += 'C:\Program Files (x86)\Steam'
    foreach ($r in $roots) {
        $libs = @($r)
        $vdf = Join-Path $r 'steamapps\libraryfolders.vdf'
        if (Test-Path $vdf) {
            foreach ($m in [regex]::Matches((Get-Content $vdf -Raw), '"path"\s+"([^"]+)"')) { $libs += $m.Groups[1].Value.Replace('\\', '\') }
        }
        foreach ($lib in $libs) {
            $acf = Join-Path $lib 'steamapps\appmanifest_97130.acf'
            if (Test-Path $acf) {
                $m = [regex]::Match((Get-Content $acf -Raw), '"installdir"\s+"([^"]+)"')
                $g = Join-Path $lib ('steamapps\common\' + $m.Groups[1].Value)
                if (Test-Path (Join-Path $g 'Data.rwd')) { return $g }
            }
        }
    }
    return $null
}

# ------------------------------------------------------------------ hashing
$Sha = [Security.Cryptography.SHA256]::Create()
function Get-Sha([byte[]]$b) { ([BitConverter]::ToString($Sha.ComputeHash($b)) -replace '-', '').ToLowerInvariant() }

$CrcTable = New-Object 'uint32[]' 256
for ($n = 0; $n -lt 256; $n++) {
    [uint32]$c = $n
    for ($k = 0; $k -lt 8; $k++) { if ($c -band 1) { $c = [uint32](0xEDB88320L -bxor ($c -shr 1)) } else { $c = $c -shr 1 } }
    $CrcTable[$n] = $c
}
function Get-Crc32([byte[]]$b) {
    [uint32]$c = 0xFFFFFFFFL
    foreach ($x in $b) { $c = [uint32]($CrcTable[($c -bxor $x) -band 0xFF] -bxor ($c -shr 8)) }
    return [uint32]($c -bxor 0xFFFFFFFFL)
}

# ------------------------------------------------------------------ Data.rwd reader
function Open-Rwd([string]$path) {
    $fs = [IO.File]::OpenRead($path)
    $br = New-Object IO.BinaryReader($fs)
    $n = $fs.Length
    $fs.Position = 8; $nsec = $br.ReadUInt32()
    $sections = @{}
    for ($i = 0; $i -lt $nsec; $i++) {
        $fs.Position = $n - 96 * $nsec + 96 * $i
        $name = [Text.Encoding]::Unicode.GetString($br.ReadBytes(64)).TrimEnd([char]0)
        $sections[$name] = @{ Off = $br.ReadUInt64(); Size = $br.ReadUInt64() }
    }
    $fs.Position = $sections['Footer'].Off
    $count = $br.ReadUInt32()
    $entries = @{}
    for ($i = 0; $i -lt $count; $i++) {
        $len = $br.ReadUInt16()
        $name = [Text.Encoding]::Unicode.GetString($br.ReadBytes(2 * $len))
        $off = $br.ReadUInt64(); $size = $br.ReadUInt64(); [void]$br.ReadUInt32(); [void]$br.ReadUInt32()
        $entries[$name.ToLowerInvariant()] = @{ Name = $name; Off = $off; Size = $size }
    }
    return @{ Stream = $fs; Reader = $br; Base = $sections['Files'].Off; Entries = $entries }
}
$script:Cache = @{}
function Get-GameFile([string]$name) {
    $key = $name.ToLowerInvariant()
    if ($script:Cache.ContainsKey($key)) { return , $script:Cache[$key] }
    $e = $script:Rwd.Entries[$key]
    if (-not $e) { return $null }
    $script:Rwd.Stream.Position = $script:Rwd.Base + $e.Off
    $b = $script:Rwd.Reader.ReadBytes([int]$e.Size)
    $script:Cache[$key] = $b
    return , $b
}

# ------------------------------------------------------------------ text helpers (Latin-1 strings = raw bytes)
# Returns @{ Bom = bool; Bodies = string[] } with line endings and BOM removed.
function Split-Text([byte[]]$b) {
    $bom = ($b.Length -ge 3 -and $b[0] -eq 0xEF -and $b[1] -eq 0xBB -and $b[2] -eq 0xBF)
    $s = $Latin1.GetString($b, [int]($(if ($bom) { 3 } else { 0 })), $b.Length - $(if ($bom) { 3 } else { 0 }))
    $parts = $s.Split([char]10)
    $bodies = New-Object 'Collections.Generic.List[string]'
    for ($i = 0; $i -lt $parts.Length; $i++) {
        $p = $parts[$i]
        if ($i -eq $parts.Length - 1) { if ($p.Length -gt 0) { $bodies.Add($p) }; break }
        if ($p.EndsWith([string][char]13)) { $p = $p.Substring(0, $p.Length - 1) }
        $bodies.Add($p)
    }
    return @{ Bom = $bom; Bodies = $bodies }
}
function Get-BaseBodies([string]$name, [string]$expect, [string]$label) {
    $b = Get-GameFile $name
    if ($null -eq $b) { throw "${label}: game file $name not found in Data.rwd" }
    if ($expect -and (Get-Sha $b) -ne $expect) { throw "${label}: game file $name differs from the retail version this patch targets" }
    return , (Split-Text $b).Bodies
}
function Expand-Eol([string]$spec, [int]$count) {
    $map = @{ crlf = "`r`n"; lf = "`n"; none = '' }
    $parts = $spec.Trim().Split(' ')
    $out = New-Object 'Collections.Generic.List[string]'
    if ($parts.Length -eq 1 -and $parts[0] -notmatch '\*') { for ($i = 0; $i -lt $count; $i++) { $out.Add($map[$parts[0]]) }; return , $out }
    for ($i = 0; $i -lt $parts.Length; $i++) {
        $p = $parts[$i]
        if ($p -match '^(\w+)\*(\d+)$') { for ($j = 0; $j -lt [int]$Matches[2]; $j++) { $out.Add($map[$Matches[1]]) } }
        else {
            $rest = 0; for ($q = $i + 1; $q -lt $parts.Length; $q++) { $rest += [int]($parts[$q].Split('*')[1]) }
            $fill = $count - $out.Count - $rest
            for ($j = 0; $j -lt $fill; $j++) { $out.Add($map[$p]) }
        }
    }
    return , $out
}

function Invoke-Patch([string]$text, [string]$label) {
    $base = $null; $baseSha = $null; $refs = @{}; $result = $null; $bom = $false; $eol = 'crlf'
    $hunks = New-Object 'Collections.Generic.List[object]'
    foreach ($line in $text.Split([char]10)) {
        if ($hunks.Count -eq 0) {
            if (-not $line -or $line.StartsWith('#')) { continue }
            if ($line -match '^base (.+) sha256=([0-9a-f]{64})$') { $base = $Matches[1]; $baseSha = $Matches[2]; continue }
            if ($line -match '^ref (.+) sha256=([0-9a-f]{64})$') { $refs[$Matches[1]] = $Matches[2]; continue }
            if ($line -match '^result sha256=([0-9a-f]{64}) bytes=\d+$') { $result = $Matches[1]; continue }
            if ($line -match '^bom (yes|no)$') { $bom = $Matches[1] -eq 'yes'; continue }
            if ($line -match '^eol (.+)$') { $eol = $Matches[1]; continue }
        }
        if ($line.StartsWith('@@ ')) {
            if ($line -notmatch '^@@ (\d+) -(\d+)(?::([0-9a-f]{8}))? \+(\d+) @@') { throw "${label}: bad hunk header $line" }
            $hunks.Add(@{ Start = [int]$Matches[1]; Del = [int]$Matches[2]; Hash = $Matches[3]; Add = [int]$Matches[4]; Body = (New-Object 'Collections.Generic.List[string]') })
        } elseif ($hunks.Count -and $line) { $hunks[$hunks.Count - 1].Body.Add($line) }
    }
    $baseBodies = New-Object 'Collections.Generic.List[string]'
    if ($base) { $baseBodies = Get-BaseBodies $base $baseSha $label }
    $out = New-Object 'Collections.Generic.List[string]'
    $pos = 0
    foreach ($h in $hunks) {
        $s = $h.Start - 1
        if ($s -lt $pos -or $s + $h.Del -gt $baseBodies.Count) { throw "${label}: hunk at line $($h.Start) out of range" }
        for ($i = $pos; $i -lt $s; $i++) { $out.Add($baseBodies[$i]) }
        if ($h.Hash) {
            $removed = New-Object 'Collections.Generic.List[string]'
            for ($i = $s; $i -lt $s + $h.Del; $i++) { $removed.Add($baseBodies[$i]) }
            if ((Get-Sha $Latin1.GetBytes(($removed -join "`n"))).Substring(0, 8) -ne $h.Hash) { throw "${label}: base text at line $($h.Start) is not what the patch expects" }
        }
        $produced = 0
        foreach ($item in $h.Body) {
            if ($item.StartsWith('=')) {
                $m = [regex]::Match($item.Substring(1).Trim(), '^(.+) (\d+)-(\d+)$')
                $name = $m.Groups[1].Value; $a = [int]$m.Groups[2].Value; $z = [int]$m.Groups[3].Value
                if ($base -and $name -eq $base) { $src = $baseBodies } else { $src = Get-BaseBodies $name $refs[$name] $label }
                for ($i = $a - 1; $i -lt $z; $i++) { $out.Add($src[$i]) }
                $produced += $z - $a + 1
            } elseif ($item.StartsWith('+')) {
                $out.Add($Latin1.GetString($Utf8.GetBytes($item.Substring(1))))
                $produced++
            } else { throw "${label}: bad line" }
        }
        if ($produced -ne $h.Add) { throw "${label}: hunk at line $($h.Start) produced $produced lines, expected $($h.Add)" }
        $pos = $s + $h.Del
    }
    for ($i = $pos; $i -lt $baseBodies.Count; $i++) { $out.Add($baseBodies[$i]) }
    $terms = Expand-Eol $eol $out.Count
    if ($terms.Count -ne $out.Count) { throw "${label}: line-ending spec does not cover the file" }
    $sb = New-Object Text.StringBuilder
    for ($i = 0; $i -lt $out.Count; $i++) { [void]$sb.Append($out[$i]).Append($terms[$i]) }
    $bytes = $Latin1.GetBytes($sb.ToString())
    if ($bom) { $bytes = [byte[]](0xEF, 0xBB, 0xBF) + $bytes }
    if ($result -and (Get-Sha $bytes) -ne $result) { throw "${label}: result does not match the expected file" }
    return , $bytes
}

function Invoke-Delta([byte[]]$blob, [string]$label) {
    $hdrEnd = [Array]::IndexOf($blob, [byte]10, 9)
    $meta = $Utf8.GetString($blob, 9, $hdrEnd - 9) | ConvertFrom-Json
    $base = Get-GameFile $meta.base
    if ($null -eq $base) { throw "${label}: game file $($meta.base) not found in Data.rwd" }
    if ((Get-Sha $base) -ne $meta.base_sha256) { throw "${label}: game file $($meta.base) differs from the retail version this delta targets" }
    # BBDELTA1 = zlib(our file XOR game file); BBDELTA2 = zlib(our file) XOR game file
    $v2 = $Utf8.GetString($blob, 0, 9) -eq "BBDELTA2`n"
    $payload = [byte[]]::new($blob.Length - $hdrEnd - 1)
    [Array]::Copy($blob, $hdrEnd + 1, $payload, 0, $payload.Length)
    if ($v2) { for ($i = 0; $i -lt $payload.Length; $i++) { $payload[$i] = $payload[$i] -bxor $base[$i % $base.Length] } }
    # zlib stream = 2-byte header + raw deflate + adler32; .NET Framework reads the raw deflate part
    $ms = [IO.MemoryStream]::new($payload, 2, $payload.Length - 2)
    $ds = New-Object IO.Compression.DeflateStream($ms, [IO.Compression.CompressionMode]::Decompress)
    $outMs = New-Object IO.MemoryStream
    $ds.CopyTo($outMs); $ds.Dispose()
    $x = $outMs.ToArray()
    if (-not $v2) { for ($i = 0; $i -lt $x.Length; $i++) { $x[$i] = $x[$i] -bxor $base[$i % $base.Length] } }
    if ($x.Length -ne $meta.bytes -or (Get-Sha $x) -ne $meta.result_sha256) { throw "${label}: result does not match the expected file" }
    return , $x
}

# ------------------------------------------------------------------ build
function Get-Sources {
    $src = @{}
    foreach ($top in 'patches', 'original') {
        $dir = Join-Path $Root $top
        if (-not (Test-Path $dir)) { continue }
        foreach ($f in Get-ChildItem $dir -Recurse -File) {
            if ($f.Name -in 'Thumbs.db', 'Desktop.ini', '.gitkeep') { continue }
            $rel = $f.FullName.Substring($dir.Length + 1).Replace('\', '/')
            $kind = 'original'
            if ($top -eq 'patches') {
                if ($rel.EndsWith('.bbpatch')) { $kind = 'patch'; $rel = $rel.Substring(0, $rel.Length - 8) }
                elseif ($rel.EndsWith('.bbdelta')) { $kind = 'delta'; $rel = $rel.Substring(0, $rel.Length - 8) }
                else { continue }
            }
            $src[$rel] = @{ Kind = $kind; Path = $f.FullName }
        }
    }
    return $src
}

function Build-Archive([string]$out) {
    $src = Get-Sources
    $names = [string[]]@($src.Keys)
    # same order as bb.py: sort by the lower-cased name, ordinal (OrdinalIgnoreCase upper-cases,
    # which would put '_' after letters and change the archive)
    $keys = [string[]]@($names | ForEach-Object { $_.ToLowerInvariant() })
    [Array]::Sort($keys, $names, [StringComparer]::Ordinal)
    $files = New-Object 'Collections.Generic.List[object]'
    $errors = @()
    foreach ($rel in $names) {
        $s = $src[$rel]
        try {
            if ($s.Kind -eq 'patch') { $data = Invoke-Patch ([IO.File]::ReadAllText($s.Path, $Utf8)) $rel }
            elseif ($s.Kind -eq 'delta') { $data = Invoke-Delta ([IO.File]::ReadAllBytes($s.Path)) $rel }
            else { $data = [IO.File]::ReadAllBytes($s.Path) }
            $files.Add(@{ Name = $rel; Data = $data })
        } catch { $errors += "  ${rel}: $($_.Exception.Message)" }
    }
    if ($errors) { throw ("Build failed:`n" + ($errors -join "`n")) }

    # stamp = CRC32 of SHA256 over (lower-case name, NUL, bytes) for every file - matches bb.py
    $digest = [Security.Cryptography.SHA256]::Create()
    foreach ($f in $files) {
        $nb = $Utf8.GetBytes($f.Name.ToLowerInvariant() + [char]0)
        [void]$digest.TransformBlock($nb, 0, $nb.Length, $null, 0)
        [void]$digest.TransformBlock($f.Data, 0, $f.Data.Length, $null, 0)
    }
    [void]$digest.TransformFinalBlock((New-Object byte[] 0), 0, 0)
    $stamp = Get-Crc32 $digest.Hash

    $tmp = "$out.tmp"
    $fs = [IO.File]::Create($tmp)
    $bw = New-Object IO.BinaryWriter($fs)
    $bw.Write([Text.Encoding]::ASCII.GetBytes('TGCK')); $bw.Write([uint32]2); $bw.Write([uint32]3)
    $hdr = New-Object IO.MemoryStream; $hw = New-Object IO.BinaryWriter($hdr)
    $hw.Write([uint32]2); $hw.Write([uint16]2); $hw.Write([Text.Encoding]::Unicode.GetBytes('K2')); $hw.Write([uint32]0); $hw.Write([uint32]$stamp)
    $hdrBytes = $hdr.ToArray()
    $bw.Write($hdrBytes)
    $filesOff = 12 + $hdrBytes.Length
    $offsets = @(); [uint64]$rel = 0
    foreach ($f in $files) { $offsets += $rel; $bw.Write([byte[]]$f.Data); $rel += [uint64]$f.Data.Length }
    $foot = New-Object IO.MemoryStream; $fw = New-Object IO.BinaryWriter($foot)
    $fw.Write([uint32]$files.Count)
    for ($i = 0; $i -lt $files.Count; $i++) {
        $fw.Write([uint16]$files[$i].Name.Length); $fw.Write([Text.Encoding]::Unicode.GetBytes($files[$i].Name))
        $fw.Write([uint64]$offsets[$i]); $fw.Write([uint64]$files[$i].Data.Length); $fw.Write([uint32]0); $fw.Write([uint32]$i)
    }
    $footBytes = $foot.ToArray()
    $footOff = [uint64]$filesOff + $rel
    $bw.Write($footBytes)
    foreach ($sec in @(@('Header', 12, $hdrBytes.Length), @('Files', $filesOff, $rel), @('Footer', $footOff, $footBytes.Length))) {
        $nameBytes = New-Object byte[] 64
        $nb = [Text.Encoding]::Unicode.GetBytes($sec[0]); [Array]::Copy($nb, $nameBytes, $nb.Length)
        $bw.Write($nameBytes); $bw.Write([uint64]$sec[1]); $bw.Write([uint64]$sec[2]); $bw.Write([uint32]0); $bw.Write([uint32]0); $bw.Write([uint64]$sec[2])
    }
    $bw.Dispose()
    Move-Item -LiteralPath $tmp $out -Force
    return @{ Count = $files.Count; Stamp = $stamp }
}

# ------------------------------------------------------------------ main
try {
    if (-not $GameDir) { $GameDir = Find-Game }
    if (-not $GameDir -or -not (Test-Path (Join-Path $GameDir 'Data.rwd'))) { throw 'Kohan II not found. Run again with -GameDir "<folder that contains Data.rwd>".' }
    $script_ = Join-Path $GameDir "startup\$Startup"
    $arcPath = Join-Path $GameDir "$ModDir\$Archive"

    if ($Uninstall) {
        if (Test-Path $script_) {
            if (-not (Get-Content $script_ -Raw).StartsWith($Marker)) { throw "$script_ was not written by Battleborn - left alone" }
            Remove-Item -LiteralPath $script_
        }
        if (Test-Path $arcPath) { Remove-Item -LiteralPath $arcPath }
        $d = Join-Path $GameDir $ModDir
        if ((Test-Path $d) -and -not (Get-ChildItem $d -Force)) { Remove-Item -LiteralPath $d }
        Write-Host 'Battleborn uninstalled.'
        Finish 0
    }

    if (Get-Process k2 -ErrorAction SilentlyContinue) { throw 'Kohan II is running - close it first.' }
    $script:Rwd = Open-Rwd (Join-Path $GameDir 'Data.rwd')
    try {
        if ($OutFile) { $target = $OutFile } else {
            New-Item -ItemType Directory -Force (Join-Path $GameDir $ModDir) | Out-Null
            $target = $arcPath
        }
        Write-Host "Building Battleborn from $GameDir\Data.rwd ..."
        $r = Build-Archive $target
    } finally { $script:Rwd.Stream.Dispose() }
    if ($OutFile) { Write-Host ("Built {0}: {1} files, stamp {2:x8}" -f $OutFile, $r.Count, $r.Stamp); Finish 0 }

    $lines = @("$Marker - written by Install-Battleborn.ps1; delete it (or run with -Uninstall) to disable.", "addmod $ModDir/$Archive")
    [IO.File]::WriteAllText($script_, (($lines -join "`r`n") + "`r`n"), [Text.Encoding]::ASCII)
    Write-Host ("Installed Battleborn: {0} files, stamp {1:x8}" -f $r.Count, $r.Stamp)
    Write-Host "  $arcPath"
    Write-Host "  $script_"
    Write-Host 'Start Kohan II through Steam as usual. In multiplayer every player needs the same Battleborn version.'
    Finish 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    Finish 1
}
