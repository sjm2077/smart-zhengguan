<template>
  <section class="courses-page">
    <header class="page-hero">
      <div class="hero-copy">
        <div class="eyebrow">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
          </svg>
          TEACHING RESOURCES
        </div>
        <h1>我的课程</h1>
        <p>集中查看本人已获授权的授课课程与学期信息，让日常教学安排一目了然。</p>
        <div class="hero-tags">
          <span><i></i> 教师专属空间</span>
          <span><i></i> 服务端授权数据</span>
        </div>
      </div>

      <div class="hero-side">
        <div class="hero-emblem" aria-hidden="true">
          <svg viewBox="0 0 120 120">
            <path d="M19 36 60 16l41 20-41 20L19 36Z" />
            <path d="M34 45v26c0 8 12 15 26 15s26-7 26-15V45" />
            <path d="M101 37v29" />
            <circle cx="101" cy="72" r="5" />
            <path d="M31 93h58" />
          </svg>
        </div>
        <div class="hero-user">
          <span class="avatar">{{ avatarLetter }}</span>
          <span class="hero-user-text">
            <small>当前登录教师</small>
            <strong>{{ username }}</strong>
            <span>任课教师</span>
          </span>
        </div>
      </div>
    </header>

    <div class="summary-grid">
      <article class="summary-card">
        <div class="summary-icon summary-icon-blue">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
          </svg>
        </div>
        <div class="summary-copy">
          <span>授课课程</span>
          <strong>{{ courses.length }}</strong>
          <small>当前账号已授权的课程</small>
        </div>
      </article>

      <article class="summary-card">
        <div class="summary-icon summary-icon-teal">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <rect x="3" y="5" width="18" height="16" rx="2" />
            <path d="M16 3v4M8 3v4M3 10h18" />
          </svg>
        </div>
        <div class="summary-copy">
          <span>涉及学期</span>
          <strong>{{ semesterOptions.length }}</strong>
          <small>按课程学期信息汇总</small>
        </div>
      </article>

      <article class="summary-card">
        <div class="summary-icon summary-icon-violet">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-4-4" />
          </svg>
        </div>
        <div class="summary-copy">
          <span>当前筛选结果</span>
          <strong>{{ filteredCourses.length }}</strong>
          <small>课程列表匹配数量</small>
        </div>
      </article>
    </div>

    <section class="course-panel">
      <div class="panel-heading">
        <div>
          <div class="heading-title-row">
            <span class="heading-accent"></span>
            <h2>课程列表</h2>
          </div>
          <p>可按课程名称、课程代码或学期快速查找。</p>
        </div>
        <button class="refresh-button" type="button" :disabled="loading" @click="loadCourses">
          <svg :class="{ spinning: loading }" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M20 7v5h-5" />
            <path d="M4.5 9A8 8 0 0 1 18 5l2 2M4 17v-5h5" />
            <path d="M19.5 15A8 8 0 0 1 6 19l-2-2" />
          </svg>
          {{ loading ? '正在刷新' : '刷新课程' }}
        </button>
      </div>

      <div class="filter-bar">
        <label class="search-box">
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-4-4" />
          </svg>
          <input
            v-model="searchKeyword"
            type="search"
            placeholder="搜索课程名称或课程代码"
            aria-label="搜索课程名称或课程代码"
          />
          <button
            v-if="searchKeyword"
            class="clear-search"
            type="button"
            aria-label="清空搜索"
            @click="searchKeyword = ''"
          >×</button>
        </label>

        <label class="semester-select">
          <span>学期</span>
          <select v-model="selectedSemester" aria-label="按学期筛选">
            <option value="all">全部学期</option>
            <option v-for="semester in semesterOptions" :key="semester" :value="semester">
              {{ semester }}
            </option>
          </select>
        </label>

        <button
          v-if="searchKeyword || selectedSemester !== 'all'"
          class="reset-button"
          type="button"
          @click="resetFilters"
        >重置筛选</button>
      </div>

      <div v-if="errorMessage" class="message message-warning">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v5M12 16.5v.1" />
        </svg>
        <span>{{ errorMessage }}</span>
      </div>

      <div v-if="loading && !loaded" class="loading-state">
        <span class="loading-spinner"></span>
        <span>正在读取当前账号的课程信息…</span>
      </div>

      <template v-else>
        <div class="table-meta">
          <span>共 <b>{{ courses.length }}</b> 门课程</span>
          <span>当前显示 <b>{{ filteredCourses.length }}</b> 条</span>
        </div>

        <div v-if="filteredCourses.length" class="table-wrap">
          <table>
            <thead>
              <tr>
                <th class="index-column">序号</th>
                <th>课程代码</th>
                <th>课程名称</th>
                <th>所属学期</th>
                <th class="status-column">数据范围</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(course, index) in filteredCourses" :key="course.id">
                <td class="index-column">{{ String(index + 1).padStart(2, '0') }}</td>
                <td><span class="course-code">{{ course.code || '—' }}</span></td>
                <td>
                  <div class="course-name-cell">
                    <span class="course-mini-icon">
                      <svg viewBox="0 0 24 24" aria-hidden="true">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
                      </svg>
                    </span>
                    <strong>{{ course.name || '未命名课程' }}</strong>
                  </div>
                </td>
                <td>
                  <span class="semester-label">{{ course.semester_name || '当前授权学期' }}</span>
                </td>
                <td class="status-column"><span class="scope-badge"><i></i> 已授权</span></td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-else class="empty-state">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z" />
            </svg>
          </div>
          <strong>{{ courses.length ? '没有找到匹配的课程' : '暂时没有可展示的课程' }}</strong>
          <p>{{ courses.length ? '请调整搜索关键词或学期条件后重试。' : '当前账号暂无服务端返回的授课课程，请确认课程授权信息。' }}</p>
          <button v-if="courses.length && (searchKeyword || selectedSemester !== 'all')" type="button" @click="resetFilters">
            清除筛选条件
          </button>
        </div>
      </template>

      <footer class="panel-footer">
        <span class="footer-dot"></span>
        课程信息以服务端实际返回及当前账号权限为准。
      </footer>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/api/index'

