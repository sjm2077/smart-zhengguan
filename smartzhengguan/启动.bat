@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo   Graduate Management - Starting...
echo ========================================
echo.

if not exist "node_modules\" (
    echo [ERROR] node_modules not found. Run npm install first.
    goto :fail
)

set "NPM_CMD="
if exist "%ProgramFiles%\nodejs\npm.cmd" set "NPM_CMD=%ProgramFiles%\nodejs\npm.cmd"
if not defined NPM_CMD (
    for /f "delims=" %%i in ('where npm.cmd 2^>nul') do set "NPM_CMD=%%i"
)
if not defined NPM_CMD (
    echo [ERROR] npm.cmd not found. Please install Node.js.
    goto :fail
)
echo [INFO] npm: %NPM_CMD%

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] backend virtual environment not found.
    echo [INFO] Creating virtual environment...
    cd backend
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd ..
)

if not exist "backend\db.sqlite3" (
    echo [WARN] backend\db.sqlite3 not found. Run migrations first.
)

call :kill_port 8000
call :kill_port 3000

echo [1/2] Starting Django backend on http://127.0.0.1:8000 ...
start "Graduate Backend" /d "%~dp0backend" "%~dp0backend\.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000

echo [INFO] Waiting for backend to initialize...
timeout /t 4 /nobreak >nul

echo [2/2] Starting Vite frontend on http://127.0.0.1:3000 ...
start "Graduate Frontend" /d "%~dp0" "%NPM_CMD%" run dev -- --host 127.0.0.1 --port 3000

echo.
echo ========================================
echo   [DONE] Both services started!
echo   Frontend : http://127.0.0.1:3000
echo   Backend  : http://127.0.0.1:8000/api/v1/
echo ========================================
echo.
endlocal
exit /b 0

:kill_port
powershell -NoProfile -Command "$p=(netstat -ano|sls ':%1 .*LISTENING'|%%{($_.Line -split'\s+')[-1]});if($p){Write-Host('[INFO] Port %1 in use, killing PID='+$p);Stop-Process -Id $p -Force}"
exit /b 0

:fail
echo.
echo [FAIL] Startup aborted. Please fix the issues above.
pause
endlocal
exit /b 1
