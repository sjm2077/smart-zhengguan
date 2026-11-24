<template>
  <!-- ============================================================
       成绩分析与教学质量中心 — BI 分析平台
       布局：统计卡片 → GPA分布+区间分析 → 不及格率+趋势 → 学院排行+优秀率
             → 挂科预警+波动分析
  ============================================================ -->
  <div class="grade-hub">
    <!-- ========== 顶部标题栏 ========== -->
    <div class="hub-topbar">
      <div class="hub-title-area">
        <h2 class="hub-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="hub-title-icon">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
          成绩分析与教学质量中心
        </h2>
        <p class="hub-subtitle">政治学与公共管理学院 · 教学质量监测中心 · 学情分析平台</p>
      </div>
      <div class="hub-actions">
        <button class="btn-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          录入成绩
        </button>
        <button class="btn-outline">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          导出报表
        </button>
      </div>
    </div>

    <!-- ========== 第1行：4 统计卡片 ========== -->
    <div class="hub-stats-row">
      <div class="hub-stat-card" v-for="stat in gradeStats" :key="stat.label">
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
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="trend-arrow">
                <polyline :points="stat.trendUp ? '18 15 12 9 6 15' : '6 9 12 15 18 9'"/>
              </svg>
              {{ stat.trend }}
            </span>
            {{ stat.sub }}
          </div>
        </div>
        <div class="hub-stat-spark">
          <svg viewBox="0 0 80 28" class="spark-svg">
            <polyline :points="stat.sparkline" fill="none" :stroke="stat.color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- ========== 第2行：GPA分布图 + 成绩区间分析 ========== -->
    <div class="hub-row-2col">
      <!-- 1. GPA分布图 (ECharts 直方图+密度曲线) -->
      <div id="module-gpa-distribution" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/></svg>
            GPA 分布图
          </span>
          <span class="hub-panel-badge">均值 {{ avgGpa }} / 中位 {{ medianGpa }}</span>
        </div>
        <div class="hub-chart-wrap" ref="gpaDistChartRef"></div>
      </div>

      <!-- 2. 成绩区间分析 (ECharts 堆叠柱状图) -->
      <div id="module-score-interval" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            成绩区间分析
          </span>
          <div class="interval-legend">
            <span class="interval-dot" style="background:#1E3A8A"></span>优秀
            <span class="interval-dot" style="background:#3B82F6"></span>良好
            <span class="interval-dot" style="background:#60A5FA"></span>中等
            <span class="interval-dot" style="background:#93C5FD"></span>及格
            <span class="interval-dot" style="background:#DC2626"></span>不及格
          </div>
        </div>
        <div class="hub-chart-wrap" ref="scoreIntervalChartRef"></div>
      </div>
    </div>

    <!-- ========== 第3行：不及格率统计 + 成绩趋势折线图 ========== -->
    <div class="hub-row-2col">
      <!-- 3. 不及格率统计 (ECharts 横向柱状+标记线) -->
      <div id="module-fail-rate" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
            各学院不及格率统计
          </span>
          <span class="hub-panel-badge" style="background:#FEF2F2;color:#DC2626;">警戒线 8%</span>
        </div>
        <div class="hub-chart-wrap" ref="failRateChartRef"></div>
      </div>

      <!-- 4. 成绩趋势折线图 (ECharts 多线) -->
      <div id="module-grade-trend" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
            近5学期成绩趋势
          </span>
          <div class="trend-legend-sm">
            <span class="legend-dot" style="background:#1E3A8A"></span>GPA
            <span class="legend-dot" style="background:#3B82F6"></span>平均分
            <span class="legend-dot" style="background:#60A5FA"></span>优秀率
          </div>
        </div>
        <div class="hub-chart-wrap" ref="gradeTrendChartRef"></div>
      </div>
    </div>

    <!-- ========== 第4行：各学院平均分排行 + 优秀率分析 ========== -->
    <div class="hub-row-2col">
      <!-- 5. 各学院平均分排行 (ECharts 排序柱状图) -->
      <div id="module-college-avg-rank" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>
            </svg>
            各学院平均分排行
          </span>
          <span class="hub-panel-badge">全校均分 {{ schoolAvg }}</span>
        </div>
        <div class="hub-chart-wrap" ref="collegeRankChartRef"></div>
      </div>

      <!-- 6. 优秀率分析 (ECharts 雷达图) -->
      <div id="module-excellence-rate" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            多维优秀率分析
          </span>
          <span class="hub-panel-badge">雷达图</span>
        </div>
        <div class="hub-chart-wrap" ref="radarChartRef"></div>
      </div>
    </div>

    <!-- ========== 第5行：挂科预警 + 成绩波动分析 ========== -->
    <div class="hub-row-2col">
      <!-- 7. 挂科预警列表 -->
      <div id="module-fail-warning" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            挂科预警 · 高危课程
          </span>
          <span class="hub-panel-badge" style="background:#FEF2F2;color:#DC2626;">
            <span class="pulse-dot-sm"></span>
            {{ failWarningCourses.length }} 门
          </span>
        </div>
        <div class="fail-warning-list">
          <div class="fw-item" v-for="(fw, idx) in failWarningCourses" :key="fw.course">
            <div class="fw-rank" :class="'fw-rank-' + (idx + 1)">{{ idx + 1 }}</div>
            <div class="fw-info">
              <span class="fw-course">{{ fw.course }}</span>
              <span class="fw-college">{{ fw.college }}</span>
            </div>
            <div class="fw-metrics">
              <div class="fw-bars">
                <div class="fw-bar-row">
                  <span class="fw-bar-label">不及格率</span>
                  <div class="fw-bar-bg">
                    <div class="fw-bar-fill danger-fill" :style="{ width: fw.failRate + '%' }"></div>
                  </div>
                  <span class="fw-bar-val danger-val">{{ fw.failRate }}%</span>
                </div>
                <div class="fw-bar-row">
                  <span class="fw-bar-label">平均分</span>
                  <div class="fw-bar-bg">
                    <div class="fw-bar-fill warn-fill" :style="{ width: (fw.avgScore / 100 * 100) + '%' }"></div>
                  </div>
                  <span class="fw-bar-val">{{ fw.avgScore }}</span>
                </div>
              </div>
            </div>
            <div class="fw-trend-badge" :class="fw.trend === 'up' ? 'trend-bad' : 'trend-good'">
              {{ fw.trend === 'up' ? '↑ 恶化' : '↓ 改善' }}
            </div>
          </div>
        </div>
      </div>

      <!-- 8. 成绩波动分析 (ECharts) -->
      <div id="module-volatility" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            成绩波动分析
          </span>
          <span class="hub-panel-badge">标准差 {{ volatilityStd }}</span>
        </div>
        <div class="hub-chart-wrap" ref="volatilityChartRef"></div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'

