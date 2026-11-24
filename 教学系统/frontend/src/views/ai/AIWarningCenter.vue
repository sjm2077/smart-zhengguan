<template>
  <div class="ai-center" id="module-ai-warning-center">
    <header class="ai-header">
      <div>
        <div class="ai-eyebrow"><span class="ai-accent"></span> 教学管理 / 智能分析</div>
        <h1>智能分析与预警中心</h1>
        <p>教务咨询 · 数据分析 · 风险核查 · 演示预测</p>
      </div>
      <div class="ai-header-actions">
        <span class="ai-term">{{ overview?.semester?.name || (loadError ? '后端数据未就绪' : '当前学期尚未关联') }}</span>
        <button type="button" class="ai-btn ai-btn-ghost" :disabled="loading" @click="refreshAll">刷新数据</button>
      </div>
    </header>

    <div class="ai-banner" role="status">
      <span class="ai-indicator" :class="overview?.ai.enabled ? 'is-on' : 'is-off'"></span>
      <span v-if="loading">正在从教务数据库读取统计与风险检查结果…</span>
      <span v-else-if="loadError">{{ loadError }}</span>
      <span v-else-if="overview?.ai.enabled">DeepSeek 已在服务器侧配置；问答使用脱敏的聚合数据，实际风险由业务规则判定。</span>
      <span v-else>DeepSeek 尚未配置。基础教务数据查询、站内导航、规则预警仍可使用；</span>
    </div>

    <div v-if="overview?.demo_data" class="ai-history-info" role="status"><strong>演示数据环境：</strong>含合成历史记录或人工生成的考核日期，仅供功能展示，不代表真实教学历史或预测效果。</div>

    <div class="ai-kpis">
      <article class="ai-kpi"><span>本学期课程</span><strong>{{ fmt(overview?.summary.courses) }}</strong><small>按教务数据库课程关联统计</small></article>
      <article class="ai-kpi"><span>本学期考试</span><strong>{{ fmt(overview?.summary.exams) }}</strong><small>本学期登记场次</small></article>
      <article class="ai-kpi"><span>规则命中事项</span><strong>{{ fmt(overview?.rule_total) }}</strong><small>{{ overview?.rules_complete ? '完整检测的命中数' : '仅已扫描范围的命中数' }}</small></article>
      <article class="ai-kpi"><span>待核查及处理中</span><strong>{{ fmt(overview ? overview.case_counts.pending + overview.case_counts.in_progress : undefined) }}</strong><small>已建立的持久化处理记录</small></article>
    </div>

    <nav id="ai-module-nav" class="ai-section-nav" aria-label="智能分析模块导航">
      <button type="button" @click="jumpTo('ai-chat-zone')"><span>01</span>智能问答</button>
      <button type="button" @click="jumpTo('ai-grade-zone')"><span>02</span>学业成绩</button>
      <button type="button" @click="jumpTo('ai-operations-zone')"><span>03</span>教学运行</button>
      <button type="button" @click="jumpTo('ai-risk-zone')"><span>04</span>风险核查与处置</button>
      <button type="button" @click="jumpTo('ai-history-zone')"><span>05</span>历史趋势</button>
      <button type="button" @click="jumpTo('ai-replay-zone')"><span>06</span>预测与研判</button>
    </nav>
    <div class="ai-zone" id="ai-chat-zone">
      <div class="ai-zone-heading"><span class="ai-zone-number">01</span><div><h2>智能问答</h2><p>教务咨询与业务导航</p></div><button type="button" class="ai-zone-return" @click="jumpTo('ai-module-nav')">返回导航 ↑</button></div>
      <section class="ai-panel ai-chat-panel" aria-labelledby="ai-chat-title">
        <div class="ai-panel-head">
          <div><h2 id="ai-chat-title">教务咨询与导航</h2><p>根据教务登记数据回答问题</p></div>
          <span class="ai-tag">{{ overview?.ai.enabled ? 'DeepSeek + 数据查询' : '基础数据查询' }}</span>
        </div>
        <div class="ai-prompts">
          <button v-for="prompt in examplePrompts" :key="prompt" class="ai-prompt" type="button" :disabled="sending" @click="sendQuestion(prompt)">{{ prompt }}</button>
        </div>
        <div class="ai-conversation" ref="chatScrollRef" aria-live="polite">
          <div v-if="!messages.length" class="ai-chat-empty">
            <div class="ai-chat-symbol">?</div>
            <h3>可直接询问本学期教学情况</h3>
            <p>例如：“第18周安排了多少场考试？”或“打开成绩管理”。回答会附带可靠的来源说明与页面入口。</p>
          </div>
          <div v-for="m in messages" :key="m.id" class="ai-message" :class="m.role === 'user' ? 'ai-message-user' : 'ai-message-assistant'">
            <span class="ai-message-avatar">{{ m.role === 'user' ? '我' : '智' }}</span>
            <div class="ai-bubble">
              <div v-if="m.role === 'assistant' && m.mode === 'deepseek'" class="ai-message-content ai-rich-answer">
                <template v-for="(block, bi) in formatAnswer(m.content)" :key="bi">
                  <component v-if="block.kind === 'heading' || block.kind === 'paragraph'" :is="block.kind === 'heading' ? 'h3' : 'p'">
                    <template v-for="(part, pi) in block.parts" :key="pi"><strong v-if="part.bold">{{ part.text }}</strong><span v-else>{{ part.text }}</span></template>
                  </component>
                  <component v-else :is="block.kind === 'ordered' ? 'ol' : 'ul'" :start="block.kind === 'ordered' ? block.start : undefined">
                    <li v-for="(item, ii) in block.items" :key="ii"><template v-for="(part, pi) in item" :key="pi"><strong v-if="part.bold">{{ part.text }}</strong><span v-else>{{ part.text }}</span></template></li>
                  </component>
                </template>
              </div>
              <div v-else class="ai-message-content">{{ m.content }}</div>
              <div v-if="m.role === 'assistant'" class="ai-message-meta">
                <span>{{ modeLabel(m.mode) }}</span><span v-if="m.sources?.length">数据来源：{{ m.sources.map(sourceLabel).join('、') }}</span>
              </div>
              <div v-if="m.actions?.length" class="ai-answer-actions">
                <button v-for="action in m.actions" :key="action.path" type="button" class="ai-inline-link" @click="navigate(action.path)">{{ action.label }} <span>›</span></button>
              </div>
            </div>
          </div>
          <div v-if="sending" class="ai-chat-working">正在查询教务数据并整理回答…</div>
        </div>
        <form class="ai-chat-form" @submit.prevent="sendQuestion()">
          <textarea v-model="question" :disabled="sending" maxlength="500" rows="2" placeholder="输入教务问题，例如：本学期有什么考试安排异常？" @keydown.ctrl.enter.prevent="sendQuestion()"></textarea>
          <div class="ai-chat-footer"><span>仅提供辅助分析，不代替正式教务审核。Ctrl + Enter 发送</span><button class="ai-btn ai-btn-primary" :disabled="sending || !question.trim()" type="submit">{{ sending ? '查询中' : '发送问题' }}</button></div>
        </form>
      </section>
    </div>
    <div class="ai-zone" id="ai-grade-zone">
      <div class="ai-zone-heading"><span class="ai-zone-number">02</span><div><h2>学业成绩</h2><p>成绩分布与课程比较</p></div><button type="button" class="ai-zone-return" @click="jumpTo('ai-module-nav')">返回导航 ↑</button></div>
      <section class="ai-panel" id="ai-grade-section">
        <div class="ai-panel-head"><div><h2>本学期成绩概览</h2></div><button class="ai-inline-link" @click="navigate('/grade')">进入成绩管理 ›</button></div>
        <div class="ai-mini-metrics">
          <div><span>已发布成绩记录</span><strong>{{ fmt(overview?.summary.published_grades) }}</strong></div>
          <div><span>涉及学生</span><strong>{{ fmt(overview?.summary.graded_students) }}</strong></div>
          <div><span>有效记录平均分</span><strong>{{ overview?.analyses.grade.average_score == null ? '—' : overview.analyses.grade.average_score }}</strong></div>
        </div>
        <p class="ai-explanation">{{ overview?.analyses.grade.explanation || '等待读取已发布成绩数据。' }}</p>
        <template v-if="gradeStats && gradeStats.records > 0">
          <div class="ai-grade-metrics">
            <div><span>记录及格率</span><strong>{{ pct(gradeStats.pass_rate) }}</strong><small>≥60分 · {{ fmt(gradeStats.pass_count) }} 条</small></div>
            <div><span>低于60分记录占比</span><strong>{{ pct(gradeStats.below_pass_rate) }}</strong><small>{{ fmt(gradeStats.below_pass_count) }} 条</small></div>
            <div><span>记录优秀率</span><strong>{{ pct(gradeStats.excellent_rate) }}</strong><small>≥90分 · {{ fmt(gradeStats.excellent_count) }} 条</small></div>
            <div><span>成绩中位数</span><strong>{{ fmt(gradeStats.median_score) }}</strong><small>分</small></div>
            <div><span>成绩标准差</span><strong>{{ fmt(gradeStats.std_score) }}</strong><small>总体标准差 · 分</small></div>
            <div><span>有效成绩记录</span><strong>{{ fmt(gradeStats.records) }}</strong><small>排除 {{ fmt(gradeStats.excluded_records) }} 条</small></div>
          </div>
          <div class="ai-chart-block ai-grade-dist">
            <div class="ai-chart-heading"><strong>已发布成绩分数段分布</strong><span>有效百分制记录 · {{ fmt(gradeStats.records) }} 条</span></div>
            <div v-for="band in gradeStats.distribution" :key="band.label" class="ai-grade-band">
              <span>{{ band.label }}</span><div class="ai-grade-track"><div :style="{ width: pct(band.rate) }"></div></div><b>{{ fmt(band.count) }} 条</b><small>{{ pct(band.rate) }}</small>
            </div>
            <p class="ai-chart-footnote">区间按实际小数成绩划分。百分比独立四舍五入，合计可能略有误差。</p>
          </div>
          <div class="ai-grade-student"><strong>学生口径</strong><span>有效成绩涉及 {{ fmt(gradeStats.valid_students) }} 名学生；其中 {{ fmt(gradeStats.below_pass_students) }} 名至少有一条低于60分的考核记录。</span><small>按学生去重；仅为描述性统计，不代表挂科人数或正式学业预警。</small></div>
          <div class="ai-chart-heading ai-course-heading"><strong>课程成绩结构对比</strong><span>{{ fmt(gradeStats.course_results.length) }} 门有有效成绩的课程</span></div>
          <div class="ai-score-table-wrap">
            <table class="ai-table ai-grade-table"><thead><tr><th>课程</th><th>有效记录</th><th>均分</th><th>及格率</th><th>优秀率</th></tr></thead>
              <tbody><tr v-for="course in gradeCoursePage" :key="course.course_id"><td>{{ course.course_name }}</td><td>{{ fmt(course.records) }}</td><td>{{ course.average_score ?? '—' }}</td><td>{{ pct(course.pass_rate) }}</td><td>{{ pct(course.excellent_rate) }}</td></tr></tbody>
            </table>
          </div>
          <div v-if="gradePages > 1" class="ai-cases-footer"><span>第 {{ gradePage }} / {{ gradePages }} 页</span><div class="ai-case-controls"><button class="ai-btn ai-btn-ghost ai-btn-small" :disabled="gradePage <= 1" @click="gradePage--">上一页</button><button class="ai-btn ai-btn-ghost ai-btn-small" :disabled="gradePage >= gradePages" @click="gradePage++">下一页</button></div></div>
          <p class="ai-chart-footnote">课程比率按有效考核记录计算，未按考核权重合成最终成绩。</p>
        </template>
        <div v-else-if="gradeStats" class="ai-state ai-small-state">当前没有符合百分制口径的已发布成绩；排除 {{ fmt(gradeStats.excluded_records) }} 条记录。暂无可计算的分布或比率。</div>
        <div v-else class="ai-state ai-small-state">{{ loadError ? '成绩数据暂时无法读取。' : '等待后端返回深度成绩统计。' }}</div>
      </section>
    </div>
    <div class="ai-zone" id="ai-operations-zone">
      <div class="ai-zone-heading"><span class="ai-zone-number">03</span><div><h2>教学运行</h2><p>教学资源与考试安排</p></div><button type="button" class="ai-zone-return" @click="jumpTo('ai-module-nav')">返回导航 ↑</button></div>
      <section class="ai-panel" id="ai-teaching-section">
        <div class="ai-panel-head"><div><h2>本学期教学资源概览</h2></div><button class="ai-inline-link" @click="navigate('/analysis')">进入教学分析 ›</button></div>
        <template v-if="operations">
          <div class="ai-op-kpis">
            <div><span>在开课程（按教学班去重）</span><strong>{{ fmt(operations.active_courses) }}</strong><small>门</small></div>
            <div><span>在开教学班</span><strong>{{ fmt(operations.active_classes) }}</strong><small>个</small></div>
            <div><span>任课教师（去重）</span><strong>{{ fmt(operations.teachers) }}</strong><small>人</small></div>
            <div><span>选课登记人次</span><strong>{{ fmt(operations.enrolled_total) }}</strong><small>人次 · 非去重人数</small></div>
          </div>
          <div class="ai-op-grid">
            <article class="ai-op-card">
              <div class="ai-op-head"><h3>教师教学任务</h3><button class="ai-inline-link" @click="navigate('/teacher')">教师管理 ›</button></div>
              <div class="ai-op-pair"><div><span>人均承担教学班</span><strong>{{ fmt(operations.teacher_average_classes) }}</strong></div><div><span>单人最多承担教学班</span><strong>{{ fmt(operations.teacher_max_classes) }}</strong></div></div>
              <div v-if="operations.teacher_distribution.length" class="ai-op-distribution"><span v-for="group in operations.teacher_distribution" :key="group.classes">承担 {{ group.classes }} 班：{{ group.teachers }} 人</span></div>
              <div v-if="operations.teacher_preview.length" class="ai-op-table-wrap"><table class="ai-table ai-op-table"><thead><tr><th>任课教师</th><th>教学班</th><th>课程</th></tr></thead><tbody><tr v-for="teacher in operations.teacher_preview" :key="teacher.id"><td>{{ teacher.name }}</td><td>{{ fmt(teacher.classes) }}</td><td>{{ fmt(teacher.courses) }}</td></tr></tbody></table></div>
              <p v-else class="ai-state">暂无在开教学班对应的教师任务。</p>
              <p class="ai-chart-footnote">按承担教学班数降序展示至多8名教师。仅反映登记任务数量，不代表实际授课学时或绩效。</p>
            </article>
            <article class="ai-op-card">
              <div class="ai-op-head"><h3>教学资源与容量</h3><button class="ai-inline-link" @click="navigate('/course')">课程管理 ›</button></div>
              <div class="ai-op-util"><span>已登记正容量教学班利用率</span><strong>{{ pct(operations.capacity.utilization) }}</strong><div class="ai-op-track"><div :style="{ width: Math.min(100, operations.capacity.utilization ?? 0) + '%' }"></div></div><small>{{ fmt(operations.capacity.enrolled) }} 人次 / {{ fmt(operations.capacity.seats) }} 个计划名额 · {{ fmt(operations.capacity.known_classes) }} 个班纳入</small></div>
              <div class="ai-op-pair ai-op-cap"><div><span>各班剩余名额合计</span><strong>{{ fmt(operations.capacity.spare) }}</strong></div><div><span>各班超出名额合计</span><strong>{{ fmt(operations.capacity.excess) }}</strong></div><div><span>恰好满额班</span><strong>{{ fmt(operations.capacity.full_classes) }}</strong></div><div><span>超容量班</span><strong>{{ fmt(operations.capacity.over_classes) }}</strong></div></div>
              <p class="ai-chart-footnote">未登记正容量 {{ fmt(operations.capacity.unknown_classes) }} 班，不计入利用率；剩余和超出名额分别累计，不相互抵消。利用率可超过100%。</p>
            </article>
            <article class="ai-op-card">
              <div class="ai-op-head"><h3>排课星期分布</h3><span>按在开教学班计数</span></div>
              <div class="ai-op-bars"><div v-for="day in operations.schedule.weekdays" :key="day.label" class="ai-op-bar"><span>{{ day.label }}</span><div class="ai-op-track"><div :style="{ width: opBar(day.count, operations.schedule.parsed) }"></div></div><b>{{ fmt(day.count) }} 班</b></div></div>
              <p class="ai-chart-footnote">可解析 {{ fmt(operations.schedule.parsed) }} 班 · 格式未解析 {{ fmt(operations.schedule.unparsed) }} 班 · 未登记 {{ fmt(operations.schedule.missing) }} 班。只识别单一明确星期和节次格式，未解析不等于未排课。</p>
            </article>
            <article class="ai-op-card">
              <div class="ai-op-head"><h3>考试日期与考场登记</h3><button class="ai-inline-link" @click="navigate('/exam')">考试管理 ›</button></div>
              <div class="ai-op-pair ai-op-cap"><div><span>涉及考试日期</span><strong>{{ fmt(operations.exams.days) }}</strong></div><div><span>单日最多考试</span><strong>{{ fmt(operations.exams.peak_daily) }}</strong></div><div><span>不同考场登记名称</span><strong>{{ fmt(operations.exams.venues) }}</strong></div><div><span>单一考场累计最多场次</span><strong>{{ fmt(operations.exams.peak_venue) }}</strong></div></div>
              <div v-if="operations.exams.busiest_days.length" class="ai-op-bars"><div v-for="day in operations.exams.busiest_days" :key="day.date" class="ai-op-bar ai-op-date"><span>{{ day.date }}</span><div class="ai-op-track"><div :style="{ width: opBar(day.count, operations.exams.peak_daily ?? 0) }"></div></div><b>{{ fmt(day.count) }} 场</b></div></div>
              <p v-else class="ai-state">暂无已登记日期的考试。</p>
              <p class="ai-chart-footnote">按本地日期统计场次，展示考试场次较多的日期（至多8日）；地点登记 {{ fmt(operations.exams.located) }} / {{ fmt(operations.exams.total) }} 场。不同登记名称不等于实际考场数或占用率。</p>
            </article>
          </div>
        </template>
        <div v-else class="ai-state">{{ overview?.semester ? '教学运行综合统计暂不可用：后端尚未返回完整统计或登记记录超过扫描上限。' : '尚无当前学期，无法计算教学运行综合指标。' }}</div>
        <div class="ai-op-check-heading"><h3>登记质量与规则核查</h3><span>排课、容量及考试登记</span></div>
        <div class="ai-op-grid ai-op-check-grid">
        <div class="ai-running-items">
          <div><span>未登记上课时间的教学班</span><strong>{{ fmt(overview?.analyses.teaching.missing_schedule) }}</strong><button @click="navigate('/course')">核查排课</button></div>
          <div><span>选课人数超过登记容量的教学班</span><strong>{{ fmt(overview?.analyses.teaching.over_capacity) }}</strong><button @click="navigate('/course')">核查人数</button></div>
          <div><span>尚未安排考试地点</span><strong>{{ fmt(overview?.analyses.teaching.missing_exam_location) }}</strong><button @click="navigate('/exam')">核查考场</button></div>
          <div><span>已检测的考场时间冲突</span><strong>{{ fmt(overview?.analyses.teaching.venue_collisions) }}</strong><button @click="navigate('/exam')">查看排考</button></div>
          <div><span>第18 / 19周登记考试</span><strong>{{ fmt(overview?.analyses.teaching.week18_exams) }} / {{ fmt(overview?.analyses.teaching.week19_exams) }}</strong><button @click="navigate('/exam')">考试日历</button></div>
        </div>
        <div v-if="teachingCoverage.length" class="ai-coverage">
          <div class="ai-chart-heading"><strong>教学运行数据登记完整度</strong><span>依据已录入字段，不代表教学质量评分</span></div>
          <div v-for="metric in teachingCoverage" :key="metric.label" class="ai-coverage-row">
            <div class="ai-coverage-label"><span>{{ metric.label }}</span><b>{{ metric.rate.toFixed(1) }}%</b></div>
            <div class="ai-coverage-track"><span :style="{ width: metric.rate + '%' }"></span></div>
            <small>{{ metric.completed }} / {{ metric.total }} 条已登记</small>
          </div>
        </div>
        </div>
        <div class="ai-source-disclaimer">预警依据为真实教学班、考试时间与地点字段。暂不对课堂效果、教师教学能力或学校未核验制度作自动评价。</div>
      </section>
    </div>
    <div class="ai-zone" id="ai-risk-zone">
      <div class="ai-zone-heading"><span class="ai-zone-number">04</span><div><h2>风险核查与处置</h2><p>规则检测及人工处理台账</p></div><button type="button" class="ai-zone-return" @click="jumpTo('ai-module-nav')">返回导航 ↑</button></div>
      <section class="ai-panel ai-warning-panel" aria-labelledby="ai-warning-title">
        <div class="ai-panel-head">
          <div><h2 id="ai-warning-title">规则识别与风险核查</h2><p>按业务规则识别，交由人工核查</p></div>
          <button type="button" class="ai-btn ai-btn-ghost ai-btn-small" @click="jumpTo('ai-case-section')">处理记录</button>
        </div>
        <div v-if="riskSegments.length" class="ai-chart-block ai-risk-visual">
          <div class="ai-chart-heading"><strong>待核查事项类型分布</strong><span>最多展示160项 · 当前图表 {{ riskTotal }} 项 / 总计 {{ fmt(overview?.rule_total) }} 项</span></div>
          <div ref="riskChartRef" class="ai-risk-chart" role="img" :aria-label="riskChartDescription"></div>
        </div>
        <div class="ai-warning-list">
          <div v-if="loadError && !overview" class="ai-state">未能读取智能分析后端数据，暂不能判断学期风险；请检查 Django 服务、登录权限及数据库迁移。</div>
          <div v-else-if="!overview?.semester" class="ai-state">本学期档案未建立，不能启动学期风险检查。</div>
          <div v-else-if="!overview.rule_preview.length && !overview.rules_complete" class="ai-state">规则扫描不完整，不能判断是否存在异常。请检查数据规模与后端扫描上限。</div>
          <div v-else-if="!overview.rule_preview.length" class="ai-state">现有规则未发现登记异常；不代表所有教学风险均已排除。</div>
          <article v-for="risk in overview?.rule_preview.slice(0, 8) || []" :key="risk.key" class="ai-risk">
            <div class="ai-risk-top"><span class="ai-risk-severity" :class="risk.severity">{{ risk.severity === 'high' ? '需优先核查' : '待核查' }}</span><span>{{ risk.category }}</span></div>
            <strong>{{ risk.title }}</strong><p>{{ risk.description }}</p>
            <div class="ai-risk-foot"><span>依据：{{ risk.source }}</span><button class="ai-inline-link" @click="navigate(risk.route_path)">查看原页面 ›</button></div>
          </article>
          <p v-if="overview && overview.rule_preview.length > 8" class="ai-extra-note">其余 {{ Math.max(0, overview.rule_total - 8) }} 项可在完整扫描后同步到下方台账。</p>
        </div>
        <div class="ai-warning-actions"><button type="button" class="ai-btn ai-btn-primary" :disabled="syncing || !overview?.semester || !overview?.rules_complete" @click="syncWarnings">{{ syncing ? '同步中…' : '将检测结果加入核查台账' }}</button></div>
      </section>
    <section class="ai-panel ai-case-panel" id="ai-case-section">
      <div class="ai-panel-head">
        <div><h2>预警管理与处理记录</h2><p>待核查 → 处理中 → 已解决；误报可标记已排除</p></div>
        <div class="ai-case-controls"><select v-model="caseFilter"><option value="">全部状态</option><option value="pending">待核查</option><option value="in_progress">处理中</option><option value="resolved">已解决</option><option value="dismissed">已排除</option></select><button class="ai-btn ai-btn-ghost ai-btn-small" @click="loadCases()">刷新记录</button></div>
      </div>
      <div v-if="caseProgressTotal > 0" class="ai-case-progress">
        <div class="ai-case-progress-head"><strong>本学期核查处理进度</strong><span>共 {{ caseProgressTotal }} 项 · 已结束处理 {{ caseClosedTotal }} 项</span></div>
        <div class="ai-case-progress-track" role="img" :aria-label="caseProgressDescription">
          <span v-for="part in caseProgress" :key="part.key" :style="{ width: part.width + '%', backgroundColor: part.color }" :title="part.label + '：' + part.count + '项'"></span>
        </div>
        <div class="ai-case-progress-legend"><span v-for="part in caseProgress" :key="part.key"><i :style="{ backgroundColor: part.color }"></i>{{ part.label }} {{ part.count }}</span></div>
      </div>
      <div class="ai-score-table-wrap"><table class="ai-table ai-case-table"><thead><tr><th>规则事项</th><th>风险类别</th><th>人工状态</th><th>来源状态</th><th>责任人</th><th>更新时间</th><th>操作</th></tr></thead>
        <tbody><tr v-for="row in visibleCases" :key="row.id"><td><strong>{{ row.title }}</strong><small>{{ row.semester_key }}</small></td><td>{{ row.category }}</td><td><span class="ai-case-status">{{ row.status_label }}</span></td><td><span :class="row.source_active ? 'ai-source-active' : 'ai-source-cleared'">{{ row.source_active ? (row.source_reappeared_at ? '当前命中（曾复现）' : '当前命中') : '来源已解除' }}</span></td><td>{{ row.handler || '待指定' }}</td><td>{{ timeText(row.updated_at) }}</td><td><button class="ai-inline-link" @click="editCase(row)">核查处理 ›</button></td></tr>
          <tr v-if="!visibleCases.length"><td colspan="7" class="ai-table-empty">{{ loadError && !overview ? '智能分析后端数据尚未读取成功，无法核实处理记录。' : '暂无此状态的处理记录。可将上方规则识别结果加入核查台账。' }}</td></tr>
        </tbody></table></div>
      <div class="ai-cases-footer"><span>已显示 {{ cases.length }} / {{ casesTotal }} 项</span><button v-if="nextCaseOffset !== null" class="ai-btn ai-btn-ghost ai-btn-small" :disabled="casesLoading" @click="loadMoreCases">{{ casesLoading ? '加载中…' : '加载更多记录' }}</button></div>
    </section>
    </div>

    <div class="ai-zone" id="ai-history-zone">
      <div class="ai-zone-heading"><span class="ai-zone-number">05</span><div><h2>历史趋势分析</h2><p>跨学期登记统计 · 同课程对照 · 数据质量核查</p></div><button type="button" class="ai-zone-return" @click="jumpTo('ai-module-nav')">返回导航 ↑</button></div>
      <section class="ai-panel" aria-labelledby="ai-history-title">
        <div class="ai-panel-head"><div><h2 id="ai-history-title">跨学期教学与成绩对照</h2><p>按业务记录所属学期统计，不推断缺失历史，不生成预测值</p></div><button class="ai-btn ai-btn-ghost ai-btn-small" :disabled="sending || !history" @click="askHistory">智能解读历史数据</button></div>
        <template v-if="history">
          <div class="ai-op-kpis ai-history-kpis">
            <div><span>已登记学期档案</span><strong>{{ fmt(history.total_archives) }}</strong><small>含尚无业务记录的档案</small></div>
            <div><span>本次展示学期</span><strong>{{ fmt(history.terms.length) }}</strong><small>最多8期</small></div>
            <div><span>有业务记录学期</span><strong>{{ fmt(history.observed_terms) }}</strong><small>教学班、考试或已发布成绩</small></div>
            <div><span>有有效成绩学期</span><strong>{{ fmt(history.grade_terms) }}</strong><small>百分制考核记录</small></div>
          </div>
          <p class="ai-explanation">{{ history.note }} 未展示档案 {{ history.excluded_archives }} 个（可能为更早、未来、日期不明或与当前起始日期相同的学期）；全部档案中未登记起始日期 {{ history.undated_archives }} 个。</p>
          <div v-if="history.observed_terms < 2" class="ai-history-info">不足两个有业务记录的学期，目前不能判断跨学期变化。以下只显示已登记数据。</div>
          <div v-if="history.terms.length" class="ai-history-content">
            <div class="ai-history-chart">
              <div class="ai-history-subhead"><strong>逐期指标对照</strong><label>指标 <select v-model="historyMetric" aria-label="选择历史指标"><option value="classes">登记教学班数</option><option value="enrolled">选课登记人次</option><option value="teachers">任课教师数</option><option value="average_score">成绩记录均分</option><option value="pass_rate">记录及格率</option><option value="excellent_rate">记录优秀率</option><option value="capacity_rate">正容量班利用率</option></select></label></div>
              <div v-for="term in history.terms" :key="term.id" class="ai-history-bar-row">
                <div><b>{{ term.name }}</b><small>{{ historyPeriod(term) }}</small></div>
                <div class="ai-op-track" :class="{'ai-history-no-value': historyValue(term) == null}"><div :style="{ width: opBar(historyValue(term) ?? 0, historyMax) }"></div></div>
                <strong>{{ historyValue(term) == null ? '无可算值' : historyIsPct ? pct(historyValue(term)) : fmt(historyValue(term)) }}</strong>
              </div>
              <p class="ai-source-disclaimer">柱长按所选指标统一尺度展示；空白代表无可计算记录，不能当作零。进行中与结束学期仅作描述性比较。</p>
            </div>
            <div class="ai-history-subhead"><strong>教学规模与成绩结构</strong><small>按登记学期 · 日期状态不代表数据齐全</small></div>
            <div class="ai-history-table-wrap"><table class="ai-table ai-history-table"><thead><tr><th>学期 / 日期状态</th><th>课程</th><th>教学班</th><th>教师</th><th>选课人次</th><th>容量利用率</th><th>考试</th><th>有效成绩</th><th>均分</th><th>及格率</th><th>优秀率</th></tr></thead><tbody>
              <tr v-for="term in history.terms" :key="term.id"><td><b>{{ term.name }}</b><small>{{ historyPeriod(term) }}</small></td><td>{{ fmt(term.courses) }}</td><td>{{ fmt(term.classes) }}</td><td>{{ fmt(term.teachers) }}</td><td>{{ fmt(term.enrolled) }}</td><td>{{ pct(term.capacity_rate) }}</td><td>{{ fmt(term.exams) }}</td><td>{{ fmt(term.grade_records) }}</td><td>{{ fmt(term.average_score) }}</td><td>{{ pct(term.pass_rate) }}</td><td>{{ pct(term.excellent_rate) }}</td></tr>
            </tbody></table></div>
            <p class="ai-source-disclaimer">课程及教师按未取消教学班去重，包含已结课班；选课人次不是学生人数。容量仅统计正容量班；成绩比例以有效百分制考核记录为分母，并非最终课程通过率。</p>
            <div class="ai-history-course">
              <div class="ai-history-subhead"><strong>同一课程跨学期比较</strong><label v-if="history.courses.length">选择课程 <select v-model.number="historyCourseId" aria-label="选择同课程"><option v-for="c in history.courses" :key="c.course_id" :value="c.course_id">{{ c.course_name }}</option></select></label></div>
              <div v-if="!selectedHistoryCourse" class="ai-state">暂未发现两个及以上学期均有有效成绩记录的同一课程（按课程ID匹配，不按名称合并）。</div>
              <div v-else class="ai-history-table-wrap"><table class="ai-table ai-history-table"><thead><tr><th>学期</th><th>有效记录</th><th>涉及学生</th><th>均分</th><th>记录及格率</th><th>记录优秀率</th></tr></thead><tbody><tr v-for="term in selectedHistoryCourse.terms" :key="term.semester_id"><td>{{ term.semester }}</td><td>{{ fmt(term.records) }}</td><td>{{ fmt(term.student_count) }}</td><td>{{ fmt(term.average_score) }}</td><td>{{ pct(term.pass_rate) }}</td><td>{{ pct(term.excellent_rate) }}</td></tr></tbody></table></div>
              <p class="ai-source-disclaimer">仅对照已有记录，不对缺少学期补零；学生构成及考核类型可能不同，不直接评价教师绩效或学习进步。</p>
            </div>
          </div>
          <div v-else class="ai-state">尚无符合展示范围的学期档案。请维护学期起止日期及业务记录。</div>
        </template>
        <div v-else class="ai-state">{{ loading ? '正在读取历史学期数据…' : '历史统计暂不可用，请刷新或确认后端已更新。' }}</div>
      </section>
      <section v-if="history && history.terms.length" class="ai-panel">
        <div class="ai-panel-head"><div><h2>学期数据有效性核查</h2><p>核对登记日期和关联关系，仅提示待核查数据，不修改数据库或预警台账</p></div><button class="ai-btn ai-btn-ghost ai-btn-small" @click="navigate('/exam')">进入考试管理 ›</button></div>
        <div class="ai-history-info" v-if="history.terms.some(t => (t.quality.exams.outside ?? 0) > 0 || (t.quality.grades.outside ?? 0) > 0 || t.quality.linked_exam_conflicts > 0)">发现日期越界或成绩关联冲突。相关记录仍按原登记学期展示；请核实归属与日期后再用于趋势判断或训练预测模型。</div>
        <div class="ai-history-table-wrap"><table class="ai-table ai-history-table"><thead><tr><th>学期</th><th>档案日期范围</th><th>考试日期越界 / 缺失</th><th>成绩日期越界 / 缺失</th><th>成绩关联考试冲突</th><th>排除成绩</th></tr></thead><tbody>
          <tr v-for="term in history.terms" :key="term.id"><td>{{ term.name }}</td><td><span>{{ term.start || '未登记' }} ～ {{ term.end || '未登记' }}</span><small v-if="!term.quality.bounds_valid">日期不全或无效，不能判断越界</small></td><td :class="{'ai-history-alert': (term.quality.exams.outside ?? 0) > 0}">{{ fmt(term.quality.exams.outside) }} / {{ fmt(term.quality.exams.missing) }}</td><td :class="{'ai-history-alert': (term.quality.grades.outside ?? 0) > 0}">{{ fmt(term.quality.grades.outside) }} / {{ fmt(term.quality.grades.missing) }}</td><td :class="{'ai-history-alert': term.quality.linked_exam_conflicts > 0}">{{ fmt(term.quality.linked_exam_conflicts) }}</td><td>{{ fmt(term.excluded_records) }}</td></tr>
        </tbody></table></div>
        <p class="ai-source-disclaimer">考试日期按本地日期核对；成绩日期使用考核日期字段，仅统计已发布记录；关联冲突指成绩与关联考试的学期或课程不同。日期越界不等于正式教学事故；缺日期与越界分别统计。 — 表示无法计算。</p>
      </section>
    </div>

    <div class="ai-zone" id="ai-replay-zone">
      <div class="ai-zone-heading"><span class="ai-zone-number">06</span><div><h2>智能预测与风险研判</h2><p>历史演示预测回放 · 模型评估 · 智能解读</p></div><button type="button" class="ai-zone-return" @click="jumpTo('ai-module-nav')">返回导航 ↑</button></div>
      <section class="ai-panel">
        <div class="ai-panel-head"><div><h2>学业风险预测模型（演示）</h2><p>使用已训练模型回放历史合成学期</p></div><div class="ai-replay-actions"><button type="button" class="ai-btn ai-btn-ghost" :disabled="replayLoading || sending" @click="runReplay">{{ replayLoading ? '正在回放…' : '运行演示预测' }}</button><button type="button" class="ai-btn ai-btn-ghost" :disabled="!prediction || sending || replayLoading" @click="explainReplay">智能解读预测结果</button></div></div>
        <div class="ai-history-info">仅用于合成历史数据上的模型功能展示。关注阈值不是学校正式预警标准，不形成学生名单、不自动加入正式预警台账。</div>
        <p v-if="replayError" class="ai-history-info" role="alert">{{ replayError }}</p>
        <div v-if="!prediction && !replayError" class="ai-replay-empty">点击“运行演示预测”，读取历史合成数据并实际运行模型。</div>
        <template v-if="prediction">
          <p class="ai-explanation">回放学期：{{ prediction.semester }} · 模拟预测截止日：{{ prediction.cutoff }} · 训练学期：{{ prediction.train_semester }} · 关注阈值：{{ pct(prediction.threshold * 100) }}</p>
          <div class="ai-op-kpis ai-replay-kpis">
            <div><span>回放样本</span><strong>{{ fmt(prediction.samples) }}</strong><small>学生—课程样本</small></div>
            <div><span>达到关注阈值</span><strong>{{ fmt(prediction.flagged) }}</strong><small>模型分类结果</small></div>
            <div><span>未达到关注阈值</span><strong>{{ fmt(prediction.unflagged) }}</strong><small>不等于无风险</small></div>
            <div><span>实际低分样本</span><strong>{{ fmt(prediction.actual_low) }}</strong><small>历史合成期末标签</small></div>
          </div>
          <div class="ai-history-chart"><div class="ai-history-subhead"><strong>回放分类分布</strong><small>按样本统计 · 非学生人数</small></div>
            <div v-for="item in [{ label: '达到关注阈值', value: prediction.flagged }, { label: '未达到关注阈值', value: prediction.unflagged }]" :key="item.label" class="ai-history-bar-row"><b>{{ item.label }}</b><div class="ai-op-track"><div :style="{ width: opBar(item.value, prediction.samples) }"></div></div><strong>{{ fmt(item.value) }}</strong></div>
          </div>
          <div class="ai-history-subhead"><strong>课程级演示预测对照</strong><small>仅显示至少5名不同学生的课程</small></div>
          <div class="ai-history-table-wrap"><table class="ai-table ai-history-table"><thead><tr><th>课程</th><th>回放样本</th><th>达到关注阈值</th><th>平均模型概率</th></tr></thead><tbody><tr v-for="(c,i) in prediction.courses" :key="i"><td>{{ c.course }}</td><td>{{ fmt(c.samples) }}</td><td>{{ fmt(c.flagged) }}</td><td>{{ pct(c.mean_probability * 100) }}</td></tr></tbody></table></div>
          <p class="ai-explanation">模型概率仅为合成数据回放输出，不是已校准的真实学业风险概率。未展示的小样本课程合计 {{ prediction.suppressed_samples }} 个样本。</p>
          <div class="ai-replay-eval"><div><strong>模型评估 · {{ prediction.model }}</strong><div class="ai-op-kpis ai-replay-metrics"><div v-for="m in replayMetrics" :key="m.label"><span>{{ m.label }}</span><strong>{{ m.value.toFixed(4) }}</strong></div></div></div><div><strong>混淆矩阵（历史标签）</strong><table class="ai-table"><thead><tr><th></th><th>实际低分</th><th>实际非低分</th></tr></thead><tbody><tr><td>达到关注阈值</td><td>{{ prediction.confusion.tp }}</td><td>{{ prediction.confusion.fp }}</td></tr><tr><td>未达到阈值</td><td>{{ prediction.confusion.fn }}</td><td>{{ prediction.confusion.tn }}</td></tr></tbody></table></div></div>
          <p class="ai-source-disclaimer">{{ prediction.note }} 训练与评估学生存在重叠，合成日期不证明真实发布时间；结果不可用于真实学生正式判定。</p>
        </template>
      </section>
    </div>

    <details class="ai-notes" v-if="overview?.data_notes?.length"><summary>数据范围与判断边界（展开查看统计口径）</summary><p v-for="note in overview.data_notes" :key="note">{{ note }}</p></details>

    <el-dialog v-model="caseDialogVisible" title="核查与处理预警事项" width="560px" :close-on-click-modal="false">
      <div class="ai-case-dialog" v-if="editingCase">
        <strong>{{ editingCase.title }}</strong><p>{{ editingCase.description }}</p>
        <p class="ai-source-note">{{ editingCase.source_active ? '当前仍命中业务规则；人工结案不会自动修改原始业务数据。' : '原始数据已不再命中规则，但历史人工处理记录仍保留。' }}</p>
        <label>处理状态<select v-model="caseEdit.status"><option value="pending">待核查</option><option value="in_progress">处理中</option><option value="resolved">已解决</option><option value="dismissed">已排除</option></select></label>
        <label>责任人<input v-model.trim="caseEdit.handler" maxlength="80" placeholder="请输入真实责任人或部门" /></label>
        <label>核查与处理说明<textarea v-model.trim="caseEdit.resolution_note" maxlength="2000" rows="4" placeholder="结案或排除风险时必须填写可核验的处理依据"></textarea></label>
        <span class="ai-muted">该操作仅修改当前风险事项的处理记录，不会自动更改成绩、排考或教学班数据。</span>
      </div>
      <template #footer><button class="ai-btn ai-btn-ghost" @click="caseDialogVisible=false">取消</button><button class="ai-btn ai-btn-primary" :disabled="savingCase" @click="saveCase">{{ savingCase ? '保存中…' : '保存处理结果' }}</button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import * as echarts from 'echarts'
