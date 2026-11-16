# Builds dist\FoundryTracker_Armeria_V<version>.exe, dist\SHA256_V<version>.txt and the release zip.
# The version comes from src\resources.py. -Python picks the interpreter for .venv-build (Python 3.12 with Tk).
# -Out puts dist\ and build\ in another folder (for example F:\Compilaciones\FoundryTracker); by default, next to this script.
param([string]$Python = 'python', [string]$Out = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$trackerSource = Join-Path $PSScriptRoot 'src'
$dist = Join-Path $Out 'dist'
$work = Join-Path $Out 'build'
$venv = Join-Path $PSScriptRoot '.venv-build'
$py = Join-Path $venv 'Scripts\python.exe'

if (-not (Test-Path $py)) {
    & $Python -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear .venv-build con $Python." }
}
& $py -m pip install --disable-pip-version-check --quiet -r (Join-Path $PSScriptRoot 'requirements-build.txt')
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las herramientas de requirements-build.txt.' }

& $py (Join-Path $PSScriptRoot 'test_tracker.py')
if ($LASTEXITCODE -ne 0) { throw 'Los tests fallaron; no se compila.' }

& $py (Join-Path $PSScriptRoot 'test_security.py')
if ($LASTEXITCODE -ne 0) { throw 'Security tests failed; build stopped.' }

$version = (Select-String -Path "$trackerSource\resources.py" -Pattern "^VERSION='([^']+)'").Matches[0].Groups[1].Value
if ($version -notmatch '^\d+\.\d+\.\d+$') { throw 'Invalid release version.' }
$tag = $version.Replace('.', '')
$name = "FoundryTracker_Armeria_V$tag"

# --noupx: a UPX-packed onefile build is what antivirus tools flag most often.
& $py -m PyInstaller --noconfirm --onefile --windowed --noupx --exclude-module numpy --icon "$trackerSource\emblems\app_icon.ico" --name $name --add-data "$trackerSource\catalog.json;." --add-data "$trackerSource\emblems;emblems" --add-data "$trackerSource\weapons;weapons" --add-data "$trackerSource\lang;lang" --add-binary "$trackerSource\adb\adb.exe;adb" --add-binary "$trackerSource\adb\AdbWinApi.dll;adb" --add-binary "$trackerSource\adb\AdbWinUsbApi.dll;adb" --distpath $dist --workpath $work --specpath $work "$trackerSource\app.py"
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller no pudo generar el ejecutable.' }

$exe = Join-Path $dist "$name.exe"
$sha = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLower()
[IO.File]::WriteAllText((Join-Path $dist "SHA256_V$tag.txt"), "$sha *dist/$name.exe`n")

$stage = Join-Path $work "release_V$tag"
$resolvedStage = [IO.Path]::GetFullPath($stage)
$buildRoot = [IO.Path]::GetFullPath($work) + [IO.Path]::DirectorySeparatorChar
if (-not $resolvedStage.StartsWith($buildRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Release path escapes build folder.' }
Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $stage | Out-Null
Copy-Item -LiteralPath $exe, (Join-Path $PSScriptRoot 'LEEME.md'), (Join-Path $PSScriptRoot 'README.md') -Destination $stage
[IO.File]::WriteAllText((Join-Path $stage 'SHA256.txt'), "$sha  $name.exe`n")
$zip = Join-Path $dist "$name.zip"
Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip
Write-Host "$name.exe  sha256 $sha"
Write-Host "Zip: $zip"
