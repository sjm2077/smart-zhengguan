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
        :source-text="kpi.sourceText"
        :source-type="kpi.sourceType"
      />
    </section>

    <!-- 中部主体：三栏布局 -->
    <section class="main-section">
      <!-- 左塔：全院学生规模（3张） -->
      <div class="col-left">
        <div class="section-title">
          <span class="title-bar"></span>
          <span class="title-name">全院学生规模与结构</span>
        </div>
        <div class="cards-wrapper">
          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">各培养层次年招生规模（人/年）<span class="demo-tag official">学院官网</span></h3>
            </div>
            <div ref="lineChartRef" class="chart-body"></div>
          </div>

          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">全院在院生构成<span class="demo-tag">官网×学制估算</span></h3>
            </div>
            <div ref="pieChartRef" class="chart-body"></div>
          </div>

          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">学业完成率<span class="demo-tag">教学系统</span></h3>
            </div>
            <div ref="gaugeChartRef" class="chart-body"></div>
          </div>
        </div>
      </div>

      <!-- 中栏：生源地域分布 + 学术关键词词云 -->
      <div class="col-center">
        <div class="section-title center-title">
          <span class="title-bar"></span>
          <span class="title-name">生源地域分布<span class="demo-tag">全院示意估算</span></span>
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
            <h3 class="card-title">学术研究关键词<span class="demo-tag official">官网论文</span></h3>
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
              <h3 class="card-title">就业率趋势<span class="demo-tag">演示数据</span></h3>
            </div>
            <div ref="employmentChartRef" class="chart-body"></div>
          </div>

          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">各系专任教师规模<span class="demo-tag official">学院官网</span></h3>
            </div>
            <div ref="barChartRef" class="chart-body"></div>
          </div>

          <div class="chart-card">
            <div class="card-header">
              <h3 class="card-title">教师职称分布<span class="demo-tag official">学院官网</span></h3>
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
            <h3 class="card-title">科研项目级别分布<span class="demo-tag official">学院官网</span></h3>
          </div>
          <div ref="bar3ChartRef" class="chart-body"></div>
        </div>

        <div class="chart-card bottom-card">
          <div class="card-header">
            <h3 class="card-title">官网学术成果年度分布<span class="demo-tag official">官网爬取</span></h3>
          </div>
          <div ref="fundingChartRef" class="chart-body"></div>
        </div>

        <div class="chart-card bottom-card">
          <div class="card-header">
            <h3 class="card-title">官网科研产出构成<span class="demo-tag official">官网原文</span></h3>
          </div>
          <div ref="radarChartRef" class="chart-body"></div>
        </div>

        <div class="chart-card bottom-card">
          <div class="card-header">
            <h3 class="card-title">课程类型分布<span class="demo-tag">教学系统</span></h3>
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

// KPI数据（全院口径：本科 + 硕士 + 博士 + MPA + 留学生，不再只统计研究生子系统）
// 官网《学院简介》只公布“每年招生规模”，在校生数按 年招生 × 标准学制 换算，卡片角标如实标注“估算”。
// sourceText/sourceType：official=学院官网原文；est=官网口径换算的估算值；sub=子系统；demo=演示
const kpiData = reactive([
  { key: 'students', title: '全院在校生', value: 2420, unit: '人', trend: 0, trendDirection: 'up', gradient: 'linear-gradient(135deg, #00d4ff, #0099cc)', color: '#00d4ff', permission: '', sourceText: '官网招生×学制', sourceType: 'est' },
  { key: 'undergrad', title: '本科在校生', value: 600, unit: '人', trend: 0, trendDirection: 'up', gradient: 'linear-gradient(135deg, #13c2c2, #36cfc9)', color: '#13c2c2', permission: '', sourceText: '150人/年×4年', sourceType: 'est' },
  { key: 'master', title: '硕士在校生', value: 1560, unit: '人', trend: 0, trendDirection: 'up', gradient: 'linear-gradient(135deg, #2f54eb, #597ef7)', color: '#2f54eb', permission: '', sourceText: '学硕360+MPA1200', sourceType: 'est' },
  { key: 'doctor', title: '博士在校生', value: 140, unit: '人', trend: 0, trendDirection: 'up', gradient: 'linear-gradient(135deg, #52c41a, #73d13d)', color: '#52c41a', permission: '', sourceText: '35人/年×4年', sourceType: 'est' },
  { key: 'staff', title: '专任教师', value: 93, unit: '人', trend: 0, trendDirection: 'up', gradient: 'linear-gradient(135deg, #7b2cbf, #9b59b6)', color: '#7b2cbf', permission: '', sourceText: '学院官网', sourceType: 'official' },
  { key: 'funding', title: '近五年科研经费', value: 6000, unit: '万元', trend: 0, trendDirection: 'up', gradient: 'linear-gradient(135deg, #faad14, #ffc53d)', color: '#faad14', permission: '', sourceText: '学院官网', sourceType: 'official' }
])

