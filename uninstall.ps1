# ABC - desinstallation Windows (PowerShell).
#   irm https://raw.githubusercontent.com/matglitch-974/abc/main/uninstall.ps1 | iex
# Remet la configuration de Claude Code dans ~/.claude, retire les liens et reglages ajoutes,
# puis demande avant de toucher a ~/ai et ~/project. Claude Code reste installe.
$ErrorActionPreference = 'Stop'
function Confirm2($Warning, $Question, $Word) {   # deux confirmations : [o/N], puis le mot tape en entier
  Write-Host $Warning -ForegroundColor Red
  if ((Read-Host "$Question [o/N]") -notin 'o','O') { return $false }
  if ((Read-Host "Seconde confirmation : tapez '$Word'") -ne $Word) { Write-Host 'Annule.'; return $false }
  return $true
}
if (-not (Confirm2 'ATTENTION : la desinstallation retire ABC de Claude Code (reglages, hooks, liens, variable CLAUDE_CONFIG_DIR) et remet la configuration dans ~/.claude. Vos dossiers ~/ai et ~/project restent en place, sauf si vous demandez ensuite leur suppression.' 'Desinstaller ABC ?' 'desinstaller')) { Write-Host "Rien n'a ete modifie."; exit 0 }
$AI = Join-Path $HOME 'ai'
$CC = Join-Path $AI '2-tools\3-software\claude-code'
$CL = Join-Path $HOME '.claude'

# 1. Configuration : ~/ai/2-tools/3-software/claude-code -> ~/.claude (jonctions remplacees par des copies)
if ((Test-Path $CC) -and -not (Test-Path $CL)) {
  foreach ($j in "$CC\skills", "$CC\agents\0-persona", "$CC\agents\system-agents", "$CC\plugins") {   # system-agents : ancien lien
    if ((Test-Path $j) -and (Get-Item $j -Force).LinkType) {
      $target = (Get-Item $j -Force).Target; (Get-Item $j -Force).Delete()
      if ($j -like '*\plugins' -and $target -and (Test-Path $target)) { Copy-Item $target $j -Recurse; Write-Host "copie : $j" }
    }
  }
  $ClaudeMd = "$CC\CLAUDE.md"
  if ((Test-Path $ClaudeMd) -and ((Get-Content $ClaudeMd -Raw) -match '@~/ai/AGENTS.md')) { Remove-Item $ClaudeMd }
  Move-Item $CC $CL; Write-Host "configuration remise : $CL"
  if ((Test-Path "$CL\.claude.json") -and -not (Test-Path "$HOME\.claude.json")) { Move-Item "$CL\.claude.json" "$HOME\.claude.json" }
  Get-ChildItem $CL -Force | Where-Object { $_.Name -match '\.bak-(abc|bcai|bci)$' } | ForEach-Object {   # .bak-bcai, .bak-bci : d'avant ABC
    $orig = $_.FullName -replace '\.bak-(abc|bcai|bci)$',''
    if (-not (Test-Path $orig)) { Move-Item $_.FullName $orig; Write-Host "restaure : $orig" }
  }
}
Remove-Item "$HOME\.local\bin\abc.cmd", "$HOME\.local\bin\bcai.cmd", "$HOME\.local\bin\bci.cmd" -ErrorAction SilentlyContinue   # bcai, bci : anciens noms
# Commande de Claude Code : agent.exe redevient claude.exe (s'il s'agit bien de Claude Code et que claude.exe est libre)
$Cli = if ($env:ABC_CLI) { $env:ABC_CLI } else { 'agent' }
$Exe = "$HOME\.local\bin\$Cli.exe"
if ($Cli -ne 'claude' -and (Test-Path $Exe) -and -not (Test-Path "$HOME\.local\bin\claude.exe") -and ((& $Exe --version 2>$null | Select-Object -First 1) -match 'Claude Code')) {
  Rename-Item $Exe 'claude.exe'; Write-Host "commande : $Cli -> claude"
}
[Environment]::SetEnvironmentVariable('CLAUDE_CONFIG_DIR', $null, 'User'); Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue

# 2. Reglages : retirer uniquement ce que l'installation a ajoute
$S = "$CL\settings.json"
if (Test-Path $S) {
  $cfg = Get-Content $S -Raw -Encoding UTF8 | ConvertFrom-Json   # sans -Encoding, PowerShell 5.1 lit en ANSI
  if ($cfg.permissions.deny) { $cfg.permissions.deny = @($cfg.permissions.deny | Where-Object { $_ -notlike 'Agent(*' }) }
  if ($cfg.hooks) { foreach ($ev in @($cfg.hooks.PSObject.Properties.Name)) {
    $cfg.hooks.$ev = @($cfg.hooks.$ev | Where-Object { -not ($_.hooks[0].command -like '*guard-sensible*' -or $_.hooks[0].command -like '*memory-hook*') })
  } }
  [IO.File]::WriteAllText($S, ($cfg | ConvertTo-Json -Depth 20)); Write-Host "reglages nettoyes : $S"
}

# Modeles Ollama ranges dans ~/ai par ABC : remis dans ~/.ollama/models avant toute suppression de ~/ai
$OM = [Environment]::GetEnvironmentVariable('OLLAMA_MODELS', 'User')
if ($OM -and $OM.StartsWith($AI)) {
  New-Item -ItemType Directory -Force "$HOME\.ollama\models" | Out-Null
  Get-ChildItem $OM -Force -ErrorAction SilentlyContinue | ForEach-Object { Move-Item $_.FullName "$HOME\.ollama\models\" -ErrorAction SilentlyContinue }
  [Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $null, 'User'); Write-Host 'modeles Ollama remis dans ~/.ollama/models'
}

if (Confirm2 'DANGER : supprimer ~/ai efface DEFINITIVEMENT memoire, personas, skills, corbeille ET toutes les sauvegardes (backup-abc). Aucune recuperation possible.' 'Supprimer definitivement ~/ai ?' 'supprimer ai') { Remove-Item -Recurse -Force $AI; Write-Host '~/ai supprime' }
if (Confirm2 "DANGER : supprimer ~/project efface DEFINITIVEMENT tous vos projets, y compris leurs dossiers sensible/ et ce qui n'a jamais ete pousse sur GitHub." 'Supprimer definitivement ~/project ?' 'supprimer project') { Remove-Item -Recurse -Force (Join-Path $HOME 'project'); Write-Host '~/project supprime' }
Write-Host 'Desinstallation terminee. Claude Code lui-meme reste installe. Ouvrez un nouveau terminal.'
