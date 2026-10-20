# ==============================================================================
# Script thiet lap moi truong phat trien (Setup Environment) cho may moi
# Chay: .\setup-environment.ps1
# ==============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$rootDir = $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> THIET LAP MOI TRUONG PHAT TRIEN CHO HE THONG (SETUP)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Kiem tra Python
Write-Host "[1/5] Kiem tra Python..." -ForegroundColor Yellow
$pythonVer = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Chua cai dat Python! Vui long cai dat Python 3.10+ tai https://www.python.org/" -ForegroundColor Red
    exit 1
} else {
    Write-Host "    [OK] $pythonVer" -ForegroundColor Green
}

# 2. Kiem tra Node.js
Write-Host "[2/5] Kiem tra Node.js..." -ForegroundColor Yellow
$nodeVer = node --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Chua cai dat Node.js! Vui long cai dat Node.js 18+ tai https://nodejs.org/" -ForegroundColor Red
    exit 1
} else {
    Write-Host "    [OK] Node.js $nodeVer" -ForegroundColor Green
}

# 3. Kiem tra & cai dat pnpm neu chua co
Write-Host "[3/5] Kiem tra pnpm..." -ForegroundColor Yellow
$pnpmVer = pnpm --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "    [!] Chua co pnpm, dang tu dong cai dat qua npm..." -ForegroundColor Cyan
    npm install -g pnpm
} else {
    Write-Host "    [OK] pnpm $pnpmVer" -ForegroundColor Green
}

# 4. Cai dat toan bo Python dependencies
Write-Host "[4/5] Cai dat Python dependencies tu requirements.txt..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r "$rootDir\requirements.txt"
if ($LASTEXITCODE -eq 0) {
    Write-Host "    [OK] Cai dat thanh cong cac thu vien Python!" -ForegroundColor Green
} else {
    Write-Host "    [!] Co loi xay ra khi pip install." -ForegroundColor Red
}

# 5. Cai dat Front-end Monorepo dependencies
Write-Host "[5/5] Cai dat Front-end Monorepo dependencies (pnpm install)..." -ForegroundColor Yellow
Set-Location "$rootDir\front-end"
pnpm install
Set-Location $rootDir

# Tao file .env neu chua co
if (!(Test-Path "$rootDir\.env") -and (Test-Path "$rootDir\.env.example")) {
    Copy-Item "$rootDir\.env.example" "$rootDir\.env"
    Write-Host "    [OK] Da tu dong tao file .env tu .env.example!" -ForegroundColor Green
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> MOI TRUONG DA DUOC THIET LAP SAN SANG!" -ForegroundColor Green
Write-Host "Buoc tiep theo:" -ForegroundColor Yellow
Write-Host "1. Khoi tao CSDL:  .\init-databases-local.ps1" -ForegroundColor White
Write-Host "2. Khoi chay he thong: .\start-services-local.ps1" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
