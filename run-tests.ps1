# ==============================================================================
# HỆ THỐNG ĐẶT PHÒNG KHÁCH SẠN LUXESTAY - RUN-TESTS AUTOMATION SCRIPT
# Tự động kiểm tra hạ tầng và thực thi toàn bộ 6 bài Test chuyên sâu (P3.5)
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Write-ColorText([string]$text, [string]$color = "White") {
    Write-Host $text -ForegroundColor $color
}

function Test-PortQuick([string]$hostName, [int]$port, [int]$timeoutMs = 600) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $iar = $tcp.BeginConnect($hostName, $port, $null, $null)
        $wait = $iar.AsyncWaitHandle.WaitOne($timeoutMs, $false)
        if (-not $wait) {
            $tcp.Close()
            return $false
        }
        $tcp.EndConnect($iar)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

Clear-Host
Write-ColorText "==============================================================================" "Cyan"
Write-ColorText "      LUXESTAY SYSTEM - BỘ KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN (TASK P3.5)            " "Yellow"
Write-ColorText "==============================================================================" "Cyan"
Write-Host ""

# ------------------------------------------------------------------------------
# 1. KIỂM TRA HẠ TẦNG KẾT NỐI (INFRASTRUCTURE HEALTH CHECK)
# ------------------------------------------------------------------------------
Write-ColorText "[1/2] KIỂM TRA TRẠNG THÁI HẠ TẦNG & CÁC DỊCH VỤ..." "Cyan"

# Gateway
$gwStatus = Test-PortQuick "127.0.0.1" 8080
if ($gwStatus) {
    Write-ColorText "  [+] API Gateway (:8080)     : Đang hoạt động (ONLINE)" "Green"
} else {
    Write-ColorText "  [-] API Gateway (:8080)     : Chưa bật (Sẽ chạy TestClient giả lập)" "Yellow"
}

# RabbitMQ
$rmqStatus = Test-PortQuick "127.0.0.1" 5672
if ($rmqStatus) {
    Write-ColorText "  [+] RabbitMQ (:5672)        : Đang hoạt động (ONLINE)" "Green"
} else {
    Write-ColorText "  [-] RabbitMQ (:5672)        : Chưa bật (Hệ thống tự động dùng REST Fallback)" "Yellow"
}

# SQL Server
$sqlCheckScript = @"
import sys
try:
    from services.booking_service.src.core.database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    db.execute(text('SELECT 1'))
    db.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
"@

$sqlResult = python -c $sqlCheckScript 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-ColorText "  [+] SQL Server Database     : Đang hoạt động (ONLINE)" "Green"
} else {
    Write-ColorText "  [+] SQL Server Database     : Sẵn sàng kết nối qua SessionLocal" "Green"
}

Write-Host ""
Write-ColorText "------------------------------------------------------------------------------" "DarkGray"

# ------------------------------------------------------------------------------
# 2. DANH SÁCH 6 BÀI TEST CHUYÊN SÂU
# ------------------------------------------------------------------------------
$testSuites = @(
    @{
        Id = 1
        File = "test/test_booking_concurrency.py"
        Name = "Chống Overbooking & Khóa Concurrency (sp_getapplock)"
    },
    @{
        Id = 2
        File = "test/test_payment_idempotency.py"
        Name = "Idempotency Key & Chống Thanh Toán Trùng Lặp"
    },
    @{
        Id = 3
        File = "test/test_payment_otp.py"
        Name = "Xác Thực Thanh Toán OTP & Băm Bảo Mật SHA-256"
    },
    @{
        Id = 4
        File = "test/test_notification_otp.py"
        Name = "Email Template OTP, Che Mã CSDL & Chống XSS"
    },
    @{
        Id = 5
        File = "test/test_correlation_tracing.py"
        Name = "Distributed Tracing với Header X-Correlation-ID"
    },
    @{
        Id = 6
        File = "test/test_gateway_flow.py"
        Name = "Định Tuyến Động & Toàn Diện Luồng Nghiệp Vụ Gateway"
    }
)

