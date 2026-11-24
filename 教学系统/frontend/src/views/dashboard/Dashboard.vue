<template>
  <div class="dashboard">
    <!-- ===== Layer 1: Top KPI Cards (6-column, ~110px) ===== -->
    <div :class="`kpi-strip kpi-strip--${kpiList.length}`">
      <div class="kpi-card" v-for="kpi in kpiList" :key="kpi.label">
        <div class="kpi-inner">
          <span class="kpi-label">{{ kpi.label }}</span>
          <div class="kpi-value-row">
            <span class="kpi-number">{{ kpi.value }}</span>
            <span v-if="kpi.unit" class="kpi-unit">{{ kpi.unit }}</span>
            <span v-if="kpi.change !== null && kpi.change !== undefined" class="kpi-change" :class="kpi.up ? 'up' : 'down'">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline :points="kpi.up ? '18 15 12 9 6 15' : '6 9 12 15 18 9'"/></svg>
              {{ kpi.up ? '+' : '' }}{{ kpi.change }}%
            </span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="summaryError" class="kpi-error" role="alert">{{ summaryError }}</div>

    <!-- ===== Layer 2: Core Teaching Analysis (Visual Center) ===== -->
    <div id="module-teaching-analysis" class="section-header">
      <h2 class="section-title">教学运行分析</h2>
      <span class="section-subtitle">本学期 · 实时数据</span>
    </div>
    <div class="row-core">
      <!-- Left 4-col stack -->
      <div class="core-left">
        <div id="module-college-course-structure" class="panel panel--flex">
          <div class="panel-header">
            <h3 class="panel-title">课程类型结构分布</h3>
          </div>
          <div class="panel-chart" ref="pieRef"></div>
        </div>
        <div id="module-teaching-quality-ranking" class="panel panel--flex">
          <div class="panel-header">
            <h3 class="panel-title">课程平均成绩排行</h3>
          </div>
          <div class="panel-chart" ref="barRef"></div>
        </div>
      </div>
      <!-- Right 8-col main visual -->
      <div class="core-right">
        <div id="module-major-course-trend" class="panel panel--flex panel--hero">
          <div class="panel-header">
            <h3 class="panel-title">本学期成绩类型对比</h3>
          </div>
          <div class="panel-chart panel-chart--lg" ref="trendRef"></div>
        </div>
      </div>
    </div>

    <!-- ===== Layer 3: Student Development + Teaching Hotspot ===== -->
    <div id="module-student-cultivation" class="section-header">
      <h2 class="section-title">学生培养与教学热点</h2>
      <span class="section-subtitle">本科 · 研究生</span>
    </div>
    <div class="row-half">
      <!-- Left 6-col -->
      <div class="row-half-left">
        <div id="module-grade-distribution" class="panel panel--flex">
          <div class="panel-header">
            <h3 class="panel-title">学生成绩分布</h3>
          </div>
          <div class="panel-chart" ref="gradeRef"></div>
        </div>
        <div id="module-graduate-employment" class="panel panel--flex">
          <div class="panel-header">
            <h3 class="panel-title">毕业生就业去向</h3>
            <span class="panel-hint">{{ employmentUsingDemoData ? '演示数据 · 2026届' : employmentYear ? `${employmentYear}届统计` : '按毕业年份统计' }}</span>
          </div>
          <div class="panel-chart" ref="roseRef"></div>
        </div>
      </div>
      <!-- Right 6-col wordcloud -->
      <div class="row-half-right">
        <div id="module-teaching-hotspot" class="panel panel--flex panel--wordcloud">
          <div class="panel-header">
            <h3 class="panel-title">教学热点分析</h3>
            <span class="panel-hint">依据当前课程数据</span>
          </div>
          <div class="wordcloud-wrap">
            <div v-if="wordCloudTags.length === 0" class="empty-state">{{ courseLoadError ? '课程数据加载失败' : '暂无课程主题数据' }}</div>
            <span
              v-for="w in wordCloudTags"
              :key="w.name"
              class="wc-tag"
              :style="{ fontSize: w.size + 'px', color: w.color, fontWeight: w.bold ? '700' : '400', opacity: w.opacity }"
            >{{ w.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== Layer 4: Teacher & Research Analysis ===== -->
    <div id="module-teacher-development" class="section-header">
      <h2 class="section-title">教师发展与科研分析</h2>
    </div>
    <div class="row-half">
      <div id="module-teacher-title-structure" class="panel panel--flex">
        <div class="panel-header">
          <h3 class="panel-title">教师职称结构</h3>
        </div>
        <div class="panel-chart" ref="titleRef"></div>
      </div>
      <div id="module-research-trend" class="panel panel--flex">
        <div class="panel-header">
          <h3 class="panel-title">科研项目与成果趋势</h3>
          <span class="panel-hint">演示数据 · 科研项目与成果趋势</span>
        </div>
        <div class="panel-chart" ref="researchRef"></div>
      </div>
    </div>

    <!-- ===== Layer 5: Notification & Alerts Center ===== -->
    <div id="module-notification-alert" class="section-header">
      <h2 class="section-title">通知与预警</h2>
    </div>
    <div class="row-info">
      <!-- Left 5-col: Notices -->
      <div id="module-college-notices" class="panel info-notice">
        <div class="panel-header">
          <h3 class="panel-title">学院通知公告</h3>
          <span class="panel-hint">已发布公告</span>
        </div>
        <div class="notice-list">
          <div v-if="noticeLoading" class="empty-state">正在加载通知公告…</div>
          <div v-else-if="noticeLoadError" class="empty-state">通知公告加载失败，请检查接口</div>
          <div v-else-if="notices.length === 0" class="empty-state">暂无已发布的通知公告</div>
          <template v-else>
            <div v-for="n in notices" :key="n.id" class="notice-item">
              <span class="notice-badge" :class="'badge-' + n.type">{{ n.typeLabel }}</span>
              <span class="notice-text" :title="n.title">{{ n.title }}</span>
              <span class="notice-time">{{ n.time }}</span>
            </div>
          </template>
        </div>
      </div>
      <!-- Middle 4-col: Alerts -->
      <div id="module-teaching-alerts" class="panel info-alerts" :class="{ 'info-alerts--empty': alerts.length === 0 }">
        <div class="panel-header">
          <h3 class="panel-title">教学异常预警</h3>
          <span class="alert-total" :class="{ 'alert-total--empty': alerts.length === 0 }">{{ alerts.length }} 项</span>
        </div>
        <div class="alert-list">
          <div v-if="alertsLoading" class="empty-state">正在计算教学预警…</div>
          <div v-else-if="alertsLoadError" class="empty-state">教学预警加载失败，请检查接口</div>
          <div v-else-if="alerts.length === 0" class="empty-state">当前暂无符合规则的教学异常</div>
          <template v-else>
            <div v-for="a in alerts" :key="a.id" class="alert-item" :class="'alert-' + a.level">
              <span class="alert-tag" :class="'tag-' + a.level">{{ a.levelLabel }}</span>
              <span class="alert-title">{{ a.title }}</span>
              <span class="alert-meta">{{ a.desc }}</span>
            </div>
          </template>
        </div>
      </div>
      <!-- Right 3-col: Live Stream -->
      <div id="module-live-stream" class="panel info-live">
        <div class="panel-header">
          <h3 class="panel-title">实时动态</h3>
        </div>
        <div class="live-list" :class="{ 'live-list--ready': !liveLoading }">
          <div v-if="liveLoading" class="empty-state">正在加载近期操作…</div>
          <div v-else class="live-track" aria-label="近期业务动态滚动列表">
            <div v-for="copyIndex in 2" :key="copyIndex" class="live-group" :aria-hidden="copyIndex === 2">
              <div v-for="item in liveDisplayItems" :key="`${copyIndex}-${item.id}`" class="live-item">
                <span class="live-time">{{ item.time }}</span>
                <span class="live-text" :title="item.text">{{ item.text }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed, type Ref } from 'vue'
import * as echarts from 'echarts'
import {
  getDashboardSummary,
  getGraduateEmploymentStats,
  getDashboardAlerts,
  getDashboardLiveFeed,
  type KpiSummary,
  type GraduateEmploymentItem,
  type DashboardAlertItem,
  type DashboardLiveItem as ApiDashboardLiveItem,
} from '@/api/dashboard'
import { getResearchProjectTrend, getResearchAchievementTrend } from '@/api/research'
import {
  getScoreDistribution,
  getCourseScores,
  getGradeTypeComparison,
  type ScoreDistribution,
  type CourseScoreStat,
} from '@/api/analysis'
import { getCourses, type CourseItem } from '@/api/course'
import { getTeachers, type TeacherItem } from '@/api/teacher'
import { getNotices, type NoticeItem } from '@/api/notice'

type DashboardSummary = KpiSummary & {
  total_teachers?: number
  current_teaching_classes?: number
}

type CourseRecord = CourseItem & {
  is_active?: boolean
}

type TeacherRecord = TeacherItem & {
  is_active?: boolean
}

type PageResult<T> = {
  count?: number
  results?: T[]
}

type KpiCard = {
  label: string
  value: string
  unit: string
  change?: number | null
  up?: boolean
}

type GradeTypeRow = {
  label: string
  avgScore: number | null
  passRate: number | null
}

type DashboardNotice = {
  id: number
  type: 'info' | 'warning' | 'success'
  typeLabel: string
  title: string
  time: string
}

type DashboardAlert = DashboardAlertItem

type DashboardLiveItem = ApiDashboardLiveItem

type ResearchTrendRow = {
  year: number
  projectCount: number
  achievementCount: number
}

// Chart refs
const pieRef = ref<HTMLElement | null>(null)
const barRef = ref<HTMLElement | null>(null)
const trendRef = ref<HTMLElement | null>(null)
const gradeRef = ref<HTMLElement | null>(null)
const roseRef = ref<HTMLElement | null>(null)
const titleRef = ref<HTMLElement | null>(null)
const researchRef = ref<HTMLElement | null>(null)

let charts: echarts.ECharts[] = []
let isAlive = true

// ==================== Live API data ====================
const summary = ref<DashboardSummary | null>(null)
const summaryError = ref('')
const currentRole = ref(readCurrentRole())

const courses = ref<CourseRecord[]>([])
const courseLoadError = ref(false)

const courseScores = ref<CourseScoreStat[]>([])
const courseScoresError = ref(false)

const scoreDistribution = ref<ScoreDistribution[]>([])
const scoreDistributionError = ref(false)

const gradeTypeRows = ref<GradeTypeRow[]>([])
const gradeTypeError = ref(false)

const teachers = ref<TeacherRecord[]>([])
const teacherLoadError = ref(false)

const notices = ref<DashboardNotice[]>([])
const noticeLoadError = ref(false)
const noticeLoading = ref(true)

const employmentData = ref<GraduateEmploymentItem[]>([])
const employmentYear = ref<number | null>(null)
const employmentLoadError = ref(false)
const employmentUsingDemoData = ref(false)

// 首页演示数据：仅当后端没有有效就业统计数据时使用，并在界面明确标注。
const DEMO_EMPLOYMENT_DATA: GraduateEmploymentItem[] = [
  { name: '协议/合同就业', value: 72 },
  { name: '升学', value: 28 },
  { name: '考公考编', value: 14 },
  { name: '灵活就业', value: 8 },
  { name: '自主创业', value: 3 },
  { name: '待就业', value: 10 },
  { name: '其他', value: 4 },
]

const researchTrendRows = ref<ResearchTrendRow[]>([])
const researchLoadError = ref(false)

const alerts = ref<DashboardAlert[]>([])
const alertsLoading = ref(true)
const alertsLoadError = ref(false)
const liveStream = ref<DashboardLiveItem[]>([])
const liveLoading = ref(true)
const liveLoadError = ref(false)
let dynamicRefreshTimer: number | null = null

// 首页演示动态：后端真实日志优先展示，演示记录用于填充滚动列表，避免数据较少时模块空白。
const DEMO_LIVE_MESSAGES = [
  '演示：更新课程《公共政策分析》的课程信息',
  '演示：完成本学期教学班信息核对',
  '演示：发布《期末考试安排通知》',
  '演示：更新教师教学任务分配',
  '演示：完成学生学籍信息核验',
  '演示：录入《行政管理学》课程成绩',
  '演示：更新课程考核方式与成绩构成',
  '演示：新增《数字政府与治理》课程资料',
  '演示：完成考试场地与监考安排检查',
  '演示：更新学院教学通知公告',
  '演示：汇总本学期课程运行情况',
  '演示：完成教学质量数据整理',
]

function formatLiveTime(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

const liveDisplayItems = computed<DashboardLiveItem[]>(() => {
  const now = Date.now()
  const demoItems: DashboardLiveItem[] = DEMO_LIVE_MESSAGES.map((text, index) => ({
    id: -(index + 1),
    time: formatLiveTime(new Date(now - (index + 1) * 3 * 60 * 1000)),
    text,
    module: '教学管理',
    action: '演示',
    actor: '演示数据',
  }))

  // 保留后端真实记录，并追加演示记录，确保动态栏有足够内容连续滚动。
  return [...liveStream.value, ...demoItems]
})

function readCurrentRole(): string {
  try {
    const raw = localStorage.getItem('user_info')
    if (!raw) return 'unassigned'

    const user = JSON.parse(raw) as { role?: string; role_name?: string }
    return String(user.role || user.role_name || 'unassigned').trim().toLowerCase()
  } catch {
    return 'unassigned'
  }
}

function roleCategory(role: string): 'student' | 'teacher' | 'admin' | 'unassigned' {
  const value = role.trim().toLowerCase()
  if (value.includes('student') || value.includes('学生')) return 'student'
  if (value.includes('teacher') || value.includes('教师')) return 'teacher'
  if (
    value.includes('admin') ||
    value.includes('academic') ||
    value.includes('viewer') ||
    value.includes('教务') ||
    value.includes('管理员')
  ) {
    return 'admin'
  }
  return 'unassigned'
}

function formatCount(value: unknown): string {
  if (value === null || value === undefined || value === '') return '--'
  const number = Number(value)
  return Number.isFinite(number) ? number.toLocaleString('zh-CN') : '--'
}

function formatDecimal(value: unknown, digits = 2): string {
  if (value === null || value === undefined || value === '') return '--'
  const number = Number(value)
  return Number.isFinite(number) ? number.toFixed(digits) : '--'
}

const kpiList = computed<KpiCard[]>(() => {
  const data = summary.value
  const count = (value: unknown) => data ? formatCount(value) : '--'
  const score = data ? formatDecimal(data.avg_score) : '--'
  const rate = data ? formatDecimal(data.exam_pass_rate) : '--'
  const role = roleCategory(currentRole.value)

  if (role === 'student') {
    return [
      { label: '已有成绩课程数', value: count(data?.total_courses), unit: '门' },
      { label: '本人平均成绩', value: score, unit: '分' },
      { label: '本人成绩及格率', value: rate, unit: '%' },
    ]
  }

  if (role === 'teacher') {
    return [
      { label: '授课关联学生', value: count(data?.total_students), unit: '人' },
      { label: '本人授课课程', value: count(data?.total_courses), unit: '门' },
      { label: '授课平均成绩', value: score, unit: '分' },
      { label: '授课成绩及格率', value: rate, unit: '%' },
    ]
  }

  if (role === 'admin') {
    return [
      { label: '本学期开课班次', value: count(data?.current_teaching_classes), unit: '个' },
      { label: '学院学生人数', value: count(data?.total_students), unit: '人' },
      { label: '在职教师人数', value: count(data?.total_teachers), unit: '人' },
      { label: '启用课程数量', value: count(data?.total_courses), unit: '门' },
      { label: '学院平均成绩', value: score, unit: '分' },
      { label: '成绩及格率', value: rate, unit: '%' },
    ]
  }

  // Unknown roles only receive neutral, API-scoped summary fields.
  return [
    { label: '当前范围学生数', value: count(data?.total_students), unit: '人' },
    { label: '当前范围课程数', value: count(data?.total_courses), unit: '门' },
    { label: '平均成绩', value: score, unit: '分' },
    { label: '成绩及格率', value: rate, unit: '%' },
  ]
})

async function loadDashboardSummary(): Promise<void> {
  currentRole.value = readCurrentRole()
  summaryError.value = ''

  try {
    summary.value = await getDashboardSummary() as DashboardSummary
  } catch (error: unknown) {
    summary.value = null
    const detail = error as {
      response?: { data?: { detail?: string } }
      message?: string
    }
    summaryError.value =
      detail.response?.data?.detail ||
      detail.message ||
      '首页统计数据加载失败，请检查后端服务和登录状态。'
    console.error('加载首页统计数据失败：', error)
  }
}

async function fetchAllPages<T>(
  fetchPage: (page: number) => Promise<PageResult<T>>,
): Promise<T[]> {
  const first = await fetchPage(1)
  const firstResults = Array.isArray(first?.results) ? first.results : []
  const total = Math.max(0, Number(first?.count ?? firstResults.length))
  const pageSize = firstResults.length || 10
  const pageCount = Math.min(Math.ceil(total / pageSize), 100)
  const all = [...firstResults]

  for (let page = 2; page <= pageCount; page += 1) {
    const response = await fetchPage(page)
    const pageResults = Array.isArray(response?.results) ? response.results : []
    if (pageResults.length === 0) break
    all.push(...pageResults)
  }

  return total > 0 ? all.slice(0, total) : all
}

async function loadCourses(): Promise<void> {
  courseLoadError.value = false
  try {
    const result = await fetchAllPages<CourseRecord>(
      page => getCourses({ page, page_size: 100 }) as Promise<PageResult<CourseRecord>>,
    )
    courses.value = result.filter(course => course.is_active !== false)
  } catch (error) {
    courseLoadError.value = true
    courses.value = []
    console.error('加载课程数据失败：', error)
  }
}

async function loadCourseScores(): Promise<void> {
  courseScoresError.value = false
  try {
    const result = await getCourseScores()
    courseScores.value = Array.isArray(result) ? result : []
  } catch (error) {
    courseScoresError.value = true
    courseScores.value = []
    console.error('加载课程成绩统计失败：', error)
  }
}

async function loadScoreDistribution(): Promise<void> {
  scoreDistributionError.value = false
  try {
    const result = await getScoreDistribution()
    scoreDistribution.value = Array.isArray(result) ? result : []
  } catch (error) {
    scoreDistributionError.value = true
    scoreDistribution.value = []
    console.error('加载成绩分布失败：', error)
  }
}

function extractArray(value: unknown): unknown[] {
  if (Array.isArray(value)) return value
  if (!value || typeof value !== 'object') return []

  const object = value as Record<string, unknown>
  const keys = [
    'results',
    'comparison',
    'comparisons',
    'grade_type_comparison',
    'grade_type_stats',
    'grade_type_results',
    'grade_type_comparison_stats',
    'grade_types',
    'items',
    'data',
  ]

  for (const key of keys) {
    if (Array.isArray(object[key])) return object[key] as unknown[]
  }

  return []
}

function firstDefined(object: Record<string, unknown>, keys: string[]): unknown {
  for (const key of keys) {
    if (object[key] !== null && object[key] !== undefined && object[key] !== '') {
      return object[key]
    }
  }
  return undefined
}

function nullableNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}

function normalizeGradeTypeLabel(value: unknown): string {
  const label = String(value ?? '').trim().toLowerCase()
  if (label.includes('usual') || label.includes('平时')) return '平时'
  if (label.includes('midterm') || label.includes('期中')) return '期中'
  if (label.includes('final') || label.includes('期末')) return '期末'
  return String(value ?? '').trim()
}

async function loadGradeTypeComparison(): Promise<void> {
  gradeTypeError.value = false
  try {
    const response: unknown = await getGradeTypeComparison()
    gradeTypeRows.value = extractArray(response)
      .map((item): GradeTypeRow | null => {
        if (!item || typeof item !== 'object') return null
        const row = item as Record<string, unknown>
        const labelValue = firstDefined(row, [
          'grade_type_display',
          'grade_type_name',
          'exam_type',
          'grade_type',
          'score_type',
          'type_label',
          'type_name',
          'exam_type_name',
          'type',
          'label',
          'name',
        ])
        const label = normalizeGradeTypeLabel(labelValue)
        const avgScore = nullableNumber(firstDefined(row, [
          'avg_score',
          'average_score',
          'avg',
          'average',
        ]))
        const passRate = nullableNumber(firstDefined(row, [
          'pass_rate',
          'passRate',
          'passed_rate',
          'pass_rate_percent',
          'passRatePercent',
        ]))

        if (!label || (avgScore === null && passRate === null)) return null
        const normalizedPassRate =
          passRate !== null && passRate >= 0 && passRate <= 1
            ? passRate * 100
            : passRate
        return { label, avgScore, passRate: normalizedPassRate }
      })
      .filter((row): row is GradeTypeRow => row !== null)
      .sort((a, b) => {
        const order = ['平时', '期中', '期末']
        const aIndex = order.indexOf(a.label)
        const bIndex = order.indexOf(b.label)
        return (aIndex < 0 ? 99 : aIndex) - (bIndex < 0 ? 99 : bIndex)
      })
  } catch (error) {
    gradeTypeError.value = true
    gradeTypeRows.value = []
    console.error('加载成绩类型对比失败：', error)
  }
}

async function loadTeachers(): Promise<void> {
  teacherLoadError.value = false
  try {
    const result = await fetchAllPages<TeacherRecord>(
      page => getTeachers({ page, page_size: 100 }) as Promise<PageResult<TeacherRecord>>,
    )
    teachers.value = result.filter(teacher => teacher.is_active !== false)
  } catch (error) {
    teacherLoadError.value = true
    teachers.value = []
    console.error('加载教师数据失败：', error)
  }
}

function formatNoticeDate(value: string): string {
  if (!value) return '--'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '--'
  return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

async function loadNotices(): Promise<void> {
  noticeLoadError.value = false
  noticeLoading.value = true
  try {
    const all = await fetchAllPages<NoticeItem>(
      page => getNotices({ page, page_size: 100 }),
    )

    notices.value = all
      .filter(notice => notice.is_published)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5)
      .map(notice => ({
        id: notice.id,
        type: notice.notice_type === 'warning'
          ? 'warning'
          : notice.notice_type === 'success'
            ? 'success'
            : 'info',
        typeLabel: notice.notice_type === 'warning'
          ? '提醒'
          : notice.notice_type === 'success'
            ? '完成'
            : '通知',
        title: notice.title,
        time: formatNoticeDate(notice.created_at),
      }))
  } catch (error) {
    noticeLoadError.value = true
    notices.value = []
    console.error('加载通知公告失败：', error)
  } finally {
    noticeLoading.value = false
  }
}

// ==================== Course keywords ====================
const wordCloudTags = computed(() => {
  const palette = [
    '#0F172A', '#1E3A8A', '#1E40AF', '#2563EB', '#3B82F6',
    '#60A5FA', '#3B82F6', '#60A5FA', '#93C5FD', '#93C5FD',
    '#BFDBFE', '#BFDBFE', '#DBEAFE', '#DBEAFE', '#EFF6FF',
  ]

  const records = courses.value
    .filter(course => Boolean(course.name?.trim()))
    .slice(0, 15)

  const maxCredit = Math.max(1, ...records.map(course => Number(course.credit) || 1))

  return records.map((course, index) => {
    const credit = Number(course.credit) || 1
    return {
      name: course.name,
      size: 13 + (credit / maxCredit) * 15,
      color: palette[index % palette.length],
      bold: index < 4,
      opacity: Math.max(0.62, 1 - index * 0.025),
    }
  })
})

// ==================== Chart helpers ====================
const palette = ['#0F172A', '#1E3A8A', '#2563EB', '#60A5FA', '#93C5FD', '#BFDBFE']

function chartFor(target: Ref<HTMLElement | null>): echarts.ECharts | null {
  const element = target.value
  if (!element) return null

  const existing = echarts.getInstanceByDom(element)
  if (existing) {
    if (!charts.includes(existing)) charts.push(existing)
    return existing
  }

  const chart = echarts.init(element)
  charts.push(chart)
  return chart
}

function showNoData(target: Ref<HTMLElement | null>, message: string): void {
  const chart = chartFor(target)
  if (!chart) return

  chart.setOption({
    title: {
      text: message,
      left: 'center',
      top: 'middle',
      textStyle: {
        color: '#9CA3AF',
        fontSize: 13,
        fontWeight: 'normal',
      },
    },
    tooltip: { show: false },
    xAxis: { show: false },
    yAxis: { show: false },
    series: [],
  }, true)
}

function initPie(): void {
  if (courses.value.length === 0) {
    showNoData(pieRef, courseLoadError.value ? '课程数据加载失败' : '暂无课程数据')
    return
  }

  const counts = new Map<string, number>()
  courses.value.forEach(course => {
    const type = String(course.course_type || '').trim() || '未分类'
    counts.set(type, (counts.get(type) || 0) + 1)
  })

  const data = Array.from(counts.entries()).map(([name, value], index) => ({
    name,
    value,
    itemStyle: { color: palette[index % palette.length] },
  }))

  const chart = chartFor(pieRef)
  if (!chart) return

  chart.setOption({
    title: { show: false },
    tooltip: {
      trigger: 'item',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#1F2937', fontSize: 12 },
      formatter: '{b}<br/>课程数：{c} 门（{d}%）',
    },
    series: [{
      type: 'pie',
      radius: ['55%', '78%'],
      center: ['50%', '50%'],
      label: { show: false },
      emphasis: { scale: true, scaleSize: 6 },
      itemStyle: { borderColor: '#FFFFFF', borderWidth: 2, borderRadius: 4 },
      data,
    }],
  }, true)
}

function initBar(): void {
  const data = courseScores.value
    .filter(item =>
      item &&
      item.course_name &&
      Number.isFinite(Number(item.avg_score)),
    )
    .map(item => ({
      name: item.course_name,
      value: Number(item.avg_score),
    }))
    .sort((a, b) => a.value - b.value)
    .slice(-6)

  if (data.length === 0) {
    showNoData(barRef, courseScoresError.value ? '课程成绩加载失败' : '暂无课程成绩数据')
    return
  }

  const chart = chartFor(barRef)
  if (!chart) return

  chart.setOption({
    title: { show: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#1F2937', fontSize: 12 },
      formatter: (params: unknown) => {
        const items = Array.isArray(params) ? params : [params]
        const item = items[0] as { name?: string; value?: number | string } | undefined
        return `${item?.name ?? ''}<br/>平均成绩：${Number(item?.value ?? 0).toFixed(2)} 分`
      },
    },
    grid: { top: 6, right: 42, bottom: 6, left: 96 },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: '#9CA3AF', fontSize: 10 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#374151', fontSize: 11, width: 90, overflow: 'truncate' },
    },
    series: [{
      type: 'bar',
      data: data.map(item => ({
        value: item.value,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#0F172A' },
            { offset: 1, color: '#3B82F6' },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
      })),
      barWidth: 16,
      label: {
        show: true,
        position: 'right',
        color: '#1F2937',
        fontSize: 11,
        fontWeight: 'bold',
        formatter: (params: unknown) => {
          const item = params as { value?: unknown }
          return Number(item.value).toFixed(2)
        },
      },
    }],
  }, true)
}

function initTrend(): void {
  const data = gradeTypeRows.value
  if (data.length === 0) {
    showNoData(trendRef, gradeTypeError.value ? '成绩类型对比加载失败' : '暂无成绩类型对比数据')
    return
  }

  const chart = chartFor(trendRef)
  if (!chart) return

  chart.setOption({
    title: { show: false },
    color: ['#0F172A', '#3B82F6'],
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#1F2937', fontSize: 12 },
      formatter: (params: unknown) => {
        const items = Array.isArray(params) ? params as Array<{
          axisValueLabel?: string
          name?: string
          seriesName?: string
          value?: number | string | null
          marker?: string
        }> : [params as {
          axisValueLabel?: string
          name?: string
          seriesName?: string
          value?: number | string | null
          marker?: string
        }]
        const label = items[0]?.axisValueLabel ?? items[0]?.name ?? ''
        return [
          label,
          ...items.map(item => {
            const value = item.value === null || item.value === undefined
              ? '--'
              : Number(item.value).toFixed(2)
            return `${item.marker ?? ''}${item.seriesName ?? ''}：${value}${item.seriesName === '及格率' ? '%' : ' 分'}`
          }),
        ].join('<br/>')
      },
    },
    legend: {
      data: ['平均成绩', '及格率'],
      top: 0,
      textStyle: { color: '#6B7280', fontSize: 11 },
    },
    grid: { top: 38, right: 58, bottom: 32, left: 58 },
    xAxis: {
      type: 'category',
      data: data.map(item => item.label),
      axisLabel: { color: '#9CA3AF', fontSize: 10 },
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: '平均成绩（分）',
        min: 0,
        max: 100,
        nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
        axisLabel: { color: '#9CA3AF', fontSize: 10 },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      },
      {
        type: 'value',
        name: '及格率（%）',
        min: 0,
        max: 100,
        position: 'right',
        nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
        axisLabel: { color: '#9CA3AF', fontSize: 10 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '平均成绩',
        type: 'line',
        data: data.map(item => item.avgScore),
        yAxisIndex: 0,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5 },
        emphasis: { focus: 'series' },
      },
      {
        name: '及格率',
        type: 'line',
        data: data.map(item => item.passRate),
        yAxisIndex: 1,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5 },
        emphasis: { focus: 'series' },
      },
    ],
  }, true)
}

