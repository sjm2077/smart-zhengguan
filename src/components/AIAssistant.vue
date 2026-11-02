<template>
  <div class="ai-assistant" ref="assistantRef">
    <button class="ai-toggle-btn" @click="toggleAssistant" :title="showPanel ? '收起AI助手' : '打开AI助手'">
      <span v-if="!showPanel">🤖</span>
      <span v-else>✕</span>
    </button>

    <transition name="slide-up">
      <div class="ai-panel" v-if="showPanel">
        <div class="panel-header">
          <div class="header-info">
            <span class="ai-icon">🤖</span>
            <div class="ai-title">
              <h3>政管AI助手</h3>
              <span class="status-dot"></span>
              <span class="status-text">在线</span>
            </div>
          </div>
        </div>

        <div class="panel-tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.key"
            :class="['tab-btn', { active: activeTab === tab.key }]"
            @click="switchTab(tab.key)"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="panel-content">
          <div v-if="activeTab === 'qa'" class="qa-section">
            <div class="quick-questions">
              <span class="quick-title">热门问题</span>
              <div class="question-list">
                <button 
                  v-for="q in quickQuestions" 
                  :key="q"
                  class="question-tag"
                  @click="sendQuestion(q)"
                >
                  {{ q }}
                </button>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'report'" class="report-section">
            <div class="report-list">
              <div class="report-item" @click="interpretReport('overview')">
                <div class="report-icon">📊</div>
                <div class="report-info">
                  <div class="report-name">综合概览解读</div>
                  <div class="report-desc">解读当前页面KPI和图表</div>
                </div>
              </div>
              <div class="report-item" @click="interpretReport('students')">
                <div class="report-icon">👥</div>
                <div class="report-info">
                  <div class="report-name">学生数据分析</div>
                  <div class="report-desc">解读生源分布、男女比例等</div>
                </div>
              </div>
              <div class="report-item" @click="interpretReport('research')">
                <div class="report-icon">🔬</div>
                <div class="report-info">
                  <div class="report-name">科研经费分析</div>
                  <div class="report-desc">解读科研项目和经费情况</div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'warning'" class="warning-section">
            <div class="warning-list">
              <div class="warning-item danger">
                <div class="warning-icon">🚨</div>
                <div class="warning-content">
                  <div class="warning-title">预算执行预警</div>
                  <div class="warning-desc">科研经费预算执行率偏低，可能影响项目进度</div>
                  <div class="warning-time">10分钟前</div>
                </div>
              </div>
              <div class="warning-item warning">
                <div class="warning-icon">⚠️</div>
                <div class="warning-content">
                  <div class="warning-title">招生趋势预警</div>
                  <div class="warning-desc">部分专业报名人数呈下降趋势</div>
                  <div class="warning-time">30分钟前</div>
                </div>
              </div>
              <div class="warning-item info">
                <div class="warning-icon">ℹ️</div>
                <div class="warning-content">
                  <div class="warning-title">数据更新提醒</div>
                  <div class="warning-desc">学生数据已更新，建议查看</div>
                  <div class="warning-time">2小时前</div>
                </div>
              </div>
            </div>
          </div>

          <div class="chat-messages" v-if="messages.length > 0">
            <div 
              v-for="(msg, idx) in messages" 
              :key="idx"
              :class="['message', msg.role]"
            >
              <div class="message-avatar">
                {{ msg.role === 'user' ? '👤' : '🤖' }}
              </div>
              <div class="message-content">
                <div class="message-text" style="white-space: pre-wrap;">{{ msg.content }}</div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            </div>
          </div>

          <div class="typing-indicator" v-if="isTyping">
            <div class="typing-dots">
              <span></span><span></span><span></span>
            </div>
            <span>AI正在思考...</span>
          </div>
        </div>

        <div class="panel-input">
          <textarea 
            v-model="inputText"
            placeholder="请输入您的问题..."
            @keydown.enter.prevent="sendMessage"
            @keydown.enter.ctrl="sendMessage"
            ref="inputRef"
            rows="1"
          ></textarea>
          <button class="send-btn" @click="sendMessage" :disabled="!inputText.trim() || isTyping">
            ➤
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const emit = defineEmits(['send-question'])

