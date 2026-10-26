# ==============================================================================
# Script tu dong khoi tao toan bo 6 CSDL Microservices tren SQL Server cuc bo
# ==============================================================================
param(
    [string]$Server = "localhost",
    [string]$Username = "",
    [string]$Password = ""
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$rootDir = $PSScriptRoot

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> KHOI TAO CO SO DU LIEU CHO TOAN BO MICROSERVICES" -ForegroundColor Green
Write-Host ">>> Server: $Server" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$sqlFiles = @(
    @{ Name = "Hotel Service";        File = "services\hotel-service\database_update.sql" },
    @{ Name = "User Service";         File = "services\user-service\database_init.sql" },
    @{ Name = "Room Service";         File = "services\room-service\database_init.sql" },
    @{ Name = "Booking Service";      File = "services\booking-service\database_init.sql" },
    @{ Name = "Payment Service";      File = "services\payment-service\database_init.sql" },
    @{ Name = "Notification Service"; File = "services\notification-service\database_init.sql" }
)

$step = 1
foreach ($item in $sqlFiles) {
    $filePath = Join-Path $rootDir $item.File
    if (!(Test-Path $filePath)) {
        Write-Host "[-] Khong tim thay file: $filePath" -ForegroundColor Red
        continue
    }

    Write-Host "[$step/$($sqlFiles.Count)] Dang khoi tao $($item.Name)..." -ForegroundColor Yellow
    
    if ($Username -and $Password) {
        $cmd = "sqlcmd -C -S `"$Server`" -U `"$Username`" -P `"$Password`" -i `"$filePath`" -b"
    } else {
        # Windows Authentication (Trusted Connection)
        $cmd = "sqlcmd -C -S `"$Server`" -E -i `"$filePath`" -b"
    }

    Invoke-Expression $cmd
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    [OK] Khoi tao thanh cong $($item.Name)!" -ForegroundColor Green
    } else {
        Write-Host "    [!] Co loi xay ra khi thuc thi $($item.Name) (ExitCode: $LASTEXITCODE)" -ForegroundColor Red
    }
    $step++
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> HOAN TAT QUA TRINH KHOI TAO CSDL!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
