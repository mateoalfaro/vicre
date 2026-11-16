# Builds dist\vicre\vicre.exe: a portable folder to copy to a USB drive.
# Use -OneFile for a single exe (slower start: it unpacks to %TEMP% each run).
# Run from the repository root on Windows with Python 3.11+.
param([switch]$OneFile)
$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip pyinstaller pillow pystray pypdf
python tools\extract_fuentes.py fuentes\Ejercicios_y_Respuestas.pdf build\fuentes
$mode = if ($OneFile) { "--onefile" } else { "--onedir" }
pyinstaller $mode --noconsole --name vicre `
  --paths . `
  --add-data "build\fuentes;fuentes" `
  --hidden-import vicre.winshot --hidden-import vicre.wintype --hidden-import vicre.winapp `
  packaging\windows\vicre_win.py
Write-Host "Done. Copy dist\vicre to the USB drive; put agy.exe in that folder (or set VICRE_AGY_BIN). Data lives in vicre-data\ beside vicre.exe."
