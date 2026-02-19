@echo off
setlocal

set "APP_NAME=SoftSafe Vextro"
set "ROOT=%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo Python nao encontrado. Instale o Python 3.10+ e tente novamente.
  exit /b 1
)

if not exist "%ROOT%ffmpeg.exe" (
  echo ffmpeg.exe nao encontrado em %ROOT%
  echo Copie o ffmpeg.exe para a pasta do projeto e execute novamente.
  exit /b 1
)

python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r "%ROOT%requirements.txt" >nul 2>&1
python -m pip install pyinstaller >nul 2>&1

python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "%APP_NAME%" ^
  --icon "%ROOT%ico.ico" ^
  --version-file "%ROOT%version_info.txt" ^
  --add-data "%ROOT%ico.png;." ^
  --add-data "%ROOT%exit.png;." ^
  --add-binary "%ROOT%ffmpeg.exe;." ^
  "%ROOT%main.py"

if errorlevel 1 (
  echo Falha no build.
  exit /b 1
)

echo Build concluido. Saida em: %ROOT%dist\%APP_NAME%.exe
endlocal
