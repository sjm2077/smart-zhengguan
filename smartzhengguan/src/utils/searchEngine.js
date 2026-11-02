import {
  academicChangeMockData,
  academicStatusMockData,
  admissionMockData,
  changePasswordMockData,
  degreeDefenseMockData,
  degreeMockData,
  employmentMockData,
  homeMockData,
  intelligentPredictionMockData,
  personalCenterMockData,
  scholarshipMockData,
  systemSettingsMockData,
  trainingCourseMockData,
  trainingMockData,
} from '../mock/graduateManagementMock'
import { formatMetricValue, queryRecords } from './queryData'

const SEARCH_HISTORY_KEY = 'graduate-global-search-history'
const MAX_HISTORY = 8

const KIND_LABELS = {
  module: '功能入口',
  record: '业务记录',
  notice: '通知待办',
  analysis: '跨模块汇总',
}

const KIND_ACTIONS = {
  module: '进入模块',
  record: '查看模块',
  notice: '前往查看',
  analysis: '查看汇总',
}

const KIND_PRIORITY = {
  module: 0,
  record: 1,
  notice: 2,
  analysis: 3,
}

const DEFAULT_SEARCH_KEYWORDS = [
  '2024级',
  '博士',
  '休学',
  '待审核',
  '答辩',
  '奖学金',
  '高风险',
  '行政管理',
]

const MODULE_DEFINITIONS = [
  {
    key: 'home',
    title: '首页',
    route: '/home',
    description: '查看学院研究生总体概况、通知和待办。',
    keywords: ['首页', '总览', '概况', '通知', '待办', 'dashboard'],
  },
  {
    key: 'admission',
    title: '招生管理',
    route: '/admission',
    description: '覆盖报名、复试、拟录取和招生计划。',
    keywords: ['招生', '报名', '复试', '录取', '拟录取', '调剂'],
  },
  {
    key: 'academic-status',
    title: '学籍管理',
    route: '/academic-status',
    description: '查看学籍总览、注册状态和异动情况。',
    keywords: ['学籍', '注册', '在籍', '异动', '休学', '复学', '退学'],
  },
  {
    key: 'academic-change',
    title: '学籍异动管理',
    route: '/academic-change',
    description: '处理休学、复学、延期毕业和专业变更。',
    keywords: ['异动', '休学', '复学', '延期毕业', '专业变更'],
  },
  {
    key: 'training',
    title: '培养管理',
    route: '/training',
    description: '查看培养计划、进度和培养环节执行情况。',
    keywords: ['培养', '培养计划', '开题', '中期', '论文进度'],
  },
  {
    key: 'training-course',
    title: '课程与培养环节',
    route: '/training-course',
    description: '管理排课、课程执行和培养环节预警。',
    keywords: ['课程', '排课', '培养环节', '课表', '成绩', '开题', '中期'],
  },
  {
    key: 'degree',
    title: '学位管理',
    route: '/degree',
    description: '查看学位申请、论文评阅和授予情况。',
    keywords: ['学位', '论文', '评阅', '授予', '毕业'],
  },
  {
    key: 'degree-defense',
    title: '答辩管理',
    route: '/degree-defense',
    description: '统一处理答辩场次、专家安排和结果回收。',
    keywords: ['答辩', '场次', '会场', '专家', '答辩安排'],
  },
  {
    key: 'scholarship',
    title: '奖助管理',
    route: '/scholarship',
    description: '查看奖学金、助学金和资助覆盖情况。',
    keywords: ['奖助', '奖学金', '助学金', '资助', '国家奖学金'],
  },
  {
    key: 'employment',
    title: '就业管理',
    route: '/employment',
    description: '查看就业率、签约率和就业去向。',
    keywords: ['就业', '签约', '招聘', '去向', '升学', '出国'],
  },
  {
    key: 'intelligent-prediction',
    title: '智能预测',
    route: '/intelligent-prediction',
    description: '跟踪风险预警、发展指数和关键影响因素。',
    keywords: ['智能预测', '预警', '风险', '高风险', '发展指数', 'AI'],
  },
  {
    key: 'system',
    title: '系统设置',
    route: '/system',
    description: '维护业务参数、消息模板和开放时间。',
    keywords: ['系统', '设置', '配置', '模板', '开放时间'],
  },
  {
    key: 'personal',
    title: '个人中心',
    route: '/personal',
    description: '查看个人资料、快捷入口和操作日志。',
    keywords: ['个人中心', '资料', '个人', '日志', '快捷入口'],
  },
  {
    key: 'change-pwd',
    title: '修改密码',
    route: '/change-pwd',
    description: '处理密码更新和账户安全校验。',
    keywords: ['密码', '安全', '修改密码', '账户安全'],
  },
]