interface Course {
  id: number
  code?: string
  name?: string
  semester_name?: string
}

interface ListResult<T> {
  count: number
  results: T[]
}

function normalizeList<T>(payload: any): ListResult<T> {
  if (Array.isArray(payload)) {
    return { count: payload.length, results: payload as T[] }
  }

  const results = Array.isArray(payload?.results) ? payload.results as T[] : []
  return { count: Number(payload?.count ?? results.length), results }
}

async function fetchCourses(): Promise<ListResult<Course>> {
  const payload = await api.get('/courses/', { params: { page_size: 100 } })
  return normalizeList<Course>(payload)
}

function readUsername(): string {
  try {
    const user = JSON.parse(localStorage.getItem('user_info') || '{}')
    return String(user.name || user.first_name || user.username || '教师用户')
  } catch {
    return '教师用户'
  }
}

const username = ref(readUsername())
const loading = ref(false)
const loaded = ref(false)
const errorMessage = ref('')
const courses = ref<Course[]>([])
const searchKeyword = ref('')
const selectedSemester = ref('all')

const avatarLetter = computed(() => username.value.trim().charAt(0).toUpperCase() || 'T')

const semesterOptions = computed(() => {
  const semesters = courses.value.map((course) => course.semester_name || '当前授权学期')
  return [...new Set(semesters)].sort((a, b) => b.localeCompare(a, 'zh-CN'))
})

const filteredCourses = computed(() => {
  const keyword = searchKeyword.value.trim().toLocaleLowerCase()
  return courses.value.filter((course) => {
    const matchesKeyword = !keyword || [
      course.code,
      course.name,
      course.semester_name,
    ].some((value) => String(value ?? '').toLocaleLowerCase().includes(keyword))

    const semester = course.semester_name || '当前授权学期'
    const matchesSemester = selectedSemester.value === 'all' || semester === selectedSemester.value
    return matchesKeyword && matchesSemester
  })
})

