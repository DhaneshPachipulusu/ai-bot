# start.ps1 - Run both backend and frontend simultaneously

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AI Interview Bot - Starting All...   " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Backend (FastAPI with uvicorn)
Write-Host "[1/2] Starting Backend (FastAPI)..." -ForegroundColor Yellow
$backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -PassThru

Start-Sleep -Seconds 2

# Start Frontend (Next.js)
Write-Host "[2/2] Starting Frontend (Next.js)..." -ForegroundColor Yellow
$frontend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\ai-frontend'; npm run dev" -PassThru

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Both servers are starting!           " -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000      " -ForegroundColor Green
Write-Host "   Frontend: http://localhost:3000      " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Enter to stop both servers..." -ForegroundColor Red
Read-Host

# Kill both processes
Write-Host "Stopping servers..." -ForegroundColor Yellow
Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue

# Also kill any orphaned processes on the ports
Get-Process -Name "node" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Host "All servers stopped." -ForegroundColor Green
