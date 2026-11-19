# Builds dist\vicre\vicre.exe (portable folder) or dist\vicre.exe with -OneFile.
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
$out = if ($OneFile) { "dist" } else { "dist\vicre" }
Copy-Item packaging\windows\vicre.env "$out\vicre.env" -Force
Write-Host "Done. Copy dist\vicre to the USB drive and put opencode2.exe in it. Edit vicre.env to change model/variant. Data and login live in vicre-data\ beside vicre.exe."
