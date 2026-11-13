Write-Host "Starting Parrot Cards PyJHora Astro Engine (FastAPI) on port 8000..." -ForegroundColor Cyan
Set-Location -Path $PSScriptRoot
py -3.11 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