// ========== Reactive State ==========
const gpaDistChartRef = ref<HTMLElement | null>(null)
const scoreIntervalChartRef = ref<HTMLElement | null>(null)
const failRateChartRef = ref<HTMLElement | null>(null)
const gradeTrendChartRef = ref<HTMLElement | null>(null)
const collegeRankChartRef = ref<HTMLElement | null>(null)
const radarChartRef = ref<HTMLElement | null>(null)
const volatilityChartRef = ref<HTMLElement | null>(null)

let gpaDistChart: echarts.ECharts | null = null
let scoreIntervalChart: echarts.ECharts | null = null
let failRateChart: echarts.ECharts | null = null
let gradeTrendChart: echarts.ECharts | null = null
let collegeRankChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null
let volatilityChart: echarts.ECharts | null = null

// ========== 1. 统计卡片 ==========
const avgGpa = computed(() => '3.38')
const medianGpa = computed(() => '3.32')
const schoolAvg = computed(() => '81.2')
const volatilityStd = computed(() => '5.4')

const gradeStats = computed(() => [
  {
    label: '已录入成绩',
    value: '1,826',
    unit: '条',
    trend: '+72',
    trendUp: true,
    sub: '录入率 95.1%',
    icon: 'M9 11l3 3L22 4 M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11',
    bg: '#EFF6FF',
    color: '#1E3A8A',
    sparkline: '0,14 10,17 20,13 30,18 40,15 50,19 60,16 70,20 80,14',
  },
  {
    label: '全院平均分',
    value: '81.2',
    unit: '分',
    trend: '+1.6',
    trendUp: true,
    sub: '较上学期',
    icon: 'M12 20v-6 M6 20V10 M18 20V4',
    bg: '#DBEAFE',
    color: '#3B82F6',
    sparkline: '0,17 10,15 20,18 30,14 40,19 50,15 60,18 70,16 80,19',
  },
  {
    label: '通过率',
    value: '96.5',
    unit: '%',
    trend: '+0.8',
    trendUp: true,
    sub: '不及格仅 62 人次',
    icon: 'M22 12h-4l-3 9L9 3l-3 9H2',
    bg: '#BFDBFE',
    color: '#2563EB',
    sparkline: '0,15 10,18 20,14 30,19 40,16 50,20 60,15 70,18 80,16',
  },
  {
    label: '优秀率',
    value: '16.8',
    unit: '%',
    trend: '+1.4',
    trendUp: true,
    sub: '≥90 分 307 人',
    icon: 'M12 15l-2 2l1-3.5l-2-1.5h2.5L12 8.5l.5 3.5H15l-2 1.5l1 3.5z',
    bg: '#F3F4F6',
    color: '#64748B',
    sparkline: '0,13 10,16 20,12 30,17 40,14 50,18 60,16 70,19 80,15',
  },
])

