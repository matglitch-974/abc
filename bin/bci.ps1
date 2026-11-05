# bci : ancien nom de la commande bcai (obsolete), garde pour les anciens bci.cmd qui appellent ce fichier.
Write-Warning 'bci est obsolete : utilisez bcai'
& (Join-Path $PSScriptRoot 'bcai.ps1') @args
