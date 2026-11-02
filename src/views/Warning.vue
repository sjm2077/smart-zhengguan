<template>
  <div class="warning-page">
    <div class="page-header">
      <h2>智能预警系统</h2>
      <p>实时监控学院各项数据指标，智能预警异常情况</p>
      <p class="source-note">
        数据分级：<b>A 官网真实</b>（pspa.sdu.edu.cn 定时爬取） · <b>B 真实采集文件</b>（研究生 Excel / 论文 CSV） ·
        <b>C 子系统演示台账</b>（科研模拟脚本生成，非官网口径）。每条预警标注来源，官网无公开口径的指标不做编造。
      </p>
    </div>

    <div class="kpi-overview">
      <div class="kpi-card warning-card">
        <div class="kpi-icon">🔴</div>
        <div class="kpi-info">
          <div class="kpi-label">紧急预警</div>
          <div class="kpi-value">{{ stats.emergency }}</div>
        </div>
      </div>
      <div class="kpi-card caution-card">
        <div class="kpi-icon">🟡</div>
        <div class="kpi-info">
          <div class="kpi-label">关注提醒</div>
          <div class="kpi-value">{{ stats.warning }}</div>
        </div>
      </div>
      <div class="kpi-card normal-card">
        <div class="kpi-icon">🟢</div>
        <div class="kpi-info">
          <div class="kpi-label">正常指标</div>
          <div class="kpi-value">{{ stats.normal }}</div>
        </div>
      </div>
      <div class="kpi-card info-card">
        <div class="kpi-icon">🔵</div>
        <div class="kpi-info">
          <div class="kpi-label">已处理</div>
          <div class="kpi-value">{{ stats.resolved }}</div>
        </div>
      </div>
    </div>

    <div class="warning-section">
      <div class="section-title">
        <span class="title-icon">⚠️</span>
        <span>当前预警</span>
        <span class="section-count">（{{ activeWarnings.length }} 条）</span>
      </div>
      <div class="warning-list">
        <div
          v-for="item in activeWarnings"
          :key="item.id"
          class="warning-item"
          :class="item.level"
        >
          <div class="warning-header">
            <div class="warning-type">
              <span class="type-badge" :class="item.level">{{ levelLabel(item.level) }}</span>
              <span class="type-name">{{ item.typeName }}</span>
              <span class="warning-source">{{ item.source || '未标注来源' }}</span>
            </div>
            <span class="warning-time">{{ item.time }}</span>
          </div>
          <div class="warning-content">
            <div class="warning-title">{{ item.title }}</div>
            <div class="warning-desc">{{ item.description }}</div>
            <div class="warning-metrics">
              <div v-for="m in item.metrics" :key="m.label" class="metric">
                <span class="metric-label">{{ m.label }}</span>
                <span class="metric-value" :class="m.status">{{ m.value }}</span>
              </div>
            </div>
            <div class="warning-actions">
              <button class="action-btn primary" @click="viewDetail(item)">
                {{ item.detailBtnText || '查看详情' }}
              </button>
              <button
                class="action-btn"
                :class="{ processed: item.processed }"
                @click="markProcessed(item)"
              >
                {{ item.processed ? '已处理 ✓' : (item.processBtnText || '标记处理') }}
              </button>
              <button v-if="item.hasAI" class="action-btn ai" @click="aiAnalysis(item)">
                AI分析
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="metrics-section">
      <div class="section-title">
        <span class="title-icon">📊</span>
        <span>预警指标监控</span>
      </div>
      <div class="metrics-grid">
        <div v-for="m in metrics" :key="m.name" class="metric-card">
          <div class="metric-header">
            <span class="metric-name">{{ m.name }}</span>
            <span class="metric-status" :class="m.status">{{ m.statusLabel }}</span>
          </div>
          <div class="metric-value">{{ m.value }}</div>
          <div class="metric-bar">
            <div
              class="bar-fill"
              :class="m.barColor"
              :style="{ width: m.percent + '%' }"
            ></div>
          </div>
          <div class="metric-range">
            <span class="low">{{ m.lowLabel }}</span>
            <span class="high">{{ m.highLabel }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 官网《学院简介》权威指标（学院自己公布的口径） ===== -->
    <div class="metrics-section official-section">
      <div class="section-title">
        <span class="title-icon">🏛️</span>
        <span>官网权威指标（《学院简介》原文）</span>
        <span class="section-count">
          {{ profileLoading ? '（读取中…）' : `（${profileItems.length} 项，来源 pspa.sdu.edu.cn/xygk/xyjj.htm）` }}
        </span>
      </div>
      <p v-if="profileError" class="official-error">{{ profileError }}</p>
      <div class="official-grid">
        <div v-for="it in profileItems" :key="it.key" class="official-card" :title="it.raw">
          <div class="official-label">{{ it.label }}</div>
          <div class="official-value">
            {{ formatNum(it.value) }}<span class="official-unit">{{ it.unit }}</span>
          </div>
          <div class="official-raw">{{ it.raw }}</div>
        </div>
      </div>
    </div>

    <div class="history-section">
      <div class="section-title">
        <span class="title-icon">📜</span>
        <span>预警历史</span>
        <span class="section-count">（{{ historyList.length }} 条）</span>
      </div>
      <div class="history-list">
        <div
          v-for="item in historyList"
          :key="item.id"
          class="history-item resolved"
        >
          <div class="history-icon">✅</div>
          <div class="history-content">
            <div class="history-title">{{ item.title }}</div>
            <div class="history-desc">{{ item.description }}</div>
            <div class="history-time">{{ item.time }} · 由 {{ item.handler }} 处理</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== 详情弹窗 ===== -->
    <Teleport to="body">
      <div v-if="showDetail" class="dialog-overlay" @click.self="showDetail = false">
        <div class="dialog-box">
          <div class="dialog-header">
            <h3>{{ detailItem?.title }}</h3>
            <button class="dialog-close" @click="showDetail = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="dialog-body">
            <div class="detail-section">
              <div class="detail-label">预警类型</div>
              <div class="detail-value">
                <span class="type-badge" :class="detailItem?.level">{{ levelLabel(detailItem?.level) }}</span>
                {{ detailItem?.typeName }}
              </div>
            </div>
            <div class="detail-section">
              <div class="detail-label">预警描述</div>
              <div class="detail-value">{{ detailItem?.description }}</div>
            </div>
            <div class="detail-section">
              <div class="detail-label">详细数据</div>
              <div class="detail-metrics">
                <div v-for="m in detailItem?.metrics" :key="m.label" class="detail-metric">
                  <span class="dm-label">{{ m.label }}</span>
                  <span class="dm-value" :class="m.status">{{ m.value }}</span>
                </div>
              </div>
            </div>
            <div class="detail-section">
              <div class="detail-label">建议措施</div>
              <div class="detail-value suggestion">{{ detailItem?.suggestion }}</div>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="form-btn cancel" @click="showDetail = false">关闭</button>
            <button v-if="!detailItem?.processed" class="form-btn submit" @click="markFromDetail">
              标记处理
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ===== AI分析弹窗 ===== -->
    <Teleport to="body">
      <div v-if="showAI" class="dialog-overlay" @click.self="showAI = false">
        <div class="dialog-box ai-dialog">
          <div class="dialog-header">
            <h3>🤖 AI 智能分析</h3>
            <button class="dialog-close" @click="showAI = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </button>
          </div>
          <div class="dialog-body">
            <div class="ai-query-label">正在分析：<strong>{{ aiItem?.title }}</strong></div>
            <div class="ai-result-box">
              <div v-if="aiLoading" class="ai-loading">
                <span class="ai-spinner"></span>
                <span>AI 正在分析数据，请稍候...</span>
              </div>
              <div v-else class="ai-result">
                <div class="ai-text">{{ aiResult }}</div>
              </div>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="form-btn cancel" @click="showAI = false">关闭</button>
            <button class="form-btn submit" :disabled="aiLoading" @click="regenerateAI">
              {{ aiLoading ? '分析中...' : '重新分析' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Toast -->
    <Teleport to="body">
      <transition name="toast-fade">
        <div v-if="toast.show" class="toast" :class="toast.type">
          <span>{{ toast.message }}</span>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'

const toast = ref({ show: false, message: '' })
let toastTimer = null

const showToast = (msg) => {
  if (toastTimer) clearTimeout(toastTimer)
  toast.value = { show: true, message: msg }
  toastTimer = setTimeout(() => { toast.value.show = false }, 2000)
}

const levelLabel = (level) => {
  const map = { danger: '紧急', warning: '警告', info: '信息' }
  return map[level] || level
}

// 统计
const stats = reactive({
  emergency: 0,
  warning: 0,
  normal: 0,
  resolved: 0
})

// 预警数据（从真实 API 动态生成）
const warnings = ref([])

const activeWarnings = computed(() => warnings.value.filter(w => !w.processed))

const historyList = ref([])

// 指标监控数据（全部由下方规则从真实接口回填，初始只占位、不写死数值）
const metrics = ref([
  { key: 'fund', name: '经费执行率（科研系统）', value: '--', percent: 0, barColor: 'success', status: '加载中', statusLabel: '加载中', lowLabel: '低于 50% 预警', highLabel: '目标 ≥90%' },
  { key: 'score', name: '教师平均综合分（科研系统）', value: '--', percent: 0, barColor: 'success', status: '加载中', statusLabel: '加载中', lowLabel: '低 <75', highLabel: '优 >85' },
  { key: 'project', name: '官网近五年项目', value: '--', percent: 0, barColor: 'info', status: '', statusLabel: '', lowLabel: '重大+社科+国自然+部委', highLabel: '等待官网指标' },
  { key: 'achv', name: '官网学术成果', value: '--', percent: 0, barColor: 'info', status: '', statusLabel: '', lowLabel: '官网学术成果页', highLabel: '等待官网指标' },
  { key: 'profile', name: '官网教师主页覆盖率', value: '--', percent: 0, barColor: 'info', status: '', statusLabel: '', lowLabel: '个人主页可检索', highLabel: '目标 ≥90%' },
  { key: 'notice', name: '官网通知公告采集', value: '--', percent: 0, barColor: 'info', status: '', statusLabel: '', lowLabel: '通知公告栏目', highLabel: '等待官网指标' }
])

const setMetric = (key, patch) => {
  const m = metrics.value.find(x => x.key === key)
  if (m) Object.assign(m, patch)
}

// 官网《学院简介》权威指标（真实原文，不含任何估算）
const profileItems = ref([])
const profileError = ref('')
const profileLoading = ref(true)
const formatNum = (v) => (v === null || v === undefined ? '--' : (Number.isInteger(v) ? v : v.toFixed(1)))

const loadProfileStats = async () => {
  profileLoading.value = true
  profileError.value = ''
  try {
    const r = await fetch('/api-research/api/real/pspa-profile')
    if (!r.ok) throw new Error('HTTP ' + r.status)
    const d = await r.json()
    profileItems.value = d.items || []
    const derived = d.derived || {}

    setMetric('project', {
      value: (derived.project_total || 0) + ' 项',
      percent: Math.min(100, Math.round(derived.project_total || 0)),
      highLabel: `官网合计 ${derived.project_total || 0} 项`,
      status: '正常',
      statusLabel: '官网口径'
    })
    setMetric('notice', {
      highLabel: '官网通知公告栏目持续采集'
    })

    historyList.value = [
      { id: 'h1', title: '智能预警系统启动', description: '接入科研库（MySQL 8888）、研究生库（MySQL 8000）与学院官网爬取数据，规则引擎按接口数据实时计算', time: '系统启动', handler: '系统自动' },
      { id: 'h2', title: '官网权威指标已加载', description: `《学院简介》原文指标 ${profileItems.value.length} 项：在职教师 ${formatNum(d.data?.teacher_total)} 人、教授 ${formatNum(d.data?.teacher_professor)} 人、博导 ${formatNum(d.data?.supervisor_phd)} 人、近五年项目 ${formatNum(derived.project_total)} 项`, time: '数据初始化', handler: '系统自动' },
      { id: 'h3', title: '预警规则引擎生效', description: '项目进度、经费执行率、官网学术成果、官网项目、官网通知、师资评分、教师主页覆盖率共 7 条规则按真实接口数据计算', time: '数据初始化', handler: '系统自动' }
    ]
  } catch (e) {
    profileError.value = '官网权威指标加载失败（需启动科研后端 8888）'
    historyList.value = [
      { id: 'h1', title: '智能预警系统启动', description: '规则引擎已启动，后端接口不可用时不会编造任何指标', time: '系统启动', handler: '系统自动' }
    ]
  } finally {
    profileLoading.value = false
  }
}

// ==================== 真实数据驱动的规则引擎 ====================
let nextId = 100
const addWarning = (w) => {
  warnings.value.push({ id: nextId++, processed: false, hasAI: true, time: '刚刚', ...w })
  updateStats()
}

const updateStats = () => {
  const unresolved = warnings.value.filter(w => !w.processed)
  stats.emergency = unresolved.filter(w => w.level === 'danger').length
  stats.warning = unresolved.filter(w => w.level === 'warning').length
  stats.normal = unresolved.filter(w => w.level === 'info').length
  stats.resolved = warnings.value.filter(w => w.processed).length
}

// 规则1：项目进度预警（科研系统项目台账；注意：该表由模拟数据脚本生成，
// 属"子系统数据"，不是学院官方口径）
async function ruleProjectProgress() {
  try {
    const r = await fetch('/api-research/api/admin/risk-projects')
    if (!r.ok) return
    const data = await r.json()
    const risky = data.data || []
    risky.forEach(p => {
      const level = p.progress < 30 ? 'danger' : 'warning'
      addWarning({
        level,
        typeName: level === 'danger' ? '项目进度严重滞后' : '项目进度预警',
        source: 'C 科研子系统台账（模拟脚本）',
        title: `项目「${p.project_name}」进度 ${p.progress}%`,
        description: `负责人 ${p.leader} 的项目「${p.project_name}」当前执行进度仅 ${p.progress}%，距计划完成率（80%）存在较大差距。（数据来源：科研系统项目台账，为演示用模拟台账，非官网口径）`,
        suggestion: `1. 立即联系负责人 ${p.leader} 了解滞后原因\n2. 制定两周内追赶计划\n3. 如涉及经费使用问题，同步启动经费督导`,
        metrics: [
          { label: '项目编号', value: p.project_no, status: '' },
          { label: '当前进度', value: p.progress + '%', status: level },
          { label: '状态', value: p.status, status: '' },
          { label: '截止日期', value: p.end_date, status: '' },
        ]
      })
    })
  } catch (e) { /* silent */ }
}

// 规则2：经费执行率预警（真实数据：项目进度加权执行率）
async function ruleFundExecution() {
  try {
    const r = await fetch('/api-research/api/fund/overview')
    if (!r.ok) return
    const d = await r.json()
    // execution_rate  = 全部项目进度加权执行率
    // ongoing_rate    = 在研项目进度加权执行率（更应关注）
    const rate = d.execution_rate || 0
    const ongoingRate = d.ongoing_rate || 0
    const ongoingCount = d.ongoing_count || 0
    const ongoingFund = d.ongoing_fund || 0
    const executed = d.executed_amount || 0

    let level = 'info', label = '良好', barColor = 'success'
    if (rate < 50) { level = 'danger'; label = '偏低'; barColor = 'danger' }
    else if (rate < 70) { level = 'warning'; label = '偏低'; barColor = 'warning' }
    else if (rate >= 90) { label = '优秀'; barColor = 'info' }

    setMetric('fund', {
      name: '经费执行率（科研系统）',
      value: rate.toFixed(1) + '%',
      percent: Math.round(Math.min(rate, 100)),
      barColor,
      status: label,
      statusLabel: label,
      lowLabel: `在研 ${ongoingCount} 项仅 ${ongoingRate.toFixed(1)}%`,
      highLabel: '目标 ≥90%'
    })

    addWarning({
      level,
      typeName: level === 'info' ? '经费执行良好' : '经费执行预警',
      source: 'C 科研子系统台账（模拟脚本）',
      title: `科研经费进度加权执行率 ${rate.toFixed(1)}%，在研项目仅 ${ongoingRate.toFixed(1)}%`,
      description: `全部 ${d.project_count} 个项目预算合计 ${Number(d.total_amount).toFixed(0)} 万元，按项目进度折算已执行 ${Number(executed).toFixed(0)} 万元，执行率 ${rate.toFixed(1)}%。其中在研 ${ongoingCount} 个项目执行率仅 ${ongoingRate.toFixed(1)}%，是拉低整体执行率的主因。（口径：项目进度加权，FundDetail 记录的是经费分配而非支出流水；数据来源科研系统模拟台账）`,
      suggestion: `1. 重点督导在研项目（${ongoingCount} 个，经费 ${Number(ongoingFund).toFixed(0)} 万元）执行进度\n2. 召开项目进度推进会，明确时间节点\n3. 对进度低于 30% 的项目挂账督办\n4. 已结题 ${d.finished_count} 个项目及时完成经费决算`,
      metrics: [
        { label: '整体执行率', value: rate.toFixed(1) + '%', status: level },
        { label: '在研执行率', value: ongoingRate.toFixed(1) + '%', status: 'danger' },
        { label: '已执行', value: Number(executed).toFixed(0) + '万', status: '' },
        { label: '预算总额', value: Number(d.total_amount).toFixed(0) + '万', status: '' },
      ],
      detailBtnText: '查看项目',
    })
  } catch (e) { /* silent */ }
}

// 规则3：官网学术成果动态（爬虫采集 pspa-achievement，真实页面数据）
async function rulePaperUpdate() {
  try {
    const r = await fetch('/api-research/api/real/pspa-achievements?limit=3')
    if (!r.ok) return
    const d = await r.json()
    const list = d.data || []
    const total = d.total || 0

    // 官网成果页当前可采集上限按 500 条作为进度展示基准，实际条数以接口 total 为准
    setMetric('achv', {
      value: total + ' 条',
      percent: Math.min(100, Math.round(total / 5)),
      highLabel: `采集进度（基准 500 条）`,
      status: '正常',
      statusLabel: '官网口径'
    })

    if (list.length > 0) {
      const latest = list[0]
      addWarning({
        level: 'info',
        typeName: '官网学术成果',
        source: 'A 官网学术成果页',
        title: `官网学术成果最新收录：${(latest.title || '').slice(0, 40)}`,
        description: `学院官网「学术成果」栏目已采集 ${total} 条真实记录，最新一条类别为「${latest.category || '未分类'}」，发布日期 ${latest.date || '未标注'}。`,
        suggestion: `1. 关注学院最新科研成果，及时做成果宣传\n2. 鼓励教师围绕优势方向持续产出\n3. 每 6 小时定时重采，保持官网数据同步`,
        metrics: [
          { label: '累计采集', value: total + ' 条', status: '' },
          { label: '成果类别', value: latest.category || '未分类', status: '' },
          { label: '发布日期', value: latest.date || '-', status: '' },
        ],
        detailBtnText: '查看成果',
        processBtnText: '标记已读',
      })
    }
  } catch (e) { /* silent */ }
}

// 规则4a：官网科研项目（学院简介原文：重大攻关/国家社科/国自然/部委项目）
async function ruleProjectCount() {
  try {
    const r = await fetch('/api-research/api/real/pspa-profile')
    if (!r.ok) return
    const d = await r.json()
    const p = d.data || {}
    const derived = d.derived || {}
    const total = derived.project_total || 0

    setMetric('project', {
      value: total + ' 项',
      percent: Math.min(100, Math.round(total)),
      highLabel: `官网合计 ${total} 项`,
      status: '正常',
      statusLabel: '官网口径'
    })

    addWarning({
      level: 'info',
      typeName: '官网科研项目',
      source: 'A 官网《学院简介》',
      title: `学院官网公布近五年承担科研项目 ${total} 项，总经费 ${p.fund_total || 0} 万元`,
      description: `官网《学院简介》原文：承担国家社科基金重大项目、教育部重大攻关项目 ${p.project_major || 0} 余项，国家社科基金各类项目 ${p.project_nssf || 0} 余项，国家自然科学基金项目 ${p.project_nsfc || 0} 余项，其他部委各类项目 ${p.project_ministry || 0} 多项，总项目经费六千余万元。`,
      suggestion: '1. 以官网口径作为对外汇报基准，内部项目台账另作明细\n2. 关注重大/国自然项目占比，优化项目结构\n3. 定期核对官网数据与内部台账差异',
      metrics: [
        { label: '重大攻关', value: (p.project_major || 0) + ' 项', status: '' },
        { label: '国家社科', value: (p.project_nssf || 0) + ' 项', status: '' },
        { label: '国自然', value: (p.project_nsfc || 0) + ' 项', status: '' },
        { label: '总经费', value: (p.fund_total || 0) + ' 万', status: '' },
      ],
      processBtnText: '标记已读',
    })
  } catch (e) { /* silent */ }
}

// 规则4b：官网通知公告（爬虫采集，最新一条即“待关注”事项）
async function ruleNoticeUpdate() {
  try {
    const r = await fetch('/api-research/api/real/pspa-notices?limit=1')
    if (!r.ok) return
    const d = await r.json()
    const list = d.data || []
    const total = d.total || 0
    if (!list.length) return
    const latest = list[0]
    setMetric('notice', {
      value: total + ' 条',
      percent: Math.min(100, Math.round(total / 10)),
      status: '正常',
      statusLabel: '官网口径',
      lowLabel: `最新 ${latest.date || '未标注'}`,
      highLabel: `官网栏目累计 ${total} 条`
    })
    addWarning({
      level: 'info',
      typeName: '官网通知公告',
      source: 'A 官网通知公告',
      title: `官网最新通知：${(latest.title || '').slice(0, 46)}`,
      description: `学院官网通知公告栏目已采集 ${total} 条，最新一条发布于 ${latest.date || '未标注'}。请及时查看是否涉及本平台业务（教学、科研、人事、研究生）。`,
      suggestion: '1. 打开原文核对通知要求与截止时间\n2. 涉及数据报送的，同步到对应业务子系统\n3. 保持每 6 小时定时采集',
      metrics: [
        { label: '累计采集', value: total + ' 条', status: '' },
        { label: '发布日期', value: latest.date || '-', status: '' },
        { label: '来源', value: 'pspa.sdu.edu.cn', status: '' },
      ],
      detailBtnText: '查看通知',
      processBtnText: '标记已读',
    })
  } catch (e) { /* silent */ }
}

// 规则5：教师平均综合分（数据来源科研系统 TeacherScore，模拟台账）
async function ruleTeacherScore() {
  try {
    const r = await fetch('/api-research/api/real/overview')
    if (!r.ok) return
    const d = await r.json()
    const avg = d.avg_sum_score || 0
    const teacherCount = d.teacher_count || 0
    const cnpapers = d.cnki_count || 0

    setMetric('score', {
      name: '教师平均综合分（科研系统）',
      value: avg.toFixed(1),
      percent: Math.round(Math.min(avg, 100)),
      barColor: avg >= 85 ? 'success' : avg >= 75 ? 'warning' : 'danger',
      status: avg >= 85 ? '优秀' : avg >= 75 ? '良好' : '偏低',
      statusLabel: avg >= 85 ? '优秀' : avg >= 75 ? '良好' : '偏低',
      lowLabel: `${teacherCount} 人 · CNKI ${cnpapers} 篇`,
      highLabel: '优秀线 ≥85'
    })

    if (avg < 80) {
      addWarning({
        level: 'warning',
        typeName: '师资发展',
        source: 'C 科研子系统评分（模拟台账）',
        title: `教师平均综合分 ${avg.toFixed(1)}，低于优秀线（85）`,
        description: `${teacherCount} 名教师综合评分均值 ${avg.toFixed(1)}，近 ${cnpapers} 篇CNKI论文。建议关注低分教师发展支持。`,
        suggestion: '1. 对综合分低于70的教师进行一对一访谈\n2. 制定差异化发展计划\n3. 加强导师指导和团队建设',
        metrics: [
          { label: '教师数', value: teacherCount + ' 人', status: '' },
          { label: '平均综合分', value: avg.toFixed(1), status: 'warning' },
          { label: 'CNKI论文', value: cnpapers + ' 篇', status: '' },
        ],
      })
    } else {
      addWarning({
        level: 'info',
        typeName: '师资发展',
        source: 'C 科研子系统评分（模拟台账）',
        title: `教师平均综合分 ${avg.toFixed(1)}，整体良好`,
        description: `${teacherCount} 名教师综合评分均值 ${avg.toFixed(1)}，师资队伍整体呈现上升态势。`,
        suggestion: '继续保持，鼓励优秀教师发挥传帮带作用。',
        metrics: [
          { label: '教师数', value: teacherCount + ' 人', status: '' },
          { label: '平均综合分', value: avg.toFixed(1), status: '' },
        ],
        processBtnText: '标记已读',
      })
    }
  } catch (e) { /* silent */ }
}

// 规则6：官网教师主页覆盖率（真实：PspaTeacher 93 人 vs 个人主页可检索 88 人）
async function ruleProfileCoverage() {
  try {
    const r = await fetch('/api-research/api/real/pspa-faculty-portrait')
    if (!r.ok) return
    const d = await r.json()
    const o = d.overall || {}
    const total = o.teacher_count || 0
    const profiled = o.profile_count || 0
    if (!total) return
    const rate = (profiled / total) * 100
    const level = rate < 85 ? 'warning' : 'info'

    setMetric('profile', {
      value: rate.toFixed(1) + '%',
      percent: Math.round(Math.min(rate, 100)),
      barColor: rate < 85 ? 'warning' : 'success',
      status: rate < 85 ? '偏低' : '正常',
      statusLabel: rate < 85 ? '偏低' : '正常',
      lowLabel: `个人主页可检索 ${profiled} 人`,
      highLabel: `官网教师名录 ${total} 人`
    })

    addWarning({
      level,
      typeName: '官网数据完整性',
      source: 'A 官网教师名录 + 个人主页',
      title: `官网教师主页覆盖率 ${rate.toFixed(1)}%（${profiled}/${total} 人）`,
      description: `学院官网教师名录共采集 ${total} 名在职教师，其中 ${profiled} 人可检索到个人主页详细信息（职称、研究方向、成果）。另有 ${total - profiled} 人仅有名录条目，画像与词云分析会缺少这部分信息。`,
      suggestion: `1. 核对缺少主页的 ${Math.max(0, total - profiled)} 名教师，确认官网是否已发布主页\n2. 画像与词云分析中对该部分教师标注“信息待补充”\n3. 保持每 6 小时增量重采，主页发布后自动入库`,
      metrics: [
        { label: '教师名录', value: total + ' 人', status: '' },
        { label: '可检索主页', value: profiled + ' 人', status: '' },
        { label: '覆盖率', value: rate.toFixed(1) + '%', status: level === 'warning' ? 'warning' : '' },
      ],
      processBtnText: '标记已读',
    })
  } catch (e) { /* silent */ }
}

// ==================== 初始化 ====================
async function loadRealWarnings() {
  // 官网权威指标与规则并行加载
  await Promise.allSettled([
    loadProfileStats(),
    ruleProjectProgress(),
    ruleFundExecution(),
    rulePaperUpdate(),
    ruleProjectCount(),
    ruleNoticeUpdate(),
    ruleTeacherScore(),
    ruleProfileCoverage(),
  ])
  // 兜底：如果所有 API 都挂了（比如后端没启动），至少给出明确提示，不编造预警
  if (warnings.value.length === 0) {
    warnings.value = [
      { id: 1, level: 'danger', typeName: '服务离线', source: '系统状态', time: '系统离线', processed: false, hasAI: true,
        title: '后端服务未启动，无法获取真实数据',
        description: '请先启动科研后端（8888端口）和研究生后端（8000端口），系统将自动接入真实数据。',
        suggestion: '1. 启动科研后端: cd research_system && python manage.py runserver 8888\n2. 启动研究生后端: cd smartzhengguan/.../backend && python manage.py runserver 8000',
        metrics: [
          { label: '状态', value: '后端离线', status: 'danger' },
          { label: '影响范围', value: '全部预警', status: '' },
        ]
      },
      { id: 2, level: 'info', typeName: '数据来源说明', source: '系统说明', time: '系统离线', processed: false, hasAI: false,
        title: '当前为离线演示模式',
        description: '当后端服务不可用时，预警系统进入离线演示模式。启动后端后所有预警、指标将基于真实数据库数据生成。',
        suggestion: '启动后端服务后刷新页面即可看到真实数据驱动的智能预警。',
        metrics: [
          { label: '模式', value: '离线演示', status: '' },
          { label: '数据', value: '等待接入', status: '' },
        ],
        processBtnText: '标记已读',
      }
    ]
    updateStats()
  }
}

onMounted(loadRealWarnings)

// 详情弹窗
const showDetail = ref(false)
const detailItem = ref(null)

const viewDetail = (item) => {
  detailItem.value = item
  showDetail.value = true
}

const markFromDetail = () => {
  if (detailItem.value) {
    detailItem.value.processed = true
    const raw = warnings.value.find(w => w.id === detailItem.value.id)
    if (raw) raw.processed = true
    updateStats()
  }
  showDetail.value = false
  showToast('✅ 已标记处理')
}

// 标记处理
const markProcessed = (item) => {
  item.processed = true
  updateStats()
  showToast('✅ 已标记处理')
}

// AI分析
const showAI = ref(false)
const aiItem = ref(null)
const aiLoading = ref(false)
const aiResult = ref('')

// 用预警自身的真实指标构造提问，交给后端 AI 代理（Key 只在服务端）
function buildAIPrompt(item) {
  const metricLines = (item.metrics || [])
    .map(m => `- ${m.label}：${m.value}`)
    .join('\n')
  return `【预警类型】${item.typeName}
【预警标题】${item.title}
【现状描述】${item.description}
【关键指标】
${metricLines}

请基于以上真实业务数据，给出：1）问题成因分析（分点）；2）可执行的处置建议（分点，明确责任与时间）；3）后续需持续监控的指标。控制在 400 字以内，直接输出中文正文，不要客套话。`
}

const SYSTEM_PROMPT = '你是高校科研管理数据分析助手，擅长根据真实业务指标做归因分析和给出可落地的管理建议。回答务实、具体、分点，避免空话。'

// 本地兜底分析（后端不可用或 AI 调用失败时，仍基于真实指标给出结构化结论）
function localAnalysis(item) {
  const m = item.metrics || []
  const lines = m.map(x => `${x.label}：${x.value}`).join('、')
  return `【成因分析】
当前预警为「${item.title}」。已知真实指标：${lines}。
从数据看，主要矛盾集中在指标值与预期目标之间的差距，且与其他关联指标存在联动，需要结合项目执行节奏综合判断。

【处置建议】
1. 由科研管理部门牵头，梳理涉及的项目/教师清单，明确到人。
2. 对差距最大的对象设置两周内追赶节点，纳入月度进度检查。
3. 涉及经费与进度的，同步启动经费督导流程。

【持续监控】
建议持续跟踪上述指标变化，并在下一周期复核是否收敛。

（说明：当前为本地规则生成的兜底分析，接入 AI 代理后可获得更深入的归因）`
}

async function runAI(item) {
  aiLoading.value = true
  aiResult.value = ''
  try {
    const resp = await fetch('/api-grad/v1/chat-proxy/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        system_prompt: SYSTEM_PROMPT,
        message: buildAIPrompt(item),
      }),
    })
    if (!resp.ok) throw new Error('proxy ' + resp.status)
    const data = await resp.json()
    const content = (data.content || '').trim()
    aiResult.value = content || localAnalysis(item)
  } catch (e) {
    aiResult.value = localAnalysis(item)
  } finally {
    aiLoading.value = false
  }
}

