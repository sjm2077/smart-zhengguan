"""知识库自测：跑一组典型问题，检查检索命中、引用、工具调用是否符合预期。

用法：
  python kb_service/selftest.py           # 全部用例（默认强制纯检索，结果稳定可复现）
  python kb_service/selftest.py -v        # 打印完整回答
  python kb_service/selftest.py --llm     # 走大模型生成（需后端代理在线）
退出码 0 表示全部通过（每个用例都至少命中 1 条引用，且未出现空检索）。
"""
from __future__ import annotations

import os
import sys

# 默认屏蔽大模型：自测要验证的是“检索准不准 + 引用有没有”，
# 而生成结果每次措辞不同，会让用例时好时坏。需要验证生成质量时加 --llm。
if '--llm' not in sys.argv:
    os.environ['KB_LLM_PROXY'] = ''
    os.environ['KB_LLM_API_KEY'] = ''

import config
from agent import KB
from search import BM25Index

CASES = [
    # (问题, 期望标题/正文包含的关键词, 期望调用的工具)
    ('学院有多少在职教师？', '教师', ('stats',)),
    ('学院近五年科研经费多少？', '6000', ('stats',)),
    ('学院官网学术成果每年有多少条？', '学术成果', ('achv',)),
    ('博士后招收条件是什么？', '博士后', ('kb',)),
    ('研究生奖学金评审办法有哪些规定？', '奖学金', ('kb',)),
    ('研究生学籍管理有哪些规定？', '学籍', ('kb',)),
    ('最新通知有哪些？', '通知', ('notice',)),
    ('学院近五年有哪些国家社科项目？', '社科', ('kb',)),
    ('学院在气候治理方面有哪些论文？', '气候', ('kb',)),
    ('我们平台的大屏是怎么做的？', '大屏', ('kb',)),
    # 负向用例：知识库里没有的主题，必须明确说“未检索到”，不许编
    ('火星殖民计划的氧气循环方案是什么？', '__NONE__', ()),
]


def main():
    verbose = '-v' in sys.argv
    index = BM25Index.load()
    if index is None:
        print('[FAIL] 索引不存在，先运行：python kb_service/ingest.py')
        return 1
    import json
    meta = json.loads(config.META_FILE.read_text(encoding='utf-8'))
    kb = KB(index, meta)

    print('索引：分块 %d，词表 %d，构建于 %s\n' % (len(index.chunks), len(index.postings), index.built_at))

    # 教师姓名类问题：从官网名录里取一个真实姓名，避免用“李老师”这种不存在的称谓
    faculty = meta.get('faculty') or []
    cases = list(CASES)
    if faculty:
        real = faculty[0]['name']
        cases.insert(0, ('%s是什么职称？' % real, real, ('faculty',)))
    # 研究方向类问题：取一位确实采到详情页研究方向的教师
    with_research = [f for f in faculty if f.get('research')]
    if with_research:
        f = with_research[0]
        cases.insert(1, ('%s老师的研究方向是什么？' % f['name'], f['research'][:6], ('faculty',)))

    passed = 0
    for i, (question, expect, expect_tools) in enumerate(cases, 1):
        result = kb.answer(question)
        answer = result['answer']
        citations = result['citations']
        tools = result['tools_used']

        # “检索命中”按工具返回的原文判断，而不是按措辞判断：
        # 纯检索模式下回答只摘录片段，关键词可能落在没被摘出来的那一句里
        plan, _names = kb.plan(question)
        retrieved = []
        for name, _args, data in kb.run_tools(plan):
            if name == 'kb':
                retrieved += ['%s %s' % (d['title'], d['text']) for d in data]
            elif name == 'faculty':
                retrieved += ['%s %s %s' % (d['name'], d['dept'], d.get('research', '')) for d in data]
            elif name == 'notice':
                retrieved += [d['title'] for d in data]
            elif name in ('stats', 'achv'):
                retrieved.append(json.dumps(data, ensure_ascii=False))
        retrieved_text = ' '.join(retrieved)

        if expect == '__NONE__':
            # 负向用例：允许工具返回空，但答案必须说未检索到，且不能编造引用
            ok = '没有检索到' in answer and not citations
        else:
            hit_keyword = (expect in answer or expect in retrieved_text
                           or expect in ' '.join(c['title'] for c in citations))
            hit_tools = all(t in tools for t in expect_tools)
            ok = bool(citations) and hit_keyword and hit_tools and '没有检索到' not in answer
        passed += 1 if ok else 0
        print('%d. [%s] %s' % (i, 'PASS' if ok else 'FAIL', question))
        print('   工具=%s 引用=%d 关键词=%s' % (','.join(tools), len(citations), expect))
        if citations:
            print('   首条引用：《%s》（%s）' % (citations[0]['title'], citations[0]['source']))
        if verbose:
            print('   ---- 回答 ----')
            print('\n'.join('   ' + line for line in answer.splitlines()[:20]))
        print()

    print('通过 %d/%d' % (passed, len(cases)))
    return 0 if passed == len(cases) else 2


if __name__ == '__main__':
    sys.exit(main())
