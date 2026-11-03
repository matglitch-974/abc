# Better Claude Instance — installation Windows 10 / 11 (PowerShell).
#   irm https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/install.ps1 | iex
$ErrorActionPreference = 'Stop'
$Repo   = 'https://github.com/matglitch-974/better-claude-instance'
$Branch = if ($env:BCI_BRANCH) { $env:BCI_BRANCH } else { 'main' }
$AI     = Join-Path $HOME 'ai'
$OLD    = Join-Path $HOME '.claude'
$CC     = Join-Path $AI '2-tools\3-software\claude-code'   # CLAUDE_CONFIG_DIR : remplace ~/.claude
$Dest   = Join-Path $AI '2-tools\3-software\better-claude-instance'

function Say($m) { Write-Host "`n==> $m" -ForegroundColor Cyan }
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') }

# --- Git (requis par Claude Code sous Windows) ---------------------------------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  Say 'Installation de Git'
  winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
  Refresh-Path
}

# --- Python (identifiants de sous-agents : agent-id.py) ---------------------------
if (-not (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' })) {
  Say 'Installation de Python'
  winget install --id Python.Python.3.13 -e --source winget --accept-package-agreements --accept-source-agreements
  Refresh-Path
}

# --- Claude Code (installateur officiel) ----------------------------------------
if (-not (Get-Command claude -ErrorAction SilentlyContinue) -and -not (Test-Path "$HOME\.local\bin\claude.exe")) {
  Say 'Installation de Claude Code'
  Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
  Refresh-Path
}

# --- Téléchargement ------------------------------------------------------------
Say 'Téléchargement de Better Claude Instance'
if (Test-Path "$Dest\.git") { git -C $Dest pull -q --ff-only }
else { New-Item -ItemType Directory -Force (Split-Path $Dest) | Out-Null; git clone -q --depth 1 -b $Branch $Repo $Dest }

$Py = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1).Source
$Backup = Join-Path $Dest 'hooks\bci-backup.py'

# --- Sauvegarde avant installation (première installation seulement, conservée à vie) ----
if ((Test-Path $AI) -or (Test-Path $OLD)) { & $Py $Backup install-avant }

# --- Arborescence et fichiers de base (jamais écrasés) ---------------------------
Say 'Création de ~/ai et ~/project'
'0-persona\system-agents','1-bench','2-tools\0-mcp\sensible','2-tools\1-skills','2-tools\2-plugins','2-tools\3-software\claude-code','2-tools\logs','3-llm','4-trash' |
  ForEach-Object { New-Item -ItemType Directory -Force (Join-Path $AI $_) | Out-Null }
New-Item -ItemType Directory -Force (Join-Path $HOME 'project') | Out-Null
'user','feedback','project','reference','journal' | ForEach-Object { New-Item -ItemType Directory -Force (Join-Path $AI "memory\$_") | Out-Null }

$Skel = Join-Path $Dest 'skeleton'
Get-ChildItem $Skel -Recurse -File | ForEach-Object {
  $dst = Join-Path $HOME $_.FullName.Substring($Skel.Length + 1)
  if (Test-Path $dst) { Write-Host "conservé : $dst" }
  else { New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null; Copy-Item $_.FullName $dst; Write-Host "créé     : $dst" }
}

# --- Configuration de Claude Code dans ~/ai (CLAUDE_CONFIG_DIR) ----------------------
[Environment]::SetEnvironmentVariable('CLAUDE_CONFIG_DIR', $CC, 'User'); $env:CLAUDE_CONFIG_DIR = $CC
$Stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
if ((Test-Path $OLD) -and -not (Get-Item $OLD -Force).LinkType) {
  Get-ChildItem $OLD -Force | ForEach-Object {
    $item = $_; $n = $item.Name; $f = $item.FullName           # dans switch, $_ désigne la valeur testée
    if ($item.LinkType) { return }                               # anciens liens BCI : recréés plus bas
    switch ($n) {
      'plugins' { if (-not (Get-ChildItem "$AI\2-tools\2-plugins" -Force)) { Remove-Item "$AI\2-tools\2-plugins"; Move-Item $f "$AI\2-tools\2-plugins" } else { Move-Item $f "$CC\plugins.bak-bci" } }
      { $_ -in 'CLAUDE.md','skills' } { if (-not (Test-Path "$CC\$n.bak-bci")) { Move-Item $f "$CC\$n.bak-bci" } }
      default { if (-not (Test-Path "$CC\$n")) { Move-Item $f "$CC\$n" } }
    }
  }
  Move-Item $OLD "$AI\4-trash\claude-ancien_$Stamp"; Write-Host "migré    : ~/.claude -> $CC (restes dans 4-trash)"
}
$OldJson = Join-Path $HOME '.claude.json'
if (Test-Path $OldJson) { if (Test-Path "$CC\.claude.json") { Move-Item $OldJson "$AI\4-trash\claude.json-ancien_$Stamp" } else { Move-Item $OldJson "$CC\.claude.json" } }

