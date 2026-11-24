<template>
  <section class="role-page">
    <header class="hero">
      <div>
        <p class="eyebrow">TEACHING WORKSPACE</p>
        <h1>教师工作台</h1>
        <p class="hero-subtitle">查看本人授课课程、教学班、考试安排与成绩记录。</p>
      </div>
      <div class="hero-user">
        <span class="avatar">{{ username.slice(0, 1).toUpperCase() }}</span>
        <span><b>{{ username }}</b><small>任课教师</small></span>
      </div>
    </header>

    <div class="toolbar">
      <span>数据范围：当前教师已授权的教学任务</span>
      <button class="refresh-button" type="button" :disabled="loading" @click="loadData">
        {{ loading ? '正在刷新…' : '刷新数据' }}
      </button>
    </div>

    <div v-if="errorMessage" class="message message-warning">{{ errorMessage }}</div>
    <div v-if="loading && !loaded" class="message">正在加载教师工作数据…</div>

    <div class="stats-grid">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.note }}</small>
      </article>
    </div>

    <div class="content-grid">
      <section class="panel">
        <div class="panel-heading">
          <div><h2>我的授课课程</h2><p>仅展示后端授权给当前教师的课程</p></div>
          <span class="count-pill">{{ courseCount }} 门</span>
        </div>
        <div v-if="courses.length" class="table-wrap">
          <table>
            <thead><tr><th>课程代码</th><th>课程名称</th><th>学期</th></tr></thead>
            <tbody>
              <tr v-for="course in courses.slice(0, 8)" :key="course.id">
                <td>{{ course.code || '—' }}</td>
                <td>{{ course.name || '未命名课程' }}</td>
                <td>{{ course.semester_name || '当前授权学期' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">当前账号暂无可展示的授课课程。</div>
      </section>

      <section class="panel">
        <div class="panel-heading">
          <div><h2>近期考试安排</h2><p>根据教师授权范围读取</p></div>
          <span class="count-pill">{{ upcomingExams.length }} 项</span>
        </div>
        <div v-if="upcomingExams.length" class="list">
          <article v-for="exam in upcomingExams" :key="exam.id" class="list-row">
            <div class="date-badge">
              <b>{{ dateParts(exam.exam_date).day }}</b>
              <small>{{ dateParts(exam.exam_date).month }}</small>
            </div>
            <div class="list-main">
              <b>{{ exam.name || exam.course_name || '课程考试' }}</b>
              <small>{{ exam.course_name || '相关课程' }} · {{ formatDate(exam.exam_date) }}</small>
              <small v-if="exam.location">地点：{{ exam.location }}</small>
            </div>
          </article>
        </div>
        <div v-else class="empty-state">暂无可展示的近期考试安排。</div>
      </section>

      <section class="panel">
        <div class="panel-heading">
          <div><h2>我的教学班</h2><p>课程、班级与排课信息</p></div>
          <span class="count-pill">{{ classCount }} 个</span>
        </div>
        <div v-if="classes.length" class="class-list">
          <article v-for="item in classes.slice(0, 8)" :key="item.id" class="class-row">
            <div class="class-icon">班</div>
            <div class="list-main">
              <b>{{ item.class_name || item.course_name || '教学班' }}</b>
              <small>{{ item.course_name || '课程信息待完善' }} · {{ item.semester_name || '学期未标注' }}</small>
              <small>{{ item.schedule || '暂未填写排课时间' }} <span v-if="item.classroom">· {{ item.classroom }}</span></small>
            </div>
          </article>
        </div>
        <div v-else class="empty-state">当前账号暂无教学班记录。</div>
      </section>

      <section class="panel">
        <div class="panel-heading">
          <div><h2>近期成绩记录</h2><p>只显示本人授课范围内的成绩</p></div>
          <span class="count-pill">{{ gradeCount }} 条</span>
        </div>
        <div v-if="recentGrades.length" class="table-wrap">
          <table>
            <thead><tr><th>学生</th><th>课程</th><th>成绩</th><th>考试类型</th></tr></thead>
            <tbody>
              <tr v-for="grade in recentGrades" :key="grade.id">
                <td>{{ grade.student_name || '学生' }}</td>
                <td>{{ grade.course_name || '课程' }}</td>
                <td><span class="score" :class="Number(grade.score) >= 60 ? 'pass' : 'fail'">{{ grade.score ?? '—' }}</span></td>
                <td>{{ grade.exam_type || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">当前没有可展示的成绩记录。</div>
      </section>
    </div>

    <p class="footnote">本工作台为只读概览。课程、学生、考试和成绩的实际可见范围以服务端权限校验结果为准。</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/api/index'

interface ListResult<T> {
  count: number
  results: T[]
}

interface Course {
  id: number
  code?: string
  name?: string
  semester_name?: string
}

interface TeachingClass {
  id: number
  class_name?: string
  course_name?: string
  semester_name?: string
  schedule?: string
  classroom?: string
}

interface Exam {
  id: number
  name?: string
  course_name?: string
  exam_date?: string
  location?: string
}

interface Grade {
  id: number
  student_name?: string
  course_name?: string
  score?: number | string | null
  exam_type?: string
  exam_date?: string
}

function normalizeList<T>(payload: any): ListResult<T> {
  if (Array.isArray(payload)) {
    return { count: payload.length, results: payload as T[] }
  }
  const results = Array.isArray(payload?.results) ? payload.results as T[] : []
  return { count: Number(payload?.count ?? results.length), results }
}

async function fetchList<T>(path: string): Promise<ListResult<T>> {
  const payload = await api.get(path, { params: { page_size: 100 } })
  return normalizeList<T>(payload)
}

function readUsername(): string {
  try {
    const user = JSON.parse(localStorage.getItem('user_info') || '{}')
    return String(user.username || user.name || '教师用户')
  } catch {
    return '教师用户'
  }
}

const username = ref(readUsername())
const loading = ref(false)
const loaded = ref(false)
const errorMessage = ref('')
const courses = ref<Course[]>([])
const classes = ref<TeachingClass[]>([])
const exams = ref<Exam[]>([])
const grades = ref<Grade[]>([])
const courseCount = ref(0)
const classCount = ref(0)
const examCount = ref(0)
const gradeCount = ref(0)

const stats = computed(() => [
  { label: '我的授课课程', value: courseCount.value, note: '按当前账号权限统计' },
  { label: '我的教学班', value: classCount.value, note: '本人关联的教学班' },
  { label: '授课成绩记录', value: gradeCount.value, note: '本人授权课程范围' },
  { label: '相关考试', value: examCount.value, note: '本人授权课程考试' },
])

const upcomingExams = computed(() => {
  const now = Date.now()
  return exams.value
    .filter((exam) => {
      const time = exam.exam_date ? new Date(exam.exam_date).getTime() : Number.NaN
      return Number.isFinite(time) && time >= now
    })
    .sort((a, b) => new Date(a.exam_date || 0).getTime() - new Date(b.exam_date || 0).getTime())
    .slice(0, 6)
})

const recentGrades = computed(() =>
  [...grades.value]
    .sort((a, b) => new Date(b.exam_date || 0).getTime() - new Date(a.exam_date || 0).getTime())
    .slice(0, 8),
)

function formatDate(value?: string): string {
  if (!value) return '时间待定'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('zh-CN')
}

function dateParts(value?: string): { day: string; month: string } {
  if (!value) return { day: '--', month: '待定' }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return { day: '--', month: '待定' }
  return {
    day: String(date.getDate()).padStart(2, '0'),
    month: `${date.getMonth() + 1}月`,
  }
}

async function loadData() {
  loading.value = true
  errorMessage.value = ''
  const [courseData, classData, examData, gradeData] = await Promise.all([
    fetchList<Course>('/courses/').catch(() => null),
    fetchList<TeachingClass>('/teaching-classes/').catch(() => null),
    fetchList<Exam>('/exams/').catch(() => null),
    fetchList<Grade>('/grades/').catch(() => null),
  ])

  if (courseData) {
    courses.value = courseData.results
    courseCount.value = courseData.count
  }
  if (classData) {
    classes.value = classData.results
    classCount.value = classData.count
  }
  if (examData) {
    exams.value = examData.results
    examCount.value = examData.count
  }
  if (gradeData) {
    grades.value = gradeData.results
    gradeCount.value = gradeData.count
  }

  if (!courseData || !classData || !examData || !gradeData) {
    errorMessage.value = '部分数据暂时无法加载。请确认后端服务正常，并检查当前教师账号的数据授权范围。'
  }

  loaded.value = true
  loading.value = false
}

onMounted(loadData)
</script>

<style scoped>
.role-page{max-width:1500px;margin:0 auto;color:#172b4d}
.hero{display:flex;justify-content:space-between;align-items:center;gap:24px;padding:28px 32px;border-radius:18px;background:linear-gradient(120deg,#0b2a5b,#18548e);color:#fff;box-shadow:0 12px 30px #0b2a5b18}
.eyebrow{margin:0 0 8px;color:#a9d2ff;font-size:11px;letter-spacing:2px}
.hero h1{margin:0;font-size:28px;font-weight:700}
.hero-subtitle{margin:10px 0 0;color:#d7e8fa;font-size:14px}
.hero-user{display:flex;align-items:center;gap:12px;min-width:150px}
.avatar{display:grid;place-items:center;width:44px;height:44px;border-radius:50%;background:#ffffff20;border:1px solid #ffffff55;font-size:18px;font-weight:700}
.hero-user b,.hero-user small{display:block}.hero-user b{font-size:14px}.hero-user small{margin-top:5px;color:#c6def6;font-size:12px}
.toolbar{display:flex;justify-content:space-between;align-items:center;gap:16px;margin:18px 2px;color:#73839a;font-size:12px}
.refresh-button{padding:9px 15px;border:1px solid #dbe5f0;border-radius:9px;background:#fff;color:#245b91;cursor:pointer}.refresh-button:disabled{opacity:.6;cursor:wait}
.stats-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:18px 0}
.stat-card,.panel{background:#fff;border:1px solid #e7edf5;border-radius:15px;box-shadow:0 4px 16px #173b6508}
.stat-card{padding:20px 22px}.stat-label{display:block;color:#718198;font-size:13px}.stat-card strong{display:block;margin:12px 0 8px;color:#1765a8;font-size:30px;line-height:1.1}.stat-card small{color:#99a5b5;font-size:11px}
.content-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}
.panel{padding:22px;min-width:0}.panel-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:17px}.panel-heading h2{margin:0;font-size:17px;color:#203753}.panel-heading p{margin:7px 0 0;color:#8a98aa;font-size:12px}.count-pill{flex-shrink:0;padding:6px 10px;border-radius:20px;background:#edf5ff;color:#2165a4;font-size:12px}
.table-wrap{width:100%;overflow-x:auto}table{width:100%;border-collapse:collapse;text-align:left;font-size:12px}th{padding:11px 9px;background:#f7f9fc;color:#7c8ba0;font-weight:600;white-space:nowrap}td{padding:13px 9px;border-bottom:1px solid #eef2f7;color:#40536c}tbody tr:last-child td{border-bottom:0}
.list,.class-list{display:flex;flex-direction:column}.list-row,.class-row{display:flex;align-items:center;gap:13px;padding:13px 0;border-top:1px solid #eef2f7}.list-row:first-child,.class-row:first-child{border-top:0}
.date-badge{display:flex;flex-direction:column;align-items:center;justify-content:center;width:48px;height:52px;flex-shrink:0;border-radius:11px;background:#edf5ff;color:#1e64a2}.date-badge b{font-size:18px}.date-badge small{margin-top:2px;font-size:11px}
.class-icon{display:grid;place-items:center;width:42px;height:42px;flex-shrink:0;border-radius:12px;background:#eef7f2;color:#27845b;font-size:14px;font-weight:700}
.list-main{min-width:0}.list-main b,.list-main small{display:block}.list-main b{font-size:13px;color:#30445d}.list-main small{margin-top:5px;color:#8593a5;font-size:11px;line-height:1.5}
.score{display:inline-block;min-width:35px;text-align:center;padding:4px 7px;border-radius:7px;font-weight:700}.score.pass{background:#eaf8f0;color:#218455}.score.fail{background:#fff0ed;color:#c44b3e}
.empty-state{padding:28px 10px;text-align:center;color:#9aa6b5;font-size:12px;background:#fafbfd;border-radius:10px}
.message{margin:14px 0;padding:12px 15px;border-radius:10px;background:#f3f7fc;color:#526980;font-size:13px}.message-warning{background:#fff7e8;color:#8a6420}
.footnote{margin:18px 2px 0;color:#9aa6b5;font-size:11px;line-height:1.7}
@media(max-width:1050px){.stats-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.content-grid{grid-template-columns:1fr}}
@media(max-width:600px){.hero{align-items:flex-start;flex-direction:column;padding:22px}.hero h1{font-size:23px}.stats-grid{gap:10px}.stat-card{padding:16px}.stat-card strong{font-size:25px}.panel{padding:16px}.toolbar{align-items:flex-start;flex-direction:column}}
</style>