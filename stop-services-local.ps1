# ==============================================================================
# Script dung toan bo cac dich vu chay cuc bo (Local Environment)
# ==============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> DANG DUNG TOAN BO DICH VU LOCAL..." -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$rootDir = $PSScriptRoot
$ports = @(8000, 8001, 8002, 8003, 8004, 8005, 8080, 3000, 3001)
$stoppedPids = @()

# 1. Dung theo PID luu trong .pids.json neu co
$pidFile = "$rootDir\.pids.json"
if (Test-Path $pidFile) {
    try {
        $savedPids = Get-Content $pidFile | ConvertFrom-Json
        foreach ($item in $savedPids) {
            $p = Get-Process -Id $item.PID -ErrorAction SilentlyContinue
            if ($p) {
                Write-Host "  [-] Dung $($item.Service) (PID: $($item.PID))..." -ForegroundColor DarkYellow
                Stop-Process -Id $item.PID -Force -ErrorAction SilentlyContinue
                $stoppedPids += $item.PID
            }
        }
    } catch {
        # ignore parse errors
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

# 2. Quet va giai phong cac Port 8000 - 8005, 8080, 3000
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $procId = $conn.OwningProcess
            if ($procId -and $procId -ne 0 -and ($stoppedPids -notcontains $procId)) {
                $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
                $procName = if ($proc) { $proc.ProcessName } else { "Unknown" }
                Write-Host "  [-] Giai phong Port $port (PID: $procId - $procName)..." -ForegroundColor DarkYellow
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                $stoppedPids += $procId
            }
        }
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[OK] TAT CA CAC DICH VU DA DUOC DUNG VA GIAI PHONG PORT!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