function initGrade(): void {
  const rangeLabels: Record<string, string> = {
    '0-59': '60以下',
    '60-69': '60-69',
    '70-79': '70-79',
    '80-89': '80-89',
    '90-100': '90-100',
  }

  const data = scoreDistribution.value.map(item => ({
    name: rangeLabels[item.score_range] || item.score_range,
    value: Number(item.count) || 0,
  }))
  const total = data.reduce((sum, item) => sum + item.value, 0)

  if (data.length === 0 || total === 0) {
    showNoData(gradeRef, scoreDistributionError.value ? '成绩分布加载失败' : '暂无成绩分布数据')
    return
  }

  const chart = chartFor(gradeRef)
  if (!chart) return

  chart.setOption({
    title: { show: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#1F2937', fontSize: 12 },
      formatter: (params: unknown) => {
        const items = Array.isArray(params) ? params : [params]
        const item = items[0] as { name?: string; value?: number | string } | undefined
        return `${item?.name ?? ''}<br/>成绩记录：${Number(item?.value ?? 0).toLocaleString('zh-CN')} 条`
      },
    },
    grid: { top: 22, right: 18, bottom: 28, left: 48 },
    xAxis: {
      type: 'category',
      data: data.map(item => item.name),
      axisLabel: { color: '#9CA3AF', fontSize: 10 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#E5E7EB' } },
    },
    yAxis: {
      type: 'value',
      name: '成绩记录数',
      min: 0,
      nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
      axisLabel: { color: '#9CA3AF', fontSize: 10 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
    },
    series: [{
      type: 'bar',
      data: data.map((item, index) => ({
        value: item.value,
        itemStyle: {
          color: ['#93C5FD', '#60A5FA', '#3B82F6', '#2563EB', '#1E3A8A'][index % 5],
          borderRadius: [6, 6, 0, 0],
        },
      })),
      barWidth: 28,
      label: {
        show: true,
        position: 'top',
        color: '#374151',
        fontSize: 11,
        fontWeight: 'bold',
        formatter: (params: unknown) => {
          const item = params as { value?: unknown }
          return Number(item.value).toLocaleString('zh-CN')
        },
      },
    }],
  }, true)
}

function initRose(): void {
  const data = employmentData.value.filter(item => Number(item.value) > 0)
  if (data.length === 0) {
    showNoData(
      roseRef,
      employmentLoadError.value ? '就业统计加载失败' : '暂无毕业生就业去向数据',
    )
    return
  }

  const chart = chartFor(roseRef)
  if (!chart) return

  chart.setOption({
    title: { show: false },
    color: palette,
    tooltip: {
      trigger: 'item',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#1F2937', fontSize: 12 },
      formatter: (params: unknown) => {
        const item = params as { name?: string; value?: number | string; percent?: number }
        return `${item.name ?? ''}<br/>人数：${Number(item.value ?? 0).toLocaleString('zh-CN')} 人（${Number(item.percent ?? 0).toFixed(1)}%）`
      },
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 8,
      top: 'middle',
      textStyle: { color: '#6B7280', fontSize: 10 },
    },
    series: [{
      type: 'pie',
      radius: ['32%', '68%'],
      center: ['36%', '50%'],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: '#FFFFFF', borderWidth: 2, borderRadius: 3 },
      label: { show: false },
      emphasis: { label: { show: true, fontSize: 12, fontWeight: 'bold' } },
      data,
    }],
  }, true)
}

function initTitle(): void {
  const counts = new Map<string, number>()
  teachers.value.forEach(teacher => {
    const title = String(teacher.title || '').trim() || '未填写'
    counts.set(title, (counts.get(title) || 0) + 1)
  })

  const data = Array.from(counts.entries())
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => a.value - b.value)

  if (data.length === 0) {
    showNoData(titleRef, teacherLoadError.value ? '教师数据加载失败' : '暂无教师职称数据')
    return
  }

  const chart = chartFor(titleRef)
  if (!chart) return

  chart.setOption({
    title: { show: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#1F2937', fontSize: 12 },
      formatter: (params: unknown) => {
        const items = Array.isArray(params) ? params : [params]
        const item = items[0] as { name?: string; value?: number | string } | undefined
        return `${item?.name ?? ''}<br/>教师人数：${Number(item?.value ?? 0)} 人`
      },
    },
    grid: { top: 8, right: 32, bottom: 8, left: 76 },
    xAxis: {
      type: 'value',
      min: 0,
      axisLabel: { color: '#9CA3AF', fontSize: 10 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'category',
      data: data.map(item => item.name),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#374151', fontSize: 10, width: 68, overflow: 'truncate' },
    },
    series: [{
      type: 'bar',
      data: data.map(item => ({
        value: item.value,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#0F172A' },
            { offset: 1, color: '#60A5FA' },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
      })),
      barWidth: 18,
      label: {
        show: true,
        position: 'right',
        color: '#374151',
        fontSize: 11,
        fontWeight: 'bold',
      },
    }],
  }, true)
}

function initResearch(): void {
  if (researchLoadError.value) {
    showNoData(researchRef, '科研系统数据加载失败')
    return
  }

  const data = researchTrendRows.value
  if (data.length === 0 || !data.some(item => item.projectCount > 0 || item.achievementCount > 0)) {
    showNoData(researchRef, '暂无科研项目或成果记录')
    return
  }

  const chart = chartFor(researchRef)
  if (!chart) return

  chart.setOption({
    title: { show: false },
    color: ['#1E3A8A', '#3B82F6'],
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#1F2937', fontSize: 12 },
    },
    legend: {
      data: ['科研项目数', '科研成果数'],
      top: 0,
      textStyle: { color: '#6B7280', fontSize: 11 },
    },
    grid: { top: 36, right: 22, bottom: 28, left: 42 },
    xAxis: {
      type: 'category',
      data: data.map(item => String(item.year)),
      axisLabel: { color: '#9CA3AF', fontSize: 10 },
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      minInterval: 1,
      axisLabel: { color: '#9CA3AF', fontSize: 10 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
    },
    series: [
      {
        name: '科研项目数',
        type: 'line',
        data: data.map(item => item.projectCount),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5 },
      },
      {
        name: '科研成果数',
        type: 'line',
        data: data.map(item => item.achievementCount),
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5 },
      },
    ],
  }, true)
}

