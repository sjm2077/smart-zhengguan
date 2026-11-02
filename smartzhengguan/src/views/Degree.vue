<template>
  <div class="degree-page">
    <div class="page-header">
      <span class="page-title">学院学位管理数据概览</span>
      <div class="header-right">
        <span class="update-time">数据更新时间：{{ pageData.updatedAt || '--' }}</span>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="card in statCards" :key="card.title">
        <DashboardCard
          :title="card.title"
          :number="card.number"
          :change="card.change"
          :icon="card.icon"
          :iconBg="card.iconBg"
          :changeLabel="card.changeLabel"
        />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="16"><ChartCard title="学院近五年学位申请人数趋势" :chartOptions="applicationTrendChart" chartHeight="340px" /></el-col>
      <el-col :span="8"><ChartCard title="学院学位申请类型分布" :chartOptions="applicationTypeChart" chartHeight="340px" /></el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="8"><ChartCard title="学院论文评阅结果分布" :chartOptions="paperReviewChart" chartHeight="340px" /></el-col>
      <el-col :span="8"><ChartCard title="学院答辩结果分布" :chartOptions="defenseResultChart" chartHeight="340px" /></el-col>
      <el-col :span="8">
        <div class="info-card">
          <div class="info-card-header"><span class="info-card-title">学位通知公告</span><a class="more-link" href="#">更多 &gt;</a></div>
          <div class="notice-list">
            <div v-for="n in degreeNotices" :key="n.title" class="notice-item"><span class="notice-text">{{ n.title }}</span><span class="notice-date">{{ n.date }}</span></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="16"><ChartCard title="学院学位授予专业分布" :chartOptions="disciplineChart" chartHeight="340px" /></el-col>
      <el-col :span="8"><ChartCard title="学院近五年学位授予数量趋势" :chartOptions="awardTrendChart" chartHeight="340px" /></el-col>
    </el-row>
  </div>
</template>

<script>
import DashboardCard from '../components/DashboardCard.vue'
import ChartCard from '../components/ChartCard.vue'
import { getDegreeData } from '../services/mockDataService'

const CARD_META = [
  { icon: 'clipboard', iconBg: '#EEF4FF', unit: '人' },
  { icon: 'clock', iconBg: '#EEF4FF', unit: '人' },
  { icon: 'file', iconBg: '#EEF4FF', unit: '篇' },
  { icon: 'graduation', iconBg: '#EEF4FF', unit: '人' },
]
const EMPTY_PAGE_DATA = {
  updatedAt: '',
  statCards: [],
  charts: {
    applicationTypes: [],
    applicationTrend: [],
    paperReview: [],
    defenseResults: [],
    awardTrend: [],
    disciplineDistribution: [],
  },
  notices: [],
  todos: [],
}

