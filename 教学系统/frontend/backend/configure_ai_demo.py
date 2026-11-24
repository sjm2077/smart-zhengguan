"""Persist only a trusted, locally trained demo replay directory. Python 3.8 compatible."""
import argparse
import os
from pathlib import Path
import shutil
import tempfile
from dotenv import dotenv_values, set_key

KEY = 'AI_DEMO_REPLAY_DIR'


def persist_model_dir(env_file, model_dir):
    env_file = Path(env_file)
    model_dir = Path(model_dir).resolve(strict=True)
    if not env_file.is_file():
        raise ValueError('Existing backend .env required; refusing to replace configuration.')
    for name in ('report.json', 'demo_model.joblib'):
        if not (model_dir / name).is_file():
            raise ValueError('Missing model artifact: ' + name)
    original = env_file.read_bytes()
    before = dotenv_values(str(env_file), interpolate=False)
    value = model_dir.as_posix()
    fd, temp_name = tempfile.mkstemp(prefix='.ai-env-', dir=str(env_file.parent))
    os.close(fd)
    temp = Path(temp_name)
    try:
        temp.write_bytes(original)
        set_key(str(temp), KEY, value, quote_mode='always', encoding='utf-8')
        after = dotenv_values(str(temp), interpolate=False)
        expected = dict(before)
        expected[KEY] = value
        if dict(after) != expected:
            raise ValueError('Other dotenv settings would change; refusing update.')
        if env_file.read_bytes() != original:
            raise ValueError('Configuration changed during update; retry.')
        if temp.read_bytes() != original:
            shutil.copymode(str(env_file), str(temp))
            os.replace(str(temp), str(env_file))
    finally:
        if temp.exists():
            temp.unlink()
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', required=True)
    parser.add_argument('--confirm-local-artifact', action='store_true')
    args = parser.parse_args()
    if not args.confirm_local_artifact:
        parser.error('Only your own locally trained joblib artifact is allowed.')
    model_dir = Path(args.model_dir).resolve(strict=True)
    backend = Path(__file__).resolve().parent
    env_file = backend / '.env'
    if not env_file.is_file():
        raise ValueError('Existing backend .env required.')
    # Explicit path for the real read-only replay, before changing .env.
    os.environ[KEY] = model_dir.as_posix()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    from teaching.ai_demo_replay import replay
    result = replay()
    if result.get('demo_only') is not True or result.get('deployment_authorized') is not False:
        raise ValueError('Unexpected replay authorization contract')
    print('REPLAY OK: samples={}, flagged={}, actual_low={}'.format(result['samples'], result['flagged'], result['actual_low']))
    persist_model_dir(env_file, model_dir)
    print('CONFIG SAVED: AI_DEMO_REPLAY_DIR (other parsed .env settings preserved)')


if __name__ == '__main__':
    main()