import api from '@/api/index'
import { formatAnswer } from './answerFormat'

type WarningStatus = 'pending' | 'in_progress' | 'resolved' | 'dismissed'
type Risk = { key: string; category: string; severity: string; title: string; description: string; source: string; route_path: string }
type Case = Risk & { id: number; semester_key: string; status: WarningStatus; status_label: string; handler: string; resolution_note: string; source_active: boolean; source_reappeared_at: string | null; updated_at: string }
type Stats = { courses: number; teaching_classes: number; exams: number; published_grades: number; graded_students: number }
type GradeCourse = { course_id: number; course_name: string; student_count: number; records: number; average_score: number | null; pass_rate: number | null; excellent_rate: number | null }
type GradeStats = { records: number; average_score: number | null; median_score: number | null; std_score: number | null; pass_count: number; below_pass_count: number; excellent_count: number; pass_rate: number | null; below_pass_rate: number | null; excellent_rate: number | null; excluded_records: number; valid_students: number; below_pass_students: number; distribution: Array<{ label: string; count: number; rate: number | null }>; course_results: GradeCourse[]; explanation: string }
type Operations = {
  active_classes: number; active_courses: number; teachers: number; enrolled_total: number
  teacher_average_classes: number | null; teacher_max_classes: number | null
  teacher_distribution: Array<{classes: number; teachers: number}>
  teacher_preview: Array<{id: number; name: string; classes: number; courses: number}>
  capacity: { known_classes: number; unknown_classes: number; seats: number; enrolled: number; utilization: number | null; spare: number; excess: number; full_classes: number; over_classes: number }
  schedule: { parsed: number; unparsed: number; missing: number; weekdays: Array<{label: string; count: number}> }
  exams: { total: number; days: number; dated: number; peak_daily: number | null; venues: number; located: number; peak_venue: number | null; busiest_days: Array<{date: string; count: number}> }
}
type HistoryDateQuality = { missing: number; outside: number | null; dated: number }
type HistoryTerm = { demo_generated_grades?: number; demo_normalized_grades?: number; id: number; name: string; start: string | null; end: string | null; period: 'open' | 'closed' | 'unknown' | 'future'; has_data: boolean; classes: number; courses: number; teachers: number; enrolled: number; capacity_rate: number | null; exams: number; grade_records: number; published_records: number; excluded_records: number; valid_students: number; average_score: number | null; pass_rate: number | null; excellent_rate: number | null; quality: { bounds_valid: boolean; exams: HistoryDateQuality; grades: HistoryDateQuality; linked_exam_conflicts: number } }
type HistoryCourse = { course_id: number; course_name: string; terms: Array<{ semester_id: number; semester: string; student_count: number; records: number; average_score: number | null; pass_rate: number | null; excellent_rate: number | null }> }
type HistoryStats = { terms: HistoryTerm[]; courses: HistoryCourse[]; current_id: number | null; total_archives: number; undated_archives: number; excluded_archives: number; observed_terms: number; grade_terms: number; note: string }
type HistoryMetric = 'classes' | 'enrolled' | 'teachers' | 'average_score' | 'pass_rate' | 'excellent_rate' | 'capacity_rate'
type Overview = {
  demo_data?: boolean
  history_trend?: HistoryStats
  semester: { id: number; name: string } | null
  summary: Stats
  analyses: { grade: GradeStats
    teaching: { missing_schedule: number; over_capacity: number; active_classes_scanned: number; missing_exam_location: number; venue_collisions: number; week18_exams: number | null; week19_exams: number | null; operations?: Operations | null } }
  rule_preview: Risk[]; rule_total: number; rules_complete: boolean; data_notes: string[]
  ai: { enabled: boolean; model: string }
  case_counts: { pending: number; in_progress: number; resolved: number; dismissed: number; source_active: number; source_cleared: number }
}
type RouteAction = { label: string; path: string }
type Message = { id: string; role: 'user' | 'assistant'; content: string; actions?: RouteAction[]; mode?: string; sources?: string[] }
type Reply = { answer: string; mode: string; actions: RouteAction[]; data_sources: string[] }
const router = useRouter()
const allowedPaths = new Set(['/course', '/teacher', '/student', '/exam', '/grade', '/analysis', '/ai-warning'])
const overview = ref<Overview | null>(null)
type Replay = { model: string; semester: string; train_semester: string; cutoff: string; threshold: number; samples: number; flagged: number; unflagged: number; actual_low: number; suppressed_samples: number; note: string; courses: { course: string; samples: number; flagged: number; mean_probability: number }[]; confusion: { tp: number; fp: number; fn: number; tn: number }; metrics: { roc_auc: number; average_precision: number; f1: number; brier: number; precision: number; recall: number } }
const prediction = ref<Replay | null>(null)
const replayLoading = ref(false)
const replayError = ref('')
const replayMetrics = computed(() => {
  const m = prediction.value?.metrics
  return m ? [{label:'ROC-AUC',value:m.roc_auc},{label:'AP',value:m.average_precision},{label:'F1',value:m.f1},{label:'Brier',value:m.brier},{label:'Precision',value:m.precision},{label:'Recall',value:m.recall}] : []
})
async function runReplay() {
  if (replayLoading.value) return
  replayLoading.value = true; prediction.value = null; replayError.value = ''
  try { prediction.value = await api.post('/ai/demo-replay/', {}, { timeout: 45000 }) as unknown as Replay }
  catch (e) { replayError.value = extractError(e, '历史演示预测回放不可用。') }
  finally { replayLoading.value = false }
}
function explainReplay() {
  if (!prediction.value || sending.value) return
  jumpTo('ai-chat-zone')
  void sendQuestion('请解读历史演示预测回放的模型表现、关注样本、误报和漏报、课程级汇总及适用边界，不作真实学生风险判定。')
}