async function loadGraduateEmployment(): Promise<void> {
  employmentLoadError.value = false
  employmentUsingDemoData.value = false

  try {
    const response = await getGraduateEmploymentStats()
    const actualData = Array.isArray(response?.data)
      ? response.data.filter(item => Number(item.value) > 0)
      : []

    // 接口无记录或只有 0 人测试记录时，首页改用明确标注的演示数据。
    if (actualData.length > 0) {
      employmentYear.value = response.year
      employmentData.value = actualData
      return
    }

    employmentYear.value = 2026
    employmentData.value = DEMO_EMPLOYMENT_DATA.map(item => ({ ...item }))
    employmentUsingDemoData.value = true
  } catch (error) {
    // 首页展示优先保证完整；演示数据有明确标签，不冒充真实统计结果。
    console.warn('就业统计接口不可用，首页使用本地演示数据：', error)
    employmentYear.value = 2026
    employmentData.value = DEMO_EMPLOYMENT_DATA.map(item => ({ ...item }))
    employmentUsingDemoData.value = true
  }
}

async function loadResearchTrend(): Promise<void> {
  researchLoadError.value = false
  const years = [2021, 2022, 2023, 2024, 2025, new Date().getFullYear()]
  try {
    const [projectResult, achievementResult] = await Promise.all([
      getResearchProjectTrend(years),
      getResearchAchievementTrend(years),
    ])
    const projectMap = new Map<number, number>()
    const achievementMap = new Map<number, number>()
    projectResult.years.forEach((year, index) => projectMap.set(Number(year), Number(projectResult.values[index]) || 0))
    achievementResult.years.forEach((year, index) => achievementMap.set(Number(year), Number(achievementResult.values[index]) || 0))
    const allYears = Array.from(new Set([...projectResult.years, ...achievementResult.years])).sort((a, b) => a - b)
    researchTrendRows.value = allYears.map(year => ({
      year,
      projectCount: projectMap.get(year) ?? 0,
      achievementCount: achievementMap.get(year) ?? 0,
    }))
  } catch (error) {
    researchTrendRows.value = []
    researchLoadError.value = true
    console.error('加载科研项目与成果趋势失败：', error)
  }
}

