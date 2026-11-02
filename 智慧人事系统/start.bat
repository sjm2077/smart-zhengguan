@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════╗
echo ║   院长随手看 · 人事系统        ║
echo ╚══════════════════════════════════╝
echo.

:: 先释放可能占用的端口
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: 启动服务器
echo 🚀 正在启动服务器...
node server.js
pause