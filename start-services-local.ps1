# ==============================================================================
# Script khoi chay toan bo he thong chay ngam trong Antigravity (Khong popup cua so)
# ==============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$rootDir = $PSScriptRoot
$logDir = "$rootDir\logs"
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> KHOI CHAY HE THONG MICROSERVICES & FRONTEND (BACKGROUND)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Tu dong giai phong cac cong truoc khi khoi chay
$ports = @(8000, 8001, 8002, 8003, 8004, 8005, 8080, 3000, 3001)
foreach ($targetPort in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $targetPort -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $ownerId = $conn.OwningProcess
            if ($ownerId -and $ownerId -ne 0) {
                Stop-Process -Id $ownerId -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

$services = @(
    @{ Name = "Hotel Service";        Port = 8000; Dir = "services\hotel-service";        Type = "python"; Args = "-m uvicorn src.main:app --port 8000"; Log = "hotel-service" },
    @{ Name = "User Service";         Port = 8001; Dir = "services\user-service";         Type = "python"; Args = "-m uvicorn src.main:app --port 8001"; Log = "user-service" },
    @{ Name = "Room Service";         Port = 8002; Dir = "services\room-service";         Type = "python"; Args = "-m uvicorn src.main:app --port 8002"; Log = "room-service" },
    @{ Name = "Booking Service";      Port = 8003; Dir = "services\booking-service";      Type = "python"; Args = "-m uvicorn src.main:app --port 8003"; Log = "booking-service" },
    @{ Name = "Payment Service";      Port = 8004; Dir = "services\payment-service";      Type = "python"; Args = "-m uvicorn src.main:app --port 8004"; Log = "payment-service" },
    @{ Name = "Notification Service"; Port = 8005; Dir = "services\notification-service"; Type = "python"; Args = "-m uvicorn src.main:app --port 8005"; Log = "notification-service" },
    @{ Name = "API Gateway";          Port = 8080; Dir = "gateway";                      Type = "python"; Args = "-m uvicorn src.main:app --port 8080"; Log = "gateway" },
    @{ Name = "Admin Dashboard";      Port = 3000; Dir = "front-end\apps\admin-dashboard"; Type = "cmd";    Args = "/c npx next dev -p 3000";              Log = "admin-dashboard" },
    @{ Name = "Customer Web App";     Port = 3001; Dir = "front-end\apps\customer-web";    Type = "cmd";    Args = "/c npx next dev -p 3001";              Log = "customer-web" }
)

$startedList = @()
$step = 1

foreach ($svc in $services) {
    Write-Host "[$step/9] Dang khoi chay $($svc.Name) (Port $($svc.Port))..." -ForegroundColor Yellow
    $workDir = "$rootDir\$($svc.Dir)"
    $outLog = "$logDir\$($svc.Log).log"
    $errLog = "$logDir\$($svc.Log)-err.log"

    if ($svc.Type -eq "python") {
        $proc = Start-Process -FilePath "python" `
            -ArgumentList $svc.Args `
            -WorkingDirectory $workDir `
            -WindowStyle Hidden `
            -RedirectStandardOutput $outLog `
            -RedirectStandardError $errLog `
            -PassThru
    } else {
        $proc = Start-Process -FilePath "cmd.exe" `
            -ArgumentList $svc.Args `
            -WorkingDirectory $workDir `
            -WindowStyle Hidden `
            -PassThru
    }

    $startedList += @{
        Service = $svc.Name
        Port = $svc.Port
        ProcessId = $proc.Id
        Log = $outLog
    }
    $step++
}

# Luu danh sach PID vao .pids.json
$startedList | ConvertTo-Json | Set-Content "$rootDir\.pids.json" -Encoding UTF8

Write-Host ""
Write-Host "Dang cho cac dich vu khoi dong (4 giay)..." -ForegroundColor Cyan
Start-Sleep -Seconds 4

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> TRANG THAI HOAT DONG CAC DICH VU (LOCAL SERVICES):" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

foreach ($svc in $services) {
    $conn = Get-NetTCPConnection -LocalPort $svc.Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $status = "[RUNNING]"
        $color = "Green"
    } else {
        $status = "[STARTING]"
        $color = "Yellow"
    }
    $url = if ($svc.Port -eq 3000) { "http://localhost:3000" } elseif ($svc.Port -eq 3001) { "http://localhost:3001" } elseif ($svc.Port -eq 8080) { "http://localhost:8080" } else { "http://localhost:$($svc.Port)/docs" }
    Write-Host ("{0,-11} {1,-22} Port {2,-5} -> {3}" -f $status, $svc.Name, $svc.Port, $url) -ForegroundColor $color
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "LENH TIEN ICH (Chay truc tiep tren terminal Antigravity):" -ForegroundColor Yellow
Write-Host "- Xem log thoi gian thuc: Get-Content logs\gateway.log -Wait" -ForegroundColor Gray
Write-Host "- Kiem tra trang thai:    .\status-services-local.ps1" -ForegroundColor Gray
Write-Host "- Dung tat ca dich vu:    .\stop-services-local.ps1" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan
