<template>
  <div class="exam-hub">
    <!-- 页面仅显示当前学期，不提供历史学期切换 -->
    <header class="hub-topbar">
      <div>
        <h2 class="hub-title"><span class="title-symbol">▣</span> 考试调度与考务中心</h2>
        <p class="hub-subtitle">山东大学政治学与公共管理学院 · 本学期考试编排与考务管理</p>
      </div>
      <div class="hub-actions">
        <span class="semester-tag">2026—2027学年 · 第一学期</span>
        <button class="btn-outline" :disabled="loading" @click="refreshData">{{ loading ? '刷新中…' : '刷新数据' }}</button>
        <button class="btn-primary" :disabled="!currentSemesterId || loading" @click="openNewExam">＋ 新增考试</button>
      </div>
    </header>

    <div class="status-note" :class="{ 'note-warning': !currentSemesterId }">
      <span class="note-dot"></span>
      <span v-if="loading">正在读取教务系统中的本学期考试安排…</span>
      <span v-else-if="loadError">{{ loadError }}</span>
      <span v-else-if="!currentSemesterId">教务系统尚未找到2026—2027学年第一学期档案。当前只显示校历参考信息，不使用旧学期或虚构考试数据。</span>
      <span v-else>当前学期已固定，考试信息来自现有教务接口；未录入的考试、考场与监考信息不会自动生成。</span>
    </div>

    <!-- 本学期客观统计 -->
    <section class="hub-stats-row">
      <article v-for="(s, i) in stats" :key="s.label" class="hub-stat-card">
        <div class="stat-icon" :class="'icon-' + i"><span>{{ ['▣', '▤', '◷', '!'][i] }}</span></div>
        <div class="stat-copy">
          <p class="stat-label">{{ s.label }}</p>
          <p class="stat-value">{{ s.value }}<small>{{ s.unit }}</small></p>
          <p class="stat-desc">{{ s.desc }}</p>
        </div>
      </article>
    </section>

    <!-- 专业与年级考试安排（新增核心模块） -->
    <section id="module-exam-cohorts" class="hub-panel full-panel">
      <div class="panel-head">
        <div><h3><span class="accent"></span>专业与年级考试安排</h3><p class="panel-sub">按专业、入学年级查询本学期考试；支持调整考试信息及适用范围草稿</p></div>
        <span class="panel-badge">{{ scopedExams.length }} 场记录</span>
      </div>
      <div class="filters-bar">
        <label>所属专业
          <select v-model="filterMajor"><option value="">全部专业</option><option v-for="m in majors" :key="m" :value="m">{{ m }}</option></select>
        </label>
        <label>入学年级
          <select v-model="filterGrade"><option value="">全部年级</option><option v-for="g in grades" :key="g" :value="g">{{ g }}级</option></select>
        </label>
        <label class="search-control">搜索考试
          <input v-model.trim="examQuery" placeholder="考试名称 / 课程 / 考场" />
        </label>
        <button class="btn-outline" @click="resetFilters">重置</button>
        <button class="btn-outline" @click="exportCsv">导出 CSV</button>
      </div>
      <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>考试日期 / 时段</th><th>考试 / 课程</th><th>考核类型</th><th>考场</th><th>适用专业 / 年级</th><th>状态</th><th>操作</th></tr></thead>
          <tbody>
            <tr v-for="exam in scopedExams" :key="exam.id">
              <td><strong>{{ exam.date }}</strong><small>{{ exam.time }}</small></td>
              <td><strong>{{ exam.name }}</strong><small>{{ exam.courseName }}</small></td>
              <td>{{ exam.examType || '待填写' }}</td>
              <td>{{ exam.location || '待安排' }}</td>
              <td><span :class="{ muted: !scopeOf(exam.id) }">{{ scopeLabel(exam.id) }}</span><small v-if="scopeOf(exam.id)">本机关联草稿</small></td>
              <td><span class="state-tag" :class="'state-' + exam.statusKey">{{ exam.status }}</span></td>
              <td class="cell-actions">
                <button @click="editScope(exam.id)">关联范围</button>
                <button @click="editExam(exam)">编辑</button>
              </td>
            </tr>
            <tr v-if="!scopedExams.length"><td colspan="7" class="empty-cell">暂无符合条件的考试记录。可切换“全部专业”查看未关联的考试。</td></tr>
          </tbody>
        </table>
      </div>
      <p class="module-hint">说明：目前原有 Exam 模型不包含“适用专业、年级、行政班”关联字段。本页面的关联范围仅保存在当前浏览器，不能作为已提交学校的正式排考依据；考试基本信息的保存仍使用原有教务接口。</p>
    </section>

    <!-- 学校校历事实与学期周次，来源与考试计划必须分开 -->
    <section class="hub-panel full-panel academic-panel">
      <div class="panel-head">
        <div><h3><span class="accent"></span>山东大学本学期教学周与考试安排参考</h3><p class="panel-sub">根据2026年秋季学期开学时间计算教学周次</p></div>
        <span class="panel-badge">2026—2027学年第一学期</span>
      </div>
      <div class="academic-items">
        <div><span>学生返校注册</span><strong>2026年8月30日</strong><small>学校公布的开学安排</small></div>
        <div><span>正式开始上课</span><strong>2026年8月31日</strong><small>按此日期作为教学第1周</small></div>
        <div><span>第18周</span><strong>12月28日—1月3日</strong><small>期末排考参考窗口</small></div>
        <div><span>第19周</span><strong>1月4日—1月10日</strong><small>期末排考参考窗口</small></div>
      </div>
      <p class="module-hint">第18、19周的具体日期由上课起始日推算；目前尚未确认学校已将两周全部指定为统一考试周，因此这里只作排考参考。其他教学周也可能有期中或单独课程考核。具体考试以校方通知及数据库正式排考为准。</p>
    </section>

    <!-- 考试日历与今日考试：与原页面相同的左右结构 -->
    <section class="hub-row-2col">
      <div id="module-exam-calendar" class="hub-panel calendar-panel">
        <div class="panel-head"><h3><span class="accent"></span>考试日历</h3>
          <div class="cal-navigation"><button @click="changeMonth(-1)" aria-label="上月">‹</button><b>{{ calendarTitle }}</b><button @click="changeMonth(1)" aria-label="下月">›</button></div>
        </div>
        <div class="calendar-grid">
          <span class="weekday" v-for="name in weekdays" :key="name">{{ name }}</span>
          <button v-for="(cell, i) in calendarCells" :key="i" class="calendar-day"
            :class="{ 'other-month': !cell.inMonth, 'is-today': cell.isToday, 'is-window': cell.isReferenceWeek, 'is-selected': selectedDate === cell.key }"
            @click="selectDate(cell)">
            <span>{{ cell.day }}</span><small v-if="cell.isReferenceWeek && cell.inMonth">参考考试周</small>
            <span class="exam-dots" v-if="cell.count"><i v-for="n in Math.min(cell.count, 3)" :key="n"></i></span>
          </button>
        </div>
        <p class="calendar-hint">淡蓝色背景表示第18、19教学周的日期，并不代表当天已有考试；蓝色小圆点才代表已登记的考试。</p>
      </div>

      <div id="module-today-exams" class="hub-panel day-panel">
        <div class="panel-head"><h3><span class="accent"></span>{{ selectedDate === todayStr ? '今日考试' : '选定日期考试' }}</h3><span class="panel-badge">{{ selectedDate }}</span></div>
        <div v-if="selectedExams.length" class="day-list">
          <div class="day-exam" v-for="e in selectedExams" :key="e.id">
            <b>{{ e.time }}</b><div><strong>{{ e.name }}</strong><small>{{ e.courseName }}</small></div>
            <span class="day-exam-room">{{ e.location || '地点待安排' }}</span><span class="state-tag" :class="'state-' + e.statusKey">{{ e.status }}</span>
          </div>
        </div>
        <div v-else class="day-empty"><span>◷</span><strong>该日期暂无已登记考试</strong><p>可通过上方专业与年级考试安排登记考试信息</p></div>
      </div>
    </section>

    <!-- 实际考场分布和可核验的冲突 -->
    <section class="hub-row-2col">
      <div id="module-exam-room-distribution" class="hub-panel">
        <div class="panel-head"><h3><span class="accent"></span>考场分布</h3><span class="panel-badge">{{ venues.length }} 处地点</span></div>
        <div v-if="venues.length" ref="venueChartRef" class="chart-holder"></div>
        <div v-else class="panel-empty">尚未登记本学期考试场地，暂无考场分布数据。</div>
      </div>
      <div id="module-conflict-warning" class="hub-panel">
        <div class="panel-head"><h3><span class="accent"></span>考试冲突检查</h3><span class="panel-badge" :class="{ 'badge-danger': conflicts.length }">{{ conflicts.length }} 项</span></div>
        <div v-if="conflicts.length" class="conflict-list">
          <div v-for="c in conflicts" :key="c.id" class="conflict-item"><span>!</span><div><strong>同一考场时间冲突</strong><p>{{ c.detail }}</p></div></div>
        </div>
        <div v-else class="panel-empty">目前没有发现同考场、同时段重叠的考试。监考教师和同班级冲突需要后端提供正式关联数据才能进一步核验。</div>
      </div>
    </section>

    <!-- 监考安排保留，但是不伪造教师姓名 -->
    <section id="module-invigilation-arrangement" class="hub-panel full-panel">
      <div class="panel-head"><h3><span class="accent"></span>监考安排</h3><span class="panel-badge">本学期</span></div>
      <p class="module-hint">现有考试记录尚未包含正式监考教师、巡考及联系电话字段，因此这里只列出已登记考试，未录入人员不会使用虚构姓名填充。</p>
      <div class="table-scroll">
        <table class="data-table">
          <thead><tr><th>考试名称</th><th>考试日期</th><th>考试时段</th><th>考场</th><th>主监考</th><th>副监考</th><th>确认状态</th></tr></thead>
          <tbody>
            <tr v-for="e in sortedExams" :key="e.id"><td>{{ e.name }}</td><td>{{ e.date }}</td><td>{{ e.time }}</td><td>{{ e.location || '待安排' }}</td><td class="muted">待录入</td><td class="muted">待录入</td><td><span class="state-tag state-pending">待确认</span></td></tr>
            <tr v-if="!sortedExams.length"><td colspan="7" class="empty-cell">暂无本学期考试安排</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 考试时间轴：仅列真实考试与有来源的教学周起点 -->
    <section id="module-exam-timeline" class="hub-panel full-panel">
      <div class="panel-head"><h3><span class="accent"></span>考试工作时间轴</h3><span class="panel-badge">本学期</span></div>
      <div class="timeline-list">
        <div class="timeline-entry" v-for="(event, index) in timeline" :key="index" :class="{ 'timeline-past': event.date < todayStr }">
          <span class="timeline-point"></span><strong>{{ event.date }}</strong><div><b>{{ event.title }}</b><p>{{ event.note }}</p></div>
        </div>
      </div>
    </section>

    <!-- 原页面三列区保留，但不能拿模拟人数、缺考率充当实测 -->
    <section class="hub-row-3col">
      <div id="module-exam-progress" class="hub-panel">
        <div class="panel-head"><h3><span class="accent"></span>考试进度状态</h3><span class="panel-badge">{{ allExams.length }} 场</span></div>
        <div v-if="allExams.length" ref="progressChartRef" class="chart-holder compact"></div>
        <div v-else class="panel-empty">暂无本学期考试安排</div>
        <p class="small-footnote">进度状态按当前时间和考试开始时间、时长推算。</p>
      </div>
      <div id="module-absence-statistics" class="hub-panel">
        <div class="panel-head"><h3><span class="accent"></span>缺考统计</h3><span class="panel-badge">待接入</span></div>
        <div class="panel-empty"><strong>暂无可靠的缺考记录</strong><p>目前考试接口没有到考签到和缺考登记数据，不能据此计算缺考人数、缺考率。</p></div>
      </div>
      <div id="module-room-utilization" class="hub-panel">
        <div class="panel-head"><h3><span class="accent"></span>考场利用率</h3><span class="panel-badge">待接入</span></div>
        <div class="panel-empty"><strong>尚无考场容量数据</strong><p>现有考试地点为文本字段，没有座位容量信息，暂不生成利用率百分比。</p></div>
      </div>
    </section>

    <!-- 原实时考试监控模块已完整删除 -->

    <!-- 新增或编辑考试 -->
    <el-dialog v-model="editDialogVisible" :title="editingExamId ? '编辑本学期考试' : '新增本学期考试'" width="580px" append-to-body>
      <el-form label-position="top" :model="editForm" class="exam-form">
        <el-form-item label="考试名称" required><el-input v-model="editForm.name" maxlength="160" /></el-form-item>
        <div class="form-row">
          <el-form-item label="课程" required><el-select v-model="editForm.course" filterable placeholder="请选择课程" style="width:100%"><el-option v-for="c in courses" :key="c.id" :label="c.code + ' · ' + c.name" :value="c.id" /></el-select></el-form-item>
          <el-form-item label="考试类型"><el-select v-model="editForm.exam_type" style="width:100%"><el-option label="期末考试" value="期末考试"/><el-option label="期中考试" value="期中考试"/><el-option label="补考" value="补考"/><el-option label="课程考核" value="课程考核"/></el-select></el-form-item>
        </div>
        <div class="form-row">
          <el-form-item label="考试开始日期与时间" required><el-input v-model="editForm.localDateTime" type="datetime-local" /></el-form-item>
          <el-form-item label="考试时长（分钟）" required><el-input-number v-model="editForm.duration" :min="10" :max="480" style="width:100%" /></el-form-item>
        </div>
        <el-form-item label="考场地点"><el-input v-model.trim="editForm.location" maxlength="120" placeholder="尚未确定可暂留空" /></el-form-item>
        <p class="module-hint">保存的是考试基本信息。专业年级归属暂时只能维护本机草稿，监考与考生名单需后端进一步支持。</p>
      </el-form>
      <template #footer><el-button @click="editDialogVisible=false">取消</el-button><el-button type="primary" :loading="savingExam" @click="saveExam">保存考试</el-button></template>
    </el-dialog>

    <!-- 专业与年级归属当前后端缺字段，本机草稿明确标注 -->
    <el-dialog v-model="scopeDialogVisible" title="关联适用专业与年级（本机草稿）" width="490px" append-to-body>
      <p class="module-hint">当前考试接口尚无专业、年级或行政班关联字段。此处只保存到当前浏览器，换设备后无法同步，也不代表正式排考。</p>
      <el-form label-position="top">
        <el-form-item label="适用专业"><el-select v-model="scopeMajor" placeholder="待关联" clearable style="width:100%"><el-option v-for="m in majors" :key="m" :label="m" :value="m" /></el-select></el-form-item>
        <el-form-item label="适用入学年级"><el-select v-model="scopeGrade" clearable placeholder="待关联" style="width:100%"><el-option v-for="g in grades" :key="g" :label="g+'级'" :value="g" /></el-select></el-form-item>
      </el-form>
      <template #footer><el-button @click="scopeDialogVisible=false">取消</el-button><el-button type="primary" @click="saveScope">保存本机草稿</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import api from '@/api/index'

