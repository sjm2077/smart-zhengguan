<template>
  <section class="grades-page">
    <header class="page-hero">
      <div class="hero-copy">
        <div class="eyebrow">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/><path d="M9 7h7M9 11h7"/></svg>
          TEACHING PERFORMANCE
        </div>
        <h1>成绩管理</h1>
        <p>集中查询本人授课范围内的成绩记录，了解课程表现与成绩分布。</p>
        <div class="hero-tags"><span><i></i> 教师专属空间</span><span><i></i> 成绩数据来自现有教务接口</span></div>
      </div>
      <div class="hero-side" aria-hidden="true">
        <div class="hero-emblem"><svg viewBox="0 0 120 120"><path d="M20 93h80"/><path d="M30 83V62h15v21M53 83V42h15v41M76 83V27h15v56"/><path d="m26 45 24-15 17 6 27-22"/><path d="M83 14h11v11"/></svg></div>
        <span class="hero-side-caption">GRADE OVERVIEW</span>
      </div>
    </header>

    <div class="summary-grid">
      <article class="summary-card"><div class="summary-icon summary-icon-blue"><svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/></svg></div><div class="summary-copy"><span>当前筛选记录</span><strong>{{ filteredGrades.length }}</strong><small>符合当前查询条件的成绩记录</small></div></article>
      <article class="summary-card"><div class="summary-icon summary-icon-teal"><svg viewBox="0 0 24 24"><path d="M3 3v18h18M7 14l4-4 4 3 5-7"/></svg></div><div class="summary-copy"><span>平均成绩</span><strong>{{ averageScore === null ? '—' : averageScore.toFixed(1) }}</strong><small>仅统计存在有效分数的记录</small></div></article>
      <article class="summary-card"><div class="summary-icon summary-icon-violet"><svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18"/><circle cx="12" cy="12" r="9"/></svg></div><div class="summary-copy"><span>及格率</span><strong>{{ passRate === null ? '—' : `${passRate.toFixed(1)}%` }}</strong><small>按百分制 60 分及格口径计算</small></div></article>
      <article class="summary-card"><div class="summary-icon summary-icon-amber"><svg viewBox="0 0 24 24"><path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2L12 17.3l-5.6 2.9 1.1-6.2L3 9.6l6.2-.9L12 3Z"/></svg></div><div class="summary-copy"><span>90 分及以上</span><strong>{{ excellentCount }}</strong><small>当前筛选结果中的高分记录</small></div></article>
    </div>

    <div class="insight-grid">
      <section class="panel distribution-panel">
        <div class="panel-heading"><div><div class="heading-title-row"><span class="heading-accent"></span><h2>成绩分布</h2></div><p>按当前筛选结果统计，分数缺失的记录不纳入分布。</p></div><span class="subtle-count">{{ scoredGrades.length }} 条有效分数</span></div>
        <div v-if="scoredGrades.length" class="distribution-list">
          <div v-for="bucket in scoreDistribution" :key="bucket.label" class="distribution-row">
            <span class="distribution-label">{{ bucket.label }}</span>
            <div class="distribution-track"><span :class="bucket.className" :style="{ width: `${bucket.percent}%` }"></span></div>
            <strong>{{ bucket.count }}</strong><small>{{ bucket.percent.toFixed(0) }}%</small>
          </div>
        </div>
        <div v-else class="mini-empty">当前筛选结果中暂无可用于统计的成绩分数。</div>
      </section>
      <section class="panel course-panel">
        <div class="panel-heading"><div><div class="heading-title-row"><span class="heading-accent"></span><h2>课程成绩概览</h2></div><p>查看不同课程在当前筛选结果中的记录量与平均成绩。</p></div></div>
        <div v-if="courseSummaries.length" class="course-summary-list">
          <div v-for="course in courseSummaries.slice(0, 4)" :key="course.name" class="course-summary-row">
            <div class="course-summary-main"><strong>{{ course.name }}</strong><span>{{ course.count }} 条记录</span></div>
            <div class="course-average"><strong>{{ course.average === null ? '—' : course.average.toFixed(1) }}</strong><span>平均分</span></div>
            <div class="course-mini-track"><span :style="{ width: `${course.average === null ? 0 : Math.max(0, Math.min(course.average, 100))}%` }"></span></div>
          </div>
        </div>
        <div v-else class="mini-empty">当前筛选结果暂无课程成绩数据。</div>
      </section>
    </div>

    <section class="grades-panel">
      <div class="panel-heading">
        <div><div class="heading-title-row"><span class="heading-accent"></span><h2>成绩记录</h2></div><p>可按学生、课程、教学班、考试类型或学期查找。页面只展示接口实际返回的数据。</p></div>
        <div class="heading-actions">
          <button class="secondary-button" type="button" :disabled="loading" @click="loadGrades"><svg :class="{ spinning: loading }" viewBox="0 0 24 24"><path d="M20 7v5h-5M4.5 9A8 8 0 0 1 18 5l2 2M4 17v-5h5M19.5 15A8 8 0 0 1 6 19l-2-2"/></svg>{{ loading ? '正在刷新' : '刷新成绩' }}</button>
          <button class="primary-button" type="button" :disabled="!filteredGrades.length" @click="exportCsv"><svg viewBox="0 0 24 24"><path d="M12 3v12m-5-5 5 5 5-5M4 17v4h16v-4"/></svg>导出当前结果</button>
        </div>
      </div>

      <div class="filter-bar">
        <label class="search-box"><svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg><input v-model.trim="keyword" type="search" placeholder="搜索学生、课程名称、课程代码或教学班" aria-label="搜索成绩" /></label>
        <label class="filter-control"><span>课程</span><select v-model="selectedCourse"><option value="all">全部课程</option><option v-for="course in courseOptions" :key="course" :value="course">{{ course }}</option></select></label>
        <label class="filter-control"><span>考试类型</span><select v-model="selectedExamType"><option value="all">全部类型</option><option v-for="type in examTypeOptions" :key="type" :value="type">{{ type }}</option></select></label>
        <label class="filter-control"><span>成绩范围</span><select v-model="selectedBand"><option value="all">全部分数</option><option value="excellent">90 分及以上</option><option value="good">80–89 分</option><option value="pass">60–79 分</option><option value="fail">60 分以下</option><option value="missing">未录入分数</option></select></label>
      </div>

      <div v-if="errorMessage" class="state-message state-error"><strong>成绩信息暂时无法加载</strong><span>{{ errorMessage }}</span><button type="button" @click="loadGrades">重试</button></div>
      <div v-else-if="loading && !loaded" class="state-message">正在加载当前教师授权范围内的成绩记录…</div>
      <template v-else>
        <div class="result-meta"><span>共 {{ grades.length }} 条已加载记录</span><span>筛选后 {{ filteredGrades.length }} 条 · 当前显示 {{ pagedGrades.length }} 条</span></div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>学生</th><th>课程 / 教学班</th><th>考试类型</th><th>学期</th><th>成绩</th><th>成绩状态</th><th>操作</th></tr></thead>
            <tbody>
              <tr v-for="grade in pagedGrades" :key="grade.id">
                <td><div class="student-cell"><span class="student-avatar">{{ avatarText(grade.studentName) }}</span><span><strong>{{ grade.studentName || '学生信息未提供' }}</strong><small>{{ grade.studentCode || '学号暂未提供' }}</small></span></div></td>
                <td><div class="course-cell"><strong>{{ grade.courseName || '课程信息未提供' }}</strong><small>{{ grade.className || grade.courseCode || '教学班信息暂未提供' }}</small></div></td>
                <td>{{ grade.examType || '未注明' }}</td>
                <td>{{ grade.semesterName || '暂未提供' }}</td>
                <td><span class="score-pill" :class="scoreClass(grade.score)">{{ grade.score === null ? '—' : grade.score.toFixed(2).replace(/\.00$/, '') }}</span></td>
                <td><span class="status-pill" :class="statusClass(grade.score)">{{ statusLabel(grade.score) }}</span></td>
                <td><button class="table-action" type="button" @click="selectedGrade = grade">查看详情 <span aria-hidden="true">→</span></button></td>
              </tr>
              <tr v-if="!filteredGrades.length"><td colspan="7"><div class="table-empty"><strong>{{ grades.length ? '没有符合条件的成绩记录' : '当前账号暂无可展示的成绩记录' }}</strong><span>{{ grades.length ? '请调整筛选条件后重试。' : '请检查成绩数据是否已录入，以及后端是否已正确关联教师与授课范围。' }}</span><button v-if="keyword || selectedCourse !== 'all' || selectedExamType !== 'all' || selectedBand !== 'all'" type="button" @click="clearFilters">清除筛选</button></div></td></tr>
            </tbody>
          </table>
        </div>
        <div class="pagination" v-if="filteredGrades.length"><span>第 {{ page }} / {{ totalPages }} 页</span><div><button type="button" :disabled="page <= 1" @click="page--">上一页</button><button type="button" :disabled="page >= totalPages" @click="page++">下一页</button></div></div>
      </template>
      <p class="footnote">成绩仅供教学工作参考；查询范围及数据权限以服务端授权为准。本页面不新增、修改或删除成绩。</p>
    </section>

    <div v-if="selectedGrade" class="drawer-backdrop" role="presentation" @click.self="selectedGrade = null" @keydown.esc.window="selectedGrade = null">
      <aside class="detail-drawer" role="dialog" aria-modal="true" aria-labelledby="grade-detail-title">
        <header class="drawer-header"><div class="drawer-icon"><svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/><path d="M9 7h7M9 11h7"/></svg></div><div class="drawer-title"><small>GRADE RECORD DETAILS</small><h2 id="grade-detail-title">成绩记录详情</h2><p>{{ selectedGrade.courseName || '课程信息未提供' }}</p></div><button class="drawer-close" type="button" aria-label="关闭详情" @click="selectedGrade = null">×</button></header>
        <div class="drawer-body"><div class="score-highlight"><span>本条成绩</span><strong>{{ selectedGrade.score === null ? '—' : selectedGrade.score.toFixed(2).replace(/\.00$/, '') }}</strong><em :class="statusClass(selectedGrade.score)">{{ statusLabel(selectedGrade.score) }}</em></div><div class="drawer-section-title"><span></span> 基本信息</div><div class="detail-grid"><div class="detail-field"><small>学生姓名</small><strong>{{ selectedGrade.studentName || '暂未提供' }}</strong></div><div class="detail-field"><small>学生学号</small><strong>{{ selectedGrade.studentCode || '暂未提供' }}</strong></div><div class="detail-field"><small>课程名称</small><strong>{{ selectedGrade.courseName || '暂未提供' }}</strong></div><div class="detail-field"><small>课程代码</small><strong>{{ selectedGrade.courseCode || '暂未提供' }}</strong></div><div class="detail-field"><small>教学班</small><strong>{{ selectedGrade.className || '暂未提供' }}</strong></div><div class="detail-field"><small>考试类型</small><strong>{{ selectedGrade.examType || '未注明' }}</strong></div><div class="detail-field"><small>所属学期</small><strong>{{ selectedGrade.semesterName || '暂未提供' }}</strong></div><div class="detail-field"><small>记录编号</small><strong>{{ selectedGrade.id }}</strong></div><div class="detail-field"><small>记录时间</small><strong>{{ selectedGrade.recordDate || '接口未提供' }}</strong></div></div><p class="drawer-note">详情字段仅依据现有成绩接口返回内容展示；缺少的字段不会以演示数据补齐。</p></div>
        <footer class="drawer-footer"><button type="button" @click="selectedGrade = null">关闭</button></footer>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import api from '@/api/index'