// ========== 2. GPA分布图 (柱状+密度曲线) ==========
function initGpaDistChart() {
  if (!gpaDistChartRef.value) return
  gpaDistChart = echarts.init(gpaDistChartRef.value)
  const gpaBins = ['0-0.5', '0.5-1.0', '1.0-1.5', '1.5-2.0', '2.0-2.5', '2.5-3.0', '3.0-3.5', '3.5-4.0']
  const counts = [12, 28, 56, 98, 186, 420, 562, 464]
  const densityValues = [0.5, 0.9, 1.6, 3.2, 6.8, 14.2, 22.5, 26.8]

  gpaDistChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 11 }, itemWidth: 14, itemHeight: 8, itemGap: 24 },
    grid: { top: 10, right: 40, bottom: 40, left: 50 },
    xAxis: {
      type: 'category',
      data: gpaBins,
      axisLabel: { color: '#6B7280', fontSize: 10 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#E5E7EB' } },
    },
    yAxis: [
      {
        type: 'value',
        name: '人数',
        nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
        axisLabel: { color: '#6B7280', fontSize: 10 },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      },
      {
        type: 'value',
        name: '密度',
        nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
        axisLabel: { show: false },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '学生数',
        type: 'bar',
        data: counts.map((v, i) => ({
          value: v,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#3B82F6' },
              { offset: 1, color: '#93C5FD' },
            ]),
            borderRadius: [6, 6, 0, 0],
          },
        })),
        barWidth: 28,
        label: { show: true, position: 'top', color: '#3B82F6', fontSize: 10, fontWeight: 600 },
      },
      {
        name: '密度曲线',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: densityValues,
        lineStyle: { width: 3, color: '#1E3A8A' },
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(30, 58, 138, 0.15)' },
            { offset: 1, color: 'rgba(30, 58, 138, 0.01)' },
          ]),
        },
        itemStyle: { color: '#1E3A8A' },
      },
    ],
  })
}

