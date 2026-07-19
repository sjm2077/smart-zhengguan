<template>
  <div
    class="dashboard"
    ref="dashboardRef"
    @dblclick="handleDblclick"
  >
    <!-- 顶部搜索栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <div class="header-logo">
          <span class="logo-icon">🏛️</span>
          <span class="logo-text">智慧政管综合平台</span>
        </div>
      </div>
      <div class="header-center">
        <SearchBar />
      </div>
      <div class="header-right">
        <div class="user-info" @click="goToProfile">
          <span class="user-avatar">{{ currentUser?.avatar || '👤' }}</span>
          <span class="user-name">{{ currentUser?.name || '用户' }}</span>
        </div>
      </div>
    </div>

    <!-- 顶部通栏：KPI区 -->
    <section class="kpi-section">
      <KpiCard
        v-for="kpi in kpiData"
        :key="kpi.key"
        :title="kpi.title"
        :value="kpi.value"
        :unit="kpi.unit"
        :trend="kpi.trend"
        :trend-direction="kpi.trendDirection"
        :gradient="kpi.gradient"
        :color="kpi.color"
        :permission="kpi.permission"
      />
    </section>

    <!-- 中部主体：三栏布局 -->
    <section class="main-section">
      <!-- 左塔：学生学情数据（3张） -->
      <div class="col-left">
        <div class="section-title">
          <span class="title-bar"></span>
          <span class="title-name">学生学情数据</span>
        </div>
        <div class="cards-wrapper">
          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">近五年在院生趋势</h3>
            </div>
            <div ref="lineChartRef" class="chart-body"></div>
          </div>

          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">政管学院男女比例</h3>
            </div>
            <div ref="pieChartRef" class="chart-body"></div>
          </div>

          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">学业完成率</h3>
            </div>
            <div ref="gaugeChartRef" class="chart-body"></div>
          </div>
        </div>
      </div>

      <!-- 中栏：生源地域分布 + 学术关键词词云 -->
      <div class="col-center">
        <div class="section-title center-title">
          <span class="title-bar"></span>
          <span class="title-name">生源地域分布</span>
          <span class="title-bar title-bar-right"></span>
        </div>
        <div class="map-wrapper">
          <div class="chart-card map-card">
            <div class="map-glow-line"></div>
            <div class="map-card-header">
              <button 
                class="map-toggle-btn" 
                :class="{ active: isChinaMap }"
                @click="toggleMapType"
              >
                {{ isChinaMap ? '🌏 国内生源' : '🌍 国际留学' }}
              </button>
            </div>
            <div ref="mapChartRef" class="chart-body map-body"></div>
          </div>
        </div>

        <div class="chart-card wordcloud-card">
          <div class="card-header">
            <h3 class="card-title">学术研究关键词</h3>
          </div>
          <div ref="wordCloudChartRef" class="chart-body wordcloud-body"></div>
        </div>
      </div>

      <!-- 右塔：就业与师资统计（3张） -->
      <div class="col-right">
        <div class="section-title">
          <span class="title-bar"></span>
          <span class="title-name">就业与师资统计</span>
        </div>
        <div class="cards-wrapper">
          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">就业率趋势</h3>
            </div>
            <div ref="employmentChartRef" class="chart-body"></div>
          </div>

          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">专业人数TOP6</h3>
            </div>
            <div ref="barChartRef" class="chart-body"></div>
          </div>

          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">教师职称分布</h3>
            </div>
            <div ref="facultyChartRef" class="chart-body"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- 底部通栏：科研成果数据分析（4张） -->
    <section class="bottom-section">
      <div class="section-title">
        <span class="title-bar"></span>
        <span class="title-name">科研成果数据分析</span>
      </div>
      <div class="bottom-cards">
        <div class="chart-card bottom-card">
          <div class="card-header">
            <h3 class="card-title">科研项目级别分布</h3>
          </div>
          <div ref="bar3ChartRef" class="chart-body"></div>
        </div>

        <div class="chart-card bottom-card">
          <div class="card-header">
            <h3 class="card-title">科研经费来源</h3>
          </div>
          <div ref="fundingChartRef" class="chart-body"></div>
        </div>

        <div class="chart-card bottom-card">
          <div class="card-header">
            <h3 class="card-title">学院综合实力测评</h3>
          </div>
          <div ref="radarChartRef" class="chart-body"></div>
        </div>

        <div class="chart-card bottom-card">
          <div class="card-header">
            <h3 class="card-title">课程类型分布</h3>
          </div>
          <div ref="courseChartRef" class="chart-body"></div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed } from 'vue'
import KpiCard from '../components/KpiCard.vue'
import SearchBar from '../components/SearchBar.vue'
import { useAuthStore } from '../stores/auth'
import { useDashboardStore } from '../stores/dashboard'
import { useRouter } from 'vue-router'

const echarts = window.echarts
const router = useRouter()
const authStore = useAuthStore()
const dashboardStore = useDashboardStore()

const currentUser = computed(() => authStore.currentUser)
const goToProfile = () => router.push('/profile')

// 仪表盘容器引用
const dashboardRef = ref(null)

// 缩放比例相关
const scale = ref(1)
const minScale = 0.6
const maxScale = 1.5
const scaleStep = 0.05

// ResizeObserver 实例
let resizeObserver = null

// 图表引用
const pieChartRef = ref(null)
const barChartRef = ref(null)
const lineChartRef = ref(null)
const radarChartRef = ref(null)
const mapChartRef = ref(null)
const gaugeChartRef = ref(null)
const bar3ChartRef = ref(null)
const employmentChartRef = ref(null)
const facultyChartRef = ref(null)
const fundingChartRef = ref(null)
const courseChartRef = ref(null)
const wordCloudChartRef = ref(null)

// 图表实例
let pieChart = null
let barChart = null
let lineChart = null
let radarChart = null
let mapChart = null
let gaugeChart = null
let bar3Chart = null
let employmentChart = null
let facultyChart = null
let fundingChart = null
let courseChart = null
let wordCloudChart = null

// KPI数据
const kpiData = reactive([
  { key: 'students', title: '在院生总数', value: 1320, unit: '人', trend: 13.5, trendDirection: 'up', gradient: 'linear-gradient(135deg, #00d4ff, #0099cc)', color: '#00d4ff', permission: '' },
  { key: 'staff', title: '专任教职工', value: 93, unit: '人', trend: 2.3, trendDirection: 'up', gradient: 'linear-gradient(135deg, #7b2cbf, #9b59b6)', color: '#7b2cbf', permission: '' },
  { key: 'projects', title: '在研项目数', value: 307, unit: '项', trend: 8.2, trendDirection: 'up', gradient: 'linear-gradient(135deg, #eb2f96, #ff6b9d)', color: '#eb2f96', permission: '' },
  { key: 'funding', title: '五年科研经费', value: 4000, unit: '万元', trend: 15.6, trendDirection: 'up', gradient: 'linear-gradient(135deg, #faad14, #ffc53d)', color: '#faad14', permission: '' },
  { key: 'budget', title: '年度预算执行', value: 910, unit: '万元', trend: 5.1, trendDirection: 'up', gradient: 'linear-gradient(135deg, #52c41a, #73d13d)', color: '#52c41a', permission: '' }
])

kpiData.forEach(kpi => { kpi.permission = authStore.getKpiPermission(kpi.key) })

// 学生性别数据
const studentData = [
  { value: 502, name: '男生', itemStyle: { color: '#00d4ff' } },
  { value: 818, name: '女生', itemStyle: { color: '#7b2cbf' } }
]

// 专业人数数据
const majorData = [
  { name: 'MPA公共管理', value: 300 },
  { name: '行政管理', value: 210 },
  { name: '政治学理论', value: 135 },
  { name: '中共党史', value: 60 },
  { name: '世界史', value: 52 },
  { name: '国际政治', value: 45 }
]

// 在院生趋势数据 - 本科生:研究生=2:1比例
const trendData = {
  years: ['2022', '2023', '2024', '2025', '2026'],
  total: [1280, 1300, 1310, 1315, 1320],
  graduate: [427, 433, 437, 438, 440],      // 约占总数1/3
  undergraduate: [853, 867, 873, 877, 880]  // 约占总数2/3
}

// 就业率数据
const employmentData = {
  years: ['2021', '2022', '2023', '2024', '2025'],
  rate: [93, 94, 95, 96, 97],
  state: [45, 46, 47, 48, 49],
  enterprise: [35, 36, 37, 38, 39]
}

// 雷达图数据 - 文字换行处理
const radarData = {
  indicator: [
    { name: '科研\n产出', max: 100 },
    { name: '师资\n力量', max: 100 },
    { name: '国际\n化办学', max: 100 },
    { name: '社会\n服务', max: 100 },
    { name: '人才\n培养质量', max: 100 }
  ],
  value: [88, 92, 75, 85, 90]
}

// 教师职称数据
const facultyData = [
  { name: '教授', value: 37, itemStyle: { color: '#7b2cbf' } },
  { name: '副教授', value: 29, itemStyle: { color: '#00d4ff' } },
  { name: '讲师', value: 27, itemStyle: { color: '#52c41a' } }
]

// 科研经费数据
const fundingData = [
  { name: '国家级课题', value: 1650 },
  { name: '省部级课题', value: 1320 },
  { name: '横向合作', value: 790 },
  { name: '校级科研', value: 240 }
]

// 课程类型数据
const courseData = [
  { name: '专业核心课', value: 46 },
  { name: '公共基础课', value: 34 },
  { name: '社会实践实训', value: 13 },
  { name: '通识选修课', value: 7 }
]

