<template>
  <section class="role-page">
    <header class="hero">
      <div>
        <p class="eyebrow">MY LEARNING SPACE</p>
        <h1>学生个人中心</h1>
        <p class="hero-subtitle">集中查看个人学籍、修读课程与已发布成绩。</p>
      </div>
      <div class="hero-user">
        <span class="avatar">{{ studentName.slice(0, 1) }}</span>
        <span><b>{{ studentName }}</b><small>{{ profile?.student_no || '学生账号' }}</small></span>
      </div>
    </header>

    <div class="toolbar">
      <span>个人数据根据当前登录学生身份获取；这里只展示已授权的个人记录。</span>
      <button class="refresh-button" type="button" :disabled="loading" @click="loadData">
        {{ loading ? '正在刷新…' : '刷新个人数据' }}
      </button>
    </div>

    <div v-if="errorMessage" class="message message-warning">{{ errorMessage }}</div>
    <div v-if="loading && !loaded" class="message">正在加载个人学习数据…</div>

    <div class="stats-grid">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.note }}</small>
      </article>
    </div>

    <div class="content-grid">
      <section class="panel profile-panel">
        <div class="panel-heading"><div><h2>我的学籍信息</h2><p>由当前登录身份关联的学生档案提供</p></div><span class="status-pill">个人档案</span></div>
        <div class="profile-grid">
          <div><span>姓名</span><b>{{ profile?.name || studentName }}</b></div>
          <div><span>学号</span><b>{{ profile?.student_no || '—' }}</b></div>
          <div><span>学院</span><b>{{ profile?.college_name || '—' }}</b></div>
          <div><span>专业</span><b>{{ profile?.major || '—' }}</b></div>
          <div><span>年级</span><b>{{ profile?.grade || '—' }}</b></div>
          <div><span>行政班</span><b>{{ profile?.class_name || '—' }}</b></div>
        </div>
        <p class="privacy-note">个人档案为只读展示。如需更正学籍信息，请联系教务管理人员。</p>
      </section>

      <section class="panel">
        <div class="panel-heading"><div><h2>我的修读课程</h2><p>根据个人成绩记录关联课程，并展示已授权教学班信息</p></div><span class="count-pill">{{ courses.length }} 门</span></div>
        <div v-if="courses.length" class="course-list">
          <article v-for="course in courses" :key="course.id" class="course-row">
            <div class="course-symbol">课</div>
            <div class="course-main">
              <b>{{ course.name }}</b>
              <small>{{ course.className || '教学班信息待完善' }}</small>
              <small>{{ course.schedule || '暂未提供排课时间' }}<span v-if="course.classroom"> · {{ course.classroom }}</span></small>
            </div>
          </article>
        </div>
        <div v-else class="empty-state">当前没有可展示的个人课程记录。</div>
      </section>

      <section class="panel grade-panel">
        <div class="panel-heading"><div><h2>我的成绩</h2><p>仅展示当前学生已发布的成绩记录</p></div><span class="count-pill">{{ gradeCount }} 条</span></div>
        <div v-if="recentGrades.length" class="table-wrap">
          <table>
            <thead><tr><th>课程</th><th>考试类型</th><th>成绩</th><th>日期</th></tr></thead>
            <tbody>
              <tr v-for="grade in recentGrades" :key="grade.id">
                <td>{{ grade.course_name || '课程' }}</td>
                <td>{{ grade.exam_type || '—' }}</td>
                <td><span class="score" :class="Number(grade.score) >= 60 ? 'pass' : 'fail'">{{ grade.score ?? '—' }}</span></td>
                <td>{{ formatDate(grade.exam_date) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="empty-state">暂无已发布成绩记录。</div>
      </section>

      <section class="panel">
        <div class="panel-heading"><div><h2>学习情况</h2><p>由个人已发布成绩计算，不使用全校统计数据</p></div></div>
        <div class="progress-row"><div><span>成绩合格率</span><b>{{ passRateLabel }}</b></div><div class="progress-track"><span :style="{ width: `${passRate}%` }"></span></div></div>
        <div class="progress-row"><div><span>平均成绩</span><b>{{ averageScoreLabel }}</b></div><div class="progress-track"><span :style="{ width: `${Math.min(100, Math.max(0, averageScore))}%` }"></span></div></div>
        <div class="learning-note">
          <b>学习建议</b>
          <p v-if="gradeCount === 0">当前暂无已发布成绩。请关注课程安排与教务通知，成绩发布后会显示在这里。</p>
          <p v-else-if="passRate < 60">部分课程成绩需要重点关注，建议及时复习薄弱知识点，并向任课教师咨询。</p>
          <p v-else-if="averageScore >= 85">当前个人成绩表现良好，建议保持学习节奏并持续关注各课程进度。</p>
          <p v-else>建议定期查看课程成绩，结合课程要求安排复习时间。</p>
        </div>
      </section>
    </div>

    <p class="footnote">学生端不提供全校学生档案、成绩录入、教师管理或全校排名入口。数据范围由后端接口权限决定。</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/api/index'

interface ListResult<T> {
  count: number
  results: T[]
}

interface StudentProfile {
  id: number
  student_no?: string
  name?: string
  college_name?: string
  major?: string
  grade?: string
  class_name?: string
}

interface Grade {
  id: number
  course: number
  course_name?: string
  score?: number | string | null
  exam_type?: string
  exam_date?: string
  semester_name?: string
}

interface TeachingClass {
  id: number
  course: number
  course_name?: string
  class_name?: string
  schedule?: string
  classroom?: string
}

interface PersonalCourse {
  id: number
  name: string
  className?: string
  schedule?: string
  classroom?: string
}

function normalizeList<T>(payload: any): ListResult<T> {
  if (Array.isArray(payload)) return { count: payload.length, results: payload as T[] }
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
    return String(user.username || user.name || '学生用户')
  } catch {
    return '学生用户'
  }
}

const studentName = ref(readUsername())
const loading = ref(false)
const loaded = ref(false)
const errorMessage = ref('')
const profile = ref<StudentProfile | null>(null)
const grades = ref<Grade[]>([])
const gradeCount = ref(0)
const teachingClasses = ref<TeachingClass[]>([])

const courses = computed<PersonalCourse[]>(() => {
  const gradeCourseMap = new Map<number, string>()
  grades.value.forEach((grade) => {
    if (grade.course != null) {
      gradeCourseMap.set(grade.course, grade.course_name || `课程 ${grade.course}`)
    }
  })

  const classMap = new Map<number, TeachingClass>()
  teachingClasses.value.forEach((item) => {
    if (gradeCourseMap.has(item.course) && !classMap.has(item.course)) classMap.set(item.course, item)
  })

  return Array.from(gradeCourseMap.entries()).map(([id, name]) => {
    const teachingClass = classMap.get(id)
    return {
      id,
      name,
      className: teachingClass?.class_name,
      schedule: teachingClass?.schedule,
      classroom: teachingClass?.classroom,
    }
  }).sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
})

const averageScore = computed(() => {
  const values = grades.value
    .map((item) => Number(item.score))
    .filter((value) => Number.isFinite(value))
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0
})

const passRate = computed(() => {
  const values = grades.value.map((item) => Number(item.score)).filter(Number.isFinite)
  return values.length ? (values.filter((value) => value >= 60).length / values.length) * 100 : 0
})

const averageScoreLabel = computed(() => gradeCount.value ? averageScore.value.toFixed(1) : '—')
const passRateLabel = computed(() => gradeCount.value ? `${passRate.value.toFixed(1)}%` : '—')

const stats = computed(() => [
  { label: '个人修读课程', value: courses.value.length, note: '按个人成绩关联课程统计' },
  { label: '已发布成绩', value: gradeCount.value, note: '未发布成绩不会显示' },
  { label: '个人平均成绩', value: averageScoreLabel.value, note: '仅按个人已发布成绩计算' },
  { label: '个人合格率', value: passRateLabel.value, note: '以 60 分为合格线' },
])

const recentGrades = computed(() =>
  [...grades.value]
    .sort((a, b) => new Date(b.exam_date || 0).getTime() - new Date(a.exam_date || 0).getTime())
    .slice(0, 10),
)

function formatDate(value?: string): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('zh-CN')
}

