<template>
  <div class="admission-page">
    <div class="stats-grid">
      <DashboardCard
        v-for="card in statCards"
        :key="card.title"
        :title="card.title"
        :number="card.number"
        :icon="card.icon"
        :iconBg="card.iconBg"
        :changeLabel="card.changeLabel"
      />
    </div>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="8">
        <ChartCard title="近五年报名人数趋势" :chartOptions="applyTrendChartOptions" chartHeight="300px" />
      </el-col>
      <el-col :span="8">
        <ChartCard title="报考专业 TOP10" :chartOptions="majorTopChartOptions" chartHeight="300px" />
      </el-col>
      <el-col :span="8">
        <ChartCard title="生源地分布" :chartOptions="regionDonutChartOptions" chartHeight="300px" />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="14">
        <div class="section-card progress-card">
          <div class="card-header">
            <span class="card-title">招生进度概览</span>
          </div>
          <el-table :data="progressData" class="progress-table" :header-cell-style="headerCellStyle">
            <el-table-column prop="stage" label="阶段" min-width="100" />
            <el-table-column prop="startTime" label="开始时间" min-width="110" />
            <el-table-column prop="endTime" label="结束时间" min-width="110" />
            <el-table-column prop="status" label="当前状态" min-width="90">
              <template #default="{ row }">
                <span :class="statusClass(row.status)">{{ row.status }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="completion" label="完成度" min-width="180">
              <template #default="{ row }">
                <div class="progress-cell">
                  <el-progress
                    :percentage="row.completionPercent"
                    :color="progressColor(row.completionPercent)"
                    :stroke-width="8"
                  />
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" min-width="90">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openProgressDetail(row)">查看详情</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
      <el-col :span="10">
        <div class="section-card notice-card">
          <div class="card-header">
            <span class="card-title">招生通知</span>
            <el-button link type="primary" size="small" class="more-link">更多 &gt;</el-button>
          </div>
          <ul class="notice-list">
            <li
              v-for="(item, index) in noticeList"
              :key="index"
              class="notice-item"
              @click="openNotice(item)"
            >
              <span class="notice-title">{{ item.title }}</span>
              <span class="notice-date">{{ item.date }}</span>
            </li>
          </ul>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="progressDialogVisible" title="招生进度详情" width="460px">
      <div v-if="activeProgress" class="dialog-block">
        <div class="dialog-title">{{ activeProgress.stage }}</div>
        <div class="dialog-body">开始时间：{{ activeProgress.startTime }}</div>
        <div class="dialog-body">结束时间：{{ activeProgress.endTime }}</div>
        <div class="dialog-body">当前状态：{{ activeProgress.status }}</div>
        <div class="dialog-body">完成进度：{{ activeProgress.completionPercent }}%</div>
      </div>
    </el-dialog>

    <el-dialog v-model="noticeDialogVisible" title="通知详情" width="460px">
      <div v-if="activeNotice" class="dialog-block">
        <div class="dialog-title">{{ activeNotice.title }}</div>
        <div class="dialog-time">{{ activeNotice.date }}</div>
        <div class="dialog-body">{{ activeNotice.title }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import DashboardCard from '../components/DashboardCard.vue'
import ChartCard from '../components/ChartCard.vue'
import { getAdmissionData } from '../services/mockDataService'

const CHART_COLORS = ['#2F6BFF', '#58A6FF', '#D4A017', '#8B9BB4', '#34A853', '#F59E0B']
const PIE_COLORS = ['#2F6BFF', '#58A6FF', '#D4A017', '#34A853', '#B0BEC5']
const CARD_META = [
  { icon: 'edit', iconBg: '#EEF4FF' },
  { icon: 'check-circle', iconBg: '#EEFDF3' },
  { icon: 'users', iconBg: '#ECF4FF' },
  { icon: 'graduation', iconBg: '#EEF4FF' },
  { icon: 'target', iconBg: '#F5F3FF' },
]

const EMPTY_PAGE_DATA = {
  updatedAt: '',
  statCards: [],
  charts: {
    applyTrend: [],
    majorTop: [],
    sourceDistribution: [],
  },
  progress: [],
  notices: [],
}

export default {
  components: { DashboardCard, ChartCard },
  data() {
    return {
      pageData: EMPTY_PAGE_DATA,
      progressDialogVisible: false,
      noticeDialogVisible: false,
      activeProgress: null,
      activeNotice: null,
    }
  },
  computed: {
    statCards() {
      return (this.pageData.statCards || []).map((card, index) => ({
        ...card,
        number: this.formatCardNumber(card.number),
        icon: CARD_META[index]?.icon || 'chart',
        iconBg: CARD_META[index]?.iconBg || '#EEF4FF',
      }))
    },
    progressData() {
      return this.pageData.progress || []
    },
    noticeList() {
      return this.pageData.notices || []
    },
    applyTrendChartOptions() {
      const trendData = this.pageData.charts?.applyTrend || []
      const maxValue = Math.max(...trendData.map((item) => Number(item.value || 0)), 0)
      const yAxisMax = maxValue > 0 ? Math.ceil(maxValue / 1000) * 1000 + 1000 : 6000
      return {
        tooltip: {
          trigger: 'axis',
          formatter: '{b}年<br/>报名人数：{c}人',
        },
        grid: { left: '8%', right: '5%', bottom: '10%', top: '10px', containLabel: true },
        xAxis: {
          type: 'category',
          data: trendData.map((item) => item.year),
          axisLabel: { color: '#666', fontSize: 11 },
          axisLine: { lineStyle: { color: '#E5E7EB' } },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: yAxisMax,
          axisLabel: { color: '#666', fontSize: 11 },
          splitLine: { lineStyle: { color: '#E5E7EB', type: 'dashed' } },
        },
        series: [
          {
            type: 'line',
            data: trendData.map((item) => item.value),
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            lineStyle: { color: '#2F6BFF', width: 3 },
            itemStyle: { color: '#2F6BFF', borderColor: '#fff', borderWidth: 2 },
            areaStyle: {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: 'rgba(47,107,255,0.25)' },
                  { offset: 1, color: 'rgba(47,107,255,0.02)' },
                ],
              },
            },
          },
        ],
      }
    },
    majorTopChartOptions() {
      const data = [...(this.pageData.charts?.majorTop || [])].sort((left, right) => right.value - left.value)
      return {
        tooltip: {
          trigger: 'axis',
          formatter: '{b}：{c}人',
        },
        grid: { left: '5%', right: '12%', bottom: '5%', top: '5px', containLabel: true },
        xAxis: {
          type: 'value',
          axisLabel: { color: '#666', fontSize: 11 },
          splitLine: { lineStyle: { color: '#E5E7EB', type: 'dashed' } },
        },
        yAxis: {
          type: 'category',
          inverse: true,
          data: data.map((item) => item.name),
          axisLabel: { color: '#666', fontSize: 11 },
          axisLine: { lineStyle: { color: '#E5E7EB' } },
        },
        series: [
          {
            type: 'bar',
            barWidth: '50%',
            label: {
              show: true,
              position: 'right',
              color: '#333',
              fontSize: 11,
              formatter: '{c}人',
            },
            data: data.map((item, index) => ({
              value: item.value,
              itemStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                  { offset: 0, color: CHART_COLORS[index % CHART_COLORS.length] },
                  { offset: 1, color: `${CHART_COLORS[index % CHART_COLORS.length]}88` },
                ]),
                borderRadius: [0, 0, 0, 0],
              },
            })),
          },
        ],
      }
    },
    regionDonutChartOptions() {
      const data = this.pageData.charts?.sourceDistribution || []
      return {
        tooltip: { trigger: 'item', formatter: '{b}：{c}%' },
        legend: {
          orient: 'vertical',
          right: 8,
          top: 'center',
          textStyle: { color: '#333', fontSize: 11 },
          formatter: (name) => {
            const item = data.find((entry) => entry.name === name)
            return `${name}  ${item?.value || 0}%`
          },
        },
        series: [
          {
            type: 'pie',
            radius: ['55%', '78%'],
            center: ['38%', '50%'],
            itemStyle: {
              borderColor: '#fff',
              borderWidth: 3,
              borderRadius: 0,
            },
            label: { show: false },
            emphasis: {
              scaleSize: 8,
            },
            data: data.map((item, index) => ({
              value: item.value,
              name: item.name,
              itemStyle: { color: PIE_COLORS[index] || '#B0BEC5' },
            })),
          },
        ],
      }
    },
  },
  async mounted() {
    await this.loadPageData()
  },
  methods: {
    formatCardNumber(value) {
      return typeof value === 'number' ? value.toLocaleString('zh-CN') : value
    },
    async loadPageData() {
      this.pageData = await getAdmissionData()
    },
    openProgressDetail(row) {
      this.activeProgress = row
      this.progressDialogVisible = true
    },
    openNotice(item) {
      this.activeNotice = item
      this.noticeDialogVisible = true
    },
    headerCellStyle() {
      return {
        background: '#F8FAFC',
        color: '#344054',
        fontWeight: 600,
        fontSize: '13px',
      }
    },
    statusClass(status) {
      return {
        'status-done': status === '已结束',
        'status-ongoing': status === '进行中',
        'status-pending': status === '未开始',
      }
    },
    progressColor(percent) {
      if (percent >= 100) return '#16A34A'
      if (percent > 0) return '#2F6BFF'
      return '#D1D5DB'
    },
  },
}
</script>

