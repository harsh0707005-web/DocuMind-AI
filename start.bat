@echo off
echo ========================================================
echo               Starting DocuMind AI
echo ========================================================
echo.
echo [1/2] Launching Backend on http://localhost:8003...
start "DocuMind Backend" cmd /k "cd /d "%~dp0backend" && .\venv\Scripts\python.exe main.py"

echo [2/2] Launching Frontend on http://localhost:5173...
start "DocuMind Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both servers are starting in separate windows!
echo - Backend API:  http://localhost:8003 (Docs: http://localhost:8003/docs)
echo - Frontend UI:  http://localhost:5173
echo.