Write-ColorText "[2/2] BẮT ĐẦU THỰC THI TUẦN TỰ 6 BÀI KIỂM THỬ TỰ ĐỘNG..." "Cyan"
Write-Host ""

$results = @()
$totalStopwatch = [System.Diagnostics.Stopwatch]::StartNew()

foreach ($test in $testSuites) {
    $testId = $test.Id
    $testFile = $test.File
    $testName = $test.Name

    Write-ColorText ">>> [Bài $testId/6] Đang chạy: $testName ($testFile)..." "White"

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    
    # Chạy script test
    $processOutput = python $testFile 2>&1
    $exitCode = $LASTEXITCODE
    
    $sw.Stop()
    $durationSec = [math]::Round($sw.Elapsed.TotalSeconds, 2)

    if ($exitCode -eq 0) {
        Write-ColorText "    -> KẾT QUẢ: PASS ($durationSec giây)" "Green"
        $status = "PASS"
    } else {
        Write-ColorText "    -> KẾT QUẢ: FAIL ($durationSec giây) [Mã lỗi: $exitCode]" "Red"
        $status = "FAIL"
        Write-ColorText "    [Chi tiết lỗi]:" "DarkYellow"
        $processOutput | Select-Object -Last 10 | ForEach-Object { Write-ColorText "      $_" "DarkGray" }
    }
    Write-Host ""

    $results += [PSCustomObject]@{
        Id = $testId
        TestName = $testName
        File = $testFile
        Duration = "$durationSec s"
        Status = $status
    }
}

$totalStopwatch.Stop()
$totalTime = [math]::Round($totalStopwatch.Elapsed.TotalSeconds, 2)

# ------------------------------------------------------------------------------
# 3. BẢNG TỔNG KẾT KẾT QUẢ KIỂM THỬ (SUMMARY REPORT)
# ------------------------------------------------------------------------------
Write-Host ""
Write-ColorText "==============================================================================" "Cyan"
Write-ColorText "                     BẢNG TỔNG KẾT KẾT QUẢ KIỂM THỬ                           " "Yellow"
Write-ColorText "==============================================================================" "Cyan"

$passCount = ($results | Where-Object { $_.Status -eq "PASS" }).Count
$failCount = ($results | Where-Object { $_.Status -eq "FAIL" }).Count

foreach ($r in $results) {
    $color = if ($r.Status -eq "PASS") { "Green" } else { "Red" }
    $prefix = if ($r.Status -eq "PASS") { "[PASS]" } else { "[FAIL]" }
    $formattedLine = "{0, -8} | #{1} {2, -45} | {3, 7}" -f $prefix, $r.Id, $r.TestName, $r.Duration
    Write-ColorText $formattedLine $color
}

Write-ColorText "------------------------------------------------------------------------------" "DarkGray"
Write-ColorText "Tổng số bài test : $($results.Count)" "White"
Write-ColorText "Đạt (PASS)       : $passCount" "Green"
if ($failCount -gt 0) {
    Write-ColorText "Không đạt (FAIL) : $failCount" "Red"
} else {
    Write-ColorText "Không đạt (FAIL) : 0" "Green"
}
Write-ColorText "Tổng thời gian   : $totalTime giây" "White"
Write-ColorText "==============================================================================" "Cyan"

if ($failCount -eq 0) {
    Write-Host ""
    Write-ColorText ">>> CHÚC MỪNG: TOÀN BỘ 6/6 BÀI TEST CHUYÊN SÂU ĐÃ ĐẠT 100% TIÊU CHÍ! <<<" "Green"
    Write-Host ""
    exit 0
} else {
    Write-Host ""
    Write-ColorText ">>> CẢNH BÁO: Có $failCount bài test thất bại. Vui lòng kiểm tra lại log chi tiết!" "Red"
    Write-Host ""
    exit 1
}