async function loadDashboardAlerts(): Promise<void> {
  alertsLoadError.value = false
  try {
    const response = await getDashboardAlerts()
    alerts.value = Array.isArray(response?.results) ? response.results : []
  } catch (error) {
    alerts.value = []
    alertsLoadError.value = true
    console.error('加载教学异常预警失败：', error)
  } finally {
    alertsLoading.value = false
  }
}

async function loadDashboardLiveFeed(): Promise<void> {
  liveLoadError.value = false
  try {
    const response = await getDashboardLiveFeed({ limit: 8 })
    liveStream.value = Array.isArray(response?.results) ? response.results : []
  } catch (error) {
    // 实时接口不可用时仍展示明确标注的演示动态，不让首页模块空白。
    liveStream.value = []
    liveLoadError.value = false
    console.warn('实时动态接口暂不可用，当前展示演示动态：', error)
  } finally {
    liveLoading.value = false
  }
}

// ==================== Lifecycle ====================
onMounted(async () => {
  await nextTick()
  window.addEventListener('resize', handleResize)

  await Promise.all([
    loadDashboardSummary(),
    loadCourses(),
    loadCourseScores(),
    loadScoreDistribution(),
    loadGradeTypeComparison(),
    loadTeachers(),
    loadNotices(),
    loadGraduateEmployment(),
    loadResearchTrend(),
    loadDashboardAlerts(),
    loadDashboardLiveFeed(),
  ])

  if (!isAlive) return

  await nextTick()
  initPie()
  initBar()
  initTrend()
  initGrade()
  initRose()
  initTitle()
  initResearch()

  dynamicRefreshTimer = window.setInterval(() => {
    if (!isAlive) return
    void Promise.all([loadDashboardAlerts(), loadDashboardLiveFeed()])
  }, 60000)
})