kpiData.forEach(kpi => { kpi.permission = authStore.getKpiPermission(kpi.key) })

// 全院在院生构成：官网《学院简介》年招生规模 × 标准学制（估算）
// 数据由 /api/real/pspa-college-overview 回填，此处仅为接口不可用时的兜底默认值
const levelData = [
  { value: 600, name: '本科生', itemStyle: { color: '#13c2c2' } },
  { value: 360, name: '学术型硕士', itemStyle: { color: '#00d4ff' } },
  { value: 140, name: '博士研究生', itemStyle: { color: '#52c41a' } },
  { value: 1200, name: '公共管理硕士（MPA）', itemStyle: { color: '#7b2cbf' } },
  { value: 120, name: '全英文项目留学生', itemStyle: { color: '#faad14' } }
]

// 各培养层次年招生规模（官网原文，人/年）
const enrollPerYearData = [
  { name: '本科生', value: 150 },
  { name: '学术型硕士', value: 120 },
  { name: '博士研究生', value: 35 },
  { name: '公共管理硕士（MPA）', value: 400 },
  { name: '全英文项目留学生', value: 40 }
]

// 柱状图横轴简称：卡片宽度只够放 5 个短标签，用简称避免标签互相压字；
// 完整名称在 tooltip 中仍按原名显示（tooltip 的 {b} 取横轴原始类目名）
const SHORT_LEVEL = {
  本科生: '本科',
  学术型硕士: '学硕',
  博士研究生: '博士',
  '公共管理硕士（MPA）': 'MPA',
  全英文项目留学生: '留学生'
}

// 各系专任教师规模（官网全职教师页面）
const deptData = [
  { name: '公共管理系', value: 39 },
  { name: '政治学系', value: 19 },
  { name: '国际政治系', value: 17 },
  { name: '科社系', value: 13 },
  { name: '公共治理研究院', value: 5 }
]

// 全院在校生总数（用于生源地地图占比与 tooltip）
const collegeStudentTotal = ref(2420)
// 全英文项目留学生在校生（用于国际地图 tooltip 占比）
const intlStudentTotal = ref(120)

// 就业率数据（暂无官方数据源，保留演示数据，接口就绪后可替换）
const employmentData = {
  years: ['2021', '2022', '2023', '2024', '2025'],
  rate: [93, 94, 95, 96, 97],
  state: [45, 46, 47, 48, 49],
  enterprise: [35, 36, 37, 38, 39]
}

// 学业完成率（教学系统 3621 条真实成绩及格率；0 = 未加载用默认值）
const completionRate = ref(0)

// 官网科研产出构成（《学院简介》原文：论文600/CSSCI500/SSCI100/著作100/智库报告300）
const researchOutputData = [
  { name: '发表论文', value: 600 },
  { name: 'CSSCI 来源期刊', value: 500 },
  { name: 'SSCI 论文', value: 100 },
  { name: '出版著作', value: 100 },
  { name: '智库报告', value: 300 }
]

// 教师职称数据
const facultyData = [
  { name: '教授', value: 37, itemStyle: { color: '#7b2cbf' } },
  { name: '副教授', value: 29, itemStyle: { color: '#00d4ff' } },
  { name: '讲师', value: 27, itemStyle: { color: '#52c41a' } }
]

// 科研项目级别数据（官网《学院简介》原文：重大攻关10+国家社科30+国自然10+部委50）
const projectLevelData = [
  { name: '重大攻关', value: 10 },
  { name: '国家社科', value: 30 },
  { name: '国自然', value: 10 },
  { name: '部委项目', value: 50 }
]

