$repo='C:\Users\danjo\source\repos\kohan2-battleborn'
$nl="`r`n"

# ---- name pools (harvested from vanilla outpost + settlement namelists) ----
$gauri = @('Braadstrad','Tygarn','Tyrton','Thorne','Tyrgar','Hallvei','Asa','Thoragn','Thorunn','Arnorg','Audrunn','Jotta','Braad','Straad','Thorhil','Hrodhil','Jord','Vigun','Thorhal','Grodhil','Ingun','Asta','Thyra','Berd','Solf','Horbran','Thrand','Thrunor','Finaran','Arim','Hork','Thorkel','Berjod','Bogmund','Garlend','Thorgri','Horhald','Thorvar','Ard','Thormod','Ottard','Thrad','Horvarn','Hardi','Akolf','Rund','Sumarno','Vein','Lodvar','Thjar')
$shadow = @('Abarne','Aberri','Agurne','Aimar','Ainhoa','Aintzine','Aiora','Aizeti','Alatz','Alkain','Altzibar','Amalur','Anakoz','Anartz','Etor','Ezkerra','Iigo','Ilazki','Iloz','Odol','Oier','Oneka','Oro','Oxel','Ugutz','Bazil','Bazkoare','Berbiz','Bernat','Bihar','Bilintx','Bizi','Bizkargi','Bortzaioriz','Deunoro','Diagur','Dolore','Doltza','Domeka','Dunixi','Gaizka','Ganix','Garazi','Gurutz','Haritz','Joxepa','Kaxen','Matxin','Nabar','Tartalo')
$haroun = @('Maiar','Miraj','Maja','Majii','Ajaah','Balbala','Akishku','Muih','Certrix','Rhyana','Aodan','Foren','Alva','Aoiser','Moynabr','Myran','Fairen','Rionne','Daigabr','Cathalr','Tasaghr','Artius','Liarbha','Ildadha','Scotar','Shandar','Planth','Apranil','Eyama','Ayaama','Valjaan','Vaajah','Halrahj','Rumarj','Akubar','Alabar','Riimar','Baruka','Dharjun','Ramjur','Mosran','Ahdayira','Dashur','Paar','Jaav','Rajar','Valan','Sulram','Dharjan','Najrahd')
$drauga = @('Kharth','Thargoth','Vargon','Thurnok','Varth','Tharnoth','Tharn','Raht','Mrar','Khanar','Khandar','Ranahk','Tontarn','Nam','Khaan','Kharnoth','Kharn','Khran','Karguk','Golgograth','Jurakan','Gojuk','Ralthajuk','Sholgora','Kargoth','Vurkagoth','Vorgoth','Narroth','Jarroth','Gorakan','Yarkan','Kaanjar','Virghor','Grooth','Kurgoth','Thantok','Thartok','Vartok','Guuntar','Gharth','Saarn','Trajar','Margoth','Raark','Vaatgar','Sark','Rahk','Vikrahk','Varkath','Tundor')
$persons = @('Payne','Ilyana','Kyran','Jensine','Sofiya','Jordan','Garadun','Ethan','Delroba','Caleb','Thain','Javidan','Dylan','Aidan','Shala','Jelal','Tzarkyn','Graeme','Isrel','Aethan','Adrian','Garret','Mayton','Graymar','Fairfax','Dorian','Faran','Jerod','Whelan','Nathan')
$trees = @('Alder','Oak','Pine','Elm','Ash','Birch','Cedar','Maple','Rowan','Willow','Hazel','Yew','Aspen','Beech','Hawthorn','Chestnut')
$darkadj = @('Black','Grey','Blood','Dead','Dark','Grave','Ash','Night','Dusk','Worm','Ghost','Rot','Barrow')
$darkbird = @('Crow','Raven','Vulture','Owl','Bat')

function Combine([string[]]$bases,[string]$fmt,[int]$take){ $bases | Select-Object -First $take | ForEach-Object { $fmt -f $_ } }

