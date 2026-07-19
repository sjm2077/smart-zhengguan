import streamlit as st
import streamlit.components.v1 as components
import os


st.title("师资力量")
st.markdown(
    """
    <style>
    .css-hxt7ib { 
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

base_path = os.path.join(os.path.dirname(__file__), "html")

with open(os.path.join(base_path, "培养经历.html"), "r", encoding="utf-8") as file1:
    content1 = file1.read()
components.html(content1, height=500)  

col1, col2 = st.columns([2, 1])
with open(os.path.join(base_path, "职称情况.html"), "r", encoding="utf-8") as file2:
    content2 = file2.read()
with col1:
    components.html(content2, height=400)

with open(os.path.join(base_path, "学位情况.html"), "r", encoding="utf-8") as file3:
    content3 = file3.read()
with col2:
    components.html(content3, height=400)

with open(os.path.join(base_path, "年度回顾.html"), "r", encoding="utf-8") as file4:
    content4 = file4.read()
components.html(content4, height=1400)