onUnmounted(() => {
  isAlive = false
  charts.forEach(chart => {
    if (!chart.isDisposed()) chart.dispose()
  })
  charts = []
  if (dynamicRefreshTimer !== null) {
    window.clearInterval(dynamicRefreshTimer)
    dynamicRefreshTimer = null
  }
  window.removeEventListener('resize', handleResize)
})

function handleResize(): void {
  charts.forEach(chart => {
    if (!chart.isDisposed()) chart.resize()
  })
}
</script>

<style lang="scss" scoped>
/* ============================================================
   Dashboard — 12-Grid Data Cockpit
   设计方向：高校智慧校园·数据驾驶舱·政务大数据平台
   气质：稳重·专业·克制·数据化
   ============================================================ */

/* ----- Tokens ----- */
$c-bg: #F5F7FA;
$c-card: #FFFFFF;
$c-border: #E5E7EB;
$c-text: #1F2937;
$c-secondary: #6B7280;
$c-muted: #9CA3AF;
$c-primary: #1E3A8A;
$c-accent: #2563EB;
$radius: 8px;
$shadow-card: 0 1px 2px rgba(0, 0, 0, 0.04);
$shadow-hover: 0 2px 8px rgba(0, 0, 0, 0.06);

.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  min-height: 100%;
  background: $c-bg;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

