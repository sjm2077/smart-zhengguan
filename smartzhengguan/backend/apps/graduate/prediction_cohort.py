"""群体干预查询：从实测快照排序，不用当前个人画像代替全体学生。"""
import re


def is_cohort_question(question, history=None):
    text = str(question or '').strip()
    population = re.search(r'哪些|哪几|谁|名单|排名|排行|[Tt][Oo][Pp]\s*\d+|所有学生|全体学生|最需要|找出|全院', text)
    topic = re.search(r'干预|风险|预警|关注|跟进|逾期|沟通|培养', text)
    if population and topic:
        return True
    # 仅承接明确的群体范围追问，避免把“他为什么高风险”继续当群体问题。
    if re.search(r'^(那|只看|换成|改为|其中|再看)', text) and re.search(r'20\d{2}|专业|硕士|博士|前\d+', text):
        return any(is_cohort_question(item.get('content') or item.get('text', ''))
                   for item in (history or [])[-4:] if item.get('role') == 'user')
    return False


def build_cohort_chat(question, history=None):
    from . import services as s

    original_question = question
    snapshots = [item for item in s.build_prediction_sources()
                 if not getattr(item, 'is_virtual', False)
                 and item.student.name.strip()
                 and item.student.name.strip() != item.student.student_id
                 and not re.fullmatch(r'学生\d+', item.student.name.strip())]
    scope = []
    if re.search(r'^(那|只看|换成|改为|其中|再看)', question) and not re.search(r'全部|全院|所有|全体', question):
        previous = next((item.get('content') or item.get('text', '')
                         for item in reversed(history or [])
                         if item.get('role') == 'user' and is_cohort_question(item.get('content') or item.get('text', ''))), '')
        # 本轮明确说出的范围优先；不携带左侧个人筛选。
        if not re.search(r'20\d{2}', question):
            match = re.search(r'20\d{2}级?', previous)
            if match:
                question += ' ' + match.group()
        majors = {item.student.major for item in snapshots if item.student.major}
        if not any(major in question for major in majors):
            question += ' ' + ' '.join(major for major in majors if major in previous)
        if not any(degree in question for degree in ('学术型硕士', '专业型硕士', '博士')):
            question += ' ' + ' '.join(degree for degree in ('学术型硕士', '专业型硕士', '博士') if degree in previous)
    year = re.search(r'(20\d{2})\s*(?:级|年级)?', question)
    if year:
        scope.append(year.group(1) + '级')
        snapshots = [item for item in snapshots if year.group(1) in item.student.grade]
    majors = {item.student.major for item in snapshots if item.student.major}
    requested = [major for major in majors if major in question]
    if requested:
        scope.extend(sorted(requested))
        snapshots = [item for item in snapshots if item.student.major in requested]
    degrees = [label for label in ('学术型硕士', '专业型硕士', '博士') if label in question]
    if degrees:
        scope.extend(degrees)
        snapshots = [item for item in snapshots if s.degree_type_display(item.student.degree_type) in degrees]
    scope_label = ' · '.join(scope) if scope else '全部年级 · 全部专业 · 全部学位类型'
    rows = []
    severity = {'high': 3, 'alert': 2, 'medium': 1, 'low': 0}
    metric = 'communication' if '沟通' in question else 'overdue' if '逾期' in question else 'training' if '培养' in question else 'risk'
    for item in snapshots:
        data = s.serialize_prediction_current_snapshot(item)
        factors = s.prediction_build_factor_breakdown(data, s.prediction_compute_radar(data))
        risk = s.prediction_build_risk_profile(factors, item)
        overdue = int(data.get('overdueTasksCount') or 0)
        meetings = int(data.get('advisorMeetingCount60d') or 0)
        training = float(data.get('trainingPlanCompletionRate') or 0)
        hits = int(overdue > 0) + int(meetings < 2) + int(training < 100)
        level = severity.get(item.risk_level, 0)
        if metric == 'overdue' and overdue <= 0 or metric == 'communication' and meetings >= 2 or metric == 'training' and training >= 100:
            continue
        if metric == 'risk' and not level and not hits:
            continue
        row = {**s.serialize_prediction_student(item), **risk,
               'riskLevel': s.risk_level_display(item.risk_level),
               'overdueTasksCount': overdue, 'advisorMeetingCount60d': meetings,
               'trainingPlanCompletionRate': training}
        primary = {'risk': level, 'overdue': overdue, 'communication': -meetings, 'training': -training}[metric]
        rows.append(((primary, risk['riskScore'], hits), row))
    rows.sort(key=lambda entry: (-entry[0][0], -entry[0][1], -entry[0][2], entry[1]['studentId']))
    count_match = re.search(r'(?:[Tt][Oo][Pp]\s*|前\s*)(\d+)', question)
    limit = min(20, max(1, int(count_match.group(1)))) if count_match else 5
    selected = [row for _, row in rows[:limit]]
    rules = {'risk': '风险等级（高风险、预警、关注、正常）优先，其次按风险分、命中风险项数降序',
             'overdue': '任务逾期次数降序，其次按风险分降序',
             'communication': '近60天导师沟通次数升序，其次按风险分降序',
             'training': '培养计划完成率升序，其次按风险分降序'}
    lines = [f'统计范围：本学院，{scope_label}；共 {len(snapshots)} 名有实测快照的学生。',
             f'排序口径：{rules[metric]}。未使用左侧选中学生作为群体答案。']
    if selected:
        lines.append(f'建议优先核实以下 {len(selected)} 位同学（符合当前风险条件共 {len(rows)} 人）：')
        for index, row in enumerate(selected, 1):
            lines.append(f"{index}. {row['name']}（{row['grade']} · {row['major']} · {row['degreeType']}）："
                         f"{row['riskLevel']}，风险分 {row['riskScore']}；任务逾期 {row['overdueTasksCount']} 次，"
                         f"近60天导师沟通 {row['advisorMeetingCount60d']} 次，培养计划完成率 {row['trainingPlanCompletionRate']:g}%。"
                         f"跟进建议：{row['suggestion']}。")
    else:
        lines.append('当前范围内没有符合条件的学生。')
    return {
        'studentId': None, 'question': original_question,
        'scope': {'type': 'cohort', 'label': scope_label, 'studentCount': len(snapshots)},
        'students': selected,
        'answer': {'directAnswer': '\n\n'.join(lines),
                   'reasoning': ['仅统计每位学生最新的实测快照，排除无快照的推算样本。',
                                 '这是基于现有指标的筛查顺序，需核实记录与培养阶段后决定干预措施。'],
                   'actionPlan': ['逐一核实异常指标，与导师和学生确认原因，再约定跟进动作与复核时间。'],
                   'citations': []},
        'capabilities': s.prediction_ai_capabilities(),
        'trace': {'generationMode': 'cohort_ranking', 'llmUsed': False, 'promptRoute': 'cohort_ranking'},
    }
