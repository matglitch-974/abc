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

# --- settings.json : agents intégrés désactivés + hook sensible/ ----------------
$Bash = Join-Path (Split-Path (Split-Path (Get-Command git).Source)) 'bin\bash.exe'
$Hook = (Join-Path $Dest 'hooks\guard-sensible.sh') -replace '\\','/'
$HookCmd = "`"$($Bash -replace '\\','/')`" `"$Hook`""
$Deny = 'Agent(Explore)','Agent(Plan)','Agent(general-purpose)','Agent(statusline-setup)','Agent(claude-code-guide)'

$S = "$CL\settings.json"
$cfg = if ((Test-Path $S) -and (Get-Content $S -Raw).Trim()) { if (-not (Test-Path "$S.bak-bci")) { Copy-Item $S "$S.bak-bci" }; Get-Content $S -Raw | ConvertFrom-Json } else { [pscustomobject]@{} }
if (-not $cfg.permissions) { $cfg | Add-Member permissions ([pscustomobject]@{}) }
$cfg.permissions | Add-Member deny (@(@($cfg.permissions.deny) + $Deny | Where-Object { $_ } | Select-Object -Unique)) -Force
if (-not $cfg.hooks) { $cfg | Add-Member hooks ([pscustomobject]@{}) }
$pre = @(@($cfg.hooks.PreToolUse) | Where-Object { $_ -and -not ($_.hooks[0].command -like '*guard-sensible*') })
$pre += [pscustomobject]@{ matcher = 'Bash'; hooks = @([pscustomobject]@{ type = 'command'; command = $HookCmd }) }
$cfg.hooks | Add-Member PreToolUse $pre -Force
[IO.File]::WriteAllText($S, ($cfg | ConvertTo-Json -Depth 20))   # UTF-8 sans BOM
Write-Host "réglages : $S"

Say 'Terminé. Ouvrez un nouveau terminal, puis tapez : claude'
