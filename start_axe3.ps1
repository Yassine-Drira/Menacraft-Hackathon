$ErrorActionPreference = "Stop"

Set-Location "C:\Users\yassi\Menacraft-Hackathon"

# Optional cleanup of previous servers on port 8002.
Get-NetTCPConnection -LocalPort 8002 -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique |
  ForEach-Object {
    try { Stop-Process -Id $_ -Force -ErrorAction Stop } catch {}
  }

Set-Location "C:\Users\yassi\Menacraft-Hackathon\axe3"
& "C:\Users\yassi\Menacraft-Hackathon\.venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8002
