$ErrorActionPreference = 'Stop'
$trackerSource = Join-Path $PSScriptRoot 'src'
python -m PyInstaller --noconfirm --onefile --windowed --exclude-module numpy --icon "$trackerSource\emblems\app_icon.ico" --name FoundryTracker_Armeria --add-data "$trackerSource\catalog.json;." --add-data "$trackerSource\emblems;emblems" --add-data "$trackerSource\weapons;weapons" --add-data "$trackerSource\lang;lang" --add-binary "$trackerSource\adb\adb.exe;adb" --add-binary "$trackerSource\adb\AdbWinApi.dll;adb" --add-binary "$trackerSource\adb\AdbWinUsbApi.dll;adb" --distpath "$PSScriptRoot\dist" --workpath "$PSScriptRoot\build" --specpath "$PSScriptRoot" "$trackerSource\app.py"
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller no pudo generar el ejecutable.' }
