<template>
  <div class="feature-page">
    <div class="page-header">
      <div class="header-left">
        <span class="page-title">{{ config.title }}</span>
        <span class="page-subtitle">{{ config.subtitle }}</span>
      </div>
      <div class="header-right">
        <span class="update-time">数据更新时间：{{ config.updatedAt }}</span>
        <el-button
          v-if="config.primaryAction"
          :type="config.primaryAction.type || 'primary'"
          class="primary-action-btn"
          @click="handlePrimaryAction"
        >
          {{ config.primaryAction.label }}
        </el-button>
      </div>
    </div>

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

    <el-row :gutter="16" class="chart-row">
      <el-col :span="14">
        <ChartCard :title="config.trendChart.title" :chartOptions="trendChartOptions" chartHeight="320px" />
      </el-col>
      <el-col :span="10">
        <ChartCard :title="config.donutChart.title" :chartOptions="donutChartOptions" chartHeight="320px" />
      </el-col>
    </el-row>

    <el-row :gutter="16" class="chart-row">
      <el-col :span="10">
        <ChartCard :title="config.barChart.title" :chartOptions="barChartOptions" chartHeight="320px" />
      </el-col>
      <el-col :span="14">
        <div class="section-card table-card">
          <div class="card-header">
            <span class="card-title">{{ config.tableCard.title }}</span>
            <el-tag type="info" effect="plain">共 {{ config.tableCard.rows.length }} 条</el-tag>
          </div>
          <el-table :data="config.tableCard.rows" stripe size="small" class="compact-table" @row-click="openRowDetail">
            <el-table-column
              v-for="column in config.tableCard.columns"
              :key="column.prop"
              :prop="column.prop"
              :label="column.label"
              :width="column.width"
              :min-width="column.minWidth"
            >
              <template v-if="column.kind === 'tag'" #default="{ row }">
                <el-tag :type="row[column.typeField || 'statusType'] || 'info'" size="small">
                  {{ row[column.prop] }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click.stop="openRowDetail(row)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="bottom-row">
      <el-col :span="12">
        <div class="section-card info-card">
          <div class="card-header">
            <span class="card-title">{{ config.noticeCard.title }}</span>
            <a class="more-link" href="#" @click.prevent="noticeListVisible = true">更多 ></a>
          </div>
          <div class="notice-list">
            <div
              v-for="item in config.noticeCard.items"
              :key="`${item.title}-${item.date}`"
              class="notice-item clickable"
              @click="openNotice(item)"
            >
              <span class="notice-title">{{ item.title }}</span>
              <span class="notice-date">{{ item.date }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="section-card info-card">
          <div class="card-header">
            <span class="card-title">{{ config.todoCard.title }}</span>
            <el-tag type="primary" effect="plain">{{ totalTodoCount }}</el-tag>
          </div>
          <div class="todo-list">
            <div v-for="item in config.todoCard.items" :key="item.label" class="todo-item" @click="openTodo(item)">
              <div class="todo-left">
                <span class="todo-dot"></span>
                <span class="todo-label">{{ item.label }}</span>
              </div>
              <span class="todo-count">{{ item.count }}</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-drawer v-model="rowDetailVisible" title="记录详情" size="420px">
      <el-descriptions v-if="activeRow" :column="1" border>
        <el-descriptions-item
          v-for="column in detailColumns"
          :key="column.prop"
          :label="column.label"
        >
          <el-tag v-if="column.kind === 'tag'" :type="activeRow[column.typeField || 'statusType'] || 'info'" size="small">
            {{ activeRow[column.prop] }}
          </el-tag>
          <span v-else>{{ activeRow[column.prop] || '-' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-drawer>

    <el-dialog v-model="noticeDetailVisible" title="通知详情" width="460px">
      <div v-if="activeNotice" class="dialog-block">
        <div class="dialog-title">{{ activeNotice.title }}</div>
        <div class="dialog-time">{{ activeNotice.date }}</div>
        <div class="dialog-body">{{ activeNotice.title }}</div>
      </div>
    </el-dialog>

    <el-dialog v-model="noticeListVisible" title="通知列表" width="520px">
      <div class="dialog-list">
        <div
          v-for="item in config.noticeCard.items"
          :key="`${item.title}-${item.date}-list`"
          class="dialog-list-item"
          @click="openNotice(item)"
        >
          <span>{{ item.title }}</span>
          <span class="dialog-time">{{ item.date }}</span>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="todoDetailVisible" title="待办详情" width="420px">
      <div v-if="activeTodo" class="dialog-block">
        <div class="dialog-title">{{ activeTodo.label }}</div>
        <div class="dialog-body">当前待处理数量：{{ activeTodo.count }}</div>
        <div class="dialog-tip">该模块目前已接入前端待办展示，后续可继续补状态流转和批量处理。</div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import DashboardCard from './DashboardCard.vue'
import ChartCard from './ChartCard.vue'

const DONUT_COLORS = ['#165DFF', '#0FC6C2', '#722ED1', '#FA8C16', '#98A2B3']
const BAR_COLORS = ['#0A2463', '#165DFF', '#52A3FF', '#7CC1FF', '#A8D6FF', '#C9E6FF']

export default {
  components: { DashboardCard, ChartCard },
  props: {
    config: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      rowDetailVisible: false,
      noticeDetailVisible: false,
      noticeListVisible: false,
      todoDetailVisible: false,
      activeRow: null,
      activeNotice: null,
      activeTodo: null,
    }
  },
  computed: {
    statCards() {
      return (this.config.statCards || []).map((card) => ({
        ...card,
        number: this.formatCardNumber(card.number),
      }))
    },
    totalTodoCount() {
      return (this.config.todoCard?.items || []).reduce((sum, item) => sum + Number(item.count || 0), 0)
    },
    detailColumns() {
      return this.config.tableCard?.columns || []
    },
    trendChartOptions() {
      const chart = this.config.trendChart
      return {
        tooltip: {
          trigger: 'axis',
          formatter: (params) => params.map((item) => `${item.seriesName}：${item.value}${chart.unit || ''}`).join('<br/>'),
        },
        legend: {
          top: 0,
          textStyle: { color: '#666', fontSize: 12 },
        },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '40px', containLabel: true },
        xAxis: {
          type: 'category',
          data: chart.labels,
          axisLabel: { color: '#666' },
          axisLine: { lineStyle: { color: '#E5E7EB' } },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            color: '#666',
            formatter: chart.unit ? `{value}${chart.unit}` : '{value}',
          },
          splitLine: { lineStyle: { color: '#E5E7EB', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        series: [
          {
            name: chart.seriesName,
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 8,
            data: chart.values,
            lineStyle: { color: '#165DFF', width: 3 },
            itemStyle: { color: '#165DFF', borderColor: '#fff', borderWidth: 2 },
            areaStyle: { color: 'rgba(22,93,255,0.10)' },
          },
          ...(chart.targetValues ? [{
            name: chart.targetName || '目标值',
            type: 'line',
            smooth: true,
            symbol: 'none',
            data: chart.targetValues,
            lineStyle: { color: '#F53F3F', width: 2, type: 'dashed' },
          }] : []),
        ],
      }
    },
    donutChartOptions() {
      const chart = this.config.donutChart
      const total = chart.items.reduce((sum, item) => sum + Number(item.value || 0), 0)
      return {
        tooltip: {
          trigger: 'item',
          formatter: chart.unit === '%'
            ? '{b}：{c}%'
            : `{b}：{c}${chart.unit || ''}（{d}%）`,
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          textStyle: { color: '#333', fontSize: 12 },
        },
        series: [{
          type: 'pie',
          radius: ['52%', '72%'],
          center: ['38%', '46%'],
          itemStyle: { borderRadius: 0, borderColor: '#fff', borderWidth: 3 },
          label: { show: false },
          emphasis: { label: { show: true, fontSize: 14, fontWeight: 'bold' } },
          data: chart.items.map((item, index) => ({
            ...item,
            itemStyle: { color: item.color || DONUT_COLORS[index % DONUT_COLORS.length] },
          })),
        }],
        graphic: chart.centerLabel ? [
          {
            type: 'text',
            left: '38%',
            top: '38%',
            style: {
              text: chart.centerValue || (chart.unit === '%' ? `${total}%` : this.formatCardNumber(total)),
              fill: '#1F2937',
              fontSize: 20,
              fontWeight: 600,
              textAlign: 'center',
            },
          },
          {
            type: 'text',
            left: '36%',
            top: '49%',
            style: {
              text: chart.centerLabel,
              fill: '#86909C',
              fontSize: 11,
              textAlign: 'center',
            },
          },
        ] : [],
      }
    },
    barChartOptions() {
      const chart = this.config.barChart
      const data = [...chart.items].sort((left, right) => right.value - left.value)
      return {
        tooltip: {
          trigger: 'axis',
          formatter: chart.unit === '%'
            ? '{b}：{c}%'
            : `{b}：{c}${chart.unit || ''}`,
        },
        grid: { left: '3%', right: '10%', bottom: '3%', top: '5px', containLabel: true },
        xAxis: {
          type: 'value',
          axisLabel: {
            color: '#666',
            formatter: chart.unit ? `{value}${chart.unit}` : '{value}',
          },
          splitLine: { lineStyle: { color: '#E5E7EB', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'category',
          inverse: true,
          data: data.map((item) => item.name),
          axisLabel: { color: '#666', fontSize: 11 },
          axisLine: { lineStyle: { color: '#E5E7EB' } },
        },
        series: [{
          type: 'bar',
          barWidth: '52%',
          data: data.map((item, index) => ({
            value: item.value,
            itemStyle: { color: item.color || BAR_COLORS[index % BAR_COLORS.length], borderRadius: [0, 0, 0, 0] },
          })),
          label: {
            show: true,
            position: 'right',
            color: '#333',
            fontSize: 11,
            formatter: chart.unit ? `{c}${chart.unit}` : '{c}',
          },
        }],
      }
    },
  },
  methods: {
    formatCardNumber(value) {
      if (typeof value === 'number') {
        return Number.isInteger(value) ? value.toLocaleString('zh-CN') : value.toFixed(1)
      }
      return value
    },
    handlePrimaryAction() {
      const action = this.config.primaryAction
      if (!action) return
      if (action.route) {
        this.$router.push(action.route)
        return
      }
      this.$message?.success(action.message || `${action.label} 已执行`)
    },
    openRowDetail(row) {
      this.activeRow = row
      this.rowDetailVisible = true
    },
    openNotice(item) {
      this.activeNotice = item
      this.noticeDetailVisible = true
    },
    openTodo(item) {
      this.activeTodo = item
      this.todoDetailVisible = true
    },
  },
}
</script>

<style scoped>
.feature-page {
  color: #333;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.page-subtitle {
  font-size: 13px;
  color: #86909C;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.update-time {
  font-size: 13px;
  color: #86909C;
}

.primary-action-btn {
  background: #0A2463 !important;
  border-color: #0A2463 !important;
}

.stat-row,
.chart-row,
.bottom-row {
  margin-bottom: 16px;
}

.section-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  height: 100%;
}

.table-card,
.info-card {
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #F0F0F0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1D2939;
}

.compact-table :deep(.el-table__header th) {
  background: #F8FAFC;
  color: #344054;
  font-weight: 600;
  font-size: 13px;
}

.more-link {
  font-size: 13px;
  color: #165DFF;
  text-decoration: none;
}

.notice-list,
.todo-list,
.dialog-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notice-item,
.todo-item,
.dialog-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  min-height: 44px;
  padding: 0 4px;
  border-bottom: 1px dashed #F0F0F0;
}

.clickable,
.todo-item,
.dialog-list-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.clickable:hover,
.todo-item:hover,
.dialog-list-item:hover {
  background: #F7F8FA;
  border-radius: 6px;
}

.notice-title,
.todo-label {
  font-size: 14px;
  color: #333;
}

.notice-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notice-date,
.dialog-time {
  font-size: 12px;
  color: #999;
  flex-shrink: 0;
}

.todo-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.todo-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #165DFF;
  flex-shrink: 0;
}

.todo-count {
  min-width: 26px;
  height: 22px;
  line-height: 22px;
  padding: 0 8px;
  border-radius: 999px;
  background: #EEF4FF;
  color: #165DFF;
  text-align: center;
  font-size: 12px;
  font-weight: 600;
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

.dialog-body {
  font-size: 14px;
  color: #344054;
  line-height: 1.7;
}

.dialog-tip {
  font-size: 12px;
  color: #98A2B3;
}

@media (max-width: 1200px) {
  .page-header,
  .header-right {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
