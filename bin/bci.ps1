# bci — commande de Better Claude Instance (Windows). Appelée par bci.cmd.
$Dest = Join-Path $HOME 'ai\2-tools\3-software\better-claude-instance'
$AI   = Join-Path $HOME 'ai'
$Py   = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1).Source
if (-not $Py) { $Py = (Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe", "$env:ProgramFiles\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object { [int]($_.Directory.Name -replace '\D','') } -Descending | Select-Object -First 1).FullName }
if (-not $Py -and (Get-Command uv -ErrorAction SilentlyContinue)) { $Py = uv python find 3.13 2>$null }
$Cmd, $Rest = $args
switch ($Cmd) {
  { $_ -in 'install','update' } {
    if (Test-Path "$Dest\.git") { git -C $Dest pull -q --ff-only }
    & powershell -NoProfile -ExecutionPolicy Bypass -File "$Dest\install.ps1"; break }
  'uninstall' { & powershell -NoProfile -ExecutionPolicy Bypass -File "$Dest\uninstall.ps1"; break }
  'backup'    { if ($Rest -contains 'list') { & $Py "$Dest\hooks\bci-backup.py" list } else { & $Py "$Dest\hooks\bci-backup.py" quotidienne }; break }
  'search'    { & $Py "$AI\2-tools\1-skills\search\search.py" @Rest; break }
  'keys'      { & $Py "$Dest\hooks\bci-keys.py" @Rest; break }
  'import'    { if (-not $Rest) { $Rest = @('all') }; & $Py "$Dest\hooks\bci-import.py" @Rest; break }
  'version'   { $V = Get-Content "$Dest\VERSION" -ErrorAction SilentlyContinue; git -C $Dest log -1 --format="BCI $V %h (%cs)"; break }
  'status'    {
    $V = Get-Content "$Dest\VERSION" -ErrorAction SilentlyContinue
    git -C $Dest log -1 --format="BCI          $V %h (%cs)"
    Write-Host "Claude Code  $(claude --version 2>$null)"
    Write-Host "config       $env:CLAUDE_CONFIG_DIR"
    if (Test-Path "$HOME\.claude") { Write-Host 'ATTENTION    ~/.claude existe : cache laissé par une session hors BCI, rangé dans 4-trash au prochain démarrage de claude' }
    Write-Host "recherche    $(& $Py "$AI\2-tools\1-skills\search\search.py" status)"
    Write-Host "sauvegardes  $((& $Py "$Dest\hooks\bci-backup.py" list | Measure-Object).Count)"; break }
  default {
    @'
bci install            installe ou met à jour BCI (dernière version de GitHub) ; alias : bci update
bci uninstall          désinstalle, après deux confirmations (puis deux autres avant toute suppression)
bci status             état : versions, configuration, recherche, sauvegardes
bci backup [list]      sauvegarde immédiate, ou liste des sauvegardes
bci search "requête"   recherche web (SearXNG local) ; options : bci search -h
bci keys open|close|status   coffre chiffré de 2-tools/4-keys-code (restic)
bci import [skills|agents|secrets|llm]   réimporte l'existant (copies ; idempotent)
bci version            version installée
'@ | Write-Host }
}
