<template>
  <div class="scholarship-page">
    <div class="page-header">
      <span class="page-title">学院奖助管理数据概览</span>
      <div class="header-right">
        <span class="update-time">数据更新时间：{{ pageData.updatedAt || '--' }}</span>
      </div>
    </div>

    <el-row :gutter="16" class="stat-row">
      <el-col :span="4.8" v-for="card in statCards" :key="card.title">
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
      <el-col :span="8"><ChartCard title="奖学金类型占比" :chartOptions="scholarshipTypeChart" /></el-col>
      <el-col :span="8"><ChartCard title="助学金类型占比" :chartOptions="aidTypeChart" /></el-col>
      <el-col :span="8"><ChartCard title="学院学生受奖情况分布" :chartOptions="studentAwardDistChart" /></el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="16"><ChartCard title="学院近五年奖助学金发放金额趋势" :chartOptions="trendChart" chartHeight="340px" /></el-col>
      <el-col :span="8"><ChartCard title="各年级获奖人数" :chartOptions="gradeAwardChart" chartHeight="340px" /></el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="24"><ChartCard title="学院专业获奖占比" :chartOptions="collegeAwardChart" chartHeight="380px" /></el-col>
    </el-row>

    <el-row :gutter="16" class="bottom-row">
      <el-col :span="12">
        <div class="info-card">
          <div class="info-card-header"><span class="info-card-title">奖励通知公告</span><a class="more-link" href="#">更多 ></a></div>
          <div class="notice-list">
            <div v-for="n in scholarshipNotices" :key="n.title" class="notice-item"><span class="notice-text">{{ n.title }}</span><span class="notice-date">{{ n.date }}</span></div>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="info-card">
          <div class="info-card-header"><span class="info-card-title">奖励待办事项</span></div>
          <div class="todo-list">
            <div v-for="t in scholarshipTodos" :key="t.label" class="todo-item"><span class="todo-label">{{ t.label }}</span><span class="todo-badge">{{ t.count }}</span></div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import DashboardCard from '../components/DashboardCard.vue'
import ChartCard from '../components/ChartCard.vue'
import { getScholarshipData } from '../services/mockDataService'

