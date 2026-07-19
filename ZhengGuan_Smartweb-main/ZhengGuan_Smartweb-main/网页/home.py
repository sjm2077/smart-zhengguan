import streamlit as st
import importlib
import importlib.util
import os
import sys
import subprocess

def install_and_import(package):
    try:
        importlib.import_module(package)
    except ImportError:
        try:
            print(f"正在安装 {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"{package} 安装成功")
        except Exception as e:
            print(f"无法安装 {package}: {e}")
    finally:
        globals()[package] = importlib.import_module(package)

# 自动检测并安装依赖库
required_packages = ["jieba", "whoosh"]
for package in required_packages:
    install_and_import(package)

def rewrite_streamlit_index(new_content):
    try:
        # 动态获取 Streamlit 模块的安装路径
        streamlit_spec = importlib.util.find_spec("streamlit")
        if not streamlit_spec or not streamlit_spec.submodule_search_locations:
            raise ModuleNotFoundError("未找到 Streamlit")

        streamlit_path = streamlit_spec.submodule_search_locations[0]
        index_file_path = os.path.join(streamlit_path, "static", "index.html")

        # 检查文件是否存在
        if not os.path.isfile(index_file_path):
            raise FileNotFoundError(f"找不到文件 {index_file_path}")

        # 写入新内容
        with open(index_file_path, "w", encoding="utf-8") as file:
            file.write(new_content)

        print(f"覆写了 {index_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")


rewrite_streamlit_index(
"""
<!doctype html><html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1,shrink-to-fit=no"/><link rel="shortcut icon" href="./favicon.png"/><link rel="preload" href="./static/media/SourceSansPro-Regular.0d69e5ff5e92ac64a0c9.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="./static/media/SourceSansPro-SemiBold.abed79cd0df1827e18cf.woff2" as="font" type="font/woff2" crossorigin><link rel="preload" href="./static/media/SourceSansPro-Bold.118dea98980e20a81ced.woff2" as="font" type="font/woff2" crossorigin><title>Streamlit</title><script>window.prerenderReady=!1</script><script defer="defer" src="./static/js/main.75ac1cb6.js"></script><link href="./static/css/main.23bdda6f.css" rel="stylesheet"></head><body><script src="https://agi-dev-platform-web.bj.bcebos.com/ai_apaas/embed/output/embedLiteSDK.js?responseExpires=0"></script> <script> new EmbedLiteSDK({appId: '3e32fc42-53b6-495d-a739-38b13c50ca6a', code: 'embed3dx7ftgTSl8cQNPH6DsF'}); </script><style>.appbuilder-bubbleContent{top: 100px !important; height: calc(100% - 140px) !important;}</style><noscript>You need to enable JavaScript to run this app.</noscript><div id="root"></div></body></html>
"""
)


# 设置页面标题和布局
st.set_page_config(page_title="智慧政管平台",layout="wide")

st.markdown(f"<h1 style='color: rgb(86,110,230);'>智慧政管平台</h1>", unsafe_allow_html=True)
st.markdown(
    """
    <style>
    /* 隐藏侧边栏拖动手柄 */
    .css-hxt7ib {  /* 这个类名可能会更新 */
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)
