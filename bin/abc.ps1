# abc - commande d'ABC (Windows). Appelee par abc.cmd.
$Dest = Join-Path $HOME 'ai\2-tools\3-software\abc'
$AI   = Join-Path $HOME 'ai'
$Py   = (Get-Command python -ErrorAction SilentlyContinue | Where-Object { $_.Source -notlike '*WindowsApps*' } | Select-Object -First 1).Source
if (-not $Py) { $Py = (Get-ChildItem "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe", "$env:ProgramFiles\Python3*\python.exe" -ErrorAction SilentlyContinue | Sort-Object { [int]($_.Directory.Name -replace '\D','') } -Descending | Select-Object -First 1).FullName }
if (-not $Py -and (Get-Command uv -ErrorAction SilentlyContinue)) { $Py = uv python find 3.13 2>$null }
$Cli  = if ($env:ABC_CLI) { $env:ABC_CLI } else { 'agent' }   # commande de Claude Code
if (-not (Get-Command $Cli -CommandType Application -ErrorAction SilentlyContinue)) { $Cli = 'claude' }
$Installer = "$Dest\ABC-install-$((Get-Content "$Dest\VERSION" -ErrorAction SilentlyContinue | Select-Object -First 1)).ps1"
# Les .ps1 du depot sont en ASCII pur, sans BOM (un BOM casse la premiere ligne sous irm | iex) ;
# on lit quand meme les installateurs en UTF-8 et on les execute comme irm | iex.
function Run-Utf8($f) { "iex ([IO.File]::ReadAllText('$($f -replace "'","''")', [Text.Encoding]::UTF8))" }
$Cmd, $Rest = $args
switch ($Cmd) {
  { $_ -in 'install','update' } {
    if (Test-Path "$Dest\.git") { git -C $Dest pull -q --ff-only }
    & powershell -NoProfile -ExecutionPolicy Bypass -Command (Run-Utf8 $Installer); break }
  'uninstall' { & powershell -NoProfile -ExecutionPolicy Bypass -Command (Run-Utf8 "$Dest\uninstall.ps1"); break }
  'backup'    { if ($Rest -contains 'list') { & $Py "$Dest\hooks\abc-backup.py" list } else { & $Py "$Dest\hooks\abc-backup.py" quotidienne }; break }
  'search'    { & $Py "$AI\2-tools\1-skills\search\search.py" @Rest; break }
  'keys'      { & $Py "$Dest\hooks\abc-keys.py" @Rest; break }
  'import'    { if (-not $Rest) { $Rest = @('all') }; & $Py "$Dest\hooks\abc-import.py" @Rest; break }
  'version'   { $V = Get-Content "$Dest\VERSION" -ErrorAction SilentlyContinue; git -C $Dest log -1 --format="ABC $V %h (%cs)"; break }
  'status'    {
    $V = Get-Content "$Dest\VERSION" -ErrorAction SilentlyContinue
    git -C $Dest log -1 --format="ABC          $V %h (%cs)"
    Write-Host "Claude Code  $(& $Cli --version 2>$null) (commande $Cli)"
    Write-Host "config       $env:CLAUDE_CONFIG_DIR"
    if (Test-Path "$HOME\.claude") { Write-Host 'ATTENTION    ~/.claude existe : cache laisse par une session hors ABC, range dans 4-trash au prochain demarrage de Claude Code' }
    Write-Host "recherche    $(& $Py "$AI\2-tools\1-skills\search\search.py" status)"
    Write-Host "sauvegardes  $((& $Py "$Dest\hooks\abc-backup.py" list | Measure-Object).Count)"; break }
  default {
    @'
abc install            installe ou met a jour ABC (derniere version de GitHub) ; alias : abc update
abc uninstall          desinstalle, apres deux confirmations (puis deux autres avant toute suppression)
abc status             etat : versions, configuration, recherche, sauvegardes
abc backup [list]      sauvegarde immediate, ou liste des sauvegardes
abc search "requete"   recherche web (SearXNG local) ; options : abc search -h
abc keys open|close|status   coffre chiffre de 2-tools/4-keys-code (restic)
abc import [skills|agents|secrets|llm]   reimporte l'existant (copies ; idempotent)
abc version            version installee
'@ | Write-Host }
}
