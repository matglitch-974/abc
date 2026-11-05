# BCAI — installation Windows 10 / 11 (PowerShell).
#   irm matglitch-974.github.io/bc.ps1 | iex
#   (secours : irm https://raw.githubusercontent.com/matglitch-974/bcai/main/install.ps1 | iex)
$ErrorActionPreference = 'Stop'
$Repo   = 'https://github.com/matglitch-974/bcai'
$Branch = if ($env:BCAI_BRANCH) { $env:BCAI_BRANCH } elseif ($env:BCI_BRANCH) { $env:BCI_BRANCH } else { 'main' }   # BCI_BRANCH : ancien nom
$AI     = Join-Path $HOME 'ai'
$OLD    = Join-Path $HOME '.claude'
$CC     = Join-Path $AI '2-tools\3-software\claude-code'   # CLAUDE_CONFIG_DIR : remplace ~/.claude
$Dest   = Join-Path $AI '2-tools\3-software\bcai'
$OldDest = Join-Path $AI '2-tools\3-software\better-claude-instance'   # emplacement d'avant le renommage en BCAI

function Say($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') + ";$HOME\.local\bin" }
$HasWinget = [bool](Get-Command winget -ErrorAction SilentlyContinue)   # absent sur les Windows allégés
function Winget($id) {
  if (-not $HasWinget) { return $false }
  winget install --id $id -e --source winget --accept-package-agreements --accept-source-agreements; Refresh-Path; return $true
}
# Python hors PATH (installé pour l'utilisateur seul, alias WindowsApps) : chercher aussi le lanceur py et les dossiers usuels.
function Find-Python {
  $c = Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1
  if ($c) { return $c.Source }
  if (Get-Command py -ErrorAction SilentlyContinue) { $p = & py -3 -c 'import sys; print(sys.executable)' 2>$null; if ($p -and (Test-Path $p)) { return $p } }
  $c = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe", "$env:ProgramFiles\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object { [int]($_.Directory.Name -replace '\D','') } -Descending | Select-Object -First 1
  if ($c) { return $c.FullName }
  if (Get-Command uv -ErrorAction SilentlyContinue) { $p = & uv python find 3.13 2>$null; if ($p -and (Test-Path $p)) { return $p } }
  return $null
}

# --- Git (requis par Claude Code sous Windows) ---------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Say 'Installation de Git'
  if (-not (Winget 'Git.Git')) { Write-Error 'Git est requis et winget est absent : installez Git pour Windows (git-scm.com), puis relancez.' }
}

# --- uv (outils Python ; sert aussi à installer Python sans winget) -------------------
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Say 'Installation de uv'
  if (-not (Winget 'astral-sh.uv')) { Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression; Refresh-Path }
}

# --- Python (identifiants de sous-agents, hooks) -----------------------------------
if (-not (Find-Python)) {
  Say 'Installation de Python'
  if (-not (Winget 'Python.Python.3.13')) { uv python install 3.13 }
}

# --- Claude Code (installateur officiel) ----------------------------------------
if (-not (Get-Command claude -ErrorAction SilentlyContinue) -and -not (Test-Path "$HOME\.local\bin\claude.exe")) {
  Say 'Installation de Claude Code'
  Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
  Refresh-Path
}

# --- Téléchargement ------------------------------------------------------------
Say 'Téléchargement de BCAI'
# Installation d'avant BCAI : le dossier est renommé ; une jonction reste à l'ancien emplacement pour les
# sessions Claude ouvertes, qui appellent encore les hooks par là (retirée ensuite par memory-hook.py).
# Dossier tenu par un programme : nouveau clone, l'ancien est rangé plus tard par le hook mémoire.
if ((Test-Path $OldDest) -and -not (Get-Item $OldDest -Force).LinkType -and -not (Test-Path $Dest)) {
  try { [IO.Directory]::Move($OldDest, $Dest); Write-Host "renommé  : $OldDest -> $Dest" }
  catch { Write-Host "en cache : $OldDest est encore utilisé ; nouveau clone dans $Dest" }
  if ((Test-Path $Dest) -and -not (Test-Path $OldDest)) {
    try { New-Item -ItemType Junction -Path $OldDest -Target $Dest | Out-Null } catch { Write-Warning "jonction $OldDest impossible : $_" }
  }
}
if (Test-Path "$Dest\.git") { git -C $Dest remote set-url origin $Repo; git -C $Dest pull -q --ff-only }   # set-url : clone de l'ancien dépôt
else { New-Item -ItemType Directory -Force (Split-Path $Dest) | Out-Null; git clone -q --depth 1 -b $Branch $Repo $Dest }