const aiAnalysis = (item) => {
  aiItem.value = item
  showAI.value = true
  runAI(item)
}

const regenerateAI = () => {
  if (aiItem.value) runAI(aiItem.value)
}
</script>

<style scoped>
.warning-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 10px;
}

.page-header h2 {
  font-size: 28px;
  color: #fff;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-header p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.page-header .source-note {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.42);
  line-height: 1.6;
}

.page-header .source-note b {
  color: rgba(0, 212, 255, 0.75);
  font-weight: 600;
}

.warning-source {
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  white-space: nowrap;
}

/* 官网权威指标 */
.official-section .section-count {
  font-size: 12px;
}

.official-error {
  font-size: 13px;
  color: #ff7875;
  margin-bottom: 12px;
}

.official-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.official-card {
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid rgba(0, 212, 255, 0.18);
  background: rgba(0, 212, 255, 0.04);
}

.official-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 6px;
}

.official-value {
  font-size: 24px;
  font-weight: 700;
  color: #00d4ff;
}

.official-unit {
  font-size: 12px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  margin-left: 4px;
}

.official-raw {
  margin-top: 6px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* KPI */
.kpi-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.kpi-card {
  padding: 20px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  display: flex;
  align-items: center;
  gap: 16px;
}

.kpi-card.warning-card { border-color: rgba(255, 77, 79, 0.4); }
.kpi-card.caution-card { border-color: rgba(250, 173, 20, 0.4); }
.kpi-card.normal-card { border-color: rgba(82, 196, 26, 0.4); }
.kpi-card.info-card { border-color: rgba(0, 212, 255, 0.4); }

.kpi-icon { font-size: 36px; }
.kpi-info { flex: 1; }
.kpi-label { font-size: 13px; color: rgba(255, 255, 255, 0.6); margin-bottom: 4px; }
.kpi-value { font-size: 28px; font-weight: 700; color: #fff; }
.warning-card .kpi-value { color: #ff4d4f; }
.caution-card .kpi-value { color: #faad14; }
.normal-card .kpi-value { color: #52c41a; }
.info-card .kpi-value { color: #00d4ff; }

/* Section */
.warning-section,
.metrics-section,
.history-section {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  padding: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 18px;
  color: #fff;
  font-weight: 600;
}

.section-count {
  font-size: 13px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.4);
}

.title-icon { font-size: 20px; }

/* Warning list */
.warning-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.warning-item {
  padding: 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.3s;
}

.warning-item.danger {
  border-color: rgba(255, 77, 79, 0.4);
  background: rgba(255, 77, 79, 0.05);
}

.warning-item.warning {
  border-color: rgba(250, 173, 20, 0.4);
  background: rgba(250, 173, 20, 0.05);
}

.warning-item.info {
  border-color: rgba(0, 212, 255, 0.4);
  background: rgba(0, 212, 255, 0.05);
}

.warning-item.danger:hover { border-color: rgba(255, 77, 79, 0.7); }
.warning-item.warning:hover { border-color: rgba(250, 173, 20, 0.7); }
.warning-item.info:hover { border-color: rgba(0, 212, 255, 0.7); }

.warning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.warning-type {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.type-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.type-badge.danger { background: rgba(255, 77, 79, 0.2); color: #ff4d4f; }
.type-badge.warning { background: rgba(250, 173, 20, 0.2); color: #faad14; }
.type-badge.info { background: rgba(0, 212, 255, 0.2); color: #00d4ff; }

.type-name { color: rgba(255, 255, 255, 0.8); font-size: 14px; }
.warning-time { font-size: 12px; color: rgba(255, 255, 255, 0.4); }
.warning-content { flex: 1; }
.warning-title { font-size: 16px; color: #fff; font-weight: 600; margin-bottom: 8px; }
.warning-desc { font-size: 14px; color: rgba(255, 255, 255, 0.7); line-height: 1.6; margin-bottom: 16px; }

.warning-metrics {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.metric { display: flex; flex-direction: column; gap: 4px; }
.metric-label { font-size: 12px; color: rgba(255, 255, 255, 0.5); }
.metric-value { font-size: 16px; font-weight: 600; color: #fff; }
.metric-value.danger { color: #ff4d4f; }
.metric-value.warning { color: #faad14; }

.warning-actions { display: flex; gap: 10px; }

.action-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  background: rgba(0, 212, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.5);
}

.action-btn.primary {
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border-color: transparent;
  color: #fff;
}

.action-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
}

.action-btn.processed {
  background: rgba(82, 196, 26, 0.15);
  border-color: rgba(82, 196, 26, 0.4);
  color: #52c41a;
  cursor: default;
}

.action-btn.ai {
  border-color: rgba(123, 44, 191, 0.5);
  background: rgba(123, 44, 191, 0.1);
  color: #a855f7;
}

.action-btn.ai:hover {
  background: rgba(123, 44, 191, 0.2);
  border-color: rgba(123, 44, 191, 0.7);
}

/* Metrics grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 16px;
}

.metric-card {
  padding: 20px;
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  background: rgba(0, 0, 0, 0.2);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.metric-name { font-size: 14px; color: rgba(255, 255, 255, 0.7); }

.metric-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 8px;
}

.metric-status.偏低 { background: rgba(255, 77, 79, 0.2); color: #ff4d4f; }
.metric-status.正常 { background: rgba(82, 196, 26, 0.2); color: #52c41a; }
.metric-status.良好 { background: rgba(24, 144, 255, 0.2); color: #1890ff; }
.metric-status.优秀 { background: rgba(123, 44, 191, 0.2); color: #7b2cbf; }

.metric-card .metric-value {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 12px;
}

.metric-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }
.bar-fill.danger { background: linear-gradient(90deg, #ff4d4f, #ff7875); }
.bar-fill.warning { background: linear-gradient(90deg, #faad14, #ffc53d); }
.bar-fill.success { background: linear-gradient(90deg, #52c41a, #73d13d); }
.bar-fill.info { background: linear-gradient(90deg, #00d4ff, #7b2cbf); }

.metric-range {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

/* History */
.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border: 1px solid rgba(82, 196, 26, 0.3);
  background: rgba(82, 196, 26, 0.03);
}

.history-icon { font-size: 24px; }
.history-content { flex: 1; }
.history-title { font-size: 14px; color: #fff; font-weight: 600; margin-bottom: 4px; }
.history-desc { font-size: 13px; color: rgba(255, 255, 255, 0.6); margin-bottom: 4px; }
.history-time { font-size: 12px; color: rgba(255, 255, 255, 0.4); }

/* ===== Dialog ===== */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-box {
  width: 520px;
  max-width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
  background: #0d2a5e;
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  animation: dialog-in 0.25s ease-out;
}

.ai-dialog {
  width: 600px;
}

@keyframes dialog-in {
  from { opacity: 0; transform: scale(0.92) translateY(20px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}

.dialog-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.dialog-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.2s;
}

.dialog-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.dialog-close svg { width: 18px; height: 18px; }

.dialog-body {
  padding: 20px 24px;
}

.detail-section {
  margin-bottom: 16px;
}

.detail-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.detail-value {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
}

.detail-value .type-badge {
  margin-right: 8px;
}

.detail-value.suggestion {
  white-space: pre-line;
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  color: rgba(255, 255, 255, 0.85);
}

.detail-metrics {
  display: flex;
  gap: 16px;
}

.detail-metric {
  flex: 1;
  text-align: center;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.dm-label { display: block; font-size: 12px; color: rgba(255, 255, 255, 0.5); margin-bottom: 4px; }
.dm-value { font-size: 20px; font-weight: 700; color: #fff; }
.dm-value.danger { color: #ff4d4f; }
.dm-value.warning { color: #faad14; }

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 0 24px 20px;
}

.form-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.form-btn.cancel {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.7);
}

.form-btn.cancel:hover { background: rgba(255, 255, 255, 0.1); }

.form-btn.submit {
  background: linear-gradient(135deg, #00d4ff, #0099cc);
  color: #fff;
}

.form-btn.submit:hover { box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3); }
.form-btn.submit:disabled { opacity: 0.5; cursor: not-allowed; }

/* AI Analysis */
.ai-query-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 16px;
  padding: 10px 14px;
  background: rgba(0, 212, 255, 0.06);
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.1);
}

.ai-query-label strong { color: #fff; }

.ai-result-box {
  min-height: 200px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  padding: 20px;
  border: 1px solid rgba(0, 212, 255, 0.08);
}

.ai-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 160px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.ai-spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(0, 212, 255, 0.15);
  border-top-color: #00d4ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.ai-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.8;
  white-space: pre-line;
}

/* Toast */
.toast {
  position: fixed;
  top: 30px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 28px;
  background: #1a3a1a;
  border: 1px solid rgba(82, 196, 26, 0.4);
  border-radius: 10px;
  font-size: 14px;
  color: #b7eb8f;
  font-weight: 500;
  z-index: 99999;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
}

.toast-fade-enter-active,
.toast-fade-leave-active { transition: all 0.3s ease; }
.toast-fade-enter-from,
.toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-20px); }

@media (max-width: 1200px) {
  .kpi-overview, .metrics-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 768px) {
  .kpi-overview, .metrics-grid { grid-template-columns: 1fr; }
  .warning-metrics { flex-wrap: wrap; }
  .warning-actions { flex-wrap: wrap; }
  .detail-metrics { flex-wrap: wrap; }
}
</style>