// ========== 3. 成绩区间分析 ==========
function initScoreIntervalChart() {
  if (!scoreIntervalChartRef.value) return
  scoreIntervalChart = echarts.init(scoreIntervalChartRef.value)
  const courses = ['政治学原理', '公共管理学', '行政管理学', '国际关系理论', '社会调查方法', '比较政治学']
  scoreIntervalChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 10 }, itemWidth: 12, itemHeight: 8, itemGap: 16 },
    grid: { top: 10, right: 30, bottom: 40, left: 50 },
    xAxis: {
      type: 'category',
      data: courses,
      axisLabel: { color: '#6B7280', fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '占比(%)',
      nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
      axisLabel: { color: '#6B7280', fontSize: 10 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
    },
    series: [
      { name: '优秀(≥90)', type: 'bar', stack: 'total', data: [20, 16, 14, 18, 12, 15], itemStyle: { color: '#1E3A8A', borderRadius: [0, 0, 0, 0] }, barWidth: 36, emphasis: { focus: 'series' } },
      { name: '良好(80-89)', type: 'bar', stack: 'total', data: [35, 30, 28, 34, 26, 31], itemStyle: { color: '#3B82F6' }, emphasis: { focus: 'series' } },
      { name: '中等(70-79)', type: 'bar', stack: 'total', data: [28, 32, 34, 28, 36, 30], itemStyle: { color: '#60A5FA' }, emphasis: { focus: 'series' } },
      { name: '及格(60-69)', type: 'bar', stack: 'total', data: [13, 17, 19, 15, 22, 19], itemStyle: { color: '#93C5FD' }, emphasis: { focus: 'series' } },
      { name: '不及格(<60)', type: 'bar', stack: 'total', data: [4, 5, 5, 5, 4, 5], itemStyle: { color: '#DC2626', borderRadius: [6, 6, 0, 0] }, emphasis: { focus: 'series' } },
    ],
  })
}

// ========== 4. 不及格率统计 ==========
function initFailRateChart() {
  if (!failRateChartRef.value) return
  failRateChart = echarts.init(failRateChartRef.value)
  const colleges = ['政治学教研室', '公共管理教研室', '国际政治教研室', '科社教研室', '公共政策研究中心', '城市治理研究中心']
  const failRates = [2.8, 3.5, 4.2, 3.1, 5.6, 4.8]

  failRateChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
      formatter: (p: any) => `${p[0].name}<br/>不及格率：<strong>${p[0].value}%</strong>`,
    },
    grid: { top: 10, right: 40, bottom: 10, left: 56 },
    xAxis: { type: 'value', max: 15, axisLabel: { color: '#6B7280', fontSize: 10, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } } },
    yAxis: {
      type: 'category',
      data: colleges,
      axisLabel: { color: '#6B7280', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: failRates.map((v, i) => ({
        value: v,
        itemStyle: {
          color: v >= 8
            ? new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#DC2626' }, { offset: 1, color: '#FEE2E2' }])
            : new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#3B82F6' }, { offset: 1, color: '#DBEAFE' }]),
          borderRadius: [0, 6, 6, 0],
        },
      })),
      barWidth: 18,
      label: { show: true, position: 'right', color: '#374151', fontSize: 11, fontWeight: 600, formatter: '{c}%' },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#DC2626', type: 'dashed', width: 2 },
        label: { color: '#DC2626', fontSize: 10, formatter: '警戒线 8%' },
        data: [{ xAxis: 8 }],
      },
    }],
  })
}

