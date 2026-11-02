<template>
  <div class="employment-page">
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

    <div class="content-wrapper">
      <div class="left-col">
        <div class="section-card trend-section">
          <div class="section-card-header">
            <span class="section-card-title">2020-2024年学院核心指标趋势</span>
            <div class="metric-toggles">
              <el-button
                v-for="m in metrics"
                :key="m.key"
                :type="activeMetric === m.key ? 'primary' : ''"
                size="small"
                :class="{ 'metric-btn-active': activeMetric === m.key }"
                @click="switchMetric(m.key)"
              >{{ m.label }}</el-button>
            </div>
          </div>
          <div ref="trendChartRef" class="chart-box" style="height:340px"></div>
        </div>

        <div class="dist-grid">
          <div class="section-card dist-card">
            <div class="section-card-header">
              <span class="section-card-title">单位性质分布</span>
            </div>
            <div ref="unitNatureChartRef" class="chart-box" style="height:280px"></div>
          </div>
          <div class="section-card dist-card">
            <div class="section-card-header">
              <span class="section-card-title">行业分布 TOP10</span>
            </div>
            <div ref="industryChartRef" class="chart-box" style="height:280px"></div>
          </div>
        </div>
      </div>

      <div class="right-col">
        <div class="section-card dest-section">
          <div class="section-card-header">
            <span class="section-card-title">学院就业去向统计</span>
          </div>
          <div ref="destDonutRef" class="chart-box" style="height:200px"></div>
          <el-table :data="employmentStats" stripe size="small" class="dest-table" :header-cell-style="tableHeaderStyle">
            <el-table-column prop="type" label="去向类型" />
            <el-table-column prop="count" label="人数" width="70" align="right" />
            <el-table-column prop="percent" label="占比" width="70" align="right" />
          </el-table>
        </div>

        <div class="section-card info-section">
          <div class="section-card-header">
            <span class="section-card-title">学院就业信息统计</span>
          </div>
          <el-table
            :data="sortedInfoStats"
            stripe
            size="small"
            class="info-table"
            :header-cell-style="tableHeaderStyle"
            :default-sort="{ prop: 'valueNum', order: 'descending' }"
            @sort-change="onSortChange"
          >
            <el-table-column prop="label" label="指标" sortable="custom" />
            <el-table-column prop="value" label="数值" width="100" align="right" sortable="custom" />
          </el-table>
        </div>
      </div>
    </div>

    <div class="section-card region-full-card">
      <div class="section-card-header">
        <span class="section-card-title">就业地区分布</span>
        <el-select v-model="selectedProvince" size="small" class="province-select" placeholder="选择省份" clearable @change="onProvinceChange">
          <el-option v-for="p in topProvinces" :key="p.name" :label="p.name" :value="p.name" />
        </el-select>
      </div>
      <div ref="regionChartRef" class="chart-box" style="height:360px"></div>
    </div>
  </div>
</template>

<script>
import DashboardCard from '../components/DashboardCard.vue'
import * as echarts from 'echarts'
import { getEmploymentData } from '../services/mockDataService'

const LOCAL_CHINA_MAP_URL = '/maps-china-100000.json'
const REMOTE_CHINA_MAP_URL = 'https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json'
const NON_MAP_REGION_NAMES = new Set(['其他', '境外', '海外', '待更新', '未知'])

const C = {
  primary: '#165DFF',
  green: '#13C2C2',
  red: '#F53F3F',
  orange: '#FA8C16',
  purple: '#722ED1',
  blue: '#4080FF',
  gray: '#98A2B3',
}

const CARD_META = [
  { icon: 'trend', iconBg: '#ECFEFB' },
  { icon: 'check-circle', iconBg: '#EEFDF3' },
  { icon: 'target', iconBg: '#F5F3FF' },
  { icon: 'alert-circle', iconBg: '#FFF7E8' },
]

const EMPTY_PAGE_DATA = {
  statCards: [],
  metrics: [],
  charts: {
    unitNature: [],
    industryTop: [],
    destinationStats: [],
    infoStats: [],
    provinceDistribution: [],
  },
}

