@echo off
title 智慧人事系统 - Django
echo ========================================
echo   院长随手看 · 人事系统 (Django)
echo ========================================
echo.

cd /d "%~dp0"

:: 检查 Python 是否可用
echo [1/3] 检查 Python ...
python --version >nul 2>&1
if errorlevel 1 (
    echo   [错误] 未找到 Python，请先安装 Python 3.8+
    echo   下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo   Python 就绪

:: 检查 Django 依赖
echo [2/3] 检查依赖 ...
pip show django >nul 2>&1
if errorlevel 1 (
    echo   正在安装 Django + openpyxl ...
    pip install django openpyxl -i https://pypi.tuna.tsinghua.edu.cn/simple
    if errorlevel 1 (
        echo   [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
)
echo   依赖就绪

:: 启动 Django
echo [3/3] 启动 Django 服务器 ...
echo.
echo   地址: http://localhost:8000
echo   按 Ctrl+C 停止服务器
echo ========================================
echo.
python manage.py runserver 0.0.0.0:8000
pause
