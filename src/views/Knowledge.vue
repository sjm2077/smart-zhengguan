<template>
  <div class="kb-page">
    <!-- 顶部说明条：数据来源与检索方式如实标注 -->
    <div class="kb-banner">
      <div class="banner-left">
        <span class="banner-icon">🧠</span>
        <div class="banner-text">
          <h2>知识库 & 智能体</h2>
          <p>
            <span class="tag official">学院官网真实爬取</span>
            <span class="tag official">研究生制度文件</span>
            <span class="tag sub">论文题录 CSV</span>
            <span class="tag plain">检索方式：BM25 关键词（非向量语义检索）</span>
          </p>
        </div>
      </div>
      <div class="banner-right">
        <div class="stat">
          <span class="stat-num">{{ status.doc_count || 0 }}</span>
          <span class="stat-label">文档</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ status.chunk_count || 0 }}</span>
          <span class="stat-label">分块</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ status.vocab || 0 }}</span>
          <span class="stat-label">词表</span>
        </div>
        <div class="mode" :class="modeClass">{{ modeText }}</div>
      </div>
    </div>

    <div v-if="offline" class="offline-tip">
      知识库服务未启动（127.0.0.1:8900）。启动命令：
      <code>python kb_service\server.py</code>
    </div>

    <!-- 数据覆盖：如实说明每类采集到多少，而不是只报“总量” -->
    <div class="coverage">
      <span class="cov-item"><b>{{ status.faculty_count || 0 }}</b> 位教师名录</span>
      <span class="cov-item"><b>{{ (status.corpus && status.corpus.teacher_profiles) || 0 }}</b> 份个人主页详情</span>
      <span class="cov-item"><b>{{ (status.achievement && status.achievement.total) || 0 }}</b> 条学术成果</span>
      <span class="cov-item"><b>{{ (status.corpus && status.corpus.notices_with_body) || 0 }}</b> 篇通知正文</span>
      <span class="cov-item"><b>{{ (status.corpus && status.corpus.papers) || 0 }}</b> 篇论文题录</span>
      <span class="cov-note">全部来自 pspa.sdu.edu.cn 官网爬取与 CSV 题录，未使用任何模拟数据</span>
    </div>

    <div class="kb-body">
      <!-- 左：知识库检索 -->
      <section class="panel search-panel">
        <div class="panel-head">
          <h3>知识库检索</h3>
          <span class="hint">来源：官网通知/成果/教师/简介 + 制度文件</span>
        </div>

        <div class="search-row">
          <input
            v-model="query"
            class="search-input"
            placeholder="例如：博士后招收条件 / 奖学金评审 / 国家社科项目"
            @keyup.enter="doSearch"
          />
          <button class="btn primary" :disabled="searching" @click="doSearch">
            {{ searching ? '检索中' : '检索' }}
          </button>
        </div>

        <div class="filter-row">
          <button
            v-for="t in types"
            :key="t.value"
            class="chip"
            :class="{ active: docType === t.value }"
            @click="switchType(t.value)"
          >
            {{ t.label }}
          </button>
        </div>

        <div class="result-list">
          <div v-if="!results.length && searched" class="empty">没有命中，换个关键词试试</div>
          <div v-for="(r, i) in results" :key="i" class="result-item">
            <div class="result-head">
              <span class="result-title">{{ r.title }}</span>
              <span class="result-score">{{ r.score }}</span>
            </div>
            <div class="result-meta">
              <span class="tag sub">{{ r.source }}</span>
              <span v-if="r.date" class="date">{{ r.date }}</span>
            </div>
            <p class="result-text">{{ r.text }}</p>
            <a v-if="r.url" :href="r.url" target="_blank" class="result-link">查看原文 ↗</a>
          </div>
        </div>
      </section>

      <!-- 右：智能体问答 -->
      <section class="panel ask-panel">
        <div class="panel-head">
          <h3>智能体问答</h3>
          <span class="hint">规划 → 调工具 → 生成，回答附引用</span>
        </div>

        <div class="quick-row">
          <button
            v-for="q in quickQuestions"
            :key="q"
            class="chip small"
            @click="ask(q)"
          >{{ q }}</button>
        </div>

        <div class="chat-list" ref="chatRef">
          <div v-if="!messages.length" class="empty">
            试着问：学院的师资与科研规模如何？博士后招收条件是什么？李老师是什么职称？
          </div>
          <div v-for="(m, i) in messages" :key="i" class="msg" :class="m.role">
            <div class="msg-role">{{ m.role === 'user' ? '我' : '智能体' }}</div>
            <div class="msg-body">
              <div class="msg-text">{{ m.text }}</div>
              <div v-if="m.meta" class="msg-meta">
                <span v-if="m.meta.mode" class="tag" :class="m.meta.mode === 'llm' ? 'official' : 'plain'">
                  {{ m.meta.mode === 'llm' ? '大模型生成' : '纯检索摘录' }}
                </span>
                <span v-if="m.meta.tools && m.meta.tools.length" class="tag plain">
                  工具：{{ m.meta.tools.join(' / ') }}
                </span>
              </div>
              <div v-if="m.citations && m.citations.length" class="cite-list">
                <div v-for="(c, ci) in m.citations" :key="ci" class="cite-item">
                  <span class="cite-no">[{{ ci + 1 }}]</span>
                  <span class="cite-title">{{ c.title }}</span>
                  <span class="cite-src">{{ c.source }}<template v-if="c.date"> · {{ c.date }}</template></span>
                  <a v-if="c.url" :href="c.url" target="_blank" class="cite-link">原文 ↗</a>
                </div>
              </div>
            </div>
          </div>
          <div v-if="asking" class="msg assistant">
            <div class="msg-role">智能体</div>
            <div class="msg-body"><div class="msg-text typing">正在检索知识库…</div></div>
          </div>
        </div>

        <div class="ask-row">
          <input
            v-model="question"
            class="search-input"
            placeholder="输入问题，Enter 发送"
            @keyup.enter="ask()"
          />
          <button class="btn" :disabled="asking" @click="ask()">发送</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'

