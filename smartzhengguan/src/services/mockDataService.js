import {
  academicChangeMockData,
  academicStatusMockData,
  admissionMockData,
  changePasswordMockData,
  degreeMockData,
  degreeDefenseMockData,
  employmentMockData,
  homeMockData,
  intelligentPredictionMockData,
  personalCenterMockData,
  scholarshipMockData,
  sharedOptions,
  systemSettingsMockData,
  trainingCourseMockData,
  trainingMockData,
} from '../mock/graduateManagementMock'
import {
  buildCrossModuleQueryFallback,
  getQuerySummary,
  getSingleProfileModuleTables,
} from '../utils/queryData'
import { searchEverything } from '../utils/searchEngine'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')

function clone(data) {
  return JSON.parse(JSON.stringify(data))
}

function resolve(data) {
  return Promise.resolve(clone(data))
}

function roundToOne(value) {
  return Number(Number(value || 0).toFixed(1))
}

function parseNumber(value) {
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric : 0
}

function hasMeaningfulRowMetrics(row = {}) {
  return (
    parseNumber(row.awardCount) > 0 ||
    parseNumber(row.employedCount) > 0 ||
    parseNumber(row.trainingCompletionRate) > 0 ||
    parseNumber(row.degreeProgressRate) > 0
  )
}

function hasMeaningfulModuleRows(module = {}) {
  return (module.rows || []).some((row) => row && row.value && row.value !== '-')
}

function getDiagnosisType(score) {
  if (score >= 82) return 'success'
  if (score >= 72) return 'info'
  if (score >= 62) return 'warning'
  return 'danger'
}

function getDiagnosisLabel(type) {
  return {
    success: '优势明显',
    info: '结构稳定',
    warning: '需要补短',
    danger: '重点跟进',
  }[type] || '结构稳定'
}

function getCompositeScore(row = {}) {
  return roundToOne(
    parseNumber(row.awardRate) * 0.28 +
    parseNumber(row.employmentRate) * 0.34 +
    parseNumber(row.trainingCompletionRate) * 0.2 +
    parseNumber(row.degreeProgressRate) * 0.18,
  )
}

function mergePopulationIntoPortrait(baseRow = {}, realRow = {}) {
  const totalStudents = parseNumber(realRow.totalStudents) || parseNumber(baseRow.totalStudents)
  let maleCount = parseNumber(realRow.maleCount)
  let femaleCount = parseNumber(realRow.femaleCount)

  if (!maleCount && !femaleCount) {
    maleCount = parseNumber(baseRow.maleCount)
    femaleCount = parseNumber(baseRow.femaleCount)
  }

  if (totalStudents > 0 && maleCount + femaleCount !== totalStudents) {
    if (maleCount > 0 && femaleCount === 0) {
      femaleCount = Math.max(totalStudents - maleCount, 0)
    } else if (femaleCount > 0 && maleCount === 0) {
      maleCount = Math.max(totalStudents - femaleCount, 0)
    } else {
      const baseMaleRatio = parseNumber(realRow.maleRatio) || parseNumber(baseRow.maleRatio)
      maleCount = Math.round(totalStudents * baseMaleRatio / 100)
      femaleCount = totalStudents - maleCount
    }
  }

  const maleRatio = totalStudents > 0
    ? roundToOne(maleCount * 100 / totalStudents)
    : roundToOne(realRow.maleRatio || baseRow.maleRatio)
  const femaleRatio = totalStudents > 0
    ? roundToOne(100 - maleRatio)
    : roundToOne(realRow.femaleRatio || baseRow.femaleRatio)

  const awardRate = roundToOne(baseRow.awardRate || realRow.awardRate)
  const employmentRate = roundToOne(baseRow.employmentRate || realRow.employmentRate)
  const trainingCompletionRate = roundToOne(baseRow.trainingCompletionRate || realRow.trainingCompletionRate)
  const degreeProgressRate = roundToOne(baseRow.degreeProgressRate || realRow.degreeProgressRate)
  const furtherStudyRate = roundToOne(baseRow.furtherStudyRate || realRow.furtherStudyRate)
  const flexibleEmploymentRate = roundToOne(baseRow.flexibleEmploymentRate || realRow.flexibleEmploymentRate)
  const contractEmploymentRate = roundToOne(baseRow.contractEmploymentRate || realRow.contractEmploymentRate)
  const unemploymentRate = roundToOne(Math.max(0, 100 - employmentRate))
  const compositeScore = getCompositeScore({
    awardRate,
    employmentRate,
    trainingCompletionRate,
    degreeProgressRate,
  })
  const diagnosisType = getDiagnosisType(compositeScore)

  return {
    ...baseRow,
    ...realRow,
    totalStudents,
    maleCount,
    femaleCount,
    maleRatio,
    femaleRatio,
    genderRatioText: `${maleCount}:${femaleCount}`,
    awardRate,
    awardCount: Math.min(totalStudents, Math.round(totalStudents * awardRate / 100)),
    employmentRate,
    employedCount: Math.min(totalStudents, Math.round(totalStudents * employmentRate / 100)),
    trainingCompletionRate,
    degreeProgressRate,
    furtherStudyRate,
    flexibleEmploymentRate,
    contractEmploymentRate,
    unemploymentRate,
    compositeScore,
    diagnosisType,
    diagnosisLabel: getDiagnosisLabel(diagnosisType),
    genderBalanceScore: roundToOne(100 - Math.abs(maleRatio - 50) * 2),
    averageSalary: realRow.averageSalary ?? baseRow.averageSalary ?? null,
    updatedAt: realRow.updatedAt || baseRow.updatedAt || '',
  }
}

