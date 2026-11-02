from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "frontend" / "backend"
PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
REQUIREMENTS = BACKEND / "requirements.txt"

if not PYTHON.is_file():
    sys.exit(f"后端 B 的 Python 环境不存在：{PYTHON}")

if not REQUIREMENTS.is_file():
    sys.exit(f"后端 B 的 requirements.txt 不存在：{REQUIREMENTS}")

print("正式后端：", BACKEND)
print("依赖清单：", REQUIREMENTS)
print("开始安装后端 B 的依赖……")

result = subprocess.run(
    [str(PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
    cwd=str(BACKEND),
)

sys.exit(result.returncode)
