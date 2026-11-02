# 采集官网真实数据 → 重建知识库索引（一条命令完成闭环）
# 用法： powershell -ExecutionPolicy Bypass -File scripts\refresh_kb.ps1
#        powershell -ExecutionPolicy Bypass -File scripts\refresh_kb.ps1 -Pages 20 -WithDetail
#        powershell -ExecutionPolicy Bypass -File scripts\refresh_kb.ps1 -Pages 20 -WithDetail -TeacherProfile

param(
    [int]$Pages = 12,
    [switch]$WithDetail,
    [int]$DetailLimit = 0,
    [switch]$TeacherProfile,
    [int]$ProfileLimit = 0,
    [switch]$ProfileRetry
)

$ErrorActionPreference = 'Stop'
$Root   = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root 'research_system\venv\Scripts\python.exe'
$env:PYTHONIOENCODING = 'utf-8'

if (-not (Test-Path $Python)) { throw "未找到虚拟环境 Python：$Python" }

$crawlArgs = @((Join-Path $Root 'scripts\crawler_pspa.py'), '--once', '--pages', $Pages)
if ($WithDetail) {
    $crawlArgs += '--with-detail'
    $crawlArgs += '--detail-limit'
    $crawlArgs += $DetailLimit
}
if ($TeacherProfile) {
    $crawlArgs += '--teacher-profile'
    $crawlArgs += '--profile-limit'
    $crawlArgs += $ProfileLimit
}
if ($ProfileRetry) {
    $crawlArgs += '--profile-retry'
}

Write-Host '[1/2] 采集学院官网数据…'
& $Python @crawlArgs

Write-Host ''
Write-Host '[2/2] 重建知识库索引…'
& $Python (Join-Path $Root 'kb_service\ingest.py')

Write-Host ''
Write-Host '完成。若知识库服务正在运行，调用 POST /kb/rebuild 可热加载新索引：'
Write-Host '  Invoke-WebRequest -Uri http://127.0.0.1:8900/rebuild -Method Post -UseBasicParsing'