function mergeDetailModulesWithFallback(realModules = [], fallbackModules = []) {
  const realModuleMap = new Map((realModules || []).map((module) => [module.key, module]))

  return fallbackModules.map((module) => {
    if (module.key === 'profile') {
      return module
    }

    const realModule = realModuleMap.get(module.key)
    return hasMeaningfulModuleRows(realModule) ? realModule : module
  })
}

function enhanceCrossModuleSingleProfile(apiData, fallbackData) {
  if (!fallbackData?.focusRow) return apiData

  const focusRow = (!apiData?.focusRow || !hasMeaningfulRowMetrics(apiData.focusRow))
    ? mergePopulationIntoPortrait(fallbackData.focusRow, apiData?.focusRow)
    : apiData.focusRow

  const fallbackModules = getSingleProfileModuleTables(focusRow)
  const detailModules = mergeDetailModulesWithFallback(apiData?.detailModules || [], fallbackModules)

  return {
    ...apiData,
    mode: 'single_profile',
    focusRow,
    detailModules,
    latestUpdatedAt: apiData?.latestUpdatedAt || focusRow.updatedAt || fallbackData.latestUpdatedAt || '',
  }
}

function enhanceCrossModuleComparison(apiData, fallbackData) {
  const fallbackMap = new Map(
    (fallbackData?.comparisonRows || []).map((row) => [`${row.grade}__${row.major}`, row]),
  )

  const comparisonRows = (apiData?.comparisonRows || []).map((row) => {
    if (hasMeaningfulRowMetrics(row)) {
      return row
    }

    const fallbackRow = fallbackMap.get(`${row.grade}__${row.major}`)
    return fallbackRow ? mergePopulationIntoPortrait(fallbackRow, row) : row
  })

  return {
    ...apiData,
    mode: comparisonRows.length ? 'comparison' : apiData?.mode || 'empty',
    comparisonRows,
    summary: getQuerySummary(comparisonRows),
    latestUpdatedAt: apiData?.latestUpdatedAt || fallbackData?.latestUpdatedAt || '',
  }
}

function enhanceCrossModuleQueryResponse(apiData, filters = {}) {
  const fallbackData = buildCrossModuleQueryFallback(filters)

  if (apiData?.mode === 'empty' && fallbackData.mode !== 'empty') {
    return fallbackData
  }

  if (apiData?.mode === 'single_profile') {
    return enhanceCrossModuleSingleProfile(apiData, fallbackData)
  }

  if (apiData?.mode === 'comparison') {
    return enhanceCrossModuleComparison(apiData, fallbackData)
  }

  return apiData
}

async function requestJson(path, fallbackData) {
  return requestJsonWithInit(path, fallbackData)
}

async function requestJsonWithInit(path, fallbackData, init = {}, options = {}) {
  const { allowFallback = true } = options
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init.headers || {}),
      },
    })

    if (!response.ok) {
      const responseText = await response.text()
      const detail = responseText ? ` - ${responseText}` : ''
      throw new Error(`Request failed with status ${response.status}${detail}`)
    }

    return await response.json()
  } catch (error) {
    if (!allowFallback) {
      throw error
    }
    console.warn(`[data-service] Failed to load ${path}, using mock fallback.`, error)
    return clone(fallbackData)
  }
}