# Windows : les liens symboliques de fichiers exigent des droits admin.
# CLAUDE.md importe donc AGENTS.md ; settings.json reste un vrai fichier dans $CC ; les dossiers sont des jonctions.
New-Item -ItemType Directory -Force "$CC\agents" | Out-Null
function Backup($p) { if ((Test-Path $p) -and -not ((Get-Item $p -Force).LinkType)) { Move-Item $p "$p.bak-bci" -Force; Write-Host "sauvegardé : $p.bak-bci" } }
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
$Bash = Join-Path (Split-Path (Split-Path (Get-Command git).Source)) 'bin\bash.exe'
$Hook = (Join-Path $Dest 'hooks\guard-sensible.sh') -replace '\\','/'
$HookCmd = "`"$($Bash -replace '\\','/')`" `"$Hook`""
$MemHook = (Join-Path $Dest 'hooks\memory-hook.py') -replace '\\','/'
$MemCmd = "`"$($Py -replace '\\','/')`" `"$MemHook`""
$Deny = 'Agent(Explore)','Agent(Plan)','Agent(general-purpose)','Agent(statusline-setup)','Agent(claude-code-guide)'

$S = "$CC\settings.json"
$cfg = if ((Test-Path $S) -and (Get-Content $S -Raw).Trim()) { if (-not (Test-Path "$S.bak-bci")) { Copy-Item $S "$S.bak-bci" }; Get-Content $S -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
if (-not $cfg.permissions) { $cfg | Add-Member permissions ([pscustomobject]@{}) }
$cfg.permissions | Add-Member deny (@(@($cfg.permissions.deny) + $Deny | Where-Object { $_ } | Select-Object -Unique)) -Force
if (-not $cfg.hooks) { $cfg | Add-Member hooks ([pscustomobject]@{}) }
$pre = @(@($cfg.hooks.PreToolUse) | Where-Object { $_ -and -not ($_.hooks[0].command -like '*guard-sensible*') })
$pre += [pscustomobject]@{ matcher = 'Bash'; hooks = @([pscustomobject]@{ type = 'command'; command = $HookCmd }) }
$cfg.hooks | Add-Member PreToolUse $pre -Force
$mem = [pscustomobject]@{ type = 'command'; command = $MemCmd }
foreach ($ev in 'SessionStart','UserPromptSubmit','PostToolUse','PreCompact','Stop','SessionEnd') {
  $list = @(@($cfg.hooks.$ev) | Where-Object { $_ -and -not ($_.hooks[0].command -like '*memory-hook*') })
  $entry = if ($ev -eq 'PostToolUse') { [pscustomobject]@{ matcher = 'Write|Edit|MultiEdit|NotebookEdit'; hooks = @($mem) } } else { [pscustomobject]@{ hooks = @($mem) } }
  $cfg.hooks | Add-Member $ev @($list + $entry) -Force
}
[IO.File]::WriteAllText($S, ($cfg | ConvertTo-Json -Depth 20))   # UTF-8 sans BOM
Write-Host "réglages : $S"

# --- Outils : restic, recherche web (SearXNG local, sans clé) ; non bloquants
Say 'Outils de recherche web et de sauvegarde'
if (-not (Get-Command restic -ErrorAction SilentlyContinue)) { winget install --id restic.restic -e --source winget --accept-package-agreements --accept-source-agreements; Refresh-Path }
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) { winget install --id OpenJS.NodeJS.LTS -e --source winget --accept-package-agreements --accept-source-agreements; Refresh-Path }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { winget install --id astral-sh.uv -e --source winget --accept-package-agreements --accept-source-agreements; Refresh-Path }
$env:Path = "$HOME\.local\bin;$env:Path"
$SXD = "$AI\2-tools\3-software\searxng"
if (Get-Command uv -ErrorAction SilentlyContinue) {
  if (Test-Path "$SXD\.git") { git -C $SXD pull -q --ff-only } else { git clone -q --depth 1 https://github.com/searxng/searxng.git $SXD }
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

# --- Commande bci (dans ~/.local/bin, ajouté au PATH utilisateur si absent) ---------------
$Bin = "$HOME\.local\bin"
New-Item -ItemType Directory -Force $Bin | Out-Null
Copy-Item "$Dest\bin\bci.cmd" "$Bin\bci.cmd" -Force
$UserPath = [Environment]::GetEnvironmentVariable('Path','User')
if (($UserPath -split ';') -notcontains $Bin) { [Environment]::SetEnvironmentVariable('Path', "$UserPath;$Bin", 'User') }

# --- Sauvegarde après installation ---------------------------------------------------
& $Py $Backup install-apres
Say 'Terminé. Ouvrez un nouveau terminal, puis tapez : claude   (mises à jour : bci install)'
