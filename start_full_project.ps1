$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  throw "Python venv not found at $venvPython"
}

function Start-Window {
  param(
    [string]$Title,
    [string]$WorkDir,
    [string]$Command
  )

  $fullCmd = "$host.UI.RawUI.WindowTitle = '$Title'; Set-Location '$WorkDir'; $Command"
  Start-Process powershell -ArgumentList "-NoExit", "-Command", $fullCmd | Out-Null
}

$axe1Back = Join-Path $root "axe1\challenge1\back"
$axe1Front = Join-Path $root "axe1\challenge1\front"
$axe2Back = Join-Path $root "axe2\backend"
$axe2Front = Join-Path $root "axe2\frontend"
$axe3Root = Join-Path $root "axe3"

$required = @($axe1Back, $axe1Front, $axe2Back, $axe2Front, $axe3Root)
foreach ($path in $required) {
  if (-not (Test-Path $path)) {
    throw "Missing required path: $path"
  }
}

Write-Host "Launching Menacraft full stack..." -ForegroundColor Cyan
Write-Host "Axe 1 backend:  http://127.0.0.1:8001" -ForegroundColor Gray
Write-Host "Axe 2 backend:  http://127.0.0.1:8000" -ForegroundColor Gray
Write-Host "Axe 3 backend:  http://127.0.0.1:8002" -ForegroundColor Gray
Write-Host "Axe 1 frontend: http://127.0.0.1:3000" -ForegroundColor Gray
Write-Host "Axe 2 frontend: http://127.0.0.1:5173" -ForegroundColor Gray

# Axe 1 backend on 8001 to avoid collision with Axe 2 backend.
Start-Window -Title "Axe1 Backend" -WorkDir $axe1Back -Command "& '$venvPython' -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload"

# Axe 2 backend on 8000 (used by its frontend code).
Start-Window -Title "Axe2 Backend" -WorkDir $axe2Back -Command "& '$venvPython' run.py"

# Axe 3 backend on 8002.
Start-Window -Title "Axe3 Backend" -WorkDir $axe3Root -Command "& '$venvPython' run_server.py"

# Axe 1 frontend points to Axe 1 backend via env var.
Start-Window -Title "Axe1 Frontend" -WorkDir $axe1Front -Command "if (!(Test-Path 'node_modules')) { npm install }; `$env:REACT_APP_API_URL='http://127.0.0.1:8001'; npm start"

# Axe 2 frontend points to 8000 in code; run Vite on 5173.
Start-Window -Title "Axe2 Frontend" -WorkDir $axe2Front -Command "if (!(Test-Path 'node_modules')) { npm install }; npm run dev -- --host 127.0.0.1 --port 5173"

Start-Sleep -Seconds 3

$homePage = Join-Path $root "index.html"
if (Test-Path $homePage) {
  Start-Process $homePage | Out-Null
}

Write-Host "All services started in separate terminals." -ForegroundColor Green
Write-Host "Use the opened homepage to navigate across axes." -ForegroundColor Green