function resetFilters() {
  searchKeyword.value = ''
  selectedSemester.value = 'all'
}

async function loadCourses() {
  loading.value = true
  errorMessage.value = ''

  try {
    const result = await fetchCourses()
    courses.value = result.results
    loaded.value = true
  } catch (error) {
    errorMessage.value = '课程信息暂时无法加载，请确认后端服务正常，并检查当前教师账号的课程授权。'
    loaded.value = true
    console.error('加载教师课程失败：', error)
  } finally {
    loading.value = false
  }
}

onMounted(loadCourses)
</script>

<style scoped>
.courses-page {
  width: 100%;
  max-width: 1500px;
  margin: 0 auto;
  color: #1c3553;
  --course-blue: #1f4c91;
  --course-blue-dark: #0d2b5b;
  --course-muted: #8191a7;
  --course-border: #e6edf5;
}

.page-hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  min-height: 190px;
  padding: 30px 34px;
  overflow: hidden;
  border-radius: 20px;
  background:
    radial-gradient(circle at 75% 20%, rgba(107, 177, 255, .22), transparent 27%),
    linear-gradient(116deg, #102e62 0%, #174c83 58%, #23649a 100%);
  color: #fff;
  box-shadow: 0 14px 34px rgba(17, 57, 103, .12);
}

.page-hero::after {
  position: absolute;
  top: -90px;
  right: 115px;
  width: 270px;
  height: 270px;
  border: 1px solid rgba(255, 255, 255, .09);
  border-radius: 50%;
  content: '';
  pointer-events: none;
}

.hero-copy,
.hero-side {
  position: relative;
  z-index: 1;
}

.hero-copy {
  max-width: 760px;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 13px;
  color: #a8d2ff;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 2.2px;
}

.eyebrow svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.page-hero h1 {
  margin: 0;
  color: #fff;
  font-size: 29px;
  font-weight: 750;
  letter-spacing: .5px;
}

.page-hero p {
  max-width: 650px;
  margin: 11px 0 0;
  color: #d2e4f8;
  font-size: 13px;
  line-height: 1.8;
}

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.hero-tags span {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  border: 1px solid rgba(255, 255, 255, .16);
  border-radius: 20px;
  background: rgba(255, 255, 255, .07);
  color: #dcecff;
  font-size: 11px;
}

.hero-tags i,
.scope-badge i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #49d5ae;
}

.hero-side {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 225px;
}

.hero-emblem {
  display: grid;
  place-items: center;
  width: 100px;
  height: 100px;
  border: 1px solid rgba(255, 255, 255, .15);
  border-radius: 26px;
  background: rgba(255, 255, 255, .08);
  transform: rotate(-5deg);
}

.hero-emblem svg {
  width: 78px;
  height: 78px;
  fill: none;
  stroke: #9dceff;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.hero-user {
  display: flex;
  align-items: center;
  gap: 11px;
  min-width: 0;
}

.avatar {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  border: 1px solid rgba(255, 255, 255, .38);
  border-radius: 50%;
  background: rgba(255, 255, 255, .12);
  color: #fff;
  font-size: 17px;
  font-weight: 700;
}

.hero-user-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 4px;
}

.hero-user-text small,
.hero-user-text > span {
  color: #c3dcf5;
  font-size: 10px;
}

.hero-user-text strong {
  max-width: 130px;
  overflow: hidden;
  color: #fff;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin: 20px 0;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 15px;
  min-width: 0;
  padding: 19px 21px;
  border: 1px solid var(--course-border);
  border-radius: 15px;
  background: #fff;
  box-shadow: 0 5px 18px rgba(22, 55, 93, .035);
}

.summary-icon {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  flex: 0 0 auto;
  border-radius: 13px;
}

