<template>
  <div class="warning-center">
    <!-- ===== Layer 1: Warning KPI Cards (5-column, ~110px) ===== -->
    <div class="kpi-strip">
      <div class="kpi-card" v-for="kpi in kpiList" :key="kpi.label">
        <div class="kpi-inner">
          <span class="kpi-label">{{ kpi.label }}</span>
          <div class="kpi-value-row">
            <span class="kpi-number">{{ kpi.value }}</span>
            <span v-if="kpi.unit" class="kpi-unit">{{ kpi.unit }}</span>
            <span class="kpi-change" :class="kpi.up ? 'up' : 'down'">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline :points="kpi.up ? '18 15 12 9 6 15' : '6 9 12 15 18 9'"/></svg>
              {{ kpi.up ? '+' : '' }}{{ kpi.change }}%
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Layer 2: Academic Warning Trend + Risk Distribution ===== -->
    <div id="module-academic-risk" class="section-header">
      <h2 class="section-title">学业预警与风险分析</h2>
      <span class="section-subtitle">本学期 · 实时监控</span>
    </div>
    <div class="row-core">
      <!-- Left: 学业预警趋势折线图 -->
      <div class="core-left">
        <div class="panel panel--flex">
          <div id="module-risk-trend" class="panel-header">
            <h3 class="panel-title">各风险等级学生数量趋势</h3>
            <div class="legend-inline">
              <span v-for="l in trendLegend" :key="l.label" class="legend-dot" :style="{ background: l.color }"></span>
              <span class="legend-text">{{ trendLegend.map(l => l.label).join(' · ') }}</span>
            </div>
          </div>
          <div class="panel-chart" ref="trendRef"></div>
        </div>
      </div>
      <!-- Right: 风险等级分布饼图 -->
      <div class="core-right">
        <div class="panel panel--flex panel--hero">
          <div id="module-risk-distribution" class="panel-header">
            <h3 class="panel-title">当前风险等级分布</h3>
          </div>
          <div class="panel-chart panel-chart--lg" ref="pieRef"></div>
        </div>
      </div>
    </div>

    <!-- ===== Layer 3: College Ranking + Warning Student List ===== -->
    <div id="module-college-ranking" class="section-header">
      <h2 class="section-title">学院预警排行与重点学生</h2>
      <span class="section-subtitle">按风险程度排序</span>
    </div>
    <div class="row-half">
      <!-- Left: 学院预警排行柱状图 -->
      <div class="panel panel--flex">
          <div id="module-college-warning-ranking" class="panel-header">
            <h3 class="panel-title">各学院预警学生数量排行</h3>
        </div>
        <div class="panel-chart" ref="barRef"></div>
      </div>
      <!-- Right: 预警学生列表 -->
      <div class="panel panel--flex panel--student-list">
          <div id="module-key-warning-students" class="panel-header">
            <h3 class="panel-title">重点预警学生</h3>
          <span class="student-total">共 {{ warningStudents.length }} 人</span>
        </div>
        <div class="student-table-wrap">
          <table class="student-table">
            <thead>
              <tr>
                <th>学号</th>
                <th>姓名</th>
                <th>学院</th>
                <th>风险类型</th>
                <th>风险等级</th>
                <th>预警时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in warningStudents" :key="s.id">
                <td class="cell-id">{{ s.studentId }}</td>
                <td class="cell-name">{{ s.name }}</td>
                <td>{{ s.college }}</td>
                <td>{{ s.riskType }}</td>
                <td>
                  <span class="risk-tag" :class="'risk-' + s.riskLevel">{{ s.riskLevelLabel }}</span>
                </td>
                <td class="cell-time">{{ s.warnTime }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ===== Layer 4: Teaching Exception Events ===== -->
    <div id="module-exception-events" class="section-header">
      <h2 class="section-title">教学异常事件记录</h2>
      <span class="section-subtitle">近30天异常汇总</span>
    </div>
    <div class="row-exception">
      <div class="panel panel--flex">
          <div id="module-exception-list" class="panel-header">
            <h3 class="panel-title">异常事件列表</h3>
          <span class="exception-total">{{ exceptionEvents.length }} 项事件</span>
        </div>
        <div class="exception-list">
          <div v-for="e in exceptionEvents" :key="e.id" class="exception-item" :class="'exception-' + e.severity">
            <div class="exception-left">
              <span class="exception-tag" :class="'etag-' + e.severity">{{ e.severityLabel }}</span>
            </div>
            <div class="exception-body">
              <div class="exception-title">{{ e.title }}</div>
              <div class="exception-desc">{{ e.desc }}</div>
            </div>
            <div class="exception-right">
              <span class="exception-source">{{ e.source }}</span>
              <span class="exception-time">{{ e.time }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

// Chart refs
const trendRef = ref<HTMLElement | null>(null)
const pieRef = ref<HTMLElement | null>(null)
const barRef = ref<HTMLElement | null>(null)

let charts: echarts.ECharts[] = []

// ==================== KPI Data ====================
const kpiList = [
  { label: '当前预警学生数', value: '86', unit: '人', change: 5.2, up: false },
  { label: '挂科风险人数', value: '42', unit: '人', change: 3.8, up: false },
  { label: '出勤异常人数', value: '28', unit: '人', change: 2.1, up: false },
  { label: '学业预警率', value: '3.5', unit: '%', change: 0.8, up: false },
  { label: '已干预学生数', value: '58', unit: '人', change: 12.6, up: true },
]

// ==================== Trend Legend ====================
const trendLegend = [
  { label: '高风险', color: '#1E3A8A' },
  { label: '中风险', color: '#3B82F6' },
  { label: '低风险', color: '#93C5FD' },
]

// ==================== Warning Students ====================
const warningStudents = [
  { id: 1, studentId: '2023001042', name: '张明远', college: '行政管理学院', riskType: '挂科风险', riskLevel: 'high', riskLevelLabel: '高风险', warnTime: '06-24 14:30' },
  { id: 2, studentId: '2023002078', name: '李思雨', college: '政治学学院', riskType: '出勤异常', riskLevel: 'high', riskLevelLabel: '高风险', warnTime: '06-24 11:15' },
  { id: 3, studentId: '2022003156', name: '王晓峰', college: '国际政治学院', riskType: '挂科风险', riskLevel: 'high', riskLevelLabel: '高风险', warnTime: '06-23 16:42' },
  { id: 4, studentId: '2023004231', name: '赵思涵', college: '城市治理学院', riskType: '综合预警', riskLevel: 'mid', riskLevelLabel: '中风险', warnTime: '06-23 09:28' },
  { id: 5, studentId: '2022001008', name: '陈宇轩', college: '行政管理学院', riskType: '挂科风险', riskLevel: 'mid', riskLevelLabel: '中风险', warnTime: '06-22 15:10' },
  { id: 6, studentId: '2023003089', name: '刘芳菲', college: '公共政策学院', riskType: '出勤异常', riskLevel: 'mid', riskLevelLabel: '中风险', warnTime: '06-22 10:55' },
  { id: 7, studentId: '2022004155', name: '周子涵', college: '政治学学院', riskType: '挂科风险', riskLevel: 'mid', riskLevelLabel: '中风险', warnTime: '06-21 14:22' },
  { id: 8, studentId: '2023005012', name: '吴俊杰', college: '行政管理学院', riskType: '综合预警', riskLevel: 'low', riskLevelLabel: '低风险', warnTime: '06-21 08:45' },
  { id: 9, studentId: '2022002018', name: '郑雅文', college: '科社学院', riskType: '出勤异常', riskLevel: 'low', riskLevelLabel: '低风险', warnTime: '06-20 16:33' },
  { id: 10, studentId: '2023001033', name: '林浩然', college: '国际政治学院', riskType: '挂科风险', riskLevel: 'low', riskLevelLabel: '低风险', warnTime: '06-20 11:08' },
]

// ==================== Exception Events ====================
const exceptionEvents = [
  { id: 1, severity: 'critical', severityLabel: '严重', title: '《公共政策分析》课程挂科率超过25%', desc: '本学期选课人数120人，累计挂科31人，挂科率25.8%，超出学院预警线15%', source: '成绩系统', time: '06-25 10:22' },
  { id: 2, severity: 'critical', severityLabel: '严重', title: '行政管理学院3名学生连续缺课超过5次', desc: '2023级行政管理专业张明远、陈宇轩、吴俊杰连续缺勤，出勤率低于40%', source: '考勤系统', time: '06-24 16:45' },
  { id: 3, severity: 'critical', severityLabel: '严重', title: '《当代中国政治制度》教学满意度评分低于3.0', desc: '本学期评教得分2.85分，较上学期下降0.52分，需要教学院长关注', source: '评教系统', time: '06-24 09:30' },
  { id: 4, severity: 'warning', severityLabel: '警告', title: '国际政治学院体育课程免修申请激增', desc: '近两周共有14名学生申请免修，较去年同期增加8人，需关注学生体质健康状况', source: '教务系统', time: '06-23 14:15' },
  { id: 5, severity: 'warning', severityLabel: '警告', title: '城市治理学院毕业论文进度滞后预警', desc: '2022级共12名学生论文中期检查未通过，首批提交率仅68%', source: '论文系统', time: '06-22 11:50' },
  { id: 6, severity: 'warning', severityLabel: '警告', title: '公共政策学院研究生课程选课人数不足', desc: '《比较公共政策》选课仅5人，低于开课门槛8人标准', source: '教务系统', time: '06-21 15:38' },
  { id: 7, severity: 'info', severityLabel: '提示', title: '科社学院课堂互动率较上月提升12%', desc: '本月平均互动率78.5%，较上月66.2%有明显提升，教学质量改善趋势良好', source: '课堂分析', time: '06-20 10:05' },
  { id: 8, severity: 'info', severityLabel: '提示', title: '政治学学院自习室利用率连续3周超90%', desc: '期末复习阶段自习室日均使用率92%，建议动态扩容以满足学生需求', source: '资源监控', time: '06-19 17:22' },
]

// ==================== Init Charts ====================
function initTrend() {
  if (!trendRef.value) return
  const c = echarts.init(trendRef.value)
  c.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E5E7EB', textStyle: { color: '#1F2937', fontSize: 12 } },
    grid: { top: 20, right: 48, bottom: 28, left: 52 },
    xAxis: { type: 'category', data: ['第1周', '第4周', '第8周', '第12周', '第16周', '第20周'], axisLabel: { color: '#9CA3AF', fontSize: 11 }, axisLine: { lineStyle: { color: '#E5E7EB' } }, axisTick: { show: false } },
    yAxis: { type: 'value', name: '人数', nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, axisLabel: { color: '#9CA3AF', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }, min: 0 },
    series: [
      { name: '高风险', type: 'line', data: [18, 22, 25, 28, 26, 24], smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { color: '#1E3A8A', width: 2.5 }, itemStyle: { color: '#1E3A8A' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(30,58,138,0.10)' }, { offset: 1, color: 'rgba(30,58,138,0.0)' }]) } },
      { name: '中风险', type: 'line', data: [32, 35, 38, 42, 38, 36], smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { color: '#3B82F6', width: 2.5 }, itemStyle: { color: '#3B82F6' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(59,130,246,0.08)' }, { offset: 1, color: 'rgba(59,130,246,0.0)' }]) } },
      { name: '低风险', type: 'line', data: [45, 42, 36, 30, 28, 26], smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { color: '#93C5FD', width: 2.5 }, itemStyle: { color: '#93C5FD' }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(147,197,253,0.08)' }, { offset: 1, color: 'rgba(147,197,253,0.0)' }]) } },
    ],
  })
  charts.push(c)
}

function initPie() {
  if (!pieRef.value) return
  const c = echarts.init(pieRef.value)
  c.setOption({
    tooltip: { trigger: 'item', backgroundColor: '#fff', borderColor: '#E5E7EB', textStyle: { color: '#1F2937', fontSize: 12 }, formatter: '{b}: {c}人 ({d}%)' },
    series: [{
      type: 'pie', radius: ['55%', '78%'], center: ['50%', '50%'],
      label: { show: false },
      emphasis: { scaleSize: 6 },
      itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 4 },
      data: [
        { value: 24, name: '学业高风险', itemStyle: { color: '#1E3A8A' } },
        { value: 36, name: '学业中风险', itemStyle: { color: '#3B82F6' } },
        { value: 26, name: '学业低风险', itemStyle: { color: '#93C5FD' } },
        { value: 42, name: '出勤预警', itemStyle: { color: '#60A5FA' } },
        { value: 18, name: '挂科预警', itemStyle: { color: '#BFDBFE' } },
        { value: 12, name: '综合预警', itemStyle: { color: '#DBEAFE' } },
      ],
    }],
  })
  charts.push(c)
}

function initBar() {
  if (!barRef.value) return
  const c = echarts.init(barRef.value)
  const rawData = [
    { name: '行政管理学院', high: 8, mid: 14, low: 10 },
    { name: '政治学学院', high: 6, mid: 12, low: 8 },
    { name: '国际政治学院', high: 4, mid: 10, low: 7 },
    { name: '城市治理学院', high: 3, mid: 8, low: 6 },
    { name: '公共政策学院', high: 5, mid: 9, low: 5 },
    { name: '科社学院', high: 2, mid: 5, low: 4 },
  ]
  c.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E5E7EB', textStyle: { color: '#1F2937', fontSize: 12 }, axisPointer: { type: 'shadow' } },
    grid: { top: 16, right: 20, bottom: 28, left: 48 },
    xAxis: { type: 'category', data: rawData.map(d => d.name), axisLabel: { color: '#9CA3AF', fontSize: 10, rotate: 25 }, axisTick: { show: false }, axisLine: { lineStyle: { color: '#E5E7EB' } } },
    yAxis: { type: 'value', name: '人数', nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, axisLabel: { color: '#9CA3AF', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } } },
    series: [
      { name: '高风险', type: 'bar', stack: 'total', data: rawData.map(d => d.high), itemStyle: { color: '#1E3A8A' }, barWidth: 26 },
      { name: '中风险', type: 'bar', stack: 'total', data: rawData.map(d => d.mid), itemStyle: { color: '#3B82F6' } },
      { name: '低风险', type: 'bar', stack: 'total', data: rawData.map(d => d.low), itemStyle: { color: '#93C5FD', borderRadius: [4, 4, 0, 0] } },
    ],
  })
  charts.push(c)
}

// ==================== Lifecycle ====================
onMounted(async () => {
  await nextTick()
  initTrend()
  initPie()
  initBar()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  charts.forEach(c => c.dispose())
  charts = []
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  charts.forEach(c => c.resize?.())
}
</script>

<style lang="scss" scoped>
/* ============================================================
   WarningCenter — 教学预警中心
   设计方向：教学运行监控 · 学业预警分析
   气质：稳重 · 专业 · 克制 · 数据化
   与 Dashboard 完全一致的视觉风格
   ============================================================ */

/* ----- Tokens (identical to Dashboard.vue) ----- */
$c-bg: #F5F7FA;
$c-card: #FFFFFF;
$c-border: #E5E7EB;
$c-text: #1F2937;
$c-secondary: #6B7280;
$c-muted: #9CA3AF;
$c-primary: #1E3A8A;
$c-accent: #2563EB;
$radius: 8px;
$shadow-card: 0 1px 2px rgba(0, 0, 0, 0.04);
$shadow-hover: 0 2px 8px rgba(0, 0, 0, 0.06);

.warning-center {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  min-height: 100%;
  background: $c-bg;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ===== Layer 1: KPI Strip ===== */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.kpi-card {
  background: $c-card;
  border: 1px solid $c-border;
  border-radius: $radius;
  padding: 16px 20px;
  box-shadow: $shadow-card;
  transition: box-shadow 0.2s;
  &:hover {
    box-shadow: $shadow-hover;
  }
}

.kpi-inner {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.kpi-label {
  font-size: 12px;
  color: $c-muted;
  font-weight: 500;
}

.kpi-value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.kpi-number {
  font-size: 26px;
  font-weight: 700;
  color: $c-text;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.kpi-unit {
  font-size: 12px;
  color: $c-secondary;
  font-weight: 500;
}

.kpi-change {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  &.up {
    color: #059669;
    background: #ECFDF5;
  }
  &.down {
    color: #DC2626;
    background: #FEF2F2;
  }
}

/* ===== Section Header ===== */
.section-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 4px 0 0;
}

.section-title {
  font-size: 15px;
  font-weight: 700;
  color: $c-text;
  margin: 0;
  position: relative;
  padding-left: 12px;
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 15px;
    background: $c-primary;
    border-radius: 2px;
  }
}

.section-subtitle {
  font-size: 11px;
  color: $c-muted;
  font-weight: 400;
}

/* ===== Panel (Unified Card) ===== */
.panel {
  background: $c-card;
  border: 1px solid $c-border;
  border-radius: $radius;
  padding: 16px 20px;
  box-shadow: $shadow-card;
  display: flex;
  flex-direction: column;
}

.panel--flex {
  flex: 1;
  min-height: 0;
}

.panel--hero {
  // main visual emphasis
}

.panel--student-list {
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  margin-bottom: 4px;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: $c-text;
  margin: 0;
}

.panel-chart {
  flex: 1;
  min-height: 0;
  width: 100%;
}

.panel-chart--lg {
  min-height: 340px;
}

.legend-inline {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
  &:first-child { margin-left: 4px; }
}

.legend-text {
  font-size: 10px;
  color: $c-muted;
}

/* ===== Layer 2: Core Analysis (4 + 8) ===== */
.row-core {
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: 12px;
  min-height: 440px;
}

.core-left {
  min-height: 0;
  & > .panel {
    height: 100%;
    .panel-chart {
      min-height: 340px;
    }
  }
}

.core-right {
  min-height: 0;
  & > .panel {
    height: 100%;
    .panel-chart--lg {
      min-height: 340px;
    }
  }
}

/* ===== Layer 3: Half-half rows ===== */
.row-half {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 12px;
  min-height: 420px;
}

/* ===== Student Table ===== */
.student-total {
  font-size: 11px;
  font-weight: 600;
  color: $c-primary;
  background: #EFF6FF;
  padding: 2px 8px;
  border-radius: 4px;
}

.student-table-wrap {
  flex: 1;
  overflow-y: auto;
  margin-top: 6px;
}

.student-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;

  th {
    padding: 10px 8px;
    text-align: left;
    border-bottom: 2px solid #F3F4F6;
    color: $c-muted;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
    position: sticky;
    top: 0;
    background: $c-card;
  }

  td {
    padding: 10px 8px;
    border-bottom: 1px solid #F3F4F6;
    color: $c-text;
  }

  tbody tr {
    transition: background 0.15s;
    &:hover {
      background: #F9FAFB;
    }
  }

  .cell-id {
    color: $c-secondary;
    font-size: 11px;
    font-variant-numeric: tabular-nums;
  }

  .cell-name {
    font-weight: 600;
    color: $c-text;
  }

  .cell-time {
    color: $c-muted;
    font-size: 11px;
    font-variant-numeric: tabular-nums;
  }
}

/* Risk Tags (blue-only palette, matching ECharts) */
.risk-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  &.risk-high {
    background: #DBEAFE;
    color: #1E3A8A;
  }
  &.risk-mid {
    background: #EFF6FF;
    color: #3B82F6;
  }
  &.risk-low {
    background: #F5F9FF;
    color: #60A5FA;
  }
}

/* ===== Layer 4: Exception Events ===== */
.row-exception {
  min-height: 0;
}

.exception-total {
  font-size: 11px;
  font-weight: 600;
  color: $c-primary;
  background: #EFF6FF;
  padding: 2px 8px;
  border-radius: 4px;
}

.exception-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  flex: 1;
}

