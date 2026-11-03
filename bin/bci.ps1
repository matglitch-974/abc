# bci — commande de Better Claude Instance (Windows). Appelée par bci.cmd.
$Dest = Join-Path $HOME 'ai\2-tools\3-software\better-claude-instance'
$AI   = Join-Path $HOME 'ai'
$Py   = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1).Source
$Cmd, $Rest = $args
switch ($Cmd) {
  { $_ -in 'install','update' } {
    if (Test-Path "$Dest\.git") { git -C $Dest pull -q --ff-only }
    & powershell -NoProfile -ExecutionPolicy Bypass -File "$Dest\install.ps1"; break }
  'uninstall' { & powershell -NoProfile -ExecutionPolicy Bypass -File "$Dest\uninstall.ps1"; break }
  'backup'    { if ($Rest -contains 'list') { & $Py "$Dest\hooks\bci-backup.py" list } else { & $Py "$Dest\hooks\bci-backup.py" quotidienne }; break }
  'search'    { & $Py "$AI\2-tools\1-skills\search\search.py" @Rest; break }
  'version'   { git -C $Dest log -1 --format='BCI %h (%cs)'; break }
  'status'    {
    git -C $Dest log -1 --format='BCI          %h (%cs)'
    Write-Host "Claude Code  $(claude --version 2>$null)"
    Write-Host "config       $env:CLAUDE_CONFIG_DIR"
    if (Test-Path "$HOME\.claude") { Write-Host 'ATTENTION    ~/.claude existe : CLAUDE_CONFIG_DIR manquait au lancement de claude' }
    Write-Host "recherche    $(& $Py "$AI\2-tools\1-skills\search\search.py" status)"
    Write-Host "sauvegardes  $((& $Py "$Dest\hooks\bci-backup.py" list | Measure-Object).Count)"; break }
  default {
    @'
bci install            installe ou met à jour BCI (dernière version de GitHub) ; alias : bci update
bci uninstall          désinstalle, après deux confirmations (puis deux autres avant toute suppression)
bci status             état : versions, configuration, recherche, sauvegardes
bci backup [list]      sauvegarde immédiate, ou liste des sauvegardes
bci search "requête"   recherche web (SearXNG local) ; options : bci search -h
bci version            version installée
'@ | Write-Host }
}
