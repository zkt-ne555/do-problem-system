@echo off
echo =========================================
echo       Starting Intelligent System
echo =========================================
echo.

echo [1/2] Starting Backend (FastAPI)...
start "Backend_FastAPI" cmd /k "cd /d %~dp0 && uvicorn main:app --reload"

echo [2/2] Starting Frontend (Vue3)...
start "Frontend_Vue3" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo =========================================
echo Commands sent! 
echo Two new terminal windows should open. 
echo Please keep them running in the background.
echo.
echo [TIP]
echo Access the frontend at: http://localhost:5173
echo =========================================
pause