export default {
  components: { DashboardCard, ChartCard },
  data() {
    return {
      pageData: EMPTY_PAGE_DATA,
    }
  },
  computed: {
    statCards() {
      return (this.pageData.statCards || []).map((card, index) => ({
        ...card,
        number: this.formatCardNumber(card.number, CARD_META[index]?.unit),
        change: null,
        changeLabel: card.changeLabel,
        icon: CARD_META[index]?.icon || 'chart',
        iconBg: CARD_META[index]?.iconBg || '#EEF4FF',
      }))
    },
    degreeNotices() {
      return this.pageData.notices || []
    },
    applicationTypeChart() {
      const data = this.pageData.charts?.applicationTypes || []
      const academic = data[0]?.value || 0
      const professional = data[1]?.value || 0
      const total = academic + professional
      const academicPercent = total ? ((academic / total) * 100).toFixed(0) : '0'
      const professionalPercent = total ? ((professional / total) * 100).toFixed(0) : '0'
      return {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const item = params[0]
            const percent = item.seriesName === '学术学位' ? academicPercent : professionalPercent
            return `${item.seriesName}: ${Math.abs(item.value)}人 (${percent}%)`
          },
        },
        legend: { top: 0, textStyle: { color: '#333', fontSize: 12 } },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
        xAxis: { type: 'value', axisLabel: { color: '#666' }, splitLine: { lineStyle: { color: '#E5E7EB' } } },
        yAxis: { type: 'category', data: ['学位类型'], axisLabel: { color: '#666' }, axisLine: { lineStyle: { color: '#E5E7EB' } } },
        series: [
          {
            name: data[0]?.name || '学术学位',
            type: 'bar',
            data: [-academic],
            barWidth: '30%',
            label: { show: true, position: 'left', color: '#333', fontSize: 14, formatter: `${academic}人` },
            itemStyle: { color: '#165DFF', borderRadius: [0, 0, 0, 0] },
          },
          {
            name: data[1]?.name || '专业学位',
            type: 'bar',
            data: [professional],
            barWidth: '30%',
            label: { show: true, position: 'right', color: '#333', fontSize: 14, formatter: `${professional}人` },
            itemStyle: { color: '#722ED1', borderRadius: [0, 0, 0, 0] },
          },
        ],
      }
    },
    applicationTrendChart() {
      const data = this.pageData.charts?.applicationTrend || []
      return {
        tooltip: { trigger: 'axis' },
        legend: { top: 0, textStyle: { color: '#333', fontSize: 12 } },
        grid: { left: '3%', right: '8%', bottom: '3%', top: '40px', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.map((item) => item.year),
          axisLabel: { color: '#666' },
          axisLine: { lineStyle: { color: '#E5E7EB' } },
        },
        yAxis: [
          {
            type: 'value',
            name: '申请人数',
            axisLabel: { color: '#666' },
            splitLine: { lineStyle: { color: '#E5E7EB' } },
          },
          {
            type: 'value',
            name: '增长率',
            axisLabel: { color: '#666', formatter: '{value}%' },
            splitLine: { show: false },
          },
        ],
        series: [
          {
            name: '申请人数',
            type: 'line',
            data: data.map((item) => item.count),
            lineStyle: { color: '#165DFF' },
            itemStyle: { color: '#165DFF', borderColor: '#165DFF', borderWidth: 2 },
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
          },
          {
            name: '同比增长率',
            type: 'line',
            yAxisIndex: 1,
            data: data.map((item) => item.growth),
            lineStyle: { color: '#13C2C2', type: 'dashed' },
            itemStyle: { color: '#13C2C2' },
            smooth: true,
            symbol: 'diamond',
            symbolSize: 8,
            label: { show: true, color: '#13C2C2', fontSize: 11, formatter: '{c}%' },
          },
        ],
      }
    },
    paperReviewChart() {
      const data = this.pageData.charts?.paperReview || []
      const colors = ['#165DFF', '#13C2C2', '#FF4D4F']
      return {
        tooltip: { trigger: 'item', formatter: '{b}：{c}%（{d}%）' },
        legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#333', fontSize: 11 }, itemWidth: 8, itemHeight: 8 },
        series: [{
          type: 'pie',
          radius: ['0%', '68%'],
          center: ['38%', '50%'],
          itemStyle: { borderRadius: 0, borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
          data: data.map((item, index) => ({
            ...item,
            itemStyle: { color: colors[index] || '#165DFF' },
          })),
        }],
      }
    },
    defenseResultChart() {
      const data = this.pageData.charts?.defenseResults || []
      const colors = ['#165DFF', '#13C2C2', '#FF4D4F']
      return {
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#333', fontSize: 12 } },
        series: [{
          type: 'pie',
          radius: ['50%', '70%'],
          center: ['40%', '50%'],
          itemStyle: { borderRadius: 0, borderColor: '#fff', borderWidth: 3 },
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
          data: data.map((item, index) => ({
            value: item.value,
            name: `${item.name} ${item.percent}%`,
            itemStyle: { color: colors[index] || '#165DFF' },
          })),
        }],
      }
    },
    awardTrendChart() {
      const data = this.pageData.charts?.awardTrend || []
      return {
        tooltip: { trigger: 'axis', formatter: '{b}年<br/>授予人数: {c}人' },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '10px', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.map((item) => item.year),
          axisLabel: { color: '#666' },
          axisLine: { lineStyle: { color: '#E5E7EB' } },
        },
        yAxis: {
          type: 'value',
          axisLabel: { color: '#666' },
          splitLine: { lineStyle: { color: '#E5E7EB' } },
        },
        series: [{
          type: 'bar',
          barWidth: '40%',
          label: { show: true, position: 'top', color: '#333', fontSize: 12 },
          data: data.map((item) => ({
            value: item.value,
            itemStyle: { color: '#165DFF' },
          })),
        }],
      }
    },
    disciplineChart() {
      const data = this.pageData.charts?.disciplineDistribution || []
      const colors = ['#165DFF', '#3D8BFF', '#69B1FF', '#94CBFF', '#BBDEFB', '#C5E1FF']
      return {
        tooltip: { trigger: 'axis' },
        legend: { top: 0, textStyle: { color: '#333', fontSize: 12 } },
        grid: { left: '3%', right: '8%', bottom: '3%', top: '40px', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.map((item) => item.name),
          axisLabel: { color: '#666', rotate: 15 },
          axisLine: { lineStyle: { color: '#E5E7EB' } },
        },
        yAxis: [
          {
            type: 'value',
            name: '授予人数',
            axisLabel: { color: '#666' },
            splitLine: { lineStyle: { color: '#E5E7EB' } },
          },
          {
            type: 'value',
            name: '累计占比',
            max: 100,
            axisLabel: { color: '#666', formatter: '{value}%' },
            splitLine: { show: false },
          },
        ],
        series: [
          {
            name: '授予人数',
            type: 'bar',
            barWidth: '50%',
            data: data.map((item, index) => ({
              value: item.count,
              itemStyle: { color: colors[index] || '#165DFF' },
            })),
            label: { show: true, position: 'top', color: '#333', fontSize: 11 },
          },
          {
            name: '累计占比',
            type: 'line',
            yAxisIndex: 1,
            data: data.map((item) => item.cumulative),
            lineStyle: { color: '#FF4D4F' },
            itemStyle: { color: '#FF4D4F' },
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            label: { show: true, color: '#FF4D4F', fontSize: 11, formatter: '{c}%' },
          },
        ],
      }
    },
  },
  async mounted() {
    this.pageData = await getDegreeData()
  },
  methods: {
    formatCardNumber(value, unit = '') {
      if (typeof value !== 'number') return value
      return `${value.toLocaleString('zh-CN')}${unit}`
    },
  },
}
</script>

