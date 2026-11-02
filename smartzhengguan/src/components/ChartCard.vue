<template>
  <div class="chart-card">
    <div class="chart-header">
      <span class="chart-title">{{ title }}</span>
      <el-button
        v-if="showExport"
        class="export-btn"
        size="small"
        text
        @click="handleExport"
      >导出</el-button>
    </div>
    <div ref="chartRef" class="chart-box" :style="{ height: chartHeight }"></div>
  </div>
</template>

<script>
import { defineComponent, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

export default defineComponent({
  props: {
    title: { type: String, default: '' },
    chartOptions: { type: Object, default: () => ({}) },
    showExport: { type: Boolean, default: false },
    chartHeight: { type: String, default: '280px' },
  },
  setup(props) {
    const chartRef = ref(null)
    let chart = null
    let resizeObserver = null

    const resizeChart = () => {
      if (chart) chart.resize()
    }

    const initChart = () => {
      if (!chartRef.value) return
      if (!chart) {
        chart = echarts.init(chartRef.value)
      }
      const opts = props.chartOptions || {}
      if (opts.radar && (!opts.radar.indicator || !opts.radar.indicator.length)) return
      chart.setOption(opts, true)
      nextTick(() => resizeChart())
    }

    const handleExport = () => {
      if (!chart) return
      const url = chart.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#fff',
      })
      const link = document.createElement('a')
      link.href = url
      link.download = `${props.title || '图表'}.png`
      link.click()
    }

    onMounted(() => {
      initChart()
      window.addEventListener('resize', resizeChart)
      if (window.ResizeObserver && chartRef.value) {
        resizeObserver = new ResizeObserver(() => resizeChart())
        resizeObserver.observe(chartRef.value)
      }
    })

    watch(() => props.chartOptions, () => initChart(), { deep: true })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', resizeChart)
      if (resizeObserver) {
        resizeObserver.disconnect()
        resizeObserver = null
      }
      if (chart) {
        chart.dispose()
        chart = null
      }
    })

    return { chartRef, handleExport }
  },
})
</script>

<style scoped>
.chart-card {
  background: #fff;
  border-radius: 0;
  padding: 20px;
  height: 100%;
  min-width: 0;
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.chart-title {
  font-size: 16px;
  font-weight: 400;
  color: #333;
}
.export-btn {
  font-size: 12px;
  color: #165DFF;
  padding: 2px 8px;
}
.chart-box {
  width: 100%;
}
</style>
