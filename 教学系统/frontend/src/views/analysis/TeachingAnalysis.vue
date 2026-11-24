<template>
  <div class="analysis-hub">
    <!-- 顶部标题栏 -->
    <div class="hub-topbar">
      <div class="hub-title-area">
        <h2 class="hub-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="hub-title-icon">
            <path d="M18 20V10 M12 20V4 M6 20v-6"/>
          </svg>
          教学决策与数据洞察平台
        </h2>
        <p class="hub-subtitle">政治学与公共管理学院 · 教学综合评估与决策支持中心 · 数据驱动治理</p>
      </div>
      <div class="hub-actions">
        <div class="period-tabs">
          <button v-for="p in periods" :key="p.val" :class="['period-tab', { active: activePeriod === p.val }]" @click="activePeriod = p.val">{{ p.label }}</button>
        </div>
        <select v-model="collegeFilter" class="filter-select">
          <option value="">全部专业</option>
          <option v-for="major in majorOptions" :key="major" :value="major">{{major}}</option>
        </select>
      </div>
    </div>

    <!-- 第1行：6 教学KPI指标卡片 -->
    <div class="hub-stats-row-6">
      <div class="hub-stat-card" v-for="stat in kpis" :key="stat.label">
        <div class="hub-stat-icon" :style="{ background: stat.bg, color: stat.color }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path :d="stat.icon"/></svg>
        </div>
        <div class="hub-stat-body">
          <div class="hub-stat-label">{{ stat.label }}</div>
          <div class="hub-stat-value">
            <span class="hub-stat-num">{{ stat.value }}</span>
            <span class="hub-stat-unit">{{ stat.unit }}</span>
          </div>
          <div class="hub-stat-sub">
            <span class="hub-stat-trend" :class="stat.trendUp ? 'trend-up' : 'trend-down'">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="trend-arrow"><polyline :points="stat.trendUp ? '18 15 12 9 6 15' : '6 9 12 15 18 9'"/></svg>
              {{ stat.trend }}
            </span>
            {{ stat.sub }}
          </div>
        </div>
      </div>
    </div>

    <!-- 第2行：数据驾驶舱 + 教学质量改进事项台账 -->
    <div class="hub-row-dashboard">
      <div class="hub-panel cockpit-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            数据驾驶舱
          </span>
          <div class="cockpit-time-group">
            <button v-for="t in cockpitTimes" :key="t" class="cockpit-time-chip" :class="{ active: cockpitTime === t }" @click="cockpitTime = t">{{ t }}</button>
          </div>
        </div>
        <div class="cockpit-grid">
          <div class="cockpit-gauge-area" ref="gaugeChartRef"></div>
          <div class="cockpit-metrics">
            <div class="cm-row" v-for="m in cockpitMetrics" :key="m.label">
              <div class="cm-icon" :style="{ background: m.bg, color: m.color }">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path :d="m.icon"/></svg>
              </div>
              <div class="cm-body">
                <span class="cm-label">{{ m.label }}</span>
                <span class="cm-val" :style="{ color: m.color }">{{ m.value }}</span>
              </div>
              <div class="cm-spark">
                <svg viewBox="0 0 60 20" class="cm-spark-svg">
                  <polyline :points="m.spark" fill="none" :stroke="m.trend >= 0 ? '#059669' : '#DC2626'" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="cm-spark-val" :class="m.trend >= 0 ? 'up' : 'down'">{{ m.trend >= 0 ? '+' : '' }}{{ m.trend }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="hub-panel task-panel">
        <div class="hub-panel-header"><span class="hub-panel-title">教学质量改进事项台账</span><span class="hub-panel-badge">{{ visibleTasks.length }} 项</span></div>
        <p class="task-note">供管理员记录教学改进工作，不生成AI结论。暂存于当前浏览器，并非正式院务审批记录。</p>
        <form class="task-form" @submit.prevent="addTask">
          <input v-model.trim="taskForm.title" maxlength="80" required placeholder="待办事项 / 整改问题（必填）" />
          <div class="task-fields">
            <select v-model="taskForm.major" required><option value="" disabled>所属专业</option><option value="全院">全院共性事项</option><option v-for="m in majorOptions" :key="m" :value="m">{{m}}</option></select>
            <input v-model.trim="taskForm.owner" maxlength="30" placeholder="责任人或部门" />
          </div>
          <div class="task-fields">
            <input type="date" aria-label="计划完成日期" v-model="taskForm.due"/>
            <button class="task-submit" type="submit">＋ 登记事项</button>
          </div>
        </form>
        <div class="task-items">
          <div v-if="!visibleTasks.length" class="task-empty">暂无已登记事项，可使用上方表单新增。</div>
          <div v-for="t in visibleTasks" :key="t.id" class="task-item">
            <input type="checkbox" :checked="t.done" @change="toggleTask(t.id)" :aria-label="'完成状态 '+t.title"/>
            <div class="task-content"><b :class="{completed:t.done}">{{t.title}}</b><small>{{t.major}}<template v-if="t.owner"> · {{t.owner}}</template><template v-if="t.due"> · 截止 {{t.due}}</template></small></div>
            <span class="task-state">{{t.done?'已完成':'待处理'}}</span>
            <button class="task-remove" @click="removeTask(t.id)" aria-label="删除">×</button>
          </div>
        </div>
        <div class="task-footer">当前筛选：{{visibleTasks.filter(t=>t.done).length}} 项已完成 · {{visibleTasks.filter(t=>!t.done).length}} 项待处理 <span>本机记录</span></div>
      </div>
    </div>

    <!-- 第3行：学院对比雷达图 + 热点词云 -->
    <div class="hub-row-2col">
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><circle cx="12" cy="12" r="10"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="12" x2="22" y2="12"/></svg>
            教研室对比雷达图
          </span>
          <div class="radar-legend">
            <span class="rl-item" v-for="c in radarColleges" :key="c.name">
              <span class="rl-dot" :style="{ background: c.color }"></span>{{ c.name }}
            </span>
          </div>
        </div>
        <div class="hub-chart-wrap" ref="radarChartRef"></div>
      </div>

      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>
            教学热点词云
          </span>
          <span class="hub-panel-badge">实时热度</span>
        </div>
        <div class="wordcloud-wrap">
          <span
            v-for="word in wordCloud"
            :key="word.text"
            class="wc-word"
            :style="{
              fontSize: word.size + 'px',
              color: word.color,
              fontWeight: word.weight,
              opacity: word.opacity,
              transform: `rotate(${word.rotate}deg)`,
              top: word.top + '%',
              left: word.left + '%',
            }"
          >{{ word.text }}</span>
        </div>
      </div>
    </div>

    <!-- 第4行：教学质量分析与趋势预测 + 风险预警 -->
    <div class="hub-row-2col">
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
            教学质量分析与趋势预测
          </span>
          <span class="hub-panel-badge">{{ activePeriodLabel }}</span>
        </div>
        <div class="hub-chart-wrap" ref="qualityChartRef"></div>
      </div>

      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            风险预警
          </span>
          <span class="hub-panel-badge" :style="{ background: riskStats.high > 0 ? '#FEF2F2' : '#ECFDF5', color: riskStats.high > 0 ? '#DC2626' : '#059669' }">{{ riskStats.high }} 项高风险</span>
        </div>
        <div class="risk-grid">
          <div class="risk-card" v-for="risk in risks" :key="risk.id" :class="'risk-level-' + risk.level">
            <div class="risk-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="risk-icon" :class="'risk-icon-' + risk.level"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <span class="risk-tag" :class="'risk-tag-' + risk.level">{{ risk.level === 'high' ? '高风险' : risk.level === 'medium' ? '中风险' : '低风险' }}</span>
              <span class="risk-time">{{ risk.time }}</span>
            </div>
            <div class="risk-body">
              <span class="risk-title">{{ risk.title }}</span>
              <span class="risk-desc">{{ risk.desc }}</span>
            </div>
            <div class="risk-footer">
              <span class="risk-indicator">影响范围：{{ risk.scope }}</span>
              <span class="risk-action">{{ risk.action }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第5行：教学满意度分析 + 多维度数据联动 -->
    <div class="hub-row-2col">
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            教学满意度分析
          </span>
          <span class="hub-panel-badge">全院调研</span>
        </div>
        <div class="hub-chart-wrap" ref="satisfactionChartRef"></div>
      </div>

      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            教师教学质量分布
          </span>
          <div class="scatter-legend">
            <span class="sl-item"><span class="sl-dot" style="background: #1E3A8A;"></span>政治学教研室</span>
            <span class="sl-item"><span class="sl-dot" style="background: #3B82F6;"></span>公共管理教研室</span>
            <span class="sl-item"><span class="sl-dot" style="background: #60A5FA;"></span>国际政治教研室</span>
            <span class="sl-item"><span class="sl-dot" style="background: #93C5FD;"></span>科社教研室</span>
          </div>
        </div>
        <div class="hub-chart-wrap" ref="scatterChartRef"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

const activePeriod = ref('semester')
const collegeFilter = ref('')
const majorOptions = ["行政管理","政治学与行政学","国际政治","科学社会主义","行政管理+电子科学与技术双学位","国际政治＋英语双学位"]
const cockpitTime = ref('本月')

const gaugeChartRef = ref<HTMLElement | null>(null)
const radarChartRef = ref<HTMLElement | null>(null)
const qualityChartRef = ref<HTMLElement | null>(null)
const satisfactionChartRef = ref<HTMLElement | null>(null)
const scatterChartRef = ref<HTMLElement | null>(null)

let gaugeChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null
let qualityChart: echarts.ECharts | null = null
let satisfactionChart: echarts.ECharts | null = null
let scatterChart: echarts.ECharts | null = null

const periods = [
  { val: 'semester', label: '本学期' },
  { val: 'year', label: '本学年' },
  { val: 'all', label: '全部' },
]
const activePeriodLabel = computed(() => periods.find(p => p.val === activePeriod.value)?.label || '本学期')
const cockpitTimes = ['本月', '本季', '本年度']

// ---- 1. 教学KPI指标 (山大政管学院) ----
const kpis = [
  {
    label: '教学质量指数', value: '84.8', unit: '分',
    sub: '较上月 +1.6', trend: '+1.6%', trendUp: true,
    icon: 'M9 11l3 3L22 4 M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11',
    bg: '#EFF6FF', color: '#1E3A8A',
  },
  {
    label: '学生满意度', value: '94.6', unit: '%',
    sub: '较上学期 +1.2', trend: '+1.2%', trendUp: true,
    icon: 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2 M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
    bg: '#F5F3FF', color: '#7C3AED',
  },
  {
    label: '课程达标率', value: '96.8', unit: '%',
    sub: '较上月 -0.3', trend: '-0.3%', trendUp: false,
    icon: 'M22 11.08V12a10 10 0 1 1-5.93-9.14 M22 4L12 14.01l-3-3',
    bg: '#ECFDF5', color: '#059669',
  },
  {
    label: '研讨参与指数', value: '82.4', unit: '分',
    sub: '较上月 +3.6', trend: '+3.6%', trendUp: true,
    icon: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z',
    bg: '#FEF3C7', color: '#D97706',
  },
  {
    label: '教学资源利用率', value: '88.1', unit: '%',
    sub: '较上学期 +4.0', trend: '+4.0%', trendUp: true,
    icon: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z',
    bg: '#DBEAFE', color: '#3B82F6',
  },
  {
    label: '学业预警率', value: '4.2', unit: '%',
    sub: '较上月 -0.8', trend: '-0.8%', trendUp: false,
    icon: 'M12 9v2m0 4h.01M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z',
    bg: '#FEF2F2', color: '#DC2626',
  },
]

// ---- 10. 数据驾驶舱指标 ----
const cockpitMetrics = [
  { label: '开设课程数', value: '63 门', icon: 'M12 6.25a.75.75 0 0 1 .75.75v10a.75.75 0 0 1-1.5 0V7a.75.75 0 0 1 .75-.75z M15.95 8.25a.75.75 0 0 1 .75.75v7a.75.75 0 0 1-1.5 0V9a.75.75 0 0 1 .75-.75z M8.05 10.25a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3a.75.75 0 0 1 .75-.75z', trend: 5.2, bg: '#EFF6FF', color: '#1E3A8A', spark: '0,14 10,13 20,15 30,12 40,16 50,14 60,17' },
  { label: '在授教师', value: '48 人', icon: 'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0z M12 14a7 7 0 0 0-7 7h14a7 7 0 0 0-7-7z', trend: 2.1, bg: '#F5F3FF', color: '#7C3AED', spark: '0,16 10,14 20,17 30,15 40,18 50,16 60,19' },
  { label: '人均课时', value: '8.2 时/周', icon: 'M12 2v4 M12 22v-4 M4.93 4.93l2.83 2.83 M16.24 16.24l2.83 2.83 M2 12h4 M22 12h-4 M4.93 19.07l2.83-2.83 M16.24 7.76l2.83-2.83', trend: -0.6, bg: '#ECFDF5', color: '#059669', spark: '0,13 10,15 20,12 30,14 40,11 50,13 60,10' },
  { label: '督导评分', value: '86.2 分', icon: 'M9 12l2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0z', trend: 1.8, bg: '#FFF7ED', color: '#EA580C', spark: '0,15 10,14 20,16 30,15 40,17 50,16 60,18' },
]

// ---- 仪表盘图表 ----
function initGaugeChart() {
  if (!gaugeChartRef.value) return
  gaugeChart = echarts.init(gaugeChartRef.value)
  gaugeChart.setOption({
    series: [{
      type: 'gauge', startAngle: 210, endAngle: -30, center: ['50%', '55%'], radius: '85%',
      min: 0, max: 100, splitNumber: 10,
      axisLine: { show: true, lineStyle: { width: 20, color: [[0.3, '#93C5FD'], [0.6, '#3B82F6'], [0.8, '#2563EB'], [1, '#1E3A8A']] } },
      pointer: { icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z', length: '70%', width: 8, offsetCenter: [0, '-10%'], itemStyle: { color: '#1E3A8A' } },
      axisTick: { length: 12, lineStyle: { color: 'auto', width: 2 } },
      splitLine: { length: 22, lineStyle: { color: 'auto', width: 4 } },
      axisLabel: { color: '#6B7280', fontSize: 10, distance: -38 },
      title: { offsetCenter: [0, '82%'], fontSize: 13, color: '#374151', fontWeight: 600 },
      detail: { valueAnimation: true, fontSize: 36, fontWeight: 700, color: '#1E3A8A', offsetCenter: [0, '55%'] },
      data: [{ value: 84.8, name: '教学质量指数' }],
    }],
  })
}

// ---- 2. 教研室对比雷达图 ----
const radarColleges = [
  { name: '政治学教研室', color: '#1E3A8A' },
  { name: '公共管理教研室', color: '#3B82F6' },
  { name: '国际政治教研室', color: '#60A5FA' },
  { name: '科社教研室', color: '#93C5FD' },
]

function initRadarChart() {
  if (!radarChartRef.value) return
  radarChart = echarts.init(radarChartRef.value)
  radarChart.setOption({
    tooltip: { backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#374151', fontSize: 12 } },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 10 }, itemWidth: 12, itemHeight: 8, itemGap: 16 },
    radar: {
      center: ['50%', '46%'], radius: '68%',
      indicator: [
        { name: '教学质量', max: 100 }, { name: '学生满意度', max: 100 },
        { name: '科研产出', max: 100 }, { name: '课程创新', max: 100 },
        { name: '师生互动', max: 100 }, { name: '社会服务', max: 100 },
      ],
      axisName: { color: '#6B7280', fontSize: 10 },
      splitArea: { areaStyle: { color: ['#FAFAFA', '#F9FAFB'] } },
    },
    series: [
      { type: 'radar', name: '政治学教研室', data: [{ value: [88, 92, 85, 86, 82, 78] }], symbol: 'circle', symbolSize: 4, lineStyle: { color: '#1E3A8A', width: 2 }, areaStyle: { color: 'rgba(30,58,138,0.08)' }, itemStyle: { color: '#1E3A8A' } },
      { type: 'radar', name: '公共管理教研室', data: [{ value: [85, 88, 82, 90, 86, 92] }], symbol: 'circle', symbolSize: 4, lineStyle: { color: '#3B82F6', width: 2 }, areaStyle: { color: 'rgba(59,130,246,0.08)' }, itemStyle: { color: '#3B82F6' } },
      { type: 'radar', name: '国际政治教研室', data: [{ value: [82, 86, 88, 84, 80, 74] }], symbol: 'circle', symbolSize: 4, lineStyle: { color: '#60A5FA', width: 2 }, areaStyle: { color: 'rgba(96,165,250,0.08)' }, itemStyle: { color: '#60A5FA' } },
      { type: 'radar', name: '科社教研室', data: [{ value: [74, 76, 72, 68, 74, 70] }], symbol: 'circle', symbolSize: 4, lineStyle: { color: '#93C5FD', width: 2 }, areaStyle: { color: 'rgba(147,197,253,0.08)' }, itemStyle: { color: '#93C5FD' } },
    ],
  })
}

// ---- 3. 教学热点词云 ----
const wordCloud = [
  { text: '治理现代化', size: 28, color: '#1E3A8A', weight: 700, opacity: 1, rotate: 0, top: 12, left: 8 },
  { text: '公共政策', size: 24, color: '#2563EB', weight: 700, opacity: 0.95, rotate: -8, top: 8, left: 52 },
  { text: '国际关系', size: 22, color: '#3B82F6', weight: 600, opacity: 0.9, rotate: 5, top: 30, left: 20 },
  { text: '数字政府', size: 20, color: '#60A5FA', weight: 600, opacity: 0.88, rotate: -3, top: 50, left: 6 },
  { text: '比较政治', size: 18, color: '#1E40AF', weight: 600, opacity: 0.85, rotate: 10, top: 18, left: 40 },
  { text: '行政管理', size: 16, color: '#3B82F6', weight: 500, opacity: 0.82, rotate: -12, top: 60, left: 42 },
  { text: '田野调查', size: 14, color: '#60A5FA', weight: 500, opacity: 0.8, rotate: 6, top: 55, left: 65 },
  { text: '全球治理', size: 12, color: '#93C5FD', weight: 500, opacity: 0.78, rotate: 0, top: 75, left: 18 },
  { text: '公共管理', size: 11, color: '#1E3A8A', weight: 400, opacity: 0.75, rotate: -7, top: 70, left: 55 },
  { text: '外交学', size: 10, color: '#3B82F6', weight: 400, opacity: 0.72, rotate: 8, top: 40, left: 72 },
  { text: '社会调查', size: 9, color: '#60A5FA', weight: 400, opacity: 0.7, rotate: -4, top: 80, left: 40 },
  { text: '双学位', size: 8, color: '#93C5FD', weight: 400, opacity: 0.68, rotate: 3, top: 24, left: 75 },
  { text: '课程思政', size: 7, color: '#BFDBFE', weight: 400, opacity: 0.65, rotate: -9, top: 85, left: 72 },
  { text: '研讨式教学', size: 6, color: '#BFDBFE', weight: 300, opacity: 0.6, rotate: 5, top: 14, left: 3 },
]

// ---- 4. 教学质量分析与趋势预测 ----
function initQualityChart() {
  if (!qualityChartRef.value) return
  qualityChart = echarts.init(qualityChartRef.value)
  qualityChart.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#374151', fontSize: 12 } },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 10 }, itemWidth: 12, itemHeight: 8, itemGap: 16 },
    grid: { top: 20, right: 50, bottom: 40, left: 50 },
    xAxis: {
      type: 'category',
      data: ['21秋', '22春', '22秋', '23春', '23秋', '24春', '24秋', '25春', '25秋(预)', '26春(预)'],
      axisLabel: { color: '#6B7280', fontSize: 10 },
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value', name: '质量分数', nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
      axisLabel: { color: '#6B7280', fontSize: 10 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      min: 3.0, max: 5.0,
    },
    series: [
      {
        name: '实际质量分', type: 'line',
        data: [3.7, 3.8, 3.9, 4.0, 4.1, 4.2, 4.2, 4.3, null, null],
        smooth: true, lineStyle: { color: '#1E3A8A', width: 3 },
        itemStyle: { color: '#1E3A8A' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(30,58,138,0.15)' }, { offset: 1, color: 'rgba(30,58,138,0.01)' }]) },
        symbol: 'circle', symbolSize: 8,
      },
      {
        name: '预测趋势', type: 'line',
        data: [null, null, null, null, null, null, null, null, 4.4, 4.6],
        smooth: true, lineStyle: { color: '#93C5FD', width: 2.5, type: 'dashed' },
        itemStyle: { color: '#3B82F6' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(59,130,246,0.1)' }, { offset: 1, color: 'rgba(59,130,246,0.01)' }]) },
        symbol: 'diamond', symbolSize: 10,
      },
      {
        name: '目标线', type: 'line',
        data: [4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5, 4.5],
        lineStyle: { color: '#D1D5DB', width: 1, type: 'dotted' },
        itemStyle: { color: '#D1D5DB' }, symbol: 'none', silent: true,
      },
    ],
  })
}

// ---- 6. 风险预警 ----
const risks = [
  { id: 1, level: 'high', time: '1小时前', title: '社会调查方法 - 挂科率持续攀升', desc: '近2学期不及格率从5.8%上升至8.5%，需立即干预。建议加强SPSS/Stata实操辅导，增设研究方法工作坊，提高过程性考核占比。', scope: '2个班级 · 68名学生', action: '立即处理' },
  { id: 2, level: 'high', time: '3小时前', title: '科社教研室 - 教学质量波动', desc: '科学社会主义专业评教连续2学期下滑，教研室已启动教学质量专项督导，排查核心问题并制定改进方案。', scope: '1个专业 · 32名学生', action: '教研室介入' },
  { id: 3, level: 'medium', time: '6小时前', title: '国际政治教研室 - 英文文献缺藏率偏高', desc: '外交学、区域国别研究相关最新英文专著缺藏率达35%，影响双学位培养质量。建议纳入文献资源建设计划。', scope: '2个专业 · 86名学生', action: '资源采购' },
  { id: 4, level: 'medium', time: '1天前', title: '青年教师 - 科研产出不均衡', desc: '仅25%教师承担了65%科研产出，建议加强课题申报辅导和学术论文写作训练，培育团队协作机制。', scope: '8名教师 · 覆盖12门课', action: '安排指导' },
  { id: 5, level: 'low', time: '2天前', title: '公共管理案例库 - 资源更新需求', desc: '当前案例库中近2年新案例占比仅15%，建议组织教师更新公共治理数字化转型相关教学案例。', scope: '1个案例库 · 全院共享', action: '教研组更新' },
]

const riskStats = computed(() => ({
  high: risks.filter(r => r.level === 'high').length,
  medium: risks.filter(r => r.level === 'medium').length,
  low: risks.filter(r => r.level === 'low').length,
}))

// ---- 7. 教学满意度分析 ----
function initSatisfactionChart() {
  if (!satisfactionChartRef.value) return
  satisfactionChart = echarts.init(satisfactionChartRef.value)
  satisfactionChart.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#374151', fontSize: 12 } },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 10 }, itemWidth: 12, itemHeight: 8, itemGap: 16 },
    grid: { top: 20, right: 30, bottom: 40, left: 46 },
    xAxis: {
      type: 'category',
      data: ['教学内容', '教学方法', '课堂氛围', '课后辅导', '考核方式', '教材选用'],
      axisLabel: { color: '#6B7280', fontSize: 10 }, axisTick: { show: false },
    },
    yAxis: {
      type: 'value', name: '满意度 %', nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
      axisLabel: { color: '#6B7280', fontSize: 10 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }, max: 100,
    },
    series: [
      { name: '非常满意', type: 'bar', stack: 'total', data: [58, 52, 46, 42, 38, 35], itemStyle: { color: '#1E3A8A', borderRadius: [0, 0, 0, 0] }, barWidth: 28, emphasis: { focus: 'series' } },
      { name: '满意', type: 'bar', stack: 'total', data: [32, 34, 36, 37, 36, 38], itemStyle: { color: '#3B82F6' }, emphasis: { focus: 'series' } },
      { name: '一般', type: 'bar', stack: 'total', data: [7, 10, 13, 15, 19, 20], itemStyle: { color: '#93C5FD' }, emphasis: { focus: 'series' } },
      { name: '不满意', type: 'bar', stack: 'total', data: [3, 4, 5, 6, 7, 7], itemStyle: { color: '#E5E7EB', borderRadius: [6, 6, 0, 0] }, emphasis: { focus: 'series' } },
    ],
  })
}

// ---- 8. 教师教学质量分布 (散点气泡图) ----
function initScatterChart() {
  if (!scatterChartRef.value) return
  scatterChart = echarts.init(scatterChartRef.value)
  scatterChart.setOption({
    tooltip: {
      trigger: 'item', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      formatter: (p: any) => `<b>${p.name}</b><br/>教学质量：${p.value[0]}<br/>满意度：${p.value[1]}<br/>课程完成率：${p.value[2]}%`,
    },
    grid: { top: 20, right: 30, bottom: 30, left: 52 },
    xAxis: { name: '教学质量指数', nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, axisLabel: { color: '#6B7280', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }, min: 60, max: 100 },
    yAxis: { name: '学生满意度', nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, axisLabel: { color: '#6B7280', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } }, min: 60, max: 100 },
    series: [{
      type: 'scatter', symbolSize: (v: any) => (v?.[2] ?? 60) * 0.5,
      data: [
        { value: [88, 92, 96], name: '政治学教研室' },
        { value: [85, 88, 92], name: '公共管理教研室' },
        { value: [82, 86, 88], name: '国际政治教研室' },
        { value: [74, 76, 80], name: '科社教研室' },
        { value: [86, 84, 89], name: '公共政策研究中心' },
        { value: [78, 80, 76], name: '城市治理研究中心' },
        { value: [90, 90, 94], name: '双学位培养组' },
      ],
      itemStyle: { color: (p: any) => ['#1E3A8A', '#2563EB', '#3B82F6', '#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE'][p.dataIndex % 7], opacity: 0.75, shadowBlur: 8, shadowColor: 'rgba(30,58,138,0.2)' },
      emphasis: { scale: 1.5, itemStyle: { opacity: 1 } },
      label: { show: true, position: 'right', formatter: '{b}', color: '#6B7280', fontSize: 9 },
    }],
  })
}


type TeachingTask={id:string;title:string;major:string;owner:string;due:string;done:boolean}
const keyTasks='sdu-teaching-quality-local-tasks-v1'
const tasks=ref<TeachingTask[]>([])
const taskForm=ref({title:'',major:'',owner:'',due:''})
const visibleTasks=computed(()=>tasks.value.filter(t=>!collegeFilter.value||t.major===collegeFilter.value||t.major==='全院'))
function saveTasks(){try{localStorage.setItem(keyTasks,JSON.stringify(tasks.value))}catch{}}
function addTask(){if(!taskForm.value.title||!taskForm.value.major)return
  tasks.value.unshift({...taskForm.value,id:Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,7),done:false})
  taskForm.value={title:'',major:collegeFilter.value||'',owner:'',due:''};saveTasks()}
