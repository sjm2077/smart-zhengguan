"""中文检索核心：字符二元分词 + BM25。

为什么不用向量检索：
  - 向量检索需要 Embedding（本地要 GPU/大模型，在线要按 token 付费），
    目前已确认为“待评估预算”项，因此先用零成本的 BM25 保证可用；
  - 接口层预留了 embedding 位（见 search() 的注释），后续换索引不用改调用方。
"""
from __future__ import annotations

import math
import pickle
import re
from collections import Counter
from pathlib import Path

import config

CJK_RE = re.compile(r'[\u4e00-\u9fff]+')
ASCII_RE = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9.\-]*')

# 极简停用词（中文虚词 + 常见无信息词），避免撑大倒排表
STOPWORDS = set("""
的 了 和 与 及 或 在 是 为 对 从 到 由 以 其 之 而 也 都 就 但 并 且 等 这 那 有 无 不 很
我 你 他 她 它 我们 你们 他们 请问 关于 进行 通过 根据 按照 关于 一个 一种 什么 怎么 如何
以及 同时 相关 有关 可以 需要 必须 应该 已 将 把 被 让 使 于 中 上 下 内 外 前 后
""".split())


def tokenize(text: str):
    """中文按二元切分，英文/数字按词切分，去掉停用词。"""
    text = (text or '').lower()
    tokens = []
    for m in CJK_RE.finditer(text):
        run = m.group(0)
        if len(run) == 1:
            if run not in STOPWORDS:
                tokens.append(run)
            continue
        for i in range(len(run) - 1):
            gram = run[i:i + 2]
            if gram not in STOPWORDS:
                tokens.append(gram)
    for m in ASCII_RE.finditer(text):
        w = m.group(0)
        if len(w) <= 1 and not w.isdigit():
            continue
        if w not in STOPWORDS:
            tokens.append(w)
    return tokens


# 领域同义词/近义说法：查询侧扩展，索引不重复建（零成本提升召回）
# 例如问“师资力量”时，正文里写的可能是“在职教师/教授”，二元分词命中不了，需要补词
QUERY_EXPANSION = {
    '师资': ['教师', '教授', '副教授'],
    '老师': ['教师', '导师'],
    '教师': ['师资', '导师'],
    '经费': ['科研经费', '项目经费'],
    '奖助': ['奖学金', '助学金', '资助'],
    '奖学金': ['奖助', '评审', '资助'],
    '论文': ['题录', '期刊', '发表'],
    '成果': ['获奖', '著作', '论文'],
    '研究方向': ['研究领域', '主要从事'],
    '研究领域': ['研究方向', '主要从事'],
    '招生': ['招收', '录取'],
    '研究生': ['硕士', '博士', 'MPA'],
    '通知': ['公告', '公示', '申报'],
    '公告': ['通知', '公示'],
    '制度': ['规定', '办法', '细则'],
    '规定': ['办法', '细则', '制度'],
}


def expand_query(query: str):
    """返回与查询相关、但原查询里没出现的补充词（用于加权召回）。"""
    q = query or ''
    extras = []
    for key, values in QUERY_EXPANSION.items():
        if key in q:
            for v in values:
                if v not in q:
                    extras.append(v)
    return extras


class BM25Index:
    """内存倒排 + BM25 打分，序列化用 pickle。"""

    def __init__(self, chunks=None):
        self.chunks = chunks or []
        self.postings = {}      # token -> [(chunk_idx, tf), ...]
        self.doc_len = []
        self.avgdl = 1.0
        self.idf = {}
        self.built_at = ''
        if chunks:
            self.build(chunks)

    def build(self, chunks):
        self.chunks = chunks
        self.postings = {}
        self.doc_len = []
        for idx, ch in enumerate(chunks):
            toks = tokenize(ch['title'] + ' ' + ch['text'])
            # 标题加权：标题词重复计入一次
            toks += tokenize(ch['title'])
            tf = Counter(toks)
            self.doc_len.append(len(toks) or 1)
            for tok, c in tf.items():
                self.postings.setdefault(tok, []).append((idx, c))
        self.avgdl = sum(self.doc_len) / max(1, len(self.doc_len))
        n = len(self.chunks)
        self.idf = {}
        for tok, plist in self.postings.items():
            df = len(plist)
            self.idf[tok] = math.log(1 + (n - df + 0.5) / (df + 0.5))
        return self

    # ---------- 检索 ----------
    def search(self, query: str, topk: int = 5, doc_type: str = '', min_score: float = 0.0):
        q_tokens = tokenize(query)
        if not q_tokens or not self.chunks:
            return []
        # 原查询词权重 1.0；同义扩展词权重 0.45，只加召回、不喧宾夺主
        base = set(q_tokens)
        extra = {t for v in expand_query(query) for t in tokenize(v)} - base
        weighted = [(tok, 1.0) for tok in base] + [(tok, 0.45) for tok in extra]

        scores = {}
        for tok, weight in weighted:
            plist = self.postings.get(tok)
            if not plist:
                continue
            idf = self.idf.get(tok, 0.0)
            for idx, tf in plist:
                dl = self.doc_len[idx]
                denom = tf + config.BM25_K1 * (1 - config.BM25_B + config.BM25_B * dl / self.avgdl)
                scores[idx] = scores.get(idx, 0.0) + weight * idf * tf * (config.BM25_K1 + 1) / denom

        # 覆盖度加分：命中的不同查询词越多，排越前（缓解长查询被单一高频词主导）
        hit = {}
        for tok in base:
            for idx, _tf in self.postings.get(tok, []):
                hit[idx] = hit.get(idx, 0) + 1
        total_q = len(base)
        for idx in list(scores):
            scores[idx] *= 1 + 0.6 * hit.get(idx, 0) / total_q

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        out = []
        for idx, score in ranked:
            ch = self.chunks[idx]
            if doc_type and ch.get('type') != doc_type:
                continue
            if score < min_score:
                continue
            item = dict(ch)
            item['score'] = round(score, 4)
            # 覆盖度：该块命中了多少个不同的原查询词（0~1），用于过滤“只沾一个词”的弱相关结果
            item['coverage'] = round(hit.get(idx, 0) / total_q, 3)
            out.append(item)
            if len(out) >= topk:
                break
        return out

    # ---------- 持久化 ----------
    def save(self, path: Path = None):
        path = path or config.INDEX_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'postings': self.postings,
                'doc_len': self.doc_len,
                'avgdl': self.avgdl,
                'idf': self.idf,
                'built_at': self.built_at,
            }, f, protocol=4)

    @classmethod
    def load(cls, path: Path = None):
        path = path or config.INDEX_FILE
        if not Path(path).exists():
            return None
        with open(path, 'rb') as f:
            data = pickle.load(f)
        obj = cls.__new__(cls)
        obj.chunks = data['chunks']
        obj.postings = data['postings']
        obj.doc_len = data['doc_len']
        obj.avgdl = data['avgdl']
        obj.idf = data['idf']
        obj.built_at = data.get('built_at', '')
        return obj