/* ===== Layer 1: KPI Strip (6 columns) ===== */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.kpi-strip--3 {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.kpi-strip--4 {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.kpi-error {
  margin-top: -8px;
  color: #B91C1C;
  font-size: 12px;
  line-height: 1.5;
}

.kpi-card {
  background: $c-card;
  border: 1px solid $c-border;
  border-radius: $radius;
  padding: 16px 20px;
  box-shadow: $shadow-card;
  transition: box-shadow 0.2s;
  &:hover {
    box-shadow: $shadow-hover;
  }
}

.kpi-inner {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.kpi-label {
  font-size: 12px;
  color: $c-muted;
  font-weight: 500;
}

.kpi-value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.kpi-number {
  font-size: 26px;
  font-weight: 700;
  color: $c-text;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}

.kpi-unit {
  font-size: 12px;
  color: $c-secondary;
  font-weight: 500;
}

.kpi-change {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  &.up {
    color: #059669;
    background: #ECFDF5;
  }
  &.down {
    color: #DC2626;
    background: #FEF2F2;
  }
}

/* ===== Section Header ===== */
.section-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 4px 0 0;
}

.section-title {
  font-size: 15px;
  font-weight: 700;
  color: $c-text;
  margin: 0;
  position: relative;
  padding-left: 12px;
  &::before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 15px;
    background: $c-primary;
    border-radius: 2px;
  }
}

.section-subtitle {
  font-size: 11px;
  color: $c-muted;
  font-weight: 400;
}

/* ===== Panel (Unified Card) ===== */
.panel {
  background: $c-card;
  border: 1px solid $c-border;
  border-radius: $radius;
  padding: 16px 20px;
  box-shadow: $shadow-card;
  display: flex;
  flex-direction: column;
}

.panel--flex {
  flex: 1;
  min-height: 0;
}

.panel--hero {
  // main visual emphasis
}

.panel--wordcloud {
  // wordcloud panel
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  margin-bottom: 4px;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: $c-text;
  margin: 0;
}

.panel-hint {
  font-size: 11px;
  color: $c-muted;
}

.panel-link {
  font-size: 12px;
  color: $c-accent;
  text-decoration: none;
  cursor: pointer;
  &:hover { opacity: 0.8; }
}

.panel-chart {
  flex: 1;
  min-height: 0;
  width: 100%;
}

/* Height control per layer */
.panel-chart--lg {
  min-height: 340px;
}

// Generic chart heights set via parent grids

.legend-inline {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
  &:first-child { margin-left: 4px; }
}

.legend-text {
  font-size: 10px;
  color: $c-muted;
}

/* ===== Layer 2: Core Analysis (4 + 8) ===== */
.row-core {
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: 12px;
  min-height: 440px;
}

.core-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  & > .panel {
    flex: 1;
    min-height: 0;
    .panel-chart {
      min-height: 160px;
    }
  }
}

