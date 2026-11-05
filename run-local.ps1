$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiDir = Join-Path $root "api"
$webDir = Join-Path $root "web"

Write-Host "Setting up the local Spotify Stats stack..."

if (Get-Command fnm -ErrorAction SilentlyContinue) {
    Write-Host "Activating the fnm-managed Node toolchain..."
    fnm env --use-on-cd --shell powershell | Out-String | Invoke-Expression
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found in PATH. Install Node.js or use fnm first, then rerun this script."
}

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher (py) was not found in PATH. Install Python 3.11 and rerun this script."
}

if (-not (Test-Path (Join-Path $apiDir ".venv"))) {
    Write-Host "Creating Python virtual environment for the API..."
    & py -3.11 -m venv (Join-Path $apiDir ".venv")
}

$venvActivate = Join-Path $apiDir ".venv\Scripts\Activate.ps1"
& $venvActivate
python -m pip install --upgrade pip
pip install -r (Join-Path $apiDir "requirements-dev.txt")

if (-not (Test-Path (Join-Path $apiDir "dev_server.py"))) {
    @'
from flask import Flask, request
from spotify_stats.service import build_stats_result

app = Flask(__name__)


@app.post("/api/stats")
def stats():
    result = build_stats_result(request.data)
    return result.body, result.status


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7071, debug=True)
'@ | Set-Content -Path (Join-Path $apiDir "dev_server.py")
}

if (-not (Test-Path (Join-Path $webDir "node_modules"))) {
    Write-Host "Installing web dependencies..."
    Push-Location $webDir
    npm install
    Pop-Location
}

Write-Host "Starting the local API dev server on http://localhost:7071"
$apiProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$apiDir'; & '$venvActivate'; python dev_server.py" -WorkingDirectory $apiDir -PassThru

Write-Host "Starting the web app on http://localhost:5173"
$webProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "if (Get-Command fnm -ErrorAction SilentlyContinue) { fnm env --use-on-cd --shell powershell | Out-String | Invoke-Expression }; cd '$webDir'; npm run dev -- --host 0.0.0.0" -WorkingDirectory $root -PassThru

Write-Host ""
Write-Host "Both services were launched in separate PowerShell windows."
Write-Host "API:     http://localhost:7071/api/stats"
Write-Host "Web:     http://localhost:5173"
Write-Host ""
Write-Host "Use Ctrl+C inside either server window to stop it."
Write-Host "The API is running with a local Flask dev server, not Azure Functions."
