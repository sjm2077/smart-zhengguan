"""知识库智能体：规划 → 调工具 → 生成（带引用）。

工具（都是本地/只读，不碰任何子系统写接口）：
  1. kb_search(query, type)    BM25 全文检索（知识库）
  2. official_stats(keys)      学院官网《学院简介》官方口径数字
  3. faculty_lookup(name/dept) 官网教师名录
  4. notice_search(keyword)    官网通知公告（标题/日期/链接）

生成策略：
  - 配了大模型（KB_LLM_API_KEY 或 KB_LLM_PROXY）→ 用检索结果生成回答，强制带 [n] 引用；
  - 没配 → 纯检索模式（原文摘录 + 引用），并在回答里明说未接入生成模型。
  任一情况都只依据检索到的资料，资料不足直接说“未检索到”，不编造。
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

import config
from search import BM25Index

STATS_LABELS = {
    'teacher_total': '在职教师',
    'teacher_professor': '教授',
    'teacher_associate': '副教授（副研究员）',
    'teacher_lecturer': '讲师（助理研究员）',
    'teacher_postdoc': '全职博士后',
    'teacher_phd': '具有博士学位',
    'teacher_overseas': '海外名校毕业',
    'supervisor_phd': '博士生导师',
    'supervisor_master': '硕士生导师',
    'paper_total': '近五年发表论文',
    'paper_ssci': 'SSCI 论文',
    'paper_cssci': 'CSSCI 来源期刊论文',
    'book_total': '出版著作',
    'thinktank_report': '智库报告',
    'project_major': '国家社科重大/教育部重大攻关项目',
    'project_nssf': '国家社科基金各类项目',
    'project_nsfc': '国家自然科学基金项目',
    'project_ministry': '其他部委各类项目',
    'project_total': '近五年科研项目合计',
    'fund_total': '近五年科研项目总经费(万元)',
    'enroll_undergrad': '每年招收本科生',
    'enroll_master': '每年招收学术硕士',
    'enroll_doctor': '每年招收博士',
    'enroll_mpa': '每年招收公共管理专业硕士',
    'enroll_intl': '每年招收全英文项目留学生',
    'enroll_graduate_total': '每年招收研究生合计',
}

STAT_INTENT = ('多少', '几', '人数', '数量', '统计', '经费', '项目数', '规模', '比例', '合计', '一共')
# 只有强制度词才额外做制度库过滤检索；“条件/要求/申请”过于宽泛，会误伤通知类问题
POLICY_INTENT = ('规定', '办法', '学籍', '奖助', '奖学金', '评审', '细则', '培养方案', '学籍管理')
NOTICE_INTENT = ('通知', '公告', '招聘', '申报', '截止', '报名', '公示', '启事')
PLATFORM_INTENT = ('平台', '大屏', '系统架构', '我们做', '项目汇报', '数据中台', '知识库怎么')
ACHV_INTENT = ('学术成果', '成果', '著作', '获奖')
ACHV_STAT_INTENT = ('多少', '几', '每年', '年度', '分布', '统计', '数量', '趋势', '合计')


class KB:
    def __init__(self, index: BM25Index, meta: dict):
        self.index = index
        self.meta = meta

    # ---------------- 工具 ----------------
    def kb_search(self, query, topk=5, doc_type='', exclude_types=None):
        # 同一篇文档可能被切成多块，检索后按「标题+来源」合并，只保留最高分那块
        hits = self.index.search(query, topk=topk * 4, doc_type=doc_type)
        out, seen = [], set()
        for h in hits:
            if exclude_types and h['type'] in exclude_types:
                continue
            # 覆盖率太低说明只是“沾了个词”，不是真相关：宁可说没检索到，也不拿不相干内容凑数
            if h.get('coverage', 1.0) < config.MIN_COVERAGE:
                continue
            key = (h['title'], h['source'])
            if key in seen:
                continue
            seen.add(key)
            out.append({
                'title': h['title'], 'type': h['type'], 'source': h['source'],
                'date': h.get('date', ''), 'url': h.get('url', ''),
                'text': h['text'][:400], 'score': h.get('score', 0),
                'coverage': h.get('coverage', 0),
            })
            if len(out) >= topk:
                break
        return out

    def official_stats(self, keys=None):
        stats = self.meta.get('stats') or {}
        if keys:
            return {k: stats.get(k) for k in keys if k in stats}
        return stats

    def achievement_stats(self):
        """官网学术成果按年/按类别的真实计数（来自爬虫落库的 400 条记录）。"""
        achv = self.meta.get('achievement') or {}
        return {
            'total': achv.get('total', 0),
            'by_year': achv.get('by_year', {}),
            'by_category': achv.get('by_category', {}),
            'recent': achv.get('recent', [])[:6],
            'papers_csv': (self.meta.get('corpus') or {}).get('papers', 0),
        }

    def faculty_lookup(self, name=None, dept=None, title=None, limit=20):
        rows = self.meta.get('faculty') or []
        out = []
        for r in rows:
            if name and name not in r['name']:
                continue
            if dept and dept not in r['dept']:
                continue
            if title and title not in r['title']:
                continue
            out.append(r)
            if len(out) >= limit:
                break
        return out

    def notice_search(self, keyword='', limit=5):
        rows = self.meta.get('notices') or []
        if not keyword:
            return rows[:limit]
        matched = [r for r in rows if keyword in r['title']]
        return matched[:limit] if matched else self.kb_search(keyword, topk=limit, doc_type='notice')

    # ---------------- 规划 ----------------
    def plan(self, question):
        """按意图选工具：有精确意图就用精确工具，没有才用通用检索兜底。

        这样做的原因：通用检索在“问某位老师研究方向”或“官网成果每年多少”这类问题上
        会把招生简章、通知里的同名字段一起召回，反而盖住正确答案。精确意图命中时，
        只跑对应的类型检索；意图不明时再用通用检索 + 覆盖率门槛兜住。
        """
        q = question or ''
        names = [f['name'] for f in (self.meta.get('faculty') or []) if len(f['name']) >= 2]
        hit_names = [n for n in names if n in q]
        is_platform = any(k in q for k in PLATFORM_INTENT)
        asks_research = any(k in q for k in ('研究方向', '研究领域', '研究什么', '做什么研究',
                                             '简介', '哪方面', '什么方向'))
        asks_achv = any(k in q for k in ACHV_INTENT)

        general = {'query': q}
        if not is_platform:
            # 平台建设文档只在问“平台/大屏/架构”时参与检索，避免污染业务问题
            general['exclude_types'] = ['platform']

        if hit_names and asks_research:
            # “某老师研究什么方向”：教师详情页正文才是答案，别让通知/招生简章混进来
            tools = [('kb', {'query': hit_names[0], 'doc_type': 'faculty'}),
                     ('faculty', {'name': hit_names[0]})]
        else:
            tools = []
            if not asks_achv:
                tools.append(('kb', general))
            if hit_names:
                tools.append(('faculty', {'name': hit_names[0]}))
            if any(k in q for k in STAT_INTENT) or re.search(r'\d', q):
                tools.append(('stats', {}))
            if asks_achv:
                tools.append(('kb', {'query': q, 'doc_type': 'achievement'}))
                if any(k in q for k in ACHV_STAT_INTENT):
                    tools.append(('achv', {}))
            if any(k in q for k in POLICY_INTENT):
                tools.insert(1, ('kb', {'query': q, 'doc_type': 'policy'}))
            if any(k in q for k in NOTICE_INTENT) or '最新' in q:
                tools.append(('notice', {'keyword': ''}))
            if is_platform:
                tools.insert(1, ('kb', {'query': q, 'doc_type': 'platform'}))

        uniq, seen = [], set()
        for name, args in tools:
            key = (name, json.dumps(args, sort_keys=True, ensure_ascii=False))
            if key in seen:
                continue
            seen.add(key)
            uniq.append((name, args))
        return uniq, hit_names

    def run_tools(self, plan):
        priority = {'stats': 0, 'achv': 1, 'faculty': 2, 'notice': 3, 'kb': 4}
        results = []
        for name, args in sorted(plan, key=lambda x: priority.get(x[0], 9)):
            if name == 'kb':
                results.append(('kb', args, self.kb_search(args['query'], topk=config.TOP_K,
                                                          doc_type=args.get('doc_type', ''),
                                                          exclude_types=args.get('exclude_types'))))
            elif name == 'stats':
                results.append(('stats', args, self.official_stats()))
            elif name == 'achv':
                results.append(('achv', args, self.achievement_stats()))
            elif name == 'faculty':
                results.append(('faculty', args, self.faculty_lookup(**args)))
            elif name == 'notice':
                results.append(('notice', args, self.notice_search(args.get('keyword', ''), limit=5)))
        return results

    # ---------------- 组装上下文 ----------------
    def build_context(self, tool_results):
        """把各工具结果拼成带编号的上下文；同时生成可点击的引用列表。

        编号规则：[1][2]… 统一编号，知识库命中、教师名录、通知公告都进引用，
        这样界面上每个结论都能点回原始出处。
        """
        citations = []
        blocks = []
        max_cites = 8

        def add_cite(title, source, doc_type, date='', url='', snippet=''):
            # 同一篇资料可能被不同工具重复命中（如教师工具 + 教师检索），按「来源+链接」去重
            key = (source, url or title)
            for i, c in enumerate(citations, 1):
                if (c['source'], c['url'] or c['title']) == key:
                    return i
            if len(citations) >= max_cites:
                return None
            citations.append({
                'title': title, 'source': source, 'type': doc_type,
                'date': date or '', 'url': url or '', 'snippet': (snippet or '')[:180],
            })
            return len(citations)

        for name, args, data in tool_results:
            if name == 'kb':
                lines = ['【知识库检索结果】']
                for item in data:
                    no = add_cite(item['title'], item['source'], item['type'],
                                  item.get('date', ''), item.get('url', ''), item['text'])
                    if no is None:
                        break
                    lines.append('[%d] 《%s》（%s%s）\n%s' % (
                        no, item['title'], item['source'],
                        ('，' + item['date']) if item.get('date') else '', item['text']))
                if len(lines) > 1:
                    blocks.append('\n'.join(lines))
            elif name == 'stats':
                lines = ['【学院官网《学院简介》官方口径】']
                add_cite('山东大学政治学与公共管理学院·学院简介', '学院官网·学院简介', 'profile',
                         url='https://pspa.sdu.edu.cn/xygk/xyjj.htm',
                         snippet='官网《学院简介》公布的师资、科研、招生数字')
                for k, v in data.items():
                    if v is None:
                        continue
                    lines.append('- %s：%s' % (STATS_LABELS.get(k, k), _num(v)))
                blocks.append('\n'.join(lines))
            elif name == 'achv':
                lines = ['【官网学术成果统计（爬虫落库记录直接计数）】']
                no = add_cite('学院官网·学术成果列表', '学院官网·学术成果', 'achievement',
                              url='https://pspa.sdu.edu.cn/xsky/xscg.htm',
                              snippet='官网学术成果栏目 /xsky/xscg.htm 的爬虫落库记录')
                lines.append('- 学术成果列表总数：%d 条%s' % (data.get('total', 0),
                                                          (' [%d]' % no) if no else ''))
                by_year = data.get('by_year') or {}
                if by_year:
                    lines.append('- 按年份：' + '、'.join(
                        '%s 年 %d 条' % (y, n) for y, n in by_year.items() if y))
                by_cat = data.get('by_category') or {}
                if by_cat:
                    lines.append('- 按类别：' + '、'.join(
                        '%s %d 条' % (c, n) for c, n in list(by_cat.items())[:6]))
                for it in (data.get('recent') or [])[:5]:
                    item_no = add_cite(it['title'], '学院官网·学术成果', 'achievement',
                                       it.get('date', ''), it.get('url', ''),
                                       '%s｜%s' % (it.get('category', ''), it.get('date', '')))
                    tag = ('[%d] ' % item_no) if item_no else ''
                    lines.append('- %s%s（%s，%s）' % (tag, it['title'], it.get('category', '未分类'),
                                                      it.get('date', '未标注')))
                if data.get('papers_csv'):
                    lines.append('- 另有官网论文题录 %d 篇（题录 CSV，与上面的成果列表不是同一口径）'
                                 % data['papers_csv'])
                blocks.append('\n'.join(lines))
            elif name == 'faculty':
                lines = ['【官网教师名录】']
                for f in data:
                    no = add_cite(f['name'], '学院官网·教师名录', 'faculty', '', f.get('url', ''),
                                  '%s，%s' % (f['dept'] or '学院', f['title'] or '职称未标注'))
                    tag = ('[%d] ' % no) if no else ''
                    research = ('，研究方向：' + f['research']) if f.get('research') else ''
                    lines.append('- %s%s，%s，%s%s%s' % (tag, f['name'], f['dept'] or '学院',
                                                        f['title'] or '职称未标注', research,
                                                        ('，主页 ' + f['url']) if f.get('url') else ''))
                if len(lines) > 1:
                    blocks.append('\n'.join(lines))
            elif name == 'notice':
                lines = ['【官网通知公告】']
                for n in data:
                    no = add_cite(n['title'], '学院官网·通知公告', 'notice',
                                  n.get('date', ''), n.get('url', ''), n['title'])
                    tag = ('[%d] ' % no) if no else ''
                    lines.append('- %s%s（%s）%s' % (tag, n['title'], n.get('date') or '日期未标注',
                                                     (' ' + n['url']) if n.get('url') else ''))
                if len(lines) > 1:
                    blocks.append('\n'.join(lines))
        return '\n\n'.join(blocks), citations

    # ---------------- 生成 ----------------
    def answer(self, question):
        plan, hit_names = self.plan(question)
        tool_results = self.run_tools(plan)
        context, citations = self.build_context(tool_results)
        tools_used = [name for name, _a, _d in tool_results]

        has_material = bool(citations) or any(d for n, _a, d in tool_results if n != 'kb')
        if not has_material:
            return {
                'answer': '知识库中没有检索到与该问题相关的资料。'
                          '目前已收录：学院官网教师名录、学术成果、通知公告、学院简介官方口径、'
                          '官网论文题录、学校研究生制度文件。可以换个关键词，或指明是「通知/制度/教师/统计」哪一类。',
                'citations': [], 'tools_used': tools_used, 'mode': 'retrieval',
            }

        llm_answer = self._call_llm(question, context)
        if llm_answer:
            llm_answer = strip_markdown(llm_answer)
            # 模型偶尔会把资料外的内容也写进来，用末尾的“引用”段提醒用户核对原文
            if citations and not re.search(r'\[\d+\]', llm_answer):
                llm_answer += '\n\n（依据以下资料）'
            return {'answer': llm_answer, 'citations': citations,
                    'tools_used': tools_used, 'mode': 'llm'}

        return {'answer': self._fallback_answer(question, tool_results, citations),
                'citations': citations, 'tools_used': tools_used, 'mode': 'retrieval'}

    def _fallback_answer(self, question, tool_results, citations):
        parts = ['（当前未配置大模型 Key，以下为知识库原文摘录，不做生成式改写）', '']
        for name, _args, data in tool_results:
            if name == 'stats':
                parts.append('官网《学院简介》可得数字：')
                for k, v in data.items():
                    if v is None:
                        continue
                    parts.append('- %s：%s' % (STATS_LABELS.get(k, k), _num(v)))
                parts.append('')
            elif name == 'faculty':
                parts.append('官网教师名录命中 %d 人：' % len(data))
                for f in data[:8]:
                    research = ('，研究方向：' + f['research']) if f.get('research') else ''
                    parts.append('- %s（%s，%s%s）' % (f['name'], f['dept'] or '学院',
                                                      f['title'] or '未标注', research))
                parts.append('')
            elif name == 'achv':
                parts.append('官网学术成果统计（爬虫落库，直接计数）：')
                parts.append('- 总数：%d 条' % data.get('total', 0))
                for y, n in (data.get('by_year') or {}).items():
                    parts.append('- %s 年：%d 条' % (y, n))
                for c, n in list((data.get('by_category') or {}).items())[:6]:
                    parts.append('- 类别「%s」：%d 条' % (c, n))
                for it in (data.get('recent') or [])[:4]:
                    parts.append('- 最近收录：%s（%s，%s）' % (it['title'], it.get('category', ''),
                                                          it.get('date', '未标注')))
                if data.get('papers_csv'):
                    parts.append('- 另有官网论文题录 %d 篇（题录 CSV，口径不同）' % data['papers_csv'])
                parts.append('')
            elif name == 'notice':
                parts.append('官网通知公告（最近 %d 条）：' % len(data))
                for n in data:
                    parts.append('- %s（%s）' % (n['title'], n.get('date') or '日期未标注'))
                parts.append('')
            elif name == 'kb':
                parts.append('知识库最相关的原文：')
                for i, item in enumerate(data[:5], 1):
                    parts.append('%d. 《%s》%s' % (i, item['title'], item['text'][:240]))
                parts.append('')
        if citations:
            parts.append('引用：')
            for i, c in enumerate(citations[:5], 1):
                tail = (' ' + c['url']) if c.get('url') else ''
                parts.append('[%d] 《%s》（%s）%s' % (i, c['title'], c['source'], tail))
        return '\n'.join(parts).strip()

    def _call_llm(self, question, context):
        system = (
            '你是山东大学政治学与公共管理学院“智慧政管平台”的知识库助手。'
            '只能依据下面【资料】回答，资料里没有的就说“知识库未收录”，绝不编造数字或制度条款。'
            '要求：1) 先直接给出结论，再用 1. 2. 3. 分点展开，不要用 Markdown 的 # 和 **；'
            '2) 每个结论后面用 [1][2] 标注资料编号，编号必须来自【资料】；'
            '3) 资料里已有的数字要照实写出来，不要因为“不是官方口径”就回答未收录，'
            '区分即可：官网《学院简介》是官方口径，爬虫落库/子系统数据要标明来源差别；'
            '4) 只有资料完全没有对应内容时才说“知识库未收录该信息”，不要用常识补齐。'
        )
        user = '【资料】\n%s\n\n【问题】%s' % (context, question)

        if config.LLM_PROXY:
            return self._post(config.LLM_PROXY, {'system_prompt': system, 'message': user}, 'proxy')
        if config.LLM_API_KEY:
            url = config.LLM_BASE_URL.rstrip('/') + '/chat/completions'
            body = {
                'model': config.LLM_MODEL,
                'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
                'temperature': 0.2,
                'stream': False,
            }
            return self._post(url, body, 'direct', api_key=config.LLM_API_KEY)
        return ''

    def _post(self, url, body, mode, api_key=''):
        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = 'Bearer ' + api_key
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'),
                                         headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=config.LLM_TIMEOUT) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            if mode == 'proxy':
                return (data.get('reply') or data.get('content') or data.get('answer') or '').strip()
            return (data['choices'][0]['message']['content'] or '').strip()
        except Exception as exc:
            print('[WARN] 大模型调用失败，降级为检索模式：%s' % exc)
            return ''


def strip_markdown(text):
    """去掉大模型爱加的 Markdown 装饰，前端按纯文本渲染。"""
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)      # **加粗**
    text = re.sub(r'(?m)^#{1,6}\s*', '', text)        # # 标题
    text = re.sub(r'`([^`]*)`', r'\1', text)          # `代码`
    text = re.sub(r'(?m)^\s*[-*]\s+', '', text)       # - 列表（保留数字列表）
    return text.strip()


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return str(int(f)) if f == int(f) else ('%.2f' % f)
