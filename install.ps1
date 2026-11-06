# ABC (Agents with a Better Context) - ancien point d'entree de l'installateur Windows (BCAI).
# Renvoi vers ABC-install-<version>.ps1, version lue dans VERSION. Garde en place : d'anciens liens le visent
# (lien court bc.ps1 deja publie, adresse .../bcai/main/install.ps1 redirigee par GitHub vers ce depot).
$AbcBranch = if ($env:ABC_BRANCH) { $env:ABC_BRANCH } elseif ($env:BCAI_BRANCH) { $env:BCAI_BRANCH } else { 'main' }
$AbcVersion = (Invoke-RestMethod "https://raw.githubusercontent.com/matglitch-974/abc/$AbcBranch/VERSION").Trim()
Invoke-RestMethod "https://raw.githubusercontent.com/matglitch-974/abc/$AbcBranch/ABC-install-$AbcVersion.ps1" | Invoke-Expression