export default {
  components: { DashboardCard },
  data() {
    return {
      pageData: EMPTY_PAGE_DATA,
      selectedProvince: '',
      activeMetric: 'employment',
      sortProp: null,
      sortOrder: null,
      mapLoaded: false,
      trendChart: null,
      unitNatureChart: null,
      industryChart: null,
      regionChart: null,
      destDonutChart: null,
    }
  },
  computed: {
    metrics() {
      return this.pageData.metrics || []
    },
    metricMap() {
      return this.metrics.reduce((result, item) => {
        result[item.key] = item
        return result
      }, {})
    },
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
    employmentStats() {
      return this.pageData.charts?.destinationStats || []
    },
    infoStats() {
      return this.pageData.charts?.infoStats || []
    },
    provinceDistribution() {
      return this.pageData.charts?.provinceDistribution || []
    },
    topProvinces() {
      return [...this.provinceDistribution].sort((left, right) => right.value - left.value).slice(0, 5)
    },
    sortedInfoStats() {
      const data = [...this.infoStats]
      if (!this.sortProp) return data
      data.sort((left, right) => {
        const leftValue = this.sortProp === 'label' ? left.label : left.valueNum
        const rightValue = this.sortProp === 'label' ? right.label : right.valueNum
        const direction = this.sortOrder === 'ascending' ? 1 : -1
        if (leftValue === rightValue) return 0
        return (leftValue > rightValue ? 1 : -1) * direction
      })
      return data
    },
  },
  async mounted() {
    await this.loadPageData()
    this.$nextTick(() => {
      this.initTrendChart()
      this.initUnitNatureChart()
      this.initIndustryChart()
      this.initDestDonutChart()
      this.loadChinaMap()
    })
  },
  beforeUnmount() {
    this.disposeAllCharts()
  },
  methods: {
    formatCardNumber(value, unit = '') {
      if (typeof value !== 'number') return value
      const display = Number.isInteger(value) ? value.toLocaleString('zh-CN') : value.toFixed(1)
      return `${display}${unit || ''}`
    },
    async loadPageData() {
      const data = await getEmploymentData()
      this.pageData = data
      if (!this.metricMap[this.activeMetric]) {
        this.activeMetric = data.metrics?.[0]?.key || 'employment'
      }
    },
    initTrendChart() {
      const el = this.$refs.trendChartRef
      if (!el) return
      if (!this.trendChart) this.trendChart = echarts.init(el)
      this.updateTrendChart()
    },
    updateTrendChart() {
      if (!this.trendChart) return
      const data = this.metricMap[this.activeMetric]
      if (!data) return
      this.trendChart.setOption({
        tooltip: { trigger: 'axis', formatter: `{b}年<br/>${data.label}：{c}${data.unit}` },
        grid: { left: '4%', right: '5%', bottom: '3%', top: '30px', containLabel: true },
        xAxis: {
          type: 'category',
          data: data.series.map((item) => item.year),
          axisLabel: { color: '#86909C', fontSize: 12 },
          axisLine: { lineStyle: { color: '#E5E7EB' } },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          min: data.key === 'furtherStudy' ? 0 : 60,
          max: data.key === 'furtherStudy' ? 15 : 95,
          axisLabel: { color: '#86909C', fontSize: 12, formatter: `{value}${data.unit}` },
          splitLine: { lineStyle: { color: '#E5E7EB', type: 'dashed' } },
        },
        series: [{
          type: 'line',
          data: data.series.map((item) => item.value),
          lineStyle: { color: C.primary, width: 3 },
          itemStyle: { color: C.primary, borderColor: '#fff', borderWidth: 2 },
          areaStyle: { color: `${C.primary}12` },
          symbol: 'circle',
          symbolSize: 10,
          smooth: true,
          label: { show: true, color: '#333', fontSize: 12, formatter: `{c}${data.unit}`, position: 'top', distance: 10 },
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { color: C.red, type: 'dashed', width: 2 },
            label: { color: C.red, fontSize: 12, formatter: data.key === 'furtherStudy' ? '目标值 12%' : '目标值 85%', position: 'end' },
            data: [{ yAxis: data.key === 'furtherStudy' ? 12 : 85 }],
          },
        }],
      }, true)
    },
    switchMetric(key) {
      this.activeMetric = key
      this.updateTrendChart()
    },
    initUnitNatureChart() {
      const el = this.$refs.unitNatureChartRef
      if (!el) return
      if (!this.unitNatureChart) this.unitNatureChart = echarts.init(el)
      const data = [...(this.pageData.charts?.unitNature || [])].sort((left, right) => right.value - left.value)
      this.unitNatureChart.setOption({
        tooltip: { trigger: 'axis', formatter: '{b}：{c}%' },
        grid: { left: '3%', right: '12%', bottom: '3%', top: '5px', containLabel: true },
        xAxis: { type: 'value', axisLabel: { color: '#86909C', fontSize: 11, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#E5E7EB', type: 'dashed' } } },
        yAxis: { type: 'category', inverse: true, data: data.map((item) => item.name), axisLabel: { color: '#333', fontSize: 12 }, axisLine: { lineStyle: { color: '#E5E7EB' } } },
        series: [{
          type: 'bar',
          barWidth: '50%',
          label: { show: true, position: 'right', color: '#333', fontSize: 11, formatter: '{c}%' },
          data: data.map((item) => ({
            value: item.value,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: C.primary },
                { offset: 1, color: `${C.primary}88` },
              ]),
              borderRadius: [0, 0, 0, 0],
            },
          })),
        }],
      })
    },
    initIndustryChart() {
      const el = this.$refs.industryChartRef
      if (!el) return
      if (!this.industryChart) this.industryChart = echarts.init(el)
      const data = [...(this.pageData.charts?.industryTop || [])].sort((left, right) => right.value - left.value)
      this.industryChart.setOption({
        tooltip: { trigger: 'axis', formatter: '{b}：{c}%' },
        grid: { left: '3%', right: '12%', bottom: '3%', top: '5px', containLabel: true },
        xAxis: { type: 'value', axisLabel: { color: '#86909C', fontSize: 11, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#E5E7EB', type: 'dashed' } } },
        yAxis: { type: 'category', inverse: true, data: data.map((item) => item.name), axisLabel: { color: '#333', fontSize: 12 }, axisLine: { lineStyle: { color: '#E5E7EB' } } },
        series: [{
          type: 'bar',
          barWidth: '50%',
          label: { show: true, position: 'right', color: '#333', fontSize: 11, formatter: '{c}%' },
          data: data.map((item) => ({
            value: item.value,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: C.blue },
                { offset: 1, color: `${C.blue}88` },
              ]),
              borderRadius: [0, 0, 0, 0],
            },
          })),
        }],
      })
    },
    initDestDonutChart() {
      const el = this.$refs.destDonutRef
      if (!el) return
      if (!this.destDonutChart) this.destDonutChart = echarts.init(el)
      const colors = [C.primary, C.green, C.purple, C.orange, C.gray]
      this.destDonutChart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}：{c}人（{d}%）' },
        legend: { orient: 'vertical', right: 5, top: 'center', textStyle: { color: '#666', fontSize: 11 }, itemWidth: 8, itemHeight: 8 },
        series: [{
          type: 'pie',
          radius: ['50%', '72%'],
          center: ['40%', '50%'],
          itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 0 },
          label: { show: false },
          data: this.employmentStats.map((item, index) => ({
            value: item.count,
            name: item.type,
            itemStyle: { color: colors[index] || C.primary },
          })),
        }],
      })
    },
    async loadChinaMap() {
      if (this.mapLoaded) {
        this.initRegionChart()
        return
      }
      try {
        const geoJson = await this.fetchChinaMapJson()
        echarts.registerMap('china', geoJson)
        this.mapLoaded = true
        this.initRegionChart()
      } catch (error) {
        console.warn('地图加载失败', error)
        this.initRegionChartFallback()
      }
    },
    initRegionChart() {
      const el = this.$refs.regionChartRef
      if (!el) return
      if (!this.regionChart) this.regionChart = echarts.init(el)
      if (!this.mapLoaded) {
        this.initRegionChartFallback()
        return
      }

      const allData = this.normalizeMapRegionData(this.provinceDistribution)
      const top5 = this.normalizeMapRegionData(this.topProvinces).map((item) => ({
        ...item,
        label: { show: true, color: '#333', fontSize: 11, formatter: '{b}\n{c}人' },
      }))
      const otherData = allData.filter((item) => !this.topProvinces.some((top) => top.name === item.name))
      const maxValue = Math.max(...allData.map((item) => item.value), 0)

      this.regionChart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}<br/>就业人数：{c}人' },
        visualMap: {
          min: 0,
          max: maxValue || 620,
          left: 10,
          bottom: 10,
          text: ['高', '低'],
          textStyle: { color: '#86909C', fontSize: 11 },
          inRange: { color: ['#E8F0FE', '#BBDEFB', '#69B1FF', '#1565C0', C.primary] },
          calculable: true,
        },
        series: [{
          type: 'map',
          map: 'china',
          roam: false,
          label: { show: false },
          emphasis: { label: { show: true, color: '#333' }, itemStyle: { areaColor: '#FFE082' } },
          data: [
            ...top5.map((item) => ({ name: item.name, value: item.value })),
            ...otherData,
          ],
        }],
      }, true)
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
    initRegionChartFallback() {
      const el = this.$refs.regionChartRef
      if (!el) return
      if (!this.regionChart) this.regionChart = echarts.init(el)
      const data = [...this.topProvinces].sort((left, right) => right.value - left.value)
      this.regionChart.setOption({
        tooltip: { trigger: 'axis', formatter: '{b}：{c}人' },
        grid: { left: '3%', right: '12%', bottom: '3%', top: '5px', containLabel: true },
        xAxis: { type: 'value', axisLabel: { color: '#86909C', fontSize: 11 }, splitLine: { lineStyle: { color: '#E5E7EB', type: 'dashed' } } },
        yAxis: { type: 'category', inverse: true, data: data.map((item) => item.name), axisLabel: { color: '#333', fontSize: 12 } },
        series: [{
          type: 'bar',
          barWidth: '50%',
          label: { show: true, position: 'right', color: '#333', fontSize: 11, formatter: '{c}人' },
          data: data.map((item) => ({
            value: item.value,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: C.primary },
                { offset: 1, color: `${C.primary}88` },
              ]),
              borderRadius: [0, 0, 0, 0],
            },
          })),
        }],
      }, true)
    },
    onProvinceChange(value) {
      if (!value) {
        this.initRegionChart()
        return
      }
      if (this.$message) this.$message.info(`已选择省份：${value}`)
    },
    onSortChange({ prop, order }) {
      this.sortProp = prop
      this.sortOrder = order
    },
    tableHeaderStyle() {
      return { background: '#F8FAFC', color: '#344054', fontWeight: 600, fontSize: '13px' }
    },
    disposeAllCharts() {
      const charts = ['trendChart', 'unitNatureChart', 'industryChart', 'regionChart', 'destDonutChart']
      charts.forEach((key) => {
        if (this[key]) {
          this[key].dispose()
          this[key] = null
        }
      })
    },
  },
}
</script>