async function loadData() {
  loading.value = true
  errorMessage.value = ''

  const [studentData, gradeData, classData] = await Promise.all([
    fetchList<StudentProfile>('/students/').catch(() => null),
    fetchList<Grade>('/grades/').catch(() => null),
    fetchList<TeachingClass>('/teaching-classes/').catch(() => null),
  ])

  if (studentData) profile.value = studentData.results[0] ?? null
  if (gradeData) {
    grades.value = gradeData.results
    gradeCount.value = gradeData.count
  }
  if (classData) teachingClasses.value = classData.results

  if (!studentData || !gradeData || !classData) {
    errorMessage.value = '部分个人数据暂时无法加载。请确认后端服务正常，并检查当前学生账号与学籍档案的关联。'
  }

  if (profile.value?.name) studentName.value = profile.value.name
  loaded.value = true
  loading.value = false
}

onMounted(loadData)
</script>

<style scoped>
.role-page{max-width:1500px;margin:0 auto;color:#172b4d}
.hero{display:flex;justify-content:space-between;align-items:center;gap:24px;padding:28px 32px;border-radius:18px;background:linear-gradient(120deg,#123d69,#2878a9);color:#fff;box-shadow:0 12px 30px #123d6918}
.eyebrow{margin:0 0 8px;color:#b9e1ff;font-size:11px;letter-spacing:2px}
.hero h1{margin:0;font-size:28px;font-weight:700}.hero-subtitle{margin:10px 0 0;color:#d5eaf9;font-size:14px}
.hero-user{display:flex;align-items:center;gap:12px;min-width:150px}.avatar{display:grid;place-items:center;width:44px;height:44px;border-radius:50%;background:#ffffff20;border:1px solid #ffffff55;font-size:18px;font-weight:700}
.hero-user b,.hero-user small{display:block}.hero-user b{font-size:14px}.hero-user small{margin-top:5px;color:#d0e8f8;font-size:12px}
.toolbar{display:flex;justify-content:space-between;align-items:center;gap:16px;margin:18px 2px;color:#73839a;font-size:12px}
.refresh-button{padding:9px 15px;border:1px solid #dbe5f0;border-radius:9px;background:#fff;color:#245b91;cursor:pointer}.refresh-button:disabled{opacity:.6;cursor:wait}
.stats-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin:18px 0}
.stat-card,.panel{background:#fff;border:1px solid #e7edf5;border-radius:15px;box-shadow:0 4px 16px #173b6508}
.stat-card{padding:20px 22px}.stat-label{display:block;color:#718198;font-size:13px}.stat-card strong{display:block;margin:12px 0 8px;color:#1765a8;font-size:30px;line-height:1.1}.stat-card small{color:#99a5b5;font-size:11px}
.content-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.panel{padding:22px;min-width:0}
.panel-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:17px}.panel-heading h2{margin:0;font-size:17px;color:#203753}.panel-heading p{margin:7px 0 0;color:#8a98aa;font-size:12px}
.count-pill,.status-pill{flex-shrink:0;padding:6px 10px;border-radius:20px;background:#edf5ff;color:#2165a4;font-size:12px}.status-pill{background:#edf8f1;color:#238153}
.profile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 18px}.profile-grid div{padding:14px 0;border-bottom:1px solid #eef2f7}.profile-grid span,.profile-grid b{display:block}.profile-grid span{margin-bottom:7px;color:#8a98aa;font-size:12px}.profile-grid b{color:#344b66;font-size:13px;overflow-wrap:anywhere}
.privacy-note{margin:16px 0 0;padding:12px 14px;border-radius:9px;background:#f5f8fc;color:#75859a;font-size:11px;line-height:1.8}
.course-list{display:flex;flex-direction:column}.course-row{display:flex;align-items:center;gap:13px;padding:13px 0;border-top:1px solid #eef2f7}.course-row:first-child{border-top:0}.course-symbol{display:grid;place-items:center;width:42px;height:42px;flex-shrink:0;border-radius:12px;background:#e8f3ff;color:#1762a8;font-size:14px;font-weight:700}
.course-main{min-width:0}.course-main b,.course-main small{display:block}.course-main b{font-size:13px;color:#30445d}.course-main small{margin-top:5px;color:#8593a5;font-size:11px;line-height:1.5}
.table-wrap{width:100%;overflow-x:auto}table{width:100%;border-collapse:collapse;text-align:left;font-size:12px}th{padding:11px 9px;background:#f7f9fc;color:#7c8ba0;font-weight:600;white-space:nowrap}td{padding:13px 9px;border-bottom:1px solid #eef2f7;color:#40536c}tbody tr:last-child td{border-bottom:0}
.score{display:inline-block;min-width:35px;text-align:center;padding:4px 7px;border-radius:7px;font-weight:700}.score.pass{background:#eaf8f0;color:#218455}.score.fail{background:#fff0ed;color:#c44b3e}
.progress-row{margin:18px 0}.progress-row>div:first-child{display:flex;justify-content:space-between;gap:12px;margin-bottom:9px;color:#61748b;font-size:13px}.progress-row b{color:#2466a2}
.progress-track{height:8px;overflow:hidden;border-radius:10px;background:#edf1f6}.progress-track span{display:block;height:100%;border-radius:10px;background:linear-gradient(90deg,#4b9ee8,#2469ae);transition:width .25s}
.learning-note{margin-top:22px;padding:15px;border-radius:11px;background:#f3f8ff}.learning-note b{font-size:13px;color:#285982}.learning-note p{margin:8px 0 0;color:#6d8097;font-size:12px;line-height:1.8}
.empty-state{padding:28px 10px;text-align:center;color:#9aa6b5;font-size:12px;background:#fafbfd;border-radius:10px}
.message{margin:14px 0;padding:12px 15px;border-radius:10px;background:#f3f7fc;color:#526980;font-size:13px}.message-warning{background:#fff7e8;color:#8a6420}
.footnote{margin:18px 2px 0;color:#9aa6b5;font-size:11px;line-height:1.7}
@media(max-width:1050px){.stats-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.content-grid{grid-template-columns:1fr}}
@media(max-width:600px){.hero{align-items:flex-start;flex-direction:column;padding:22px}.hero h1{font-size:23px}.stats-grid{gap:10px}.stat-card{padding:16px}.stat-card strong{font-size:25px}.panel{padding:16px}.toolbar{align-items:flex-start;flex-direction:column}.profile-grid{grid-template-columns:1fr}}
</style>