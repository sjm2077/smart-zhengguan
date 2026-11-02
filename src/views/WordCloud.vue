<template>
  <div class="wordcloud-page">
    <div class="stars-layer">
      <div v-for="n in 60" :key="n" class="star" :style="{
        left: ((n * 17) % 100) + '%',
        top: ((n * 23 + 7) % 100) + '%',
        width: (n % 3 === 0 ? 3 : 2) + 'px',
        height: (n % 3 === 0 ? 3 : 2) + 'px',
        animationDelay: (n * 0.3) + 's',
        animationDuration: (2 + (n % 3)) + 's',
        opacity: 0.3 + (n % 5) * 0.15
      }"></div>
    </div>
    <div class="page-header">
      <h2>词云分析</h2>
      <p>
        点击关键词查看跨领域关联分析 · 共 {{ totalKeywords }} 个关键词
        <span class="src-note">数据来源：官网论文题录 375 篇 / 教师个人主页 88 人 / 通知公告 {{ noticeDocs }} 条（真实爬取，非手工词表）</span>
      </p>
      <p v-if="wcLoading" class="src-note">正在从学院官网数据计算词频…</p>
      <p v-else-if="wcError" class="src-note error">{{ wcError }}</p>
    </div>

    <div class="galaxy-container">
      <div 
        v-for="(panel, index) in panels" 
        :key="panel.key"
        class="galaxy-panel"
        :style="{ '--panel-color': panel.color, '--panel-glow': panel.glow }"
      >
        <div class="panel-header">
            <div class="panel-icon" :style="{ background: panel.color }"></div>
            <h3>{{ panel.title }}</h3>
            <span class="panel-count">{{ panel.subtitle }} · {{ panel.data.length }}词</span>
          </div>
        <div class="chart-wrapper" :ref="(el) => setChartRef(el, panel.key)"></div>
        <div class="panel-footer">
          <span>点击词 → 高亮关联</span>
        </div>
      </div>
    </div>

    <transition name="slide-up">
      <div v-if="selectedWord" class="detail-panel">
        <div class="detail-header">
          <h3>详情面板：{{ selectedWord.name }}</h3>
          <button class="close-btn" @click="clearSelection">✕</button>
        </div>
        <div class="detail-content">
          <div class="weight-section">
            <div class="weight-item">
              <span class="weight-label">论文出现</span>
              <div class="weight-bar">
                <div class="weight-fill research" :style="{ width: researchPercent + '%' }"></div>
              </div>
              <span class="weight-value">{{ researchWeight }}</span>
            </div>
            <div class="weight-item">
              <span class="weight-label">教师人数</span>
              <div class="weight-bar">
                <div class="weight-fill course" :style="{ width: coursePercent + '%' }"></div>
              </div>
              <span class="weight-value">{{ courseWeight }}</span>
            </div>
            <div class="weight-item">
              <span class="weight-label">通知提及</span>
              <div class="weight-bar">
                <div class="weight-fill evaluation" :style="{ width: evaluationPercent + '%' }"></div>
              </div>
              <span class="weight-value">{{ evaluationWeight }}</span>
            </div>
          </div>

          <div class="trend-section">
            <h4>年度分布（官网真实年份）</h4>
            <div class="trend-chart" ref="trendChartRef"></div>
          </div>

          <div class="cooccurrence-section">
            <h4>共现词</h4>
            <div class="cooccurrence-tags">
              <span 
                v-for="(word, idx) in cooccurrenceWords" 
                :key="idx"
                class="cooccurrence-tag"
                :style="{ '--tag-color': getTagColor(idx) }"
                @click="selectWord(word)"
              >
                {{ word }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const panels = ref([
  {
    key: 'research',
    title: '科研关键词',
    subtitle: '官网论文题录 375 篇',
    color: '#00d4ff',
    glow: 'rgba(0, 212, 255, 0.5)',
    data: []
  },
  {
    key: 'course',
    title: '教师研究方向',
    subtitle: '官网个人主页 88 人',
    color: '#a855f7',
    glow: 'rgba(168, 85, 247, 0.5)',
    data: []
  },
  {
    key: 'evaluation',
    title: '通知公告热词',
    subtitle: '官网通知 899 条',
    color: '#ff9500',
    glow: 'rgba(255, 149, 0, 0.5)',
    data: []
  }
])

const chartRefs = ref({})
const trendChartRef = ref(null)
const selectedWord = ref(null)
const chartInstances = ref({})
const trendChartInstance = ref(null)

// 三个面板的词与共现关系全部由后端从官网数据现算（见 /api/real/pspa-wordcloud）
const panelWords = ref({ research: [], course: [], evaluation: [] })
const cooccurrenceMap = ref({ research: {}, course: {}, evaluation: {} })
const edgeMap = ref({ research: [], course: [], evaluation: [] })
const wcLoading = ref(true)
const wcError = ref('')
const wcSource = ref({})
const noticeDocs = ref(0)

const loadWordcloudData = async () => {
  wcLoading.value = true
  wcError.value = ''
  try {
    const res = await fetch('/api-research/api/real/pspa-wordcloud')
    if (!res.ok) throw new Error('HTTP ' + res.status)
    const json = await res.json()
    panelWords.value = json.panels || { research: [], course: [], evaluation: [] }
    cooccurrenceMap.value = json.cooccurrence || { research: {}, course: {}, evaluation: {} }
    edgeMap.value = json.edges || { research: [], course: [], evaluation: [] }
    wcSource.value = json.source || {}
    noticeDocs.value = json.notice_docs || 0
    panels.value.forEach(p => { p.data = panelWords.value[p.key] || [] })
  } catch (e) {
    wcError.value = '官网词云数据加载失败：' + e.message
  } finally {
    wcLoading.value = false
  }
}

const getWords = (key) => panelWords.value[key] || []

const findWord = (key, name) => getWords(key).find(w => w.name === name)

const researchWeight = computed(() => {
  if (!selectedWord.value) return 0
  const word = findWord('research', selectedWord.value.name)
  return word ? word.value : 0
})

const courseWeight = computed(() => {
  if (!selectedWord.value) return 0
  const word = findWord('course', selectedWord.value.name)
  return word ? word.value : 0
})

const evaluationWeight = computed(() => {
  if (!selectedWord.value) return 0
  const word = findWord('evaluation', selectedWord.value.name)
  return word ? word.value : 0
})

const maxWeight = (key) => Math.max(1, ...getWords(key).map(w => w.value))

// 三个面板的量纲不同（论文次数/教师人数/通知提及），进度条按各自最大值归一
const researchPercent = computed(() => Math.round(researchWeight.value / maxWeight('research') * 100))
const coursePercent = computed(() => Math.round(courseWeight.value / maxWeight('course') * 100))
const evaluationPercent = computed(() => Math.round(evaluationWeight.value / maxWeight('evaluation') * 100))

const cooccurrenceWords = computed(() => {
  if (!selectedWord.value) return []
  const name = selectedWord.value.name
  const merged = []
  ;['research', 'course', 'evaluation'].forEach(key => {
    const list = (cooccurrenceMap.value[key] || {})[name] || []
    list.forEach(w => { if (!merged.includes(w)) merged.push(w) })
  })
  return merged.slice(0, 8)
})

const selectedWordYears = computed(() => {
  if (!selectedWord.value) return {}
  const name = selectedWord.value.name
  const out = {}
  ;['research', 'evaluation'].forEach(key => {
    const w = findWord(key, name)
    if (w && w.years) out[key] = w.years
  })
  return out
})

const totalKeywords = computed(() => getWords('research').length + getWords('course').length + getWords('evaluation').length)

const setChartRef = (el, key) => {
  if (el) {
    chartRefs.value[key] = el
  }
}

const getTagColor = (idx) => {
  const colors = ['#00d4ff', '#a855f7', '#ff9500', '#4ecdc4', '#ffe66d']
  return colors[idx % colors.length]
}

const createBubbleOption = (data, panelColor, highlightWords = [], edges = []) => {
  const nodes = data.map(item => ({
    name: item.name,
    value: item.value,
    symbolSize: Math.max(24, Math.min(66, item.value * 0.55 + 8)),
    category: 0
  }))

  // 连线来自官网真实共现（同一篇论文的关键词、同一份教师主页的研究方向、同一条通知里同时出现）
  const names = new Set(data.map(d => d.name))
  const links = edges
    .filter(e => names.has(e.source) && names.has(e.target))
    .slice(0, 160)
    .map(e => ({
      source: e.source,
      target: e.target,
      value: e.value,
      lineStyle: { width: Math.min(5, 1 + e.value * 0.4) }
    }))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(0, 0, 0, 0.9)',
      borderColor: panelColor,
      borderWidth: 1,
      textStyle: { color: '#fff' },
      formatter: (params) => {
        if (params.dataType === 'node') {
          return `<div><b style="color:${panelColor}">${params.name}</b><br/>出现次数: ${params.value}</div>`
        }
        if (params.dataType === 'edge') {
          return `<div>${params.data.source} ↔ ${params.data.target}<br/>共现 ${params.data.value} 次</div>`
        }
        return ''
      }
    },
    animationDuration: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [
      {
        name: '关键词星系',
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 4 }
        },
        force: {
          repulsion: 180,
          gravity: 0.08,
          edgeLength: [50, 140],
          layoutAnimation: true
        },
        data: nodes.map(node => {
          const isHighlighted = highlightWords.includes(node.name)
          const baseColor = panelColor
          const brightColor = (c) => {
            const v = parseInt(c.slice(1), 16)
            const r = Math.min(255, (v >> 16) + 80)
            const g = Math.min(255, ((v >> 8) & 0xff) + 80)
            const b = Math.min(255, (v & 0xff) + 80)
            return `rgb(${r},${g},${b})`
          }
          return {
            ...node,
            itemStyle: {
              color: isHighlighted
                ? baseColor
                : baseColor + '88',
              borderColor: isHighlighted
                ? brightColor(baseColor)
                : baseColor + 'aa',
              borderWidth: isHighlighted ? 4 : 2.5,
              shadowBlur: isHighlighted ? 35 : 20,
              shadowColor: isHighlighted
                ? 'rgba(255,255,255,0.6)'
                : baseColor + '60'
            },
            label: {
              show: true,
              position: 'bottom',
              distance: 6,
              fontSize: Math.max(13, Math.min(17, node.value / 6.5)),
              color: isHighlighted ? '#ffffff' : '#f0f0f0',
              fontWeight: isHighlighted ? 'bold' : '500',
              textShadowColor: 'rgba(0,0,0,0.9)',
              textShadowBlur: 6,
              textBorderColor: 'rgba(0,0,0,0.5)',
              textBorderWidth: 1
            }
          }
        }),
        links: links.map(link => {
          const isHighlighted = highlightWords.length > 0 && 
            highlightWords.includes(link.source) && 
            highlightWords.includes(link.target)
          return {
            ...link,
            lineStyle: {
              color: isHighlighted 
                ? panelColor 
                : panelColor + '77',
              width: isHighlighted ? 4 : 2,
              curveness: 0.3,
              shadowBlur: isHighlighted ? 12 : 6,
              shadowColor: isHighlighted ? panelColor : panelColor + '40',
              opacity: isHighlighted ? 1 : 0.5
            }
          }
        }),
        categories: [{ name: '关键词' }]
      }
    ]
  }
}