$lists = [ordered]@{
  human = [ordered]@{
    woodmill = @('Deepwood Camp','Oakfell Camp','Timberline Camp','Pinewatch Camp','Elmshade Camp','Thornwood Camp','Woodhaven Camp','Silverwood Camp','Greenwood Camp','Bluepine Camp','Blackforest Camp','Havenwood Camp') +
      (Combine $persons "{0}'s Clearing" 10) + (Combine ($persons | Select-Object -Skip 10) "{0}'s Grove" 9) +
      (Combine $trees '{0} Creek Camp' 10) + (Combine ($trees | Select-Object -Skip 10) '{0}shade Lodge' 6) +
      @('Logger''s Rest','Hewer''s Camp','Feller''s Hollow')
    sawmill = @('Greatsaw Mill','Riverlog Mill','Splitpine Sawyard','Ironsaw Mill','Heartwood Mill','Millwright''s Rest','Oakfell Sawyard','Ashford Sawworks','Twinblade Mill','Longsaw Mill','Whipsaw Mill','Broadplank Mill') +
      (Combine $persons "{0}'s Sawworks" 13) + (Combine $trees '{0} Sawmill' 13) + (Combine ($trees | Select-Object -Skip 4) '{0}plank Mill' 12)
    woodmarket = @('Timberfair Market','Woodwright''s Market','Delroba Trading Post','Sawyer''s Exchange','Javidan Timber Fair','Cartwright''s Market','Fairfax Lumber Exchange','Wainwright''s Post','Cooper''s Market','Bowyer''s Exchange','Fletcher''s Market','Joiner''s Exchange') +
      (Combine $persons "{0}'s Timber Yard" 13) + (Combine $trees '{0} Timber Fair' 13) +
      @('Carpenter''s Row','Turner''s Market','Wheeler''s Post','Carver''s Exchange','Shipwright''s Yard','Woodmonger''s Row','Lumberman''s Exchange','Timberwright''s Post','Charcoal Row','Barkpeeler''s Market','Stave Market','Timber Toll House')
  }
  drauga = [ordered]@{
    woodmill  = Combine $drauga 'Ghorn {0}' 50
    sawmill   = Combine $drauga 'Krazh {0}' 50
    woodmarket= Combine $drauga 'Bharg {0}' 50
  }
  gauri = [ordered]@{
    woodmill  = Combine $gauri 'Skog {0}' 50
    sawmill   = Combine $gauri 'Verk {0}' 50
    woodmarket= Combine $gauri 'Torg {0}' 50
  }
  haroun = [ordered]@{
    woodmill  = Combine $haroun 'Ghaba {0}' 50
    sawmill   = Combine $haroun 'Minshar {0}' 50
    woodmarket= Combine $haroun 'Sihr {0}' 50
  }
  shadow = [ordered]@{
    woodmill  = Combine $shadow 'Oihan {0}' 50
    sawmill   = Combine $shadow 'Zur {0}' 50
    woodmarket= Combine $shadow 'Sorgin {0}' 50
  }
  undead = [ordered]@{
    woodmill = @('Gallowwood Camp','Deadfall Lodge','Mirewood Camp','Blackbough Camp','Hangman''s Grove','Widowwood Camp','Crowfeather Camp','Mourner''s Grove','Barrowpine Camp','Duskwood Lodge','Fenwood Camp','Ghostbark Grove') +
      (Combine $darkadj '{0}wood Camp' 13) + (Combine $darkadj '{0}pine Lodge' 13) + (Combine $darkbird "{0}'s Grove" 5) +
      @('Gravebark Camp','Tombwood Camp','Sorrowwood Camp','Witherwood Camp','Palewood Camp','Coldbough Camp','Direwood Camp')
    sawmill = @('Bonesaw Mill','Gravewood Sawworks','Coffin Mill','Splitbone Sawyard','Corpsewood Mill','Black Casket Mill','Gallows Sawyard','Reaper''s Mill','Deadgrain Mill','Charnel Sawworks','Wormrot Mill','Bierwood Mill') +
      (Combine $darkadj '{0}saw Mill' 13) + (Combine $darkadj '{0}wood Sawyard' 13) +
      @('Ossuary Sawworks','Cadaver Mill','Shroudwood Mill','Elegy Mill','Requiem Sawyard','Dirge Mill','Lament Mill','Pyre Mill','Cairn Sawworks','Sexton''s Mill','Gravedigger''s Mill','Undertaker''s Mill')
    woodmarket = @('Soulwood Exchange','Grave Goods Market','Ashen Tithe','Deadman''s Barter','Charnel Exchange','Bonecarver''s Market','Reliquary Market','Black Tithe','Cryptwood Exchange','Mourning Market','Sepulcher Exchange','Vulture''s Barter') +
      (Combine $darkadj '{0}wood Exchange' 13) + (Combine $darkadj '{0} Barter Post' 13) +
      @('Coffinmaker''s Market','Shroudweaver''s Market','Gravedigger''s Exchange','Undertaker''s Post','Embalmer''s Market','Sexton''s Exchange','Cairnwright''s Market','Boneturner''s Post','Ashmonger''s Row','Tombcarver''s Market','Wightmonger''s Row','Pallbearer''s Post')
  }
}

