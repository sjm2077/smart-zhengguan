<template>
  <div class="home-page">
    <GlobalQueryBar />

    <el-row :gutter="16" class="home-row">
      <el-col :span="8" class="home-col">
        <div class="hero-card">
          <div class="hero-label">{{ headline.title }}</div>
          <div class="hero-number">{{ formatNumber(headline.totalStudents) }}<span class="hero-unit">人</span></div>
          <div class="hero-divider"></div>
          <div class="hero-summary">
            <div class="hero-item">
              <span class="hero-dot master"></span>
              <span class="hero-text">学院硕士研究生 <b>{{ formatNumber(headline.masterCount) }}</b> 人</span>
            </div>
            <div class="hero-item">
              <span class="hero-dot doctor"></span>
              <span class="hero-text">学院博士研究生 <b>{{ formatNumber(headline.doctorCount) }}</b> 人</span>
            </div>
            <div class="hero-item">
              <span class="hero-dot international"></span>
              <span class="hero-text">学院国际学生 <b>{{ formatNumber(headline.internationalCount) }}</b> 人</span>
            </div>
            <div class="hero-item">
              <span class="hero-dot graduate"></span>
              <span class="hero-text">学院本年毕业 <b>{{ formatNumber(headline.annualGraduates) }}</b> 人</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="16" class="home-col">
        <el-row :gutter="14" class="stat-grid">
          <el-col :span="8" v-for="card in statCards" :key="card.title">
            <DashboardCard
              :title="card.title"
              :number="formatCardNumber(card.number)"
              :icon="card.icon"
              :iconBg="card.iconBg"
              :changeLabel="card.changeLabel"
            />
          </el-col>
        </el-row>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="home-row">
      <el-col :span="16" class="home-col">
        <ChartCard
          title="学院近五年人数趋势"
          :chartOptions="trendChart"
          chartHeight="380px"
        />
      </el-col>

      <el-col :span="8" class="home-col">
        <el-row :gutter="0" class="side-charts">
          <el-col :span="24" class="side-chart-item">
            <ChartCard
              title="性别比例"
              :chartOptions="genderChart"
              chartHeight="180px"
            />
          </el-col>
          <el-col :span="24" class="side-chart-item side-chart-spacer">
            <ChartCard
              title="年级分布"
              :chartOptions="gradeChart"
              chartHeight="180px"
            />
          </el-col>
        </el-row>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="home-row bottom-row">
      <el-col :span="7" class="home-col">
        <div class="section-card notice-card">
          <div class="card-header">
            <span class="card-title">通知公告</span>
            <a class="more-link" href="https://www.grad.sdu.edu.cn/" target="_blank">更多 ></a>
          </div>
          <div class="notice-scroll-window">
            <div class="notice-scroll-track">
              <div
                v-for="(notice, index) in scrollingNotices"
                :key="`${notice.title}-${index}`"
                class="notice-item"
                :class="{ 'has-link': notice.url }"
                @click="handleNoticeClick(notice)"
              >
                <span class="notice-text">{{ notice.title }}</span>
                <span class="notice-date">{{ notice.date }}</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="7" class="home-col">
        <div class="section-card todo-card">
          <div class="card-header">
            <span class="card-title">待办事项</span>
            <span class="card-badge">{{ totalTodos }}</span>
          </div>
          <div class="todo-list">
            <div
              v-for="todo in todos"
              :key="todo.label"
              class="todo-item"
              @click="handleTodoClick(todo)"
            >
              <div class="todo-left">
                <span class="todo-dot"></span>
                <span class="todo-label">{{ todo.label }}</span>
              </div>
              <span class="todo-count">{{ todo.count }}</span>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :span="10" class="home-col">
        <div class="region-chart-shell">
          <ChartCard
            title="学院生源地分布"
            :chartOptions="regionChart"
            :key="'map-' + mapLoaded"
            chartHeight="320px"
          />
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import DashboardCard from '../components/DashboardCard.vue'
import ChartCard from '../components/ChartCard.vue'
import GlobalQueryBar from '../components/GlobalQueryBar.vue'
import { getHomeDashboardData } from '../services/mockDataService'

const LOCAL_CHINA_MAP_URL = '/maps-china-100000.json'
const REMOTE_CHINA_MAP_URL = 'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'
const EMPTY_HOME_DATA = {
  updatedAt: '',
  headline: {
    title: '学院研究生数据概览',
    subtitle: '',
    totalStudents: 0,
    masterCount: 0,
    doctorCount: 0,
    internationalCount: 0,
    annualGraduates: 0,
  },
  statCards: [],
  charts: {
    trend: [],
    gender: [],
    grades: [],
    sourceRegions: [],
  },
  notices: [],
  todos: [],
}

