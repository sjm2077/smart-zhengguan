@echo off
chcp 65001 >nul
setlocal

set "ROOT=%~dp0"
set "BACKEND=%ROOT%frontend\backend"
set "PYTHON=%BACKEND%\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [错误] 后端 B 的 Python 环境不存在。
    pause
    exit /b 1
)

if not exist "%BACKEND%\requirements.txt" (
    echo [错误] 后端 B 缺少 requirements.txt。
    pause
    exit /b 1
)

cd /d "%BACKEND%"
echo 正式后端：frontend\backend
echo 即将根据后端 B 的 requirements.txt 安装依赖。
"%PYTHON%" -m pip install -r requirements.txt

if errorlevel 1 (
    echo [错误] 依赖安装失败。
    pause
    exit /b 1
)

echo 依赖安装完成。
pause