const initCharts = () => {
  panels.value.forEach(panel => {
    const data = getWords(panel.key)
    panel.data = data

    if (!chartRefs.value[panel.key]) return

    if (chartInstances.value[panel.key]) {
      chartInstances.value[panel.key].dispose()
    }

    chartInstances.value[panel.key] = echarts.init(chartRefs.value[panel.key])
    const option = createBubbleOption(data, panel.color, [], edgeMap.value[panel.key] || [])
    chartInstances.value[panel.key].setOption(option)

    chartInstances.value[panel.key].on('click', (params) => {
      if (params.dataType === 'node') {
        handleWordClick(params.name)
      }
    })

    chartInstances.value[panel.key].on('dblclick', () => {
      const chart = chartInstances.value[panel.key]
      chart.dispatchAction({ type: 'restore' })
    })
  })
}

const handleWordClick = (wordName) => {
  selectedWord.value = { name: wordName }
  
  const relatedWords = [wordName, ...cooccurrenceWords.value]

  panels.value.forEach(panel => {
    const data = getWords(panel.key)
    const option = createBubbleOption(data, panel.color, relatedWords, edgeMap.value[panel.key] || [])
    if (chartInstances.value[panel.key]) {
      chartInstances.value[panel.key].setOption(option, true)
    }
  })

  nextTick(() => {
    initTrendChart()
  })
}