.exception-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid #F3F4F6;
  transition: background 0.15s;
  &:last-child { border-bottom: none; }
  &:hover {
    background: #FAFBFC;
    margin: 0 -20px;
    padding-left: 20px;
    padding-right: 20px;
  }

  &.exception-critical {
    border-left: 3px solid #1E3A8A;
    padding-left: 17px;
    margin-left: 0;
  }
  &.exception-warning {
    border-left: 3px solid #3B82F6;
    padding-left: 17px;
    margin-left: 0;
  }
  &.exception-info {
    border-left: 3px solid #93C5FD;
    padding-left: 17px;
    margin-left: 0;
  }
}

.exception-left {
  flex-shrink: 0;
  padding-top: 1px;
}

.exception-tag {
  display: inline-block;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 3px;
  white-space: nowrap;
  &.etag-critical {
    background: #DBEAFE;
    color: #1E3A8A;
  }
  &.etag-warning {
    background: #EFF6FF;
    color: #3B82F6;
  }
  &.etag-info {
    background: #F5F9FF;
    color: #60A5FA;
  }
}

.exception-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.exception-title {
  font-size: 13px;
  font-weight: 600;
  color: $c-text;
  line-height: 1.4;
}

.exception-desc {
  font-size: 11px;
  color: $c-secondary;
  line-height: 1.5;
}

