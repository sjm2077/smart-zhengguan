<template>
  <div class="training-page">
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6" v-for="card in statCards" :key="card.title">
        <DashboardCard
          :title="card.title"
          :number="card.number"
          :icon="card.icon"
          :iconBg="card.iconBg"
          :changeLabel="card.changeLabel"
        />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row overview-row">
      <el-col :span="8" class="chart-col">
        <ChartCard
          title="培养计划完成情况"
          :chartOptions="planCompletionOptions"
          :showExport="true"
          chartHeight="280px"
        />
      </el-col>
      <el-col :span="8" class="chart-col">
        <ChartCard
          title="近五年培养计划完成率趋势"
          :chartOptions="trendOptions"
          chartHeight="280px"
        />
      </el-col>
      <el-col :span="8" class="chart-col">
        <ChartCard
          title="审核状态分布"
          :chartOptions="statusChartOptions"
          chartHeight="280px"
        />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="8" class="chart-col">
        <ChartCard
          title="各年级完成率"
          :chartOptions="completionChartOptions"
          chartHeight="280px"
        />
      </el-col>
      <el-col :span="8" class="chart-col">
        <ChartCard
          title="培养环节分布"
          :chartOptions="stageChartOptions"
          chartHeight="280px"
        />
      </el-col>
      <el-col :span="8" class="chart-col">
        <ChartCard
          title="培养评价结果分布"
          :chartOptions="evaluationOptions"
          chartHeight="280px"
        />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row detail-row">
      <el-col :span="8" class="chart-col">
        <ChartCard
          title="多维度培养评价雷达图"
          :chartOptions="radarOptions"
          chartHeight="280px"
        />
      </el-col>
      <el-col :span="16" class="chart-col">
        <div class="section-card table-card">
          <div class="card-header">
            <span class="card-title">培养计划列表</span>
            <div class="card-header-right">
              <el-button class="export-table-btn" size="small" text @click="exportTable">导出Excel</el-button>
            </div>
          </div>
          <div class="table-wrapper">
            <el-table
              :data="pagedPlans"
              stripe
              size="small"
              class="compact-table"
              @row-click="handleRowClick"
              highlight-current-row
            >
              <el-table-column prop="studentId" label="学号" width="85" sortable />
              <el-table-column prop="name" label="姓名" width="70" />
              <el-table-column prop="grade" label="年级" width="80" sortable />
              <el-table-column prop="major" label="专业" min-width="100" />
              <el-table-column prop="stage" label="培养环节" width="85" sortable />
              <el-table-column label="状态" width="80">
                <template #default="scope">
                  <el-tag :type="scope.row.tagType" size="small">{{ scope.row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70" fixed="right">
                <template #default>
                  <el-button link type="primary" size="small">查看</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div class="table-footer">
            <span class="card-tip">共 {{ filteredPlans.length }} 条</span>
            <el-pagination
              v-model:current-page="currentPage"
              size="small"
              layout="prev, pager, next"
              :total="filteredPlans.length"
              :page-size="pageSize"
            />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import DashboardCard from '../components/DashboardCard.vue'
import ChartCard from '../components/ChartCard.vue'
import { getTrainingData } from '../services/mockDataService'

const CARD_META = [
  { icon: 'layers', iconBg: '#EEF4FF' },
  { icon: 'shield', iconBg: '#EEF4FF' },
  { icon: 'trend', iconBg: '#EEF4FF' },
  { icon: 'user', iconBg: '#EEF4FF' },
]
const EMPTY_PAGE_DATA = {
  filters: {
    default: { grade: '', major: '', stage: '', status: '' },
    grades: [],
    majors: [],
    stages: [],
    statuses: [],
  },
  charts: {
    planCompletion: [],
    completionTrend: [],
    statusDistribution: [],
    gradeCompletion: [],
    stageDistribution: [],
    evaluationDistribution: [],
    radar: [],
  },
  plans: [],
  notices: [],
  todos: [],
}

export default {
  components: { DashboardCard, ChartCard },
  data() {
    return {
      pageData: EMPTY_PAGE_DATA,
      currentPage: 1,
      pageSize: 4,
      filters: { ...EMPTY_PAGE_DATA.filters.default },
    }
  },
  computed: {
    gradeOptions() {
      return this.pageData.filters?.grades || []
    },
    majorOptions() {
      return this.pageData.filters?.majors || []
    },
    stageOptions() {
      return this.pageData.filters?.stages || []
    },
    statusOptions() {
      return this.pageData.filters?.statuses || []
    },
    plans() {
      return this.pageData.plans || []
    },
    filteredPlans() {
      return this.plans.filter((item) => {
        const matchGrade = !this.filters.grade || item.grade === this.filters.grade
        const matchMajor = !this.filters.major || item.major === this.filters.major
        const matchStage = !this.filters.stage || item.stage === this.filters.stage
        const matchStatus = !this.filters.status || item.status === this.filters.status
        return matchGrade && matchMajor && matchStage && matchStatus
      })
    },
    pagedPlans() {
      const start = (this.currentPage - 1) * this.pageSize
      return this.filteredPlans.slice(start, start + this.pageSize)
    },
    statCards() {
      const total = this.filteredPlans.length
      const pendingReview = this.filteredPlans.filter((item) => item.status === '待审核').length
      const approved = this.filteredPlans.filter((item) => item.status === '审核通过').length
      const averageCompletion = total
        ? Math.round(this.filteredPlans.reduce((sum, item) => sum + item.completion, 0) / total)
        : 0
      const advisorConfirmed = this.filteredPlans.filter((item) => item.status !== '待提交').length
      const advisorRate = total ? Math.round((advisorConfirmed / total) * 100) : 0

      return [
        { title: '培养计划总数', number: `${total}项`, changeLabel: '当前筛选结果' },
        { title: '待审核计划', number: `${pendingReview}项`, changeLabel: '需本周完成处理' },
        { title: '平均完成率', number: `${averageCompletion}%`, changeLabel: `已通过 ${approved} 项` },
        { title: '导师确认率', number: `${advisorRate}%`, changeLabel: '按当前记录统计' },
      ].map((card, index) => ({
        ...card,
        icon: CARD_META[index]?.icon || 'chart',
        iconBg: CARD_META[index]?.iconBg || '#EEF4FF',
      }))
    },
    planCompletionOptions() {
      const data = this.pageData.charts?.planCompletion || []
      const colorMap = {
        已完成: '#165DFF',
        进行中: '#0FC6C2',
        未开始: '#722ED1',
        已终止: '#FF7D00',
      }
      return {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => `${params[0].name}：${params[0].value}%`,
          backgroundColor: '#fff',
          borderColor: '#E5E6EB',
          textStyle: { color: '#333', fontSize: 13 },
        },
        grid: { left: '3%', right: '8%', bottom: '3%', top: '10px', containLabel: true },
        xAxis: {
          type: 'value',
          max: 100,
          axisLabel: { color: '#86909C', fontSize: 12, formatter: '{value}%' },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { lineStyle: { color: '#F0F0F0', type: 'dashed' } },
        },
        yAxis: {
          type: 'category',
          data: data.map((item) => item.name),
          axisLabel: { color: '#333', fontSize: 13 },
          axisLine: { lineStyle: { color: '#F0F0F0' } },
          axisTick: { show: false },
        },
        series: [{
          type: 'bar',
          barWidth: '50%',
          data: data.map((item) => ({
            value: item.value,
            itemStyle: { color: colorMap[item.name] || '#165DFF', borderRadius: [0, 0, 0, 0] },
          })),
          label: { show: true, position: 'right', color: '#333', fontSize: 12, formatter: '{c}%' },
        }],
      }
    },
    trendOptions() {
      const data = this.pageData.charts?.completionTrend || []
      return {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => params.map((item) => `${item.seriesName === '目标线' ? '目标完成率' : `${item.axisValue}年` }：${item.value}%`).join('<br/>'),
          backgroundColor: '#fff',
          borderColor: '#E5E6EB',
          textStyle: { color: '#333', fontSize: 13 },
        },
        grid: { left: '3%', right: '5%', bottom: '3%', top: '30px', containLabel: true },
        legend: { top: 0, textStyle: { color: '#666', fontSize: 12 }, itemWidth: 16, itemHeight: 2 },
        xAxis: {
          type: 'category',
          data: data.map((item) => item.year),
          axisLabel: { color: '#86909C', fontSize: 12 },
          axisLine: { lineStyle: { color: '#F0F0F0' } },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          min: 60,
          max: 100,
          axisLabel: { color: '#86909C', fontSize: 12, formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#F0F0F0', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        series: [
          {
            name: '实际完成率',
            type: 'line',
            data: data.map((item) => item.actual),
            lineStyle: { color: '#165DFF', width: 2 },
            itemStyle: { color: '#165DFF', borderColor: '#165DFF', borderWidth: 2 },
            symbol: 'circle',
            symbolSize: 8,
            label: { show: true, color: '#333', fontSize: 12, formatter: '{c}%', position: 'top' },
          },
          {
            name: '目标线',
            type: 'line',
            data: data.map((item) => item.target),
            lineStyle: { color: '#F53F3F', type: 'dashed', width: 2 },
            itemStyle: { color: '#F53F3F' },
            symbol: 'none',
            label: { show: false },
          },
        ],
      }
    },
    statusChartOptions() {
      const data = this.pageData.charts?.statusDistribution || []
      const colorMap = { '待提交': '#86909C', '待审核': '#FF7D00', '审核通过': '#165DFF', '驳回修改': '#F53F3F' }
      return {
        tooltip: {
          trigger: 'item',
          formatter: '{b}：{c} 人',
          backgroundColor: '#fff',
          borderColor: '#E5E6EB',
          textStyle: { color: '#333', fontSize: 13 },
        },
        legend: {
          bottom: 0,
          textStyle: { color: '#666', fontSize: 12 },
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 16,
        },
        series: [{
          type: 'pie',
          radius: ['55%', '70%'],
          center: ['50%', '43%'],
          itemStyle: { borderRadius: 0, borderColor: '#fff', borderWidth: 3 },
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#333' }, scaleSize: 8 },
          data: data.map((item) => ({
            ...item,
            itemStyle: { color: colorMap[item.name] || '#86909C' },
          })),
        }],
      }
    },
    completionChartOptions() {
      const data = this.pageData.charts?.gradeCompletion || []
      return {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => `${params[0].axisValue}：${params[0].value}%`,
          backgroundColor: '#fff',
          borderColor: '#E5E6EB',
          textStyle: { color: '#333', fontSize: 13 },
        },
        grid: { left: '3%', right: '5%', bottom: '3%', top: '10px', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.map((item) => item.grade),
          axisLabel: { color: '#86909C', fontSize: 12, margin: 12 },
          axisLine: { lineStyle: { color: '#F0F0F0' } },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          max: 100,
          axisLabel: { color: '#86909C', fontSize: 12, formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#F0F0F0', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        series: [{
          type: 'line',
          data: data.map((item) => item.value),
          lineStyle: { color: '#165DFF', width: 2 },
          itemStyle: { color: '#165DFF', borderColor: '#165DFF', borderWidth: 2 },
          symbol: 'circle',
          symbolSize: 8,
          label: { show: true, color: '#333', fontSize: 12, formatter: '{c}%', position: 'top' },
        }],
      }
    },
    stageChartOptions() {
      const data = this.pageData.charts?.stageDistribution || []
      return {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => `${params[0].name}：${params[0].value} 人`,
          backgroundColor: '#fff',
          borderColor: '#E5E6EB',
          textStyle: { color: '#333', fontSize: 13 },
        },
        grid: { left: '3%', right: '5%', bottom: '3%', top: '10px', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.map((item) => item.name),
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
        series: [{
          type: 'bar',
          barWidth: '48%',
          data: data.map((item) => ({
            value: item.value,
            itemStyle: { color: '#165DFF', borderRadius: [0, 0, 0, 0] },
          })),
          label: { show: true, position: 'top', color: '#165DFF', fontSize: 12, formatter: '{c}' },
        }],
      }
    },
    evaluationOptions() {
      const data = this.pageData.charts?.evaluationDistribution || []
      const colorMap = {
        优秀: '#165DFF',
        良好: '#0FC6C2',
        合格: '#722ED1',
        不合格: '#FF7D00',
      }
      return {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const lines = params.filter((item) => item.value > 0).map((item) => `${item.seriesName}：${item.value}%`)
            return lines.length ? lines.join('<br/>') : '无数据'
          },
          backgroundColor: '#fff',
          borderColor: '#E5E6EB',
          textStyle: { color: '#333', fontSize: 13 },
        },
        grid: { left: '3%', right: '8%', bottom: '3%', top: '10px', containLabel: true },
        xAxis: {
          type: 'value',
          max: 100,
          axisLabel: { color: '#86909C', fontSize: 12, formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#F0F0F0', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'category',
          data: ['评价分布'],
          axisLabel: { color: '#333', fontSize: 13 },
          axisLine: { lineStyle: { color: '#F0F0F0' } },
          axisTick: { show: false },
        },
        series: data.map((item) => ({
          name: item.name,
          type: 'bar',
          stack: 'total',
          barWidth: '40%',
          data: [item.value],
          color: colorMap[item.name] || '#165DFF',
          label: { show: true, fontSize: 12, color: '#fff', formatter: (params) => (params.value > 8 ? `${params.value}%` : '') },
          itemStyle: { borderColor: '#fff', borderWidth: 1 },
        })),
      }
    },
    radarOptions() {
      const data = this.pageData.charts?.radar || []
      if (!data.length) {
        return {
          title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999', fontSize: 14 } },
        }
      }
      return {
        tooltip: {
          trigger: 'item',
          formatter: (params) => params.name ? `${params.name}：${params.value} 分` : '',
          backgroundColor: '#fff',
          borderColor: '#E5E6EB',
          textStyle: { color: '#333', fontSize: 13 },
        },
        legend: { bottom: 0, textStyle: { color: '#666', fontSize: 12 }, itemWidth: 16, itemHeight: 2 },
        radar: {
          center: ['50%', '45%'],
          radius: '62%',
          indicator: data.map((item) => ({ name: item.name, max: 5 })),
          axisName: { color: '#333', fontSize: 13 },
          axisLine: { lineStyle: { color: '#F0F0F0' } },
          splitLine: { lineStyle: { color: '#F0F0F0' } },
          splitArea: { areaStyle: { color: ['rgba(22,93,255,0.02)', 'rgba(22,93,255,0.04)'] } },
        },
        series: [{
          type: 'radar',
          name: '当前评分',
          data: [{ value: data.map((item) => item.value), name: '当前评分' }],
          lineStyle: { color: '#165DFF', width: 2 },
          itemStyle: { color: '#165DFF', borderColor: '#165DFF', borderWidth: 2 },
          areaStyle: { color: 'rgba(22,93,255,0.08)' },
          symbol: 'circle',
          symbolSize: 6,
        }],
      }
    },
  },
  async mounted() {
    await this.loadPageData()
  },
  methods: {
    async loadPageData() {
      const data = await getTrainingData()
      this.pageData = data
      this.filters = { ...(data.filters?.default || EMPTY_PAGE_DATA.filters.default) }
    },
    handleRowClick(row) {
      if (this.$message) this.$message.info(`查看 ${row.name} 的培养计划详情`)
    },
    exportTable() {
      if (this.$message) this.$message.success('表格数据导出中...')
    },
  },
}
</script>