function toggleTask(id:string){const t=tasks.value.find(x=>x.id===id);if(t){t.done=!t.done;saveTasks()}}
function removeTask(id:string){tasks.value=tasks.value.filter(x=>x.id!==id);saveTasks()}
// ========== Lifecycle ==========
onMounted(async () => {
  try{const stored=JSON.parse(localStorage.getItem(keyTasks)||'[]');if(Array.isArray(stored))tasks.value=stored.filter((x):x is TeachingTask=>x&&typeof x.id==='string'&&typeof x.title==='string'&&typeof x.major==='string')}catch{}
  await nextTick()
  initGaugeChart()
  initRadarChart()
  initQualityChart()
  initSatisfactionChart()
  initScatterChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  gaugeChart?.dispose(); radarChart?.dispose(); qualityChart?.dispose()
  satisfactionChart?.dispose(); scatterChart?.dispose()
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  gaugeChart?.resize(); radarChart?.resize(); qualityChart?.resize()
  satisfactionChart?.resize(); scatterChart?.resize()
}
</script>

<style scoped>
/* ============================================================
   ANALYSIS HUB — 教学决策与数据洞察平台
   设计方向：数据驾驶舱 / 大屏风格 / 智能决策
   主色调：蓝系 (#1E3A8A → #93C5FD) + 紫/绿/橙辅助
   ============================================================ */

.analysis-hub { display: flex; flex-direction: column; gap: 20px; }

/* Topbar */
.hub-topbar { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px; }
.hub-title-area { flex: 1; min-width: 260px; }
.hub-title { font-size: 22px; font-weight: 700; color: var(--text-title); display: flex; align-items: center; gap: 10px; margin: 0; }
.hub-title-icon { width: 22px; height: 22px; color: var(--color-primary); flex-shrink: 0; }
.hub-subtitle { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
.hub-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

/* Period Tabs */
.period-tabs { display: flex; gap: 4px; background: #F3F4F6; border-radius: 8px; padding: 3px; }
.period-tab { border: none; background: transparent; padding: 6px 14px; font-size: 12px; font-weight: 500; color: #6B7280; border-radius: 6px; cursor: pointer; transition: all 0.2s; }
.period-tab.active { background: #FFF; color: #1E3A8A; box-shadow: 0 1px 3px rgba(0,0,0,0.08); font-weight: 600; }
.filter-select { height: 36px; border: 1px solid #E5E7EB; border-radius: 8px; padding: 0 12px; font-size: 13px; color: #374151; background: #FFF; outline: none; cursor: pointer; }

/* Stat Cards Row */
.hub-stats-row-6 { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; }
.hub-stat-card { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 18px 20px; display: flex; align-items: center; gap: 14px; transition: all 0.25s; cursor: default; }
.hub-stat-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.08); transform: translateY(-2px); }
.hub-stat-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.hub-stat-icon svg { width: 18px; height: 18px; }
.hub-stat-body { flex: 1; min-width: 0; }
.hub-stat-label { font-size: 11px; color: var(--text-muted); font-weight: 500; }
.hub-stat-value { display: flex; align-items: baseline; gap: 3px; margin-top: 2px; }
.hub-stat-num { font-size: 26px; font-weight: 700; color: var(--text-title); line-height: 1.1; }
.hub-stat-unit { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.hub-stat-sub { font-size: 10px; color: var(--text-muted); margin-top: 2px; display: flex; align-items: center; gap: 4px; }
.hub-stat-trend { display: inline-flex; align-items: center; gap: 2px; font-weight: 600; font-size: 10px; }
.hub-stat-trend.trend-up { color: #2563EB; }
.hub-stat-trend.trend-down { color: #059669; }
.trend-arrow { width: 10px; height: 10px; }

/* Row Layouts */
.hub-row-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.hub-row-dashboard { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 16px; }

/* Panel */
.hub-panel { background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px 22px; display: flex; flex-direction: column; }
.hub-panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-shrink: 0; }
.hub-panel-title { font-size: 15px; font-weight: 600; color: var(--text-title); display: flex; align-items: center; gap: 8px; }
.panel-title-icon { width: 16px; height: 16px; color: var(--color-primary); flex-shrink: 0; }
.hub-panel-badge { font-size: 11px; background: #EFF6FF; color: var(--color-primary); padding: 3px 10px; border-radius: 6px; font-weight: 500; white-space: nowrap; }
.hub-chart-wrap { flex: 1; min-height: 280px; width: 100%; }

/* Cockpit */
.cockpit-panel { overflow: hidden; }
.cockpit-time-group { display: flex; gap: 4px; background: #F3F4F6; border-radius: 6px; padding: 2px; }
.cockpit-time-chip { border: none; background: transparent; padding: 4px 14px; font-size: 11px; font-weight: 500; color: #6B7280; border-radius: 5px; cursor: pointer; transition: all 0.15s; }
.cockpit-time-chip.active { background: #FFF; color: #1E3A8A; box-shadow: 0 1px 2px rgba(0,0,0,0.06); font-weight: 600; }
.cockpit-grid { display: flex; gap: 16px; flex: 1; }
.cockpit-gauge-area { flex: 1.2; min-height: 280px; min-width: 200px; }
.cockpit-metrics { flex: 0.8; display: flex; flex-direction: column; justify-content: center; gap: 10px; }
.cm-row { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: #F9FAFB; border-radius: 8px; transition: background 0.15s; }
.cm-row:hover { background: #EFF6FF; }
.cm-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.cm-icon svg { width: 14px; height: 14px; }
.cm-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.cm-label { font-size: 11px; color: var(--text-muted); }
.cm-val { font-size: 16px; font-weight: 700; }
.cm-spark { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.cm-spark-svg { width: 42px; height: 14px; }
.cm-spark-val { font-size: 10px; font-weight: 600; }
.cm-spark-val.up { color: #059669; } .cm-spark-val.down { color: #DC2626; }


.task-panel{background:#fff}
.task-note{padding:9px 11px;background:#f5f8ff;border-radius:8px;color:#6b7d99;line-height:1.6;font-size:11px;margin:8px 0 12px}
.task-form{display:flex;flex-direction:column;gap:8px}
.task-form input,.task-form select{min-width:0;width:100%;box-sizing:border-box;background:#fff;border:1px solid #e0e7f3;border-radius:7px;color:#264166;font-size:12px;padding:9px}
.task-fields{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.task-submit{background:#21438e;border:0;border-radius:7px;color:#fff;font-size:12px;cursor:pointer}
.task-items{min-height:100px;max-height:270px;overflow:auto;display:flex;flex-direction:column;gap:7px;margin-top:13px}
.task-item{display:flex;align-items:center;gap:9px;padding:10px;background:#f9fbfe;border:1px solid #edf1f8;border-radius:8px}
.task-item input{accent-color:#2563eb}
.task-content{flex:1;min-width:0;display:flex;flex-direction:column;gap:5px}
.task-content b{font-size:12px;color:#1b365b;overflow-wrap:anywhere}
.task-content b.completed{text-decoration:line-through;color:#8091aa}
.task-content small{font-size:10px;color:#8a9bb6}
.task-state{font-size:10px;white-space:nowrap;background:#eef4ff;color:#4774b5;padding:4px 6px;border-radius:5px}
.task-remove{font-size:18px;color:#9ba9c0;border:0;cursor:pointer;background:none}
.task-empty{text-align:center;padding:30px 8px;color:#97a6bc;font-size:12px}
.task-footer{display:flex;gap:7px;border-top:1px solid #edf1f8;margin-top:10px;padding-top:10px;color:#6b7d9d;font-size:11px}
.task-footer span{margin-left:auto}
/* Radar Legend */
.radar-legend { display: flex; gap: 10px; flex-wrap: wrap; }
.rl-item { display: flex; align-items: center; gap: 4px; font-size: 10px; color: var(--text-muted); }
.rl-dot { width: 8px; height: 8px; border-radius: 50%; }

/* Word Cloud */
.wordcloud-wrap { position: relative; width: 100%; min-height: 280px; overflow: hidden; }
.wc-word { position: absolute; cursor: default; white-space: nowrap; transition: all 0.3s; user-select: none; }
.wc-word:hover { transform: scale(1.15); text-shadow: 0 2px 8px rgba(30,58,138,0.2); }

/* Risk Grid */
.risk-grid { display: flex; flex-direction: column; gap: 8px; flex: 1; overflow-y: auto; }
.risk-card { padding: 12px 14px; border-radius: 8px; transition: all 0.15s; }
.risk-level-high { background: #FEF2F2; border-left: 3px solid #DC2626; }
.risk-level-medium { background: #FFFBEB; border-left: 3px solid #F59E0B; }
.risk-level-low { background: #F9FAFB; border-left: 3px solid #3B82F6; }
.risk-card:hover { filter: brightness(0.98); }
.risk-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.risk-icon { width: 16px; height: 16px; flex-shrink: 0; }
.risk-icon-high { color: #DC2626; } .risk-icon-medium { color: #F59E0B; } .risk-icon-low { color: #3B82F6; }
.risk-tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.risk-tag-high { background: #FEE2E2; color: #DC2626; } .risk-tag-medium { background: #FEF3C7; color: #D97706; } .risk-tag-low { background: #EFF6FF; color: #3B82F6; }
.risk-time { margin-left: auto; font-size: 10px; color: var(--text-muted); }
.risk-body { display: flex; flex-direction: column; gap: 3px; margin-bottom: 8px; }
.risk-title { font-size: 12px; font-weight: 600; color: var(--text-title); }
.risk-desc { font-size: 11px; color: var(--text-secondary); line-height: 1.4; }
.risk-footer { display: flex; justify-content: space-between; align-items: center; }
.risk-indicator { font-size: 10px; color: var(--text-muted); }
.risk-action { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 4px; }
.risk-level-high .risk-action { color: #DC2626; background: #FEE2E2; }
.risk-level-medium .risk-action { color: #D97706; background: #FEF3C7; }
.risk-level-low .risk-action { color: #3B82F6; background: #EFF6FF; }

/* Scatter Legend */
.scatter-legend { display: flex; gap: 12px; flex-wrap: wrap; }
.sl-item { display: flex; align-items: center; gap: 4px; font-size: 10px; color: var(--text-muted); }
.sl-dot { width: 8px; height: 8px; border-radius: 50%; }

/* Responsive */
@media (max-width: 1600px) {
  .hub-stats-row-6 { grid-template-columns: repeat(3, 1fr); }
  .hub-row-dashboard { grid-template-columns: 1fr; }
  .cockpit-grid { flex-direction: column; }
  .cockpit-gauge-area { min-height: 220px; }
}
@media (max-width: 1200px) { .hub-row-2col { grid-template-columns: 1fr; } }
@media (max-width: 768px) {
  .hub-stats-row-6 { grid-template-columns: repeat(2, 1fr); }
  .hub-stat-num { font-size: 20px; }
  .hub-stat-card { padding: 14px 16px; }
  .cockpit-grid { flex-direction: column; }
}
</style>