$Py = Find-Python
if (-not $Py) { Write-Error 'Python introuvable après installation : installez Python 3 (python.org), puis relancez.' }
$Backup = Join-Path $Dest 'hooks\bcai-backup.py'

# --- Installation d'avant BCAI (better-claude-instance, backup-bci) : migration ---------------
# Sauvegardes reprises, chemins de settings.json corrigés (copie d'abord dans backup-bcai\reglages),
# commandes et fichiers du skeleton mis à jour.
& $Py (Join-Path $Dest 'hooks\bcai-migrate.py')

# --- Sauvegarde avant installation (première installation seulement, conservée à vie) ----
if ((Test-Path $AI) -or (Test-Path $OLD)) { & $Py $Backup install-avant }

# --- Arborescence et fichiers de base (jamais écrasés) ---------------------------
Say 'Création de ~/ai et ~/project'
'0-persona\system-agents','1-bench','2-tools\0-mcp','2-tools\1-skills','2-tools\2-plugins','2-tools\3-software\claude-code','2-tools\logs','3-llm','4-trash' |
  ForEach-Object { New-Item -ItemType Directory -Force (Join-Path $AI $_) | Out-Null }
New-Item -ItemType Directory -Force (Join-Path $HOME 'project') | Out-Null
'user','feedback','project','reference','journal' | ForEach-Object { New-Item -ItemType Directory -Force (Join-Path $AI "memory\$_") | Out-Null }

$Skel = Join-Path $Dest 'skeleton'
Get-ChildItem $Skel -Recurse -File | ForEach-Object {
  $dst = Join-Path $HOME $_.FullName.Substring($Skel.Length + 1)
  if (Test-Path $dst) { Write-Host "conservé : $dst" }
  else { New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null; Copy-Item $_.FullName $dst; Write-Host "créé     : $dst" }
}

# --- Import de l'existant (copies) : skills, secrets -> 2-tools\4-keys-code, autres LLM -> 3-llm ---
Say "Import de l'existant (skills, clés et jetons, autres LLM)"
& $Py (Join-Path $Dest 'hooks\bcai-import.py') all

# --- Configuration de Claude Code dans ~/ai (CLAUDE_CONFIG_DIR) ----------------------
[Environment]::SetEnvironmentVariable('CLAUDE_CONFIG_DIR', $CC, 'User'); $env:CLAUDE_CONFIG_DIR = $CC
$Stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
# Migration par copie : une session Claude ouverte garde des fichiers de ~/.claude verrouillés.
# Les fichiers illisibles sont sautés (ce ne sont que des caches de session) ; l'original est ensuite
# rangé dans 4-trash. S'il est encore tenu, il reste en cache temporaire jusqu'au prochain démarrage
# d'une session BCAI (memory-hook.py) ou au prochain `bcai install`, qui le rangent à leur tour.
function Copy-Soft($from, $to) {
  if (Test-Path $to) { return }
  Copy-Item $from $to -Recurse -Force -ErrorAction SilentlyContinue -ErrorVariable err
  if ($err) { Write-Host "sauté    : $($err.Count) fichier(s) en cours d'utilisation dans $from" }
}
function Retire($p, $label) {
  if (-not (Test-Path $p)) { return }
  # Renommage atomique : Move-Item copierait puis supprimerait élément par élément (déplacement partiel).
  $dst = "$AI\4-trash\$label`_$Stamp"
  try { if (Test-Path $p -PathType Container) { [IO.Directory]::Move($p, $dst) } else { [IO.File]::Move($p, $dst) }; Write-Host "rangé    : $p -> 4-trash" }
  catch { Write-Host "en cache : $p est encore utilisé par une session ouverte ; rangé au prochain démarrage de BCAI" }
}
if ((Test-Path $OLD) -and -not (Get-Item $OLD -Force).LinkType) {
  Get-ChildItem $OLD -Force | ForEach-Object {
    $item = $_; $n = $item.Name; $f = $item.FullName           # dans switch, $_ désigne la valeur testée
    if ($item.LinkType) { return }                               # anciens liens BCAI : recréés plus bas
    switch ($n) {
      'plugins' { if (-not (Get-ChildItem "$AI\2-tools\2-plugins" -Force)) { Remove-Item "$AI\2-tools\2-plugins"; Copy-Soft $f "$AI\2-tools\2-plugins" } else { Copy-Soft $f "$CC\plugins.bak-bcai" } }
      { $_ -in 'CLAUDE.md','skills' } { Copy-Soft $f "$CC\$n.bak-bcai" }
      default { Copy-Soft $f "$CC\$n" }
    }
  }
  Write-Host "migré    : ~/.claude -> $CC"
  Retire $OLD 'claude-ancien'
  # Sessions Claude encore ouvertes (hors BCAI) : leur laisser les identifiants, sinon elles sont déconnectées.
  # Ce reliquat est rangé par memory-hook.py dès qu'aucune autre session ne tourne.
  $Cred = "$AI\4-trash\claude-ancien_$Stamp\.credentials.json"
  if (-not (Test-Path $OLD) -and (Test-Path $Cred) -and (Get-Process claude -ErrorAction SilentlyContinue)) {
    New-Item -ItemType Directory -Force $OLD | Out-Null; Copy-Item $Cred "$OLD\.credentials.json"
    Write-Host "gardé    : ~/.claude/.credentials.json (sessions Claude ouvertes ; rangé quand elles seront fermées)"
  }
}
$OldJson = Join-Path $HOME '.claude.json'
if (Test-Path $OldJson) { Copy-Soft $OldJson "$CC\.claude.json"; Retire $OldJson 'claude.json-ancien' }