// ========== 5. 成绩趋势折线图 ==========
function initGradeTrendChart() {
  if (!gradeTrendChartRef.value) return
  gradeTrendChart = echarts.init(gradeTrendChartRef.value)
  const semesters = ['2023-1', '2023-2', '2024-1', '2024-2', '2025-1']
  gradeTrendChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 11 }, itemWidth: 14, itemHeight: 8, itemGap: 24 },
    grid: { top: 10, right: 50, bottom: 40, left: 50 },
    xAxis: {
      type: 'category',
      data: semesters,
      axisLabel: { color: '#6B7280', fontSize: 10 },
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisTick: { show: false },
    },
    yAxis: [
      { type: 'value', name: 'GPA/分数', min: 60, max: 100, nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, axisLabel: { color: '#6B7280', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } } },
      { type: 'value', name: '百分比(%)', min: 0, max: 30, nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, axisLabel: { color: '#6B7280', fontSize: 10 }, splitLine: { show: false } },
    ],
    series: [
      {
        name: 'GPA',
        type: 'line',
        smooth: true,
        data: [3.18, 3.22, 3.28, 3.35, 3.42],
        lineStyle: { width: 3, color: '#1E3A8A' },
        symbol: 'circle', symbolSize: 8,
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(30, 58, 138, 0.15)' }, { offset: 1, color: 'rgba(30, 58, 138, 0.01)' }]) },
        itemStyle: { color: '#1E3A8A' },
        label: { show: true, color: '#1E3A8A', fontSize: 10, fontWeight: 600, formatter: '{c}' },
      },
      {
        name: '平均分',
        type: 'line',
        smooth: true,
        data: [78.2, 79.5, 80.2, 80.8, 81.2],
        lineStyle: { width: 3, color: '#3B82F6' },
        symbol: 'diamond', symbolSize: 8,
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(59, 130, 246, 0.12)' }, { offset: 1, color: 'rgba(59, 130, 246, 0.01)' }]) },
        itemStyle: { color: '#3B82F6' },
        label: { show: true, color: '#3B82F6', fontSize: 10, fontWeight: 600, formatter: '{c}' },
      },
      {
        name: '优秀率',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: [13.2, 14.5, 15.2, 16.5, 16.8],
        lineStyle: { width: 2, color: '#60A5FA', type: 'dashed' },
        symbol: 'triangle', symbolSize: 8,
        itemStyle: { color: '#60A5FA' },
        label: { show: true, color: '#60A5FA', fontSize: 10, fontWeight: 600, formatter: '{c}%' },
      },
    ],
  })
}

// ========== 6. 各学院平均分排行 ==========
function initCollegeRankChart() {
  if (!collegeRankChartRef.value) return
  collegeRankChart = echarts.init(collegeRankChartRef.value)
  const collegeData = [
    { name: '国际政治与英语双学位', score: 86.5 },
    { name: '行政管理+电子双学位', score: 84.2 },
    { name: '国际政治专业', score: 82.8 },
    { name: '政治学专业', score: 81.5 },
    { name: '行政管理专业', score: 79.8 },
    { name: '科学社会主义专业', score: 77.2 },
  ]
  const sorted = [...collegeData].sort((a, b) => a.score - b.score)
  const barColors = ['#93C5FD', '#7CB7FB', '#60A5FA', '#4B8EF1', '#3B82F6', '#2563EB', '#1E40AF', '#1E3A8A']

  collegeRankChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    },
    grid: { top: 10, right: 40, bottom: 10, left: 56 },
    xAxis: { type: 'value', min: 60, max: 90, axisLabel: { color: '#6B7280', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } } },
    yAxis: { type: 'category', data: sorted.map(d => d.name), axisLabel: { color: '#6B7280', fontSize: 11 }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar',
      data: sorted.map((d, i) => ({
        value: d.score,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: barColors[i] || '#3B82F6' },
            { offset: 1, color: '#EFF6FF' },
          ]),
          borderRadius: [0, 6, 6, 0],
        },
      })),
      barWidth: 16,
      label: { show: true, position: 'right', color: '#374151', fontSize: 11, fontWeight: 600, formatter: '{c} 分' },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#3B82F6', type: 'dashed', width: 2 },
        label: { color: '#3B82F6', fontSize: 10, formatter: '院均 81.2' },
        data: [{ xAxis: 81.2 }],
      },
    }],
  })
}