const KB_BASE = '/kb'

const status = ref({})
const offline = ref(false)
const query = ref('')
const docType = ref('')
const results = ref([])
const searching = ref(false)
const searched = ref(false)

const question = ref('')
const asking = ref(false)
const messages = ref([])
const chatRef = ref(null)

const types = [
  { label: '全部', value: '' },
  { label: '通知公告', value: 'notice' },
  { label: '制度文件', value: 'policy' },
  { label: '学术成果', value: 'achievement' },
  { label: '教师名录', value: 'faculty' },
  { label: '论文题录', value: 'paper' },
  { label: '学院简介', value: 'profile' }
]

const quickQuestions = [
  '学院师资和科研规模如何？',
  '学院官网学术成果每年有多少条？',
  '费立国老师的研究方向是什么？',
  '博士后招收条件是什么？',
  '研究生奖学金评审有哪些要求？'
]

const modeText = computed(() => {
  if (status.value.llm_mode === 'direct') return '大模型直连'
  if (status.value.llm_mode === 'proxy') return '大模型代理'
  return '纯检索模式'
})
const modeClass = computed(() => (status.value.llm ? 'llm' : 'retrieval'))

const getJSON = async (url, options) => {
  const r = await fetch(url, options)
  if (!r.ok) throw new Error('HTTP ' + r.status)
  return r.json()
}

const loadStatus = async () => {
  try {
    status.value = await getJSON(KB_BASE + '/stats')
    offline.value = false
  } catch (e) {
    offline.value = true
  }
}

const doSearch = async () => {
  const q = query.value.trim()
  if (!q) return
  searching.value = true
  searched.value = true
  try {
    const params = new URLSearchParams({ q, topk: '8' })
    if (docType.value) params.set('type', docType.value)
    const d = await getJSON(KB_BASE + '/search?' + params.toString())
    results.value = d.data || []
    offline.value = false
  } catch (e) {
    offline.value = true
    results.value = []
  } finally {
    searching.value = false
  }
}

const switchType = (t) => {
  docType.value = t
  if (query.value.trim()) doSearch()
}

const scrollChat = () => {
  nextTick(() => {
    if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  })
}

const ask = async (preset) => {
  const q = (preset || question.value).trim()
  if (!q || asking.value) return
  if (!preset) question.value = ''
  messages.value.push({ role: 'user', text: q })
  asking.value = true
  scrollChat()
  try {
    const d = await getJSON(KB_BASE + '/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    })
    messages.value.push({
      role: 'assistant',
      text: d.answer || '（空回答）',
      meta: { mode: d.mode, tools: d.tools_used || [] },
      citations: d.citations || []
    })
    offline.value = false
  } catch (e) {
    offline.value = true
    messages.value.push({
      role: 'assistant',
      text: '知识库服务未响应：' + e.message + '\n请先启动：python kb_service\\server.py',
      meta: { mode: 'retrieval', tools: [] },
      citations: []
    })
  } finally {
    asking.value = false
    scrollChat()
  }
}

onMounted(loadStatus)
</script>

<style scoped>
.kb-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 14px 14px;
  overflow: hidden;
  color: #e6f7ff;
}