# Windows : les liens symboliques de fichiers exigent des droits admin.
# CLAUDE.md importe donc AGENTS.md ; settings.json reste un vrai fichier dans $CC ; les dossiers sont des jonctions.
New-Item -ItemType Directory -Force "$CC\agents" | Out-Null
function Backup($p) {   # une copie .bak-bcai existante n'est jamais écrasée : suffixe daté, puis -N
  if (-not (Test-Path $p) -or (Get-Item $p -Force).LinkType) { return }
  $b = "$p.bak-bcai"; $i = 1
  if (Test-Path -LiteralPath $b) { $b = "$p.bak-bcai-$Stamp"; while (Test-Path -LiteralPath $b) { $b = "$p.bak-bcai-$Stamp-$i"; $i++ } }
  Move-Item -LiteralPath $p $b -Force; Write-Host "sauvegardé : $b"
}
$ClaudeMd = "$CC\CLAUDE.md"
if (-not ((Test-Path $ClaudeMd) -and ((Get-Content $ClaudeMd -Raw) -match '@~/ai/AGENTS.md'))) {
  Backup $ClaudeMd; [IO.File]::WriteAllText($ClaudeMd, "@~/ai/AGENTS.md`n"); Write-Host "lien     : $ClaudeMd -> ~/ai/AGENTS.md"
}
foreach ($pair in @(@("$CC\skills", "$AI\2-tools\1-skills"), @("$CC\plugins", "$AI\2-tools\2-plugins"), @("$CC\agents\system-agents", "$AI\0-persona\system-agents"))) {
  $link, $target = $pair
  if ((Test-Path $link) -and (Get-Item $link -Force).LinkType) { (Get-Item $link -Force).Delete() } else { Backup $link }
  New-Item -ItemType Junction -Path $link -Target $target | Out-Null; Write-Host "lien     : $link -> $target"
}

# --- settings.json : agents intégrés désactivés + hooks sensible/ et mémoire -----
# bash de Git : remonter depuis git.exe (cmd\, bin\ ou mingw64\bin\ selon le PATH) jusqu'à la racine de Git
$Bash = $null; $d = Split-Path (Get-Command git).Source
while ($d -and -not $Bash) { if (Test-Path "$d\bin\bash.exe") { $Bash = "$d\bin\bash.exe" } else { $d = Split-Path $d } }
if (-not $Bash) { Write-Warning 'bash de Git introuvable : hook guard-sensible inactif'; $Bash = 'bash' }
$Hook = (Join-Path $Dest 'hooks\guard-sensible.sh') -replace '\\','/'
$HookCmd = "`"$($Bash -replace '\\','/')`" `"$Hook`""
$MemHook = (Join-Path $Dest 'hooks\memory-hook.py') -replace '\\','/'
$MemCmd = "`"$($Py -replace '\\','/')`" `"$MemHook`""
$Deny = 'Agent(Explore)','Agent(Plan)','Agent(general-purpose)','Agent(statusline-setup)','Agent(claude-code-guide)','Agent(claude)'