interface Semester { id: number; name: string; academic_year?: string; term?: string; is_current?: boolean }
interface Course { id: number; name: string; code: string }
interface ExamData { id: number; name: string; course: number; course_name?: string; semester: number; exam_type?: string; exam_date: string; duration: number; total_score?: number; location: string }
interface ExamRow { id: number; name: string; course: number; courseName: string; examType: string; raw: ExamData; date: string; time: string; location: string; status: string; statusKey: string; startMs: number; endMs: number }
interface ScopeDraft { major: string; grade: string }
interface CalendarCell { key: string; day: number; inMonth: boolean; isToday: boolean; isReferenceWeek: boolean; count: number }

const majors = ['行政管理', '政治学与行政学', '国际政治', '科学社会主义', '行政管理+电子科学与技术双学位', '国际政治＋英语双学位']
const grades = ['2022', '2023', '2024', '2025', '2026']
const weekdays = ['日','一','二','三','四','五','六']
const todayStr = formatDate(new Date())
const firstTeachingDate = new Date(2026, 7, 31)
const calendarDate = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1))
const selectedDate = ref(todayStr)
const loading = ref(false)
const loadError = ref('')
const currentSemesterId = ref<number | null>(null)
const courseRows = ref<Course[]>([])
const rawExams = ref<ExamData[]>([])
const venueChartRef = ref<HTMLElement | null>(null)
const progressChartRef = ref<HTMLElement | null>(null)
let venueChart: echarts.ECharts | null = null
let progressChart: echarts.ECharts | null = null