// ========== 7. 优秀率雷达图 ==========
function initRadarChart() {
  if (!radarChartRef.value) return
  radarChart = echarts.init(radarChartRef.value)
  radarChart.setOption({
    tooltip: { trigger: 'item', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#374151' } },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 10 }, itemWidth: 12, itemHeight: 8, itemGap: 16 },
    radar: {
      center: ['50%', '45%'],
      radius: '65%',
      indicator: [
        { name: '课堂研讨', max: 100 },
        { name: '政策分析', max: 100 },
        { name: '田野调查', max: 100 },
        { name: '期末考核', max: 100 },
        { name: '批判思维', max: 100 },
        { name: '公共服务', max: 100 },
      ],
      axisName: { color: '#6B7280', fontSize: 10 },
    },
    series: [
      {
        name: '优秀率维度',
        type: 'radar',
        data: [{
          value: [85, 80, 72, 86, 82, 78],
          name: '本学期',
          areaStyle: { color: 'rgba(30, 58, 138, 0.2)' },
          lineStyle: { color: '#1E3A8A', width: 2 },
          itemStyle: { color: '#1E3A8A' },
          symbol: 'circle',
          symbolSize: 6,
        }, {
          value: [80, 76, 68, 83, 78, 74],
          name: '上学期',
          areaStyle: { color: 'rgba(59, 130, 246, 0.1)' },
          lineStyle: { color: '#3B82F6', width: 2, type: 'dashed' },
          itemStyle: { color: '#3B82F6' },
          symbol: 'diamond',
          symbolSize: 6,
        }],
      },
    ],
  })
}

// ========== 8. 成绩波动分析 ==========
function initVolatilityChart() {
  if (!volatilityChartRef.value) return
  volatilityChart = echarts.init(volatilityChartRef.value)
  const months = ['9月', '10月', '11月', '12月', '1月', '3月', '4月', '5月']
  volatilityChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 11 }, itemWidth: 14, itemHeight: 8, itemGap: 24 },
    grid: { top: 10, right: 40, bottom: 40, left: 50 },
    xAxis: {
      type: 'category',
      data: months,
      axisLabel: { color: '#6B7280', fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      name: '标准差',
      nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
      axisLabel: { color: '#6B7280', fontSize: 10 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
    },
    series: [
      {
        name: '成绩标准差',
        type: 'line',
        smooth: true,
        data: [4.8, 5.2, 5.8, 6.2, 5.5, 4.6, 4.2, 5.0],
        lineStyle: { width: 3, color: '#1E3A8A' },
        symbol: 'circle', symbolSize: 6,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(30, 58, 138, 0.2)' },
            { offset: 1, color: 'rgba(30, 58, 138, 0.02)' },
          ]),
        },
        itemStyle: { color: '#1E3A8A' },
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: '#F59E0B', type: 'dashed', width: 2 },
          label: { color: '#F59E0B', fontSize: 10, formatter: '警戒 8.0' },
          data: [{ yAxis: 8.0 }],
        },
      },
      {
        name: '上界 (Mean+1σ)',
        type: 'line',
        smooth: true,
        data: [5.6, 6.0, 6.5, 7.0, 6.2, 5.4, 5.0, 5.8],
        lineStyle: { width: 1, color: '#93C5FD', type: 'dotted' },
        symbol: 'none',
        areaStyle: { color: 'rgba(147, 197, 253, 0.08)' },
      },
      {
        name: '下界 (Mean−1σ)',
        type: 'line',
        smooth: true,
        data: [4.0, 4.4, 5.1, 5.4, 4.8, 3.8, 3.4, 4.2],
        lineStyle: { width: 1, color: '#93C5FD', type: 'dotted' },
        symbol: 'none',
        areaStyle: { color: 'rgba(147, 197, 253, 0.08)' },
      },
    ],
  })
}

// ========== 10. 挂科预警 ==========
const failWarningCourses = [
  { course: '社会调查研究方法', college: '公共管理教研室', failRate: 8.5, avgScore: 64.2, trend: 'up' },
  { course: '计量政治学', college: '政治学教研室', failRate: 7.2, avgScore: 66.8, trend: 'up' },
  { course: '公共财政学', college: '公共管理教研室', failRate: 6.8, avgScore: 68.5, trend: 'down' },
  { course: '国际法', college: '国际政治教研室', failRate: 5.5, avgScore: 71.2, trend: 'down' },
  { course: '公共政策分析', college: '公共政策研究中心', failRate: 4.8, avgScore: 73.8, trend: 'up' },
]

