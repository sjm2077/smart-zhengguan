"""Capture/restore this upgrade without disturbing unrelated local changes."""
import argparse
import hashlib
import json
import sqlite3
import zipfile
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'src/views/IntelligentPrediction.vue', 'src/utils/riskGovernance.js',
    'tests/riskGovernance.test.mjs', 'expand_prediction_students.py',
    'backend/apps/graduate/management/commands/import_excel_data.py',
    'backend/apps/graduate/management/commands/expand_prediction_cohort.py',
    'backend/apps/graduate/tests/test_prediction_expansion.py',
    '研究生数据_2021-2026.xlsx',
]


def copy_database(source, destination):
    with sqlite3.connect(str(source)) as src, sqlite3.connect(str(destination)) as dst:
        src.backup(dst)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--restore', type=Path)
    args = parser.parse_args()
    if args.restore:
        checkpoint = args.restore.resolve()
        manifest = json.loads((checkpoint / 'manifest.json').read_text(encoding='utf-8'))
        with zipfile.ZipFile(checkpoint / 'files.zip') as archive:
            assert archive.testzip() is None
            for name, info in manifest.items():
                target = (ROOT / name).resolve()
                assert ROOT in target.parents
                if info['exists']:
                    data = archive.read(name)
                    assert hashlib.sha256(data).hexdigest() == info['sha256']
            # Save current database too, so restoring the checkpoint is reversible.
            copy_database(ROOT / 'backend/db.sqlite3', checkpoint / 'database_before_restore.sqlite3')
            copy_database(checkpoint / 'database.sqlite3', ROOT / 'backend/db.sqlite3')
            for name, info in manifest.items():
                target = ROOT / name
                if info['exists']:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(name))
                elif target.exists():
                    target.unlink()
        print('Restored code, workbook and database from:', checkpoint)
        return
    checkpoint = ROOT / '.local-backups' / ('prediction_upgrade_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    checkpoint.mkdir(parents=True)
    manifest = {}
    with zipfile.ZipFile(checkpoint / 'files.zip', 'x', zipfile.ZIP_DEFLATED) as archive:
        for name in FILES:
            target = ROOT / name
            info = {'exists': target.exists()}
            if target.exists():
                data = target.read_bytes()
                info['sha256'] = hashlib.sha256(data).hexdigest()
                archive.writestr(name, data)
            manifest[name] = info
    copy_database(ROOT / 'backend/db.sqlite3', checkpoint / 'database.sqlite3')
    (checkpoint / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (checkpoint / 'README.txt').write_text(
        'Restore code, Excel and database together:\n'
        f'backend\\.venv\\Scripts\\python.exe scripts\\prediction_checkpoint.py --restore "{checkpoint}"\n'
        'Restart the backend and refresh the browser after restoring.\n', encoding='utf-8')
    print(checkpoint)


if __name__ == '__main__':
    main()