export function getSharedOptions() {
  return requestJson('/shared-options/', sharedOptions)
}

export function getHomeDashboardData() {
  return requestJson('/home/', homeMockData)
}

export function getAdmissionData() {
  return requestJson('/admission/', admissionMockData)
}

export function getAcademicStatusData() {
  return requestJson('/academic-status/', academicStatusMockData)
}

export function getAcademicChangeData() {
  return requestJson('/academic-change/', academicChangeMockData)
}

export function getTrainingData() {
  return requestJson('/training/', trainingMockData)
}

export function getTrainingCourseData() {
  return requestJson('/training-course/', trainingCourseMockData)
}

export function getDegreeData() {
  return requestJson('/degree/', degreeMockData)
}

export function getDegreeDefenseData() {
  return requestJson('/degree-defense/', degreeDefenseMockData)
}

export function getIntelligentPredictionData() {
  return requestJsonWithInit('/intelligent-prediction/', intelligentPredictionMockData, {}, {
    allowFallback: false,
  })
}

export function getIntelligentPredictionAnalysis(payload = {}, fallbackData = null) {
  return requestJsonWithInit('/intelligent-prediction/analyze/', fallbackData, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  }, {
    allowFallback: false,
  })
}

export function getIntelligentPredictionChat(payload = {}, fallbackData = null) {
  return requestJsonWithInit('/intelligent-prediction/chat/', fallbackData, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  }, {
    allowFallback: false,
  })
}

/**
 * 流式问答。逐条把 SSE 事件交给 onEvent 回调，返回最终 payload。
 *
 * Agent 单次问答要 10~40s，一次性等整个响应会让界面像卡住，
 * 所以这里读 ReadableStream，把 status / tool_start / tool_result
 * 等过程事件实时推给调用方；最终答案以 type=final 事件里的 payload 为准。
 *
 * 注意 answer_delta 是收尾轮的 JSON 片段，不是可直接展示的文本，
 * 只适合做"正在生成"的进度提示。
 */
export async function streamIntelligentPredictionChat(payload = {}, onEvent, options = {}) {
  const { signal } = options
  const response = await fetch(`${API_BASE_URL}/intelligent-prediction/chat/stream/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(payload),
    signal,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Request failed with status ${response.status}${detail ? ` - ${detail}` : ''}`)
  }
  if (!response.body) {
    throw new Error('Streaming is not supported in this environment')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let finalPayload = null

  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      // SSE 以空行分隔事件；最后一段可能不完整，留在 buffer 里等下一块
      const blocks = buffer.split('\n\n')
      buffer = blocks.pop() ?? ''

      for (const block of blocks) {
        const line = block.trim()
        if (!line.startsWith('data:')) continue
        const raw = line.slice(5).trim()
        if (!raw || raw === '[DONE]') continue

        let event
        try {
          event = JSON.parse(raw)
        } catch {
          continue
        }
        if (event.type === 'final') {
          finalPayload = event.payload ?? null
        }
        if (typeof onEvent === 'function') {
          onEvent(event)
        }
      }
    }
  } finally {
    reader.releaseLock?.()
  }

  if (!finalPayload) {
    throw new Error('Stream ended without a final answer')
  }
  return finalPayload
}

export function getScholarshipData() {
  return requestJson('/scholarship/', scholarshipMockData)
}

export function getEmploymentData() {
  return requestJson('/employment/', employmentMockData)
}

export function getGlobalSearchResults(keyword) {
  const text = String(keyword || '').trim()
  const query = text ? `?q=${encodeURIComponent(text)}` : ''
  return requestJson(`/search/${query}`, searchEverything(text))
}

export function getCrossModuleQueryData(filters = {}) {
  const params = new URLSearchParams()
  if (filters.grade) params.set('grade', filters.grade)
  if (filters.major) params.set('major', filters.major)
  const query = params.toString() ? `?${params.toString()}` : ''
  return requestJson(`/cross-module-query/${query}`, buildCrossModuleQueryFallback(filters))
    .then((data) => enhanceCrossModuleQueryResponse(data, filters))
}

export function getSystemSettingsData() {
  return resolve(systemSettingsMockData)
}

export function getPersonalCenterData() {
  return resolve(personalCenterMockData)
}

export function getChangePasswordData() {
  return resolve(changePasswordMockData)
}
