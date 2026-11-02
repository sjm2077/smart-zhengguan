<template>
  <div class="query-results-page">
    <div class="page-header">
      <div class="header-left">
        <span class="page-title">跨模块画像分析</span>
        <span class="page-subtitle">{{ description }}</span>
      </div>
      <div class="header-right">
        <span class="update-time">查询范围：{{ conditionText }}</span>
        <el-tag v-if="latestUpdatedAt" type="info" effect="plain">数据更新：{{ latestUpdatedAt }}</el-tag>
      </div>
    </div>

    <div v-if="loading" class="section-card loading-card">
      <el-skeleton :rows="6" animated />
    </div>

    <div v-else-if="!hasQuery" class="section-card empty-card">
      <el-empty description="请选择年级或专业后查看跨模块画像分析结果" />
    </div>

    <div v-else-if="singleProfileMode && !focusRow" class="section-card empty-card">
      <el-empty description="当前年级与专业组合暂无可展示的真实业务数据" />
    </div>

    <div v-else-if="!singleProfileMode && !comparisonRows.length" class="section-card empty-card">
      <el-empty description="当前筛选条件下暂无可比较的真实业务数据" />
    </div>

    <template v-else-if="singleProfileMode">
      <div class="stats-grid">
        <DashboardCard
          v-for="card in detailStatCards"
          :key="card.title"
          :title="card.title"
          :number="card.number"
          :icon="card.icon"
          :changeLabel="card.changeLabel"
        />
      </div>

      <div class="section-card focus-card">
        <div class="focus-header">
          <div>
            <div class="focus-eyebrow">当前对象</div>
            <div class="focus-title">{{ focusRow.grade }} · {{ focusRow.major }}</div>
            <div class="focus-subtitle">
              当前仅展示该年级该专业自身的奖助、就业、培养、学位和基础画像，不再做横向比较。
            </div>
          </div>
          <el-tag :type="focusRow.diagnosisType" effect="dark">{{ focusRow.diagnosisLabel }}</el-tag>
        </div>

        <div class="focus-metrics detail-metrics">
          <div class="focus-metric">
            <span class="metric-label">样本人数</span>
            <span class="metric-value">{{ focusRow.totalStudents }}人</span>
            <span class="metric-note">男{{ focusRow.maleCount }} / 女{{ focusRow.femaleCount }}</span>
          </div>
          <div class="focus-metric">
            <span class="metric-label">获奖率</span>
            <span class="metric-value">{{ formatRate(focusRow.awardRate) }}</span>
            <span class="metric-note">{{ focusRow.awardCount }}人有奖助记录</span>
          </div>
          <div class="focus-metric">
            <span class="metric-label">就业率</span>
            <span class="metric-value">{{ formatRate(focusRow.employmentRate) }}</span>
            <span class="metric-note">{{ focusRow.employedCount }}人已有去向</span>
          </div>
          <div class="focus-metric">
            <span class="metric-label">培养完成率</span>
            <span class="metric-value">{{ formatRate(focusRow.trainingCompletionRate) }}</span>
            <span class="metric-note">来自培养计划平均进度</span>
          </div>
          <div class="focus-metric">
            <span class="metric-label">学位进度</span>
            <span class="metric-value">{{ formatRate(focusRow.degreeProgressRate) }}</span>
            <span class="metric-note">来自学位申请与答辩记录</span>
          </div>
        </div>
      </div>

      <el-row :gutter="16" class="chart-row">
        <el-col :span="8">
          <ChartCard title="获奖情况分布" :chartOptions="detailAwardChartOptions" chartHeight="320px" />
        </el-col>
        <el-col :span="8">
          <ChartCard title="就业去向分布" :chartOptions="detailEmploymentChartOptions" chartHeight="320px" />
        </el-col>
        <el-col :span="8">
          <ChartCard title="男女比例" :chartOptions="detailGenderChartOptions" chartHeight="320px" />
        </el-col>
      </el-row>

      <div class="chart-row">
        <ChartCard title="核心指标画像" :chartOptions="detailProgressChartOptions" chartHeight="320px" />
      </div>

      <div class="section-card summary-card">
        <div class="summary-header">
          <span class="summary-title">对象结论</span>
          <el-tag type="primary" effect="plain">{{ focusRow.grade }} {{ focusRow.major }}</el-tag>
        </div>
        <div class="summary-tags">
          <el-tag effect="plain" type="info">综合评分：{{ focusRow.compositeScore }}分</el-tag>
          <el-tag effect="plain" type="success">平均薪资：{{ formatAmount(focusRow.averageSalary) }}</el-tag>
          <el-tag effect="plain" type="warning">升学深造率：{{ formatRate(focusRow.furtherStudyRate) }}</el-tag>
          <el-tag effect="plain" type="danger">未就业率：{{ formatRate(focusRow.unemploymentRate) }}</el-tag>
        </div>
        <div class="insight-list">
          <div v-for="(item, index) in singleProfileInsightMessages" :key="item" class="insight-item">
            <span class="insight-index">0{{ index + 1 }}</span>
            <span class="insight-text">{{ item }}</span>
          </div>
        </div>
      </div>

      <div class="module-list">
        <div v-for="module in detailModules" :key="module.key" class="section-card module-card">
          <div class="table-header">
            <div>
              <div class="table-title">{{ module.title }}</div>
              <div class="table-subtitle">{{ module.description }}</div>
            </div>
          </div>
          <el-table :data="module.rows" stripe class="result-table">
            <el-table-column prop="item" label="指标项" min-width="180" />
            <el-table-column prop="value" label="数值" min-width="120" />
            <el-table-column prop="rate" label="占比/进度" min-width="120" />
            <el-table-column prop="note" label="说明" min-width="240" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
    </template>

    <template v-else>
      <div class="stats-grid">
        <DashboardCard
          v-for="card in comparisonStatCards"
          :key="card.title"
          :title="card.title"
          :number="card.number"
          :icon="card.icon"
          :changeLabel="card.changeLabel"
        />
      </div>

      <el-row :gutter="16" class="chart-row">
        <el-col :span="16">
          <ChartCard :title="overviewChartTitle" :chartOptions="overviewChartOptions" chartHeight="360px" />
        </el-col>
        <el-col :span="8">
          <ChartCard :title="comparisonRadarChartTitle" :chartOptions="comparisonRadarChartOptions" chartHeight="360px" />
        </el-col>
      </el-row>

      <el-row :gutter="16" class="chart-row">
        <el-col :span="10">
          <ChartCard title="男女比例对比" :chartOptions="comparisonGenderChartOptions" chartHeight="360px" />
        </el-col>
        <el-col :span="14">
          <ChartCard title="获奖率与就业率分布" :chartOptions="comparisonScatterChartOptions" chartHeight="360px" />
        </el-col>
      </el-row>

      <div class="chart-row">
        <ChartCard :title="heatmapChartTitle" :chartOptions="heatmapChartOptions" chartHeight="360px" />
      </div>

      <div class="section-card summary-card">
        <div class="summary-header">
          <span class="summary-title">分析结论</span>
          <el-tag type="primary" effect="plain">{{ scopeSummaryText }}</el-tag>
        </div>
        <div class="summary-tags">
          <el-tag effect="plain" type="info">平均获奖率：{{ formatRate(summary.averageAwardRate) }}</el-tag>
          <el-tag effect="plain" type="success">平均就业率：{{ formatRate(summary.averageEmploymentRate) }}</el-tag>
          <el-tag effect="plain" type="warning">平均培养完成率：{{ formatRate(summary.averageTrainingRate) }}</el-tag>
          <el-tag effect="plain" type="danger">平均学位进度：{{ formatRate(summary.averageDegreeRate) }}</el-tag>
        </div>
        <div class="insight-list">
          <div v-for="(item, index) in comparisonInsightMessages" :key="item" class="insight-item">
            <span class="insight-index">0{{ index + 1 }}</span>
            <span class="insight-text">{{ item }}</span>
          </div>
        </div>
      </div>

      <div class="section-card table-card">
        <div class="table-header">
          <div>
            <div class="table-title">{{ scopeTitle }}画像明细</div>
            <div class="table-subtitle">
              只选年级时展示该年级全部专业，只选专业时展示该专业跨年级的真实业务画像。
            </div>
          </div>
          <el-tag type="info" effect="plain">最新更新：{{ latestUpdatedAt || '暂无' }}</el-tag>
        </div>

        <el-table :data="tableRows" stripe class="result-table">
          <el-table-column :label="comparisonColumnLabel" min-width="150">
            <template #default="scope">
              <div class="entity-cell">
                <span class="entity-name">{{ scope.row.displayName }}</span>
                <span class="table-note">{{ scope.row.grade }} · {{ scope.row.major }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="人数结构" min-width="160">
            <template #default="scope">
              <div class="table-metric">
                <span class="table-value">{{ scope.row.totalStudents }}人</span>
                <span class="table-note">男{{ scope.row.maleCount }} / 女{{ scope.row.femaleCount }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="男女比例" min-width="150">
            <template #default="scope">
              <div class="table-metric">
                <span class="table-value">男 {{ formatRate(scope.row.maleRatio) }}</span>
                <span class="table-note">女 {{ formatRate(scope.row.femaleRatio) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="获奖率" min-width="140">
            <template #default="scope">
              <div class="table-metric">
                <span class="table-value">{{ formatRate(scope.row.awardRate) }}</span>
                <span class="table-note">{{ scope.row.awardCount }}人有奖助记录</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="就业率" min-width="140">
            <template #default="scope">
              <div class="table-metric">
                <span class="table-value">{{ formatRate(scope.row.employmentRate) }}</span>
                <span class="table-note">{{ scope.row.employedCount }}人已有去向</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="培养完成率" min-width="140">
            <template #default="scope">
              <div class="table-metric">
                <span class="table-value">{{ formatRate(scope.row.trainingCompletionRate) }}</span>
                <span class="table-note">培养计划平均进度</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="学位进度" min-width="140">
            <template #default="scope">
              <div class="table-metric">
                <span class="table-value">{{ formatRate(scope.row.degreeProgressRate) }}</span>
                <span class="table-note">申请与答辩推进情况</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="结论" min-width="120">
            <template #default="scope">
              <el-tag :type="scope.row.diagnosisType">{{ scope.row.diagnosisLabel }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>
  </div>
</template>

<script>
import ChartCard from '../components/ChartCard.vue'
import DashboardCard from '../components/DashboardCard.vue'
import { getCrossModuleQueryData } from '../services/mockDataService'
import { hasQueryFilters, normalizeQueryFilters } from '../utils/queryData'

const OVERVIEW_SERIES = {
  awardRate: { label: '获奖率', color: '#2563EB', type: 'bar' },
  employmentRate: { label: '就业率', color: '#0F766E', type: 'bar' },
  trainingCompletionRate: { label: '培养完成率', color: '#F59E0B', type: 'line' },
  degreeProgressRate: { label: '学位进度', color: '#7C3AED', type: 'line' },
}

function createEmptyPageData(filters = { grade: '', major: '' }) {
  return {
    mode: 'empty',
    filters,
    description: '请选择年级或专业后查看跨模块画像分析结果',
    conditionText: filters.grade || filters.major ? `${filters.grade || '全部年级'} ${filters.major || '全部专业'}` : '全部年级 全部专业',
    focusRow: null,
    comparisonRows: [],
    summary: {
      entityCount: 0,
      totalStudents: 0,
      averageAwardRate: 0,
      averageEmploymentRate: 0,
      averageTrainingRate: 0,
      averageDegreeRate: 0,
      averageMaleRatio: 0,
    },
    detailModules: [],
    latestUpdatedAt: '',
  }
}

export default {
  name: 'QueryResults',
  components: { DashboardCard, ChartCard },
  data() {
    return {
      loading: false,
      pageData: createEmptyPageData(),
      requestToken: 0,
    }
  },
  computed: {
    filters() {
      return normalizeQueryFilters(this.$route.query)
    },
    hasQuery() {
      return hasQueryFilters(this.filters)
    },
    singleProfileMode() {
      return this.pageData.mode === 'single_profile'
    },
    focusRow() {
      return this.pageData.focusRow || null
    },
    comparisonRows() {
      return this.pageData.comparisonRows || []
    },
    tableRows() {
      return this.comparisonRows.map((row) => ({
        ...row,
        displayName: this.filters.grade ? row.major : row.grade,
      }))
    },
    summary() {
      return this.pageData.summary || createEmptyPageData().summary
    },
    description() {
      return this.pageData.description || '跨模块画像分析'
    },
    conditionText() {
      return this.pageData.conditionText || '全部年级 全部专业'
    },
    detailModules() {
      return this.pageData.detailModules || []
    },
    latestUpdatedAt() {
      return this.pageData.latestUpdatedAt || ''
    },
    detailModuleMap() {
      return this.detailModules.reduce((map, module) => {
        map[module.key] = module
        return map
      }, {})
    },
    detailStatCards() {
      if (!this.focusRow) return []

      return [
        {
          title: '样本总人数',
          number: String(this.focusRow.totalStudents),
          icon: 'user',
          changeLabel: `${this.focusRow.grade}${this.focusRow.major}在读规模`,
        },
        {
          title: '获奖率',
          number: this.formatRate(this.focusRow.awardRate),
          icon: 'medal',
          changeLabel: `${this.focusRow.awardCount} 人有奖助记录`,
        },
        {
          title: '就业率',
          number: this.formatRate(this.focusRow.employmentRate),
          icon: 'briefcase',
          changeLabel: `${this.focusRow.employedCount} 人已有去向`,
        },
        {
          title: '综合评分',
          number: `${this.focusRow.compositeScore}分`,
          icon: 'target',
          changeLabel: this.focusRow.diagnosisLabel,
        },
      ]
    },
    comparisonStatCards() {
      return [
        {
          title: `对比${this.comparisonColumnLabel}数`,
          number: String(this.summary.entityCount),
          icon: 'layers',
          changeLabel: `${this.scopeTitle}已形成横向比较样本`,
        },
        {
          title: '样本总人数',
          number: String(this.summary.totalStudents),
          icon: 'user',
          changeLabel: '当前画像覆盖总人数',
        },
        {
          title: '平均获奖率',
          number: this.formatRate(this.summary.averageAwardRate),
          icon: 'medal',
          changeLabel: `最高 ${this.formatRate(this.topAwardRow?.awardRate || 0)}`,
        },
        {
          title: '平均就业率',
          number: this.formatRate(this.summary.averageEmploymentRate),
          icon: 'briefcase',
          changeLabel: `最高 ${this.formatRate(this.topEmploymentRow?.employmentRate || 0)}`,
        },
      ]
    },
    comparisonColumnLabel() {
      return this.filters.grade ? '专业' : '年级'
    },
    scopeTitle() {
      if (this.filters.grade) return this.filters.grade
      if (this.filters.major) return this.filters.major
      return '当前查询'
    },
    scopeSummaryText() {
      return `${this.scopeTitle}共覆盖 ${this.comparisonRows.length} 个${this.comparisonColumnLabel}，总样本 ${this.summary.totalStudents} 人`
    },
    overviewChartTitle() {
      return `${this.scopeTitle}${this.filters.grade ? '各专业' : '各年级'}核心指标对比`
    },
    comparisonRadarChartTitle() {
      return `${this.bestCompositeRow?.displayName || '当前对象'}与组均值对比`
    },
    heatmapChartTitle() {
      return `${this.scopeTitle}${this.filters.grade ? '专业' : '年级'}画像热力图`
    },
    topEmploymentRow() {
      return this.comparisonRows.reduce((best, row) => (
        !best || row.employmentRate > best.employmentRate ? row : best
      ), null)
    },
    bottomEmploymentRow() {
      return this.comparisonRows.reduce((worst, row) => (
        !worst || row.employmentRate < worst.employmentRate ? row : worst
      ), null)
    },
    topAwardRow() {
      return this.comparisonRows.reduce((best, row) => (
        !best || row.awardRate > best.awardRate ? row : best
      ), null)
    },
    bottomAwardRow() {
      return this.comparisonRows.reduce((worst, row) => (
        !worst || row.awardRate < worst.awardRate ? row : worst
      ), null)
    },
    bestCompositeRow() {
      return this.tableRows[0] || null
    },
    mostBalancedRow() {
      return this.comparisonRows.reduce((best, row) => {
        if (!best) return row
        const bestGap = Math.abs(best.maleRatio - 50)
        const currentGap = Math.abs(row.maleRatio - 50)
        return currentGap < bestGap ? row : best
      }, null)
    },
    lowPerformingRows() {
      return this.comparisonRows.filter((row) => (
        row.awardRate < this.summary.averageAwardRate &&
        row.trainingCompletionRate < this.summary.averageTrainingRate
      ))
    },
    singleProfileInsightMessages() {
      if (!this.focusRow) return []

      const scholarshipRows = this.nonEmptyRows(this.detailModuleMap.scholarship?.rows)
      const employmentRows = this.nonEmptyRows(this.detailModuleMap.employment?.rows)
      const trainingRows = this.nonEmptyRows(this.detailModuleMap.training?.rows)
      const degreeRows = this.nonEmptyRows(this.detailModuleMap.degree?.rows)

      const topScholarship = this.getRowWithMaxCount(scholarshipRows)
      const topEmployment = this.getRowWithMaxCount(employmentRows)
      const topTrainingStage = this.getRowWithMaxCount(trainingRows)
      const topDegreeItem = this.getRowWithMaxCount(degreeRows)

      const messages = [
        `${this.focusRow.grade}${this.focusRow.major}当前共纳入 ${this.focusRow.totalStudents} 人，男生 ${this.focusRow.maleCount} 人、女生 ${this.focusRow.femaleCount} 人，男女比例为 ${this.focusRow.genderRatioText}。`,
        `奖助覆盖率为 ${this.formatRate(this.focusRow.awardRate)}，${topScholarship ? `覆盖人数最多的是“${topScholarship.item}”，对应 ${topScholarship.value}。` : '当前未发现可用的奖助细分记录。'}`,
        `就业落实率为 ${this.formatRate(this.focusRow.employmentRate)}，${topEmployment ? `去向分布中人数最多的是“${topEmployment.item}”，对应 ${topEmployment.value}。` : '当前未发现可用的就业去向记录。'}`,
        `培养完成率 ${this.formatRate(this.focusRow.trainingCompletionRate)}、学位进度 ${this.formatRate(this.focusRow.degreeProgressRate)}，${topTrainingStage ? `当前培养记录主要集中在“${topTrainingStage.item}”。` : ''}${topDegreeItem ? `学位模块中“${topDegreeItem.item}”记录最多。` : ''}综合判断为“${this.focusRow.diagnosisLabel}”。`,
      ]

      return messages
    },
    comparisonInsightMessages() {
      const messages = []

      messages.push(
        `${this.scopeTitle}本次共覆盖 ${this.comparisonRows.length} 个${this.comparisonColumnLabel}、${this.summary.totalStudents} 名学生，平均获奖率 ${this.formatRate(this.summary.averageAwardRate)}，平均就业率 ${this.formatRate(this.summary.averageEmploymentRate)}。`,
      )

      if (this.topEmploymentRow && this.bottomEmploymentRow) {
        messages.push(
          `就业表现最好的是 ${this.getComparisonLabel(this.topEmploymentRow)}，就业率 ${this.formatRate(this.topEmploymentRow.employmentRate)}；最低的是 ${this.getComparisonLabel(this.bottomEmploymentRow)}，就业率 ${this.formatRate(this.bottomEmploymentRow.employmentRate)}，相差 ${this.formatPointDiff(this.topEmploymentRow.employmentRate - this.bottomEmploymentRow.employmentRate)}。`,
        )
      }

      if (this.topAwardRow && this.bottomAwardRow) {
        messages.push(
          `奖助覆盖最高的是 ${this.getComparisonLabel(this.topAwardRow)}，获奖率 ${this.formatRate(this.topAwardRow.awardRate)}；最低的是 ${this.getComparisonLabel(this.bottomAwardRow)}，获奖率 ${this.formatRate(this.bottomAwardRow.awardRate)}。`,
        )
      }

      if (this.lowPerformingRows.length) {
        messages.push(
          `需要优先补短板的是 ${this.lowPerformingRows.map((row) => this.getComparisonLabel(row)).join('、')}，这些对象的获奖率和培养完成率同时低于当前组均值。`,
        )
      } else if (this.mostBalancedRow) {
        messages.push(
          `性别结构最均衡的是 ${this.getComparisonLabel(this.mostBalancedRow)}，男生占比 ${this.formatRate(this.mostBalancedRow.maleRatio)}、女生占比 ${this.formatRate(this.mostBalancedRow.femaleRatio)}。`,
        )
      }

      return messages.slice(0, 4)
    },
    detailAwardChartOptions() {
      return this.buildModulePieChart(
        this.detailModuleMap.scholarship,
        ['#0A2463', '#2563EB', '#60A5FA', '#93C5FD', '#CBD5E1'],
      )
    },
    detailEmploymentChartOptions() {
      return this.buildModulePieChart(
        this.detailModuleMap.employment,
        ['#0F766E', '#14B8A6', '#22C55E', '#F59E0B', '#DC2626', '#94A3B8'],
      )
    },
    detailGenderChartOptions() {
      if (!this.focusRow) return {}

      return {
        tooltip: { trigger: 'item', formatter: '{b}：{c}人 ({d}%)' },
        legend: { bottom: 0, textStyle: { color: '#667085', fontSize: 12 } },
        series: [{
          type: 'pie',
          radius: ['42%', '70%'],
          center: ['50%', '42%'],
          itemStyle: { borderColor: '#fff', borderWidth: 3 },
          data: [
            { name: '男生', value: this.focusRow.maleCount, itemStyle: { color: '#2563EB' } },
            { name: '女生', value: this.focusRow.femaleCount, itemStyle: { color: '#F97316' } },
          ],
        }],
      }
    },
    detailProgressChartOptions() {
      if (!this.focusRow) return {}

      return {
        grid: { left: '4%', right: '6%', bottom: '4%', top: '12px', containLabel: true },
        xAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: { color: '#667085', formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#E4E7EC', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'category',
          data: ['获奖率', '就业率', '培养完成率', '学位进度', '升学深造率'],
          axisLabel: { color: '#667085' },
          axisLine: { lineStyle: { color: '#E4E7EC' } },
          axisTick: { show: false },
        },
        series: [{
          type: 'bar',
          barWidth: 20,
          data: [
            { value: this.focusRow.awardRate, itemStyle: { color: '#2563EB' } },
            { value: this.focusRow.employmentRate, itemStyle: { color: '#0F766E' } },
            { value: this.focusRow.trainingCompletionRate, itemStyle: { color: '#F59E0B' } },
            { value: this.focusRow.degreeProgressRate, itemStyle: { color: '#7C3AED' } },
            { value: this.focusRow.furtherStudyRate, itemStyle: { color: '#14B8A6' } },
          ],
          label: { show: true, position: 'right', color: '#344054', formatter: '{c}%' },
        }],
      }
    },
    overviewChartOptions() {
      const categories = this.tableRows.map((row) => row.displayName)

      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: (params) => {
            const title = params[0]?.axisValue || ''
            const lines = params.map((item) => `${item.marker}${item.seriesName}：${item.value}%`)
            return [title, ...lines].join('<br/>')
          },
        },
        legend: { top: 0, textStyle: { color: '#667085', fontSize: 12 } },
        grid: { left: '4%', right: '4%', bottom: '8%', top: '44px', containLabel: true },
        xAxis: {
          type: 'category',
          data: categories,
          axisLabel: { color: '#667085', interval: 0, rotate: categories.length > 5 ? 18 : 0 },
          axisLine: { lineStyle: { color: '#E4E7EC' } },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: { color: '#667085', formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#E4E7EC', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        series: Object.entries(OVERVIEW_SERIES).map(([field, meta]) => ({
          name: meta.label,
          type: meta.type,
          smooth: meta.type === 'line',
          barMaxWidth: meta.type === 'bar' ? 26 : undefined,
          symbol: meta.type === 'line' ? 'circle' : undefined,
          symbolSize: meta.type === 'line' ? 9 : undefined,
          data: this.tableRows.map((row) => ({
            value: row[field],
            itemStyle: { color: meta.color },
          })),
        })),
      }
    },
    comparisonRadarChartOptions() {
      const target = this.bestCompositeRow
      if (!target) return {}

      return {
        tooltip: { trigger: 'item' },
        legend: { bottom: 0, textStyle: { color: '#667085', fontSize: 12 } },
        radar: {
          center: ['50%', '46%'],
          radius: '62%',
          splitNumber: 4,
          axisName: { color: '#344054', fontSize: 12 },
          splitLine: { lineStyle: { color: '#E4E7EC' } },
          splitArea: { areaStyle: { color: ['#F8FAFC', '#FFFFFF'] } },
          indicator: [
            { name: '获奖', max: 100 },
            { name: '就业', max: 100 },
            { name: '培养', max: 100 },
            { name: '学位', max: 100 },
            { name: '性别均衡', max: 100 },
          ],
        },
        series: [{
          type: 'radar',
          data: [
            {
              name: target.displayName,
              value: [
                target.awardRate,
                target.employmentRate,
                target.trainingCompletionRate,
                target.degreeProgressRate,
                target.genderBalanceScore,
              ],
              itemStyle: { color: '#0A2463' },
              areaStyle: { color: 'rgba(10, 36, 99, 0.18)' },
              lineStyle: { color: '#0A2463', width: 2 },
            },
            {
              name: '组均值',
              value: [
                this.summary.averageAwardRate,
                this.summary.averageEmploymentRate,
                this.summary.averageTrainingRate,
                this.summary.averageDegreeRate,
                100 - Math.abs(this.summary.averageMaleRatio - 50) * 2,
              ],
              itemStyle: { color: '#98A2B3' },
              areaStyle: { color: 'rgba(152, 162, 179, 0.16)' },
              lineStyle: { color: '#98A2B3', width: 2 },
            },
          ],
        }],
      }
    },
    comparisonGenderChartOptions() {
      const categories = this.tableRows.map((row) => row.displayName)

      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: (params) => {
            const title = params[0]?.axisValue || ''
            const lines = params.map((item) => `${item.marker}${item.seriesName}：${item.value}%`)
            return [title, ...lines].join('<br/>')
          },
        },
        legend: { top: 0, textStyle: { color: '#667085', fontSize: 12 } },
        grid: { left: '4%', right: '4%', bottom: '4%', top: '44px', containLabel: true },
        xAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: { color: '#667085', formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#E4E7EC', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'category',
          data: categories,
          axisLabel: { color: '#667085' },
          axisLine: { lineStyle: { color: '#E4E7EC' } },
          axisTick: { show: false },
        },
        series: [
          {
            name: '男生占比',
            type: 'bar',
            stack: 'gender',
            barWidth: 20,
            itemStyle: { color: '#2563EB' },
            data: this.tableRows.map((row) => row.maleRatio),
          },
          {
            name: '女生占比',
            type: 'bar',
            stack: 'gender',
            barWidth: 20,
            itemStyle: { color: '#F97316' },
            data: this.tableRows.map((row) => row.femaleRatio),
          },
        ],
      }
    },
    comparisonScatterChartOptions() {
      return {
        tooltip: {
          formatter: ({ data: item }) => {
            const [employmentRate, awardRate, totalStudents, trainingRate, degreeRate] = item.value
            return [
              item.name,
              `就业率：${employmentRate}%`,
              `获奖率：${awardRate}%`,
              `培养完成率：${trainingRate}%`,
              `学位进度：${degreeRate}%`,
              `样本人数：${totalStudents}人`,
            ].join('<br/>')
          },
        },
        grid: { left: '6%', right: '6%', bottom: '8%', top: '12px', containLabel: true },
        xAxis: {
          type: 'value',
          min: 0,
          max: 100,
          name: '就业率',
          nameTextStyle: { color: '#667085' },
          axisLabel: { color: '#667085', formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#E4E7EC', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          name: '获奖率',
          nameTextStyle: { color: '#667085' },
          axisLabel: { color: '#667085', formatter: '{value}%' },
          splitLine: { lineStyle: { color: '#E4E7EC', type: 'dashed' } },
          axisLine: { show: false },
          axisTick: { show: false },
        },
        series: [{
          type: 'scatter',
          data: this.tableRows.map((row) => ({
            name: row.displayName,
            value: [
              row.employmentRate,
              row.awardRate,
              row.totalStudents,
              row.trainingCompletionRate,
              row.degreeProgressRate,
            ],
            symbolSize: Math.min(46, 18 + row.totalStudents * 0.35),
            label: {
              show: row.id === this.bestCompositeRow?.id,
              formatter: row.displayName,
              color: '#344054',
              fontSize: 11,
              position: 'top',
            },
            itemStyle: {
              color: this.getScatterColor(row.trainingCompletionRate),
              opacity: 0.9,
              borderColor: '#FFFFFF',
              borderWidth: 1,
            },
          })),
        }],
      }
    },
    heatmapChartOptions() {
      const metrics = ['获奖率', '就业率', '培养完成率', '学位进度', '男生占比']
      const values = this.tableRows.flatMap((row, rowIndex) => ([
        [0, rowIndex, row.awardRate],
        [1, rowIndex, row.employmentRate],
        [2, rowIndex, row.trainingCompletionRate],
        [3, rowIndex, row.degreeProgressRate],
        [4, rowIndex, row.maleRatio],
      ]))

      return {
        tooltip: {
          formatter: ({ value }) => {
            const [metricIndex, rowIndex, score] = value
            return `${this.tableRows[rowIndex].displayName}<br/>${metrics[metricIndex]}：${score}%`
          },
        },
        grid: { left: '4%', right: '10%', bottom: '8%', top: '12px', containLabel: true },
        xAxis: {
          type: 'category',
          data: metrics,
          axisLabel: { color: '#667085' },
          axisLine: { lineStyle: { color: '#E4E7EC' } },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'category',
          data: this.tableRows.map((row) => row.displayName),
          axisLabel: { color: '#667085' },
          axisLine: { lineStyle: { color: '#E4E7EC' } },
          axisTick: { show: false },
        },
        visualMap: {
          min: 0,
          max: 100,
          orient: 'vertical',
          right: 0,
          top: 'center',
          text: ['高', '低'],
          textStyle: { color: '#667085' },
          inRange: { color: ['#FDE68A', '#F59E0B', '#60A5FA', '#1D4ED8'] },
        },
        series: [{
          type: 'heatmap',
          data: values,
          label: { show: true, color: '#FFFFFF', formatter: ({ value }) => `${value[2]}%` },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.2)' } },
        }],
      }
    },
  },
  watch: {
    '$route.query': {
      immediate: true,
      deep: true,
      handler() {
        this.fetchPageData()
      },
    },
  },
  methods: {
    async fetchPageData() {
      const filters = normalizeQueryFilters(this.$route.query)
      const token = ++this.requestToken

      if (!hasQueryFilters(filters)) {
        this.pageData = createEmptyPageData(filters)
        return
      }

      this.loading = true
      try {
        const response = await getCrossModuleQueryData(filters)
        if (token !== this.requestToken) return
        this.pageData = {
          ...createEmptyPageData(filters),
          ...response,
        }
      } finally {
        if (token === this.requestToken) {
          this.loading = false
        }
      }
    },
    formatRate(value) {
      return `${Number(value || 0).toFixed(1).replace(/\.0$/, '')}%`
    },
    formatAmount(value) {
      if (value === null || value === undefined || value === '') return '暂无'
      return `${Number(value).toFixed(1).replace(/\.0$/, '')}万元`
    },
    formatPointDiff(value) {
      return `${Math.abs(Number(value || 0)).toFixed(1).replace(/\.0$/, '')} 个百分点`
    },
    getComparisonLabel(row) {
      return this.filters.grade ? row.major : row.grade
    },
    getScatterColor(trainingRate) {
      if (trainingRate >= 88) return '#0A2463'
      if (trainingRate >= 78) return '#2563EB'
      if (trainingRate >= 68) return '#F59E0B'
      return '#DC2626'
    },
    parseCount(text) {
      const match = String(text || '').match(/-?\d+(\.\d+)?/)
      return match ? Number(match[0]) : 0
    },
    nonEmptyRows(rows = []) {
      return rows.filter((row) => row && row.value && row.value !== '-')
    },
    getRowWithMaxCount(rows = []) {
      return rows.reduce((best, row) => (
        !best || this.parseCount(row.value) > this.parseCount(best.value) ? row : best
      ), null)
    },
    buildModulePieChart(module, colors) {
      const rows = this.nonEmptyRows(module?.rows || [])
      if (!rows.length) return {}

      return {
        tooltip: { trigger: 'item', formatter: '{b}：{c} ({d}%)' },
        legend: { bottom: 0, textStyle: { color: '#667085', fontSize: 12 } },
        series: [{
          type: 'pie',
          radius: ['42%', '70%'],
          center: ['50%', '42%'],
          itemStyle: { borderColor: '#fff', borderWidth: 3 },
          data: rows.map((row, index) => ({
            name: row.item,
            value: this.parseCount(row.value),
            itemStyle: { color: colors[index % colors.length] },
          })),
        }],
      }
    },
  },
}
</script>