// 科研项目级别数据
const projectLevelData = [
  { name: '国家级', value: 36 },
  { name: '省部级', value: 112 },
  { name: '市厅级', value: 94 },
  { name: '横向合作', value: 65 }
]

// 学术研究关键词数据
const wordCloudData = [
  { name: '公共管理', value: 100 },
  { name: '行政管理', value: 92 },
  { name: '政治学理论', value: 85 },
  { name: '地方治理', value: 78 },
  { name: '公共政策', value: 72 },
  { name: '社会治理', value: 68 },
  { name: '比较政治', value: 55 },
  { name: '电子政务', value: 50 },
  { name: '绩效管理', value: 45 },
  { name: '非营利组织', value: 38 },
  { name: '基层治理', value: 35 }
]

// 地图数据 - 国内生源
const mapData = [
  { name: '北京', value: 50 }, { name: '天津', value: 25 },
  { name: '河北', value: 180 }, { name: '山西', value: 80 },
  { name: '内蒙古', value: 20 }, { name: '辽宁', value: 40 },
  { name: '吉林', value: 30 }, { name: '黑龙江', value: 30 },
  { name: '上海', value: 40 }, { name: '江苏', value: 150 },
  { name: '浙江', value: 100 }, { name: '安徽', value: 70 },
  { name: '福建', value: 50 }, { name: '江西', value: 60 },
  { name: '山东', value: 500 }, { name: '河南', value: 120 },
  { name: '湖北', value: 60 }, { name: '湖南', value: 70 },
  { name: '广东', value: 100 }, { name: '广西', value: 30 },
  { name: '海南', value: 15 }, { name: '重庆', value: 40 },
  { name: '四川', value: 80 }, { name: '贵州', value: 30 },
  { name: '云南', value: 40 }, { name: '西藏', value: 5 },
  { name: '陕西', value: 50 }, { name: '甘肃', value: 25 },
  { name: '青海', value: 8 }, { name: '宁夏', value: 12 },
  { name: '新疆', value: 20 }, { name: '台湾', value: 15 },
  { name: '香港', value: 8 }, { name: '澳门', value: 3 }
]

// 世界地图数据 - 国际留学生
const worldMapData = [
  { name: 'United States', value: 45 }, { name: 'Canada', value: 12 },
  { name: 'United Kingdom', value: 38 }, { name: 'France', value: 15 },
  { name: 'Germany', value: 20 }, { name: 'Italy', value: 8 },
  { name: 'Australia', value: 25 }, { name: 'New Zealand', value: 6 },
  { name: 'Japan', value: 52 }, { name: 'Korea', value: 35 },
  { name: 'Singapore', value: 18 }, { name: 'Malaysia', value: 10 },
  { name: 'Indonesia', value: 5 }, { name: 'India', value: 8 },
  { name: 'Thailand', value: 12 }, { name: 'Vietnam', value: 6 },
  { name: 'Russia', value: 15 }, { name: 'Kazakhstan', value: 4 },
  { name: 'Brazil', value: 8 }, { name: 'Mexico', value: 6 },
  { name: 'Saudi Arabia', value: 10 }, { name: 'Egypt', value: 5 },
  { name: 'South Africa', value: 6 }, { name: 'Nigeria', value: 3 }
]

const isChinaMap = ref(true)

// 小省份列表 - 默认隐藏标签
const smallProvinces = ['天津', '上海', '北京', '宁夏', '海南', '台湾', '香港', '澳门']

// 统一tooltip样式
const tooltipStyle = {
  backgroundColor: 'rgba(10, 25, 50, 0.95)',
  borderColor: 'rgba(0, 212, 255, 0.4)',
  borderWidth: 1,
  textStyle: { color: '#fff', fontSize: 12 }
}

// 初始化饼图 - 男女比例
const initPieChart = () => {
  if (!pieChartRef.value) return
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: {
      orient: 'horizontal',
      bottom: 8,
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 13 },
      itemWidth: 14,
      itemHeight: 14,
      itemGap: 20
    },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '45%'],
      label: {
        show: true,
        position: 'inside',
        formatter: '{d}%',
        color: '#fff',
        fontSize: 14,
        fontWeight: 'bold'
      },
      labelLine: { show: false },
      data: studentData,
      emphasis: {
        itemStyle: { shadowBlur: 25, shadowColor: 'rgba(0, 212, 255, 0.5)' }
      }
    }]
  })
}

// 初始化横向柱状图 - 专业人数
const initBarChart = () => {
  if (!barChartRef.value) return
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 100, right: 60, top: 18, bottom: 35 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.65)', fontSize: 12, margin: 10 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: majorData.map(item => item.name).reverse(),
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 20,
      data: majorData.slice().reverse().map(item => ({
        value: item.value,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: 'rgba(0,212,255,0.15)' },
            { offset: 1, color: '#00d4ff' }
          ]),
          borderRadius: [0, 6, 6, 0]
        }
      })),
      label: {
        show: true,
        position: 'right',
        color: '#00d4ff',
        fontSize: 12,
        fontWeight: 'bold',
        distance: 10
      }
    }]
  })
}

