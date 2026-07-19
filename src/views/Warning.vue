<template>
  <div class="warning-page">
    <div class="page-header">
      <h2>智能预警系统</h2>
      <p>实时监控学院各项数据指标，智能预警异常情况</p>
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
import { ref, reactive, computed } from 'vue'

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
  emergency: 2,
  warning: 3,
  normal: 15,
  resolved: 28
})

// 预警数据
const warnings = ref([
  {
    id: 1,
    level: 'danger',
    typeName: '预算执行预警',
    time: '10分钟前',
    title: '科研经费预算执行率偏低',
    description: '目前科研经费预算执行率为76%，低于预期目标（85%）。建议加快项目执行进度，确保资金合理使用。',
    suggestion: '1. 梳理各项目执行进度，识别滞后环节\n2. 召开项目进度推进会，明确时间节点\n3. 对执行率低于70%的项目进行重点督导',
    metrics: [
      { label: '当前值', value: '76%', status: 'danger' },
      { label: '目标值', value: '85%', status: '' },
      { label: '偏差', value: '-9%', status: 'danger' }
    ],
    processed: false,
    hasAI: true
  },
  {
    id: 2,
    level: 'warning',
    typeName: '招生趋势预警',
    time: '30分钟前',
    title: '部分专业报名人数呈下降趋势',
    description: '国际政治专业今年报名人数同比去年下降12%，需关注招生宣传策略调整。',
    suggestion: '1. 加强线上招生宣传，拓展新媒体渠道\n2. 组织优秀在校生回母校宣讲\n3. 优化专业介绍材料，突出就业优势',
    metrics: [
      { label: '去年人数', value: '120', status: '' },
      { label: '今年人数', value: '106', status: '' },
      { label: '变化', value: '-12%', status: 'warning' }
    ],
    processed: false,
    hasAI: true
  },
  {
    id: 3,
    level: 'warning',
    typeName: '师资结构预警',
    time: '2小时前',
    title: '青年教师比例偏低',
    description: '35岁以下青年教师占比为25%，建议加强青年人才引进和培养。',
    suggestion: '1. 制定青年人才引进专项计划\n2. 加大海内外优秀博士招聘力度\n3. 完善青年教师培养和晋升机制',
    metrics: [
      { label: '青年教师', value: '33人', status: '' },
      { label: '总教师', value: '130人', status: '' },
      { label: '占比', value: '25%', status: 'warning' }
    ],
    processed: false,
    hasAI: true
  },
  {
    id: 4,
    level: 'info',
    typeName: '数据更新提醒',
    time: '2小时前',
    title: '学生数据已更新',
    description: '最新学生数据已同步，建议查看最新分析报告。',
    suggestion: '建议前往综合概览页面查看最新的学生数据分析报告。',
    metrics: [
      { label: '更新内容', value: '学生数据', status: '' },
      { label: '数据范围', value: '全部年级', status: '' },
      { label: '状态', value: '已完成', status: '' }
    ],
    processed: false,
    hasAI: false,
    detailBtnText: '查看数据',
    processBtnText: '标记已读'
  },
  {
    id: 5,
    level: 'info',
    typeName: '系统提醒',
    time: '5小时前',
    title: '月度报告生成完成',
    description: '2026年5月学院综合分析报告已生成，可在科研管理系统中查看。',
    suggestion: '建议前往科研管理系统查看完整的月度分析报告。',
    metrics: [
      { label: '报告月份', value: '2026年5月', status: '' },
      { label: '数据维度', value: '教学/科研/师资', status: '' },
      { label: '状态', value: '可查看', status: '' }
    ],
    processed: false,
    hasAI: false,
    detailBtnText: '查看报告',
    processBtnText: '标记已读'
  }
])

const activeWarnings = computed(() => warnings.value.filter(w => !w.processed))

