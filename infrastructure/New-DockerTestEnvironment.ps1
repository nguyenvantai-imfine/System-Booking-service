param([string]$Destination = (Join-Path (Split-Path $PSScriptRoot -Parent) '.env.acceptance.local'))
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Destination) { throw 'Destination exists; refusing to overwrite secrets.' }
function New-RandomSecret {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return [Convert]::ToBase64String($bytes)
}
$values = @(
    ('SA_PASSWORD=Ls9!' + (New-RandomSecret)),
    ('JWT_SECRET_KEY=' + (New-RandomSecret)),
    ('INTERNAL_SERVICE_SECRET=' + (New-RandomSecret)),
    'RABBITMQ_USER=booking',
    ('RABBITMQ_PASSWORD=' + (New-RandomSecret)),
    'MSSQL_PORT=11433',
    'RABBITMQ_PORT=15673',
    'RABBITMQ_MANAGEMENT_PORT=15674',
    'HOTEL_SERVICE_PORT=18000',
    'USER_SERVICE_PORT=18001',
    'ROOM_SERVICE_PORT=18002',
    'BOOKING_SERVICE_PORT=18003',
    'PAYMENT_SERVICE_PORT=18004',
    'NOTIFICATION_SERVICE_PORT=18005',
    'GATEWAY_PORT=18080',
    'ADMIN_PORT=13000',
    'CUSTOMER_PORT=13001',
    'NEXT_PUBLIC_GATEWAY_URL=http://localhost:18080/api/v1',
    'CORS_ORIGINS=["http://localhost:13000","http://localhost:13001","http://127.0.0.1:13000","http://127.0.0.1:13001"]',
    'MOCK_EMAIL_SEND=True'
    'SEED_DEMO_DATA=1'
)
[System.IO.File]::WriteAllLines($Destination, $values, (New-Object System.Text.UTF8Encoding($false)))
Write-Output "Created isolated test configuration at $Destination (values hidden)."
