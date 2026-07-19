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
      <p>点击关键词查看跨领域关联分析 · 共 {{ totalKeywords }} 个关键词</p>
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
          <span class="panel-count">{{ panel.data.length }}个关键词</span>
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
              <span class="weight-label">科研权重</span>
              <div class="weight-bar">
                <div class="weight-fill research" :style="{ width: researchWeight + '%' }"></div>
              </div>
              <span class="weight-value">{{ researchWeight }}</span>
            </div>
            <div class="weight-item">
              <span class="weight-label">课程权重</span>
              <div class="weight-bar">
                <div class="weight-fill course" :style="{ width: courseWeight + '%' }"></div>
              </div>
              <span class="weight-value">{{ courseWeight }}</span>
            </div>
            <div class="weight-item">
              <span class="weight-label">评价权重</span>
              <div class="weight-bar">
                <div class="weight-fill evaluation" :style="{ width: evaluationWeight + '%' }"></div>
              </div>
              <span class="weight-value">{{ evaluationWeight }}</span>
            </div>
          </div>

          <div class="trend-section">
            <h4>五年趋势</h4>
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
    subtitle: '青色星系',
    color: '#00d4ff',
    glow: 'rgba(0, 212, 255, 0.5)',
    data: []
  },
  {
    key: 'course',
    title: '课程关键词',
    subtitle: '紫色星系',
    color: '#a855f7',
    glow: 'rgba(168, 85, 247, 0.5)',
    data: []
  },
  {
    key: 'evaluation',
    title: '评价关键词',
    subtitle: '橙色星系',
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

const researchWords = [
  { name: '公共政策', value: 100 }, { name: '政府治理', value: 85 }, { name: '政治学理论', value: 78 },
  { name: '国际关系', value: 72 }, { name: '公共管理', value: 68 }, { name: '社会治理', value: 65 },
  { name: '数字政府', value: 62 }, { name: '公共服务', value: 58 }, { name: '比较政治', value: 55 },
  { name: '国际安全', value: 52 }, { name: '社会保障', value: 48 }, { name: '公共财政', value: 45 },
  { name: '城市治理', value: 42 }, { name: '政策分析', value: 38 }, { name: '政策评估', value: 35 },
  { name: '基层治理', value: 33 }, { name: '国家治理', value: 31 }, { name: '法治建设', value: 30 },
  { name: '全球化', value: 28 }, { name: '区域发展', value: 26 }, { name: '组织行为', value: 25 },
  { name: '应急管理', value: 24 }, { name: '乡村振兴', value: 23 }, { name: '数据治理', value: 22 },
  { name: '环境治理', value: 21 }, { name: '科技创新', value: 20 }, { name: '财政政策', value: 19 },
  { name: '电子政务', value: 18 }, { name: '公众参与', value: 17 }, { name: '绩效评估', value: 16 }
]

const courseWords = [
  { name: '政治学原理', value: 100 }, { name: '公共管理学', value: 92 }, { name: '公共政策', value: 88 },
  { name: '行政法学', value: 82 }, { name: '社会学', value: 78 }, { name: '管理学原理', value: 75 },
  { name: '组织行为学', value: 70 }, { name: '公共经济学', value: 65 }, { name: '统计学', value: 60 },
  { name: '研究方法', value: 55 }, { name: '行政管理', value: 50 }, { name: '国际关系', value: 48 },
  { name: '公共行政', value: 45 }, { name: '政治学方法论', value: 42 }, { name: '数据分析', value: 38 },
  { name: '公共政策分析', value: 36 }, { name: '宪法与行政法', value: 34 }, { name: '城市管理', value: 32 },
  { name: '公共部门管理', value: 30 }, { name: '非营利组织', value: 28 }, { name: '领导科学', value: 27 },
  { name: '公文写作', value: 25 }, { name: '中国政治', value: 24 }, { name: '西方政治', value: 23 },
  { name: '比较政治制度', value: 22 }, { name: '管理信息系统', value: 21 }, { name: '财政学', value: 20 },
  { name: '公共政策评估', value: 19 }, { name: '危机管理', value: 18 }, { name: '人力资源管理', value: 17 }
]

const evaluationWords = [
  { name: '教学认真', value: 100 }, { name: '课程有趣', value: 95 }, { name: '老师负责', value: 90 },
  { name: '内容丰富', value: 85 }, { name: '深入浅出', value: 80 }, { name: '互动性强', value: 75 },
  { name: '作业合理', value: 70 }, { name: '考核公正', value: 65 }, { name: '学术严谨', value: 60 },
  { name: '思维启发', value: 55 }, { name: '课堂活跃', value: 50 }, { name: '讲解清晰', value: 48 },
  { name: '答疑及时', value: 45 }, { name: '资料丰富', value: 42 }, { name: '案例生动', value: 38 },
  { name: '知识渊博', value: 35 }, { name: '逻辑清晰', value: 33 }, { name: '鼓励思考', value: 31 },
  { name: '态度和蔼', value: 30 }, { name: '板书工整', value: 28 }, { name: '节奏适中', value: 27 },
  { name: '幽默风趣', value: 26 }, { name: '联系实际', value: 25 }, { name: '重点突出', value: 24 },
  { name: '视野开阔', value: 23 }, { name: '反馈及时', value: 22 }, { name: '内容前沿', value: 21 },
  { name: '因材施教', value: 20 }, { name: '跨学科', value: 19 }, { name: '团队合作', value: 18 }
]

const cooccurrenceMap = {
  '公共政策': ['行政管理', '社会治理', '政策分析', '政府治理', '公共管理', '公共政策分析', '公共政策评估'],
  '政府治理': ['公共政策', '社会治理', '数字政府', '城市治理', '公共服务', '国家治理', '基层治理'],
  '政治学理论': ['比较政治', '国际关系', '政治学方法论', '研究方法', '行政管理', '中国政治', '西方政治'],
  '国际关系': ['国际安全', '比较政治', '政治学理论', '公共政策', '全球治理', '全球化', '国家安全'],
  '公共管理': ['行政管理', '公共政策', '公共经济学', '组织行为学', '公共服务', '公共部门管理'],
  '政治学原理': ['政治学理论', '研究方法', '行政管理', '社会学', '公共管理学', '中国政治'],
  '公共管理学': ['公共管理', '管理学原理', '组织行为学', '公共经济学', '行政法学', '公共行政'],
  '行政法学': ['公共管理学', '行政管理', '公共政策', '宪法与行政法', '公共行政', '法治建设'],
  '教学认真': ['老师负责', '学术严谨', '讲解清晰', '课程有趣', '思维启发', '知识渊博', '答疑及时'],
  '课程有趣': ['教学认真', '内容丰富', '深入浅出', '案例生动', '课堂活跃', '幽默风趣', '联系实际'],
  '社会治理': ['政府治理', '公共政策', '基层治理', '公共服务', '城市治理', '国家治理', '乡村振兴'],
  '数字政府': ['政府治理', '数据分析', '电子政务', '公共服务', '行政管理', '数据治理', '科技创新'],
  '公共服务': ['公共管理', '政府治理', '社会治理', '电子政务', '行政管理', '公共政策'],
  '组织行为学': ['管理学原理', '公共管理', '领导科学', '人力资源管理', '组织行为'],
  '数据分析': ['统计学', '研究方法', '管理信息系统', '数字政府', '数据治理'],
  '学术严谨': ['教学认真', '老师负责', '思维启发', '知识渊博', '内容前沿', '逻辑清晰'],
  '内容丰富': ['课程有趣', '深入浅出', '案例生动', '视野开阔', '资料丰富', '跨学科'],
  '深入浅出': ['内容丰富', '课程有趣', '讲解清晰', '逻辑清晰', '重点突出', '案例生动'],
  '互动性强': ['课堂活跃', '鼓励思考', '团队合作', '思维启发', '讨论交流', '公众参与'],
  '行政管理': ['公共管理', '公共行政', '行政法学', '组织行为学', '数字政府', '人力资源管理'],
  '社会保障': ['公共政策', '公共财政', '社会治理', '公共服务', '政策分析', '财政政策'],
  '城市治理': ['政府治理', '社会治理', '公共管理', '城市管理', '区域发展', '应急管理'],
  '环境治理': ['社会治理', '公共政策', '可持续发展', '乡村振兴', '区域发展', '科技创新'],
  '绩效评估': ['公共管理', '政策评估', '行政管理', '公共部门管理', '政府治理']
}

const researchWeight = computed(() => {
  if (!selectedWord.value) return 0
  const word = researchWords.find(w => w.name === selectedWord.value.name)
  return word ? word.value : 0
})

const courseWeight = computed(() => {
  if (!selectedWord.value) return 0
  const word = courseWords.find(w => w.name === selectedWord.value.name)
  return word ? word.value : 0
})

const evaluationWeight = computed(() => {
  if (!selectedWord.value) return 0
  const word = evaluationWords.find(w => w.name === selectedWord.value.name)
  return word ? word.value : 0
})

const cooccurrenceWords = computed(() => {
  if (!selectedWord.value) return []
  return cooccurrenceMap[selectedWord.value.name] || []
})

const totalKeywords = computed(() => {
  return researchWords.length + courseWords.length + evaluationWords.length
})

const setChartRef = (el, key) => {
  if (el) {
    chartRefs.value[key] = el
  }
}

const getTagColor = (idx) => {
  const colors = ['#00d4ff', '#a855f7', '#ff9500', '#4ecdc4', '#ffe66d']
  return colors[idx % colors.length]
}

const createBubbleOption = (data, panelColor, highlightWords = []) => {
  const nodes = data.map(item => ({
    name: item.name,
    value: item.value,
    symbolSize: Math.max(24, Math.min(66, item.value * 0.55 + 8)),
    category: 0
  }))

  const links = []
  for (let i = 0; i < data.length; i++) {
    for (let j = i + 1; j < data.length; j++) {
      if (Math.random() > 0.7) {
        links.push({
          source: data[i].name,
          target: data[j].name,
          value: Math.random() * 5 + 1
        })
      }
    }
  }

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
          return `<div><b style="color:${panelColor}">${params.name}</b><br/>权重: ${params.value}</div>`
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
    const data = panel.key === 'research' ? researchWords : 
                 panel.key === 'course' ? courseWords : evaluationWords
    panel.data = data

    if (!chartRefs.value[panel.key]) return

    if (chartInstances.value[panel.key]) {
      chartInstances.value[panel.key].dispose()
    }

    chartInstances.value[panel.key] = echarts.init(chartRefs.value[panel.key])
    const option = createBubbleOption(data, panel.color)
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
  
  const relatedWords = [wordName, ...(cooccurrenceMap[wordName] || [])]

  panels.value.forEach(panel => {
    const data = panel.key === 'research' ? researchWords : 
                 panel.key === 'course' ? courseWords : evaluationWords
    
    const option = createBubbleOption(data, panel.color, relatedWords)
    chartInstances.value[panel.key].setOption(option, true)
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
    const data = panel.key === 'research' ? researchWords : 
                 panel.key === 'course' ? courseWords : evaluationWords
    
    const option = createBubbleOption(data, panel.color, [])
    chartInstances.value[panel.key].setOption(option, true)
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

  const years = ['2022', '2023', '2024', '2025', '2026']
  
  const generateTrend = (baseValue) => {
    return years.map(() => {
      const variation = Math.floor(Math.random() * 30) - 15
      return Math.max(20, Math.min(100, baseValue + variation))
    })
  }

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
      data: ['科研趋势', '课程趋势', '评价趋势'],
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
      axisLabel: { color: 'rgba(255, 255, 255, 0.6)' },
      axisLine: { lineStyle: { color: 'rgba(0, 212, 255, 0.3)' } },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.05)' } }
    },
    series: [
      {
        name: '科研趋势',
        type: 'line',
        data: generateTrend(researchWeight.value),
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#00d4ff', width: 3 },
        itemStyle: { color: '#00d4ff', borderWidth: 2, borderColor: '#fff' },
        areaStyle: { color: 'rgba(0, 212, 255, 0.1)' }
      },
      {
        name: '课程趋势',
        type: 'line',
        data: generateTrend(courseWeight.value),
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#a855f7', width: 3 },
        itemStyle: { color: '#a855f7', borderWidth: 2, borderColor: '#fff' },
        areaStyle: { color: 'rgba(168, 85, 247, 0.1)' }
      },
      {
        name: '评价趋势',
        type: 'line',
        data: generateTrend(evaluationWeight.value),
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#ff9500', width: 3 },
        itemStyle: { color: '#ff9500', borderWidth: 2, borderColor: '#fff' },
        areaStyle: { color: 'rgba(255, 149, 0, 0.1)' }
      }
    ]
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

onMounted(() => {
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