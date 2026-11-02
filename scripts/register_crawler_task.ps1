# 注册 Windows 计划任务：每 6 小时运行一次官网爬虫
# 用法（PowerShell，普通权限即可，创建的是"当前用户"级任务）：
#   powershell -ExecutionPolicy Bypass -File scripts\register_crawler_task.ps1
# 卸载：
#   schtasks /Delete /TN "ZhengGuan-PSPA-Crawler" /F

$ErrorActionPreference = 'Stop'

$TaskName = 'ZhengGuan-PSPA-Crawler'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python   = Join-Path $RepoRoot 'research_system\venv\Scripts\python.exe'
$Crawler  = Join-Path $RepoRoot 'scripts\crawler_pspa.py'
$LogDir   = Join-Path $RepoRoot 'logs'

if (-not (Test-Path $Python))  { throw "未找到虚拟环境 Python：$Python" }
if (-not (Test-Path $Crawler)) { throw "未找到爬虫脚本：$Crawler" }
if (-not (Test-Path $LogDir))  { New-Item -ItemType Directory -Path $LogDir | Out-Null }

$LogFile = Join-Path $LogDir 'crawler_pspa.log'

# cmd 包装：带时间戳追加日志，避免计划任务窗口一闪而过看不到错误
$Inner = "chcp 65001>nul & echo [%date% %time%] start>>""$LogFile"" & ""$Python"" ""$Crawler"" --once --pages 5 >>""$LogFile"" 2>&1 & echo [%date% %time%] end>>""$LogFile"""
$Action = "cmd.exe /c $Inner"

Write-Host "任务名 : $TaskName"
Write-Host "解释器 : $Python"
Write-Host "脚本   : $Crawler"
Write-Host "日志   : $LogFile"
Write-Host "频率   : 每 6 小时"

schtasks /Create /TN $TaskName /TR $Action /SC HOURLY /MO 6 /F | Out-Host

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n注册成功。查看：schtasks /Query /TN $TaskName /V /FO LIST" -ForegroundColor Green
    Write-Host "立即跑一次：schtasks /Run /TN $TaskName" -ForegroundColor Green
} else {
    Write-Host "`n注册失败，退出码 $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
