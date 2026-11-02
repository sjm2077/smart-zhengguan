import { REAL_GRADES, REAL_MAJORS } from './graduateCatalog'

export const gradeOptions = [...REAL_GRADES]

export const majorOptions = [...REAL_MAJORS]

const gradeFactors = {
  '2021级': { cohortBase: 45, awards: 78, employment: 95, training: 98, degree: 96, maleAdjust: -1.8, furtherStudy: 7, salary: 14.2 },
  '2022级': { cohortBase: 42, awards: 74, employment: 93, training: 96, degree: 94, maleAdjust: -1.5, furtherStudy: 8, salary: 13.8 },
  '2023级': { cohortBase: 39, awards: 70, employment: 81, training: 87, degree: 82, maleAdjust: -0.5, furtherStudy: 10, salary: 12.9 },
  '2024级': { cohortBase: 36, awards: 66, employment: 60, training: 76, degree: 63, maleAdjust: 0.8, furtherStudy: 13, salary: 11.7 },
  '2025级': { cohortBase: 33, awards: 61, employment: 36, training: 64, degree: 42, maleAdjust: 1.5, furtherStudy: 16, salary: 10.2 },
}

const majorFactors = {
  政治学理论: { cohortDelta: 1, maleRatio: 42, awards: 2, employment: 1, training: 1, degree: 2, furtherStudy: 2, salary: 0.2 },
  科学社会主义与国际共产主义运动: { cohortDelta: 0, maleRatio: 47, awards: 5, employment: 2, training: 2, degree: 2, furtherStudy: 1, salary: 0.4 },
  中共党史: { cohortDelta: -2, maleRatio: 39, awards: -1, employment: -2, training: -1, degree: 0, furtherStudy: 1, salary: -0.3 },
  国际政治: { cohortDelta: 1, maleRatio: 46, awards: 3, employment: 3, training: 2, degree: 3, furtherStudy: 2, salary: 0.5 },
  国际关系: { cohortDelta: 2, maleRatio: 44, awards: 6, employment: 4, training: 3, degree: 4, furtherStudy: 3, salary: 0.8 },
  统一战线学: { cohortDelta: -1, maleRatio: 37, awards: 0, employment: -1, training: -1, degree: -1, furtherStudy: 1, salary: -0.2 },
  行政管理: { cohortDelta: 3, maleRatio: 33, awards: 2, employment: 1, training: 1, degree: 1, furtherStudy: 1, salary: 0.3 },
  应急管理: { cohortDelta: 4, maleRatio: 58, awards: -2, employment: 5, training: 4, degree: 2, furtherStudy: -1, salary: 0.9 },
}

const diagnosisMeta = {
  success: '优势明显',
  info: '结构稳定',
  warning: '需要补短',
  danger: '重点跟进',
}

