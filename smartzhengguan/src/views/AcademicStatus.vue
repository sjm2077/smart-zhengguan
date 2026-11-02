<template>
  <div class="academic-page">
    <el-row :gutter="14" class="stat-row">
      <el-col :span="4" v-for="card in statCards" :key="card.title">
        <DashboardCard
          :title="card.title"
          :number="card.number"
          :change="card.change"
          :changeLabel="card.changeLabel"
          :icon="card.icon"
          :iconBg="card.iconBg"
        />
      </el-col>
    </el-row>

    <el-row :gutter="14" class="chart-row">
      <el-col :span="8">
        <ChartCard title="年级分布" :chartOptions="gradePieChart" />
      </el-col>
      <el-col :span="8">
        <ChartCard title="专业分布概览" :chartOptions="top10BarChart" />
      </el-col>
      <el-col :span="8">
        <ChartCard title="学籍状态分布" :chartOptions="statusPieChart" />
      </el-col>
    </el-row>

    <el-row :gutter="14" class="chart-row equal-height-row">
      <el-col :span="14">
        <div class="section-card table-card">
          <div class="card-header">
            <span class="card-title">学籍异动记录（最近）</span>
          </div>
          <el-table :data="pagedRecords" stripe size="small" class="compact-table">
            <el-table-column prop="id" label="学号" width="110" />
            <el-table-column prop="name" label="姓名" width="70" />
            <el-table-column prop="changeType" label="异动类型" width="90" />
            <el-table-column prop="handler" label="办理人" width="80" />
            <el-table-column prop="reason" label="异动原因" min-width="120" />
            <el-table-column prop="date" label="申请日期" width="110" />
            <el-table-column prop="status" label="办理状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.tagType" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openViewDialog(row)">查看</el-button>
                <el-button link type="primary" size="small" @click="openEditDialog(row)">编辑</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="table-footer">
            <el-pagination
              v-model:current-page="recordPage"
              size="small"
              layout="prev, pager, next"
              :total="records.length"
              :page-size="5"
            />
          </div>
        </div>
      </el-col>
      <el-col :span="10">
        <ChartCard title="近五年异动人数趋势" :chartOptions="changeTrendChart" />
      </el-col>
    </el-row>

    <el-dialog v-model="viewDialogVisible" title="异动记录详情" width="520px">
      <el-descriptions v-if="activeRecord" :column="1" border>
        <el-descriptions-item label="学号">{{ activeRecord.id }}</el-descriptions-item>
        <el-descriptions-item label="姓名">{{ activeRecord.name }}</el-descriptions-item>
        <el-descriptions-item label="异动类型">{{ activeRecord.changeType }}</el-descriptions-item>
        <el-descriptions-item label="办理人">{{ activeRecord.handler }}</el-descriptions-item>
        <el-descriptions-item label="异动原因">{{ activeRecord.reason }}</el-descriptions-item>
        <el-descriptions-item label="申请日期">{{ activeRecord.date }}</el-descriptions-item>
        <el-descriptions-item label="办理状态">
          <el-tag :type="activeRecord.tagType" size="small">{{ activeRecord.status }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <el-dialog v-model="editDialogVisible" title="编辑异动记录" width="520px">
      <el-form v-if="editForm" :model="editForm" label-width="88px">
        <el-form-item label="办理人">
          <el-input v-model="editForm.handler" />
        </el-form-item>
        <el-form-item label="异动原因">
          <el-input v-model="editForm.reason" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="办理状态">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option label="办理中" value="办理中" />
            <el-option label="已通过" value="已通过" />
            <el-option label="待补材料" value="待补材料" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRecordEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import DashboardCard from '../components/DashboardCard.vue'
import ChartCard from '../components/ChartCard.vue'
import { getAcademicStatusData } from '../services/mockDataService'

const CARD_META = [
  { icon: 'user', iconBg: '#EEF4FF', unit: '人' },
  { icon: 'check-circle', iconBg: '#EEF4FF', unit: '人' },
  { icon: 'refresh', iconBg: '#EEF4FF', unit: '人' },
  { icon: 'alert-circle', iconBg: '#EEF4FF', unit: '人' },
  { icon: 'upload', iconBg: '#EEF4FF', unit: '次' },
]

const BAR_COLORS = ['#0A2463', '#0A3B8C', '#0D47A1', '#1565C0', '#1976D2', '#2196F3', '#42A5F5', '#64B5F6', '#90CAF9', '#BBDEFB']
const TREEMAP_COLORS = ['#165DFF', '#13C2C2', '#FF4D4F', '#BBDEFB']

const EMPTY_PAGE_DATA = {
  statCards: [],
  charts: {
    gradeDistribution: [],
    majorTop: [],
    statusDistribution: [],
    changeTrend: [],
  },
  records: [],
}

export default {
  components: { DashboardCard, ChartCard },
  data() {
    return {
      pageData: EMPTY_PAGE_DATA,
      recordPage: 1,
      viewDialogVisible: false,
      editDialogVisible: false,
      activeRecord: null,
      editForm: null,
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
    records() {
      return this.pageData.records || []
    },
    pagedRecords() {
      const start = (this.recordPage - 1) * 5
      return this.records.slice(start, start + 5)
    },
    gradePieChart() {
      const data = this.pageData.charts?.gradeDistribution || []
      return {
        tooltip: { trigger: 'axis', formatter: '{b}: {c}%' },
        legend: { top: 0, textStyle: { color: '#333', fontSize: 12 } },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
        xAxis: { type: 'value', max: 100, axisLabel: { color: '#666', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#E5E7EB' } } },
        yAxis: { type: 'category', data: data.map((item) => item.grade), axisLabel: { color: '#666' }, axisLine: { lineStyle: { color: '#E5E7EB' } } },
        series: [
          { name: '男生', type: 'bar', data: data.map((item) => item.male), stack: 'total', barWidth: '40%', itemStyle: { color: '#165DFF' }, label: { show: true, position: 'inside', color: '#fff', fontSize: 11, formatter: '{c}%' } },
          { name: '女生', type: 'bar', data: data.map((item) => item.female), stack: 'total', barWidth: '40%', itemStyle: { color: '#FF4D4F' }, label: { show: true, position: 'inside', color: '#fff', fontSize: 11, formatter: '{c}%' } },
        ],
      }
    },
    top10BarChart() {
      const data = [...(this.pageData.charts?.majorTop || [])].sort((left, right) => right.value - left.value)
      return {
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '10px', containLabel: true },
        xAxis: { type: 'value', axisLabel: { color: '#666', fontSize: 11 }, splitLine: { lineStyle: { color: '#E5E7EB' } } },
        yAxis: { type: 'category', data: data.map((item) => item.name), axisLabel: { color: '#666', fontSize: 11 }, axisLine: { lineStyle: { color: '#E5E7EB' } }, inverse: true },
        series: [{
          type: 'bar',
          barWidth: '55%',
          data: data.map((item, index) => ({ value: item.value, itemStyle: { color: BAR_COLORS[index] || '#165DFF' } })),
          label: { show: true, position: 'right', color: '#333', fontSize: 11 },
        }],
      }
    },
    statusPieChart() {
      const data = this.pageData.charts?.statusDistribution || []
      return {
        tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
        series: [{
          type: 'treemap',
          roam: false,
          width: '100%',
          height: '85%',
          label: { show: true, formatter: '{b}\n{c}%', fontSize: 13, color: '#fff', position: 'inside' },
          itemStyle: { borderColor: '#fff', borderWidth: 4, borderRadius: 0 },
          data: data.map((item, index) => ({ ...item, itemStyle: { color: TREEMAP_COLORS[index] || '#98A2B3' } })),
        }],
      }
    },
    changeTrendChart() {
      const data = this.pageData.charts?.changeTrend || []
      return {
        tooltip: { trigger: 'axis' },
        legend: { top: 0, textStyle: { color: '#333', fontSize: 12 } },
        grid: { left: '3%', right: '8%', bottom: '3%', top: '40px', containLabel: true },
        xAxis: { type: 'category', data: data.map((item) => item.year), axisLabel: { color: '#666' }, axisLine: { lineStyle: { color: '#E5E7EB' } } },
        yAxis: [
          { type: 'value', name: '异动人数', axisLabel: { color: '#666' }, splitLine: { lineStyle: { color: '#E5E7EB' } } },
          { type: 'value', name: '增长率', axisLabel: { color: '#666', formatter: '{value}%' }, splitLine: { show: false } },
        ],
        series: [
          { name: '异动人数', type: 'line', data: data.map((item) => item.count), color: '#165DFF', smooth: true, symbol: 'circle', symbolSize: 8, lineStyle: { width: 3 } },
          { name: '同比增长率', type: 'bar', yAxisIndex: 1, data: data.map((item) => item.growth), barWidth: '30%', itemStyle: { color: '#13C2C2' }, label: { show: true, position: 'top', color: '#333', fontSize: 11, formatter: '{c}%' } },
        ],
      }
    },
  },
  async mounted() {
    await this.loadPageData()
  },
  methods: {
    formatCardNumber(value, unit = '') {
      if (typeof value !== 'number') return value
      return `${value.toLocaleString('zh-CN')}${unit}`
    },
    async loadPageData() {
      this.pageData = await getAcademicStatusData()
    },
    openViewDialog(row) {
      this.activeRecord = row
      this.viewDialogVisible = true
    },
    openEditDialog(row) {
      this.activeRecord = row
      this.editForm = { ...row }
      this.editDialogVisible = true
    },
    saveRecordEdit() {
      const index = this.pageData.records.findIndex((item) => item.id === this.editForm.id)
      if (index === -1) return

      const statusTypeMap = {
        办理中: 'warning',
        已通过: 'success',
        待补材料: 'danger',
      }

      this.pageData.records.splice(index, 1, {
        ...this.editForm,
        tagType: statusTypeMap[this.editForm.status] || 'info',
      })
      this.editDialogVisible = false
      this.$message?.success('异动记录已更新')
    },
  },
}
</script>

<style scoped>
.academic-page { color: #333; }
.section-card { background: #fff; border-radius: 8px; padding: 16px 20px; margin-bottom: 14px; }
.stat-row { margin-bottom: 14px; row-gap: 14px; }
.stat-row .el-col { width: 20% !important; flex: 0 0 20% !important; max-width: 20% !important; }
.chart-row { margin-bottom: 14px; }
.card-header { display: flex; align-items: center; margin-bottom: 12px; }
.card-title { font-size: 16px; font-weight: 600; color: #333; }
.table-card { padding-bottom: 8px; }
.compact-table { width: 100%; font-size: 13px; }
.compact-table :deep(.el-table__header th) { background: #f8f9fa; color: #333; font-weight: 500; }
.compact-table :deep(.el-table__row:hover) { background: #f0f5ff; }
.table-footer { display: flex; justify-content: center; margin-top: 10px; }
.equal-height-row { align-items: stretch; }
.equal-height-row > .el-col { display: flex; }
.equal-height-row > .el-col > * { flex: 1; min-height: 0; }
.equal-height-row .table-card { display: flex; flex-direction: column; }
.equal-height-row .table-card .compact-table { flex: 1; }

@media (max-width: 1400px) {
  .stat-row .el-col { width: 50% !important; flex: 0 0 50% !important; max-width: 50% !important; }
}

@media (max-width: 768px) {
  .stat-row .el-col { width: 100% !important; flex: 0 0 100% !important; max-width: 100% !important; }
}
</style>
