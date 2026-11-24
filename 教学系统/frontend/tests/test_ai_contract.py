"""在未安装 Django / Vue 的环境下做静态契约验证：python -m unittest discover -s tests -v。"""
from pathlib import Path
from importlib.machinery import SourceFileLoader
import ast
import unittest

ROOT = Path(__file__).resolve().parent.parent
install = SourceFileLoader("ai_installer_test", str(ROOT / "install_ai.py")).load_module()


class TestIntegrationContracts(unittest.TestCase):
    def test_minimal_router_injection_idempotent(self):
        old = "import A from 'x'\nconst routes = [\n      {\n        path: 'dashboard/warning',\n      },\n]\n"
        code = install.patch_router(old)
        self.assertIn("path: 'ai-warning'", code)
        self.assertEqual(install.patch_router(code), code)
        self.assertIn("path: 'dashboard/warning'", code)

    def test_menu_injection_preserves_original(self):
        old = "const menuItems = [\n  { path: '/analysis', label: '教学分析', icon: 'M12 20' },\n]\n"
        code = install.patch_layout(old)
        self.assertIn("智能分析预警", code)
        self.assertEqual(install.patch_layout(code), code)
        self.assertIn("教学分析", code)

    def test_backend_additions_safe(self):
        models = "from django.db import models\n"
        urls = 'from django.urls import path, include\nurlpatterns = [\n    path("", include(router.urls)),\n]\n'
        self.assertEqual(install.patch_models(install.patch_models(models)), install.patch_models(models))
        self.assertEqual(install.patch_urls(install.patch_urls(urls)), install.patch_urls(urls))

    def test_backend_syntax(self):
        for file in (ROOT / "backend/teaching").glob("ai_*.py"):
            with self.subTest(file=file.name):
                ast.parse(file.read_text(encoding="utf-8"))

    def test_no_frontend_api_secret(self):
        vue = (ROOT / "src/views/ai/AIWarningCenter.vue").read_text(encoding="utf-8")
        self.assertNotIn("DEEPSEEK_API_KEY", vue)
        self.assertIn("/ai/chat/", vue)
        self.assertIn("/ai/warnings/sync/", vue)
        self.assertIn("/ai-warning", vue)


if __name__ == "__main__":
    unittest.main()