const props = defineProps({
  realData: {
    type: Object,
    default: () => ({
      students: 2420,
      undergrad: 600,
      master: 1560,
      doctor: 140,
      staff: 93,
      funding: 6000,
      projects: 100,
      budget: 0,
      maleRatio: null,
      femaleRatio: null
    })
  }
})

const showPanel = ref(false)
const activeTab = ref('qa')
const inputText = ref('')
const isTyping = ref(false)
const messages = ref([])
const inputRef = ref(null)
const assistantRef = ref(null)

const authStore = useAuthStore()

const currentData = computed(() => ({
  students: props.realData.students ?? 2420,
  undergrad: props.realData.undergrad ?? 600,
  master: props.realData.master ?? 1560,
  doctor: props.realData.doctor ?? 140,
  staff: props.realData.staff ?? 93,
  funding: props.realData.funding ?? 6000,
  projects: props.realData.projects ?? 100,
  budget: props.realData.budget ?? 0,
  maleRatio: props.realData.maleRatio,
  femaleRatio: props.realData.femaleRatio
}))

const tabs = [
  { key: 'qa', label: '数据问答' },
  { key: 'report', label: '报表解读' },
  { key: 'warning', label: '异常预警' }
]

const quickQuestions = [
  '当前在院生总数是多少？',
  '科研经费有多少？',
  '男女比例如何？',
  '预算执行率怎么样？',
  '分析一下生源分布',
  '今年招生情况如何？'
]

const SYSTEM_PROMPT = `你是山东大学政治学与公共管理学院的智能助手，负责回答关于学院数据的问题。

回答规范：
1. 使用简洁、专业的中文回答
2. 回答要有逻辑、有条理，重要信息可以分点列出
3. 绝对不要使用Markdown格式，包括：不要用**加粗、不要用#标题、不要用-列表符号、不要用代码块等
4. 如果需要分点说明，直接用数字编号（如1. 2. 3.）
5. 关键数据可以直接陈述，不要用特殊符号包裹
6. 保持回答清晰易懂，符合政务和学术场景的正式表述风格
7. 回答长度控制在200字以内，简洁明了`

const AI_PROXY_URL = '/api-grad/v1/chat-proxy/'