const selectWord = (wordName) => {
  handleWordClick(wordName)
}

const clearSelection = () => {
  selectedWord.value = null
  
  panels.value.forEach(panel => {
    const data = getWords(panel.key)
    const option = createBubbleOption(data, panel.color, [], edgeMap.value[panel.key] || [])
    if (chartInstances.value[panel.key]) {
      chartInstances.value[panel.key].setOption(option, true)
    }
  })

  if (trendChartInstance.value) {
    trendChartInstance.value.dispose()
    trendChartInstance.value = null
  }
}

const initTrendChart = () => {
  if (!trendChartRef.value || !selectedWord.value) return

  if (trendChartInstance.value) {
    trendChartInstance.value.dispose()
  }

  trendChartInstance.value = echarts.init(trendChartRef.value)

  const years = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']
  const data = selectedWordYears.value

  const seriesConf = [
    { key: 'research', name: '论文出现次数', color: '#00d4ff' },
    { key: 'evaluation', name: '通知提及次数', color: '#ff9500' }
  ]

  const series = seriesConf
    .filter(s => data[s.key])
    .map(s => ({
      name: s.name,
      type: 'line',
      data: years.map(y => data[s.key][y] || 0),
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { color: s.color, width: 3 },
      itemStyle: { color: s.color, borderWidth: 2, borderColor: '#fff' },
      areaStyle: { color: 'rgba(0, 212, 255, 0.08)' }
    }))

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(0, 0, 0, 0.85)',
      borderColor: '#00d4ff',
      borderWidth: 1,
      textStyle: { color: '#fff' }
    },
    legend: {
      data: series.map(s => s.name),
      textStyle: { color: 'rgba(255, 255, 255, 0.7)' },
      top: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: years,
      axisLabel: { color: 'rgba(255, 255, 255, 0.6)' },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: 'rgba(255, 255, 255, 0.6)' },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
    },
    title: series.length ? undefined : {
      text: '该词仅出现在教师研究方向里，官网无逐年数据',
      left: 'center',
      top: 'center',
      textStyle: { color: 'rgba(255,255,255,0.55)', fontSize: 13, fontWeight: 'normal' }
    },
    series
  }

  trendChartInstance.value.setOption(option)
}

