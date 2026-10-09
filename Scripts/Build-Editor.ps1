param([string]$EngineRoot = 'C:\Program Files\Epic Games\UE_5.8')
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$ProjectFile = Join-Path $ProjectRoot 'src\HollowPines.uproject'
$LogPath = Join-Path $ProjectRoot 'Artifacts\editor-build.log'
New-Item -ItemType Directory -Force (Split-Path $LogPath) | Out-Null
& (Join-Path $EngineRoot 'Engine\Build\BatchFiles\Build.bat') HollowPinesEditor Win64 Development "-Project=$ProjectFile" -WaitMutex -NoHotReloadFromIDE "-log=$LogPath"
exit $LASTEXITCODE
