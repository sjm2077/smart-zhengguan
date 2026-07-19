@echo off

title 教学管理系统启动中...

echo ==========================
echo 正在启动教学管理系统...
echo ==========================

cd /d %~dp0

cd frontend

echo.
echo 正在启动前端服务...
echo.

npm run dev

pause