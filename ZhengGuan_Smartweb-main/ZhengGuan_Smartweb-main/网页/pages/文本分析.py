import streamlit as st
import streamlit.components.v1 as components
import os


st.title("文本分析")
st.markdown(
    """
    <style>
    .css-hxt7ib { 
        display: none;
    }
    .block-container{
        padding-bottom:4rem;
        padding-right:2rem;
    }
    </style>
    
    """,
    unsafe_allow_html=True
)

base_path = os.path.join(os.path.dirname(__file__), "html")

with open(os.path.join(base_path, "词语相关图.html"), "r", encoding="utf-8") as file1:
    content1 = file1.read()
components.html(
    content1,
    height=620,  # 设置足够高度以避免内容裁剪
    scrolling=True#,  # 启用滚动支持
    # width=900
)  

col1, col2 = st.columns(2)

with open(os.path.join(base_path, "词云图.html"), "r", encoding="utf-8") as file2:
    content2 = file2.read()
with col1:
    components.html(content2, height=600)


with open(os.path.join(base_path, "论文年份.html"), "r", encoding="utf-8") as file3:
    content3 = file3.read()
with col2:
    components.html(content3, height=600)

import streamlit as st
import csv
import os
import re
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT
from whoosh.qparser import QueryParser
from jieba.analyse import ChineseAnalyzer

# 定义索引结构
schema = Schema(
    title=TEXT(stored=True, analyzer=ChineseAnalyzer()),  # 存储标题
    abstract=TEXT(stored=True, analyzer=ChineseAnalyzer())  # 存储摘要
)

# 定义索引存储目录
index_dir = "paper_index"

# 定义一个全局变量保存索引
ix = None

# 仅在第一次启动时创建索引
if not os.path.exists(index_dir):
    os.mkdir(index_dir)
    # 创建索引
    ix = create_in(index_dir, schema)
    
    # 打开 CSV 文件并读取数据
    with open('../data/Guanwang_papers_full_sum.csv', 'r', encoding='GBK') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过表头（如果有的话）
        
        # 打开索引写入器
        writer = ix.writer()

        # 遍历 CSV 文件中的每一行并将数据添加到索引中
        for row in reader:
            title, abstract = row[0], row[1]
            writer.add_document(title=title, abstract=abstract)
        
        # 提交索引写入器
        writer.commit()

else:
    # 如果索引目录已存在，直接加载索引到内存
    ix = open_dir(index_dir)

# 转换用户输入的查询语句
def convert(user_query):
    query = re.sub(r'(?<=\S)-(?=\S)', r' - ', user_query)
    query = re.sub(r'\s*-\s*', ' NOT ', query)
    query = re.sub(r'or', r' OR ', query, flags=re.IGNORECASE)
    query = query.strip()
    return query

# 执行查询并显示结果
def search(query_str):
    global ix
    query_str = convert(query_str)
    
    # 创建查询解析器
    qp = QueryParser("abstract", schema=ix.schema)  # 可以修改为"title"或者"abstract"来指定检索字段

    # 解析查询
    query = qp.parse(query_str)

    # 执行查询并返回结果
    with ix.searcher() as searcher:
        results = searcher.search(query)
        sorted_results = []
        for i, result in enumerate(results):
            title = result['title']
            sorted_results.append({
                'index': i,  # 添加索引值用于排序
                'title': title
            })

        # 按照结果的顺序（即返回的列号）排序
        sorted_results = sorted(sorted_results, key=lambda x: x['index'])
        return sorted_results

# Streamlit 用户界面
st.markdown("##### 论文检索系统")

# 用户输入查询关键词
user_query = st.text_input("请输入查询关键词：", "")

if user_query:
    # 执行查询
    results = search(user_query)

    # 显示查询结果
    if results:
        for res in results:
            st.write(f"{res['index'] + 1}. {res['title']}")  # 输出排序后的标题，并加上序号
    else:
        st.write("未找到相关结果。")