// 初始化折线图 - 在院生趋势
const initLineChart = () => {
  if (!lineChartRef.value) return
  lineChart = echarts.init(lineChartRef.value)
  const totalGradient = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: 'rgba(0,212,255,0.3)' },
    { offset: 1, color: 'rgba(0,212,255,0.02)' }
  ])
  const gradGradient = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: 'rgba(123,44,191,0.3)' },
    { offset: 1, color: 'rgba(123,44,191,0.02)' }
  ])
  const underGradient = new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: 'rgba(82,196,26,0.3)' },
    { offset: 1, color: 'rgba(82,196,26,0.02)' }
  ])

  lineChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'axis' },
    legend: {
      data: ['总人数', '研究生', '本科生'],
      bottom: 5,
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 12 },
      itemWidth: 16,
      itemHeight: 8,
      itemGap: 18
    },
    grid: { left: 55, right: 25, top: 18, bottom: 48 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trendData.years,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.75)', fontSize: 12 }
    },
    yAxis: {
      type: 'value',
      min: 400,
      max: 1400,
      interval: 200,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    series: [
      {
        name: '总人数', type: 'line', smooth: true,
        data: trendData.total,
        lineStyle: { color: '#00d4ff', width: 3 },
        areaStyle: { color: totalGradient },
        symbolSize: 8,
        itemStyle: { color: '#00d4ff' }
      },
      {
        name: '研究生', type: 'line', smooth: true,
        data: trendData.graduate,
        lineStyle: { color: '#7b2cbf', width: 3 },
        areaStyle: { color: gradGradient },
        symbolSize: 8,
        itemStyle: { color: '#7b2cbf' }
      },
      {
        name: '本科生', type: 'line', smooth: true,
        data: trendData.undergraduate,
        lineStyle: { color: '#52c41a', width: 3 },
        areaStyle: { color: underGradient },
        symbolSize: 8,
        itemStyle: { color: '#52c41a' }
      }
    ]
  })
}

// 初始化就业率趋势图
const initEmploymentChart = () => {
  if (!employmentChartRef.value) return
  employmentChart = echarts.init(employmentChartRef.value)
  employmentChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'axis' },
    legend: {
      data: ['总就业率', '公职单位', '企业'],
      bottom: 5,
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 12 },
      itemWidth: 14,
      itemHeight: 7,
      itemGap: 16
    },
    grid: { left: 55, right: 55, top: 18, bottom: 48 },
    xAxis: {
      type: 'category',
      data: employmentData.years,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.75)', fontSize: 12, margin: 8 }
    },
    yAxis: [
      {
        type: 'value',
        min: 80,
        max: 100,
        interval: 5,
        axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
        axisLabel: { color: 'rgba(255,255,255,0.6)', formatter: '{value}%', fontSize: 12 },
        splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
      },
      {
        type: 'value',
        min: 30,
        max: 60,
        interval: 10,
        axisLine: { lineStyle: { color: 'rgba(123,44,191,0.25)' } },
        axisLabel: { color: 'rgba(255,255,255,0.6)', formatter: '{value}%', fontSize: 12 },
        splitLine: { show: false }
      }
    ],
    series: [
      {
        name: '总就业率', type: 'line', smooth: true,
        data: employmentData.rate,
        lineStyle: { color: '#52c41a', width: 3 },
        symbol: 'circle', symbolSize: 8,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '公职单位', type: 'line', yAxisIndex: 1, smooth: true,
        data: employmentData.state,
        lineStyle: { color: '#00d4ff', width: 3 },
        symbol: 'circle', symbolSize: 8,
        itemStyle: { color: '#00d4ff' }
      },
      {
        name: '企业', type: 'line', yAxisIndex: 1, smooth: true,
        data: employmentData.enterprise,
        lineStyle: { color: '#faad14', width: 3 },
        symbol: 'circle', symbolSize: 8,
        itemStyle: { color: '#faad14' }
      }
    ]
  })
}

// 初始化雷达图 - 学院综合实力
const initRadarChart = () => {
  if (!radarChartRef.value) return
  radarChart = echarts.init(radarChartRef.value)
  const radarAreaColor = new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
    { offset: 0, color: 'rgba(0,212,255,0.25)' },
    { offset: 1, color: 'rgba(0,212,255,0.05)' }
  ])

  radarChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle },
    radar: {
      indicator: radarData.indicator,
      shape: 'polygon',
      splitNumber: 4,
      radius: '65%',
      center: ['50%', '55%'],
      axisName: {
        color: 'rgba(255,255,255,0.85)',
        fontSize: 12,
        lineHeight: 16,
        padding: [8, 0, 8, 0]
      },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.2)' } },
      splitArea: {
        areaStyle: {
          color: ['rgba(0,212,255,0.02)', 'rgba(0,212,255,0.05)']
        }
      },
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.3)' } }
    },
    series: [{
      type: 'radar',
      data: [{
        value: radarData.value,
        name: '综合评分',
        areaStyle: { opacity: 0.25, color: radarAreaColor },
        lineStyle: { color: '#00d4ff', width: 2.5 },
        itemStyle: { color: '#00d4ff' }
      }]
    }]
  })
}