interface GradeRecord {
  id: number | string
  studentName: string
  studentCode: string
  courseName: string
  courseCode: string
  className: string
  examType: string
  semesterName: string
  score: number | null
  recordDate: string
}

function textValue(...values: unknown[]): string {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) return value.trim()
    if (typeof value === 'number') return String(value)
  }
  return ''
}
function numericValue(...values: unknown[]): number | null {
  for (const value of values) {
    if (typeof value === 'number' && Number.isFinite(value)) return value
    if (typeof value === 'string' && value.trim() && Number.isFinite(Number(value))) return Number(value)
  }
  return null
}
function normalizeRows(payload: any): { rows: any[]; count: number | null; hasNext: boolean } {
  const outer = payload?.data ?? payload
  const source = outer?.data ?? outer
  const rows = Array.isArray(source) ? source : Array.isArray(source?.results) ? source.results : Array.isArray(source?.items) ? source.items : []
  const count = Number.isFinite(Number(source?.count)) ? Number(source.count) : null
  return { rows, count, hasNext: Boolean(source?.next) }
}
function normalizeGrade(row: any, index: number): GradeRecord {
  const student = row?.student && typeof row.student === 'object' ? row.student : {}
  const course = row?.course && typeof row.course === 'object' ? row.course : {}
  const teachingClass = row?.teaching_class && typeof row.teaching_class === 'object' ? row.teaching_class : row?.teachingClass && typeof row.teachingClass === 'object' ? row.teachingClass : {}
  const exam = row?.exam && typeof row.exam === 'object' ? row.exam : {}
  const score = numericValue(row?.score, row?.grade, row?.final_score, row?.total_score, row?.points, row?.value)
  const rawDate = textValue(row?.updated_at, row?.created_at, row?.exam_date, exam?.exam_date)
  let recordDate = rawDate
  if (rawDate) {
    const date = new Date(rawDate)
    if (!Number.isNaN(date.getTime())) recordDate = date.toLocaleDateString('zh-CN')
  }
  return {
    id: row?.id ?? `grade-${index}`,
    studentName: textValue(row?.student_name, student?.name, student?.student_name, student?.full_name, row?.student_display),
    studentCode: textValue(row?.student_code, row?.student_no, student?.student_no, student?.student_code, student?.code, row?.student_id),
    courseName: textValue(row?.course_name, course?.name, course?.title, row?.subject_name),
    courseCode: textValue(row?.course_code, course?.code, course?.course_code),
    className: textValue(row?.class_name, row?.teaching_class_name, teachingClass?.name, teachingClass?.class_name),
    examType: textValue(row?.exam_type_display, row?.exam_type_label, row?.exam_type, exam?.exam_type_display, exam?.name, exam?.title),
    semesterName: textValue(row?.semester_name, row?.semester, teachingClass?.semester_name, teachingClass?.semester?.name, course?.semester_name, exam?.semester_name),
    score,
    recordDate,
  }
}

