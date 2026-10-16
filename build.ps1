param(
    [Parameter(Mandatory=$true)][string]$OpenSCAD,
    [Parameter(Mandatory=$true)][string]$Python,
    [string]$Part = 'assembly',
    [string]$Output = 'exports/assembly.stl',
    [hashtable]$Parameters = @{}
)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskOutput = if ([IO.Path]::IsPathRooted($Output)) { $Output } else { Join-Path $taskRoot $Output }
New-Item -ItemType Directory -Path (Split-Path -Parent $taskOutput) -Force | Out-Null
$taskParameterFile = Join-Path $taskRoot ('work/build-parameters-' + [guid]::NewGuid().ToString('N') + '.json')
New-Item -ItemType Directory -Path (Split-Path -Parent $taskParameterFile) -Force | Out-Null
foreach ($taskKey in $Parameters.Keys) {
    if ($taskKey -notmatch '^[a-z_]+$' -or $Parameters[$taskKey] -isnot [ValueType]) {
        throw 'Parameters must contain named numeric/bool values only.'
    }
}
try {
    $Parameters | ConvertTo-Json | Set-Content -LiteralPath $taskParameterFile -Encoding UTF8
    & $Python (Join-Path $taskRoot 'exporter.py') --openscad $OpenSCAD --part $Part --output $taskOutput --parameters $taskParameterFile
    if ($LASTEXITCODE -ne 0) { throw "Mesh build failed with exit $LASTEXITCODE" }
} finally {
    Remove-Item -LiteralPath $taskParameterFile -ErrorAction SilentlyContinue
}
if (-not (Test-Path -LiteralPath $taskOutput)) { throw 'No output mesh was created.' }
Get-FileHash -LiteralPath $taskOutput -Algorithm SHA256
