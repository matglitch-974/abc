# Better Claude Instance — désinstallation Windows (PowerShell).
#   irm https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/uninstall.ps1 | iex
# Remet la configuration de Claude Code dans ~/.claude, retire les liens et réglages ajoutés,
# puis demande avant de toucher à ~/ai et ~/project. Claude Code reste installé.
$ErrorActionPreference = 'Stop'
function Confirm2($Warning, $Question, $Word) {   # deux confirmations : [o/N], puis le mot tapé en entier
  Write-Host $Warning -ForegroundColor Red
  if ((Read-Host "$Question [o/N]") -notin 'o','O') { return $false }
  if ((Read-Host "Seconde confirmation : tapez « $Word »") -ne $Word) { Write-Host 'Annulé.'; return $false }
  return $true
}
if (-not (Confirm2 'ATTENTION : la désinstallation retire Better Claude Instance de Claude Code (réglages, hooks, liens, variable CLAUDE_CONFIG_DIR) et remet la configuration dans ~/.claude. Vos dossiers ~/ai et ~/project restent en place, sauf si vous demandez ensuite leur suppression.' 'Désinstaller Better Claude Instance ?' 'desinstaller')) { Write-Host "Rien n'a été modifié."; exit 0 }
$AI = Join-Path $HOME 'ai'
$CC = Join-Path $AI '2-tools\3-software\claude-code'
$CL = Join-Path $HOME '.claude'

# 1. Configuration : ~/ai/2-tools/3-software/claude-code -> ~/.claude (jonctions remplacées par des copies)
if ((Test-Path $CC) -and -not (Test-Path $CL)) {
  foreach ($j in "$CC\skills", "$CC\agents\system-agents", "$CC\plugins") {
    if ((Test-Path $j) -and (Get-Item $j -Force).LinkType) {
      $target = (Get-Item $j -Force).Target; (Get-Item $j -Force).Delete()
      if ($j -like '*\plugins' -and $target -and (Test-Path $target)) { Copy-Item $target $j -Recurse; Write-Host "copié : $j" }
    }
  }
  $ClaudeMd = "$CC\CLAUDE.md"
  if ((Test-Path $ClaudeMd) -and ((Get-Content $ClaudeMd -Raw) -match '@~/ai/AGENTS.md')) { Remove-Item $ClaudeMd }
  Move-Item $CC $CL; Write-Host "configuration remise : $CL"
  if ((Test-Path "$CL\.claude.json") -and -not (Test-Path "$HOME\.claude.json")) { Move-Item "$CL\.claude.json" "$HOME\.claude.json" }
  Get-ChildItem $CL -Filter '*.bak-bci' -Force | ForEach-Object {
    $orig = $_.FullName -replace '\.bak-bci$',''
    if (-not (Test-Path $orig)) { Move-Item $_.FullName $orig; Write-Host "restauré : $orig" }
  }
}
Remove-Item "$HOME\.local\bin\bci.cmd" -ErrorAction SilentlyContinue
[Environment]::SetEnvironmentVariable('CLAUDE_CONFIG_DIR', $null, 'User'); Remove-Item Env:CLAUDE_CONFIG_DIR -ErrorAction SilentlyContinue

# 2. Réglages : retirer uniquement ce que l'installation a ajouté
$S = "$CL\settings.json"
if (Test-Path $S) {
  $cfg = Get-Content $S -Raw | ConvertFrom-Json
  if ($cfg.permissions.deny) { $cfg.permissions.deny = @($cfg.permissions.deny | Where-Object { $_ -notlike 'Agent(*' }) }
  if ($cfg.hooks) { foreach ($ev in @($cfg.hooks.PSObject.Properties.Name)) {
    $cfg.hooks.$ev = @($cfg.hooks.$ev | Where-Object { -not ($_.hooks[0].command -like '*guard-sensible*' -or $_.hooks[0].command -like '*memory-hook*') })
  } }
  [IO.File]::WriteAllText($S, ($cfg | ConvertTo-Json -Depth 20)); Write-Host "réglages nettoyés : $S"
}

# Modèles Ollama rangés dans ~/ai par BCI : remis dans ~/.ollama/models avant toute suppression de ~/ai
$OM = [Environment]::GetEnvironmentVariable('OLLAMA_MODELS', 'User')
if ($OM -and $OM.StartsWith($AI)) {
  New-Item -ItemType Directory -Force "$HOME\.ollama\models" | Out-Null
  Get-ChildItem $OM -Force -ErrorAction SilentlyContinue | ForEach-Object { Move-Item $_.FullName "$HOME\.ollama\models\" -ErrorAction SilentlyContinue }
  [Environment]::SetEnvironmentVariable('OLLAMA_MODELS', $null, 'User'); Write-Host 'modèles Ollama remis dans ~/.ollama/models'
}

if (Confirm2 'DANGER : supprimer ~/ai efface DÉFINITIVEMENT mémoire, personas, skills, corbeille ET toutes les sauvegardes (backup-bci). Aucune récupération possible.' 'Supprimer définitivement ~/ai ?' 'supprimer ai') { Remove-Item -Recurse -Force $AI; Write-Host '~/ai supprimé' }
if (Confirm2 "DANGER : supprimer ~/project efface DÉFINITIVEMENT tous vos projets, y compris leurs dossiers sensible/ et ce qui n'a jamais été poussé sur GitHub." 'Supprimer définitivement ~/project ?' 'supprimer project') { Remove-Item -Recurse -Force (Join-Path $HOME 'project'); Write-Host '~/project supprimé' }
Write-Host 'Désinstallation terminée. Claude Code lui-même reste installé. Ouvrez un nouveau terminal.'
