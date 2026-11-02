# 启动知识库 + 智能体服务（127.0.0.1:8900）
# 用法： powershell -ExecutionPolicy Bypass -File scripts\start_kb.ps1
#        powershell -ExecutionPolicy Bypass -File scripts\start_kb.ps1 -Rebuild   # 先重建索引

param(
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'
$Root   = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root 'research_system\venv\Scripts\python.exe'
$KbDir  = Join-Path $Root 'kb_service'

if (-not (Test-Path $Python)) { throw "未找到虚拟环境 Python：$Python" }

$env:PYTHONIOENCODING = 'utf-8'

if ($Rebuild -or -not (Test-Path (Join-Path $KbDir 'data\kb.pkl'))) {
    Write-Host '[1/2] 重建知识库索引…'
    & $Python (Join-Path $KbDir 'ingest.py')
}

Write-Host '[2/2] 启动知识库服务 http://127.0.0.1:8900'
Write-Host '      前端访问路径：http://localhost:3000/knowledge'
& $Python (Join-Path $KbDir 'server.py')