const cases = ref<Case[]>([])
const casesTotal = ref(0)
const nextCaseOffset = ref<number | null>(null)
const casesLoading = ref(false)
const loading = ref(false)
const loadError = ref('')
const syncing = ref(false)
const sending = ref(false)
const savingCase = ref(false)
const question = ref('')
const messages = ref<Message[]>([])
const chatScrollRef = ref<HTMLElement | null>(null)
const riskChartRef = ref<HTMLElement | null>(null)
let riskChart: echarts.ECharts | null = null
let chartResizeObserver: ResizeObserver | null = null
const caseFilter = ref('')
const caseDialogVisible = ref(false)
const editingCase = ref<Case | null>(null)
const caseEdit = ref<{ status: WarningStatus; handler: string; resolution_note: string }>({ status: 'pending', handler: '', resolution_note: '' })
const examplePrompts = [
  '本学期考试安排有哪些待核查问题？',
  '本学期成绩分布及及格率如何？',
  '有多少教学班未登记上课时间或超容量？',
  '打开考试管理页面',
]

// 图表只使用 /api/ai/overview/ 返回的数据，不使用演示统计。
const riskSegments = computed(() => {
  const counts = new Map<string, number>()
  for (const item of overview.value?.rule_preview || []) {
    const category = item.category || '其他待核查事项'
    counts.set(category, (counts.get(category) || 0) + 1)
  }
  return Array.from(counts, ([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value)
})
const riskTotal = computed(() => riskSegments.value.reduce((n, x) => n + x.value, 0))
const riskChartDescription = computed(() => riskSegments.value.map(x => `${x.name}${x.value}项`).join('、'))

const gradeStats = computed(() => {
  const g = overview.value?.analyses.grade
  return g && typeof g.records === 'number' && Array.isArray(g.distribution) ? g : null
})
const pct = (value: number | null | undefined) => value == null ? '—' : `${value.toFixed(2)}%`
const gradePage = ref(1)
const gradePages = computed(() => Math.max(1, Math.ceil((gradeStats.value?.course_results.length || 0) / 8)))
const gradeCoursePage = computed(() => (gradeStats.value?.course_results || []).slice((gradePage.value - 1) * 8, gradePage.value * 8))
watch(gradeStats, () => { gradePage.value = 1 })

const history = computed(() => overview.value?.history_trend ?? null)
const historyMetric = ref<HistoryMetric>('average_score')
const historyCourseId = ref<number | null>(null)
const selectedHistoryCourse = computed(() => history.value?.courses.find(c => c.course_id === historyCourseId.value) ?? null)
watch(history, h => { if (!h?.courses.some(c => c.course_id === historyCourseId.value)) historyCourseId.value = h?.courses[0]?.course_id ?? null })
const historyIsPct = computed(() => ['pass_rate', 'excellent_rate', 'capacity_rate'].includes(historyMetric.value))
function historyValue(t: HistoryTerm): number | null {
  const key = historyMetric.value
  if (['classes','enrolled','teachers'].includes(key) && !t.classes) return null
  return t[key]
}
const historyMax = computed(() => Math.max(historyIsPct.value || historyMetric.value === 'average_score' ? 100 : 1, ...(history.value?.terms.map(t => historyValue(t) ?? 0) || [])))
function historyPeriod(t: HistoryTerm) {
  const label = { open: '进行中', closed: '日期已结束', future: '尚未开始', unknown: '日期不明' }[t.period]
  return `${t.id === history.value?.current_id ? '当前学期 · ' : ''}${label}${!t.has_data ? ' · 无业务记录' : ''}${t.demo_generated_grades ? ' · 合成演示' : t.demo_normalized_grades ? ' · 演示日期规范化' : ''}`
}
function askHistory() {
  jumpTo('ai-chat-zone')
  void sendQuestion('请根据各学期实际登记的教学规模、成绩及数据质量，分析跨学期历史变化。说明当前学期与历史学期的覆盖差异和日期异常；数据不足时不要推断趋势。')
}

const operations = computed(() => overview.value?.analyses.teaching.operations ?? null)
const opBar = (n: number, denominator: number) => `${denominator > 0 ? Math.min(100, 100 * n / denominator) : 0}%`

const teachingCoverage = computed(() => {
  const info = overview.value
  if (!info?.rules_complete) return []
  const result: Array<{ label: string; completed: number; total: number; rate: number }> = []
  const fields = [
    { label: '在开教学班上课时间登记率', total: info.analyses.teaching.active_classes_scanned, missing: info.analyses.teaching.missing_schedule },
    { label: '考试地点登记率', total: info.summary.exams, missing: info.analyses.teaching.missing_exam_location },
  ]
  for (const field of fields) {
    const total = Number(field.total)
    const missing = Number(field.missing)
    if (Number.isFinite(total) && Number.isFinite(missing) && total > 0) {
      const completed = Math.max(0, Math.min(total, total - missing))
      result.push({ label: field.label, completed, total, rate: completed / total * 100 })
    }
  }
  return result
})

const caseProgress = computed(() => {
  const c = overview.value?.case_counts
  if (!c) return []
  const items = [
    { key: 'pending', label: '待核查', color: '#93B4F4', count: Math.max(0, c.pending) },
    { key: 'in_progress', label: '处理中', color: '#3D7DF3', count: Math.max(0, c.in_progress) },
    { key: 'resolved', label: '已解决', color: '#1F9278', count: Math.max(0, c.resolved) },
    { key: 'dismissed', label: '已排除', color: '#9CA9B9', count: Math.max(0, c.dismissed) },
  ]
  const total = items.reduce((n, x) => n + x.count, 0)
  return items.map(x => ({ ...x, width: total > 0 ? x.count / total * 100 : 0 }))
})
const caseProgressTotal = computed(() => caseProgress.value.reduce((n, x) => n + x.count, 0))
const caseClosedTotal = computed(() => (overview.value?.case_counts.resolved || 0) + (overview.value?.case_counts.dismissed || 0))
const caseProgressDescription = computed(() => caseProgress.value.map(x => `${x.label}${x.count}项`).join('、'))

const chartColors = ['#244487', '#3F7CF3', '#7EAAF5', '#A9C9FC', '#6F88B1', '#CDD8E8']
function paintRiskChart() {
  const el = riskChartRef.value
  if (!el || !riskSegments.value.length) {
    if (riskChart) { riskChart.dispose(); riskChart = null }
    return
  }
  if (riskChart && riskChart.getDom() !== el) { riskChart.dispose(); riskChart = null }
  if (!riskChart) riskChart = echarts.init(el, undefined, { renderer: 'canvas' })
  riskChart.setOption({
    color: chartColors,
    tooltip: { trigger: 'item', formatter: '{b}：{c} 项（{d}%）' },
    legend: { type: 'scroll', orient: 'vertical', right: 0, top: 'middle', width: '46%', itemWidth: 9, itemHeight: 9,
      textStyle: { fontSize: 11, color: '#697D9C' } },
    series: [{ type: 'pie', radius: ['52%', '74%'], center: ['29%', '50%'],
      label: { show: false }, labelLine: { show: false },
      itemStyle: { borderColor: '#fff', borderWidth: 2 },
      data: riskSegments.value.map(x => ({ name: x.name, value: x.value })) }],
  }, true)
}
async function redrawCharts() {
  await nextTick()
  paintRiskChart()
  chartResizeObserver?.disconnect()
  if (typeof ResizeObserver !== 'undefined') {
    chartResizeObserver = chartResizeObserver || new ResizeObserver(() => { riskChart?.resize() })
    if (riskChartRef.value) chartResizeObserver.observe(riskChartRef.value)
  }
}
function onWindowResize() { riskChart?.resize() }
watch(riskSegments, () => { void redrawCharts() }, { flush: 'post' })
onUnmounted(() => {
  chartResizeObserver?.disconnect()
  window.removeEventListener('resize', onWindowResize)
  riskChart?.dispose()
  riskChart = null
})

const visibleCases = computed(() => cases.value)
const fmt = (num: number | undefined | null) => num == null ? '—' : Number(num).toLocaleString('zh-CN')
const sourceLabel = (source: string) => ({ Semester: '学期档案', Course: '课程', TeachingClass: '教学班', Exam: '考试', 'Grade（已发布）': '已发布成绩' } as Record<string, string>)[source] || source
const modeLabel = (mode?: string) => ({ deepseek: 'DeepSeek · 聚合数据辅助解释', navigation: '站内导航', data_query: '真实数据规则查询' } as Record<string, string>)[mode || ''] || '教务数据查询'
const timeText = (iso: string) => { const d = new Date(iso); return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }
function navigate(path: string) { if (allowedPaths.has(path)) void router.push(path) }
function jumpTo(id: string) { void nextTick(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })) }
function extractError(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (error.response?.status === 404) return '智能分析后端接口尚未接入，请按部署说明注册 /api/ai/ 路由。'
  }
  return fallback
}
async function loadCases(reset = true) {
  if (casesLoading.value) return
  casesLoading.value = true
  const requestedFilter = caseFilter.value
  try {
    const offset = reset ? 0 : nextCaseOffset.value
    if (offset === null) return
    const result = await api.get('/ai/warnings/', {
      params: { status: requestedFilter || undefined, limit: 100, offset },
    }) as unknown as { count: number; results: Case[]; next_offset: number | null }
    if (caseFilter.value !== requestedFilter) return
    const rows = Array.isArray(result.results) ? result.results : []
    cases.value = reset ? rows : [...cases.value, ...rows]
    casesTotal.value = Number(result.count) || 0
    nextCaseOffset.value = result.next_offset ?? null
  } catch (e) { loadError.value = extractError(e, '预警处理记录读取失败。') }
  finally {
    casesLoading.value = false
    if (caseFilter.value !== requestedFilter) void loadCases()
  }
}
async function loadMoreCases() { await loadCases(false) }
watch(caseFilter, () => { void loadCases() })
async function refreshAll() {
  if (loading.value) return
  loading.value = true; loadError.value = ''
  try {
    overview.value = await api.get('/ai/overview/') as unknown as Overview
    await loadCases()
  } catch (e) { overview.value = null; loadError.value = extractError(e, '无法读取教务数据，请检查后端服务和登录权限。') }
  finally { loading.value = false }
}
async function syncWarnings() {
  if (syncing.value || !overview.value?.semester || !overview.value.rules_complete) return
  syncing.value = true
  try {
    const r = await api.post('/ai/warnings/sync/', {}) as unknown as { created: number; cleared: number; reappeared: number; detected: number }
    await refreshAll()
    window.alert(`本次识别 ${r.detected} 项，新增 ${r.created} 项，来源已解除 ${r.cleared} 项，再次命中 ${r.reappeared} 项。历史人工处理状态保持不变。`)
  } catch (e) { window.alert(extractError(e, '同步预警失败，请检查权限。')) }
  finally { syncing.value = false }
}
function makeId() { return `${Date.now()}-${Math.random().toString(36).slice(2)}` }
async function scrollChat(toAnswer = false) {
  await nextTick()
  const el = chatScrollRef.value
  if (!el) return
  const last = el.querySelector('.ai-message-assistant:last-of-type')
  if (toAnswer && last) {
    const top = last.getBoundingClientRect().top - el.getBoundingClientRect().top + el.scrollTop
    el.scrollTop = Math.max(0, top - 12)
  } else { el.scrollTop = el.scrollHeight }
}
async function sendQuestion(prefilled?: string) {
  const input = String(prefilled ?? question.value).trim()
  if (!input || sending.value) return
  const history = messages.value.slice(-8).map(m => ({ role: m.role, content: m.content }))
  messages.value.push({ id: makeId(), role: 'user', content: input })
  question.value = ''; sending.value = true; void scrollChat()
  try {
    // 聊天可超过普通 /api 15秒超时，因此单独设定 45 秒；JWT 仍由现有登录状态提供。
    const data = await api.post('/ai/chat/', { question: input, history }, { timeout: 45000 }) as unknown as Reply
    messages.value.push({ id: makeId(), role: 'assistant', content: data.answer, actions: (data.actions || []).filter(a => allowedPaths.has(a.path)), mode: data.mode, sources: data.data_sources })
  } catch (e) {
    messages.value.push({ id: makeId(), role: 'assistant', content: extractError(e, '问答暂时不可用，请检查后端服务或 DeepSeek API。') })
  } finally { sending.value = false; void scrollChat(true) }
}
function editCase(item: Case) {
  editingCase.value = item
  caseEdit.value = { status: item.status, handler: item.handler || '', resolution_note: item.resolution_note || '' }
  caseDialogVisible.value = true
}
async function saveCase() {
  if (!editingCase.value || savingCase.value) return
  if (['resolved', 'dismissed'].includes(caseEdit.value.status) && !caseEdit.value.resolution_note.trim()) {
    window.alert('结案或排除风险前必须填写处理依据。'); return
  }
  savingCase.value = true
  try {
    await api.patch(`/ai/warnings/${editingCase.value.id}/`, caseEdit.value)
    caseDialogVisible.value = false
    await refreshAll()
  } catch (e) { window.alert(extractError(e, '保存核查结果失败，请稍后重试。')) }
  finally { savingCase.value = false }
}
onMounted(() => { window.addEventListener('resize', onWindowResize); void refreshAll() })
</script>

