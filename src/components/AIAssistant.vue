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
      students: 1320,
      staff: 93,
      projects: 307,
      funding: 4000,
      budget: 910,
      maleRatio: 38.03,
      femaleRatio: 61.97
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
  students: props.realData.students || 1320,
  staff: props.realData.staff || 93,
  projects: props.realData.projects || 307,
  funding: props.realData.funding || 4000,
  budget: props.realData.budget || 910,
  maleRatio: props.realData.maleRatio || 38.03,
  femaleRatio: props.realData.femaleRatio || 61.97
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

const API_CONFIG = {
  baseURL: 'https://api.eppppp.top/v1/chat/completions',
  apiKey: 'sk-MoyiQoIBOjVhdlyDIPZoKipSmyRVhlt5U2KhhYFke43KJsla',
  model: '[按次]deepseek-ai/DeepSeek-V3.2'
}

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
  '在院生总数': () => `根据当前数据，山东大学政治学与公共管理学院在院生总数为${currentData.value.students}人，包括本科生、硕士生、博士生和MPA专业硕士。`,
  '教职工总数': () => `学院现有专任教职工${currentData.value.staff}人，其中教授约25人，副教授约40人，讲师约28人。`,
  '科研项目': () => `当前在研项目共${currentData.value.projects}项，其中国家级项目约35项，省部级项目约80项，横向合作项目约90项。`,
  '科研经费': () => `五年科研经费达${currentData.value.funding}万元，年度科研经费约${Math.floor(currentData.value.funding / 5)}万元。`,
  '预算执行': () => `年度预算执行${currentData.value.budget}万元，执行率保持在良好水平，建议继续保持。`,
  '男女比例': () => `学院男女比例为男生${currentData.value.maleRatio}%，女生${currentData.value.femaleRatio}%。女生比例较高是政管类专业的普遍特点。`,
  '生源分布': '生源地分布以山东省为主，占比约25%。其次是河南、江苏、广东、浙江等省份。国际化程度逐年提升，现有国际学生170人。',
  '就业率': '近五年平均就业率保持在92%以上，其中进入公职单位的比例约45%，企业就业约35%，继续深造约15%，其他约5%。',
  '专业人数': '全院共有8个主要专业方向。其中MPA规模最大约300人，行政管理约210人，政治学类约550人，公共管理类约900人。',
  '师资结构': '专任教师中，35岁以下青年教师占比25%，45岁以下中青年教师占比65%。具有博士学位的教师比例达98%。',
  '综合分析': () => `学院整体运行状况良好。在院生规模${currentData.value.students}人稳定，科研经费${currentData.value.funding}万元充足，师资结构合理。`,
  '招生情况': '2026年招生情况良好，本科生招生计划完成率98%，研究生招生计划完成率102%。国际政治专业略有下降，需关注。',
  '发展建议': '建议如下：1.加快科研经费执行进度，提高资金使用效率；2.加强青年教师引进和培养，优化师资队伍结构；3.优化招生宣传策略，稳定各专业生源规模；4.推进国际化合作交流，提升学院国际影响力。'
}

const getMockAnswer = (question) => {
  const keywords = Object.keys(mockAnswers)
  for (const keyword of keywords) {
    if (question.includes(keyword)) {
      const answer = mockAnswers[keyword]
      return typeof answer === 'function' ? answer() : answer
    }
  }
  
  return `根据学院数据，我来为您分析：

当前核心指标：
1. 在院生总数：${currentData.value.students}人
2. 专任教职工：${currentData.value.staff}人
3. 在研项目数：${currentData.value.projects}项
4. 五年科研经费：${currentData.value.funding}万元
5. 年度预算执行：${currentData.value.budget}万元
6. 男女比例：男${currentData.value.maleRatio}% / 女${currentData.value.femaleRatio}%

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

const callAI = async (prompt) => {
  try {
    isTyping.value = true

    const response = await fetch(API_CONFIG.baseURL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${API_CONFIG.apiKey}`
      },
      body: JSON.stringify({
        model: API_CONFIG.model,
        messages: [
          {
            role: 'system',
            content: SYSTEM_PROMPT
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.7,
        max_tokens: 1000
      })
    })

    if (!response.ok) {
      throw new Error('API请求失败')
    }

    const data = await response.json()
    return cleanMarkdown(data.choices[0].message.content)
  } catch (error) {
    console.log('使用本地模拟数据回答')
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
    const context = `当前学院数据：
    - 在院生总数：${currentData.value.students}人
    - 专任教职工：${currentData.value.staff}人
    - 在研项目数：${currentData.value.projects}项
    - 五年科研经费：${currentData.value.funding}万元
    - 年度预算执行：${currentData.value.budget}万元
    - 男女比例：男生${currentData.value.maleRatio}%，女生${currentData.value.femaleRatio}%
    
    请根据以上数据回答用户问题。`
    prompt = `${context}\n用户问题：${question}`
  }

  const answer = await callAI(prompt)
  addMessage('assistant', answer)
}

const interpretReport = async (type) => {
  activeTab.value = 'qa'
  
  let prompt = ''
  switch (type) {
    case 'overview':
      prompt = `请对山东大学政治学与公共管理学院的综合概览进行解读：
      - 在院生总数：${currentData.value.students}人
      - 专任教职工：${currentData.value.staff}人
      - 在研项目数：${currentData.value.projects}项
      - 五年科研经费：${currentData.value.funding}万元
      - 年度预算执行：${currentData.value.budget}万元
      请给出专业的分析和建议。`
      break
    case 'students':
      prompt = `请对山东大学政治学与公共管理学院的学生数据进行解读：
      - 在院生总数：${currentData.value.students}人
      - 男女比例：男生${currentData.value.maleRatio}%，女生${currentData.value.femaleRatio}%
      - 生源分布：山东省最多，占比约25%
      - 专业分布：行政管理、政治学、国际政治、公共管理等
      请给出专业的分析和建议。`
      break
    case 'research':
      prompt = `请对山东大学政治学与公共管理学院的科研数据进行解读：
      - 在研项目数：${currentData.value.projects}项
      - 五年科研经费：${currentData.value.funding}万元
      - 年度预算执行：${currentData.value.budget}万元
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
