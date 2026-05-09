@echo off
echo ==================================================
echo         Smart Exam System - Build to EXE
echo ==================================================
echo.

echo [1/4] Building Vue frontend...
cd /d %~dp0frontend
call npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed!
    pause
    exit /b 1
)
echo [OK] Frontend build complete.
echo.

echo [2/4] Copying dist to backend...
xcopy /E /I /Y "%~dp0frontend\dist" "%~dp0dist"
echo [OK] Dist folder copied.
echo.

echo [3/4] Installing PyInstaller (if needed)...
pip install pyinstaller
echo [OK] PyInstaller ready.
echo.

echo [4/4] Packaging EXE with PyInstaller...
cd /d %~dp0
pyinstaller ^
    --name "SmartExamSystem" ^
    --onedir ^
    --add-data "dist;dist" ^
    --hidden-import uvicorn ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.loops ^
    --hidden-import uvicorn.loops.auto ^
    --hidden-import uvicorn.protocols ^
    --hidden-import uvicorn.protocols.http ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.protocols.websockets ^
    --hidden-import uvicorn.protocols.websockets.auto ^
    --hidden-import uvicorn.lifespan ^
    --hidden-import uvicorn.lifespan.on ^
    --hidden-import uvicorn.lifespan.off ^
    --hidden-import docx ^
    --hidden-import pdfplumber ^
    --hidden-import openai ^
    --hidden-import httptools ^
    --hidden-import dotenv ^
    --hidden-import email_validator ^
    --noconfirm ^
    --clean ^
    main.py

if errorlevel 1 (
    echo [ERROR] PyInstaller packaging failed!
    pause
    exit /b 1
)

echo.
echo ==================================================
echo   BUILD SUCCESS!
echo.
echo   Output folder: %~dp0dist\SmartExamSystem\
echo   Run: dist\SmartExamSystem\SmartExamSystem.exe
echo ==================================================
pause