# validate: every list exactly 50, all unique within list
$fail=$false
foreach($f in $lists.Keys){ foreach($type in $lists[$f].Keys){ $l=$lists[$f][$type]; $u=($l | Sort-Object -Unique).Count; if($l.Count -ne 50 -or $u -ne 50){ Write-Host "BAD $f $type count=$($l.Count) unique=$u"; $fail=$true } } }
if($fail){ exit 1 } else { Write-Host 'all 18 lists: 50 unique names each' }

# strip any previously appended BB namelist loc block
$locPath = "$repo\workbench\Localization\strings_data_K2.tgi"
$t = [IO.File]::ReadAllText($locPath)
$marker = "	;; BB wood-outpost namelists (2026-08-14)"
$idx = $t.IndexOf($marker)
if($idx -ge 0){ $t = $t.Substring(0,$idx).TrimEnd() + "`r`n}`r`n"; [IO.File]::WriteAllText($locPath,$t,[Text.UTF8Encoding]::new($true)); Write-Host 'old loc block stripped' }

New-Item -ItemType Directory -Force "$repo\workbench\NameLists" | Out-Null
$locBlock = "$nl	;; BB wood-outpost namelists (2026-08-14)$nl"
foreach($f in $lists.Keys){
  $body = ''
  foreach($type in $lists[$f].Keys){
    $id = "namelist_bb_${f}_${type}"; $kb = "bb_namelist_${f}_${type}"
    $body += "$nl[NameList]$nl{$nl	IDS = $id$nl	name = `"#${kb}_name`"$nl"
    $locBlock += "	${kb}_name = `"BB $((Get-Culture).TextInfo.ToTitleCase($f)) $((Get-Culture).TextInfo.ToTitleCase($type)) Names`"$nl"
    $i = 0
    foreach($n in $lists[$f][$type]){
      $i++
      $key = '{0}_{1:d2}' -f $kb, $i
      $body += "$nl	[Name] ;; $('{0:d2}' -f $i)$nl	name = `"#$key`"$nl"
      $locBlock += "	$key = `"$n`"$nl"
    }
    $body += "}$nl"
  }
  [IO.File]::WriteAllText("$repo\workbench\NameLists\namelist_bb_${f}_wood.tgi", $body)
  Write-Host "wrote NameLists\namelist_bb_${f}_wood.tgi"
}

# append loc block before final closing brace (preserve BOM + CRLF)
$t = [IO.File]::ReadAllText($locPath)
$trimmed = $t.TrimEnd()
if(-not $trimmed.EndsWith('}')){ Write-Host 'ERROR: loc file does not end with }'; exit 1 }
$t = $trimmed.Substring(0, $trimmed.Length-1) + $locBlock + "}$nl"
[IO.File]::WriteAllText($locPath, $t, [Text.UTF8Encoding]::new($true))
Write-Host 'loc keys appended'

New-Item -ItemType Directory -Force "$repo\Data\NameLists" | Out-Null
foreach($f in $lists.Keys){ Copy-Item "$repo\workbench\NameLists\namelist_bb_${f}_wood.tgi" "$repo\Data\NameLists\namelist_bb_${f}_wood.tgi" -Force }
Copy-Item $locPath "$repo\Data\Localization\strings_data_K2.tgi" -Force
Write-Host 'copied namelists + loc to Data'
