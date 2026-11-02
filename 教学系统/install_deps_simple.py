import subprocess
import sys
import os

# Remove all proxy-related environment variables
proxy_keys = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy', 'FTP_PROXY', 'ftp_proxy', 'NO_PROXY', 'no_proxy', 'PIP_NO_PROXY']
for key in proxy_keys:
    if key in os.environ:
        del os.environ[key]

packages = [
    "djangorestframework==3.15.2",
    "djangorestframework-simplejwt==5.3.1", 
    "django-cors-headers==4.4.0",
    "django-filter==24.3",
    "PyMySQL==1.1.1",
    "python-dotenv==1.0.1",
]

for pkg in packages:
    print(f"\n>>> Installing {pkg} ...")
    cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", pkg]
    print(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    print(f"Return code: {result.returncode}")

# Verify installation
print("\n>>> Verifying imports...")
try:
    import rest_framework
    print("rest_framework: OK")
except:
    print("rest_framework: FAILED")

try:
    import rest_framework_simplejwt
    print("rest_framework_simplejwt: OK")
except:
    print("rest_framework_simplejwt: FAILED")

try:
    import corsheaders
    print("corsheaders: OK")
except:
    print("corsheaders: FAILED")

try:
    import django_filters
    print("django_filters: OK")
except:
    print("django_filters: FAILED")

try:
    import dotenv
    print("dotenv: OK")
except:
    print("dotenv: FAILED")