<style scoped>
.ai-center{--ai-blue:#0A2463;--ai-primary:#2F6BFF;--ai-border:#E5E7EB;--ai-muted:#667085;font-family:inherit;color:#1D2939;max-width:100%;padding:2px 0 26px}
.ai-header{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:14px}.ai-eyebrow{display:flex;align-items:center;gap:8px;font-size:12px;color:#62718A;margin-bottom:5px}.ai-accent{width:4px;height:14px;background:var(--ai-primary);border-radius:3px}.ai-header h1{margin:0;font-size:22px;line-height:1.5;font-weight:700;color:#142D51}.ai-header p{font-size:12px;color:#8A99AB;margin:3px 0 0}.ai-header-actions{display:flex;align-items:center;gap:9px}.ai-term{font-size:12px;font-weight:600;color:#2354A3;background:#F0F5FF;padding:11px 13px;border:1px solid #E3EAFA;border-radius:8px}.ai-btn{cursor:pointer;border-radius:8px;padding:10px 14px;white-space:nowrap;font-size:12px;font-weight:600;transition:background .15s}.ai-btn-ghost{border:1px solid #DEE5EE;background:#fff;color:#294E87}.ai-btn-ghost:hover{background:#F6F9FF}.ai-btn-primary{color:white;border:1px solid #214590;background:#214590}.ai-btn-primary:hover{background:#3161B6}.ai-btn:disabled{opacity:.6;cursor:not-allowed}.ai-btn-small{padding:7px 10px}
.ai-banner{display:flex;align-items:center;gap:9px;background:#EEF4FF;color:#49648F;border-radius:8px;font-size:12px;padding:12px 15px;margin-bottom:16px;line-height:1.5}.ai-indicator{flex:none;width:7px;height:7px;border-radius:100%;background:#A1AEC0}.ai-indicator.is-on{background:#10B981}.ai-indicator.is-off{background:#D59A25}
.ai-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:16px}.ai-kpi{display:flex;flex-direction:column;gap:5px;min-width:0;padding:18px 19px;border:1px solid var(--ai-border);background:white;border-radius:10px}.ai-kpi>span{font-size:12px;color:#8D9AAC}.ai-kpi strong{font-size:27px;line-height:1.4;color:#1D2939;font-variant-numeric:tabular-nums}.ai-kpi small{color:#98A3B3;font-size:11px;line-height:1.45}
.ai-panel{min-width:0;border:1px solid var(--ai-border);background:#fff;border-radius:10px;padding:19px;margin-bottom:16px}.ai-panel-head{display:flex;justify-content:space-between;align-items:start;gap:10px;margin-bottom:16px}.ai-panel-head h2{font-size:16px;color:#182C4C;margin:0;line-height:1.5;font-weight:700}.ai-panel-head p{font-size:11px;color:#92A0B3;margin:4px 0 0}.ai-tag{font-size:10px;background:#EEF4FF;border-radius:7px;color:#3665AE;padding:5px 8px;white-space:nowrap}.ai-main-grid{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(360px,1fr);gap:16px}.ai-chat-panel,.ai-warning-panel{min-height:560px;display:flex;flex-direction:column}.ai-prompts{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}.ai-prompt{background:#F6F9FE;border:1px solid #E6EDF8;color:#41618F;border-radius:7px;cursor:pointer;text-align:left;padding:7px 10px;font-size:11px}.ai-prompt:hover{border-color:#86AFFF;color:#2355A1}.ai-conversation{height:320px;overflow-y:auto;border:1px solid #EFF2F7;border-radius:9px;background:#FCFDFE;padding:12px;margin-bottom:12px}.ai-chat-empty{display:flex;justify-content:center;align-items:center;text-align:center;flex-direction:column;height:100%;padding:24px;color:#7B8BA4}.ai-chat-symbol{border:2px solid #CFDFFB;background:#EFF5FF;border-radius:50%;height:42px;width:42px;line-height:39px;color:#4779C7;font-size:23px;font-weight:700}.ai-chat-empty h3{font-size:14px;color:#566A88;margin:14px 0 5px}.ai-chat-empty p{font-size:12px;line-height:1.8;max-width:390px}.ai-message{display:flex;align-items:flex-start;gap:9px;margin-bottom:14px}.ai-message-avatar{flex:none;border-radius:8px;width:27px;height:27px;line-height:27px;background:#E9F0FF;text-align:center;font-size:11px;color:#2F62B5;font-weight:700}.ai-message-user .ai-message-avatar{background:#E9EDF4;color:#445570}.ai-bubble{max-width:calc(100% - 37px);padding:11px 12px;border-radius:9px;background:#EFF5FF;line-height:1.75}.ai-message-user .ai-bubble{background:#F0F2F5}.ai-message-content{font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere}.ai-message-meta{display:flex;flex-wrap:wrap;gap:8px;font-size:10px;color:#8A99B2;margin-top:8px}.ai-answer-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:9px}.ai-inline-link{background:transparent;border:0;padding:3px;color:#265BB7;font-size:11px;cursor:pointer;font-weight:600;text-align:left}.ai-inline-link:hover{text-decoration:underline}.ai-chat-working{font-size:12px;color:#7187A8;padding:10px}.ai-chat-form{border:1px solid #E3E9F1;border-radius:8px;padding:9px}.ai-chat-form textarea{display:block;resize:vertical;min-height:44px;width:100%;border:0;outline:0;font:inherit;font-size:12px;color:#30405B;background:transparent}.ai-chat-footer{display:flex;gap:10px;align-items:center;justify-content:space-between}.ai-chat-footer span{font-size:10px;color:#9AA6B7}
.ai-warning-list{flex:1;min-height:0;max-height:440px;overflow:auto}.ai-risk{border:1px solid #EEF1F6;background:#FBFCFE;padding:12px;border-radius:8px;margin-bottom:8px}.ai-risk-top{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:10px;color:#98A4B6;margin-bottom:8px}.ai-risk-severity{font-size:10px;padding:3px 6px;background:#FFF4E8;color:#B86A17;border-radius:4px}.ai-risk-severity.high{background:#FFF0F0;color:#CD4242}.ai-risk strong{font-size:12px;color:#253955}.ai-risk p{font-size:11px;color:#6D7C92;line-height:1.65;margin:6px 0}.ai-risk-foot{display:flex;align-items:center;justify-content:space-between;border-top:1px solid #EEF1F6;padding-top:7px;color:#91A0B6;font-size:10px;gap:10px}.ai-warning-actions{padding-top:12px;border-top:1px solid #EEF1F6;margin-top:10px}.ai-extra-note{font-size:11px;color:#8D99AB}.ai-state{padding:25px 14px;border-radius:8px;background:#F9FBFE;color:#8D9AAF;text-align:center;font-size:12px;line-height:1.7}.ai-small-state{margin-top:10px}
.ai-analysis-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.ai-mini-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.ai-mini-metrics>div{padding:13px;background:#F7F9FD;border-radius:8px}.ai-mini-metrics span{display:block;font-size:11px;color:#8392AB}.ai-mini-metrics strong{display:block;font-size:22px;margin-top:7px;color:#294777}.ai-explanation{font-size:11px;color:#6B7E99;line-height:1.7;background:#F6F9FE;padding:10px;border-radius:8px}.ai-score-table-wrap{overflow-x:auto}.ai-table{width:100%;border-collapse:collapse;text-align:left;font-size:12px;white-space:nowrap}.ai-table th{color:#8390A6;background:#F5F7FB;padding:10px 12px;font-weight:600}.ai-table td{border-bottom:1px solid #F0F2F5;padding:11px 12px;color:#3B4B67}.ai-table td strong{display:block;font-size:12px;white-space:normal;min-width:150px}.ai-table td small{display:block;font-size:10px;color:#9AA5B5;margin-top:3px}.ai-running-items{display:flex;flex-direction:column;gap:8px}.ai-running-items>div{display:flex;align-items:center;gap:8px;padding:12px;border:1px solid #EFF2F7;border-radius:8px}.ai-running-items span{font-size:12px;color:#60728F;flex:1}.ai-running-items strong{font-size:18px;color:#243E6C;white-space:nowrap}.ai-running-items button{font-size:11px;color:#2560BF;background:#F0F5FF;border:0;cursor:pointer;border-radius:5px;padding:6px;white-space:nowrap}.ai-source-disclaimer{font-size:11px;line-height:1.65;color:#8798AE;margin-top:13px}.ai-case-controls{display:flex;gap:9px;align-items:center}.ai-case-controls select{border:1px solid #DDE5F0;color:#344967;background:white;padding:8px 9px;font-size:12px;border-radius:7px}.ai-case-table{min-width:760px}.ai-case-status{background:#EFF4FD;color:#486DA4;border-radius:5px;padding:5px 8px;font-size:10px}.ai-table-empty{text-align:center;color:#95A3B9!important;padding:30px!important}.ai-notes{background:#F7F9FC;border:1px solid #E9EFF7;border-radius:8px;padding:15px 18px;color:#687B99}.ai-notes strong{font-size:12px;color:#344964}.ai-notes p{margin:7px 0 0;font-size:11px;line-height:1.6}.ai-case-dialog{display:flex;flex-direction:column;gap:13px}.ai-case-dialog>strong{color:#203D63}.ai-case-dialog p{font-size:12px;color:#718098;line-height:1.7}.ai-case-dialog label{font-size:12px;color:#536884;display:flex;flex-direction:column;gap:7px}.ai-case-dialog input,.ai-case-dialog select,.ai-case-dialog textarea{border:1px solid #DDE4EE;padding:9px;border-radius:7px;font:inherit;color:#334D6E;resize:vertical}.ai-muted{font-size:11px;color:#97A2B4}.ai-case-dialog+div{display:flex;gap:8px}
@media(max-width:1250px){.ai-main-grid{grid-template-columns:1fr}.ai-warning-panel{min-height:0}.ai-warning-list{max-height:350px}.ai-analysis-grid{grid-template-columns:1fr}}@media(max-width:800px){.ai-kpis{grid-template-columns:repeat(2,1fr)}.ai-header{align-items:start;flex-direction:column}.ai-chat-footer{flex-wrap:wrap}}@media(max-width:540px){.ai-kpis{grid-template-columns:1fr 1fr;gap:8px}.ai-kpi{padding:12px}.ai-header-actions{flex-wrap:wrap}.ai-panel{padding:14px}.ai-mini-metrics{gap:5px}.ai-mini-metrics>div{padding:9px}.ai-mini-metrics strong{font-size:17px}.ai-case-controls{flex-wrap:wrap}}

/* 真实数据可视化：仅在后端返回可核验数据时显示 */
.ai-chart-block{margin:0 0 14px;padding:12px;border:1px solid #E8EEF7;border-radius:9px;background:#FBFCFF}
.ai-chart-heading{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:7px;flex-wrap:wrap}
.ai-chart-heading strong{font-size:12px;color:#284569;font-weight:650}
.ai-chart-heading span{font-size:10px;color:#94A2B7;line-height:1.5}
.ai-risk-chart{height:172px;min-width:0;width:100%}
.ai-score-chart{height:204px;min-width:0;width:100%}
.ai-chart-footnote{font-size:10px;line-height:1.65;color:#90A0B4;margin:5px 0 0}
.ai-chart-no-sample{margin:10px 0}
.ai-coverage{padding:12px 12px 8px;background:#F9FBFE;border:1px solid #E9EFF8;border-radius:8px;margin-top:13px}
.ai-coverage-row{margin-bottom:11px}
.ai-coverage-label{display:flex;justify-content:space-between;align-items:center;color:#617594;font-size:11px;margin:8px 0 5px}
.ai-coverage-label b{color:#244F94;font-weight:650;font-size:11px;font-variant-numeric:tabular-nums}
.ai-coverage-track{height:6px;background:#E8EEF8;border-radius:6px;overflow:hidden}
.ai-coverage-track>span{display:block;height:100%;background:linear-gradient(90deg,#2F6BCE,#76A7F5);border-radius:6px;transition:width .25s ease}
.ai-coverage-row small{font-size:10px;color:#97A4B8;display:block;margin-top:5px}
.ai-case-progress{margin:-2px 0 15px;border-radius:9px;background:#F8FAFE;border:1px solid #E9EFF8;padding:12px 14px}
.ai-case-progress-head{display:flex;justify-content:space-between;align-items:center;gap:10px;color:#7A89A2;font-size:11px;margin-bottom:10px;flex-wrap:wrap}
.ai-case-progress-head strong{font-size:12px;color:#29476C}
.ai-case-progress-track{display:flex;height:9px;border-radius:7px;overflow:hidden;background:#E7EDF7;width:100%}
.ai-case-progress-track>span{display:block;height:100%;min-width:0;transition:width .25s ease}
.ai-case-progress-legend{display:flex;gap:12px;flex-wrap:wrap;margin-top:10px;font-size:10px;color:#74859D}
.ai-case-progress-legend span{display:flex;align-items:center;gap:5px}
.ai-case-progress-legend i{width:8px;height:8px;border-radius:3px;display:inline-block}
.ai-cases-footer{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:12px;color:#8292A9;font-size:11px}
.ai-source-active{color:#A56517;font-size:11px}
.ai-source-cleared{color:#188066;font-size:11px}
.ai-source-note{padding:9px 10px;background:#F4F7FC;border-radius:6px}
/* 仅使用Vue文本插值渲染模型内容，不注入HTML。 */
.ai-conversation{height:clamp(360px,48vh,520px)}
.ai-message-assistant .ai-bubble{min-width:0;width:100%}
.ai-rich-answer{font-size:13px;line-height:1.85;color:#30405B;white-space:normal}
.ai-rich-answer h3{font-size:14px;font-weight:700;color:#1D447D;line-height:1.55;margin:14px 0 6px}
.ai-rich-answer p{white-space:pre-wrap;margin:0 0 8px}
.ai-rich-answer ul,.ai-rich-answer ol{margin:4px 0 10px;padding-left:1.6em;list-style-position:outside}
.ai-rich-answer ul{list-style-type:disc}.ai-rich-answer ol{list-style-type:decimal}
.ai-rich-answer li{margin:4px 0;white-space:pre-wrap}
.ai-rich-answer strong{font-weight:700;color:#213B64}
.ai-rich-answer>:first-child{margin-top:0}.ai-rich-answer>:last-child{margin-bottom:0}
.ai-message-meta{line-height:1.6;border-top:1px solid #DDE7F5;padding-top:8px}
.ai-prompt:disabled{opacity:.55;cursor:not-allowed}
/* 深度成绩分析与原页面使用同一蓝白配色；不新增页面和图表依赖。 */
.ai-grade-metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:12px 0}
.ai-grade-metrics>div{background:#F7F9FD;border:1px solid #EAF0F8;border-radius:8px;padding:10px;min-width:0}
.ai-grade-metrics span,.ai-grade-metrics small{display:block;color:#7488A5;font-size:11px;line-height:1.55;overflow-wrap:anywhere}
.ai-grade-metrics strong{display:block;color:#294777;font-size:19px;margin:5px 0;font-variant-numeric:tabular-nums}
.ai-grade-band{display:grid;grid-template-columns:66px minmax(0,1fr) 60px 52px;gap:8px;align-items:center;margin:11px 0;font-size:11px;color:#60728F}
.ai-grade-band b,.ai-grade-band small{text-align:right;font-size:11px;white-space:nowrap;font-variant-numeric:tabular-nums}
.ai-grade-track{height:12px;background:#E9EFF8;border-radius:4px;overflow:hidden}.ai-grade-track>div{height:100%;background:#4B83E5;border-radius:4px}
.ai-grade-student{display:grid;gap:5px;padding:11px;background:#F6F9FE;border-radius:8px;font-size:12px;color:#405A7F;line-height:1.65;margin-bottom:15px}.ai-grade-student small{color:#788BA7;font-size:11px}
.ai-course-heading{margin-top:12px}.ai-grade-table th,.ai-grade-table td{padding:9px 7px;font-size:11px}.ai-grade-table td:first-child{white-space:normal;min-width:85px}
@media(max-width:540px){.ai-grade-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.ai-grade-band{grid-template-columns:56px minmax(0,1fr) 53px 45px;gap:4px}}

/* 独立业务分区：仅改变其他模块的外层布局与视觉层级，不改变其内容和行为。 */
.ai-center{background:#f4f7fb;padding:18px 16px 26px;border-radius:12px;box-sizing:border-box}
.ai-section-nav{display:flex;gap:8px;flex-wrap:wrap;padding:10px;background:#fff;border:1px solid #dce5f0;border-radius:10px;margin:18px 0 22px}
.ai-section-nav button{flex:1 1 150px;text-align:left;display:flex;align-items:center;gap:10px;min-height:42px;border:1px solid #e3eaf5;background:#f8faff;border-radius:7px;color:#24466f;font-size:13px;font-weight:600;cursor:pointer;padding:8px 12px}
.ai-section-nav button span{color:#5074a7;font-size:11px;font-variant-numeric:tabular-nums}.ai-section-nav button:hover,.ai-section-nav button:focus-visible{border-color:#477bc9;background:#edf4ff}
.ai-zone{border:1px solid #d6e0ee;border-radius:12px;background:#fff;margin-bottom:22px;overflow:visible;scroll-margin-top:92px;min-width:0}
.ai-zone-heading{display:flex;gap:12px;align-items:center;background:#edf3fb;border-bottom:1px solid #d6e0ee;border-radius:11px 11px 0 0;padding:16px 19px}
.ai-zone-number{display:grid;place-items:center;width:38px;height:38px;background:#163c78;color:white;font-size:15px;font-weight:700;border-radius:8px;flex:none;font-variant-numeric:tabular-nums}
.ai-zone-heading h2{font-size:17px;font-weight:700;margin:0;color:#16345e;line-height:1.4}.ai-zone-heading p{font-size:12px;color:#657b98;margin:4px 0 0}
.ai-zone>.ai-panel{border:0;border-radius:0 0 11px 11px;margin:0;padding:20px;min-height:0}.ai-zone>.ai-panel+.ai-panel{border-top:1px solid #dce5f0;border-radius:0 0 11px 11px}
.ai-zone .ai-panel-head{padding-bottom:12px;border-bottom:1px solid #e4ebf4;margin-bottom:16px}.ai-zone .ai-panel-head h2{font-size:15px}.ai-zone .ai-panel-head p{color:#6b809c}.ai-zone .ai-warning-list{flex:initial}.ai-case-panel{scroll-margin-top:92px}
.ai-op-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:16px}.ai-op-kpis>div{padding:13px 14px;background:#f4f8fe;border:1px solid #e0e9f5;border-radius:8px;min-width:0}.ai-op-kpis span,.ai-op-kpis small,.ai-op-pair span{display:block;font-size:12px;color:#637b9b;line-height:1.5}.ai-op-kpis strong{display:block;color:#244c86;font-size:25px;margin:5px 0;font-variant-numeric:tabular-nums}.ai-op-kpis small{font-size:11px}
.ai-op-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;align-items:start}.ai-op-card{padding:15px;border:1px solid #dfe7f2;background:#fcfdff;border-radius:9px;min-width:0}.ai-op-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:12px}.ai-op-head h3,.ai-op-check-heading h3{margin:0;font-size:14px;color:#25476f;font-weight:700}.ai-op-head>span,.ai-op-check-heading span{font-size:11px;color:#6d819a}.ai-op-pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:10px}.ai-op-pair>div{background:#f0f5fc;border-radius:7px;padding:9px 10px}.ai-op-pair strong{font-size:20px;font-weight:700;color:#294e82;display:block;margin-top:4px;font-variant-numeric:tabular-nums}.ai-op-distribution{display:flex;flex-wrap:wrap;gap:6px;margin:9px 0;color:#45678f;font-size:11px}.ai-op-distribution span{padding:5px 8px;border-radius:5px;background:#eaf1fb}.ai-op-table-wrap{overflow:auto}.ai-op-table td,.ai-op-table th{padding:8px 10px}.ai-op-table td:first-child{white-space:normal}.ai-op-util{padding:11px 0;margin-bottom:10px}.ai-op-util>span{display:block;color:#637b9b;font-size:12px}.ai-op-util>strong{display:block;color:#214a86;font-size:28px;margin:4px 0}.ai-op-util>small{display:block;font-size:11px;color:#637b9b;margin:7px 0}.ai-op-track{height:10px;border-radius:5px;background:#e6edf8;overflow:hidden}.ai-op-track>div{height:100%;background:#4279cd;border-radius:5px}.ai-op-bars{display:grid;gap:10px;margin:12px 0}.ai-op-bar{display:grid;grid-template-columns:44px minmax(0,1fr) 55px;gap:9px;align-items:center;font-size:12px;color:#617592}.ai-op-bar b{text-align:right;font-weight:600}.ai-op-date{grid-template-columns:84px minmax(0,1fr) 48px}.ai-op-check-heading{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:20px 0 12px;padding-top:15px;border-top:1px solid #e1e8f3}.ai-op-check-grid .ai-coverage{margin:0}.ai-op-check-grid .ai-running-items{min-width:0}
@media(max-width:1100px){.ai-op-grid{grid-template-columns:1fr}.ai-op-kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:540px){.ai-center{padding:10px 6px}.ai-zone>.ai-panel{padding:12px}.ai-zone-heading{padding:12px}.ai-op-kpis{gap:6px}.ai-op-kpis>div{padding:9px}.ai-op-kpis strong{font-size:20px}.ai-op-check-heading{align-items:flex-start;flex-direction:column}.ai-zone .ai-running-items>div{flex-wrap:wrap}.ai-section-nav button{flex-basis:120px}}

.ai-history-kpis{margin-bottom:10px}.ai-history-content{display:grid;gap:12px}.ai-history-chart,.ai-history-course{border:1px solid #e1e9f4;border-radius:9px;padding:14px;background:#f9fbfe}.ai-history-subhead{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;color:#274873;font-size:14px;margin:4px 0 12px}.ai-history-subhead small,.ai-history-subhead label{font-size:12px;color:#637b9b}.ai-history-subhead select{max-width:100%;border:1px solid #d7e3f3;background:#fff;color:#274873;padding:6px 8px;border-radius:5px;font-size:12px}.ai-history-bar-row{display:grid;grid-template-columns:minmax(130px,210px) minmax(50px,1fr) 90px;align-items:center;gap:12px;margin:12px 0;color:#294777;font-size:13px}.ai-history-bar-row small,.ai-history-table td small{display:block;margin-top:4px;color:#7588a4;font-size:11px}.ai-history-bar-row>strong{text-align:right}.ai-history-no-value{background:#f1f4f8}.ai-history-table-wrap{overflow:auto;max-width:100%}.ai-history-table{width:100%;min-width:760px}.ai-history-table th,.ai-history-table td{white-space:nowrap;padding:10px 12px}.ai-history-info{background:#fff8ea;border:1px solid #eee1c4;color:#79581c;border-radius:7px;padding:12px;margin:10px 0;font-size:13px;line-height:1.6}.ai-history-alert{color:#a15a12;font-weight:600}.ai-history-table td:first-child{white-space:normal;min-width:125px}.ai-history-content .ai-source-disclaimer{margin:2px 0 8px}
@media(max-width:600px){.ai-history-bar-row{grid-template-columns:minmax(90px,120px) minmax(40px,1fr) 62px;gap:6px;font-size:11px}.ai-history-subhead label{display:flex;flex-wrap:wrap;gap:5px;align-items:center}}
.ai-replay-actions{display:flex;gap:8px;flex-wrap:wrap}.ai-replay-empty{padding:30px;text-align:center;color:#7186a3;background:#f7f9fc;border-radius:8px}.ai-replay-kpis{margin:12px 0}.ai-replay-eval{display:grid;grid-template-columns:1.2fr 1fr;gap:18px;margin:15px 0}.ai-replay-eval>div{padding:14px;border:1px solid #e1e9f4;border-radius:8px;background:#f9fbfe;min-width:0}.ai-replay-metrics{grid-template-columns:repeat(3,minmax(0,1fr));margin-top:12px}.ai-replay-metrics strong{font-size:18px}.ai-replay-eval table{margin-top:12px}@media(max-width:800px){.ai-replay-eval{grid-template-columns:1fr}}

/* Final presentation pass: preserve all calculations, actions and data scope. */
.ai-section-nav{scroll-margin-top:92px;margin:14px 0 18px;padding:8px;gap:6px}
.ai-section-nav button{min-height:38px;flex:1 1 128px;padding:7px 10px}
.ai-zone{margin-bottom:18px}.ai-zone-heading{padding:12px 18px}.ai-zone-heading>div{flex:1;min-width:0}
.ai-zone-number{width:34px;height:34px}.ai-zone-heading h2{font-size:17px}.ai-zone-heading p{margin-top:2px}
.ai-zone-return{flex:none;background:transparent;color:#315b92;border:1px solid #cbd9eb;border-radius:6px;padding:6px 9px;font-size:11px;cursor:pointer;white-space:nowrap}
.ai-zone-return:hover,.ai-zone-return:focus-visible{background:#fff;border-color:#477bc9}
.ai-zone>.ai-panel{padding:16px 18px}.ai-zone .ai-panel-head{padding-bottom:10px;margin-bottom:12px;align-items:center;flex-wrap:wrap}
.ai-kpi>span,.ai-kpi small,.ai-source-disclaimer,.ai-chart-footnote,.ai-chart-heading span{color:#63758e}
.ai-notes summary{font-size:13px;font-weight:650;color:#344964;cursor:pointer;line-height:1.6}
.ai-notes[open] summary{margin-bottom:8px}.ai-replay-eval{align-items:start}
@media(max-width:540px){.ai-zone>.ai-panel{padding:12px}.ai-zone-heading{padding:10px 12px;gap:8px}.ai-zone-return{padding:5px 6px}.ai-zone-heading h2{font-size:15px}.ai-zone-heading p{font-size:11px}.ai-zone .ai-panel-head{align-items:flex-start}}
</style>
