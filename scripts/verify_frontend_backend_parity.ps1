param (
    [Parameter(Position = 0)]
    [string]$Location = "Delhi",

    [Parameter(Position = 1)]
    [string]$Variable = "temperature_2m",

    [Parameter(Position = 2)]
    [string]$Mode = "full_16d",

    [Parameter(Position = 3)]
    [string]$ApiBaseUrl = "http://127.0.0.1:8000"
)

$scriptPath = Join-Path $PSScriptRoot "verify_frontend_backend_parity.py"
python $scriptPath $Location $Variable $Mode $ApiBaseUrl
