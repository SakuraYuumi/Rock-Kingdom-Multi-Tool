param(
    [string]$Version = "v1.0.0",
    [switch]$SkipSelfTest
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$ReleaseDir = Join-Path $Root "release"
$BuildDir = Join-Path $ReleaseDir "pyinstaller_build"
$DistDir = Join-Path $ReleaseDir "pyinstaller_dist"
$SpecDir = Join-Path $ReleaseDir "pyinstaller_spec"
$PortableRoot = Join-Path $ReleaseDir "windows_portable"
$PortableDir = Join-Path $PortableRoot "Roco-Kingdom-Multi-Tool"
$PackageData = Join-Path $ReleaseDir "package_data"
$Entry = (Get-ChildItem -LiteralPath $Root -Filter "*.pyw" | Select-Object -First 1).FullName
$AppName = [System.IO.Path]::GetFileNameWithoutExtension($Entry)
$ZipPath = Join-Path $ReleaseDir "Roco-Kingdom-Multi-Tool-Windows-Portable-$Version.zip"

Write-Host "Building $Version from $Root"

Remove-Item -LiteralPath $BuildDir, $DistDir, $PortableRoot, $PackageData -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
New-Item -ItemType Directory -Force -Path $PackageData | Out-Null
New-Item -ItemType Directory -Force -Path $SpecDir | Out-Null

$DataSource = (Resolve-Path (Join-Path $Root "data")).Path
$ExcludedDataFiles = @(
    "pvp_team_presets.json",
    "pvp_team_slots.json",
    "user_accounts.json",
    "user_dimmed_markers.json",
    "user_marker_audit_submissions.json",
    "user_marker_notes.json",
    "user_route_cache.json",
    "user_route_progress.json"
)

Get-ChildItem -LiteralPath $DataSource -Recurse -File | ForEach-Object {
    $Relative = $_.FullName.Substring($DataSource.Length).TrimStart("\")
    $Excluded = (
        $Relative -like "accounts\*" -or
        $Relative -like "user_marker_submission_uploads\*" -or
        $ExcludedDataFiles -contains $_.Name -or
        $_.Name -like "*_summary.json" -or
        $_.Name -like "*.tmp"
    )
    if (-not $Excluded) {
        $Destination = Join-Path $PackageData $Relative
        New-Item -ItemType Directory -Force -Path (Split-Path $Destination -Parent) | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $Destination -Force
    }
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name $AppName `
    --distpath $DistDir `
    --workpath $BuildDir `
    --specpath $SpecDir `
    --add-data "$Root\assets;assets" `
    --add-data "$PackageData;data" `
    --exclude-module PyQt5.QtDBus `
    --exclude-module PyQt5.QtDesigner `
    --exclude-module PyQt5.QtHelp `
    --exclude-module PyQt5.QtNetwork `
    --exclude-module PyQt5.QtQml `
    --exclude-module PyQt5.QtQuick `
    --exclude-module PyQt5.QtSql `
    --exclude-module PyQt5.QtTest `
    --exclude-module PyQt5.QtWebSockets `
    --exclude-module tkinter `
    --exclude-module pytest `
    $Entry

New-Item -ItemType Directory -Force -Path $PortableRoot | Out-Null
Move-Item -LiteralPath (Join-Path $DistDir $AppName) -Destination $PortableDir

$Translations = Join-Path $PortableDir "_internal\PyQt5\Qt5\translations"
if (Test-Path $Translations) {
    Get-ChildItem -LiteralPath $Translations -File |
        Where-Object { $_.Name -notin @("qt_zh_CN.qm", "qtbase_zh_CN.qm") } |
        Remove-Item -Force
}

$UnusedQtPluginDirs = @(
    "_internal\PyQt5\Qt5\plugins\generic",
    "_internal\PyQt5\Qt5\plugins\iconengines",
    "_internal\PyQt5\Qt5\plugins\platformthemes",
    "_internal\PyQt5\Qt5\plugins\styles"
)
foreach ($Relative in $UnusedQtPluginDirs) {
    $Path = Join-Path $PortableDir $Relative
    if (Test-Path $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
}

Copy-Item -LiteralPath (Join-Path $Root "README.md") -Destination (Join-Path $PortableDir "README.md") -Force
New-Item -ItemType Directory -Force -Path (Join-Path $PortableDir "user_data") | Out-Null

if (-not $SkipSelfTest) {
    python -m py_compile `
        $Entry `
        (Join-Path $Root "app\app_paths.py") `
        (Join-Path $Root "app\pvp_damage.py") `
        (Join-Path $Root "app\roco_resource_map_qt.py") `
        (Join-Path $Root "app\sift_tracker_v2.py")

    python $Entry --check
    python $Entry --selftest
}

Remove-Item -LiteralPath $ZipPath -Force -ErrorAction SilentlyContinue
Compress-Archive -Path (Join-Path $PortableRoot "*") -DestinationPath $ZipPath -CompressionLevel Optimal
Remove-Item -LiteralPath $PackageData -Recurse -Force -ErrorAction SilentlyContinue

$Hash = Get-FileHash -Algorithm SHA256 -LiteralPath $ZipPath
Write-Host "Portable package: $ZipPath"
Write-Host "SHA256: $($Hash.Hash)"