$S = "$CC\settings.json"
$cfg = if ((Test-Path $S) -and (Get-Content $S -Raw).Trim()) { if (-not (Test-Path "$S.bak-bcai") -and -not (Test-Path "$S.bak-bci")) { Copy-Item $S "$S.bak-bcai" }; Get-Content $S -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
if (-not $cfg.permissions) { $cfg | Add-Member permissions ([pscustomobject]@{}) }
$cfg.permissions | Add-Member deny (@(@($cfg.permissions.deny) + $Deny | Where-Object { $_ } | Select-Object -Unique)) -Force
if (-not $cfg.hooks) { $cfg | Add-Member hooks ([pscustomobject]@{}) }
$pre = @(@($cfg.hooks.PreToolUse) | Where-Object { $_ -and -not ($_.hooks[0].command -like '*guard-sensible*') })
$pre += [pscustomobject]@{ matcher = 'Bash'; hooks = @([pscustomobject]@{ type = 'command'; command = $HookCmd }) }
$cfg.hooks | Add-Member PreToolUse $pre -Force
$mem = [pscustomobject]@{ type = 'command'; command = $MemCmd }
foreach ($ev in 'SessionStart','UserPromptSubmit','PreToolUse','PostToolUse','PreCompact','Stop','SessionEnd') {
  $list = @(@($cfg.hooks.$ev) | Where-Object { $_ -and -not ($_.hooks[0].command -like '*memory-hook*') })
  $entry = if ($ev -eq 'PostToolUse') { [pscustomobject]@{ matcher = 'Write|Edit|MultiEdit|NotebookEdit'; hooks = @($mem) } }
           elseif ($ev -eq 'PreToolUse') { [pscustomobject]@{ matcher = 'Read|Write|Edit|MultiEdit|NotebookEdit|Glob|Grep|Bash'; hooks = @($mem) } }   # cloison des agents isolés
           else { [pscustomobject]@{ hooks = @($mem) } }
  $cfg.hooks | Add-Member $ev @($list + $entry) -Force
}
$Json = $cfg | ConvertTo-Json -Depth 20
if ((Test-Path $S) -and ([IO.File]::ReadAllText($S) -cne $Json)) {   # copie datée avant toute écriture
  $Keep = "$AI\2-tools\logs\backup-bcai\reglages"
  New-Item -ItemType Directory -Force $Keep | Out-Null; Copy-Item $S "$Keep\settings.json_$Stamp"
}
[IO.File]::WriteAllText($S, $Json)   # UTF-8 sans BOM
Write-Host "réglages : $S"

# --- Outils : restic, recherche web (SearXNG local, sans clé) ; non bloquants
Say 'Outils de recherche web et de sauvegarde'
# Section non bloquante : en mode Stop, PowerShell 5.1 change le stderr redirigé d'un programme
# (« No MCP server named … ») en erreur fatale. Les échecs sont signalés par $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
if (-not (Get-Command restic -ErrorAction SilentlyContinue) -and -not (Winget 'restic.restic')) {
  # sans winget : binaire officiel depuis les releases GitHub, dans ~/.local/bin
  try {
    $rel = Invoke-RestMethod https://api.github.com/repos/restic/restic/releases/latest
    $url = ($rel.assets | Where-Object { $_.name -like '*_windows_amd64.zip' } | Select-Object -First 1).browser_download_url
    $zip = Join-Path $env:TEMP 'restic.zip'; $tmp = Join-Path $env:TEMP 'restic-bcai'
    Invoke-WebRequest $url -OutFile $zip -UseBasicParsing; Expand-Archive $zip $tmp -Force
    New-Item -ItemType Directory -Force "$HOME\.local\bin" | Out-Null
    Move-Item (Get-ChildItem "$tmp\restic*.exe" | Select-Object -First 1).FullName "$HOME\.local\bin\restic.exe" -Force
    Remove-Item $zip, $tmp -Recurse -Force; Refresh-Path
  } catch { Write-Warning "restic non installé (sauvegardes en tar.xz, pas de coffre chiffré) : $_" }
}
if (-not (Get-Command npx -ErrorAction SilentlyContinue) -and -not (Winget 'OpenJS.NodeJS.LTS')) { Write-Warning 'Node.js absent et winget indisponible : MCP searxng et playwright non installés (nodejs.org)' }
$env:Path = "$HOME\.local\bin;$env:Path"
$SXD = "$AI\2-tools\3-software\searxng"
if (Get-Command uv -ErrorAction SilentlyContinue) {
  # Le dépôt contient 4 gabarits dont le nom porte « : » (utils/templates), refusés par Git sous Windows :
  # protectNTFS levé pour ce dépôt seul ; ces fichiers ne sont pas écrits (inutiles en local).
  # Un clone cassé par l'ancienne méthode (sans requirements.txt) part dans 4-trash et est refait.
  if ((Test-Path $SXD) -and -not (Test-Path "$SXD\requirements.txt")) { Move-Item $SXD "$AI\4-trash\searxng-casse_$Stamp" }
  if (Test-Path "$SXD\.git") { git -C $SXD -c core.protectNTFS=false pull -q --ff-only }
  else { git -c core.protectNTFS=false clone -q --depth 1 https://github.com/searxng/searxng.git $SXD; git -C $SXD config core.protectNTFS false }
  if (-not (Test-Path "$SXD\.venv")) { uv venv -q "$SXD\.venv" }
  $env:VIRTUAL_ENV = "$SXD\.venv"
  uv pip install -q setuptools wheel -r "$SXD\requirements.txt"
  if ($LASTEXITCODE -eq 0) { uv pip install -q --no-build-isolation -e $SXD }
  if ($LASTEXITCODE -ne 0) { Write-Warning 'SearXNG non installé (recherche web indisponible)' }
  Remove-Item Env:VIRTUAL_ENV
}
if (Get-Command claude -ErrorAction SilentlyContinue) {
  foreach ($old in 'duckduckgo','brave') { claude mcp remove -s user $old *> $null }   # remplacés par SearXNG
  claude mcp get searxng *> $null
  if ($LASTEXITCODE -ne 0) { claude mcp add -s user searxng -e 'SEARXNG_URL=http://127.0.0.1:8888' -- npx -y mcp-searxng; if ($LASTEXITCODE -ne 0) { Write-Warning 'MCP searxng non installé' } }
  foreach ($m in @(@('fetch','uvx','mcp-server-fetch'), @('playwright','npx','-y','@playwright/mcp@latest'))) {
    claude mcp get $m[0] *> $null
    if ($LASTEXITCODE -ne 0) { claude mcp add -s user $m[0] -- @($m[1..($m.Count-1)]); if ($LASTEXITCODE -ne 0) { Write-Warning "MCP $($m[0]) non installé" } }
  }
}
if ((Get-Command uv -ErrorAction SilentlyContinue) -and -not (Get-Command scrapling -ErrorAction SilentlyContinue)) {
  uv tool install -q 'scrapling[ai,fetchers]'; if ($LASTEXITCODE -eq 0) { scrapling install } else { Write-Warning 'Scrapling non installé' }
}
if ((Get-Command claude -ErrorAction SilentlyContinue) -and (Get-Command scrapling -ErrorAction SilentlyContinue)) {
  claude mcp get scrapling *> $null; if ($LASTEXITCODE -ne 0) { claude mcp add -s user scrapling -- scrapling mcp }
}
if ((Get-Command uv -ErrorAction SilentlyContinue) -and -not (Get-Command crwl -ErrorAction SilentlyContinue)) {
  uv tool install -q crawl4ai; if ($LASTEXITCODE -eq 0) { crawl4ai-setup } else { Write-Warning 'Crawl4AI non installé' }
}

# --- Commande bcai (dans ~/.local/bin, ajouté au PATH utilisateur si absent) ---------------
$Bin = "$HOME\.local\bin"
New-Item -ItemType Directory -Force $Bin | Out-Null
Copy-Item "$Dest\bin\bcai.cmd" "$Bin\bcai.cmd" -Force
# bci : ancien nom (obsolète), gardé s'il était installé. Le nouveau bci.cmd est plus court que l'ancien :
# cmd.exe relit un .cmd modifié pendant son exécution à la même position, et n'y trouve que la fin du fichier.
if (Test-Path "$Bin\bci.cmd") { Copy-Item "$Dest\bin\bci.cmd" "$Bin\bci.cmd" -Force }
$UserPath = [Environment]::GetEnvironmentVariable('Path','User')
if (($UserPath -split ';') -notcontains $Bin) { [Environment]::SetEnvironmentVariable('Path', "$UserPath;$Bin", 'User') }

# --- Sauvegarde après installation ---------------------------------------------------
# --- Chiffrement de 4-keys-code (au choix ; BCAI_ENCRYPT_KEYS=oui|non évite la question) ------
$Keys = Join-Path $Dest 'hooks\bcai-keys.py'
if ((Test-Path "$AI\2-tools\4-keys-code") -and -not (Test-Path "$AI\2-tools\4-keys-code.restic\config") -and (Get-Command restic -ErrorAction SilentlyContinue)) {
  $ans = if ($env:BCAI_ENCRYPT_KEYS) { $env:BCAI_ENCRYPT_KEYS } elseif ($env:BCI_ENCRYPT_KEYS) { $env:BCI_ENCRYPT_KEYS } else { Read-Host "Chiffrer ~/ai/2-tools/4-keys-code (clés SSH, jetons, cookies) avec une phrase secrète ? [o/N]" }
  if ($ans -match '^(o|oui|y|yes)$') { & $Py $Keys close }
}

& $Py $Backup install-apres
Say 'Terminé. Ouvrez un nouveau terminal, puis tapez : claude   (mises à jour : bcai install)'