// 初始化教师职称饼图
const initFacultyChart = () => {
  if (!facultyChartRef.value) return
  facultyChart = echarts.init(facultyChartRef.value)
  facultyChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: {
      orient: 'vertical',
      right: 12,
      top: 'center',
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 12 },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 15
    },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['32%', '50%'],
      label: {
        show: true,
        position: 'inside',
        formatter: '{d}%',
        color: '#fff',
        fontSize: 13,
        fontWeight: 'bold'
      },
      labelLine: { show: false },
      data: facultyData,
      emphasis: {
        itemStyle: { shadowBlur: 25, shadowColor: 'rgba(0, 212, 255, 0.5)' }
      }
    }]
  })
}

// 初始化科研经费来源图
const initFundingChart = () => {
  if (!fundingChartRef.value) return
  fundingChart = echarts.init(fundingChartRef.value)
  const colors = ['#7b2cbf', '#00d4ff', '#faad14', '#52c41a']

  fundingChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 90, right: 55, top: 18, bottom: 35 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: {
        color: 'rgba(255,255,255,0.65)',
        fontSize: 12,
        margin: 10,
        formatter: function(v) {
          return v >= 1000 ? (v / 1000).toFixed(1) + '千万' : v + '万'
        }
      },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: fundingData.map(item => item.name),
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 18,
      data: fundingData.map((item, index) => ({
        value: item.value,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: colors[index] + '25' },
            { offset: 1, color: colors[index] }
          ]),
          borderRadius: [0, 6, 6, 0]
        }
      })),
      label: {
        show: true,
        position: 'right',
        color: '#fff',
        fontSize: 12,
        fontWeight: '500'
      }
    }]
  })
}

// 初始化课程类型饼图
const initCourseChart = () => {
  if (!courseChartRef.value) return
  courseChart = echarts.init(courseChartRef.value)
  courseChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'item', formatter: '{b}: {c}门 ({d}%)' },
    legend: {
      orient: 'horizontal',
      bottom: 8,
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 12 },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 18
    },
    series: [{
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['50%', '42%'],
      label: {
        show: true,
        position: 'inside',
        formatter: '{d}%',
        color: '#fff',
        fontSize: 13,
        fontWeight: 'bold'
      },
      labelLine: { show: false },
      data: courseData.map((item, index) => ({
        value: item.value,
        name: item.name,
        itemStyle: { color: ['#00d4ff', '#7b2cbf', '#faad14', '#52c41a'][index] }
      })),
      emphasis: {
        itemStyle: { shadowBlur: 25, shadowColor: 'rgba(0, 212, 255, 0.5)' }
      }
    }]
  })
}

// 切换地图类型
const toggleMapType = () => {
  isChinaMap.value = !isChinaMap.value
  if (mapChart) {
    mapChart.dispose()
    initMapChart()
  }
}

// 初始化地图
const initMapChart = () => {
  if (!mapChartRef.value) return
  mapChart = echarts.init(mapChartRef.value)

  const currentMap = isChinaMap.value ? 'china' : 'world'
  const currentData = isChinaMap.value ? mapData : worldMapData
  const maxValue = isChinaMap.value ? 500 : 52

  const worldLabelFormatter = function(params) {
    const hasData = worldMapData.some(item => item.name === params.name)
    return hasData ? params.name : ''
  }

  mapChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      ...tooltipStyle,
      trigger: 'item',
      formatter: function(params) {
        const total = isChinaMap.value ? 1320 : 300
        return params.name + ': ' + params.value + '人 (' + ((params.value / total) * 100).toFixed(1) + '%)'
      }
    },
    visualMap: {
      type: 'piecewise',
      right: 16,
      bottom: 16,
      orient: 'vertical',
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 11 },
      pieces: isChinaMap.value ? [
        { max: 500, min: 400, label: '>400', color: '#7b2cbf' },
        { max: 399, min: 100, label: '100-399', color: '#00b8d4' },
        { max: 99, min: 50, label: '50-99', color: '#00698c' },
        { max: 49, min: 0, label: '<50', color: '#004a66' }
      ] : [
        { max: 52, min: 30, label: '>30', color: '#7b2cbf' },
        { max: 29, min: 15, label: '15-29', color: '#00b8d4' },
        { max: 14, min: 5, label: '5-14', color: '#00698c' },
        { max: 4, min: 0, label: '<5', color: '#004a66' }
      ],
      itemWidth: 14,
      itemHeight: 14,
      gap: 4
    },
    geo: {
      map: currentMap,
      roam: true,
      zoom: isChinaMap.value ? 1.25 : 1,
      center: isChinaMap.value ? [105, 36] : [0, 20],
      label: {
        show: true,
        color: '#b8dfff',
        fontSize: isChinaMap.value ? 12 : 10,
        textShadowBlur: 6,
        textShadowColor: 'rgba(0, 212, 255, 0.5)',
        formatter: isChinaMap.value ? undefined : worldLabelFormatter
      },
      itemStyle: {
        areaColor: '#0d1f3a',
        borderColor: 'rgba(0, 212, 255, 0.45)',
        borderWidth: 1.2,
        shadowColor: 'rgba(0, 212, 255, 0.35)',
        shadowBlur: 30
      },
      emphasis: {
        label: {
          show: true,
          color: '#fff',
          fontSize: isChinaMap.value ? 13 : 11,
          fontWeight: 'bold'
        },
        itemStyle: { areaColor: '#ff4d4f' }
      }
    },
    series: [{
      name: isChinaMap.value ? '国内生源' : '国际留学生',
      type: 'map',
      map: currentMap,
      geoIndex: 0,
      data: currentData
    }]
  })
}