.exception-right {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.exception-source {
  font-size: 10px;
  color: $c-muted;
  background: #F9FAFB;
  padding: 1px 6px;
  border-radius: 3px;
  white-space: nowrap;
}

.exception-time {
  font-size: 10px;
  color: $c-muted;
  font-variant-numeric: tabular-nums;
}

/* ===== Responsive ===== */
@media (max-width: 1600px) {
  .kpi-strip {
    grid-template-columns: repeat(5, 1fr);
  }
}

@media (max-width: 1400px) {
  .kpi-strip {
    grid-template-columns: repeat(5, 1fr);
  }
  .row-core {
    grid-template-columns: 1fr 2fr;
  }
  .row-half {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 1100px) {
  .kpi-strip {
    grid-template-columns: repeat(3, 1fr);
  }
  .row-core {
    grid-template-columns: 1fr;
    min-height: auto;
  }
  .core-left > .panel {
    min-height: 300px;
  }
  .row-half {
    grid-template-columns: 1fr;
    min-height: auto;
  }
}

@media (max-width: 768px) {
  .warning-center {
    padding: 12px;
    gap: 12px;
  }
  .kpi-strip {
    grid-template-columns: 1fr 1fr;
  }
  .kpi-number {
    font-size: 22px;
  }
  .row-core {
    grid-template-columns: 1fr;
  }
  .row-half {
    grid-template-columns: 1fr;
  }
  .exception-item {
    flex-wrap: wrap;
  }
  .exception-right {
    flex-direction: row;
    gap: 8px;
  }
}
</style>