<style scoped>
:root {
  --primary: #003366;
  --green: #009E5F;
  --red: #E53935;
  --orange: #FB8C00;
  --purple: #8E24AA;
}

.employment-page { color: #333; }

.stat-row { margin-bottom: 24px; }

.content-wrapper {
  display: flex;
  gap: 24px;
}
.left-col { flex: 0 0 68%; min-width: 0; display: flex; flex-direction: column; gap: 24px; }
.right-col { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 24px; }

.section-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
}
.section-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.section-card-title { font-size: 16px; font-weight: 600; color: #1D2939; }

.metric-toggles { display: flex; gap: 6px; }
.metric-btn-active {
  background: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #fff !important;
}

.dist-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.dist-card { min-height: 340px; }

.region-full-card { margin-top: 24px; }

.province-select { width: 120px; }

.dest-table { margin-top: 8px; }
.dest-table :deep(.el-table__header th),
.info-table :deep(.el-table__header th) {
  background: #F8FAFC;
  color: #344054;
  font-weight: 600;
  font-size: 13px;
}
.dest-table :deep(.el-table__body td),
.info-table :deep(.el-table__body td) {
  color: #344054;
  font-size: 13px;
}
.dest-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td),
.info-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #F8FAFC;
}

.chart-box { width: 100%; }

@media (max-width: 1200px) {
  .content-wrapper { flex-direction: column; }
  .left-col { flex: 1; }
  .stat-row .el-col { flex: 0 0 50%; max-width: 50%; margin-bottom: 12px; }
  .dist-grid { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .stat-row .el-col { flex: 0 0 100%; max-width: 100%; margin-bottom: 10px; }
}
</style>