function formatDate(d: Date): string {
  return [d.getFullYear(), String(d.getMonth() + 1).padStart(2, '0'), String(d.getDate()).padStart(2, '0')].join('-')
}
function isAcademicWindow(d: Date): boolean {
  const normalized = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const week = Math.floor((normalized.getTime() - firstTeachingDate.getTime()) / 604800000) + 1
  return week === 18 || week === 19
}
function semesterMatches(s: Semester): boolean {
  const name = String(s.name ?? '').replace(/[—–]/g, '-').replace(/\s+/g, '')
  const year = String(s.academic_year ?? '').replace(/[—–]/g, '-')
  const term = String(s.term ?? '').toLowerCase()
  return (name.includes('2026-2027') && /第一学期|第1学期|2026-2027-1|秋季|秋/.test(name)) ||
    (year.includes('2026-2027') && ['first', '1', '第一学期', '秋季'].includes(term))
}
function unwrap<T>(data: unknown): { items: T[]; next: boolean; count?: number } {
  const v = data as { data?: unknown; results?: T[]; next?: string | null; count?: number } | null
  const item = v?.data && !Array.isArray(v.data) && (v.data as { results?: T[] }).results ? v.data : data
  if (Array.isArray(item)) return { items: item as T[], next: false }
  const obj = item as { results?: T[]; data?: T[]; next?: string | null; count?: number } | null
  return { items: Array.isArray(obj?.results) ? obj.results : Array.isArray(obj?.data) ? obj.data : [], next: !!obj?.next, count: obj?.count }
}
async function fetchAll<T>(url: string): Promise<T[]> {
  const result: T[] = []
  for (let page = 1; page <= 80; page++) {
    const body = await api.get(url, { params: { page, page_size: 200 } }) as unknown
    const chunk = unwrap<T>(body)
    result.push(...chunk.items)
    if (!chunk.next || !chunk.items.length || (typeof chunk.count === 'number' && result.length >= chunk.count)) break
  }
  return result
}
async function refreshData(): Promise<void> {
  loading.value = true
  loadError.value = ''
  try {
    const terms = await fetchAll<Semester>('/semesters/')
    const semester = terms.find(semesterMatches)
    currentSemesterId.value = semester?.id ?? null
    if (semester) {
      const [exams, courses] = await Promise.all([fetchAll<ExamData>('/exams/'), fetchAll<Course>('/courses/')])
      rawExams.value = exams.filter(e => Number(e.semester) === Number(semester.id))
      courseRows.value = courses
    } else { rawExams.value = []; courseRows.value = [] }
    await nextTick()
    drawCharts()
  } catch {
    rawExams.value = []
    loadError.value = '读取本学期考试数据失败，请检查网络、权限及 /api/semesters/、/api/exams/ 接口。'
    ElMessage.error('考试信息读取失败')
  } finally { loading.value = false }
}
const allExams = computed<ExamRow[]>(() => rawExams.value.map(e => {
  const start = new Date(e.exam_date)
  const startMs = start.getTime()
  const endMs = startMs + Math.max(10, Number(e.duration) || 120) * 60000
  const valid = Number.isFinite(startMs)
  const date = valid ? formatDate(start) : ''
  const timeOf = (d: Date) => String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
  const time = valid ? `${timeOf(start)}—${timeOf(new Date(endMs))}` : '待安排'
  const statusKey = valid && Date.now() >= endMs ? 'done' : valid && Date.now() >= startMs ? 'active' : 'pending'
  return {
    id: e.id, name: e.name, course: e.course,
    courseName: e.course_name || courseRows.value.find(c => Number(c.id) === Number(e.course))?.name || '课程待关联',
    examType: e.exam_type || '', raw: e, date, time, location: e.location || '', startMs, endMs,
    statusKey, status: statusKey === 'done' ? '已结束' : statusKey === 'active' ? '进行中' : '待开始',
  }
}))
const sortedExams = computed(() => [...allExams.value].sort((a, b) => a.startMs - b.startMs))
const stats = computed(() => {
  const exams = allExams.value
  const venues = new Set(exams.filter(e => !!e.location).map(e => e.location))
  return [
    { label: '本学期考试', value: exams.length, unit: '场', desc: '已登记的考试场次' },
    { label: '已登记考场', value: venues.size, unit: '处', desc: '按考场名称去重' },
    { label: '第18—19周排考', value: exams.filter(e => e.date && isAcademicWindow(new Date(`${e.date}T12:00:00`))).length, unit: '场', desc: '参考考试周内的已登记考试' },
    { label: '地点待安排', value: exams.filter(e => !e.location).length, unit: '场', desc: '需补充考场信息' },
  ]
})