const CARD_META = [
  { icon: 'medal', iconBg: '#EEF4FF' },
  { icon: 'wallet', iconBg: '#EEF4FF' },
  { icon: 'user', iconBg: '#EEF4FF' },
  { icon: 'award', iconBg: '#EEF4FF' },
  { icon: 'chart', iconBg: '#EEF4FF' },
]
const EMPTY_PAGE_DATA = {
  updatedAt: '',
  statCards: [],
  charts: {
    scholarshipTypes: [],
    aidTypes: [],
    gradeAwards: [],
    studentAwardDistribution: [],
    majorAwardTop: [],
    fundTrend: [],
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
        number: this.formatCardNumber(card.number, card.unit),
        change: null,
        changeLabel: card.changeLabel,
        icon: CARD_META[index]?.icon || 'chart',
        iconBg: CARD_META[index]?.iconBg || '#EEF4FF',
      }))
    },
    scholarshipNotices() {
      return this.pageData.notices || []
    },
    scholarshipTodos() {
      return this.pageData.todos || []
    },
    scholarshipTypeChart() {
      const data = this.pageData.charts?.scholarshipTypes || []
      const colors = ['#165DFF', '#722ED1', '#13C2C2', '#FA8C16']
      return {
        tooltip: { trigger: 'item', formatter: '{b}：{c}%' },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          textStyle: { color: '#333', fontSize: 12 },
          itemWidth: 10,
          itemHeight: 10,
        },
        series: [{
          type: 'pie',
          radius: ['52%', '72%'],
          center: ['35%', '50%'],
          itemStyle: { borderColor: '#fff', borderWidth: 3 },
          label: { show: true, color: '#333', fontSize: 12, formatter: '{b}\n{c}%' },
          labelLine: { length: 12, length2: 10 },
          data: data.map((item, index) => ({
            ...item,
            itemStyle: { color: colors[index] || '#165DFF' },
          })),
        }],
      }
    },
    aidTypeChart() {
      const data = [...(this.pageData.charts?.aidTypes || [])].sort((left, right) => left.value - right.value)
      const colors = ['#FA8C16', '#13C2C2', '#165DFF']
      return {
        tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
        grid: { left: '3%', right: '8%', bottom: '3%', top: '10px', containLabel: true },
        xAxis: { type: 'value', max: 100, axisLabel: { color: '#666', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#E5E7EB' } } },
        yAxis: { type: 'category', data: data.map((item) => item.name), axisLabel: { color: '#666' }, axisLine: { lineStyle: { color: '#E5E7EB' } } },
        series: [{
          type: 'bar',
          barWidth: '50%',
          label: { show: true, position: 'right', color: '#333', fontSize: 12, formatter: '{c}%' },
          data: data.map((item, index) => ({
            value: item.value,
            itemStyle: { color: colors[index] || '#165DFF', borderRadius: [0, 0, 0, 0] },
          })),
        }],
      }
    },
    gradeAwardChart() {
      const data = this.pageData.charts?.gradeAwards || []
      return {
        tooltip: { trigger: 'axis' },
        legend: { top: 0, textStyle: { color: '#333', fontSize: 12 } },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
        xAxis: { type: 'category', data: data.map((item) => item.grade), axisLabel: { color: '#666' }, axisLine: { lineStyle: { color: '#E5E7EB' } } },
        yAxis: { type: 'value', axisLabel: { color: '#666' }, splitLine: { lineStyle: { color: '#E5E7EB' } } },
        series: [
          { name: '国家奖学金', type: 'bar', data: data.map((item) => item.national), stack: 'total', barWidth: '45%', itemStyle: { color: '#165DFF' }, label: { show: true, position: 'inside', color: '#fff', fontSize: 11 } },
          { name: '学业奖学金', type: 'bar', data: data.map((item) => item.academic), stack: 'total', barWidth: '45%', itemStyle: { color: '#722ED1' }, label: { show: true, position: 'inside', color: '#fff', fontSize: 11 } },
          { name: '社会奖学金', type: 'bar', data: data.map((item) => item.social), stack: 'total', barWidth: '45%', itemStyle: { color: '#13C2C2' }, label: { show: true, position: 'inside', color: '#fff', fontSize: 11 } },
        ],
      }
    },
    studentAwardDistChart() {
      const data = this.pageData.charts?.studentAwardDistribution || []
      const colors = ['#165DFF', '#13C2C2', '#FA8C16']
      return {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c} ({d}%)',
          confine: true,
          position(p, a, d, r, s) {
            return [s.viewSize[0] - 170, s.viewSize[1] / 2 - d.offsetHeight / 2]
          },
        },
        legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#333', fontSize: 12 } },
        series: [{
          type: 'pie',
          radius: ['50%', '70%'],
          center: ['35%', '50%'],
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
    collegeAwardChart() {
      const data = this.pageData.charts?.majorAwardTop || []
      const colors = ['#165DFF', '#13C2C2', '#722ED1', '#FA8C16', '#F53F3F', '#98A2B3']
      return {
        tooltip: { trigger: 'item', formatter: '{b}：{c}人（{d}%）' },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          textStyle: { color: '#666', fontSize: 11 },
          itemWidth: 8,
          itemHeight: 8,
        },
        series: [{
          type: 'pie',
          roseType: 'area',
          radius: ['20%', '68%'],
          center: ['38%', '50%'],
          itemStyle: { borderRadius: 0, borderColor: '#fff', borderWidth: 2 },
          label: { show: true, fontSize: 11, color: '#333', formatter: '{b}\n{d}%' },
          emphasis: { label: { fontSize: 14, fontWeight: 'bold' }, scaleSize: 10 },
          data: data.map((item, index) => ({
            value: item.value,
            name: item.name,
            itemStyle: { color: colors[index] || '#165DFF' },
          })),
        }],
      }
    },
    trendChart() {
      const data = this.pageData.charts?.fundTrend || []
      return {
        tooltip: { trigger: 'axis', confine: true },
        legend: { top: 0, textStyle: { color: '#333' } },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
        xAxis: { type: 'category', data: data.map((item) => item.year), axisLabel: { color: '#666' }, axisLine: { lineStyle: { color: '#E5E7EB' } } },
        yAxis: { type: 'value', axisLabel: { color: '#666' }, splitLine: { lineStyle: { color: '#E5E7EB' } } },
        series: [
          {
            name: '发放金额',
            type: 'line',
            data: data.map((item) => item.value),
            lineStyle: { color: '#165DFF' },
            itemStyle: { color: '#165DFF', borderColor: '#165DFF', borderWidth: 2 },
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
          },
        ],
      }
    },
  },
  async mounted() {
    this.pageData = await getScholarshipData()
  },
  methods: {
    formatCardNumber(value, unit = '') {
      if (typeof value !== 'number') return value
      const display = Number.isInteger(value) ? value.toLocaleString('zh-CN') : value.toFixed(1)
      return `${display}${unit || ''}`
    },
  },
}
</script>

<style scoped>
.scholarship-page { color: #333; }
.scholarship-page :deep(.chart-card) { background: #fff; }
.scholarship-page :deep(.chart-title) { font-size: 16px; font-weight: 700; color: #333; }
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
