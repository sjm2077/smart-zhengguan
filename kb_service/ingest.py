"""知识库构建：把「官网真实爬取数据 + 真实文件 + 制度文件」切成块并建索引。

数据源与可信级别（与主门户大屏的角标口径保持一致）：
  A 学院官网真实爬取：教师名录 / 学术成果 / 通知公告(含正文) / 学院简介
  B 真实采集文件：官网论文题录 375 篇、CNKI 题录 55 篇、教师履历 teachers.json
  C 学校/学院制度文件：研究生文件规定 7 份（txt 原文）
  D 平台自述：项目汇报与规划文档（回答“平台怎么做的”类问题）
"""
from __future__ import annotations

import csv
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import config
from search import BM25Index

csv.field_size_limit(10 ** 8)


def clean(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').replace('\u3000', ' ')).strip()


def chunk_text(text: str, size: int = None, overlap: int = None):
    size = size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP
    text = clean(text)
    if len(text) <= size:
        return [text] if text else []
    out, start = [], 0
    step = max(1, size - overlap)
    while start < len(text):
        out.append(text[start:start + size])
        if start + size >= len(text):
            break
        start += step
    return out


class Builder:
    def __init__(self):
        self.chunks = []
        self.stats = {}
        self.faculty = []
        self.notices = []
        self.counts = {}
        self.achievement_years = Counter()
        self.achievement_cats = Counter()
        self.recent_achv = []
        self.paper_count = 0
        self.notice_body_count = 0
        self.teacher_profile_count = 0

    def _add(self, doc_type, source_label, title, text, url='', date='', extra=None):
        if not text:
            return 0
        for i, piece in enumerate(chunk_text(text)):
            ch = {
                'id': '%s:%d' % (extra.get('doc_id') if extra else title, i),
                'type': doc_type,
                'source': source_label,
                'title': clean(title)[:200],
                'text': piece,
                'url': url or '',
                'date': date or '',
            }
            if extra and extra.get('meta'):
                ch['meta'] = extra['meta']
            self.chunks.append(ch)
        self.counts[doc_type] = self.counts.get(doc_type, 0) + 1
        return 1

    # ---------- A. 官网爬取（MySQL） ----------
    def load_official(self):
        import pymysql
        try:
            conn = pymysql.connect(**config.DB)
            cur = conn.cursor()
        except Exception as exc:
            print('[WARN] 连不上 MySQL，跳过官网爬取数据：%s' % exc)
            return

        try:
            # 教师名录：一人一文档（便于“某老师什么职称/哪个系”直接命中）
            # 有详情页（研究方向/简历/项目/课程）的，把正文一并入库；这是官网真实页面内容
            cur.execute("""
                SELECT name, title, dept, url, profile, research, profile_source
                FROM api_pspa_teacher ORDER BY dept, name
            """)
            for name, title, dept, url, profile, research, psrc in cur.fetchall():
                self.faculty.append({'name': name, 'title': title or '', 'dept': dept or '',
                                     'url': url or '', 'research': research or ''})
                head = '%s，%s，%s。' % (name, dept or '学院', title or '职称未标注')
                if research:
                    head += '研究方向：%s。' % research
                if profile:
                    self.teacher_profile_count += 1
                    text = head + '官网个人主页摘录：' + profile
                else:
                    text = head + '学院官网教师名录收录，暂未采集到个人详情页。'
                self._add('faculty', '学院官网·教师名录', '%s（%s）' % (name, title or '教师'), text,
                          url=url or '', extra={'doc_id': 'teacher:' + name})

            # 学术成果：按类别+标题
            cur.execute("SELECT category, title, publish_date, url FROM api_pspa_achievement ORDER BY publish_date DESC")
            for cat, title, date, url in cur.fetchall():
                m = re.search(r'(20\d{2})', date or '')
                self.achievement_years[m.group(1)] += 1
                self.achievement_cats[cat or '未分类'] += 1
                if len(self.recent_achv) < 12:
                    self.recent_achv.append({'title': title, 'date': date or '',
                                             'category': cat or '未分类', 'url': url or ''})
                text = '【%s】%s，发布日期 %s。' % (cat or '学术成果', title, date or '未标注')
                self._add('achievement', '学院官网·学术成果', title, text,
                          url=url or '', date=date or '', extra={'doc_id': 'ach:' + (url or title)})

            # 通知公告：优先用正文，无正文则退回标题
            cur.execute("""
                SELECT title, publish_date, url, content FROM api_pspa_notice
                ORDER BY publish_date DESC
            """)
            for title, date, url, content in cur.fetchall():
                self.notices.append({'title': title, 'date': date or '', 'url': url or '', 'has_body': bool(content)})
                if content:
                    self.notice_body_count += 1
                text = content or ('通知公告：%s' % title)
                self._add('notice', '学院官网·通知公告', title, text,
                          url=url or '', date=date or '', extra={'doc_id': 'notice:' + (url or title)})

            # 学院简介权威指标：合成一份“官方口径”文档
            cur.execute("SELECT stat_key, label, value, unit, raw_text, source_url FROM api_pspa_stat ORDER BY id")
            rows = cur.fetchall()
            if rows:
                lines = []
                for key, label, value, unit, raw, src in rows:
                    self.stats[key] = float(value) if value is not None else None
                    lines.append('%s：%s %s（原文“%s”）' % (label, _fmt(value), unit or '', raw or ''))
                lines.append('以上数字均摘录自山东大学政治学与公共管理学院官网《学院简介》（/xygk/xyjj.htm），'
                             '是学院自己公布的口径。')
                self._add('profile', '学院官网·学院简介', '学院简介官方口径数据（师资/论文/项目/经费/招生）',
                          '；'.join(lines), url=rows[0][5] or '', extra={'doc_id': 'profile:xyjj'})
                # 派生口径
                keys = ['project_major', 'project_nssf', 'project_nsfc', 'project_ministry']
                self.stats['project_total'] = sum(self.stats.get(k) or 0 for k in keys)
                ek = ['enroll_master', 'enroll_doctor', 'enroll_mpa', 'enroll_intl']
                self.stats['enroll_graduate_total'] = sum(self.stats.get(k) or 0 for k in ek)
        finally:
            cur.close()
            conn.close()

    # ---------- B. 真实采集文件 ----------
    def load_papers(self):
        if config.PAPER_CSV.exists():
            with open(config.PAPER_CSV, encoding='gbk', errors='replace', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = clean(row.get('标题') or '')
                    if not title:
                        continue
                    abstract = clean(row.get('摘要') or '')
                    keywords = clean(row.get('关键词') or '')
                    journal = clean(row.get('原文刊载于') or '')
                    link = clean(row.get('原文链接') or '')
                    text = '论文：%s。关键词：%s。摘要：%s。刊载于：%s。' % (
                        title, keywords or '无', abstract or '无摘要', journal or '未标注')
                    self._add('paper', '官网论文题录(CSV)', title, text,
                              url=link, extra={'doc_id': 'paper:' + title})
                    self.paper_count += 1

        if config.CNKI_CSV.exists():
            with open(config.CNKI_CSV, encoding='gbk', errors='replace', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = clean(row.get('题名') or row.get('标题') or row.get('篇名') or '')
                    if not title:
                        continue
                    author = clean(row.get('作者') or '')
                    source = clean(row.get('来源') or row.get('刊名') or '')
                    text = 'CNKI 收录论文：%s。作者：%s。来源：%s。' % (title, author or '未标注', source or '未标注')
                    self._add('paper', 'CNKI题录(CSV)', title, text, extra={'doc_id': 'cnki:' + title})
                    self.paper_count += 1

    def load_teachers_json(self):
        """教师履历（data/teachers.json：undergraduate/graduate/doctorate 三段求学经历）。

        实况：103 位教师里只有少数填了院校，字段 null 很多——如实入库，不做补全。
        """
        if not config.TEACHERS_JSON.exists():
            return
        try:
            data = json.loads(config.TEACHERS_JSON.read_text(encoding='utf-8'))
        except Exception as exc:
            print('[WARN] teachers.json 解析失败：%s' % exc)
            return
        items = data if isinstance(data, list) else data.get('teachers') or data.get('data') or []
        stage = [('undergraduate', '本科'), ('graduate', '硕士'), ('doctorate', '博士'),
                 ('other institutions', '其他机构')]
        for item in items:
            if not isinstance(item, dict):
                continue
            name = re.sub(r'\s+', '', str(item.get('name') or ''))
            if not name:
                continue
            parts = []
            for key, label in stage:
                v = item.get(key)
                if isinstance(v, dict) and v.get('name'):
                    parts.append('%s：%s' % (label, clean(v['name'])))
            if not parts:
                continue  # 全部为 null，不入库，避免空文档污染检索
            self._add('faculty', '教师履历(teachers.json)', name,
                      '教师履历：%s。%s。' % (name, '；'.join(parts)),
                      extra={'doc_id': 'cv:' + name})

    # ---------- C. 制度文件 ----------
    def load_policies(self):
        for folder in config.POLICY_DIRS:
            if not folder.exists():
                continue
            for path in sorted(Path(folder).glob('*.txt')):
                try:
                    raw = path.read_text(encoding='utf-8')
                except UnicodeDecodeError:
                    raw = path.read_text(encoding='gbk', errors='replace')
                text = clean(raw)
                if len(text) < 50:
                    continue
                title = path.stem
                self._add('policy', '制度文件·%s' % folder.name, title,
                          '%s。%s' % (title, text),
                          extra={'doc_id': 'policy:' + title,
                                 'meta': {'file': str(path)}})

    # ---------- D. 平台自述 ----------
    def load_platform_docs(self):
        for path in config.PLATFORM_DOCS:
            if not path.exists():
                continue
            text = path.read_text(encoding='utf-8', errors='replace')
            self._add('platform', '平台建设文档', path.stem, text,
                      extra={'doc_id': 'platform:' + path.stem})

    def build(self):
        t0 = time.time()
        self.load_official()
        self.load_papers()
        self.load_teachers_json()
        self.load_policies()
        self.load_platform_docs()

        index = BM25Index(self.chunks)
        index.built_at = time.strftime('%Y-%m-%d %H:%M:%S')
        index.save()

        meta = {
            'built_at': index.built_at,
            'chunk_count': len(self.chunks),
            'doc_count': sum(self.counts.values()),
            'by_type': self.counts,
            'stats': self.stats,
            'faculty': self.faculty,
            'notices': self.notices[:500],
            'achievement': {
                'total': sum(self.achievement_cats.values()),
                'by_year': dict(sorted(self.achievement_years.items(), reverse=True)),
                'by_category': dict(self.achievement_cats.most_common()),
                'recent': self.recent_achv,
            },
            'corpus': {
                'papers': self.paper_count,
                'notices': len(self.notices),
                'notices_with_body': self.notice_body_count,
                'teacher_profiles': self.teacher_profile_count,
            },
            'vocab': len(index.postings),
            'elapsed_sec': round(time.time() - t0, 2),
            'sources': {
                'official': 'https://pspa.sdu.edu.cn（教师名录/教师详情/学术成果/通知公告/学院简介）',
                'csv': ['Guanwang_papers_full_sum.csv', 'CNKI_山东大学 政治与公共管理学院.csv', 'teachers.json'],
                'policy': [str(p) for p in config.POLICY_DIRS],
                'platform': [str(p) for p in config.PLATFORM_DOCS],
            },
        }
        config.META_FILE.parent.mkdir(parents=True, exist_ok=True)
        config.META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
        print('=== 知识库构建完成 %.2fs ===' % (time.time() - t0))
        print('  文档 %d 篇 / 分块 %d 个 / 词表 %d' % (len(self.chunks) and meta['doc_count'], len(self.chunks), len(index.postings)))
        for k, v in self.counts.items():
            print('    %-12s %d 篇' % (k, v))
        print('  数据覆盖：教师详情 %d 人 / 论文题录 %d 篇 / 通知正文 %d 篇 / 学术成果 %d 条' % (
            self.teacher_profile_count, self.paper_count, self.notice_body_count,
            meta['achievement']['total']))
        return meta


def _fmt(v):
    if v is None:
        return '未采集到'
    f = float(v)
    return str(int(f)) if f == int(f) else str(f)


def main():
    Builder().build()


if __name__ == '__main__':
    sys.exit(main())