// 本机草稿特意与学校数据库考试信息分开，防止误认为正式教务记录。
const draftKey = 'sdu-exam-major-grade-2026-2027-first-draft'
const scopes = ref<Record<number, ScopeDraft>>({})
try {
  const old = window.localStorage.getItem(draftKey)
  if (old) scopes.value = JSON.parse(old) as Record<number, ScopeDraft>
} catch { scopes.value = {} }
const filterMajor = ref('')
const filterGrade = ref('')
const examQuery = ref('')
function scopeOf(id: number): ScopeDraft | undefined {
  const s = scopes.value[id]
  return s?.major && s?.grade ? s : undefined
}
function scopeLabel(id: number): string { const s = scopeOf(id); return s ? `${s.major} · ${s.grade}级` : '尚未关联' }
const scopedExams = computed(() => sortedExams.value.filter(e => {
  const scope = scopeOf(e.id)
  const q = examQuery.value.trim().toLowerCase()
  return (!filterMajor.value || scope?.major === filterMajor.value) &&
    (!filterGrade.value || scope?.grade === filterGrade.value) &&
    (!q || `${e.name} ${e.courseName} ${e.location}`.toLowerCase().includes(q))
}))
function resetFilters(): void { filterMajor.value = ''; filterGrade.value = ''; examQuery.value = '' }
function exportCsv(): void {
  const data = [
    ['日期', '时间', '考试名称', '课程名称', '考核类型', '考场', '适用专业', '适用年级', '关联数据性质'],
    ...scopedExams.value.map(e => [e.date, e.time, e.name, e.courseName, e.examType, e.location,
      scopeOf(e.id)?.major ?? '', scopeOf(e.id)?.grade ?? '', '专业年级关联仅为本机草稿']),
  ]
  const csv = '\ufeff' + data.map(row => row.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
  const a = document.createElement('a')
  a.href = url; a.download = '2026-2027-1_专业年级考试安排_草稿.csv'; a.click()
  URL.revokeObjectURL(url)
}
const scopeDialogVisible = ref(false)
const scopeId = ref<number | null>(null)
const scopeMajor = ref('')
const scopeGrade = ref('')
function editScope(id: number): void {
  scopeId.value = id
  scopeMajor.value = scopes.value[id]?.major ?? ''
  scopeGrade.value = scopes.value[id]?.grade ?? ''
  scopeDialogVisible.value = true
}
function saveScope(): void {
  if (scopeId.value == null) return
  scopes.value = { ...scopes.value, [scopeId.value]: { major: scopeMajor.value, grade: scopeGrade.value } }
  try { window.localStorage.setItem(draftKey, JSON.stringify(scopes.value)) }
  catch { ElMessage.warning('浏览器未允许存储，关联只能保留在当前页面') }
  scopeDialogVisible.value = false
  ElMessage.success('已保存本机排考关联草稿，尚未提交到学校服务器')
}

// 年月使用 Date 进行进位，不再写死 2024 年六月。
const calendarTitle = computed(() => `${calendarDate.value.getFullYear()}年${calendarDate.value.getMonth() + 1}月`)
function changeMonth(delta: number): void {
  calendarDate.value = new Date(calendarDate.value.getFullYear(), calendarDate.value.getMonth() + delta, 1)
}
const calendarCells = computed<CalendarCell[]>(() => {
  const year = calendarDate.value.getFullYear()
  const month = calendarDate.value.getMonth()
  const firstDay = new Date(year, month, 1).getDay()
  const days = new Date(year, month + 1, 0).getDate()
  const total = Math.ceil((firstDay + days) / 7) * 7
  return Array.from({ length: total }, (_, i) => {
    const d = new Date(year, month, i - firstDay + 1)
    const key = formatDate(d)
    return { key, day: d.getDate(), inMonth: d.getMonth() === month, isToday: key === todayStr,
      isReferenceWeek: isAcademicWindow(d), count: allExams.value.filter(e => e.date === key).length }
  })
})
function selectDate(c: CalendarCell): void {
  selectedDate.value = c.key
  if (!c.inMonth) calendarDate.value = new Date(Number(c.key.slice(0, 4)), Number(c.key.slice(5, 7)) - 1, 1)
}
const selectedExams = computed(() => sortedExams.value.filter(e => e.date === selectedDate.value))

// 仅进行同一考场、考试时间重叠的可核验冲突检查。
const conflicts = computed(() => {
  const list = allExams.value.filter(e => e.location && Number.isFinite(e.startMs))
  const output: Array<{ id: number; detail: string }> = []
  for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) {
    const a = list[i], b = list[j]
    if (!a || !b || a.location !== b.location) continue
    if (a.startMs < b.endMs && b.startMs < a.endMs) output.push({ id: output.length + 1,
      detail: `${a.location}：${a.name}（${a.date} ${a.time}）与 ${b.name}（${b.date} ${b.time}）考试时间重叠` })
  }
  return output
})
const venues = computed(() => {
  const counter = new Map<string, number>()
  allExams.value.forEach(e => { if (e.location) counter.set(e.location, (counter.get(e.location) ?? 0) + 1) })
  return [...counter].map(([name, count]) => ({ name, count }))
})
const timeline = computed(() => {
  const points = [
    { date: '2026-08-31', title: '秋季学期开始上课', note: '学校2026年秋季学期开学安排' },
    { date: '2026-12-28', title: '第18周开始', note: '排考参考窗口，非已确认统一考试周' },
    { date: '2027-01-04', title: '第19周开始', note: '排考参考窗口，非已确认统一考试周' },
  ]
  allExams.value.filter(e => e.date).forEach(e => points.push({ date: e.date, title: e.name, note: `${e.time} · ${e.location || '地点待安排'}` }))
  return points.sort((a, b) => a.date.localeCompare(b.date))
})

