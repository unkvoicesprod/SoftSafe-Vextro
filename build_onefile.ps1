$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$appName = 'SoftSafe Vextro'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error 'Python nao encontrado. Instale o Python 3.10+ e tente novamente.'
}

$ffmpeg = Join-Path $root 'ffmpeg.exe'
if (-not (Test-Path $ffmpeg)) {
  Write-Error "ffmpeg.exe nao encontrado em $root. Copie o ffmpeg.exe para a pasta do projeto e execute novamente."
}

python -m pip install --upgrade pip | Out-Null
python -m pip install -r (Join-Path $root 'requirements.txt') | Out-Null
python -m pip install pyinstaller | Out-Null

$icon = Join-Path $root 'ico.ico'
$ver = Join-Path $root 'version_info.txt'
$icoPng = Join-Path $root 'ico.png'
$exitPng = Join-Path $root 'exit.png'
$mainPy = Join-Path $root 'main.py'

python -m PyInstaller --noconfirm --clean --onefile --windowed `
  --name "$appName" `
  --icon "$icon" `
  --version-file "$ver" `
  --add-data "$icoPng;." `
  --add-data "$exitPng;." `
  --add-binary "$ffmpeg;." `
  "$mainPy"

$exe = Join-Path $root "dist\$appName.exe"
if (-not (Test-Path $exe)) {
  Write-Error 'Falha no build.'
}

Write-Host "Build concluido. Saida em: $exe"