const handleResize = () => {
  Object.values(chartInstances.value).forEach(chart => {
    if (chart) chart.resize()
  })
  if (trendChartInstance.value) {
    trendChartInstance.value.resize()
  }
}

watch(selectedWord, () => {
  if (selectedWord.value) {
    nextTick(() => {
      initTrendChart()
    })
  }
})

onMounted(async () => {
  await loadWordcloudData()
  nextTick(() => {
    initCharts()
  })
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  Object.values(chartInstances.value).forEach(chart => {
    if (chart) chart.dispose()
  })
  if (trendChartInstance.value) {
    trendChartInstance.value.dispose()
  }
})
</script>

<style scoped>
.src-note {
  display: inline-block;
  margin-left: 12px;
  font-size: 12px;
  color: rgba(0, 212, 255, 0.75);
}
.src-note.error {
  color: #ff7875;
}
.wordcloud-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  box-sizing: border-box;
  background: linear-gradient(135deg, #080e20 0%, #0a1628 50%, #0d1f3c 100%);
  position: relative;
  overflow: hidden;
}

.stars-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.star {
  position: absolute;
  background: #fff;
  border-radius: 50%;
  animation: twinkle ease-in-out infinite alternate;
  box-shadow: 0 0 6px rgba(255,255,255,0.6);
}