// 初始化学术关键词词云图
const initWordCloudChart = () => {
  if (!wordCloudChartRef.value) return
  wordCloudChart = echarts.init(wordCloudChartRef.value)
  
  wordCloudChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      ...tooltipStyle,
      formatter: function(params) {
        return params.name + ': ' + params.value + '热度'
      }
    },
    series: [{
      type: 'wordCloud',
      gridSize: 10,
      sizeRange: [14, 36],
      rotationRange: [-15, 15],
      rotationStep: 15,
      shape: 'circle',
      left: 'center',
      top: 'center',
      width: '92%',
      height: '92%',
      padding: [15, 15, 15, 15],
      textStyle: {
        color: function() {
          const colors = ['#00d4ff', '#7b2cbf', '#faad14', '#52c41a', '#eb2f96', '#13c2c2']
          return colors[Math.floor(Math.random() * colors.length)]
        },
        fontSize: function(value) {
          return value * 0.3 + 14
        },
        fontWeight: 'bold',
        textShadowColor: 'rgba(0, 0, 0, 0.3)',
        textShadowBlur: 4
      },
      emphasis: {
        focus: 'self',
        textStyle: {
          color: '#fff',
          textShadowBlur: 15,
          textShadowColor: 'rgba(0, 212, 255, 0.8)'
        }
      },
      data: wordCloudData
    }]
  })
}

// 初始化仪表盘 - 学业完成率
const initGaugeChart = () => {
  if (!gaugeChartRef.value) return
  gaugeChart = echarts.init(gaugeChartRef.value)
  gaugeChart.setOption({
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge',
      radius: '72%',
      center: ['50%', '58%'],
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      splitNumber: 5,
      axisLine: {
        lineStyle: {
          width: 14,
          color: [
            [0.3, '#00d4ff'],
            [0.7, '#7b2cbf'],
            [1, '#52c41a']
          ],
          shadowColor: 'rgba(0, 212, 255, 0.4)',
          shadowBlur: 18
        }
      },
      pointer: {
        itemStyle: { color: '#00d4ff', shadowColor: 'rgba(0, 212, 255, 0.6)', shadowBlur: 12 },
        length: '58%',
        width: 5
      },
      axisTick: { show: false },
      splitLine: {
        length: 14,
        lineStyle: { color: 'rgba(255,255,255,0.8)', width: 2.5 }
      },
      axisLabel: {
        color: '#ffffff',
        distance: -20,
        fontSize: 12,
        fontWeight: 'bold',
        textShadowBlur: 6,
        textShadowColor: 'rgba(0, 212, 255, 0.6)'
      },
      detail: {
        valueAnimation: true,
        formatter: '{value}%',
        color: '#00d4ff',
        fontSize: 26,
        fontWeight: 'bold',
        offsetCenter: [0, '20%'],
        textShadowBlur: 12,
        textShadowColor: 'rgba(0, 212, 255, 0.5)'
      },
      title: {
        text: '学业完成率',
        offsetCenter: [0, '65%'],
        fontSize: 13,
        color: 'rgba(255,255,255,0.75)',
        fontWeight: '500'
      },
      data: [{ value: 94 }]
    }]
  })
}

