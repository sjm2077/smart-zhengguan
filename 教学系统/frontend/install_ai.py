# -*- coding: utf-8 -*-
"""仅注册智能分析中心需要的 4 处接入，不替换或改写其他页面业务代码。
运行位置：frontend 目录。首次运行自动备份，重复运行不重复插入。
"""
from pathlib import Path
import re
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
TARGETS = {
    "router": ROOT / "src/router/index.ts",
    "layout": ROOT / "src/layout/MainLayout.vue",
    "models": ROOT / "backend/teaching/models.py",
    "urls": ROOT / "backend/teaching/urls.py",
}
ADDITIONS = [
    ROOT / "src/views/ai/AIWarningCenter.vue",
    ROOT / "backend/teaching/ai_models.py",
    ROOT / "backend/teaching/ai_views.py",
    ROOT / "backend/teaching/ai_urls.py",
    ROOT / "backend/teaching/ai_checks.py",
]


def safe_insert(current: str, anchor: str, inserted: str, label: str) -> str:
    if current.count(anchor) != 1:
        raise RuntimeError(f"{label} 的接入位置不唯一或不存在；拒绝修改，请保留原文件并联系开发者检查。")
    return current.replace(anchor, inserted + anchor, 1)


def patch_router(code: str) -> str:
    if "AIWarningCenter.vue" in code and "path: 'ai-warning'" in code:
        return code
    if "AIWarningCenter.vue" not in code:
        insertion = "import AIWarningCenter from '../views/ai/AIWarningCenter.vue'\n"
        code = safe_insert(code, 'const routes = [', insertion + "\n", "router imports")
    if "path: 'ai-warning'" not in code:
        # 新路由放在已有警告页前；不改动原来的教学预警、教师和学生路由。
        match = re.search(r'(?m)^\s*\{\s*\n\s*path:\s*[\'\"]dashboard/warning[\'\"]', code)
        if not match:
            raise RuntimeError("router 找不到现有 dashboard/warning 路由，请检查最新路由结构。")
        insertion = "      {\n        path: 'ai-warning',\n        name: 'ai-warning',\n        component: AIWarningCenter,\n      },\n"
        code = code[:match.start()] + "\n" + insertion + code[match.start():]
    return code


def patch_layout(code: str) -> str:
    if "path: '/ai-warning'" in code:
        return code
    match = re.search(r"(?m)^\s*\{\s*path:\s*['\"]/analysis['\"],\s*label:\s*['\"]教学分析['\"].*$", code)
    if not match:
        raise RuntimeError("MainLayout.vue 找不到教学分析菜单项，无法安全新增导航。")
    newline = "\r\n" if "\r\n" in code else "\n"
    row = "  { path: '/ai-warning', label: '智能分析预警', icon: 'M12 3L2 20h20L12 3z M12 9v4 M12 17h.01' },"
    return code[:match.end()] + newline + row + code[match.end():]


def patch_models(code: str) -> str:
    if "from .ai_models import AIWarningCase" in code:
        return code
    return code.rstrip() + "\n\n# 智能预警处理记录：与 teaching 原有模型共用 Django 应用。\nfrom .ai_models import AIWarningCase\n"


def patch_urls(code: str) -> str:
    if 'include("teaching.ai_urls")' in code or "include('teaching.ai_urls')" in code:
        return code
    if "from django.urls import" not in code or "include" not in code:
        raise RuntimeError("teaching/urls.py 缺少 Django include 导入，无法安全注册 AI 接口。")
    match = re.search(r"(?m)^\s*path\(\s*['\"]['\"]\s*,\s*include\(router\.urls\)\s*\)\s*,?", code)
    if not match:
        raise RuntimeError("teaching/urls.py 找不到现有 router.urls 路由，无法安全接入。")
    indent = re.match(r"\s*", code[code.rfind('\n', 0, match.start())+1:match.end()]).group(0)
    addition = indent + 'path("ai/", include("teaching.ai_urls")),\n'
    return code[:match.start()] + addition + code[match.start():]


def main():
    if not all(p.is_file() for p in ADDITIONS):
        missing = [str(p.relative_to(ROOT)) for p in ADDITIONS if not p.is_file()]
        sys.exit("请先将 ZIP 解压到 frontend 目录；缺少新增文件：" + ", ".join(missing))
    if not all(p.is_file() for p in TARGETS.values()):
        missing = [str(p.relative_to(ROOT)) for p in TARGETS.values() if not p.is_file()]
        sys.exit("找不到原项目接入文件，停止修改：" + ", ".join(missing))
    methods = {"router": patch_router, "layout": patch_layout, "models": patch_models, "urls": patch_urls}
    updated = {}
    # 先预演所有文件，全部有合法锚点才开始写回。
    for name, path in TARGETS.items():
        original = path.read_text(encoding="utf-8-sig")
        revised = methods[name](original)
        if revised != original:
            updated[name] = (path, original, revised)
    if not updated:
        print("接入代码已存在，未做重复修改。")
        return
    suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
    for name, (path, original, revised) in updated.items():
        backup = path.with_name(path.name + ".before_ai_" + suffix + ".bak")
        backup.write_text(original, encoding="utf-8")
        path.write_text(revised, encoding="utf-8")
        print("已接入：", path.relative_to(ROOT), "| 备份：", backup.name)
    print("\n源码接入完成。现在运行：")
    print("  cd backend")
    print("  python manage.py makemigrations teaching")
    print("  python manage.py migrate")
    print("  cd ..")
    print("  npm run type-check")
    print("  npm run build")


if __name__ == "__main__":
    main()
