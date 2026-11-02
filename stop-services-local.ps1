# ==============================================================================
# Script dung toan bo cac dich vu chay cuc bo (Local Environment)
# ==============================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ">>> DANG DUNG TOAN BO DICH VU LOCAL..." -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

$rootDir = $PSScriptRoot
$stoppedPids = @()

# Stop only exact processes started and recorded by start-services-local.ps1.
$pidFile = "$rootDir\.pids.json"
if (Test-Path $pidFile) {
    try {
        $savedPids = Get-Content $pidFile | ConvertFrom-Json
        foreach ($item in $savedPids) {
            $processId = [int]$item.ProcessId
            $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
            if (!$process) {
                Write-Host "  [SKIP] $($item.Service) PID $processId is no longer running." -ForegroundColor Gray
                continue
            }

            $expectedStart = [DateTime]::Parse(
                [string]$item.StartedAt,
                [Globalization.CultureInfo]::InvariantCulture,
                [Globalization.DateTimeStyles]::RoundtripKind
            )
            if ($process.StartTime.ToUniversalTime() -ne $expectedStart.ToUniversalTime()) {
                Write-Warning "Skipping PID $processId because it no longer matches the recorded process start time."
                continue
            }

            Write-Host "  [-] Stopping $($item.Service) (PID: $processId)..." -ForegroundColor DarkYellow
            Stop-Process -Id $processId -Force -ErrorAction Stop
            $stoppedPids += $processId
        }
    } catch {
        Write-Error "Could not safely process the recorded PID file: $($_.Exception.Message)"
        exit 1
    }
} else {
    Write-Host "No process list from start-services-local.ps1 was found; no processes were stopped." -ForegroundColor Gray
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ("Stopped recorded processes: {0}. Processes not in .pids.json were left untouched." -f $stoppedPids.Count) -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
