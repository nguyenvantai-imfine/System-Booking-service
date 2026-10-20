# ==============================================================================
# Script kiem tra trang thai cac dich vu chay cuc bo (Local Environment)
# ==============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> KIEM TRA TRANG THAI CAC DICH VU LOCAL" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan

$services = @(
    @{ Name = "Hotel Service";        Port = 8000; Url = "http://localhost:8000/docs" },
    @{ Name = "User Service";         Port = 8001; Url = "http://localhost:8001/docs" },
    @{ Name = "Room Service";         Port = 8002; Url = "http://localhost:8002/docs" },
    @{ Name = "Booking Service";      Port = 8003; Url = "http://localhost:8003/docs" },
    @{ Name = "Payment Service";      Port = 8004; Url = "http://localhost:8004/docs" },
    @{ Name = "Notification Service"; Port = 8005; Url = "http://localhost:8005/docs" },
    @{ Name = "API Gateway";          Port = 8080; Url = "http://localhost:8080" },
    @{ Name = "Admin Dashboard";      Port = 3000; Url = "http://localhost:3000" },
    @{ Name = "Customer Web App";     Port = 3001; Url = "http://localhost:3001" }
)

foreach ($svc in $services) {
    $conn = Get-NetTCPConnection -LocalPort $svc.Port -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $ownerId = $conn.OwningProcess
        Write-Host ("[RUNNING]  {0,-22} (Port {1,-4}, PID {2,-6}) -> {3}" -f $svc.Name, $svc.Port, $ownerId, $svc.Url) -ForegroundColor Green
    } else {
        Write-Host ("[STOPPED]  {0,-22} (Port {1,-4})            -> Not Listening" -f $svc.Name, $svc.Port) -ForegroundColor Red
    }
}
Write-Host "==========================================================" -ForegroundColor Cyan
