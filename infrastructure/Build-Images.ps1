param(
    [string]$EnvFile = '.env.acceptance.local',
    [string]$ProjectName = 'luxestay-acceptance',
    [switch]$LegacyBuilder
)
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path $PSScriptRoot -Parent
Push-Location $repositoryRoot
$previousBuilder = $env:DOCKER_BUILDKIT
try {
    & docker compose --env-file $EnvFile -p $ProjectName config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Invalid Compose configuration.' }
    # Keep resolved secrets in memory; only public frontend build arguments are passed on.
    $resolved = (& docker compose --env-file $EnvFile -p $ProjectName config --format json | Out-String) | ConvertFrom-Json
    if ($LegacyBuilder) { $env:DOCKER_BUILDKIT = '0' }
    foreach ($service in $resolved.services.PSObject.Properties) {
        if (-not $service.Value.build) { continue }
        $build = $service.Value.build
        $arguments = @('build', '-t', ($ProjectName + '-' + $service.Name), '-f', (Join-Path $build.context $build.dockerfile))
        if ($build.args) {
            foreach ($argument in $build.args.PSObject.Properties) {
                $arguments += @('--build-arg', ($argument.Name + '=' + $argument.Value))
            }
        }
        $arguments += $build.context
        & docker @arguments
        if ($LASTEXITCODE -ne 0) { throw ('Build failed: ' + $service.Name) }
    }
} finally {
    $env:DOCKER_BUILDKIT = $previousBuilder
    Pop-Location
}