// 初始化科研项目级别分布图
const initBar3Chart = () => {
  if (!bar3ChartRef.value) return
  bar3Chart = echarts.init(bar3ChartRef.value)
  const barGradient = new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: 'rgba(123,44,191,0.2)' },
    { offset: 1, color: '#7b2cbf' }
  ])

  bar3Chart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 80, right: 60, top: 18, bottom: 35 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.65)', fontSize: 12, margin: 10 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: projectLevelData.map(item => item.name),
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 20,
      data: projectLevelData.map(item => ({
        value: item.value,
        itemStyle: { color: barGradient, borderRadius: [0, 6, 6, 0] }
      })),
      label: {
        show: true,
        position: 'right',
        color: '#7b2cbf',
        fontSize: 12,
        fontWeight: 'bold',
        distance: 10
      }
    }]
  })
}

// 初始化所有图表
const initCharts = () => {
  initPieChart()
  initBarChart()
  initLineChart()
  initEmploymentChart()
  initRadarChart()
  initFacultyChart()
  initFundingChart()
  initCourseChart()
  initMapChart()
  initWordCloudChart()
  initGaugeChart()
  initBar3Chart()
}

// 窗口大小变化时重绘图表
const handleResize = () => {
  const charts = [
    pieChart, barChart, lineChart, employmentChart, radarChart,
    facultyChart, fundingChart, courseChart, mapChart, wordCloudChart,
    gaugeChart, bar3Chart
  ]
  charts.forEach(chart => {
    if (chart) chart.resize()
  })
}

// 滚轮缩放处理
const handleWheel = (e) => {
  if (e.deltaY < 0) {
    // 向上滚动 - 放大
    scale.value = Math.min(maxScale, scale.value + scaleStep)
  } else {
    // 向下滚动 - 缩小
    scale.value = Math.max(minScale, scale.value - scaleStep)
  }
  // 缩放后重绘图表
  nextTick(() => {
    handleResize()
  })
}

// 双击重置缩放
const handleDblclick = () => {
  scale.value = 1
  nextTick(() => {
    handleResize()
  })
}

// 生命周期
onMounted(() => {
  dashboardStore.updateData({
    students: kpiData.find(k => k.key === 'students')?.value || 1320,
    staff: kpiData.find(k => k.key === 'staff')?.value || 93,
    projects: kpiData.find(k => k.key === 'projects')?.value || 307,
    funding: kpiData.find(k => k.key === 'funding')?.value || 4000,
    budget: kpiData.find(k => k.key === 'budget')?.value || 910,
    maleRatio: ((studentData.find(s => s.name === '男生')?.value || 0) / 
               ((studentData.find(s => s.name === '男生')?.value || 0) + 
                (studentData.find(s => s.name === '女生')?.value || 0)) * 100).toFixed(2) || 38.03,
    femaleRatio: ((studentData.find(s => s.name === '女生')?.value || 0) / 
                 ((studentData.find(s => s.name === '男生')?.value || 0) + 
                  (studentData.find(s => s.name === '女生')?.value || 0)) * 100).toFixed(2) || 61.97
  })
  
  nextTick(() => {
    setTimeout(() => {
      initCharts()
    }, 100)
  })
  if (dashboardRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      handleResize()
    })
    resizeObserver.observe(dashboardRef.value)
  }
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  // 停止 ResizeObserver
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  const charts = [
    pieChart, barChart, lineChart, employmentChart, radarChart,
    facultyChart, fundingChart, courseChart, mapChart, wordCloudChart,
    gaugeChart, bar3Chart
  ]
  charts.forEach(chart => {
    if (chart) chart.dispose()
  })
})
</script>

<style scoped>
/* ==================== 全局基础 ==================== */
.dashboard {
  width: 100%;
  min-height: calc(100vh - 170px - 20px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0 16px 24px;
  background: #0a1628;
  overflow-y: auto;
  overflow-x: hidden;
  animation: fadeIn 0.6s ease;
  transform-origin: center top;
}

.dashboard::-webkit-scrollbar {
  width: 8px;
}
.dashboard::-webkit-scrollbar-track {
  background: rgba(0, 212, 255, 0.05);
  border-radius: 4px;
}
.dashboard::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, #00d4ff, #7b2cbf);
  border-radius: 4px;
}
.dashboard::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, #00e5ff, #8b3ccf);
}

.dashboard:active {
  cursor: grabbing;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ==================== 分组标题样式 ==================== */
.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  padding-bottom: 10px;
  flex-shrink: 0;
}

.center-title {
  justify-content: center;
}

.title-bar {
  width: 4px;
  height: 16px;
  background: linear-gradient(180deg, #00d4ff, #7b2cbf);
  border-radius: 2px;
  flex-shrink: 0;
}

.title-bar-right {
  background: linear-gradient(180deg, #7b2cbf, #00d4ff);
}

.title-name {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 1px;
}

/* ==================== 顶部KPI区 ==================== */
.kpi-section {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
}

/* ==================== 中部主体区 ==================== */
.main-section {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}

.col-left,
.col-right {
  grid-column: span 3;
  display: flex;
  flex-direction: column;
}

.col-center {
  grid-column: span 6;
  display: flex;
  flex-direction: column;
}

.cards-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.map-wrapper {
  height: 560px;
  position: relative;
}

/* ==================== 卡片通用样式 ==================== */
.chart-card {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 12px;
  background: rgba(16, 32, 64, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.25);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}

.chart-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.6), transparent);
  z-index: 2;
}

