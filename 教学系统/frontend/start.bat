@echo off
setlocal EnableExtensions
chcp 65001 >nul
title 智慧教学平台启动器

rem ============================================================
rem 便携式启动脚本：可放在 frontend 目录，也可放在其上一级目录。
rem 前端：Vue / Vite，默认端口 5173
rem 后端：Django，默认端口 8000
rem ============================================================

set "SCRIPT_DIR=%~dp0"
if exist "%SCRIPT_DIR%package.json" (
    set "FRONTEND_DIR=%SCRIPT_DIR%"
) else if exist "%SCRIPT_DIR%frontend\package.json" (
    set "FRONTEND_DIR=%SCRIPT_DIR%frontend"
) else (
    echo [错误] 找不到前端 package.json。
    echo 请将 start.bat 放在 frontend 文件夹内，或放在包含 frontend 文件夹的项目根目录。
    goto :failed
)

for %%I in ("%FRONTEND_DIR%") do set "FRONTEND_DIR=%%~fI"
set "BACKEND_DIR=%FRONTEND_DIR%\backend"
set "PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe"

if not exist "%BACKEND_DIR%\manage.py" (
    echo [错误] 找不到 Django 后端："%BACKEND_DIR%\manage.py"
    echo 请确认已完整复制 frontend 文件夹及其 backend 子文件夹。
    goto :failed
)

if not exist "%BACKEND_DIR%\requirements.txt" (
    echo [错误] 找不到后端依赖文件 backend\requirements.txt。
    goto :failed
)

if not exist "%BACKEND_DIR%\.env" (
    echo [错误] 找不到 backend\.env 配置文件。
    echo 请先将 backend\.env.example 复制为 backend\.env，
    echo 再根据本机 MySQL 配置填写数据库名、用户名和密码。
    goto :failed
)

where npm >nul 2>nul
if errorlevel 1 (
    echo [错误] 未检测到 npm。请先安装 Node.js LTS，并确保 npm 已加入 PATH。
    goto :failed
)

rem 不自动结束任何已有进程，避免误关其他程序。
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if not errorlevel 1 (
    echo [错误] 端口 8000 已被占用。请先确认是否已有 Django 服务运行，再重新启动。
    goto :failed
)
netstat -ano | findstr /R /C:":5173 .*LISTENING" >nul
if not errorlevel 1 (
    echo [错误] 端口 5173 已被占用。请先关闭已有 Vite 前端窗口，再重新启动。
    goto :failed
)

echo.
echo ============================================================
echo             智慧教学平台 - 一键启动
echo ============================================================
echo 前端目录：%FRONTEND_DIR%
echo 后端目录：%BACKEND_DIR%
echo.

rem 第一次运行时创建 Python 虚拟环境；不会依赖原电脑的绝对路径。
if not exist "%PYTHON_EXE%" (
    echo [1/5] 正在创建 Python 虚拟环境...
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv "%BACKEND_DIR%\.venv"
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo [错误] 未检测到 Python。请安装 Python 3.12 或更高版本并加入 PATH。
            goto :failed
        )
        python -m venv "%BACKEND_DIR%\.venv"
    )
    if errorlevel 1 (
        echo [错误] 创建 Python 虚拟环境失败。
        goto :failed
    )
) else (
    echo [1/5] 检测到 Python 虚拟环境。
)

rem 当前后端依赖要求 Python 3.12 或更高版本。
"%PYTHON_EXE%" -c "import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 1)" >nul 2>nul
if errorlevel 1 (
    echo [错误] 当前 Python 版本低于 3.12 或虚拟环境不可用。请安装 Python 3.12+ 后重试。
    goto :failed
)

rem 若虚拟环境中缺少关键依赖，则自动安装 requirements.txt。
"%PYTHON_EXE%" -c "import django, rest_framework, corsheaders, rest_framework_simplejwt, MySQLdb, dotenv" >nul 2>nul
if errorlevel 1 (
    echo [2/5] 正在安装后端 Python 依赖，首次运行可能需要几分钟...
    "%PYTHON_EXE%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
    if errorlevel 1 (
        echo [错误] Python 依赖安装失败。请检查网络及 Python 环境。
        goto :failed
    )
) else (
    echo [2/5] 后端 Python 依赖已就绪。
)

rem 首次运行或未携带 node_modules 时，自动安装前端依赖。
if not exist "%FRONTEND_DIR%\node_modules\vite" (
    echo [3/5] 正在安装前端 npm 依赖，首次运行可能需要几分钟...
    pushd "%FRONTEND_DIR%"
    call npm install
    if errorlevel 1 (
        popd
        echo [错误] 前端依赖安装失败。请检查网络及 Node.js/npm 环境。
        goto :failed
    )
    popd
) else (
    echo [3/5] 前端 npm 依赖已就绪。
)

rem 检查数据库连接并应用待执行迁移；不会自动导入演示或历史业务数据。
echo [4/5] 正在检查数据库并同步数据表结构...
pushd "%BACKEND_DIR%"
"%PYTHON_EXE%" manage.py migrate --noinput
set "MIGRATE_RESULT=%ERRORLEVEL%"
popd
if not "%MIGRATE_RESULT%"=="0" goto :database_failed

echo [5/5] 正在启动前后端服务...
start "智慧教学平台 - Django 后端" /D "%BACKEND_DIR%" cmd /k ""%PYTHON_EXE%" manage.py runserver 127.0.0.1:8000"
timeout /t 2 /nobreak >nul
start "智慧教学平台 - Vue 前端" /D "%FRONTEND_DIR%" cmd /k "npm run dev -- --host 127.0.0.1 --strictPort"
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:5173"
echo.
echo 启动命令已执行。
echo 系统地址：http://127.0.0.1:5173
echo 后端接口：http://127.0.0.1:8000/api/
echo 请保持新打开的后端和前端命令窗口运行，不要关闭。
echo.
exit /b 0

:database_failed
echo.
echo [数据库连接或迁移失败]
echo 请确认：
echo   1. 本机 MySQL 服务已启动；
echo   2. MySQL 中已创建 college_teaching 数据库；
echo   3. backend\.env 中的数据库名、用户名、密码和端口正确；
echo   4. 当前数据库用户有连接数据库及执行迁移的权限。
echo 注意：启动脚本不会自动创建 MySQL 数据库，也不会自动导入业务数据。
goto :failed

:failed
echo.
echo 启动未完成。请按上面的提示处理后重新双击 start.bat。
echo.
pause
exit /b 1
