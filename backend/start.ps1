# PowerShell script to start the backend server
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting Intelligent Travel Agent Backend" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "✓ Activating virtual environment..." -ForegroundColor Green
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "✗ Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "✓ Environment configuration found" -ForegroundColor Green
} else {
    Write-Host "✗ .env file not found!" -ForegroundColor Red
    Write-Host "Please create .env file with your API keys" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "🚀 Starting server..." -ForegroundColor Green
Write-Host ""

# Start the server
python start_server.py