.core-right {
  min-height: 0;
  & > .panel {
    height: 100%;
    .panel-chart--lg {
      min-height: 340px;
    }
  }
}

/* ===== Layer 3 & 4: Half-half rows ===== */
.row-half {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  min-height: 280px;
}

.row-half-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  & > .panel {
    flex: 1;
    min-height: 0;
    .panel-chart {
      min-height: 130px;
    }
  }
}

.row-half-right {
  min-height: 0;
  & > .panel {
    height: 100%;
  }
}

/* ===== Layer 5: Info Center (5 + 4 + 3) ===== */
.row-info {
  display: grid;
  grid-template-columns: 5fr 4fr 3fr;
  gap: 12px;
  min-height: 240px;
}

/* ===== Word Cloud ===== */
.wordcloud-wrap {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  align-content: center;
  gap: 6px 14px;
  padding: 16px 24px;
  flex: 1;
}

.wc-tag {
  display: inline-block;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all 0.2s;
  line-height: 1.5;
  letter-spacing: 0.5px;
  &:hover {
    transform: scale(1.12);
    background: rgba(37, 99, 235, 0.06);
  }
}

/* ===== Notice List ===== */
.notice-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  flex: 1;
}

.notice-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px solid #F3F4F6;
  &:last-child { border-bottom: none; }
}