const grades = ref<GradeRecord[]>([])
const loading = ref(false)
const loaded = ref(false)
const errorMessage = ref('')
const keyword = ref('')
const selectedCourse = ref('all')
const selectedExamType = ref('all')
const selectedBand = ref('all')
const selectedGrade = ref<GradeRecord | null>(null)
const page = ref(1)
const pageSize = 10

async function loadGrades() {
  loading.value = true
  errorMessage.value = ''
  try {
    const allRows: any[] = []
    let currentPage = 1
    let expectedCount: number | null = null
    // Read only the existing grades endpoint. Backend permissions define the teacher's data scope.
    while (currentPage <= 100) {
      const response = await api.get('/grades/', { params: { page: currentPage, page_size: 100 } })
      const result = normalizeRows(response)
      allRows.push(...result.rows)
      if (result.count !== null) expectedCount = result.count
      if (result.rows.length === 0) break
      if (result.hasNext) {
        currentPage += 1
        continue
      }
      if (expectedCount !== null) {
        if (allRows.length < expectedCount) {
          currentPage += 1
          continue
        }
        break
      }
      if (result.rows.length >= 100) {
        currentPage += 1
        continue
      }
      break
    }
    const unique = new Map<string, GradeRecord>()
    allRows.map(normalizeGrade).forEach((grade) => unique.set(String(grade.id), grade))
    grades.value = [...unique.values()]
    loaded.value = true
  } catch (error: any) {
    errorMessage.value = error?.response?.data?.detail || error?.response?.data?.message || error?.message || '请求成绩接口失败，请检查后端服务或登录状态。'
  } finally {
    loading.value = false
  }
}