@keyframes twinkle {
  0% { opacity: 0.2; transform: scale(0.8); }
  100% { opacity: 1; transform: scale(1.2); }
}

.page-header {
  text-align: center;
  padding: 10px 0;
  position: relative;
  z-index: 1;
}

.page-header h2 {
  font-size: 28px;
  color: #fff;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #00d4ff, #a855f7, #ff9500);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
  letter-spacing: 2px;
  text-shadow: 0 0 40px rgba(0, 212, 255, 0.2);
}

.page-header p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  letter-spacing: 1px;
}

.galaxy-container {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  min-height: 500px;
  position: relative;
  z-index: 1;
}

.galaxy-panel {
  background: rgba(0, 0, 0, 0.75);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
  position: relative;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.06);
  transition: all 0.3s ease;
  backdrop-filter: blur(6px);
}

.galaxy-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, var(--panel-color), transparent);
  opacity: 0.8;
}

.galaxy-panel::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(ellipse at center, var(--panel-glow) 0%, transparent 60%);
  opacity: 0.06;
  pointer-events: none;
  animation: panelGlow 8s ease-in-out infinite alternate;
}

@keyframes panelGlow {
  0% { transform: translate(-10%, -10%); opacity: 0.04; }
  100% { transform: translate(10%, 10%); opacity: 0.08; }
}

.galaxy-panel:hover {
  border-color: var(--panel-color);
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.3), 0 0 30px var(--panel-glow);
  transform: translateY(-3px);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.15);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.panel-icon {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 0 12px var(--panel-glow);
}

.panel-header h3 {
  font-size: 16px;
  color: #fff;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 0 20px rgba(255,255,255,0.1);
}

.panel-count {
  margin-left: auto;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.08);
  padding: 4px 10px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.chart-wrapper {
  height: calc(100% - 80px);
  min-height: 380px;
}

.panel-footer {
  padding: 10px 20px;
  text-align: center;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.panel-footer span {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  letter-spacing: 0.5px;
}

.detail-panel {
  background: rgba(5, 10, 25, 0.95);
  border-radius: 16px;
  border: 1px solid rgba(0, 212, 255, 0.25);
  padding: 20px;
  margin-top: 10px;
  box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4), 0 0 30px rgba(0, 212, 255, 0.15);
  backdrop-filter: blur(8px);
  position: relative;
  z-index: 2;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
}

.detail-header h3 {
  font-size: 18px;
  color: #fff;
  margin: 0;
  font-weight: 600;
  text-shadow: 0 0 20px rgba(0,212,255,0.2);
}

.close-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(255, 77, 79, 0.25);
  border-color: rgba(255, 77, 79, 0.5);
  color: #ff4d4f;
}

.detail-content {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 24px;
}

.weight-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.weight-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weight-label {
  width: 80px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  white-space: nowrap;
}

.weight-bar {
  flex: 1;
  height: 12px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
}

.weight-fill {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease;
}

.weight-fill.research {
  background: linear-gradient(90deg, #00d4ff, #4facfe);
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.6);
}

.weight-fill.course {
  background: linear-gradient(90deg, #a855f7, #c084fc);
  box-shadow: 0 0 12px rgba(168, 85, 247, 0.6);
}

.weight-fill.evaluation {
  background: linear-gradient(90deg, #ff9500, #fbbf24);
  box-shadow: 0 0 12px rgba(255, 149, 0, 0.6);
}

.weight-value {
  width: 40px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  text-align: right;
}

.trend-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trend-section h4 {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.trend-chart {
  flex: 1;
  height: 150px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.cooccurrence-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cooccurrence-section h4 {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.cooccurrence-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.cooccurrence-tag {
  padding: 8px 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid var(--tag-color);
  color: var(--tag-color);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-shadow: 0 0 8px rgba(255,255,255,0.1);
}

.cooccurrence-tag:hover {
  background: var(--tag-color);
  color: #000;
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 4px 20px var(--tag-color);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.4s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 1200px) {
  .galaxy-container {
    grid-template-columns: 1fr;
  }
  
  .detail-content {
    grid-template-columns: 1fr;
  }
  
  .trend-chart {
    height: 200px;
  }
}
</style>