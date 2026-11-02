"""知识库服务配置。

所有路径、数据库、模型参数集中在这里，方便答辩/部署时统一改。
不读取、不复制任何其他子系统的密钥；本服务的大模型 Key 只从
kb_service/.env 或系统环境变量读取，没有就降级为“纯检索模式”。
"""
from __future__ import annotations

import os
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent
ROOT = KB_DIR.parent
INDEX_DIR = KB_DIR / 'data'
INDEX_FILE = INDEX_DIR / 'kb.pkl'
META_FILE = INDEX_DIR / 'meta.json'


def load_env():
    """读取 kb_service/.env（若存在），不覆盖已有环境变量。"""
    env_file = KB_DIR / '.env'
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()

# ---------- 数据源 ----------
DATA_DIR = ROOT / 'data'
POLICY_DIRS = [
    ROOT / 'smartzhengguan' / 'smartzhengguan' / '研究生文件规定',
]
PLATFORM_DOCS = [
    ROOT / '智慧政管平台项目汇报_实在版.md',
    ROOT / '智慧政管平台项目建设规划书.md',
]
PAPER_CSV = DATA_DIR / 'Guanwang_papers_full_sum.csv'          # GBK，375 篇官网论文题录
CNKI_CSV = DATA_DIR / 'CNKI_山东大学 政治与公共管理学院.csv'    # GBK，55 篇
TEACHERS_JSON = DATA_DIR / 'teachers.json'

# ---------- MySQL（只读学院官网爬取数据） ----------
DB = dict(
    host=os.getenv('IMPORT_DB_HOST', '127.0.0.1'),
    port=int(os.getenv('IMPORT_DB_PORT', '3306')),
    user=os.getenv('IMPORT_DB_USER', 'root'),
    password=os.getenv('IMPORT_DB_PASS', 'root'),
    database=os.getenv('IMPORT_DB_NAME', 'zhhengguan_research'),
    charset='utf8mb4',
)

# ---------- 服务 ----------
HOST = os.getenv('KB_HOST', '127.0.0.1')
PORT = int(os.getenv('KB_PORT', '8900'))

# ---------- 大模型（可选） ----------
# 三种模式，优先级从上到下：
#   1. 直连 OpenAI 兼容接口：KB_LLM_API_KEY + KB_LLM_BASE_URL
#   2. 走已有后端代理（Key 只在服务端 .env，不在前端）：KB_LLM_PROXY
#   3. 都没有：纯检索模式（只返回原文摘录 + 引用，不生成）
LLM_API_KEY = os.getenv('KB_LLM_API_KEY', '')
LLM_BASE_URL = os.getenv('KB_LLM_BASE_URL', 'https://api.deepseek.com')
LLM_MODEL = os.getenv('KB_LLM_MODEL', 'deepseek-chat')
# 默认复用研究生子系统的聊天代理（它有服务端 Key，且主门户 AIAssistant 也走这条路）。
# 该代理不可用时，answer() 会自动降级为纯检索模式，不会报错给用户。
LLM_PROXY = os.getenv('KB_LLM_PROXY', 'http://127.0.0.1:8000/api/v1/chat-proxy/')
LLM_TIMEOUT = int(os.getenv('KB_LLM_TIMEOUT', '60'))

# ---------- 检索参数 ----------
CHUNK_SIZE = 450
CHUNK_OVERLAP = 90
TOP_K = 5
BM25_K1 = 1.5
BM25_B = 0.75
# 相关性命中门槛：命中不同查询词的比例低于该值的块直接丢弃（防止“只沾一个词”被当答案）
# 实测：本知识库外行问题覆盖率 0.14~0.21，正常问题 ≥0.30，故取 0.25
MIN_COVERAGE = 0.25