const courseOptions = computed(() => [...new Set(grades.value.map(item => item.courseName).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'zh-CN')))
const examTypeOptions = computed(() => [...new Set(grades.value.map(item => item.examType).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'zh-CN')))
const filteredGrades = computed(() => {
  const query = keyword.value.toLocaleLowerCase()
  return grades.value.filter(item => {
    const searchable = [item.studentName, item.studentCode, item.courseName, item.courseCode, item.className, item.examType, item.semesterName].join(' ').toLocaleLowerCase()
    if (query && !searchable.includes(query)) return false
    if (selectedCourse.value !== 'all' && item.courseName !== selectedCourse.value) return false
    if (selectedExamType.value !== 'all' && item.examType !== selectedExamType.value) return false
    if (selectedBand.value === 'missing' && item.score !== null) return false
    if (selectedBand.value === 'excellent' && !(item.score !== null && item.score >= 90)) return false
    if (selectedBand.value === 'good' && !(item.score !== null && item.score >= 80 && item.score < 90)) return false
    if (selectedBand.value === 'pass' && !(item.score !== null && item.score >= 60 && item.score < 80)) return false
    if (selectedBand.value === 'fail' && !(item.score !== null && item.score < 60)) return false
    return true
  })
})
const scoredGrades = computed(() => filteredGrades.value.filter(item => item.score !== null))
const averageScore = computed(() => scoredGrades.value.length ? scoredGrades.value.reduce((sum, item) => sum + (item.score ?? 0), 0) / scoredGrades.value.length : null)
const passRate = computed(() => scoredGrades.value.length ? scoredGrades.value.filter(item => (item.score ?? 0) >= 60).length / scoredGrades.value.length * 100 : null)
const excellentCount = computed(() => scoredGrades.value.filter(item => (item.score ?? 0) >= 90).length)
const scoreDistribution = computed(() => {
  const buckets = [
    { label: '90–100 分', min: 90, max: Infinity, className: 'bar-excellent' },
    { label: '80–89 分', min: 80, max: 90, className: 'bar-good' },
    { label: '60–79 分', min: 60, max: 80, className: 'bar-pass' },
    { label: '60 分以下', min: -Infinity, max: 60, className: 'bar-fail' },
  ]
  return buckets.map(bucket => {
    const count = scoredGrades.value.filter(item => (item.score ?? -Infinity) >= bucket.min && (item.score ?? -Infinity) < bucket.max).length
    return { ...bucket, count, percent: scoredGrades.value.length ? count / scoredGrades.value.length * 100 : 0 }
  })
})
const courseSummaries = computed(() => {
  const map = new Map<string, GradeRecord[]>()
  filteredGrades.value.forEach(item => {
    const name = item.courseName || '课程信息未提供'
    map.set(name, [...(map.get(name) ?? []), item])
  })
  return [...map.entries()].map(([name, items]) => {
    const scores = items.filter(item => item.score !== null).map(item => item.score as number)
    return { name, count: items.length, average: scores.length ? scores.reduce((sum, score) => sum + score, 0) / scores.length : null }
  }).sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, 'zh-CN'))
})
const totalPages = computed(() => Math.max(1, Math.ceil(filteredGrades.value.length / pageSize)))
const pagedGrades = computed(() => filteredGrades.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch([keyword, selectedCourse, selectedExamType, selectedBand], () => { page.value = 1 })
watch(totalPages, value => { if (page.value > value) page.value = value })
function clearFilters() { keyword.value = ''; selectedCourse.value = 'all'; selectedExamType.value = 'all'; selectedBand.value = 'all'; page.value = 1 }
function avatarText(name: string) { return name ? [...name].slice(-1)[0] : '学' }
function scoreClass(score: number | null) { return score === null ? 'score-missing' : score >= 90 ? 'score-excellent' : score >= 60 ? 'score-pass' : 'score-fail' }
function statusClass(score: number | null) { return score === null ? 'status-missing' : score >= 60 ? 'status-pass' : 'status-fail' }
function statusLabel(score: number | null) { return score === null ? '未提供分数' : score >= 90 ? '优秀' : score >= 60 ? '及格' : '待关注' }
function exportCsv() {
  const columns = ['学生姓名', '学生学号', '课程名称', '课程代码', '教学班', '考试类型', '学期', '成绩', '记录时间']
  const rows = filteredGrades.value.map(item => [item.studentName, item.studentCode, item.courseName, item.courseCode, item.className, item.examType, item.semesterName, item.score === null ? '' : item.score, item.recordDate])
  const escapeCsv = (value: unknown) => `"${String(value ?? '').replace(/"/g, '""')}"`
  const csv = '\uFEFF' + [columns, ...rows].map(row => row.map(escapeCsv).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `教师成绩记录_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}
onMounted(loadGrades)
</script>

<style scoped>
.grades-page{display:flex;flex-direction:column;gap:20px;color:#18324f;padding-bottom:24px}.page-hero{position:relative;display:flex;align-items:center;justify-content:space-between;min-height:180px;padding:30px 34px;overflow:hidden;border-radius:20px;background:linear-gradient(112deg,#12366c 0%,#1c548c 63%,#246b9d 100%);color:#fff;box-shadow:0 14px 34px rgba(22,62,111,.12)}.page-hero:before,.page-hero:after{content:"";position:absolute;border:1px solid rgba(255,255,255,.08);border-radius:50%;pointer-events:none}.page-hero:before{width:270px;height:270px;right:7%;top:-155px}.page-hero:after{width:360px;height:360px;right:3%;top:-200px}.hero-copy{position:relative;z-index:1}.eyebrow{display:flex;align-items:center;gap:9px;font-size:11px;font-weight:800;letter-spacing:2px;color:#c7e2ff}.eyebrow svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.hero-copy h1{margin:16px 0 9px;font-size:29px;font-weight:750;letter-spacing:.3px}.hero-copy p{margin:0;color:#d4e5f8;font-size:14px}.hero-tags{display:flex;flex-wrap:wrap;gap:9px;margin-top:20px}.hero-tags span{display:inline-flex;align-items:center;gap:7px;padding:7px 11px;border:1px solid rgba(255,255,255,.15);border-radius:20px;background:rgba(255,255,255,.08);font-size:11px;color:#e1efff}.hero-tags i,.record-tag i{width:6px;height:6px;display:inline-block;border-radius:50%;background:#40d6b0}.hero-side{position:relative;z-index:1;display:flex;flex-direction:column;align-items:center;gap:12px;margin-right:18px}.hero-emblem{width:94px;height:94px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.17);border-radius:24px;background:rgba(255,255,255,.09);transform:rotate(-4deg)}.hero-emblem svg{width:70px;height:70px;fill:none;stroke:#a9d4ff;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}.hero-side-caption{font-size:9px;letter-spacing:2px;color:#c6e2fb}.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.summary-card{display:flex;align-items:center;gap:14px;min-width:0;padding:20px;border:1px solid #e8eef6;border-radius:16px;background:#fff;box-shadow:0 5px 18px rgba(29,62,99,.035)}.summary-icon{width:46px;height:46px;flex-shrink:0;display:grid;place-items:center;border-radius:14px}.summary-icon svg{width:22px;height:22px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.summary-icon-blue{background:#eaf3ff;color:#2876d8}.summary-icon-teal{background:#e8f8f4;color:#119e8a}.summary-icon-violet{background:#f1edff;color:#8362e8}.summary-icon-amber{background:#fff3e5;color:#e4932f}.summary-copy{display:flex;flex-direction:column;gap:3px;min-width:0}.summary-copy span{font-size:12px;color:#8495ab}.summary-copy strong{font-size:25px;line-height:1.25;color:#1b4e86;font-weight:750}.summary-copy small{font-size:10px;color:#9aa9bc;white-space:normal}.insight-grid{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:16px}.panel,.grades-panel{min-width:0;border:1px solid #e7edf5;border-radius:17px;background:#fff;box-shadow:0 5px 18px rgba(29,62,99,.035)}.panel{padding:22px 24px}.grades-panel{padding:22px 24px}.panel-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:20px}.heading-title-row{display:flex;align-items:center;gap:10px}.heading-accent{width:4px;height:19px;border-radius:4px;background:#3483df}.panel-heading h2{margin:0;font-size:17px;font-weight:750;color:#193a5d}.panel-heading p{margin:8px 0 0 14px;font-size:12px;color:#8da0b6;line-height:1.6}.subtle-count{padding:6px 10px;border-radius:20px;background:#f2f7fd;color:#7f95b0;font-size:11px;white-space:nowrap}.distribution-list{display:flex;flex-direction:column;gap:17px;padding:4px 2px 2px}.distribution-row{display:grid;grid-template-columns:85px minmax(80px,1fr) 32px 35px;align-items:center;gap:12px}.distribution-label{font-size:12px;color:#6e8198}.distribution-track,.course-mini-track{height:9px;overflow:hidden;border-radius:20px;background:#f0f4f9}.distribution-track span,.course-mini-track span{height:100%;display:block;border-radius:20px;transition:width .25s ease}.bar-excellent{background:linear-gradient(90deg,#2363cc,#69a7ff)}.bar-good{background:linear-gradient(90deg,#16a38e,#61d4b9)}.bar-pass{background:linear-gradient(90deg,#e6a342,#f4cf7b)}.bar-fail{background:linear-gradient(90deg,#e36e6e,#f4a3a3)}.distribution-row strong{font-size:12px;color:#314c6b;text-align:right}.distribution-row small{font-size:11px;color:#9aa9bc;text-align:right}.course-summary-list{display:flex;flex-direction:column;gap:16px}.course-summary-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px 16px;align-items:center}.course-summary-main{display:flex;flex-direction:column;gap:5px;min-width:0}.course-summary-main strong{font-size:12px;font-weight:650;color:#3a526f;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.course-summary-main span,.course-average span{font-size:10px;color:#9aa9bc}.course-average{display:flex;align-items:flex-end;gap:5px}.course-average strong{font-size:17px;color:#1c5590}.course-mini-track{grid-column:1 / -1;height:5px}.course-mini-track span{background:linear-gradient(90deg,#2b6fd1,#6aa9ff)}.mini-empty{padding:28px 10px;text-align:center;color:#9aa9bc;font-size:12px}.heading-actions{display:flex;flex-wrap:wrap;gap:8px}.secondary-button,.primary-button{display:inline-flex;align-items:center;justify-content:center;gap:7px;min-height:37px;padding:0 13px;border-radius:10px;font-size:12px;cursor:pointer;transition:all .18s ease}.secondary-button{border:1px solid #dce7f4;background:#fff;color:#3e77b8}.primary-button{border:1px solid #214d96;background:#214d96;color:#fff}.secondary-button:hover:not(:disabled){background:#f3f8ff}.primary-button:hover:not(:disabled){background:#173e80}.secondary-button:disabled,.primary-button:disabled{opacity:.5;cursor:not-allowed}.secondary-button svg,.primary-button svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.filter-bar{display:flex;flex-wrap:wrap;align-items:center;gap:12px;padding:14px;border:1px solid #edf2f8;border-radius:13px;background:#f8fafd}.search-box{display:flex;align-items:center;gap:9px;flex:1 1 280px;min-width:210px;height:40px;padding:0 12px;border:1px solid #e0e9f4;border-radius:9px;background:#fff}.search-box svg{width:17px;height:17px;flex-shrink:0;fill:none;stroke:#8ba0b9;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.search-box input{width:100%;border:0;outline:0;background:transparent;font-size:12px;color:#304b69}.search-box input::placeholder{color:#a3b1c3}.filter-control{display:flex;align-items:center;gap:8px;font-size:11px;color:#8093ab}.filter-control select{height:40px;min-width:110px;max-width:170px;padding:0 26px 0 10px;border:1px solid #e0e9f4;border-radius:9px;background:#fff;color:#3c5878;font-size:12px;outline:none}.result-meta{display:flex;justify-content:space-between;gap:12px;margin:18px 2px 10px;color:#92a3b8;font-size:11px}.table-wrap{width:100%;overflow-x:auto;border:1px solid #edf1f6;border-radius:12px}table{width:100%;border-collapse:collapse;text-align:left;white-space:nowrap}thead{background:#f5f8fc}th{height:44px;padding:0 14px;color:#8295ac;font-size:11px;font-weight:650}td{height:62px;padding:10px 14px;border-top:1px solid #eef2f7;color:#536b87;font-size:12px}tbody tr:hover{background:#fbfdff}.student-cell{display:flex;align-items:center;gap:10px}.student-avatar{width:34px;height:34px;display:grid;place-items:center;flex-shrink:0;border-radius:11px;background:linear-gradient(145deg,#e7f1ff,#dceaff);color:#2d6ec0;font-weight:750}.student-cell>span:last-child,.course-cell{display:flex;flex-direction:column;gap:4px}.student-cell strong,.course-cell strong{color:#2b496a;font-size:12px;font-weight:650}.student-cell small,.course-cell small{color:#9aa9bc;font-size:10px}.score-pill{display:inline-flex;min-width:49px;justify-content:center;padding:6px 8px;border-radius:8px;font-size:12px;font-weight:750}.score-excellent{background:#eaf3ff;color:#2268bd}.score-pass{background:#e8f8f1;color:#14855f}.score-fail{background:#fff0ed;color:#d65b4f}.score-missing{background:#f1f3f6;color:#8996a7}.status-pill{display:inline-flex;padding:5px 8px;border-radius:7px;font-size:10px}.status-pass{background:#edf9f3;color:#1d9469}.status-fail{background:#fff0ed;color:#d65b4f}.status-missing{background:#f2f4f7;color:#8b99aa}.table-action{border:0;background:transparent;color:#367ac3;font-size:11px;cursor:pointer}.table-action:hover{color:#164d91}.table-action span{margin-left:3px}.table-empty{display:flex;flex-direction:column;align-items:center;gap:8px;padding:34px 16px;text-align:center}.table-empty strong{font-size:13px;color:#61758e}.table-empty span{font-size:11px;color:#9aa9bc}.table-empty button{margin-top:5px;padding:7px 12px;border:1px solid #dce7f4;border-radius:8px;background:#fff;color:#3778ba;font-size:11px;cursor:pointer}.pagination{display:flex;justify-content:space-between;align-items:center;margin-top:14px;color:#8fa0b4;font-size:11px}.pagination div{display:flex;gap:8px}.pagination button{padding:7px 11px;border:1px solid #dfe8f2;border-radius:8px;background:#fff;color:#55708d;font-size:11px;cursor:pointer}.pagination button:disabled{opacity:.45;cursor:not-allowed}.footnote{margin:17px 0 0;padding-top:13px;border-top:1px solid #f0f3f7;color:#9aa9bc;font-size:10px;line-height:1.7}.state-message{display:flex;flex-direction:column;align-items:center;gap:10px;padding:45px 18px;color:#899bb0;font-size:12px;text-align:center}.state-message strong{color:#4e6683;font-size:14px}.state-message button{padding:8px 15px;border:1px solid #dce7f4;border-radius:8px;background:#fff;color:#3375b9;cursor:pointer}.state-error{color:#b65b51}.state-error strong{color:#b84f46}.spinning{animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.drawer-backdrop{position:fixed;inset:0;z-index:1200;display:flex;justify-content:flex-end;background:rgba(10,26,48,.38);backdrop-filter:blur(4px)}.detail-drawer{display:flex;flex-direction:column;width:min(500px,94vw);height:100%;background:#fff;box-shadow:-20px 0 60px rgba(12,33,58,.16);animation:drawer-in .22s ease-out}.drawer-header{display:flex;align-items:center;gap:14px;padding:24px 22px;border-bottom:1px solid #edf1f6}.drawer-icon{width:48px;height:48px;display:grid;place-items:center;flex-shrink:0;border-radius:14px;background:#eaf3ff;color:#2b75cc}.drawer-icon svg{width:25px;height:25px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}.drawer-title{flex:1;min-width:0}.drawer-title small{font-size:9px;letter-spacing:1.7px;color:#8ba3bd}.drawer-title h2{margin:5px 0;font-size:18px;color:#213d5d}.drawer-title p{margin:0;font-size:11px;color:#93a4b8}.drawer-close{width:34px;height:34px;border:1px solid #e2e9f1;border-radius:9px;background:#fff;color:#70839b;font-size:23px;line-height:1;cursor:pointer}.drawer-body{flex:1;overflow:auto;padding:22px}.score-highlight{display:flex;align-items:center;gap:14px;padding:18px;border:1px solid #e6eef8;border-radius:14px;background:linear-gradient(120deg,#f6faff,#fff)}.score-highlight span{color:#7e93ac;font-size:12px}.score-highlight strong{font-size:34px;color:#1e5595}.score-highlight em{margin-left:auto;padding:6px 9px;border-radius:7px;font-style:normal;font-size:10px}.drawer-section-title{display:flex;align-items:center;gap:9px;margin:26px 0 14px;color:#34506f;font-size:13px;font-weight:750}.drawer-section-title>span{width:4px;height:16px;border-radius:3px;background:#3582dd}.detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.detail-field{display:flex;flex-direction:column;gap:7px;min-height:65px;padding:13px;border-radius:10px;background:#f6f8fb;overflow-wrap:anywhere}.detail-field small{color:#8c9db1;font-size:10px}.detail-field strong{color:#405975;font-size:12px;font-weight:650}.drawer-note{margin:16px 0 0;color:#98a8ba;font-size:10px;line-height:1.8}.drawer-footer{display:flex;justify-content:flex-end;padding:16px 22px;border-top:1px solid #edf1f6}.drawer-footer button{padding:9px 17px;border:1px solid #dfe7f1;border-radius:9px;background:#fff;color:#536f8e;font-size:12px;cursor:pointer}@keyframes drawer-in{from{transform:translateX(20px);opacity:.5}to{transform:translateX(0);opacity:1}}@media(max-width:1120px){.summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.insight-grid{grid-template-columns:1fr}.filter-control{flex:1 1 145px}.filter-control select{flex:1;max-width:none}}@media(max-width:680px){.grades-page{gap:14px}.page-hero{min-height:160px;padding:24px 20px}.hero-copy h1{font-size:24px}.hero-side{display:none}.summary-grid{gap:10px}.summary-card{padding:14px 12px;gap:10px}.summary-icon{width:38px;height:38px}.summary-copy strong{font-size:22px}.summary-copy small{display:none}.panel,.grades-panel{padding:17px 14px}.panel-heading{flex-direction:column}.heading-actions{width:100%}.heading-actions button{flex:1}.filter-bar{padding:10px}.search-box{flex-basis:100%;min-width:0}.filter-control{flex-basis:100%;justify-content:space-between}.filter-control select{max-width:none}.result-meta{flex-direction:column;gap:5px}.detail-grid{grid-template-columns:1fr}.drawer-header{padding:18px 14px}.drawer-body{padding:16px}.score-highlight strong{font-size:28px}}
</style>
