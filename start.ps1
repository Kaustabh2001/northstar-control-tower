[CmdletBinding()]
param(
    [switch]$NoBuild,
    [switch]$Open
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$composeFile = Join-Path $projectRoot "infra\compose\docker-compose.yml"

function Invoke-NorthstarCompose {
    param([string[]]$Arguments)

    & docker compose -f $composeFile --profile tools @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose failed with exit code $LASTEXITCODE."
    }
}

function Wait-ForHttp {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSeconds = 120
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                Write-Host "[ready] $Name"
                return
            }
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }
    throw "$Name did not become ready within $TimeoutSeconds seconds."
}

if (-not (Test-Path -LiteralPath $composeFile)) {
    throw "Compose file not found: $composeFile"
}

& docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Desktop is not running. Start Docker Desktop and run this script again."
}

Push-Location $projectRoot
try {
    $upArguments = @("up", "-d")
    if (-not $NoBuild) {
        $upArguments += "--build"
    }

    try {
        Invoke-NorthstarCompose -Arguments $upArguments
    }
    catch {
        if ($NoBuild) {
            throw
        }
        Write-Warning "Image refresh failed. Retrying with locally cached Northstar images."
        Invoke-NorthstarCompose -Arguments @("up", "-d", "--no-build")
    }

    Wait-ForHttp -Name "Keycloak" -Url "http://localhost:8080/realms/northstar/.well-known/openid-configuration"
    Wait-ForHttp -Name "Control-plane API" -Url "http://localhost:8000/healthz"
    Wait-ForHttp -Name "Governance portal" -Url "http://localhost:5173/"

    Invoke-NorthstarCompose -Arguments @("ps")

    Write-Host ""
    Write-Host "Northstar is ready."
    Write-Host "Portal:   http://localhost:5173"
    Write-Host "API:      http://localhost:8000"
    Write-Host "Keycloak: http://localhost:8080"
    Write-Host ""
    Write-Host "Demo administrator: admin@northstar.local / northstar"

    if ($Open) {
        Start-Process "http://localhost:5173"
    }
}
finally {
    Pop-Location
}