// ========== Lifecycle ==========
onMounted(async () => {
  await nextTick()
  initGpaDistChart()
  initScoreIntervalChart()
  initFailRateChart()
  initGradeTrendChart()
  initCollegeRankChart()
  initRadarChart()
  initVolatilityChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  gpaDistChart?.dispose()
  scoreIntervalChart?.dispose()
  failRateChart?.dispose()
  gradeTrendChart?.dispose()
  collegeRankChart?.dispose()
  radarChart?.dispose()
  volatilityChart?.dispose()
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  gpaDistChart?.resize()
  scoreIntervalChart?.resize()
  failRateChart?.resize()
  gradeTrendChart?.resize()
  collegeRankChart?.resize()
  radarChart?.resize()
  volatilityChart?.resize()
}
</script>

<style scoped>
/* ============================================================
   GRADE HUB — 成绩分析与教学质量中心 样式
   设计方向：BI 分析平台 / 数据中台 / 强图表驱动
   主色调：蓝系 (#1E3A8A → #93C5FD)
   ============================================================ */

/* ---- Layout ---- */
.grade-hub {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0;
}

/* ---- Topbar ---- */
.hub-topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}
.hub-title-area {
  flex: 1;
  min-width: 260px;
}
.hub-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-title);
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  line-height: 1.3;
}
.hub-title-icon {
  width: 22px;
  height: 22px;
  color: var(--color-primary);
  flex-shrink: 0;
}
.hub-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}
.hub-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

/* ---- Semester Tabs ---- */
.semester-tabs {
  display: flex;
  gap: 4px;
  background: #F3F4F6;
  border-radius: 8px;
  padding: 3px;
}
.semester-tab {
  border: none;
  background: transparent;
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  color: #6B7280;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}
.semester-tab.active {
  background: #FFF;
  color: #1E3A8A;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  font-weight: 600;
}
.semester-tab:hover:not(.active) {
  color: #374151;
}

/* ---- Buttons ---- */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: #1E3A8A;
  color: #FFF;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary svg { width: 16px; height: 16px; }
.btn-primary:hover {
  background: #1E40AF;
  box-shadow: 0 2px 8px rgba(30, 58, 138, 0.3);
}
.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #D1D5DB;
  background: #FFF;
  color: #374151;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-outline svg { width: 16px; height: 16px; }
.btn-outline:hover { background: #F9FAFB; border-color: #9CA3AF; }

/* ---- Stat Row ---- */
.hub-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.hub-stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px 22px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
  transition: all 0.25s;
  cursor: default;
}
.hub-stat-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.hub-stat-icon {
  width: 46px; height: 46px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.hub-stat-icon svg { width: 20px; height: 20px; }
.hub-stat-body { flex: 1; min-width: 0; }
.hub-stat-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.hub-stat-value { display: flex; align-items: baseline; gap: 4px; margin-top: 2px; }
.hub-stat-num { font-size: 30px; font-weight: 700; color: var(--text-title); line-height: 1.1; }
.hub-stat-unit { font-size: 13px; color: var(--text-muted); font-weight: 500; }
.hub-stat-sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; display: flex; align-items: center; gap: 4px; }
.hub-stat-trend { display: inline-flex; align-items: center; gap: 2px; font-weight: 600; font-size: 11px; }
.hub-stat-trend.trend-up { color: #2563EB; }
.hub-stat-trend.trend-down { color: #64748B; }
.trend-arrow { width: 12px; height: 12px; }
.hub-stat-spark { position: absolute; bottom: 8px; right: 16px; opacity: 0.35; pointer-events: none; }
.spark-svg { width: 60px; height: 22px; }

/* ---- Grid Layouts ---- */
.hub-row-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* ---- Panel ---- */
.hub-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
}
.hub-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.hub-panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-title);
  display: flex;
  align-items: center;
  gap: 8px;
}
.panel-title-icon {
  width: 16px; height: 16px;
  color: var(--color-primary);
  flex-shrink: 0;
}
.hub-panel-badge {
  font-size: 11px;
  background: #EFF6FF;
  color: var(--color-primary);
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
  white-space: nowrap;
}
.pulse-dot-sm {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #DC2626;
  animation: pulse-dot 1.5s ease-in-out infinite;
  margin-right: 2px;
  vertical-align: middle;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

/* ---- Chart Wrap ---- */
.hub-chart-wrap {
  flex: 1;
  min-height: 260px;
  width: 100%;
}

/* ---- Interval Legend ---- */
.interval-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: var(--text-muted);
  flex-wrap: wrap;
}
.interval-dot {
  display: inline-block;
  width: 10px; height: 10px;
  border-radius: 2px;
}