const toggleAssistant = () => {
  showPanel.value = !showPanel.value
  if (showPanel.value) {
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
}

const switchTab = (key) => {
  activeTab.value = key
}

const handleClickOutside = (e) => {
  if (assistantRef.value && !assistantRef.value.contains(e.target)) {
    showPanel.value = false
  }
}

const getCurrentTime = () => {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const addMessage = (role, content) => {
  messages.value.push({
    role,
    content,
    time: getCurrentTime()
  })
}

const mockAnswers = {
  '在院生总数': () => `按学院官网《学院简介》公布的招生规模换算，全院在校生约${currentData.value.students}人：本科约${currentData.value.undergrad}人、硕士约${currentData.value.master}人（含 MPA）、博士约${currentData.value.doctor}人。官网只公布“每年招生规模”，在校生数按标准学制换算，属于估算口径。`,
  '教职工总数': () => `学院官网全职教师名录共${currentData.value.staff}人：教授 37 人、副教授（含副研究员）29 人、讲师（含助理研究员）27 人、全职博士后 13 人；其中博士生导师 30 人、硕士生导师 46 人，91 人具有博士学位。`,
  '科研项目': () => `官网《学院简介》公布近五年科研项目共${currentData.value.projects}项：国家社科重大/教育部重大攻关 10 余项、国家社科基金各类 30 余项、国家自然科学基金 10 余项、其他部委项目 50 多项。`,
  '科研经费': () => `官网《学院简介》公布近五年科研项目总经费${currentData.value.funding}余万元（六千余万）。`,
  '预算执行': () => '学院官网未公布年度预算执行数据，平台暂不展示；接入财务系统后可给出真实执行率。',
  '男女比例': () => '学院官网未公布全院在读学生的男女比例，平台不编造该指标；如需展示需接入学籍系统。',
  '生源分布': '学院官网未公布分省生源结构。大屏上的生源地地图按全院在校生总量做“示意估算”，不代表官网口径。',
  '就业率': '学院官网未公布就业率统计，平台不编造；就业率趋势图标注为演示数据，待就业系统接入后替换。',
  '专业人数': () => `官网只公布培养层次的招生规模，不公布各专业在读人数。按官网口径每年招收：本科生 150 人、学术硕士 120 人、博士 35 人、公共管理专业硕士（MPA）400 人、全英文项目留学生 40 人。`,
  '师资结构': '官网原文：在职教师 93 人，91 人具有博士学位，26 人毕业于海外名校；博士生导师 30 人、硕士生导师 46 人。',
  '综合分析': () => `学院整体情况（官网口径）：专任教师${currentData.value.staff}人，近五年科研项目${currentData.value.projects}项、经费${currentData.value.funding}余万元；按招生规模换算全院在校生约${currentData.value.students}人（本科 ${currentData.value.undergrad} / 硕士 ${currentData.value.master} / 博士 ${currentData.value.doctor}）。`,
  '招生情况': '官网《学院简介》：每年招收本科生 150 人左右、学术硕士研究生 120 人左右、博士研究生 35 人左右、公共管理专业学位硕士研究生（MPA）400 人左右、全英文授课项目留学生 40 人左右。',
  '发展建议': '建议如下：1.官网未公布的数据（就业率、分省生源、男女比例、预算执行）优先通过学籍/就业/财务系统对接补齐，不用估算值对外汇报；2.持续采集官网学术成果与通知公告，保持数据时效；3.教师主页覆盖率仍有缺口（88/93），可推动补齐；4.知识库与智能体继续补充学院制度原文，提高问答命中率。'
}

const getMockAnswer = (question) => {
  const keywords = Object.keys(mockAnswers)
  for (const keyword of keywords) {
    if (question.includes(keyword)) {
      const answer = mockAnswers[keyword]
      return typeof answer === 'function' ? answer() : answer
    }
  }
  
  return `根据学院官网数据，我来为您分析：

当前核心指标（全院口径）：
1. 全院在校生：${currentData.value.students}人（本科 ${currentData.value.undergrad} / 硕士 ${currentData.value.master} / 博士 ${currentData.value.doctor}，官网招生规模×学制估算）
2. 专任教师：${currentData.value.staff}人
3. 近五年科研项目：${currentData.value.projects}项
4. 近五年科研经费：${currentData.value.funding}余万元

如需更详细的分析，请告诉我您想了解的具体方面。`
}

const cleanMarkdown = (text) => {
  if (!text) return text
  let result = text
  result = result.replace(/\*\*(.*?)\*\*/g, '$1')
  result = result.replace(/\*(.*?)\*/g, '$1')
  result = result.replace(/^#{1,6}\s+/gm, '')
  result = result.replace(/^- /gm, '• ')
  result = result.replace(/^\+ /gm, '• ')
  result = result.replace(/^> /gm, '')
  result = result.replace(/`(.*?)`/g, '$1')
  result = result.replace(/```[\s\S]*?```/g, '')
  result = result.replace(/\[(.*?)\]\(.*?\)/g, '$1')
  result = result.replace(/^---+$/gm, '')
  return result.trim()
}

// 知识库优先：命中官网/制度原文时直接给带引用的答案，避免大模型脱离资料编造
// 只有“文档类/教师类/成果类”问题才先走知识库；
// 在院生、男女比例、预算执行率这类指标问题仍用大屏的实时数字回答，避免口径混用。
const KB_HINTS = ['通知', '公告', '制度', '规定', '办法', '细则', '学籍', '奖助', '奖学金',
  '评审', '培养方案', '博士后', '教师', '老师', '职称', '研究方向', '成果', '论文',
  '著作', '获奖', '招聘', '申报', '条件', '资格', '官网', '简介', '招生', '录取', '师资']

const shouldUseKB = (q) => KB_HINTS.some(k => q.includes(k))

const tryKnowledgeBase = async (question) => {
  if (!shouldUseKB(question)) return null
  try {
    const r = await fetch('/kb/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    })
    if (!r.ok) return null
    const d = await r.json()
    const cites = d.citations || []
    if (!cites.length) return null
    // 知识库明确说没收录时，交给大模型按大屏数据兜底，别把“未收录”直接甩给用户
    if ((d.answer || '').includes('没有检索到')) return null
    let text = d.answer || ''
    text += '\n\n参考来源：\n' + cites.slice(0, 5).map((c, i) =>
      `[${i + 1}] ${c.title}（${c.source}）${c.url ? ' ' + c.url : ''}`).join('\n')
    return text.trim()
  } catch (e) {
    return null
  }
}

const callAI = async (prompt) => {
  try {
    isTyping.value = true

    const response = await fetch(AI_PROXY_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        system_prompt: SYSTEM_PROMPT,
        message: prompt,
      })
    })

    if (!response.ok) {
      throw new Error(`Proxy request failed: ${response.status}`)
    }

    const data = await response.json()
    const content = data.content || ''
    if (!content) {
      throw new Error('Empty response from proxy')
    }
    return cleanMarkdown(content)
  } catch (error) {
    console.log('AI proxy unavailable, falling back to local mock. Error:', error.message)
    return getMockAnswer(prompt)
  } finally {
    isTyping.value = false
  }
}

const sendQuestion = async (question) => {
  inputText.value = question
  await sendMessage()
}

const sendMessage = async () => {
  if (!inputText.value.trim() || isTyping.value) return

  const question = inputText.value.trim()
  addMessage('user', question)
  inputText.value = ''

  let prompt = question
  if (activeTab.value === 'qa') {
    const context = `当前学院数据（全院口径，来源：学院官网）：
    - 全院在校生：${currentData.value.students}人（本科 ${currentData.value.undergrad} / 硕士 ${currentData.value.master} / 博士 ${currentData.value.doctor}，按官网招生规模×标准学制估算）
    - 专任教师：${currentData.value.staff}人
    - 近五年科研项目：${currentData.value.projects}项
    - 近五年科研经费：${currentData.value.funding}余万元
    - 说明：就业率、分省生源、男女比例、年度预算执行等官网未公布，回答时不要编造具体数值。
    
    请根据以上数据回答用户问题。`
    prompt = `${context}\n用户问题：${question}`
  }

  // 先查知识库（官网/制度原文，带引用）；没有命中再交给大模型
  let answer = await tryKnowledgeBase(question)
  if (!answer) {
    answer = await callAI(prompt)
  }
  addMessage('assistant', answer)
}

const interpretReport = async (type) => {
  activeTab.value = 'qa'
  
  let prompt = ''
  switch (type) {
    case 'overview':
      prompt = `请对山东大学政治学与公共管理学院的综合概览进行解读（数据均为学院官网口径）：
      - 全院在校生：${currentData.value.students}人（本科 ${currentData.value.undergrad} / 硕士 ${currentData.value.master} / 博士 ${currentData.value.doctor}，按官网年招生规模×标准学制估算）
      - 专任教师：${currentData.value.staff}人
      - 近五年科研项目：${currentData.value.projects}项
      - 近五年科研经费：${currentData.value.funding}余万元
      请给出专业的分析和建议。`
      break
    case 'students':
      prompt = `请对山东大学政治学与公共管理学院的学生数据（全院口径）进行解读：
      - 全院在校生：${currentData.value.students}人
      - 本科在校生：${currentData.value.undergrad}人（官网每年招收 150 人 × 4 年学制）
      - 硕士在校生：${currentData.value.master}人（学术硕士 120/年×3 年 + MPA 400/年×3 年）
      - 博士在校生：${currentData.value.doctor}人（官网 35/年×4 年）
      - 官网未公布分省生源与男女比例，请勿编造
      请给出专业的分析和建议。`
      break
    case 'research':
      prompt = `请对山东大学政治学与公共管理学院的科研数据进行解读（官网《学院简介》口径）：
      - 近五年科研项目：${currentData.value.projects}项（国家社科重大/教育部重大攻关 10 余项、国家社科基金 30 余项、国自然 10 余项、部委项目 50 多项）
      - 近五年科研经费：${currentData.value.funding}余万元
      - 官网未公布年度预算执行数据，请勿编造
      请给出专业的分析和建议。`
      break
  }

  addMessage('user', `请${type === 'overview' ? '解读综合概览' : type === 'students' ? '分析学生数据' : '分析科研经费'}`)
  const answer = await callAI(prompt)
  addMessage('assistant', answer)
}

onMounted(() => {
  addMessage('assistant', '您好！我是政管AI助手，很高兴为您服务。您可以提问关于学院数据的问题，或选择报表解读和异常预警功能。')
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  bottom: 100px;
  right: 30px;
  z-index: 9999;
}

.ai-toggle-btn {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border: none;
  font-size: 28px;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4);
  transition: all 0.3s ease;
}

.ai-toggle-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 30px rgba(0, 212, 255, 0.6);
}