const historyList = ref([
  { id: 1, title: '教学工作量统计完成', description: '本学期教师教学工作量数据已全部统计完成', time: '昨天 14:30', handler: '系统自动' },
  { id: 2, title: '科研经费到账提醒', description: '3项国家级项目经费已到账，总额520万元', time: '2天前 09:15', handler: '陈科研' },
  { id: 3, title: '学生评教数据更新', description: '本学期中期学生评教数据已同步完成', time: '3天前 16:45', handler: '王教务' },
  { id: 4, title: '实验室安全巡检完成', description: '本月实验室安全巡检已全部完成，无异常', time: '5天前 11:20', handler: '系统自动' },
  { id: 5, title: '毕业论文查重结果', description: '2026届本科毕业论文查重工作已完成，通过率98%', time: '1周前 15:00', handler: '王教务' }
])

// 指标监控数据
const metrics = ref([
  { name: '预算执行率', value: '76%', percent: 76, barColor: 'danger', status: '偏低', statusLabel: '偏低', lowLabel: '低 <75%', highLabel: '高 >90%' },
  { name: '师生比', value: '15.4:1', percent: 75, barColor: 'success', status: '正常', statusLabel: '正常', lowLabel: '低 <10:1', highLabel: '高 >20:1' },
  { name: '科研项目完成率', value: '88%', percent: 88, barColor: 'success', status: '良好', statusLabel: '良好', lowLabel: '低 <70%', highLabel: '高 >95%' },
  { name: '就业率', value: '92%', percent: 92, barColor: 'success', status: '优秀', statusLabel: '优秀', lowLabel: '低 <85%', highLabel: '高 >95%' }
])

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

const updateStats = () => {
  const unresolved = warnings.value.filter(w => !w.processed)
  stats.emergency = unresolved.filter(w => w.level === 'danger').length
  stats.warning = unresolved.filter(w => w.level === 'warning').length
  stats.normal = unresolved.filter(w => w.level === 'info').length
  stats.resolved = warnings.value.filter(w => w.processed).length
}

// AI分析
const showAI = ref(false)
const aiItem = ref(null)
const aiLoading = ref(false)
const aiResult = ref('')

const aiAnalysis = (item) => {
  aiItem.value = item
  showAI.value = true
  aiLoading.value = true
  aiResult.value = ''

  const mockResults = {
    '科研经费预算执行率偏低': '经AI分析，当前科研经费预算执行率76%低于目标值85%，主要问题集中在以下方面：\n\n1. 3个国家级项目执行进度滞后，仅完成60%，涉及经费约180万元\n2. 横向课题到账周期延长，平均到账周期从45天延长至62天\n3. 部分项目负责人同时承担多项任务，精力分散\n\n建议：优先推进执行率低于70%的项目，设立月度进度检查机制。',
    '部分专业报名人数呈下降趋势': '经AI分析，国际政治专业报名人数下降12%主要原因：\n\n1. 近三年就业数据显示，该专业对口就业率下降5个百分点\n2. 同类院校该专业招生规模扩大，竞争加剧\n3. 新媒体宣传投入不足，影响力有限\n\n建议：加大线上宣传投入，突出学院在国际事务领域的独特优势。',
    '青年教师比例偏低': '经AI分析，青年教师占比25%偏低的原因及建议：\n\n1. 近三年引进博士15人，但同期退休教师8人，净增仅7人\n2. 与同类985高校相比，引进待遇竞争力不足\n3. 青年人才成长通道有待完善\n\n建议：设立青年人才引进专项基金，提供有竞争力的科研启动经费。'
  }

  setTimeout(() => {
    aiResult.value = mockResults[item.title] || `正在对「${item.title}」进行智能分析...\n\n该预警涉及多项指标，AI建议结合历史数据进行趋势研判，并及时采取应对措施。`
    aiLoading.value = false
  }, 1500)
}

const regenerateAI = () => {
  aiLoading.value = true
  aiResult.value = ''
  setTimeout(() => {
    aiResult.value = `（重新分析结果）经AI深度分析，「${aiItem.value?.title}」相关数据已更新，建议持续关注指标变化并采取相应措施。`
    aiLoading.value = false
  }, 1200)
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
  grid-template-columns: repeat(4, 1fr);
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