const SEARCH_INDEX = buildSearchIndex()

export { DEFAULT_SEARCH_KEYWORDS, SEARCH_HISTORY_KEY }

export function normalizeSearchKeyword(keyword) {
  return String(keyword || '').trim().toLowerCase().replace(/\s+/g, ' ')
}

export function splitSearchTokens(keyword) {
  return normalizeSearchKeyword(keyword)
    .split(/[\s,，、;；/|]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

export function getSearchHistory() {
  if (typeof window === 'undefined') return []

  try {
    const parsed = JSON.parse(localStorage.getItem(SEARCH_HISTORY_KEY) || '[]')
    return Array.isArray(parsed)
      ? parsed.map((item) => String(item || '').trim()).filter(Boolean).slice(0, MAX_HISTORY)
      : []
  } catch (error) {
    console.warn('搜索历史读取失败', error)
    return []
  }
}

export function saveSearchHistory(keyword) {
  const text = String(keyword || '').trim()
  if (!text || typeof window === 'undefined') return

  const next = [text, ...getSearchHistory().filter((item) => item !== text)].slice(0, MAX_HISTORY)
  localStorage.setItem(SEARCH_HISTORY_KEY, JSON.stringify(next))
}

export function clearSearchHistory() {
  if (typeof window === 'undefined') return
  localStorage.removeItem(SEARCH_HISTORY_KEY)
}

export function getDefaultSearchSuggestions() {
  const history = getSearchHistory()
  return [...history, ...DEFAULT_SEARCH_KEYWORDS.filter((item) => !history.includes(item))].slice(0, MAX_HISTORY)
}

export function getQuickSuggestions(keyword, limit = 8) {
  return searchEverything(keyword).flatResults.slice(0, limit)
}

export function findBestRoute(keyword) {
  const result = searchEverything(keyword)
  const target = result.modules[0] || result.flatResults[0]

  if (!target) return null

  return {
    path: target.route,
    query: target.routeQuery || {},
  }
}

export function searchEverything(keyword) {
  const text = String(keyword || '').trim()
  const normalized = normalizeSearchKeyword(text)
  const tokens = splitSearchTokens(text)

  if (!normalized) {
    return {
      keyword: '',
      total: 0,
      modules: [],
      records: [],
      notices: [],
      analysis: [],
      flatResults: [],
    }
  }

  const scored = SEARCH_INDEX
    .map((item) => ({
      ...item,
      score: calculateDocumentScore(item, normalized, tokens),
    }))
    .filter((item) => item.score > 0)
    .sort(compareSearchResults)

  return {
    keyword: text,
    total: scored.length,
    modules: scored.filter((item) => item.kind === 'module'),
    records: scored.filter((item) => item.kind === 'record'),
    notices: scored.filter((item) => item.kind === 'notice'),
    analysis: scored.filter((item) => item.kind === 'analysis'),
    flatResults: scored,
  }
}

function buildSearchIndex() {
  return [
    ...MODULE_DEFINITIONS.map((item) => createDoc({
      kind: 'module',
      moduleName: item.title,
      title: item.title,
      summary: item.description,
      meta: '模块直达',
      route: item.route,
      tags: item.keywords.slice(0, 3),
      searchKeywords: [item.title, ...item.keywords, item.description],
    })),
    ...buildHomeDocs(),
    ...buildAdmissionDocs(),
    ...buildAcademicStatusDocs(),
    ...buildAcademicChangeDocs(),
    ...buildTrainingDocs(),
    ...buildTrainingCourseDocs(),
    ...buildDegreeDocs(),
    ...buildDegreeDefenseDocs(),
    ...buildScholarshipDocs(),
    ...buildEmploymentDocs(),
    ...buildIntelligentPredictionDocs(),
    ...buildSystemDocs(),
    ...buildPersonalDocs(),
    ...buildPasswordDocs(),
    ...buildCrossModuleDocs(),
  ]
}

function buildHomeDocs() {
  return [
    ...createNoticeDocs({
      moduleName: '首页',
      route: '/home',
      items: homeMockData.notices,
      typeLabel: '通知',
    }),
    ...createTodoDocs({
      moduleName: '首页',
      route: '/home',
      items: homeMockData.todos,
    }),
  ]
}

function buildAdmissionDocs() {
  return [
    ...createNoticeDocs({
      moduleName: '招生管理',
      route: '/admission',
      items: admissionMockData.notices,
      typeLabel: '通知',
    }),
  ]
}

function buildAcademicStatusDocs() {
  const records = (academicStatusMockData.records || []).map((item) => createDoc({
    kind: 'record',
    moduleName: '学籍管理',
    title: `${item.name} ${item.id}`,
    summary: `${item.changeType} · ${item.status} · 经办人 ${item.handler}`,
    meta: `${item.reason} · ${item.date}`,
    route: '/academic-status',
    statusText: item.status,
    statusType: item.tagType,
    tags: [item.changeType, item.status],
    searchKeywords: [
      item.name,
      item.id,
      item.changeType,
      item.status,
      item.reason,
      item.handler,
      item.date,
      '学籍',
      '异动',
    ],
  }))

  return records
}

function buildAcademicChangeDocs() {
  return [
    ...(academicChangeMockData.tableCard?.rows || []).map((item) => createDoc({
      kind: 'record',
      moduleName: '学籍异动管理',
      title: `${item.name} ${item.studentId}`,
      summary: `${item.changeType} · ${item.currentStep} · ${item.status}`,
      meta: `提交时间 ${item.submittedAt}`,
      route: '/academic-change',
      statusText: item.status,
      statusType: item.statusType,
      tags: [item.changeType, item.status],
      searchKeywords: [
        item.name,
        item.studentId,
        item.changeType,
        item.currentStep,
        item.status,
        item.submittedAt,
        '学籍异动',
      ],
    })),
    ...createNoticeDocs({
      moduleName: '学籍异动管理',
      route: '/academic-change',
      items: academicChangeMockData.noticeCard?.items,
      typeLabel: '通知',
    }),
    ...createTodoDocs({
      moduleName: '学籍异动管理',
      route: '/academic-change',
      items: academicChangeMockData.todoCard?.items,
    }),
  ]
}

function buildTrainingDocs() {
  return [
    ...(trainingMockData.plans || []).map((item) => createDoc({
      kind: 'record',
      moduleName: '培养管理',
      title: `${item.name} ${item.studentId}`,
      summary: `${item.grade} · ${item.major} · ${item.stage} · ${item.status}`,
      meta: `导师 ${item.advisor} · 完成度 ${item.completion}% · ${item.updatedAt}`,
      route: '/training',
      statusText: item.status,
      statusType: item.tagType,
      tags: [item.grade, item.major, item.stage],
      searchKeywords: [
        item.name,
        item.studentId,
        item.grade,
        item.major,
        item.degreeType,
        item.stage,
        item.advisor,
        item.status,
        item.updatedAt,
        '培养计划',
      ],
    })),
    ...createNoticeDocs({
      moduleName: '培养管理',
      route: '/training',
      items: trainingMockData.notices,
      typeLabel: '通知',
    }),
    ...createTodoDocs({
      moduleName: '培养管理',
      route: '/training',
      items: trainingMockData.todos,
    }),
  ]
}

function buildTrainingCourseDocs() {
  return [
    ...(trainingCourseMockData.tableCard?.rows || []).map((item) => createDoc({
      kind: 'record',
      moduleName: '课程与培养环节',
      title: item.courseName,
      summary: `${item.major} · ${item.teacher} · ${item.schedule}`,
      meta: `状态 ${item.status}`,
      route: '/training-course',
      statusText: item.status,
      statusType: item.statusType,
      tags: [item.major, item.teacher],
      searchKeywords: [
        item.courseName,
        item.teacher,
        item.major,
        item.schedule,
        item.status,
        '课程',
        '排课',
      ],
    })),
    ...createNoticeDocs({
      moduleName: '课程与培养环节',
      route: '/training-course',
      items: trainingCourseMockData.noticeCard?.items,
      typeLabel: '通知',
    }),
    ...createTodoDocs({
      moduleName: '课程与培养环节',
      route: '/training-course',
      items: trainingCourseMockData.todoCard?.items,
    }),
  ]
}

function buildDegreeDocs() {
  return [
    ...createNoticeDocs({
      moduleName: '学位管理',
      route: '/degree',
      items: degreeMockData.notices,
      typeLabel: '通知',
    }),
    ...createTodoDocs({
      moduleName: '学位管理',
      route: '/degree',
      items: degreeMockData.todos,
    }),
  ]
}

function buildDegreeDefenseDocs() {
  return [
    ...(degreeDefenseMockData.tableCard?.rows || []).map((item) => createDoc({
      kind: 'record',
      moduleName: '答辩管理',
      title: item.sessionName,
      summary: `${item.room} · ${item.time} · ${item.status}`,
      meta: `主席 ${item.chair} · 学生 ${item.students} 人`,
      route: '/degree-defense',
      statusText: item.status,
      statusType: item.statusType,
      tags: [item.room, item.time],
      searchKeywords: [
        item.sessionName,
        item.chair,
        item.room,
        item.time,
        item.status,
        '答辩',
      ],
    })),
    ...createNoticeDocs({
      moduleName: '答辩管理',
      route: '/degree-defense',
      items: degreeDefenseMockData.noticeCard?.items,
      typeLabel: '通知',
    }),
    ...createTodoDocs({
      moduleName: '答辩管理',
      route: '/degree-defense',
      items: degreeDefenseMockData.todoCard?.items,
    }),
  ]
}

function buildScholarshipDocs() {
  return [
    ...createKeywordOnlyDocs({
      moduleName: '奖助管理',
      route: '/scholarship',
      items: [
        { title: '奖学金覆盖情况', summary: '支持按奖学金、助学金、资助类型查看奖助数据。', keywords: ['奖学金', '助学金', '国家奖学金', '资助'] },
      ],
    }),
  ]
}

function buildEmploymentDocs() {
  return [
    ...createKeywordOnlyDocs({
      moduleName: '就业管理',
      route: '/employment',
      items: [
        { title: '就业去向统计', summary: '支持按签约、升学、出国和未就业查看就业数据。', keywords: ['就业', '签约', '升学', '出国', '招聘'] },
      ],
    }),
  ]
}

function buildIntelligentPredictionDocs() {
  return [
    ...(intelligentPredictionMockData.students || []).map((item) => createDoc({
      kind: 'record',
      moduleName: '智能预测',
      title: `${item.name} ${item.studentId}`,
      summary: `${item.grade} · ${item.major} · 发展指数分析`,
      meta: `课程均分 ${item.currentSnapshot.courseAverage} · 培养完成率 ${item.currentSnapshot.trainingPlanCompletionRate}% · 逾期任务 ${item.currentSnapshot.overdueTasksCount}`,
      route: '/intelligent-prediction',
      tags: [item.grade, item.major, item.degreeType],
      searchKeywords: [
        item.name,
        item.studentId,
        item.degreeType,
        item.college,
        item.major,
        item.grade,
        '智能预测',
        '预警',
      ],
    })),
    ...(intelligentPredictionMockData.tableCard?.rows || []).map((item) => createDoc({
      kind: 'record',
      moduleName: '智能预测',
      title: `${item.name} ${item.studentId}`,
      summary: `${item.riskLevel} · ${item.riskField}`,
      meta: item.suggestion,
      route: '/intelligent-prediction',
      statusText: item.riskLevel,
      statusType: item.riskType,
      tags: [item.riskLevel],
      searchKeywords: [
        item.name,
        item.studentId,
        item.riskLevel,
        item.riskField,
        item.suggestion,
        '高风险',
        '预警',
      ],
    })),
    ...createNoticeDocs({
      moduleName: '智能预测',
      route: '/intelligent-prediction',
      items: intelligentPredictionMockData.noticeCard?.items,
      typeLabel: 'AI提示',
    }),
    ...createTodoDocs({
      moduleName: '智能预测',
      route: '/intelligent-prediction',
      items: intelligentPredictionMockData.todoCard?.items,
    }),
  ]
}

function buildSystemDocs() {
  return [
    ...(systemSettingsMockData.tableCard?.rows || []).map((item) => createDoc({
      kind: 'record',
      moduleName: '系统设置',
      title: item.item,
      summary: `${item.module} · ${item.owner} · ${item.status}`,
      meta: `更新时间 ${item.updatedAt}`,
      route: '/system',
      statusText: item.status,
      statusType: item.statusType,
      tags: [item.module],
      searchKeywords: [
        item.item,
        item.module,
        item.owner,
        item.status,
        item.updatedAt,
        '系统设置',
        '配置',
      ],
    })),
    ...createNoticeDocs({
      moduleName: '系统设置',
      route: '/system',
      items: systemSettingsMockData.noticeCard?.items,
      typeLabel: '通知',
    }),
    ...createTodoDocs({
      moduleName: '系统设置',
      route: '/system',
      items: systemSettingsMockData.todoCard?.items,
    }),
  ]
}

function buildPersonalDocs() {
  return [
    ...(personalCenterMockData.operationLogs || []).map((item) => createDoc({
      kind: 'record',
      moduleName: '个人中心',
      title: item.action,
      summary: `${item.module} · ${item.status}`,
      meta: item.time,
      route: '/personal',
      statusText: item.status,
      statusType: item.statusType,
      tags: [item.module],
      searchKeywords: [
        item.action,
        item.module,
        item.status,
        item.time,
        '个人中心',
      ],
    })),
  ]
}

function buildPasswordDocs() {
  return [
    ...(changePasswordMockData.passwordLogs || []).map((item) => createDoc({
      kind: 'record',
      moduleName: '修改密码',
      title: item.action,
      summary: `${item.device} · ${item.status}`,
      meta: item.time,
      route: '/change-pwd',
      statusText: item.status,
      statusType: item.statusType,
      tags: ['账户安全'],
      searchKeywords: [
        item.action,
        item.device,
        item.status,
        item.time,
        '密码',
        '安全',
      ],
    })),
  ]
}

function buildCrossModuleDocs() {
  return queryRecords.map((item) => createDoc({
    kind: 'analysis',
    moduleName: item.moduleName,
    title: `${item.grade} ${item.major}`,
    summary: `${item.moduleName} · ${item.metricLabel} ${formatMetricValue(item.metricValue, item.metricUnit)}`,
    meta: `${item.extraLabel} ${formatMetricValue(item.extraValue, item.extraUnit)} · ${item.status}`,
    route: '/query-results',
    routeQuery: {
      grade: item.grade,
      major: item.major,
    },
    statusText: item.status,
    statusType: item.statusType,
    tags: [item.grade, item.major],
    searchKeywords: [
      item.grade,
      item.major,
      item.moduleName,
      item.metricLabel,
      item.extraLabel,
      item.status,
      item.summary,
    ],
  }))
}

function createKeywordOnlyDocs({ moduleName, route, items = [] }) {
  return items.map((item) => createDoc({
    kind: 'record',
    moduleName,
    title: item.title,
    summary: item.summary,
    meta: '可作为搜索入口使用',
    route,
    tags: item.keywords?.slice(0, 3) || [],
    searchKeywords: [item.title, item.summary, ...(item.keywords || [])],
  }))
}

function createNoticeDocs({ moduleName, route, items = [], typeLabel = '通知' }) {
  return (items || []).map((item) => createDoc({
    kind: 'notice',
    moduleName,
    title: item.title,
    summary: `${moduleName}${typeLabel ? ` · ${typeLabel}` : ''}`,
    meta: item.date || item.time || '通知信息',
    route,
    tags: typeLabel ? [typeLabel] : [],
    searchKeywords: [item.title, item.date, item.time, moduleName, typeLabel],
  }))
}

function createTodoDocs({ moduleName, route, items = [] }) {
  return (items || []).map((item) => createDoc({
    kind: 'notice',
    moduleName,
    title: item.label,
    summary: `${moduleName} · 待办事项`,
    meta: `当前数量 ${item.count}`,
    route,
    tags: ['待办'],
    searchKeywords: [item.label, moduleName, '待办', item.count],
  }))
}

function createDoc(item) {
  const tags = uniqueStrings(item.tags || [])
  const keywords = uniqueStrings([
    item.title,
    item.summary,
    item.meta,
    item.moduleName,
    ...(item.searchKeywords || []),
    ...tags,
  ])

  return {
    ...item,
    tags,
    kindLabel: KIND_LABELS[item.kind] || '搜索结果',
    actionLabel: item.actionLabel || KIND_ACTIONS[item.kind] || '查看',
    searchKeywords: keywords,
    searchText: joinSearchText(keywords),
  }
}

function calculateDocumentScore(item, query, tokens) {
  const matchedTokenCount = tokens.filter((token) => item.searchText.includes(token)).length
  const minimalMatchedCount = Math.max(1, Math.ceil(tokens.length * 0.6))

  if (!item.searchText.includes(query) && matchedTokenCount < minimalMatchedCount) {
    return 0
  }

  let score = 0
  score += scoreField(item.title, query, tokens, 16)
  score += scoreField(item.summary, query, tokens, 9)
  score += scoreField(item.meta, query, tokens, 6)
  score += scoreField(item.moduleName, query, tokens, 8)
  score += matchedTokenCount * 6
  score += (item.kind === 'module' ? 8 : 0)

  if (item.statusType === 'danger') score += 2
  if (item.statusType === 'warning') score += 1

  return score
}

function scoreField(value, query, tokens, weight) {
  const text = normalizeSearchKeyword(value)
  if (!text) return 0

  let score = 0

  if (text === query) score += weight * 6
  else if (text.startsWith(query)) score += weight * 4
  else if (text.includes(query)) score += weight * 3

  tokens.forEach((token) => {
    if (!token) return
    if (text === token) score += weight * 3
    else if (text.startsWith(token)) score += weight * 2
    else if (text.includes(token)) score += weight
  })

  return score
}

function compareSearchResults(left, right) {
  if (right.score !== left.score) return right.score - left.score

  const kindDiff = (KIND_PRIORITY[left.kind] ?? 99) - (KIND_PRIORITY[right.kind] ?? 99)
  if (kindDiff !== 0) return kindDiff

  return String(left.title).localeCompare(String(right.title), 'zh-CN')
}

function joinSearchText(values = []) {
  return values
    .flatMap((item) => item == null ? [] : [String(item)])
    .map((item) => normalizeSearchKeyword(item))
    .filter(Boolean)
    .join(' ')
}

function uniqueStrings(values = []) {
  return [...new Set(
    values
      .flatMap((item) => item == null ? [] : [String(item).trim()])
      .filter(Boolean),
  )]
}
