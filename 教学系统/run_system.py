from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
start = root / "start.bat"

if not start.exists():
    print(f"正式启动入口不存在：{start}")
    sys.exit(1)

subprocess.Popen(
    ["cmd.exe", "/c", str(start)],
    cwd=str(root),
    creationflags=subprocess.CREATE_NEW_CONSOLE,
)
print("已调用统一启动入口 start.bat；正式后端为 frontend/backend。")
