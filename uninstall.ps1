# Better Claude Instance — désinstallation Windows (PowerShell).
#   irm https://raw.githubusercontent.com/matglitch-974/better-claude-instance/main/uninstall.ps1 | iex
# Retire les liens et réglages ; demande avant de toucher à ~/ai et ~/project. Claude Code reste installé.
$ErrorActionPreference = 'Stop'
$CL = Join-Path $HOME '.claude'

$ClaudeMd = "$CL\CLAUDE.md"
if ((Test-Path $ClaudeMd) -and ((Get-Content $ClaudeMd -Raw) -match '@~/ai/AGENTS.md')) { Remove-Item $ClaudeMd; Write-Host "retiré : $ClaudeMd" }
foreach ($l in "$CL\skills", "$CL\agents\system-agents") {
  if ((Test-Path $l) -and (Get-Item $l -Force).LinkType) { (Get-Item $l -Force).Delete(); Write-Host "lien retiré : $l" }
}
$S = "$CL\settings.json"
if ((Test-Path $S) -and -not (Test-Path "$S.bak-bci")) {
  # Réglages créés par l'installation : retirer uniquement ce qu'elle a ajouté.
  $cfg = Get-Content $S -Raw | ConvertFrom-Json
  if ($cfg.permissions.deny) { $cfg.permissions.deny = @($cfg.permissions.deny | Where-Object { $_ -notlike 'Agent(*' }) }
  if ($cfg.hooks) { foreach ($ev in @($cfg.hooks.PSObject.Properties.Name)) {
    $cfg.hooks.$ev = @($cfg.hooks.$ev | Where-Object { -not ($_.hooks[0].command -like '*guard-sensible*' -or $_.hooks[0].command -like '*memory-hook*') })
  } }
  [IO.File]::WriteAllText($S, ($cfg | ConvertTo-Json -Depth 20)); Write-Host "réglages nettoyés : $S"
}
foreach ($p in $ClaudeMd, "$CL\skills", $S) {
  if (Test-Path "$p.bak-bci") { Move-Item "$p.bak-bci" $p -Force; Write-Host "restauré : $p" }
}

if ((Read-Host 'Supprimer définitivement ~/ai (personas, skills, corbeille compris) ? [o/N]') -eq 'o') { Remove-Item -Recurse -Force (Join-Path $HOME 'ai'); Write-Host '~/ai supprimé' }
if ((Read-Host 'Supprimer définitivement ~/project (tous vos projets) ? [o/N]') -eq 'o') { Remove-Item -Recurse -Force (Join-Path $HOME 'project'); Write-Host '~/project supprimé' }
Write-Host 'Désinstallation terminée. Claude Code lui-même reste installé.'