<style scoped>
.degree-page { color: #333; }
.page-header { display: none; }
.page-title { font-size: 20px; font-weight: bold; color: #333; }
.header-right { display: flex; align-items: center; gap: 16px; }
.update-time { font-size: 14px; color: #666; }
.stat-row, .chart-row, .bottom-row { margin-bottom: 16px; }
.info-card { background: #fff; border-radius: 8px; padding: 16px; height: 100%; min-height: 260px; }
.info-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #f0f0f0; }
.info-card-title { font-size: 16px; font-weight: bold; color: #333; }
.more-link { font-size: 13px; color: #165DFF; text-decoration: none; cursor: pointer; }
.notice-item { display: flex; justify-content: space-between; align-items: flex-start; padding: 8px 0; border-bottom: 1px dashed #eee; }
.notice-item:last-child { border-bottom: none; }
.notice-text { font-size: 14px; color: #333; flex: 1; line-height: 1.5; }
.notice-date { font-size: 12px; color: #999; white-space: nowrap; margin-left: 12px; }
.todo-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px dashed #eee; }
.todo-item:last-child { border-bottom: none; }
.todo-label { font-size: 14px; color: #333; }
.todo-badge { background: #FFF3E0; color: #E65100; padding: 3px 10px; border-radius: 12px; font-size: 13px; font-weight: bold; text-align: center; }
</style>