// 官网学术成果年度分布（爬虫采集 /xsky/xscg.htm，按发布日期年份聚合）
const achievementYearData = []

// 课程类型数据
const courseData = [
  { name: '专业核心课', value: 46 },
  { name: '公共基础课', value: 34 },
  { name: '社会实践实训', value: 13 },
  { name: '通识选修课', value: 7 }
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

// 生源地基准结构（经验分布，仅用于按全院在校生规模等比放大成“示意估算”）
const MAP_BASE = mapData.map(d => ({ name: d.name, value: d.value }))
const WORLD_BASE = worldMapData.map(d => ({ name: d.name, value: d.value }))

// 小省份列表 - 默认隐藏标签
const smallProvinces = ['天津', '上海', '北京', '宁夏', '海南', '台湾', '香港', '澳门']

// 统一tooltip样式
const tooltipStyle = {
  backgroundColor: 'rgba(10, 25, 50, 0.95)',
  borderColor: 'rgba(0, 212, 255, 0.4)',
  borderWidth: 1,
  textStyle: { color: '#fff', fontSize: 12 }
}

// 初始化饼图 - 全院在院生构成
const initPieChart = () => {
  if (!pieChartRef.value) return
  pieChart = echarts.init(pieChartRef.value)
  pieChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
    legend: {
      orient: 'horizontal',
      bottom: 4,
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 12
    },
    series: [{
      type: 'pie',
      // 卡片高约 260px，底部两行图例约占 36px，饼图收敛尺寸并上移，避免与图例压字
      radius: ['40%', '64%'],
      center: ['50%', '43%'],
      minAngle: 6,
      label: {
        show: true,
        position: 'inside',
        formatter: function (p) {
          return p.percent >= 4 ? p.percent + '%' : ''
        },
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold'
      },
      labelLine: { show: false },
      data: levelData,
      emphasis: {
        itemStyle: { shadowBlur: 25, shadowColor: 'rgba(0, 212, 255, 0.5)' }
      }
    }]
  })
}

// 初始化横向柱状图 - 各系专任教师规模
const initBarChart = () => {
  if (!barChartRef.value) return
  barChart = echarts.init(barChartRef.value)
  barChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '{b}: {c} 人' },
    grid: { left: 108, right: 60, top: 18, bottom: 35 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.65)', fontSize: 12, margin: 10 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: deptData.map(item => item.name).reverse(),
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 20,
      data: deptData.slice().reverse().map(item => ({
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

// 初始化柱状图 - 各培养层次年招生规模（官网原文）
const initLineChart = () => {
  if (!lineChartRef.value) return
  lineChart = echarts.init(lineChartRef.value)
  lineChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '{b}: {c} 人/年' },
    grid: { left: 52, right: 22, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: enrollPerYearData.map(d => d.name),
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: {
        color: 'rgba(255,255,255,0.75)',
        fontSize: 11,
        interval: 0,
        margin: 8,
        // 卡片较窄（5 个类目），用简称避免标签重叠
        formatter: function (v) {
          return SHORT_LEVEL[v] || v
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    series: [{
      type: 'bar',
      barWidth: 24,
      data: enrollPerYearData.map((item, index) => ({
        value: item.value,
        itemStyle: {
          color: ['#13c2c2', '#00d4ff', '#52c41a', '#7b2cbf', '#faad14'][index],
          borderRadius: [6, 6, 0, 0]
        }
      })),
      label: {
        show: true,
        position: 'top',
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold'
      }
    }]
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
    grid: { left: 52, right: 30, top: 18, bottom: 48 },
    xAxis: {
      type: 'category',
      data: employmentData.years,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.75)', fontSize: 12, margin: 8 }
    },
    // 三条曲线都是百分比，统一用一根纵轴，避免双轴造成“数值被拉伸/无法直接比较”的误读
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      interval: 20,
      name: '百分比(%)',
      nameTextStyle: { color: 'rgba(255,255,255,0.5)', fontSize: 11, padding: [0, 0, 4, 0] },
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', formatter: '{value}%', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    series: [
      {
        name: '总就业率', type: 'line', smooth: true,
        data: employmentData.rate,
        lineStyle: { color: '#52c41a', width: 3 },
        symbol: 'circle', symbolSize: 8,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '公职单位', type: 'line', smooth: true,
        data: employmentData.state,
        lineStyle: { color: '#00d4ff', width: 3 },
        symbol: 'circle', symbolSize: 8,
        itemStyle: { color: '#00d4ff' }
      },
      {
        name: '企业', type: 'line', smooth: true,
        data: employmentData.enterprise,
        lineStyle: { color: '#faad14', width: 3 },
        symbol: 'circle', symbolSize: 8,
        itemStyle: { color: '#faad14' }
      }
    ]
  })
}

// 初始化科研产出构成图（官网《学院简介》原文数字）
const initRadarChart = () => {
  if (!radarChartRef.value) return
  radarChart = echarts.init(radarChartRef.value)
  const colors = ['#00d4ff', '#7b2cbf', '#eb2f96', '#faad14', '#52c41a']

  radarChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '{b}: {c}' },
    // 左侧类目名最长“CSSCI 来源期刊”，留足宽度避免被截断/压到绘图区
    grid: { left: 112, right: 48, top: 18, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.65)', fontSize: 12, margin: 10 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: researchOutputData.map(d => d.name).reverse(),
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 18,
      data: researchOutputData.slice().reverse().map((item, index) => ({
        value: item.value,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: 'rgba(255,255,255,0.08)' },
            { offset: 1, color: colors[(researchOutputData.length - 1 - index) % colors.length] }
          ]),
          borderRadius: [0, 6, 6, 0]
        }
      })),
      label: {
        show: true,
        position: 'right',
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold',
        distance: 10
      }
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

