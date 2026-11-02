"""知识库 + 智能体 HTTP 服务（Python 标准库，零额外依赖）。

接口：
  GET  /health                     服务与索引状态
  GET  /stats                      知识库构成 + 官方口径数字
  GET  /search?q=&topk=&type=      检索
  POST /ask   {"question": "..."}  智能体问答（带引用）
  GET  /faculty?name=&dept=&title= 官网教师名录
  GET  /notices?q=&limit=          官网通知公告

启动：
  python kb_service/server.py            # 默认 127.0.0.1:8900
  python kb_service/ingest.py            # 重建索引（官网爬虫更新后执行）
"""
from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import config
from agent import KB
from search import BM25Index

_state = {'kb': None, 'lock': threading.Lock()}


def get_kb(rebuild=False):
    with _state['lock']:
        if _state['kb'] is not None and not rebuild:
            return _state['kb']
        index = BM25Index.load()
        if index is None or rebuild:
            print('[INFO] 索引不存在或要求重建，开始构建…')
            from ingest import Builder
            Builder().build()
            index = BM25Index.load()
        meta = {}
        if config.META_FILE.exists():
            meta = json.loads(config.META_FILE.read_text(encoding='utf-8'))
        _state['kb'] = KB(index, meta)
        print('[INFO] 索引就绪：分块 %d，词表 %d，构建于 %s' % (
            len(index.chunks), len(index.postings), index.built_at))
        return _state['kb']


class Handler(BaseHTTPRequestHandler):
    server_version = 'ZG-KB/1.0'

    def log_message(self, fmt, *args):
        print('  %s - %s' % (self.address_string(), fmt % args))

    # ---------- 通用 ----------
    def _send(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send({'ok': True})

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            qs = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            path = parsed.path.rstrip('/') or '/'

            if path in ('/', '/health'):
                kb = get_kb()
                self._send({
                    'status': 'ok',
                    'chunks': len(kb.index.chunks),
                    'vocab': len(kb.index.postings),
                    'built_at': kb.index.built_at,
                    'llm': bool(config.LLM_API_KEY or config.LLM_PROXY),
                    'llm_mode': 'proxy' if config.LLM_PROXY else ('direct' if config.LLM_API_KEY else 'retrieval-only'),
                })
                return

            if path == '/stats':
                kb = get_kb()
                meta = kb.meta
                self._send({
                    'built_at': meta.get('built_at', ''),
                    'doc_count': meta.get('doc_count', 0),
                    'chunk_count': meta.get('chunk_count', 0),
                    'vocab': meta.get('vocab', 0),
                    'by_type': meta.get('by_type', {}),
                    'stats': meta.get('stats', {}),
                    'sources': meta.get('sources', {}),
                    # 数据覆盖情况：教师详情页采到多少人、通知里有多少带正文、成果多少条
                    'corpus': meta.get('corpus', {}),
                    'achievement': meta.get('achievement', {}),
                    'faculty_count': len(meta.get('faculty') or []),
                    'notice_count': len(meta.get('notices') or []),
                })
                return

            if path == '/search':
                kb = get_kb()
                q = qs.get('q', '').strip()
                if not q:
                    self._send({'error': 'q is required'}, 400)
                    return
                topk = int(qs.get('topk', config.TOP_K))
                doc_type = qs.get('type', '').strip()
                self._send({'query': q, 'type': doc_type, 'data': kb.kb_search(q, topk=topk, doc_type=doc_type)})
                return

            if path == '/faculty':
                kb = get_kb()
                self._send({'data': kb.faculty_lookup(
                    name=qs.get('name', '').strip(),
                    dept=qs.get('dept', '').strip(),
                    title=qs.get('title', '').strip(),
                    limit=int(qs.get('limit', 20)),
                )})
                return

            if path == '/notices':
                kb = get_kb()
                self._send({'data': kb.notice_search(qs.get('q', '').strip(), int(qs.get('limit', 5)))})
                return

            self._send({'error': 'not found'}, 404)
        except Exception as exc:
            self._send({'error': str(exc)}, 500)

    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip('/') or '/'
            length = int(self.headers.get('Content-Length') or 0)
            raw = self.rfile.read(length) if length else b'{}'
            try:
                body = json.loads(raw.decode('utf-8'))
            except Exception:
                self._send({'error': 'invalid json'}, 400)
                return

            if path == '/ask':
                question = (body.get('question') or '').strip()
                if not question:
                    self._send({'error': 'question is required'}, 400)
                    return
                kb = get_kb()
                self._send(kb.answer(question))
                return

            if path == '/rebuild':
                get_kb(rebuild=True)
                kb = get_kb()
                self._send({'ok': True, 'chunks': len(kb.index.chunks), 'built_at': kb.index.built_at})
                return

            self._send({'error': 'not found'}, 404)
        except Exception as exc:
            self._send({'error': str(exc)}, 500)


def main():
    get_kb()
    print('知识库服务已启动：http://%s:%d' % (config.HOST, config.PORT))
    print('  /health  /stats  /search?q=  /ask  /faculty  /notices')
    ThreadingHTTPServer((config.HOST, config.PORT), Handler).serve_forever()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n已停止')
        sys.exit(0)