.ai-panel {
  position: absolute;
  bottom: 80px;
  right: 0;
  width: 420px;
  height: 600px;
  background: rgba(10, 31, 68, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-icon {
  font-size: 32px;
}

.ai-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ai-title h3 {
  font-size: 18px;
  color: #fff;
  margin: 0;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #52c41a;
  border-radius: 50%;
  margin-right: 6px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.panel-tabs {
  display: flex;
  gap: 8px;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
}

.tab-btn {
  flex: 1;
  padding: 8px 16px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  background: rgba(0, 212, 255, 0.2);
}

.tab-btn.active {
  background: rgba(0, 212, 255, 0.3);
  border-color: rgba(0, 212, 255, 0.6);
  color: #00d4ff;
}

.panel-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.qa-section,
.report-section,
.warning-section {
  height: 100%;
}

.quick-questions {
  margin-bottom: 20px;
}

.quick-title {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 12px;
  display: block;
}

.question-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.question-tag {
  padding: 6px 14px;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 16px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.question-tag:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.5);
  color: #00d4ff;
}

.report-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.report-item:hover {
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.3);
}

.report-icon {
  font-size: 32px;
}

.report-info {
  flex: 1;
}

.report-name {
  font-size: 15px;
  color: #fff;
  font-weight: 600;
  margin-bottom: 4px;
}

.report-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.warning-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.warning-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
}

