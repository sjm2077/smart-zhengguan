import subprocess, sys, os
os.chdir(r'd:\AAAstudy\大三下\实训二\人事\Test5')
result = subprocess.run([sys.executable, 'manage.py', 'check'], capture_output=True, text=True)
with open('_test_output.txt', 'w', encoding='utf-8') as f:
    f.write('STDOUT:\n' + result.stdout + '\n\nSTDERR:\n' + result.stderr + '\n\nReturn code: ' + str(result.returncode))
    f.write('\n\n---Python version: ' + sys.version)
    try:
        import django; f.write('\nDjango: ' + django.VERSION)
    except: f.write('\nDjango: NOT INSTALLED')
