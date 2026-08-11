@echo off
echo ==========================================
echo   Travel Agent Application Launcher
echo ==========================================
echo.

echo [1/2] Starting Backend Server...
start "Travel Agent Backend" cmd /k "cd backend && venv\Scripts\activate ; uvicorn app.main:app --reload --port 8000"

echo [2/2] Starting Frontend Server...
start "Travel Agent Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo   Application Started!
echo ==========================================
echo.
echo Backend URL:  http://localhost:8000
echo Frontend URL: http://localhost:5173
echo.
echo Keep this window open or close it, the servers are running in separate windows.
echo.
pause
