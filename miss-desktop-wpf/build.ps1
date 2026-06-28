<#
  MISS Desktop WPF 打包脚本 — pythonnet 内嵌 Python 版
  输出: publish\MISS\ 目录，解压即用（零依赖：无需安装 Python / .NET）
#>

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== MISS Desktop Build (pythonnet) ===" -ForegroundColor Cyan

# 1. Download & extract Python 3.12 embed
$PythonDir = "$Root\publish\python"
$PythonZip = "$Root\build\python-3.12.8-embed-amd64.zip"
$PythonUrl = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"

if (-not (Test-Path $PythonDir)) {
    Write-Host "[1/4] Downloading Python 3.12 embed..." -ForegroundColor Yellow
    if (-not (Test-Path $PythonZip)) {
        Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonZip
    }
    Expand-Archive -Path $PythonZip -DestinationPath $PythonDir -Force

    # Enable site-packages (uncomment import site in python312._pth)
    $PthFile = "$PythonDir\python312._pth"
    (Get-Content $PthFile) -replace "^#import site", "import site" | Set-Content $PthFile
    # Add Lib\site-packages path
    Add-Content $PthFile "Lib\site-packages"
}

# 2. Install pip dependencies
Write-Host "[2/4] Installing pip dependencies..." -ForegroundColor Yellow
$PipTarget = "$PythonDir\Lib\site-packages"
pip install -r "$Root\..\miss-backend\requirements.txt" -t $PipTarget --platform win_amd64 --python-version 3.12 --only-binary=:all: 2>&1
pip install pysqlite3-binary -t $PipTarget --platform win_amd64 --python-version 3.12 --only-binary=:all: 2>&1

# 3. Dotnet publish (self-contained, embeds .NET runtime)
Write-Host "[3/4] Building WPF app..." -ForegroundColor Yellow
$env:Path = "C:\Program Files\dotnet;" + $env:Path
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=false -o "$Root\publish\MISS" 2>&1
if ($LASTEXITCODE -ne 0) { throw "dotnet publish failed" }

# 4. Copy embedded Python + miss-backend + Python.Runtime.dll
Write-Host "[4/4] Copying runtime..." -ForegroundColor Yellow
Copy-Item -Recurse -Force $PythonDir "$Root\publish\MISS\python"
Copy-Item -Recurse -Force "$Root\..\miss-backend" "$Root\publish\MISS\miss-backend"

# Copy Python.Runtime.dll (pythonnet) — dotnet publish doesn't include netstandard2.0 assemblies
$PythonRuntime = "$env:USERPROFILE\.nuget\packages\pythonnet\3.1.0\lib\netstandard2.0\Python.Runtime.dll"
if (Test-Path $PythonRuntime) {
    Copy-Item $PythonRuntime "$Root\publish\MISS\" -Force
    Write-Host "  Python.Runtime.dll copied" -ForegroundColor DarkGray
} else {
    Write-Host "  WARNING: Python.Runtime.dll not found at $PythonRuntime" -ForegroundColor Yellow
}

# Clean unnecessary files
$RemoveDirs = @("__pycache__", ".pytest_cache", "tests", "docs", "build", "dist", "frontend", "frontend-desktop", ".env", ".env.example")
foreach ($d in $RemoveDirs) {
    $p = Join-Path "$Root\publish\MISS\miss-backend" $d
    if (Test-Path $p) { Remove-Item -Recurse -Force $p }
}
Get-ChildItem "$Root\publish\MISS\miss-backend" -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Remove-Item "$Root\publish\MISS\miss-backend\requirements.txt" -Force -ErrorAction SilentlyContinue

$Size = (Get-ChildItem "$Root\publish\MISS" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host ""
Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Output: $Root\publish\MISS\" -ForegroundColor White
Write-Host "Size: $([math]::Round($Size, 1)) MB" -ForegroundColor White
Write-Host "Run: .\publish\MISS\MISS.exe" -ForegroundColor White