const editDialogVisible = ref(false)
const editingExamId = ref<number | null>(null)
const savingExam = ref(false)
const editForm = ref({ name: '', course: 0, exam_type: '期末考试', localDateTime: '', duration: 120, location: '' })
const courses = computed(() => courseRows.value)
function openNewExam(): void {
  if (!currentSemesterId.value) { ElMessage.warning('请先在教务系统建立2026—2027学年第一学期'); return }
  editingExamId.value = null
  editForm.value = { name: '', course: 0, exam_type: '期末考试', localDateTime: '', duration: 120, location: '' }
  editDialogVisible.value = true
}
function toLocalInput(dateString: string): string {
  const d = new Date(dateString)
  if (!Number.isFinite(d.getTime())) return ''
  return `${formatDate(d)}T${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function editExam(e: ExamRow): void {
  editingExamId.value = e.id
  editForm.value = { name: e.name, course: e.course, exam_type: e.examType,
    localDateTime: toLocalInput(e.raw.exam_date), duration: e.raw.duration, location: e.location }
  editDialogVisible.value = true
}
async function saveExam(): Promise<void> {
  const f = editForm.value
  if (!currentSemesterId.value) { ElMessage.error('本学期未建立，无法保存考试'); return }
  if (!f.name || !f.course || !f.localDateTime || !Number.isFinite(f.duration) || f.duration < 10) {
    ElMessage.warning('请填写考试名称、课程、时间及有效的考试时长'); return
  }
  const date = new Date(f.localDateTime)
  if (!Number.isFinite(date.getTime())) { ElMessage.warning('请输入有效的考试时间'); return }
  const payload = {
    name: f.name, course: f.course, semester: currentSemesterId.value,
    exam_type: f.exam_type, exam_date: date.toISOString(), duration: f.duration,
    total_score: editingExamId.value == null ? 100 : rawExams.value.find(e => e.id === editingExamId.value)?.total_score ?? 100,
    location: f.location,
  }
  savingExam.value = true
  try {
    if (editingExamId.value != null) await api.patch(`/exams/${editingExamId.value}/`, payload)
    else await api.post('/exams/', payload)
    editDialogVisible.value = false
    ElMessage.success('考试信息已由教务接口保存')
    await refreshData()
  } catch { ElMessage.error('保存失败，请检查权限、考试日期和后端字段校验') }
  finally { savingExam.value = false }
}

function drawCharts(): void {
  if (venueChartRef.value && venues.value.length) {
    venueChart = venueChart || echarts.init(venueChartRef.value)
    venueChart.setOption({ tooltip: { trigger: 'axis' }, grid: { left: 90, top: 16, right: 42, bottom: 18 },
      xAxis: { type: 'value', minInterval: 1, axisLabel: { color: '#91A0BA' } },
      yAxis: { type: 'category', data: venues.value.map(v => v.name), axisLabel: { color: '#59677F' } },
      series: [{ type: 'bar', data: venues.value.map(v => v.count), barWidth: 15,
        itemStyle: { color: '#3477E7', borderRadius: [0, 5, 5, 0] }, label: { show: true, position: 'right' } }] })
  }
  if (progressChartRef.value && allExams.value.length) {
    progressChart = progressChart || echarts.init(progressChartRef.value)
    progressChart.setOption({ tooltip: { trigger: 'item' }, legend: { bottom: 0 },
      series: [{ type: 'pie', radius: ['44%', '68%'], center: ['50%', '44%'],
        data: [
          { name: '待开始', value: allExams.value.filter(e => e.statusKey === 'pending').length, itemStyle: { color: '#A8C8FF' } },
          { name: '进行中', value: allExams.value.filter(e => e.statusKey === 'active').length, itemStyle: { color: '#37BFA2' } },
          { name: '已结束', value: allExams.value.filter(e => e.statusKey === 'done').length, itemStyle: { color: '#21418E' } },
        ] }] })
  }
}
function resizeCharts(): void { venueChart?.resize(); progressChart?.resize() }
onMounted(async () => { await nextTick(); await refreshData(); window.addEventListener('resize', resizeCharts) })
onUnmounted(() => { venueChart?.dispose(); progressChart?.dispose(); window.removeEventListener('resize', resizeCharts) })
</script>

<style scoped>
.exam-hub { --title:#13284B;--muted:#94A4BF;--blue:#224493;--border:#E7ECF5;max-width:100%;padding:22px 24px 28px;background:#F5F7FA;color:#364563;box-sizing:border-box;min-height:100%;font-family:inherit }
* { box-sizing:border-box }
.hub-topbar { display:flex;align-items:center;justify-content:space-between;gap:20px;margin:6px 0 18px }
.hub-title { margin:0;font-size:23px;font-weight:750;color:#122649;letter-spacing:-.3px;display:flex;align-items:center;gap:10px }
.title-symbol { color:#2858BA;font-size:24px;font-weight:400 }
.hub-subtitle { margin:8px 0 0;color:#94A4BC;font-size:12px }
.hub-actions { display:flex;align-items:center;gap:8px;flex-wrap:wrap }
.semester-tag { font-size:12px;background:#EAF1FF;border:1px solid #DBE7FF;border-radius:9px;color:#234791;font-weight:650;padding:11px 14px;white-space:nowrap }
.btn-primary,.btn-outline { cursor:pointer;white-space:nowrap;border-radius:9px;min-height:38px;padding:0 15px;font-size:12px;font-weight:650 }
.btn-primary { color:white;background:#23428E;border:1px solid #23428E }
.btn-outline { background:white;color:#264B98;border:1px solid #DDE6F4 }
.btn-primary:disabled,.btn-outline:disabled { cursor:not-allowed;opacity:.55 }
.status-note { display:flex;gap:9px;align-items:center;background:#EDF4FF;padding:11px 13px;border-radius:10px;font-size:11px;color:#637DA5;margin-bottom:18px;line-height:1.6 }
.status-note.note-warning { background:#FFF6EC;color:#9E7849 }
.note-dot { flex:0 0 7px;height:7px;background:#3A8BE8;border-radius:50% }
.note-warning .note-dot { background:#EAB260 }
.hub-stats-row { display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:18px }
.hub-stat-card,.hub-panel { background:white;border:1px solid var(--border);border-radius:13px;box-shadow:0 6px 24px rgba(31,53,100,.018) }
.hub-stat-card { display:flex;gap:14px;align-items:center;min-height:116px;padding:18px }
.stat-icon { width:47px;height:47px;border-radius:12px;background:#EDF4FE;color:#244A9A;display:grid;place-items:center;font-size:25px;flex:0 0 auto }
.stat-icon.icon-1 { background:#E5F1FD;color:#4D8FF3 }
.stat-icon.icon-2 { background:#DDEAFE;color:#3F7BDF }
.stat-icon.icon-3 { background:#F2F4F8;color:#71809B }
.stat-copy { min-width:0 }
.stat-copy p { margin:0 }
.stat-label { color:#9BA7BD;font-size:12px }
.stat-value { color:#1D2C43;font-size:27px;font-weight:760;margin-top:4px!important;white-space:nowrap }
.stat-value small { font-weight:400;font-size:12px;color:#91A0B8;margin-left:5px }
.stat-desc { color:#9DAABE;font-size:10px;margin-top:4px!important;line-height:1.5 }
.hub-panel { min-width:0;padding:20px;margin-bottom:18px }
.full-panel { width:100% }
.panel-head { display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px }
.panel-head h3 { margin:0;display:flex;align-items:center;gap:9px;color:#162C4C;font-size:15px;font-weight:720 }
.panel-sub { color:#9BAAC1;font-size:11px;margin:7px 0 0 13px;line-height:1.5 }
.accent { display:inline-block;background:#307CF1;width:4px;height:17px;border-radius:4px }
.panel-badge { white-space:nowrap;background:#EAF2FF;color:#2950A0;padding:6px 10px;border-radius:7px;font-size:11px }
.badge-danger { background:#FFF0F0;color:#D34145 }
.filters-bar { display:flex;align-items:flex-end;gap:10px;flex-wrap:wrap;background:#F7F9FD;padding:13px;border:1px solid #EFF2F8;border-radius:10px;margin-bottom:12px }
.filters-bar label { display:flex;flex-direction:column;gap:7px;font-size:11px;color:#899AB2;min-width:130px }
.filters-bar input,.filters-bar select { border:1px solid #E0E7F3;background:white;padding:9px 11px;color:#455674;border-radius:8px;font-size:12px;min-height:37px;outline:none }
.filters-bar .search-control { flex:1;min-width:180px }
.filters-bar .btn-outline { height:37px;min-height:37px }
.table-scroll { overflow-x:auto }
.data-table { width:100%;border-collapse:collapse;min-width:850px;font-size:12px }
.data-table th { text-align:left;background:#F5F7FB;color:#8797AF;font-size:11px;font-weight:600;padding:13px 12px;white-space:nowrap }
.data-table td { border-bottom:1px solid #F1F3F7;padding:13px 12px;line-height:1.5;vertical-align:middle;color:#50617D }
.data-table tbody tr:hover { background:#FAFCFF }
.data-table td strong { font-weight:650;color:#233856 }
.data-table td small { display:block;margin-top:4px;color:#9CAAC1;font-size:10px }
.data-table .muted,.muted { color:#A3AEC0 }
.cell-actions { white-space:nowrap }
.cell-actions button { border:0;background:none;color:#2D66C8;cursor:pointer;font-size:11px;margin-right:5px;padding:4px }
.state-tag { font-size:10px;padding:5px 7px;border-radius:6px;white-space:nowrap }
.state-pending { background:#EFF5FF;color:#416DBB }.state-active { background:#E7F9F1;color:#23A482 }.state-done { background:#F0F2F6;color:#7F8A9D }
.empty-cell { text-align:center;color:#97A5B9!important;padding:28px!important }
.module-hint { color:#94A2B8;background:#F8FAFE;border-radius:8px;margin:12px 0 0;padding:10px 12px;line-height:1.7;font-size:11px }
.academic-items { display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px }
.academic-items div { background:#F5F8FE;border:1px solid #EEF3FC;border-radius:9px;padding:13px;display:flex;flex-direction:column;gap:9px }
.academic-items span { font-size:11px;color:#899AB5 }.academic-items strong { color:#2F4984;font-size:15px }.academic-items small { color:#A0ADC1;font-size:10px }
.hub-row-2col { display:grid;grid-template-columns:1fr 1fr;gap:16px }
.hub-row-3col { display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px }
.hub-row-2col>.hub-panel,.hub-row-3col>.hub-panel { min-width:0 }
.cal-navigation { display:flex;align-items:center;gap:10px;color:#1B2C47;font-size:12px }
.cal-navigation button { width:27px;height:28px;background:white;border:1px solid #EEF0F5;border-radius:7px;color:#50627E;cursor:pointer;font-size:18px }
.calendar-grid { display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px }
.weekday { text-align:center;font-size:11px;color:#9BA9BF;padding:10px 0;font-weight:600 }
.calendar-day { border:1px solid transparent;height:64px;border-radius:8px;background:white;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;font-size:12px;color:#3A4C6C;cursor:pointer;padding:3px }
.calendar-day.other-month { opacity:.3 }
.calendar-day.is-window { background:#EDF4FF }
.calendar-day.is-today { border-color:#94B8F0 }
.calendar-day.is-selected { background:#E5F0FF;border-color:#7CA9EB;color:#19418A;font-weight:700 }
.calendar-day:hover { background:#F0F6FF }
.calendar-day small { font-size:9px;color:#6284BF }
.exam-dots { display:flex;gap:3px }.exam-dots i { width:5px;height:5px;border-radius:50%;background:#4C98FB }
.calendar-hint { color:#99A6BA;font-size:10px;line-height:1.6;margin:10px 0 0 }
.day-list { display:flex;flex-direction:column;gap:9px }.day-exam { display:flex;align-items:center;gap:11px;background:#F7F9FD;border-radius:9px;padding:13px 10px;font-size:11px }
.day-exam>b { white-space:nowrap;font-size:11px;color:#233A5C }.day-exam>div { min-width:0;flex:1 }
.day-exam strong,.day-exam small { display:block }.day-exam strong { color:#243753;font-size:12px }.day-exam small { color:#97A8BF;margin-top:4px }
.day-exam-room { color:#8094B1 }.day-empty { display:flex;align-items:center;flex-direction:column;justify-content:center;text-align:center;min-height:265px;color:#A0AEC4;font-size:11px }
.day-empty span { font-size:27px;color:#9FBAE6 }.day-empty strong { font-size:13px;margin-top:9px }.day-empty p { font-size:11px;margin-top:6px }
.chart-holder { height:300px;width:100% }.chart-holder.compact { height:255px }
.panel-empty { min-height:180px;display:flex;justify-content:center;align-items:center;flex-direction:column;text-align:center;color:#9AABC3;line-height:1.8;font-size:12px;background:#F8FAFD;border-radius:9px;margin-top:10px;padding:22px }
.panel-empty strong { color:#7588A5;font-size:13px }.panel-empty p { margin:6px 0 0;max-width:300px }
.conflict-list { display:flex;flex-direction:column;gap:10px }.conflict-item { padding:12px;background:#FFF4F4;border-left:3px solid #E24A50;display:flex;gap:12px;border-radius:8px }
.conflict-item>span { display:grid;place-items:center;color:#CF373F;background:#FFE4E6;border-radius:6px;min-width:24px;height:24px;font-weight:800 }
.conflict-item strong { color:#9F2F36;font-size:12px }.conflict-item p { font-size:11px;color:#BA6770;margin:4px 0 0;line-height:1.6 }
.timeline-list { display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px }
.timeline-entry { border-left:2px solid #D9E5F8;padding:0 0 4px 14px;position:relative;display:flex;flex-direction:column;gap:5px;font-size:12px }
.timeline-point { width:9px;height:9px;position:absolute;left:-5.5px;top:3px;background:#5798EE;border-radius:50% }
.timeline-entry>strong { color:#2853AB }.timeline-entry b { font-size:12px;color:#334967 }.timeline-entry p { margin:5px 0 0;font-size:11px;color:#9AA8BD;line-height:1.6 }
.timeline-past .timeline-point { background:#A3B5D1 }.small-footnote { font-size:10px;color:#9CA9BC }
.form-row { display:grid;grid-template-columns:1fr 1fr;gap:12px }.form-row :deep(.el-form-item) { min-width:0 }
@media(max-width:1480px){.hub-stats-row { grid-template-columns:repeat(2,minmax(0,1fr)) }.academic-items { grid-template-columns:repeat(2,minmax(0,1fr)) }}
@media(max-width:1120px){.hub-row-2col,.hub-row-3col { grid-template-columns:1fr }.timeline-list { grid-template-columns:repeat(2,minmax(0,1fr)) }}
@media(max-width:700px){.exam-hub{padding:15px}.hub-topbar{flex-direction:column;align-items:flex-start}.hub-stats-row,.academic-items,.timeline-list,.form-row{grid-template-columns:1fr}.filters-bar label{width:100%}.filters-bar .search-control{width:100%} }
</style>