const REGION_BAR_COLORS = ['#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5', '#2196F3', '#1976D2', '#0D47A1']
const NON_MAP_REGION_NAMES = new Set(['其他', '境外', '海外', '待更新', '未知'])

export default {
  components: { DashboardCard, ChartCard, GlobalQueryBar },
  data() {
    return {
      dashboardData: EMPTY_HOME_DATA,
      mapLoaded: false,
      regionChart: this.createRegionBarChart([]),
    }
  },
  computed: {
    headline() {
      return this.dashboardData.headline || EMPTY_HOME_DATA.headline
    },
    statCards() {
      return this.dashboardData.statCards || []
    },
    notices() {
      return this.dashboardData.notices || []
    },
    todos() {
      return this.dashboardData.todos || []
    },
    trendChart() {
      const trend = this.dashboardData.charts?.trend || []
      return {
        tooltip: { trigger: 'axis' },
        legend: {
          top: 0,
          textStyle: { color: '#666', fontSize: 12 },
          itemWidth: 16,
          itemHeight: 2,
        },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
        xAxis: {
          type: 'category',
          data: trend.map((item) => item.year),
          axisLabel: { color: '#86909C', fontSize: 12 },
          axisLine: { lineStyle: { color: '#F0F0F0' } },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          axisLabel: { color: '#86909C', fontSize: 12 },
          splitLine: { lineStyle: { color: '#F0F0F0', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        series: [
          {
            name: '硕士研究生',
            type: 'line',
            data: trend.map((item) => item.master),
            areaStyle: { color: 'rgba(22,93,255,0.12)' },
            lineStyle: { color: '#165DFF', width: 2 },
            itemStyle: { color: '#165DFF' },
            symbol: 'circle',
            symbolSize: 8,
            smooth: true,
          },
          {
            name: '博士研究生',
            type: 'line',
            data: trend.map((item) => item.doctor),
            areaStyle: { color: 'rgba(15,198,194,0.12)' },
            lineStyle: { color: '#0FC6C2', width: 2 },
            itemStyle: { color: '#0FC6C2' },
            symbol: 'circle',
            symbolSize: 8,
            smooth: true,
          },
        ],
      }
    },
    genderChart() {
      const genderData = this.dashboardData.charts?.gender || []
      const total = genderData.reduce((sum, item) => sum + Number(item.value || 0), 0)
      return {
        tooltip: { trigger: 'item', formatter: '{b}：{c}人 ({d}%)' },
        legend: {
          bottom: 0,
          left: 'center',
          itemWidth: 10,
          itemHeight: 10,
          textStyle: { color: '#666', fontSize: 12 },
        },
        series: [{
          type: 'pie',
          radius: ['55%', '72%'],
          center: ['50%', '42%'],
          itemStyle: { borderColor: '#fff', borderWidth: 3, borderRadius: 0 },
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 13, fontWeight: 'bold' } },
          data: genderData.map((item, index) => ({
            ...item,
            itemStyle: { color: index === 0 ? '#165DFF' : '#FF7D00' },
          })),
        }],
        graphic: [
          {
            type: 'text',
            left: 'center',
            top: '36%',
            style: {
              text: this.formatNumber(total),
              fill: '#1F2937',
              fontSize: 22,
              fontWeight: 600,
              textAlign: 'center',
            },
          },
          {
            type: 'text',
            left: 'center',
            top: '50%',
            style: {
              text: '学院总量',
              fill: '#86909C',
              fontSize: 11,
              textAlign: 'center',
            },
          },
        ],
      }
    },
    gradeChart() {
      const gradeData = this.dashboardData.charts?.grades || []
      const maxValue = Math.max(...gradeData.map((item) => item.value), 0)
      const interval = maxValue > 0 ? Math.ceil(maxValue / 4 / 50) * 50 || 50 : 50
      const yAxisMax = maxValue > 0 ? Math.ceil(maxValue / interval) * interval : interval

      return {
        tooltip: { trigger: 'axis', formatter: '{b}：{c}人' },
        grid: { left: '3%', right: '5%', bottom: '3%', top: '10px', containLabel: true },
        xAxis: {
          type: 'category',
          data: gradeData.map((item) => item.name),
          axisLabel: { color: '#86909C', fontSize: 10 },
          axisLine: { lineStyle: { color: '#F0F0F0' } },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          max: yAxisMax,
          interval,
          axisLabel: { color: '#86909C', fontSize: 10 },
          splitLine: { lineStyle: { color: '#F0F0F0', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        series: [{
          type: 'bar',
          barWidth: '48%',
          label: { show: true, position: 'top', color: '#165DFF', fontSize: 11 },
          data: gradeData.map((item) => ({
            value: item.value,
            itemStyle: { color: '#165DFF', borderRadius: [0, 0, 0, 0] },
          })),
        }],
      }
    },
    scrollingNotices() {
      return this.notices.length > 1 ? [...this.notices, ...this.notices] : this.notices
    },
    totalTodos() {
      return this.todos.reduce((sum, item) => sum + item.count, 0)
    },
  },
  async mounted() {
    await this.loadDashboardData()
    await this.loadChinaMap()
  },
  methods: {
    formatNumber(value) {
      return Number(value || 0).toLocaleString('zh-CN')
    },
    formatCardNumber(value) {
      return typeof value === 'number' ? this.formatNumber(value) : value
    },
    handleTodoClick(todo) {
      if (this.$message) this.$message.info(`跳转至：${todo.label}`)
    },
    handleNoticeClick(notice) {
      if (notice.url) {
        window.open(notice.url, '_blank')
      } else if (this.$message) {
        this.$message.info(`查看通知：${notice.title}`)
      }
    },
    async loadDashboardData() {
      const data = await getHomeDashboardData()
      this.dashboardData = data
      this.regionChart = this.createRegionBarChart(data.charts?.sourceRegions || [])
    },
    createRegionBarChart(regionData) {
      const chartData = [...regionData]
        .sort((left, right) => left.value - right.value)
        .slice(-7)

      return {
        tooltip: { trigger: 'axis', formatter: '{b}：{c}人' },
        grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
        xAxis: {
          type: 'value',
          axisLabel: { color: '#86909C', fontSize: 11 },
          splitLine: { lineStyle: { color: '#F0F0F0', type: 'dashed' } },
        },
        yAxis: {
          type: 'category',
          data: chartData.map((item) => item.name),
          axisLabel: { color: '#333', fontSize: 11 },
          axisLine: { lineStyle: { color: '#F0F0F0' } },
        },
        series: [{
          type: 'bar',
          barWidth: '55%',
          label: { show: true, position: 'right', color: '#333', formatter: '{c}人', fontSize: 11 },
          data: chartData.map((item, index) => ({
            value: item.value,
            itemStyle: { color: REGION_BAR_COLORS[index] || '#165DFF' },
          })),
        }],
      }
    },
    createRegionMapChart(regionData) {
      const mapData = this.normalizeMapRegionData(regionData)
      const maxValue = Math.max(...mapData.map((item) => item.value), 0)
      return {
        tooltip: { trigger: 'item', formatter: '{b}<br/>学院研究生人数：{c}人' },
        visualMap: {
          min: 0,
          max: maxValue || 700,
          left: 10,
          bottom: 10,
          text: ['高', '低'],
          textStyle: { color: '#86909C', fontSize: 11 },
          inRange: { color: ['#E8F0FE', '#BBDEFB', '#64B5F6', '#2196F3', '#0D47A1'] },
          calculable: true,
        },
        series: [{
          type: 'map',
          map: 'china',
          roam: false,
          label: { show: false },
          emphasis: {
            label: { show: true, color: '#333' },
            itemStyle: { areaColor: '#FFE082' },
          },
          data: mapData,
        }],
      }
    },
    normalizeMapRegionData(regionData) {
      return (regionData || [])
        .filter((item) => item && item.name && !NON_MAP_REGION_NAMES.has(item.name))
        .map((item) => ({
          name: item.name,
          value: Number(item.value || 0),
        }))
    },
    async fetchChinaMapJson() {
      const sources = [LOCAL_CHINA_MAP_URL, REMOTE_CHINA_MAP_URL]

      for (const url of sources) {
        try {
          const res = await fetch(url)
          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`)
          }
          return await res.json()
        } catch (error) {
          console.warn(`中国地图资源加载失败: ${url}`, error)
        }
      }

      throw new Error('No available China map source')
    },
    async loadChinaMap() {
      if (this.mapLoaded) return

      const regionData = this.normalizeMapRegionData(this.dashboardData.charts?.sourceRegions || [])
      if (!regionData.length) return

      try {
        const geoJson = await this.fetchChinaMapJson()
        echarts.registerMap('china', geoJson)
        this.mapLoaded = true
        this.regionChart = this.createRegionMapChart(regionData)
      } catch (error) {
        console.warn('中国地图加载失败，使用条形图', error)
      }
    },
  },
}
</script>

<style scoped>
.home-page { color: #333; }

.home-row {
  margin-bottom: 16px;
  display: flex;
  align-items: stretch;
  flex-wrap: wrap;
}

.home-col { margin-bottom: 0; }

.home-row > .home-col {
  display: flex;
  align-self: stretch;
  min-height: 0;
}

.home-row > .home-col > * {
  width: 100%;
}

.hero-card {
  background: linear-gradient(135deg, #165DFF 0%, #0A2463 100%);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  padding: 28px 24px;
  height: 100%;
  color: #fff;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.hero-label { font-size: 14px; opacity: 0.85; margin-bottom: 6px; }
.hero-number { font-size: 42px; font-weight: 700; line-height: 1.1; margin-bottom: 4px; }
.hero-unit { font-size: 18px; font-weight: 400; opacity: 0.8; margin-left: 4px; }
.hero-divider { width: 48px; height: 2px; background: rgba(255, 255, 255, 0.3); margin: 14px 0; }
.hero-summary { display: flex; flex-direction: column; gap: 8px; }
.hero-item { display: flex; align-items: center; gap: 8px; }
.hero-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.hero-dot.master { background: #0FC6C2; }
.hero-dot.doctor { background: #722ED1; }
.hero-dot.international { background: #FF7D00; }
.hero-dot.graduate { background: rgba(255, 255, 255, 0.6); }
.hero-text { font-size: 13px; opacity: 0.9; }
.hero-text b { font-weight: 600; }

.stat-grid { display: flex; flex-wrap: wrap; }
.stat-grid .el-col { margin-bottom: 14px; }
.stat-grid .el-col:nth-child(4),
.stat-grid .el-col:nth-child(5),
.stat-grid .el-col:nth-child(6) { margin-bottom: 0; }

.side-charts { height: 100%; display: flex; flex-direction: column; }
.side-chart-item { flex: 1; }
.side-chart-spacer { margin-top: 16px; }

.section-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  height: 100%;
  box-sizing: border-box;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid #F0F0F0;
}

.card-title { font-size: 16px; font-weight: 400; color: #333; }
.more-link { font-size: 13px; color: #165DFF; text-decoration: none; cursor: pointer; }

.card-badge {
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: #165DFF;
  border-radius: 10px;
  padding: 2px 10px;
  min-width: 24px;
  text-align: center;
}

.notice-card { display: flex; flex-direction: column; overflow: hidden; }

.notice-scroll-window {
  flex: 1;
  overflow: hidden;
  position: relative;
  min-height: 0;
}

.notice-scroll-track {
  display: flex;
  flex-direction: column;
  flex: 0 0 auto;
  animation: notice-scroll 20s linear infinite;
}

.notice-card:hover .notice-scroll-track {
  animation-play-state: paused;
}

@keyframes notice-scroll {
  0% { transform: translateY(0); }
  100% { transform: translateY(-50%); }
}

.notice-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 0 0 52px;
  min-height: 52px;
  cursor: default;
  transition: background-color 0.2s;
  padding: 0 4px;
  border-bottom: 1px dashed #F0F0F0;
  box-sizing: border-box;
}

.notice-item.has-link {
  cursor: pointer;
}

.notice-item.has-link:hover {
  background-color: #f0f7ff;
}

.notice-item:last-child { border-bottom: none; }
.notice-text { font-size: 13px; color: #333; flex: 1; line-height: 1.6; }
.notice-date { font-size: 12px; color: #86909C; white-space: nowrap; margin-left: 12px; }

.bottom-row {
  flex-wrap: nowrap !important;
  align-items: stretch !important;
  height: 390px;
}

.bottom-row > .home-col {
  display: flex;
  align-self: stretch;
  height: 100%;
}

.bottom-row > .home-col > * {
  flex: 1;
  min-height: 0;
  height: auto;
  overflow: hidden;
}

.region-chart-shell {
  width: 100%;
  height: 100%;
  display: flex;
}

.region-chart-shell :deep(.chart-card) {
  flex: 1;
  box-shadow: none;
  height: 100%;
}

.todo-card { display: flex; flex-direction: column; }
.todo-list { flex: 1; display: flex; flex-direction: column; min-height: 0; }

.todo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
  padding: 0 4px;
  border-bottom: 1px dashed #F0F0F0;
  cursor: pointer;
  transition: background 0.2s;
}

.todo-item:hover { background: #F7F8FA; margin: 0 -8px; padding: 0 12px; border-radius: 4px; }
.todo-item:last-child { border-bottom: none; }
.todo-left { display: flex; align-items: center; gap: 8px; }
.todo-dot { width: 6px; height: 6px; border-radius: 50%; background: #165DFF; flex-shrink: 0; }
.todo-label { font-size: 14px; color: #333; }

.todo-count {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  background: #FF7D00;
  border-radius: 12px;
  padding: 3px 12px;
  min-width: 28px;
  text-align: center;
}

@media (max-width: 1199px) and (min-width: 768px) {
  .home-col {
    flex: 0 0 100% !important;
    max-width: 100% !important;
    margin-bottom: 16px;
  }

  .hero-number { font-size: 32px; }
  .stat-grid .el-col { flex: 0 0 33.33%; max-width: 33.33%; }
}

@media (max-width: 767px) {
  .home-col {
    flex: 0 0 100% !important;
    max-width: 100% !important;
    margin-bottom: 16px;
  }

  .hero-number { font-size: 28px; }
  .stat-grid .el-col { flex: 0 0 50%; max-width: 50%; }
}
</style>