.chart-card:hover {
  border-color: rgba(0, 212, 255, 0.45);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.08);
  transform: translateY(-2px);
}

.card-header {
  padding: 16px 18px 12px;
  flex-shrink: 0;
}

.card-title {
  font-size: 15px;
  color: #fff;
  font-weight: 600;
  margin: 0;
  letter-spacing: 0.5px;
}

.chart-body {
  flex: 1;
  min-height: 0;
  width: 100%;
  padding: 0 18px 18px;
  box-sizing: border-box;
}

/* 左右塔卡片固定高度 */
.cards-wrapper .chart-card {
  height: 260px;
  flex-shrink: 0;
}

/* ==================== 核心地图卡片 ==================== */
.map-card {
  height: 100%;
  background: linear-gradient(180deg, rgba(12, 26, 52, 0.85) 0%, rgba(8, 18, 38, 0.95) 100%);
  border: 1px solid rgba(0, 212, 255, 0.35);
  box-shadow:
    0 0 50px rgba(0, 212, 255, 0.15),
    0 6px 24px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.map-card-header {
  padding: 8px 16px;
  display: flex;
  justify-content: flex-end;
}

.map-toggle-btn {
  padding: 6px 16px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.map-toggle-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.5);
  color: #fff;
}

.map-toggle-btn.active {
  background: rgba(0, 212, 255, 0.25);
  border-color: rgba(0, 212, 255, 0.6);
  color: #00d4ff;
}

.map-glow-line {
  position: absolute;
  top: 0;
  left: 8%;
  right: 8%;
  height: 3px;
  background: linear-gradient(90deg, transparent, #00d4ff, #7b2cbf, #00d4ff, transparent);
  z-index: 3;
  filter: blur(1px);
}

.map-body {
  padding: 16px 18px 18px;
}

/* ==================== 词云区域 ==================== */
.wordcloud-card {
  height: 230px;
  flex-shrink: 0;
  margin-top: 16px;
}

.wordcloud-body {
  padding: 0 16px 14px;
}

/* ==================== 底部通栏 ==================== */
.bottom-section {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.bottom-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.bottom-card {
  height: 320px;
}

.bottom-card .chart-body {
  padding: 0 18px 16px;
}

/* ==================== 响应式 ==================== */
@media (max-width: 1600px) {
  .dashboard {
    gap: 10px;
    padding: 0 10px 20px;
  }
  .kpi-section { gap: 10px; }
  .main-section { gap: 10px; }
  .cards-wrapper { gap: 10px; }
  .bottom-cards { gap: 10px; }
  .card-header { padding: 12px 12px 8px; }
  .chart-body { padding: 0 12px 12px; }
  .map-body { padding: 14px 16px 16px; }
}

@media (max-width: 1366px) {
  .dashboard { height: calc(100vh - 160px - 15px); }
  .card-title { font-size: 12px; }
  .title-name { font-size: 14px; }
  .bottom-section { height: 220px; }
}

@media (max-width: 1200px) {
  .dashboard {
    height: auto;
    min-height: auto;
    overflow: visible;
    padding-bottom: 25px;
  }
  .main-section { grid-template-columns: 1fr; height: auto; }
  .col-left, .col-right { display: block; }
  .cards-wrapper {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    height: auto;
  }
  .col-center { min-height: 450px; }
  .bottom-section { height: auto; }
  .bottom-cards {
    grid-template-columns: repeat(2, 1fr);
    height: auto;
  }
}

@media (max-width: 768px) {
  .kpi-section { grid-template-columns: repeat(2, 1fr); }
  .cards-wrapper { grid-template-columns: 1fr; }
  .bottom-cards { grid-template-columns: 1fr; }
  .map-body { padding: 10px 12px 12px; }
}

/* ==================== 顶部搜索栏 ==================== */
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 10px 20px;
  margin-bottom: 10px;
  background: rgba(10, 25, 50, 0.5);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}
.header-left {
  flex-shrink: 0;
}
.header-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-icon {
  font-size: 28px;
  filter: drop-shadow(0 0 8px rgba(0, 212, 255, 0.4));
}
.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  white-space: nowrap;
}
.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  max-width: 520px;
}
.header-right {
  flex-shrink: 0;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 30px;
  background: rgba(0, 212, 255, 0.08);
  border: 1px solid rgba(0, 212, 255, 0.15);
  transition: all 0.3s;
}
.user-info:hover {
  background: rgba(0, 212, 255, 0.18);
  border-color: rgba(0, 212, 255, 0.4);
}
.user-avatar {
  font-size: 22px;
}
.user-name {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
}
</style>