function round(value) {
  return Number(value.toFixed(1))
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function stripZero(value) {
  return Number(value).toFixed(1).replace(/\.0$/, '')
}

function formatGenderRatio(maleCount, femaleCount) {
  return `${maleCount}:${femaleCount}`
}

function buildUpdatedAt(gradeIndex, majorIndex) {
  const day = String(24 - ((gradeIndex * 3 + majorIndex) % 10)).padStart(2, '0')
  return `2026-05-${day}`
}

function getGenderBalanceScore(maleRatio) {
  return round(100 - Math.abs(maleRatio - 50) * 2)
}

function getDiagnosisType(compositeScore) {
  if (compositeScore >= 82) return 'success'
  if (compositeScore >= 72) return 'info'
  if (compositeScore >= 62) return 'warning'
  return 'danger'
}

function createPortraitRow(grade, major, gradeIndex, majorIndex) {
  const gradeFactor = gradeFactors[grade]
  const majorFactor = majorFactors[major]
  const volatility = ((gradeIndex + majorIndex) % 3) - 1

  const totalStudents = gradeFactor.cohortBase + majorFactor.cohortDelta + ((gradeIndex + majorIndex) % 2)
  const maleRatio = clamp(
    majorFactor.maleRatio + gradeFactor.maleAdjust + volatility * 1.4,
    30,
    62,
  )
  const femaleRatio = round(100 - maleRatio)
  const maleCount = Math.round(totalStudents * maleRatio / 100)
  const femaleCount = totalStudents - maleCount

  const awardRate = clamp(
    gradeFactor.awards + majorFactor.awards + volatility * 1.6,
    48,
    90,
  )
  const employmentRate = clamp(
    gradeFactor.employment + majorFactor.employment + volatility * 1.2,
    28,
    97,
  )
  const trainingCompletionRate = clamp(
    gradeFactor.training + majorFactor.training + volatility * 1.8,
    52,
    99,
  )
  const degreeProgressRate = clamp(
    gradeFactor.degree + majorFactor.degree + volatility * 1.5,
    35,
    99,
  )
  const furtherStudyRate = clamp(
    gradeFactor.furtherStudy + majorFactor.furtherStudy + (majorIndex % 2),
    5,
    24,
  )
  const flexibleEmploymentRate = clamp(
    5 + (majorIndex % 4) + Math.max(0, 2 - gradeIndex),
    4,
    14,
  )
  const contractEmploymentRate = clamp(
    employmentRate - furtherStudyRate - flexibleEmploymentRate,
    15,
    82,
  )
  const unemploymentRate = round(100 - employmentRate)
  const averageSalary = round(
    gradeFactor.salary + majorFactor.salary + ((majorIndex + gradeIndex) % 2) * 0.2,
  )
  const awardCount = Math.round(totalStudents * awardRate / 100)
  const employedCount = Math.round(totalStudents * employmentRate / 100)
  const compositeScore = round(
    awardRate * 0.28 +
    employmentRate * 0.34 +
    trainingCompletionRate * 0.2 +
    degreeProgressRate * 0.18
  )
  const genderBalanceScore = getGenderBalanceScore(maleRatio)
  const diagnosisType = getDiagnosisType(compositeScore)

  return {
    id: `${grade}-${major}`,
    grade,
    major,
    totalStudents,
    maleCount,
    femaleCount,
    maleRatio: round(maleRatio),
    femaleRatio,
    genderRatioText: formatGenderRatio(maleCount, femaleCount),
    awardCount,
    awardRate: round(awardRate),
    employedCount,
    employmentRate: round(employmentRate),
    furtherStudyRate: round(furtherStudyRate),
    flexibleEmploymentRate: round(flexibleEmploymentRate),
    contractEmploymentRate: round(contractEmploymentRate),
    unemploymentRate,
    trainingCompletionRate: round(trainingCompletionRate),
    degreeProgressRate: round(degreeProgressRate),
    averageSalary,
    genderBalanceScore,
    compositeScore,
    diagnosisLabel: diagnosisMeta[diagnosisType],
    diagnosisType,
    updatedAt: buildUpdatedAt(gradeIndex, majorIndex),
  }
}

export const portraitRows = gradeOptions.flatMap((grade, gradeIndex) =>
  majorOptions.map((major, majorIndex) => createPortraitRow(grade, major, gradeIndex, majorIndex)),
)

export function normalizeQueryFilters(filters = {}) {
  return {
    grade: typeof filters.grade === 'string' ? filters.grade.trim() : '',
    major: typeof filters.major === 'string' ? filters.major.trim() : '',
  }
}

export function hasQueryFilters(filters = {}) {
  const normalized = normalizeQueryFilters(filters)
  return Boolean(normalized.grade || normalized.major)
}

export function formatMetricValue(value, unit) {
  if (unit === '%') return `${stripZero(value)}%`
  if (unit === '万元') return `${stripZero(value)}万元`
  return `${Math.round(value)}${unit}`
}

export function getQueryPlaceholderText(filters = {}) {
  const { grade, major } = normalizeQueryFilters(filters)
  if (grade && major) return `${grade} ${major}`
  if (grade) return `${grade} 全部专业`
  if (major) return `全部年级 ${major}`
  return '全部年级 全部专业'
}

export function getQueryDescription(filters = {}) {
  const { grade, major } = normalizeQueryFilters(filters)
  if (grade && major) return `当前展示 ${grade}${major} 的跨模块画像与分模块明细，不再与其他年级或专业做横向比较`
  if (grade) return `当前展示 ${grade} 内所有专业的获奖、就业、培养、学位和性别结构画像`
  if (major) return `当前展示 ${major} 在不同年级之间的获奖、就业、培养、学位和性别结构对比`
  return '请选择年级或专业后查看跨模块画像结果'
}

export function getQueryResultRows(filters = {}) {
  const normalized = normalizeQueryFilters(filters)
  return portraitRows.filter((row) => {
    const matchGrade = !normalized.grade || row.grade === normalized.grade
    const matchMajor = !normalized.major || row.major === normalized.major
    return matchGrade && matchMajor
  })
}

export function getQueryComparisonRows(filters = {}) {
  const normalized = normalizeQueryFilters(filters)

  if (normalized.grade) {
    return portraitRows.filter((row) => row.grade === normalized.grade)
  }

  if (normalized.major) {
    return portraitRows.filter((row) => row.major === normalized.major)
  }

  return []
}

export function getQuerySummary(rows = []) {
  if (!rows.length) {
    return {
      entityCount: 0,
      totalStudents: 0,
      averageAwardRate: 0,
      averageEmploymentRate: 0,
      averageTrainingRate: 0,
      averageDegreeRate: 0,
      averageMaleRatio: 0,
    }
  }

  const totalStudents = rows.reduce((sum, row) => sum + row.totalStudents, 0)
  const weightedAverage = (field) => round(
    rows.reduce((sum, row) => sum + row[field] * row.totalStudents, 0) / totalStudents,
  )

  return {
    entityCount: rows.length,
    totalStudents,
    averageAwardRate: weightedAverage('awardRate'),
    averageEmploymentRate: weightedAverage('employmentRate'),
    averageTrainingRate: weightedAverage('trainingCompletionRate'),
    averageDegreeRate: weightedAverage('degreeProgressRate'),
    averageMaleRatio: weightedAverage('maleRatio'),
  }
}

export function getSingleProfileModuleTables(row) {
  if (!row) return []

  const nationalAwardCount = Math.max(1, Math.round(row.awardCount * 0.16))
  const academicAwardCount = Math.max(1, Math.round(row.awardCount * 0.49))
  const socialAwardCount = Math.max(0, row.awardCount - nationalAwardCount - academicAwardCount)
  const notAwardedCount = Math.max(0, row.totalStudents - row.awardCount)

  const contractCount = Math.round(row.totalStudents * row.contractEmploymentRate / 100)
  const furtherStudyCount = Math.round(row.totalStudents * row.furtherStudyRate / 100)
  const flexibleEmploymentCount = Math.round(row.totalStudents * row.flexibleEmploymentRate / 100)
  const unemployedCount = Math.max(
    0,
    row.totalStudents - contractCount - furtherStudyCount - flexibleEmploymentCount,
  )

  const courseStageCount = Math.max(1, Math.round(row.totalStudents * 0.34))
  const proposalStageCount = Math.max(1, Math.round(row.totalStudents * 0.27))
  const midtermStageCount = Math.max(1, Math.round(row.totalStudents * 0.22))
  const defenseStageCount = Math.max(
    0,
    row.totalStudents - courseStageCount - proposalStageCount - midtermStageCount,
  )

  const proposalPassRate = clamp(row.trainingCompletionRate - 6, 35, 99)
  const midtermPassRate = clamp(row.trainingCompletionRate - 3, 40, 99)
  const defensePassRate = clamp(row.degreeProgressRate - 4, 30, 99)
  const degreeGrantedRate = clamp(row.degreeProgressRate - 8, 25, 98)

  return [
    {
      key: 'profile',
      title: '基本画像',
      description: '展示该年级该专业的规模、性别结构与综合画像结论。',
      rows: [
        { item: '总人数', value: `${row.totalStudents}人`, rate: '-', note: '当前查询样本规模' },
        { item: '男生人数', value: `${row.maleCount}人`, rate: `${row.maleRatio}%`, note: '男生占比' },
        { item: '女生人数', value: `${row.femaleCount}人`, rate: `${row.femaleRatio}%`, note: '女生占比' },
        { item: '男女比例', value: row.genderRatioText, rate: '-', note: '男:女' },
        { item: '综合评分', value: `${row.compositeScore}分`, rate: row.diagnosisLabel, note: '综合获奖、就业、培养、学位形成' },
        { item: '平均起薪', value: `${stripZero(row.averageSalary)}万元`, rate: '-', note: '毕业去向平均起薪估算' },
      ],
    },
    {
      key: 'scholarship',
      title: '奖助模块',
      description: '展示获奖覆盖和获奖结构分布。',
      rows: [
        { item: '国家级奖学金', value: `${nationalAwardCount}人`, rate: `${stripZero(nationalAwardCount * 100 / row.totalStudents)}%`, note: '高层次荣誉奖励' },
        { item: '学业奖学金', value: `${academicAwardCount}人`, rate: `${stripZero(academicAwardCount * 100 / row.totalStudents)}%`, note: '覆盖面最大的奖助类型' },
        { item: '社会及专项奖助', value: `${socialAwardCount}人`, rate: `${stripZero(socialAwardCount * 100 / row.totalStudents)}%`, note: '项目型、专项型资助' },
        { item: '未获奖学生', value: `${notAwardedCount}人`, rate: `${stripZero(notAwardedCount * 100 / row.totalStudents)}%`, note: '重点关注提升对象' },
        { item: '整体获奖率', value: `${stripZero(row.awardRate)}%`, rate: `${row.awardCount}人`, note: '当前专业整体奖助覆盖水平' },
      ],
    },
    {
      key: 'employment',
      title: '就业模块',
      description: '展示就业去向结构和落实情况。',
      rows: [
        { item: '签约就业', value: `${contractCount}人`, rate: `${stripZero(row.contractEmploymentRate)}%`, note: '单位签约、定向录用等' },
        { item: '升学深造', value: `${furtherStudyCount}人`, rate: `${stripZero(row.furtherStudyRate)}%`, note: '升博、出国深造等' },
        { item: '灵活就业', value: `${flexibleEmploymentCount}人`, rate: `${stripZero(row.flexibleEmploymentRate)}%`, note: '项目制、自由职业、短期聘用' },
        { item: '未就业', value: `${unemployedCount}人`, rate: `${stripZero(row.unemploymentRate)}%`, note: '仍需重点跟踪' },
        { item: '总体就业率', value: `${stripZero(row.employmentRate)}%`, rate: `${row.employedCount}人`, note: '已落实毕业去向人数占比' },
      ],
    },
    {
      key: 'training',
      title: '培养模块',
      description: '展示培养环节分布和推进完成度。',
      rows: [
        { item: '课程学习阶段', value: `${courseStageCount}人`, rate: `${stripZero(clamp(row.trainingCompletionRate - 18, 20, 99))}%`, note: '课程学习与基础培养' },
        { item: '论文开题阶段', value: `${proposalStageCount}人`, rate: `${stripZero(proposalPassRate)}%`, note: '开题通过率' },
        { item: '中期考核阶段', value: `${midtermStageCount}人`, rate: `${stripZero(midtermPassRate)}%`, note: '中期考核推进情况' },
        { item: '论文答辩阶段', value: `${defenseStageCount}人`, rate: `${stripZero(row.trainingCompletionRate)}%`, note: '临近毕业环节' },
        { item: '培养完成率', value: `${stripZero(row.trainingCompletionRate)}%`, rate: row.diagnosisLabel, note: '培养全过程推进结果' },
      ],
    },
    {
      key: 'degree',
      title: '学位模块',
      description: '展示论文、答辩和授予进度。',
      rows: [
        { item: '论文开题通过率', value: `${stripZero(proposalPassRate)}%`, rate: `${Math.round(row.totalStudents * proposalPassRate / 100)}人`, note: '开题阶段完成情况' },
        { item: '中期评阅通过率', value: `${stripZero(midtermPassRate)}%`, rate: `${Math.round(row.totalStudents * midtermPassRate / 100)}人`, note: '论文中期推进状态' },
        { item: '正式答辩通过率', value: `${stripZero(defensePassRate)}%`, rate: `${Math.round(row.totalStudents * defensePassRate / 100)}人`, note: '进入答辩后的通过情况' },
        { item: '学位授予进度', value: `${stripZero(row.degreeProgressRate)}%`, rate: `${Math.round(row.totalStudents * row.degreeProgressRate / 100)}人`, note: '整体学位流程推进比例' },
        { item: '学位授予完成率', value: `${stripZero(degreeGrantedRate)}%`, rate: `${Math.round(row.totalStudents * degreeGrantedRate / 100)}人`, note: '已达到可授予状态的比例' },
      ],
    },
  ]
}

export function buildCrossModuleQueryFallback(filters = {}) {
  const normalized = normalizeQueryFilters(filters)
  const description = getQueryDescription(normalized)
  const conditionText = getQueryPlaceholderText(normalized)

  if (!hasQueryFilters(normalized)) {
    return {
      mode: 'empty',
      filters: normalized,
      description,
      conditionText,
      focusRow: null,
      comparisonRows: [],
      summary: getQuerySummary([]),
      detailModules: [],
      latestUpdatedAt: '',
    }
  }

  if (normalized.grade && normalized.major) {
    const focusRow = getQueryResultRows(normalized)[0] || null
    return {
      mode: focusRow ? 'single_profile' : 'empty',
      filters: normalized,
      description,
      conditionText,
      focusRow,
      comparisonRows: [],
      summary: getQuerySummary([]),
      detailModules: getSingleProfileModuleTables(focusRow),
      latestUpdatedAt: focusRow?.updatedAt || '',
    }
  }

  const comparisonRows = [...getQueryComparisonRows(normalized)].sort((a, b) => (
    b.compositeScore - a.compositeScore ||
    b.employmentRate - a.employmentRate
  ))

  return {
    mode: comparisonRows.length ? 'comparison' : 'empty',
    filters: normalized,
    description,
    conditionText,
    focusRow: null,
    comparisonRows,
    summary: getQuerySummary(comparisonRows),
    detailModules: [],
    latestUpdatedAt: comparisonRows.map((item) => item.updatedAt).sort().reverse()[0] || '',
  }
}

export const queryRecords = portraitRows.map((row) => ({
  id: `analysis-${row.grade}-${row.major}`,
  moduleName: '跨模块画像',
  grade: row.grade,
  major: row.major,
  metricLabel: '获奖率',
  metricValue: row.awardRate,
  metricUnit: '%',
  extraLabel: '就业率',
  extraValue: row.employmentRate,
  extraUnit: '%',
  status: row.diagnosisLabel,
  statusType: row.diagnosisType,
  summary: `${row.grade}${row.major}画像：获奖率 ${formatMetricValue(row.awardRate, '%')}，就业率 ${formatMetricValue(row.employmentRate, '%')}，男女比 ${row.genderRatioText}`,
}))