<style scoped>
.admission-page {
  color: #333;
}

.section-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.chart-row {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1D2939;
}

.more-link {
  font-size: 13px;
}

.progress-card {
  height: 100%;
}

.progress-table :deep(.el-table__header th) {
  background: #F8FAFC;
  color: #344054;
  font-weight: 600;
  font-size: 13px;
}

.progress-cell {
  display: flex;
  align-items: center;
}

.progress-table :deep(.el-progress-bar__outer) {
  background-color: #F0F1F3;
}

.status-done {
  color: #16A34A;
  font-weight: 500;
}

.status-ongoing {
  color: #F59E0B;
  font-weight: 500;
}

.status-pending {
  color: #98A2B3;
  font-weight: 500;
}

.notice-card {
  height: 100%;
}

.notice-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.notice-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #F0F1F3;
  cursor: pointer;
  transition: background 0.2s;
}

.notice-item:last-child {
  border-bottom: none;
}

.notice-item:hover {
  background: #F8FAFC;
  margin: 0 -20px;
  padding: 12px 20px;
}

.notice-title {
  font-size: 13px;
  color: #344054;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 16px;
}

.notice-date {
  font-size: 12px;
  color: #98A2B3;
  flex-shrink: 0;
}

.dialog-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dialog-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D2939;
}

.dialog-time {
  font-size: 12px;
  color: #98A2B3;
}

.dialog-body {
  font-size: 14px;
  color: #344054;
  line-height: 1.7;
}

@media (max-width: 1400px) {
  .stats-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