<style scoped>
.training-page {
  color: #333;
  padding: 0;
}

.section-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 0;
  height: 100%;
}

.stat-row { margin-bottom: 16px; }
.chart-row {
  margin-bottom: 16px;
  display: flex;
  flex-wrap: wrap;
}
.detail-row { margin-bottom: 0; }
.chart-col {
  margin-bottom: 0;
  display: flex;
}
.chart-col > * {
  width: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #F0F0F0;
}
.card-title { font-size: 16px; font-weight: 400; color: #333; }
.card-header-right { display: flex; align-items: center; gap: 12px; }
.card-tip { font-size: 12px; color: #86909C; }
.export-table-btn { font-size: 12px; color: #165DFF; }

.table-card,
.notice-card {
  display: flex;
  flex-direction: column;
  min-height: 356px;
}
.table-wrapper { flex: 1; overflow-x: auto; }
.compact-table { width: 100%; }
.compact-table :deep(.el-table__header-wrapper th) {
  background-color: #F7F8FA;
  color: #333;
  font-weight: 600;
  font-size: 14px;
  height: 42px;
  border-bottom: 1px solid #E5E6EB;
}
.compact-table :deep(.el-table__body-wrapper td) {
  font-size: 14px;
  color: #333;
  height: 40px;
  border-bottom: 1px solid #E5E6EB;
}
.compact-table :deep(.el-table__cell) {
  padding: 8px 0;
}
.compact-table :deep(.el-table__body tr) { cursor: pointer; }
.compact-table :deep(.el-table__body tr:hover > td) { background-color: #F0F5FF !important; }
.compact-table :deep(.el-table__body tr.current-row > td) { background-color: #F0F5FF !important; }
.compact-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) { background-color: #FAFAFA; }
.compact-table :deep(.el-table__body tr.el-table__row--striped:hover > td) { background-color: #F0F5FF !important; }

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #F0F0F0;
}

.notice-list { flex: 1; }
.notice-item {
  display: flex;
  align-items: center;
  min-height: 36px;
  padding: 0 4px;
  border-bottom: 1px solid #F5F5F5;
  cursor: pointer;
  transition: background-color 0.2s;
  gap: 8px;
}
.notice-item:last-child { border-bottom: none; }
.notice-item:hover { background-color: #F7F8FA; }
.notice-item.read .notice-text { color: #999; }
.notice-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #F53F3F;
  flex-shrink: 0;
}
.notice-text {
  font-size: 13px;
  color: #333;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.notice-date { font-size: 12px; color: #666; white-space: nowrap; flex-shrink: 0; }

.todo-box {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #F0F0F0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.todo-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 6px;
  background: #F7F8FA;
  transition: background-color 0.2s;
}
.todo-item:hover { background: #EEF2FF; }
.todo-label { font-size: 13px; color: #333; }
.todo-count {
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: #165DFF;
  border-radius: 10px;
  padding: 2px 10px;
  min-width: 24px;
  text-align: center;
}

@media (max-width: 1199px) and (min-width: 768px) {
  .chart-col,
  .stat-row .el-col {
    flex: 0 0 100%;
    max-width: 100%;
    margin-bottom: 16px;
  }
  .table-wrapper { overflow-x: auto; }
}

@media (max-width: 767px) {
  .chart-col,
  .stat-row .el-col {
    flex: 0 0 100%;
    max-width: 100%;
    margin-bottom: 16px;
  }
  .table-wrapper { overflow-x: auto; }
}
</style>