/* 顶部说明条 */
.kb-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: linear-gradient(90deg, rgba(0, 212, 255, 0.1), rgba(123, 44, 191, 0.1));
  border: 1px solid rgba(0, 212, 255, 0.22);
  border-radius: 10px;
}
.banner-left { display: flex; align-items: center; gap: 12px; }
.banner-icon { font-size: 26px; }
.banner-text h2 { margin: 0 0 4px; font-size: 17px; letter-spacing: 1px; }
.banner-text p { margin: 0; display: flex; flex-wrap: wrap; gap: 6px; }
.banner-right { display: flex; align-items: center; gap: 18px; }
.stat { display: flex; flex-direction: column; align-items: center; }
.stat-num { font-size: 18px; font-weight: 700; color: #00d4ff; }
.stat-label { font-size: 11px; color: rgba(255, 255, 255, 0.55); }
.mode {
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 12px;
  border: 1px solid currentColor;
}
.mode.llm { color: #52c41a; background: rgba(82, 196, 26, 0.1); }
.mode.retrieval { color: #faad14; background: rgba(250, 173, 20, 0.1); }

.tag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 8px;
  border: 1px solid currentColor;
  white-space: nowrap;
}
.tag.official { color: #52c41a; background: rgba(82, 196, 26, 0.08); }
.tag.sub { color: #00d4ff; background: rgba(0, 212, 255, 0.08); }
.tag.plain { color: rgba(255, 255, 255, 0.6); background: rgba(255, 255, 255, 0.05); }

.offline-tip {
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(250, 173, 20, 0.4);
  background: rgba(250, 173, 20, 0.1);
  color: #faad14;
  font-size: 12px;
}
.offline-tip code { color: #fff; background: rgba(0, 0, 0, 0.3); padding: 1px 5px; border-radius: 4px; }

/* 数据覆盖条 */
.coverage {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 14px;
  padding: 7px 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
}
.cov-item b { color: #00d4ff; font-size: 14px; margin-right: 2px; }
.cov-note { margin-left: auto; font-size: 11px; color: rgba(255, 255, 255, 0.4); }

/* 主体两栏 */
.kb-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: rgba(16, 32, 64, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 10px;
  padding: 12px 14px;
}
.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}
.panel-head h3 {
  margin: 0;
  font-size: 14px;
  letter-spacing: 1px;
  padding-left: 8px;
  border-left: 3px solid #00d4ff;
}
.hint { font-size: 11px; color: rgba(255, 255, 255, 0.45); }

.search-row, .ask-row { display: flex; gap: 8px; }
/* 右下角为全局 AI 助手悬浮按钮预留安全区，避免“发送”按钮被机器人图标遮挡 */
.ask-row { padding-right: 72px; }
.search-input {
  flex: 1;
  min-width: 0;
  padding: 8px 12px;
  font-size: 13px;
  color: #fff;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 212, 255, 0.25);
  border-radius: 6px;
  outline: none;
}
.search-input:focus { border-color: rgba(0, 212, 255, 0.6); }
.search-input::placeholder { color: rgba(255, 255, 255, 0.35); }

.btn {
  padding: 8px 16px;
  font-size: 13px;
  color: #00d4ff;
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.45);
  border-radius: 6px;
  cursor: pointer;
}
.btn:hover:not(:disabled) { background: rgba(0, 212, 255, 0.2); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn.primary { color: #04121f; background: #00d4ff; border-color: #00d4ff; font-weight: 600; }

.filter-row, .quick-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
.chip {
  font-size: 12px;
  padding: 4px 10px;
  color: rgba(255, 255, 255, 0.7);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  cursor: pointer;
}
.chip:hover { border-color: rgba(0, 212, 255, 0.5); color: #00d4ff; }
.chip.active { color: #04121f; background: #00d4ff; border-color: #00d4ff; font-weight: 600; }
.chip.small { font-size: 11px; }

.result-list, .chat-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-right: 4px;
}
.result-list::-webkit-scrollbar, .chat-list::-webkit-scrollbar { width: 5px; }
.result-list::-webkit-scrollbar-thumb, .chat-list::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: 3px;
}

.empty { color: rgba(255, 255, 255, 0.4); font-size: 12px; padding: 16px 4px; line-height: 1.8; }

.result-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.12);
  border-radius: 8px;
}
.result-item:hover { border-color: rgba(0, 212, 255, 0.35); }
.result-head { display: flex; justify-content: space-between; gap: 8px; }
.result-title { font-size: 13px; font-weight: 600; color: #fff; }
.result-score { font-size: 11px; color: #00d4ff; white-space: nowrap; }
.result-meta { display: flex; gap: 8px; align-items: center; margin: 5px 0; }
.date, .cite-src { font-size: 11px; color: rgba(255, 255, 255, 0.45); }
.result-text {
  margin: 0 0 6px;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.72);
}
.result-link, .cite-link { font-size: 11px; color: #00d4ff; text-decoration: none; }

.msg { display: flex; gap: 8px; margin-bottom: 14px; }
.msg-role {
  flex-shrink: 0;
  width: 40px;
  font-size: 11px;
  text-align: center;
  padding-top: 3px;
  color: rgba(255, 255, 255, 0.45);
}
.msg.user .msg-role { color: #00d4ff; }
.msg-body { flex: 1; min-width: 0; }
.msg-text {
  font-size: 12.5px;
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(0, 212, 255, 0.12);
}
.msg.user .msg-text { background: rgba(0, 212, 255, 0.12); border-color: rgba(0, 212, 255, 0.3); }
.msg-text.typing { color: rgba(255, 255, 255, 0.5); }
.msg-meta { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }

.cite-list { margin-top: 8px; display: flex; flex-direction: column; gap: 5px; }
.cite-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 11px;
  padding: 5px 8px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 6px;
}
.cite-no { color: #00d4ff; }
.cite-title { color: rgba(255, 255, 255, 0.85); }
.cite-src { margin-left: auto; }

@media (max-width: 1200px) {
  .kb-body { grid-template-columns: 1fr; }
  .kb-banner { flex-direction: column; align-items: flex-start; }
}
</style>
