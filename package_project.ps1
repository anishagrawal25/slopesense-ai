$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$parent = Split-Path -Parent $projectRoot
$projectName = Split-Path -Leaf $projectRoot
$zipPath = Join-Path $parent "$projectName-developer-handoff.zip"
$stagingPath = Join-Path $env:TEMP "$projectName-developer-handoff"

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}
if (Test-Path $stagingPath) {
    Remove-Item $stagingPath -Recurse -Force
}

New-Item -ItemType Directory -Path $stagingPath | Out-Null

$items = Get-ChildItem $projectRoot -Force | Where-Object {
    $_.Name -notin @('__pycache__', '.venv', '.git')
}
$items | Copy-Item -Destination $stagingPath -Recurse -Force
$cacheDirectories = Get-ChildItem $stagingPath -Recurse -Directory -Force |
    Where-Object { $_.Name -eq '__pycache__' }
$cacheDirectories | Remove-Item -Recurse -Force
Get-ChildItem $stagingPath -Recurse -File -Force |
    Where-Object { $_.Extension -eq '.pyc' } |
    Remove-Item -Force

Compress-Archive -Path (Join-Path $stagingPath '*') -DestinationPath $zipPath -CompressionLevel Optimal
Remove-Item $stagingPath -Recurse -Force
Write-Output "Created $zipPath"