.notice-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 3px;
  flex-shrink: 0;
  &.badge-academic { background: #EFF6FF; color: #2563EB; }
  &.badge-research { background: #ECFDF5; color: #059669; }
  &.badge-admin { background: #FFF7ED; color: #EA580C; }
  &.badge-student { background: #FDF2F8; color: #DB2777; }
}

.notice-badge {
  &.badge-info { background: #EFF6FF; color: #2563EB; }
  &.badge-warning { background: #FFF7ED; color: #EA580C; }
  &.badge-success { background: #ECFDF5; color: #059669; }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-height: 96px;
  width: 100%;
  padding: 18px 12px;
  box-sizing: border-box;
  color: $c-muted;
  font-size: 12px;
  line-height: 1.7;
  text-align: center;
}

.notice-text {
  font-size: 12px;
  color: $c-text;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  &:hover { color: $c-accent; }
}

.notice-time {
  font-size: 10px;
  color: $c-muted;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

/* ===== Alert List ===== */
.info-alerts {
  background: #FFFBEB;
}

.info-alerts--empty {
  background: $c-card;
}

.alert-total {
  font-size: 11px;
  font-weight: 600;
  color: #DC2626;
  background: #FEF2F2;
  padding: 2px 8px;
  border-radius: 4px;
  &.alert-total--empty {
    color: #6B7280;
    background: #F3F4F6;
  }
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.alert-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 6px;
  border-left: 3px solid transparent;
  &.alert-red { background: #FEF2F2; border-left-color: #DC2626; }
  &.alert-orange { background: #FFF7ED; border-left-color: #EA580C; }
  &.alert-yellow { background: #FFFBEB; border-left-color: #F59E0B; }
}

.alert-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 3px;
  align-self: flex-start;
  &.tag-red { color: #DC2626; background: #FEE2E2; }
  &.tag-orange { color: #EA580C; background: #FFEDD5; }
  &.tag-yellow { color: #D97706; background: #FEF3C7; }
}

.alert-title {
  font-size: 12px;
  color: $c-text;
  font-weight: 600;
  line-height: 1.4;
}

.alert-meta {
  font-size: 10px;
  color: $c-muted;
}

/* ===== Live Stream ===== */
.live-dot {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  color: #059669;
  font-weight: 600;
}

.live-dot-inner {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10B981;
  display: inline-block;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.live-list {
  position: relative;
  display: block;
  flex: 1;
  min-height: 0;
  height: 100%;
  max-height: 230px;
  overflow: hidden;
  mask-image: linear-gradient(to bottom, transparent 0, #000 10px, #000 calc(100% - 10px), transparent 100%);
}

.live-track {
  display: flex;
  flex-direction: column;
  animation: live-feed-scroll 34s linear infinite;
  will-change: transform;
}

.live-list:hover .live-track {
  animation-play-state: paused;
}

.live-group {
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  gap: 4px;
  padding-bottom: 4px;
}

.live-item {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 27px;
  padding: 5px 0;
  border-bottom: 1px solid #F3F4F6;
  &:last-child { border-bottom: none; }
}

@keyframes live-feed-scroll {
  0% { transform: translateY(0); }
  100% { transform: translateY(-50%); }
}

@media (prefers-reduced-motion: reduce) {
  .live-track { animation: none; }
}

.live-time {
  font-size: 10px;
  color: $c-muted;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.live-text {
  font-size: 11px;
  color: $c-text;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ===== Responsive ===== */
@media (max-width: 1600px) {
  .kpi-strip--6 {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}

@media (max-width: 1400px) {
  .kpi-strip--6 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .kpi-strip--4 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .kpi-strip--3 {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .row-core {
    grid-template-columns: 1fr 2fr;
  }
}

@media (max-width: 1100px) {
  .kpi-strip--6,
  .kpi-strip--4,
  .kpi-strip--3 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .row-core {
    grid-template-columns: 1fr;
    min-height: auto;
  }
  .core-left {
    flex-direction: row;
    & > .panel {
      min-height: 260px;
    }
  }
  .row-half {
    grid-template-columns: 1fr;
    min-height: auto;
  }
  .row-half-left {
    flex-direction: row;
    & > .panel {
      min-height: 220px;
    }
  }
  .row-info {
    grid-template-columns: 1fr 1fr;
  }
  .info-live {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .dashboard {
    padding: 12px;
    gap: 12px;
  }
  .kpi-strip--6,
  .kpi-strip--4,
  .kpi-strip--3 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .kpi-number {
    font-size: 22px;
  }
  .core-left {
    flex-direction: column;
  }
  .row-half-left {
    flex-direction: column;
  }
  .row-info {
    grid-template-columns: 1fr;
  }
  .info-live {
    grid-column: span 1;
  }
}
</style>
