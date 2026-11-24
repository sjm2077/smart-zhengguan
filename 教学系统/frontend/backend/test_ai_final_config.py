import tempfile
import unittest
from pathlib import Path
from dotenv import dotenv_values
from configure_ai_demo import persist_model_dir, KEY


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = self.root / '.env'
        self.model = self.root / 'trusted model'
        self.model.mkdir()
        for name in ('report.json', 'demo_model.joblib'):
            (self.model / name).write_bytes(b'test placeholder; never loaded')
        self.env.write_text('# existing config\nDEEPSEEK_API_KEY=not-a-real-key\nDB_PASSWORD="test value"\n', encoding='utf-8')

    def test_preserves_other_settings_and_comments(self):
        before = dotenv_values(self.env, interpolate=False)
        persist_model_dir(self.env, self.model)
        after = dotenv_values(self.env, interpolate=False)
        self.assertEqual(after.pop(KEY), self.model.resolve().as_posix())
        self.assertEqual(before, after)
        self.assertIn('# existing config', self.env.read_text())

    def test_repeated_configuration_is_idempotent(self):
        persist_model_dir(self.env, self.model)
        first = self.env.read_bytes()
        persist_model_dir(self.env, self.model)
        self.assertEqual(first, self.env.read_bytes())

    def test_missing_artifact_does_not_change_config(self):
        (self.model / 'report.json').unlink()
        before = self.env.read_bytes()
        with self.assertRaises(ValueError):
            persist_model_dir(self.env, self.model)
        self.assertEqual(before, self.env.read_bytes())

    def test_replaces_existing_path(self):
        with self.env.open('a', encoding='utf-8') as stream:
            stream.write(KEY + '=old-path\n')
        persist_model_dir(self.env, self.model)
        self.assertEqual(dotenv_values(self.env)[KEY], self.model.resolve().as_posix())
        self.assertEqual(self.env.read_text().count(KEY+'='), 1)

if __name__ == '__main__':
    unittest.main()
