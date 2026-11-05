# bcai — commande de BCAI (Windows). Appelée par bcai.cmd.
$Dest = Join-Path $HOME 'ai\2-tools\3-software\bcai'
$AI   = Join-Path $HOME 'ai'
$Py   = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1).Source
if (-not $Py) { $Py = (Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe", "$env:ProgramFiles\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object { [int]($_.Directory.Name -replace '\D','') } -Descending | Select-Object -First 1).FullName }
if (-not $Py -and (Get-Command uv -ErrorAction SilentlyContinue)) { $Py = uv python find 3.13 2>$null }
# install.ps1 et uninstall.ps1 restent sans BOM (un BOM casse leur première ligne sous irm | iex) :
# -File les lirait en ANSI sous PowerShell 5.1 ; on les lit donc en UTF-8 et on les exécute comme irm | iex.
function Run-Utf8($f) { "iex ([IO.File]::ReadAllText('$($f -replace "'","''")', [Text.Encoding]::UTF8))" }
$Cmd, $Rest = $args
switch ($Cmd) {
  { $_ -in 'install','update' } {
    if (Test-Path "$Dest\.git") { git -C $Dest pull -q --ff-only }
    & powershell -NoProfile -ExecutionPolicy Bypass -Command (Run-Utf8 "$Dest\install.ps1"); break }
  'uninstall' { & powershell -NoProfile -ExecutionPolicy Bypass -Command (Run-Utf8 "$Dest\uninstall.ps1"); break }
  'backup'    { if ($Rest -contains 'list') { & $Py "$Dest\hooks\bcai-backup.py" list } else { & $Py "$Dest\hooks\bcai-backup.py" quotidienne }; break }
  'search'    { & $Py "$AI\2-tools\1-skills\search\search.py" @Rest; break }
  'keys'      { & $Py "$Dest\hooks\bcai-keys.py" @Rest; break }
  'import'    { if (-not $Rest) { $Rest = @('all') }; & $Py "$Dest\hooks\bcai-import.py" @Rest; break }
  'version'   { $V = Get-Content "$Dest\VERSION" -ErrorAction SilentlyContinue; git -C $Dest log -1 --format="BCAI $V %h (%cs)"; break }
  'status'    {
    $V = Get-Content "$Dest\VERSION" -ErrorAction SilentlyContinue
    git -C $Dest log -1 --format="BCAI         $V %h (%cs)"
    Write-Host "Claude Code  $(claude --version 2>$null)"
    Write-Host "config       $env:CLAUDE_CONFIG_DIR"
    if (Test-Path "$HOME\.claude") { Write-Host 'ATTENTION    ~/.claude existe : cache laissé par une session hors BCAI, rangé dans 4-trash au prochain démarrage de claude' }
    Write-Host "recherche    $(& $Py "$AI\2-tools\1-skills\search\search.py" status)"
    Write-Host "sauvegardes  $((& $Py "$Dest\hooks\bcai-backup.py" list | Measure-Object).Count)"; break }
  default {
    @'
bcai install            installe ou met à jour BCAI (dernière version de GitHub) ; alias : bcai update
bcai uninstall          désinstalle, après deux confirmations (puis deux autres avant toute suppression)
bcai status             état : versions, configuration, recherche, sauvegardes
bcai backup [list]      sauvegarde immédiate, ou liste des sauvegardes
bcai search "requête"   recherche web (SearXNG local) ; options : bcai search -h
bcai keys open|close|status   coffre chiffré de 2-tools/4-keys-code (restic)
bcai import [skills|agents|secrets|llm]   réimporte l'existant (copies ; idempotent)
bcai version            version installée
'@ | Write-Host }
}
