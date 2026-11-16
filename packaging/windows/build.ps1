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
Write-Host "Done. Put opencode2.exe next to vicre.exe (or set VICRE_OPENCODE_BIN)."
