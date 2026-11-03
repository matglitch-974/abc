# Better Claude Instance — désinstallation Windows (PowerShell).
#   irm https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/uninstall.ps1 | iex
# Remet la configuration de Claude Code dans ~/.claude, retire les liens et réglages ajoutés,
# puis demande avant de toucher à ~/ai et ~/project. Claude Code reste installé.
$ErrorActionPreference = 'Stop'
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

if ((Read-Host 'Supprimer définitivement ~/ai (personas, skills, sauvegardes, corbeille compris) ? [o/N]') -eq 'o') { Remove-Item -Recurse -Force $AI; Write-Host '~/ai supprimé' }
if ((Read-Host 'Supprimer définitivement ~/project (tous vos projets) ? [o/N]') -eq 'o') { Remove-Item -Recurse -Force (Join-Path $HOME 'project'); Write-Host '~/project supprimé' }
Write-Host 'Désinstallation terminée. Claude Code lui-même reste installé. Ouvrez un nouveau terminal.'
