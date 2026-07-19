import streamlit as st
import importlib
import os
import streamlit.components.v1 as components


# 设置页面标题和布局
st.set_page_config(page_title="智慧政管平台",layout="wide")

st.title("绩效考核")
st.markdown(
    """
    <style>
    .css-hxt7ib { 
        display: none;
    }
    .block-container{
        padding-bottom:3rem;
        padding-right:3rem;
    }
    </style>
    
    """,
    unsafe_allow_html=True
)

base_path = os.path.join(os.path.dirname(__file__), "html")
with open(os.path.join(base_path, "总分柱状图.html"), "r", encoding="utf-8") as file1:
    content1 = file1.read()
components.html(content1, height=360)  

col1, col2 = st.columns(2)
with open(os.path.join(base_path, "分数一览.html"), "r", encoding="utf-8") as file2:
    content2 = file2.read()
with col2:
    components.html(content2, height=550)   

with open(os.path.join(base_path, "小分雷达图.html"), "r", encoding="utf-8") as file3:
    content3 = file3.read()
with col1:
    components.html(content3, height=550)