.summary-icon svg {
  width: 23px;
  height: 23px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.summary-icon-blue {
  background: #edf4ff;
  color: #2868b2;
}

.summary-icon-teal {
  background: #eaf8f5;
  color: #168c7a;
}

.summary-icon-violet {
  background: #f2efff;
  color: #7462c8;
}

.summary-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.summary-copy > span {
  color: #71829a;
  font-size: 12px;
}

.summary-copy strong {
  margin: 5px 0 4px;
  color: #174b86;
  font-size: 28px;
  font-weight: 750;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.summary-copy small {
  overflow: hidden;
  color: #9aa7b7;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-panel {
  padding: 24px;
  border: 1px solid var(--course-border);
  border-radius: 17px;
  background: #fff;
  box-shadow: 0 5px 20px rgba(22, 55, 93, .035);
}

.panel-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.heading-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.heading-accent {
  width: 4px;
  height: 19px;
  border-radius: 3px;
  background: #2c72bd;
}

.panel-heading h2 {
  margin: 0;
  color: #1d3857;
  font-size: 17px;
  font-weight: 750;
}

.panel-heading p {
  margin: 8px 0 0 14px;
  color: #8b9ab0;
  font-size: 12px;
}

.refresh-button,
.reset-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 0 0 auto;
  padding: 9px 13px;
  border: 1px solid #dce7f4;
  border-radius: 9px;
  background: #fff;
  color: #285f9d;
  font-size: 12px;
  cursor: pointer;
  transition: background .18s, border-color .18s, transform .18s;
}

.refresh-button svg {
  width: 15px;
  height: 15px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.refresh-button:hover:not(:disabled),
.reset-button:hover {
  border-color: #b7d1ee;
  background: #f3f8ff;
}

.refresh-button:disabled {
  cursor: wait;
  opacity: .65;
}

.spinning {
  animation: spin 1s linear infinite;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 22px 0 16px;
  padding: 13px;
  border: 1px solid #edf1f7;
  border-radius: 12px;
  background: #f8fafd;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 220px;
  max-width: 430px;
  flex: 1;
  height: 38px;
  padding: 0 12px;
  border: 1px solid #e3eaf3;
  border-radius: 8px;
  background: #fff;
  transition: border-color .18s, box-shadow .18s;
}

.search-box:focus-within {
  border-color: #8ab6e8;
  box-shadow: 0 0 0 3px rgba(46, 117, 190, .09);
}

.search-box > svg {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
  fill: none;
  stroke: #8b9ab0;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.search-box input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #263f5d;
  font-size: 12px;
}

.search-box input::placeholder {
  color: #a4afbe;
}

.clear-search {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  flex: 0 0 auto;
  border: 0;
  border-radius: 50%;
  background: #eef2f7;
  color: #6d7f94;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.semester-select {
  display: flex;
  align-items: center;
  gap: 9px;
  color: #75859b;
  font-size: 12px;
}

.semester-select select {
  max-width: 230px;
  height: 38px;
  padding: 0 30px 0 11px;
  border: 1px solid #e3eaf3;
  border-radius: 8px;
  outline: 0;
  background: #fff;
  color: #344c68;
  font-size: 12px;
  cursor: pointer;
}

.semester-select select:focus {
  border-color: #8ab6e8;
}

.reset-button {
  height: 38px;
}

.table-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 2px 12px;
  color: #93a0b1;
  font-size: 11px;
}

.table-meta b {
  color: #42688f;
  font-weight: 700;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid #edf1f6;
  border-radius: 10px;
}

table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 12px;
}

thead {
  background: #f5f8fc;
}

th {
  padding: 14px 16px;
  color: #788aa1;
  font-size: 11px;
  font-weight: 650;
  white-space: nowrap;
}

td {
  padding: 15px 16px;
  border-top: 1px solid #edf1f6;
  color: #526881;
  vertical-align: middle;
}

tbody tr {
  transition: background .15s;
}

tbody tr:hover {
  background: #f8fbff;
}

