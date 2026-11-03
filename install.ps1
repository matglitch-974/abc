# Better Claude Instance — installation Windows 10 / 11 (PowerShell).
#   irm https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/install.ps1 | iex
$ErrorActionPreference = 'Stop'
$Repo   = 'https://github.com/matglitch-974/better-claude-instance'
$Branch = if ($env:BCI_BRANCH) { $env:BCI_BRANCH } else { 'main' }
$AI     = Join-Path $HOME 'ai'
$CL     = Join-Path $HOME '.claude'
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

# --- Arborescence et fichiers de base (jamais écrasés) ---------------------------
Say 'Création de ~/ai et ~/project'
'0-persona\system-agents','1-bench','2-tools\0-mcp','2-tools\1-skills','2-tools\2-plugins','2-tools\3-software','3-llm','4-trash' |
  ForEach-Object { New-Item -ItemType Directory -Force (Join-Path $AI $_) | Out-Null }
New-Item -ItemType Directory -Force (Join-Path $HOME 'project') | Out-Null
'user','feedback','project','reference','journal' | ForEach-Object { New-Item -ItemType Directory -Force (Join-Path $AI "memory\$_") | Out-Null }

$Skel = Join-Path $Dest 'skeleton'
Get-ChildItem $Skel -Recurse -File | ForEach-Object {
  $dst = Join-Path $HOME $_.FullName.Substring($Skel.Length + 1)
  if (Test-Path $dst) { Write-Host "conservé : $dst" }
  else { New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null; Copy-Item $_.FullName $dst; Write-Host "créé     : $dst" }
}

# --- Liens Claude Code ------------------------------------------------------------
# Windows : les liens symboliques de fichiers exigent des droits admin.
# CLAUDE.md importe donc AGENTS.md ; les dossiers utilisent des jonctions (sans droits admin).
New-Item -ItemType Directory -Force "$CL\agents" | Out-Null
function Backup($p) { if ((Test-Path $p) -and -not ((Get-Item $p -Force).LinkType)) { Move-Item $p "$p.bak-bci" -Force; Write-Host "sauvegardé : $p.bak-bci" } }

$ClaudeMd = "$CL\CLAUDE.md"
if (-not ((Test-Path $ClaudeMd) -and ((Get-Content $ClaudeMd -Raw) -match '@~/ai/AGENTS.md'))) {
  Backup $ClaudeMd; [IO.File]::WriteAllText($ClaudeMd, "@~/ai/AGENTS.md`n"); Write-Host "lien     : $ClaudeMd -> ~/ai/AGENTS.md"
}
foreach ($pair in @(@("$CL\skills", "$AI\2-tools\1-skills"), @("$CL\agents\system-agents", "$AI\0-persona\system-agents"))) {
  $link, $target = $pair
  if ((Test-Path $link) -and (Get-Item $link -Force).LinkType) { (Get-Item $link -Force).Delete() } else { Backup $link }
  New-Item -ItemType Junction -Path $link -Target $target | Out-Null; Write-Host "lien     : $link -> $target"
}

# --- settings.json : agents intégrés désactivés + hooks sensible/ et mémoire -----
$Bash = Join-Path (Split-Path (Split-Path (Get-Command git).Source)) 'bin\bash.exe'
$Hook = (Join-Path $Dest 'hooks\guard-sensible.sh') -replace '\\','/'
$HookCmd = "`"$($Bash -replace '\\','/')`" `"$Hook`""
$Py = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1).Source
$MemHook = (Join-Path $Dest 'hooks\memory-hook.py') -replace '\\','/'
$MemCmd = "`"$($Py -replace '\\','/')`" `"$MemHook`""
$Deny = 'Agent(Explore)','Agent(Plan)','Agent(general-purpose)','Agent(statusline-setup)','Agent(claude-code-guide)'

$S = "$CL\settings.json"
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

# --- Outils de recherche web (gratuits, sans clé) ; échecs non bloquants ---------
Say 'Outils de recherche web'
if (-not (Get-Command npx -ErrorAction SilentlyContinue)) { winget install --id OpenJS.NodeJS.LTS -e --source winget --accept-package-agreements --accept-source-agreements; Refresh-Path }
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { winget install --id astral-sh.uv -e --source winget --accept-package-agreements --accept-source-agreements; Refresh-Path }
$env:Path = "$HOME\.local\bin;$env:Path"
if (Get-Command claude -ErrorAction SilentlyContinue) {
  foreach ($m in @(@('fetch','uvx','mcp-server-fetch'), @('duckduckgo','uvx','duckduckgo-mcp-server'), @('playwright','npx','-y','@playwright/mcp@latest'))) {
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

Say 'Terminé. Ouvrez un nouveau terminal, puis tapez : claude'