// 初始化官网学术成果年度分布图（真实爬取）
const initFundingChart = () => {
  if (!fundingChartRef.value) return
  fundingChart = echarts.init(fundingChartRef.value)
  const colors = ['#7b2cbf', '#00d4ff', '#faad14', '#52c41a', '#eb2f96', '#13c2c2']

  fundingChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { ...tooltipStyle, trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 70, right: 55, top: 18, bottom: 35 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: {
        color: 'rgba(255,255,255,0.65)',
        fontSize: 12,
        margin: 10,
        formatter: function(v) {
          return v + ' 篇'
        }
      },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: achievementYearData.map(item => item.name),
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 18,
      data: achievementYearData.map((item, index) => ({
        value: item.value,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: colors[index % colors.length] + '25' },
            { offset: 1, color: colors[index % colors.length] }
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
  const maxValue = isChinaMap.value
    ? Math.max(...mapData.map(d => d.value), 1)
    : Math.max(...worldMapData.map(d => d.value), 1)

  const worldLabelFormatter = function(params) {
    const hasData = worldMapData.some(item => item.name === params.name)
    return hasData ? params.name : ''
  }

  // 分档阈值随数据最大值动态缩放，避免换数据后图例与实际分布不匹配
  const p1 = Math.round(maxValue * 0.8)
  const p2 = Math.round(maxValue * 0.4)
  const p3 = Math.round(maxValue * 0.2)

  mapChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      ...tooltipStyle,
      trigger: 'item',
      formatter: function(params) {
        if (params.value == null || params.value === '-') return params.name + '：暂无数据'
        const total = isChinaMap.value ? collegeStudentTotal.value : intlStudentTotal.value
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
        { min: p1, label: '>=' + p1, color: '#7b2cbf' },
        { max: p1 - 1, min: p2, label: p2 + '-' + (p1 - 1), color: '#00b8d4' },
        { max: p2 - 1, min: p3, label: p3 + '-' + (p2 - 1), color: '#00698c' },
        { max: p3 - 1, min: 0, label: '<' + p3, color: '#004a66' }
      ] : [
        { min: p1, label: '>=' + p1, color: '#7b2cbf' },
        { max: p1 - 1, min: p2, label: p2 + '-' + (p1 - 1), color: '#00b8d4' },
        { max: p2 - 1, min: p3, label: p3 + '-' + (p2 - 1), color: '#00698c' },
        { max: p3 - 1, min: 0, label: '<' + p3, color: '#004a66' }
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
      data: [{ value: completionRate.value || 94 }]
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

// ============ 数据接入 ============
// 大屏口径 = 全院（本科 + 学硕 + 博士 + MPA + 留学生），不再只统计研究生子系统。
//   A 官网原文：学院简介指标 / 全职教师名录 / 学术成果页 / 论文题录 / 通知公告
//   B 教学系统（同组同学子系统）课程与成绩
//   估算项：在校生 = 官网年招生规模 × 标准学制，页面上明确标注“估算”
// 任一接口失败时保留页面兜底值，不影响渲染
const fetchRealKpi = async () => {
  const get = (url) => fetch(url).then(r => r.ok ? r.json() : null).catch(() => null)

  const [college, paperKeywords, courseDist,
    pspaFaculty, gradeStat, pspaProfile, pspaAchievementStats] =
    await Promise.all([
      get('/api-research/api/real/pspa-college-overview'),
      get('/api-research/api/real/paper-keywords?limit=40'),
      get('/api-research/api/real/course-type-dist'),
      get('/api-research/api/real/pspa-faculty-title-dist'),
      get('/api-research/api/real/grade-stat'),
      get('/api-research/api/real/pspa-profile'),
      get('/api-research/api/real/pspa-achievement-stats'),
    ])

  const setKpi = (key, value) => {
    if (value == null || value === '' || Number.isNaN(Number(value))) return
    const row = kpiData.find(k => k.key === key)
    if (row) row.value = Number(value)
  }

  const profile = pspaProfile?.data || {}

  // ---- KPI：全院口径（本科 + 硕士 + 博士 + MPA + 留学生）----
  const sumEnroll = (keys) => (college?.enrollment || [])
    .filter(e => keys.includes(e.key))
    .reduce((s, e) => s + (e.in_school || 0), 0)

  if (college?.totals) {
    setKpi('students', college.totals.all)
    setKpi('undergrad', college.totals.undergrad)
    setKpi('master', sumEnroll(['master', 'mpa']))
    setKpi('doctor', sumEnroll(['doctor']))
    collegeStudentTotal.value = college.totals.all || collegeStudentTotal.value
    setKpi('staff', college.faculty?.total ?? profile.teacher_total)
    setKpi('funding', college.research?.fund_total ?? profile.fund_total)
  } else {
    setKpi('staff', profile.teacher_total)
    setKpi('funding', profile.fund_total)
  }

  // ---- 各培养层次年招生规模 / 在院生构成（官网原文 + 学制换算）----
  if (college?.enrollment?.length) {
    const palette = ['#13c2c2', '#00d4ff', '#52c41a', '#7b2cbf', '#faad14']
    levelData.length = 0
    enrollPerYearData.length = 0
    college.enrollment.forEach((e, i) => {
      levelData.push({
        value: e.in_school || 0,
        name: e.name,
        itemStyle: { color: palette[i % palette.length] }
      })
      enrollPerYearData.push({ name: e.name, value: e.per_year || 0 })
    })
  }

  // ---- 各系专任教师规模（官网全职教师名录按系聚合）----
  if (college?.dept_dist?.length) {
    deptData.length = 0
    college.dept_dist.forEach(d => deptData.push({ name: d.name, value: d.value }))
  }

  // ---- 官网科研产出构成（学院简介近五年统计）----
  if (college?.research) {
    const r = college.research
    researchOutputData.length = 0
    const push = (name, value) => {
      if (value != null) researchOutputData.push({ name, value })
    }
    push('发表论文', r.paper_total)
    push('CSSCI 来源期刊', r.paper_cssci)
    push('SSCI 论文', r.paper_ssci)
    push('出版著作', r.book_total)
    push('智库报告', r.thinktank_report)
  }

  // ---- 科研项目级别分布（官网学院简介原文数字）----
  if (profile.project_major != null) {
    projectLevelData.length = 0
    projectLevelData.push({ name: '重大攻关', value: profile.project_major })
    projectLevelData.push({ name: '国家社科', value: profile.project_nssf || 0 })
    projectLevelData.push({ name: '国自然', value: profile.project_nsfc || 0 })
    projectLevelData.push({ name: '部委项目', value: profile.project_ministry || 0 })
  }

  // ---- 官网学术成果年度分布（爬虫采集，按发布年份聚合）----
  if (pspaAchievementStats?.by_year?.length) {
    achievementYearData.length = 0
    pspaAchievementStats.by_year.forEach(y => achievementYearData.push({ name: y.name, value: y.value }))
  }

  // ---- 学术关键词词云（官网 375 篇论文关键词真实聚合）----
  if (paperKeywords?.data?.length) {
    wordCloudData.length = 0
    paperKeywords.data.forEach(d => wordCloudData.push({ name: d.name, value: d.value }))
  }

  // ---- 生源地地图：官网不公布分省生源，按全院在校生规模做示意估算 ----
  // 省份结构为学院生源的经验分布，总量与全院在校生一致，页面标注“示意估算”。
  const allStudents = college?.totals?.all || collegeStudentTotal.value
  collegeStudentTotal.value = allStudents
  const mapBaseTotal = MAP_BASE.reduce((s, d) => s + d.value, 0) || 1
  const ratio = allStudents / mapBaseTotal
  MAP_BASE.forEach((base, i) => {
    if (mapData[i]) mapData[i].value = Math.max(1, Math.round(base.value * ratio))
  })

  // 国际地图按全英文项目留学生在校生规模等比放大
  const intl = college?.enrollment?.find(e => e.key === 'intl')
  const intlTotal = intl?.in_school || intlStudentTotal.value
  intlStudentTotal.value = intlTotal
  const worldBaseTotal = WORLD_BASE.reduce((s, d) => s + d.value, 0) || 1
  const worldRatio = intlTotal / worldBaseTotal
  WORLD_BASE.forEach((base, i) => {
    if (worldMapData[i]) worldMapData[i].value = Math.max(1, Math.round(base.value * worldRatio))
  })

  // ---- 课程类型分布（教学系统课程库）----
  if (courseDist?.data?.length) {
    courseData.length = 0
    courseDist.data.forEach(d => courseData.push({ name: d.name, value: d.value }))
  }

  // ---- 教师职称分布（学院官网全职教师页面，93 人）----
  if (pspaFaculty?.data?.length) {
    const colorMap = {
      教授: '#7b2cbf', 副教授: '#00d4ff', 副研究员: '#13c2c2',
      讲师: '#52c41a', 助理研究员: '#95de64', 博士后: '#faad14', 未标注: '#8c8c8c'
    }
    facultyData.length = 0
    pspaFaculty.data.forEach(d => {
      facultyData.push({ name: d.name, value: d.value, itemStyle: { color: colorMap[d.name] || '#13c2c2' } })
    })
  }

  // ---- 学业完成率（教学系统成绩库及格率）----
  if (gradeStat?.pass_rate != null) {
    completionRate.value = Math.round(gradeStat.pass_rate)
  }

  // 说明：本函数在 onMounted 中先于 initCharts() 完成（已 await），
  // 上述数组就地更新后，图表首次渲染即为当前数据，无需二次重绘。
}

// 生命周期
onMounted(async () => {
  await fetchRealKpi()

  const num = (key) => kpiData.find(k => k.key === key)?.value || 0
  dashboardStore.updateData({
    students: num('students'),
    undergrad: num('undergrad'),
    master: num('master'),
    doctor: num('doctor'),
    staff: num('staff'),
    funding: num('funding'),
    maleRatio: '--',
    femaleRatio: '--'
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
  /* 父容器（Layout.main-content）已为固定底部导航预留 90px，这里只填满可见区域 */
  min-height: 100%;
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
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
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

/* 数据来源标注：默认橙色=子系统/演示数据，official 绿色=学院官网真实数据 */
.demo-tag {
  display: inline-block;
  margin-left: 6px;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 400;
  line-height: 1.4;
  color: #faad14;
  border: 1px solid rgba(250, 173, 20, 0.45);
  border-radius: 8px;
  background: rgba(250, 173, 20, 0.08);
  vertical-align: middle;
  letter-spacing: 0;
}

.demo-tag.official {
  color: #52c41a;
  border-color: rgba(82, 196, 26, 0.45);
  background: rgba(82, 196, 26, 0.1);
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
  .dashboard { min-height: 100%; }
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