.index-column {
  width: 70px;
  color: #a1adbb;
  font-variant-numeric: tabular-nums;
}

.course-code {
  display: inline-block;
  padding: 5px 8px;
  border: 1px solid #e4edf8;
  border-radius: 6px;
  background: #f5f9ff;
  color: #416d9e;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.course-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 190px;
}

.course-mini-icon {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  border-radius: 8px;
  background: #edf4ff;
  color: #3875b6;
}

.course-mini-icon svg {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.course-name-cell strong {
  color: #304963;
  font-size: 12px;
  font-weight: 650;
}

.semester-label {
  color: #627b96;
  white-space: nowrap;
}

.scope-badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 8px;
  border-radius: 20px;
  background: #edf9f4;
  color: #27815f;
  font-size: 10px;
  white-space: nowrap;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 45px 20px;
  border: 1px dashed #dce5ef;
  border-radius: 11px;
  background: #fbfcfe;
  text-align: center;
}

.empty-icon {
  display: grid;
  place-items: center;
  width: 56px;
  height: 56px;
  margin-bottom: 14px;
  border-radius: 17px;
  background: #edf4ff;
  color: #6a94c4;
}

.empty-icon svg {
  width: 26px;
  height: 26px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.empty-state strong {
  color: #3d536c;
  font-size: 13px;
}

.empty-state p {
  max-width: 500px;
  margin: 8px 0 0;
  color: #93a0b1;
  font-size: 11px;
  line-height: 1.8;
}

.empty-state button {
  margin-top: 14px;
  padding: 8px 12px;
  border: 1px solid #dbe6f3;
  border-radius: 8px;
  background: #fff;
  color: #2c659f;
  font-size: 11px;
  cursor: pointer;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 180px;
  color: #8798ad;
  font-size: 12px;
}

.loading-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid #dbe8f7;
  border-top-color: #2e73b7;
  border-radius: 50%;
  animation: spin .8s linear infinite;
}

.message {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  margin: 15px 0;
  padding: 12px 14px;
  border-radius: 9px;
  font-size: 12px;
  line-height: 1.7;
}

.message svg {
  width: 17px;
  height: 17px;
  flex: 0 0 auto;
  margin-top: 1px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.7;
  stroke-linecap: round;
}

.message-warning {
  border: 1px solid #f1dfb6;
  background: #fff9eb;
  color: #8c6b2c;
}

.panel-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 17px;
  padding-top: 14px;
  border-top: 1px solid #edf1f6;
  color: #9aa7b6;
  font-size: 10px;
}

.footer-dot {
  width: 5px;
  height: 5px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #9eb2ca;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 1120px) {
  .page-hero {
    padding: 26px;
  }

  .hero-side {
    min-width: auto;
  }

  .hero-emblem {
    display: none;
  }

  .summary-grid {
    gap: 12px;
  }

  .summary-card {
    padding: 17px;
  }
}

@media (max-width: 800px) {
  .page-hero {
    align-items: flex-start;
    flex-direction: column;
    gap: 22px;
  }

  .hero-side {
    width: 100%;
    padding-top: 17px;
    border-top: 1px solid rgba(255, 255, 255, .14);
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .filter-bar {
    align-items: stretch;
    flex-direction: column;
  }

  .search-box {
    max-width: none;
  }

  .semester-select {
    justify-content: space-between;
  }

  .semester-select select {
    max-width: 65%;
    flex: 1;
  }

  .reset-button {
    align-self: flex-start;
  }

  .course-panel {
    padding: 17px;
  }
}

@media (max-width: 520px) {
  .page-hero {
    padding: 22px;
    border-radius: 15px;
  }

  .page-hero h1 {
    font-size: 24px;
  }

  .panel-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .refresh-button {
    align-self: flex-start;
  }

  .course-panel {
    padding: 14px;
  }

  th,
  td {
    padding: 12px 11px;
  }

  .status-column {
    display: none;
  }
}
</style>
