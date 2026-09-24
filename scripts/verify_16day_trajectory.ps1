param (
    [Parameter(Position = 0)]
    [string]$Location = "Delhi",

    [Parameter(Position = 1)]
    [string]$Variable = "temperature_2m",

    [Parameter(Position = 2)]
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$scriptPath = Join-Path $PSScriptRoot "verify_16day_trajectory.py"
python $scriptPath $Location $Variable $BaseUrl
