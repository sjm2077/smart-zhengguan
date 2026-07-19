import shutil, os
base = r'd:\AAAstudy\大三下\实训二\人事\Test5'
files = [
    (os.path.join(base, 'css', 'styles.css'), os.path.join(base, 'static', 'css', 'styles.css')),
    (os.path.join(base, 'js', 'main.js'), os.path.join(base, 'static', 'js', 'main.js')),
]
for src, dst in files:
    shutil.copy(src, dst)
    print(f'Copied: {src} -> {dst}')
print('All done!')