<style scoped>
.query-results-page {
  color: #333;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  background: #fff;
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.page-subtitle,
.update-time {
  font-size: 13px;
  color: #86909c;
}

.empty-card,
.loading-card {
  padding: 24px;
}

.section-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.focus-card {
  background: linear-gradient(135deg, #f8fbff 0%, #ffffff 100%);
  border: 1px solid #d9e8ff;
}

.focus-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.focus-eyebrow {
  font-size: 12px;
  color: #165dff;
  font-weight: 600;
  letter-spacing: 0.04em;
}

.focus-title {
  margin-top: 8px;
  font-size: 22px;
  font-weight: 700;
  color: #1d2939;
}

.focus-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #667085;
}

.focus-metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.detail-metrics {
  grid-template-columns: repeat(5, minmax(0, 1fr));
}

.focus-metric {
  background: #fff;
  border: 1px solid #e4e7ec;
  border-radius: 12px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-label {
  font-size: 12px;
  color: #667085;
}

.metric-value {
  font-size: 20px;
  font-weight: 700;
  color: #101828;
}

.metric-note {
  font-size: 12px;
  color: #667085;
}

.chart-row {
  margin-bottom: 16px;
}

.summary-header,
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.summary-title,
.table-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.table-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #667085;
  line-height: 1.6;
}

.summary-tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.insight-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.insight-item {
  display: flex;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f8faff 0%, #ffffff 100%);
  border: 1px solid #e7eeff;
}

.insight-index {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: #0a2463;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.insight-text {
  font-size: 13px;
  line-height: 1.7;
  color: #344054;
}

.module-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.module-card {
  margin-bottom: 0;
}

.table-header {
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.entity-cell,
.table-metric {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.entity-name,
.table-value {
  font-size: 14px;
  font-weight: 600;
  color: #101828;
}

.table-note {
  font-size: 12px;
  color: #667085;
}

.result-table :deep(.el-table__header th) {
  background: #f8f9fa;
  color: #333;
  font-weight: 500;
}

@media (max-width: 1400px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .focus-metrics,
  .detail-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1100px) {
  .page-header,
  .summary-header,
  .table-header,
  .focus-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .insight-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid,
  .focus-metrics,
  .detail-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