/* ---- Trend Legend ---- */
.trend-legend-sm {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: var(--text-muted);
  flex-wrap: wrap;
}
.legend-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
}

/* ---- Fail Warning List ---- */
.fail-warning-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.fw-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  border-left: 3px solid transparent;
  transition: background 0.15s;
}
.fw-item:hover { background: #F9FAFB; }
.fw-item:nth-child(1) { border-left-color: #DC2626; background: #FEF2F2; }
.fw-item:nth-child(2) { border-left-color: #DC2626; background: #FFF5F5; }
.fw-item:nth-child(3) { border-left-color: #F59E0B; background: #FFFBEB; }
.fw-rank {
  width: 24px; height: 24px;
  border-radius: 6px;
  background: #F3F4F6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px; font-weight: 700;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.fw-rank-1 { background: #DC2626; color: #FFF; }
.fw-rank-2 { background: #EF4444; color: #FFF; }
.fw-rank-3 { background: #F59E0B; color: #FFF; }
.fw-info { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.fw-course { font-size: 13px; font-weight: 600; color: var(--text-title); }
.fw-college { font-size: 10px; color: var(--text-muted); }
.fw-metrics { flex: 1.5; min-width: 0; }
.fw-bars { display: flex; flex-direction: column; gap: 3px; }
.fw-bar-row { display: flex; align-items: center; gap: 6px; }
.fw-bar-label { font-size: 9px; color: var(--text-muted); width: 48px; text-align: right; flex-shrink: 0; }
.fw-bar-bg { flex: 1; height: 6px; background: #F3F4F6; border-radius: 3px; overflow: hidden; }
.fw-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s; }
.danger-fill { background: #DC2626; }
.warn-fill { background: #F59E0B; }
.fw-bar-val { font-size: 10px; font-weight: 600; color: var(--text-secondary); width: 36px; }
.danger-val { color: #DC2626; }
.fw-trend-badge {
  font-size: 10px; font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}
.trend-bad { background: #FEF2F2; color: #DC2626; }
.trend-good { background: #ECFDF5; color: #059669; }

/* ---- Teaching Metrics Row ---- */
.teaching-metrics-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 4px;
}
.tm-item {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.tm-ring {
  width: 48px; height: 48px;
  position: relative;
}
.tm-ring-svg {
  width: 100%; height: 100%;
  transform: rotate(-90deg);
}
.tm-ring-bg {
  fill: none;
  stroke: #F3F4F6;
  stroke-width: 3;
}
.tm-ring-fill {
  fill: none;
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.5s ease;
}
.tm-ring-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-title);
}
.tm-label {
  font-size: 10px;
  color: var(--text-muted);
}

/* ---- Responsive ---- */
@media (max-width: 1600px) {
  .hub-stats-row { grid-template-columns: repeat(2, 1fr); }
  .teaching-metrics-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 1200px) {
  .hub-row-2col { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .hub-stats-row { grid-template-columns: 1fr; }
  .hub-stat-num { font-size: 24px; }
  .hub-stat-card { padding: 14px 16px; }
  .fw-item { flex-wrap: wrap; }
  .teaching-metrics-row { grid-template-columns: repeat(2, 1fr); }
}
</style>