.warning-item.danger {
  background: rgba(255, 77, 79, 0.1);
  border: 1px solid rgba(255, 77, 79, 0.3);
}

.warning-item.warning {
  background: rgba(250, 173, 20, 0.1);
  border: 1px solid rgba(250, 173, 20, 0.3);
}

.warning-item.info {
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.3);
}

.warning-icon {
  font-size: 24px;
}

.warning-content {
  flex: 1;
}

.warning-title {
  font-size: 14px;
  color: #fff;
  font-weight: 600;
  margin-bottom: 4px;
}

.warning-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 6px;
}

.warning-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(0, 212, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: rgba(123, 44, 191, 0.2);
}

.message-content {
  flex: 1;
}

.message-text {
  font-size: 14px;
  color: #fff;
  line-height: 1.6;
  padding: 12px 16px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 12px;
  margin-bottom: 6px;
}

.message.user .message-text {
  background: rgba(123, 44, 191, 0.2);
}

.message-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.typing-dots {
  display: flex;
  gap: 4px;
}

.typing-dots span {
  width: 6px;
  height: 6px;
  background: rgba(0, 212, 255, 0.6);
  border-radius: 50%;
  animation: typing 1.4s ease-in-out infinite;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

.panel-input {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid rgba(0, 212, 255, 0.2);
}

.panel-input textarea {
  flex: 1;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 12px;
  color: #fff;
  font-size: 14px;
  padding: 12px;
  resize: none;
  outline: none;
  font-family: inherit;
  max-height: 100px;
  min-height: 44px;
}

.panel-input textarea::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.send-btn {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
