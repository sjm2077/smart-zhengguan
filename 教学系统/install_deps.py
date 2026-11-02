# -*- coding: utf-8 -*-
"""使用 urllib 直接下载 wheel 文件，绕过代理问题"""
import subprocess
import sys
import os
import shutil

base_dir = os.path.dirname(os.path.abspath(__file__))
target_dir = os.path.join(base_dir, 'backend', 'python_packages')
os.makedirs(target_dir, exist_ok=True)

python_exe = sys.executable

packages = [
    'djangorestframework==3.15.2',
    'djangorestframework-simplejwt==5.3.1',
    'django-cors-headers==4.4.0',
    'django-filter==24.3',
    'python-dotenv==1.0.1',
]

# Try downloading wheels first using urllib bypassing proxy
import urllib.request
import json
import tempfile
import zipfile
import io

# First, manually construct a URL opener with no proxy
proxy_handler = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(proxy_handler)
urllib.request.install_opener(opener)

success_count = 0
fail_count = 0

download_dir = os.path.join(base_dir, 'backend', 'downloaded_wheels')
os.makedirs(download_dir, exist_ok=True)

def download_file(url, dest):
    """Download a file with no proxy"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'pip'})
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(dest, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"    Download error: {e}")
        return False

for pkg in packages:
    pkg_name, pkg_ver = pkg.split('==')
    print(f"\n--- 安装 {pkg} ---")
    
    # Try direct pip install first with env variables cleared
    clean_env = {}
    for k, v in os.environ.items():
        kl = k.lower()
        if 'proxy' not in kl:
            clean_env[k] = v
    for pv in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']:
        clean_env[pv] = ''
    
    # Try pip install with --proxy=""
    cmd = [
        python_exe, '-m', 'pip', 'install',
        '--target', target_dir,
        '--no-cache-dir',
        '--trusted-host', 'pypi.org',
        '--trusted-host', 'files.pythonhosted.org',
        '--proxy', '""',
        pkg
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, env=clean_env)
    
    if result.returncode == 0:
        print(f"  [OK] {pkg} (pip)")
        success_count += 1
        continue
    
    # Try downloading wheel from PyPI JSON API
    pypi_url = f"https://pypi.org/pypi/{pkg_name}/{pkg_ver}/json"
    try:
        req = urllib.request.Request(pypi_url, headers={'User-Agent': 'pip'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
        
        wheel_url = None
        for url_info in data.get('urls', []):
            if url_info['packagetype'] == 'bdist_wheel' and url_info['url'].endswith('.whl'):
                # Prefer py3-none-any
                if 'py3-none-any' in url_info['filename']:
                    wheel_url = url_info['url']
                    break
                if wheel_url is None:
                    wheel_url = url_info['url']
            elif url_info['packagetype'] == 'sdist' and wheel_url is None:
                wheel_url = url_info['url']
        
        if wheel_url:
            filename = os.path.basename(wheel_url.split('#')[0].split('?')[0])
            dest = os.path.join(download_dir, filename)
            print(f"    Downloading {filename}...")
            if download_file(wheel_url, dest):
                # Install the downloaded wheel
                install_cmd = [python_exe, '-m', 'pip', 'install', '--target', target_dir, '--no-deps', dest]
                result2 = subprocess.run(install_cmd, capture_output=True, text=True, timeout=60, env=clean_env)
                if result2.returncode == 0:
                    print(f"  [OK] {pkg} (wheel)")
                    success_count += 1
                    continue
                else:
                    print(f"  [FAIL] install error: {result2.stderr[-200:]}")
            else:
                print(f"  [FAIL] download failed")
        else:
            print(f"  [FAIL] no wheel found for {pkg}")
    except Exception as e:
        print(f"  [FAIL] {e}")
    
    fail_count += 1

# Cleanup temp downloads
if os.path.exists(download_dir):
    shutil.rmtree(download_dir, ignore_errors=True)

print(f"\n{'='*40}")
print(f"安装完成: 成功 {success_count}, 失败 {fail_count}")
print(f"安装目标: {target_dir}")

if success_count == len(packages):
    print("\n所有依赖安装成功!")
    sys.exit(0)
else:
    print(f"\n{len(packages) - success_count} 个依赖未安装")
    sys.exit(1)