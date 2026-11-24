<template>
  <section class="classes-page">
    <header class="page-hero">
      <div class="hero-copy">
        <div class="eyebrow">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M20 8v6M23 11h-6"/></svg>
          TEACHING CLASSES
        </div>
        <h1>教学班级</h1>
        <p>集中查看本人承担的教学班、课程归属、学期及排课信息。</p>
        <div class="hero-tags">
          <span><i></i> 教师专属空间</span>
          <span><i></i> 使用现有教务接口</span>
        </div>
      </div>
      <div class="hero-side" aria-hidden="true">
        <div class="hero-emblem">
          <svg viewBox="0 0 120 120"><circle cx="43" cy="35" r="16"/><path d="M12 91V79c0-13 11-23 24-23h14c9 0 17 5 21 12"/><circle cx="83" cy="47" r="12"/><path d="M75 67h13c12 0 21 9 21 21v3H72"/><path d="M62 78h18M71 69v18"/></svg>
        </div>
        <span class="hero-side-caption">TEACHING SPACE</span>
      </div>
    </header>

    <div class="summary-grid">
      <article class="summary-card">
        <div class="summary-icon summary-icon-blue"><svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/></svg></div>
        <div class="summary-copy"><span>教学班数量</span><strong>{{ classes.length }}</strong><small>当前账号可查看的教学班</small></div>
      </article>
      <article class="summary-card">
        <div class="summary-icon summary-icon-teal"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></svg></div>
        <div class="summary-copy"><span>涉及学期</span><strong>{{ semesterOptions.length }}</strong><small>按实际返回的学期信息统计</small></div>
      </article>
      <article class="summary-card">
        <div class="summary-icon summary-icon-violet"><svg viewBox="0 0 24 24"><path d="M4 5h16M4 12h16M4 19h10"/><circle cx="18" cy="19" r="2"/></svg></div>
        <div class="summary-copy"><span>关联课程</span><strong>{{ uniqueCourseCount }}</strong><small>按教学班课程信息去重</small></div>
      </article>
      <article class="summary-card">
        <div class="summary-icon summary-icon-amber"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></div>
        <div class="summary-copy"><span>排课信息</span><strong>{{ scheduledCount }}</strong><small>含上课时间或教学地点的班级</small></div>
      </article>
    </div>

    <section class="classes-panel">
      <div class="panel-heading">
        <div>
          <div class="heading-title-row"><span class="heading-accent"></span><h2>我的教学班</h2></div>
          <p>可按教学班名称、课程名称、课程代码或学期查找。</p>
        </div>
        <button class="refresh-button" type="button" :disabled="loading" @click="loadClasses">
          <svg :class="{ spinning: loading }" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 7v5h-5M4.5 9A8 8 0 0 1 18 5l2 2M4 17v-5h5M19.5 15A8 8 0 0 1 6 19l-2-2"/></svg>
          {{ loading ? '正在刷新' : '刷新教学班' }}
        </button>
      </div>

      <div class="filter-bar">
        <label class="search-box">
          <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg>
          <input v-model.trim="keyword" type="search" placeholder="搜索教学班、课程名称或课程代码" aria-label="搜索教学班" />
        </label>
        <label class="semester-filter"><span>学期</span>
          <select v-model="selectedSemester" aria-label="按学期筛选"><option value="all">全部学期</option><option v-for="semester in semesterOptions" :key="semester" :value="semester">{{ semester }}</option></select>
        </label>
      </div>

      <div v-if="errorMessage" class="state-message state-error">
        <strong>教学班信息暂时无法加载</strong>
        <span>{{ errorMessage }}</span>
        <button type="button" @click="loadClasses">重试</button>
      </div>
      <div v-else-if="loading && !loaded" class="state-message">正在加载本人授权的教学班信息…</div>
      <template v-else>
        <div class="result-meta"><span>共 {{ classes.length }} 个教学班</span><span>当前显示 {{ filteredClasses.length }} 个</span></div>
        <div v-if="filteredClasses.length" class="class-grid">
          <article v-for="(item, index) in filteredClasses" :key="item.id" class="class-card">
            <div class="class-card-top">
              <span class="class-number">{{ String(index + 1).padStart(2, '0') }}</span>
              <span class="record-tag"><i></i> 教学班记录</span>
            </div>
            <h3>{{ item.className || item.courseName || '教学班' }}</h3>
            <p class="course-name">{{ item.courseName || '课程名称暂未提供' }}</p>
            <div class="class-info">
              <div><span class="info-icon"><svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/></svg></span><span><small>课程代码</small><b>{{ item.courseCode || '暂未提供' }}</b></span></div>
              <div><span class="info-icon info-icon-teal"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></svg></span><span><small>所属学期</small><b>{{ item.semesterName || '暂未提供' }}</b></span></div>
              <div><span class="info-icon info-icon-violet"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg></span><span><small>上课时间</small><b>{{ item.schedule || '暂未提供' }}</b></span></div>
              <div><span class="info-icon info-icon-amber"><svg viewBox="0 0 24 24"><path d="M3 21h18M5 21V7l7-4 7 4v14M9 10h.01M15 10h.01M9 14h.01M15 14h.01M10 21v-4h4v4"/></svg></span><span><small>教学地点</small><b>{{ item.classroom || '暂未提供' }}</b></span></div>
            </div>
            <div class="card-footer"><span>数据范围以服务端授权为准</span><button type="button" @click="selectedClass = item">查看详情 <span aria-hidden="true">→</span></button></div>
          </article>
        </div>
        <div v-else class="empty-state">
          <div class="empty-icon"><svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/></svg></div>
          <strong>{{ classes.length ? '没有符合条件的教学班' : '当前账号暂无可展示的教学班' }}</strong>
          <p>{{ classes.length ? '请调整搜索关键词或学期筛选条件。' : '如你认为应当存在教学班记录，请检查后端数据及教师授权关系。' }}</p>
          <button v-if="keyword || selectedSemester !== 'all'" type="button" @click="clearFilters">清除筛选</button>
        </div>
      </template>
      <p class="footnote">本页面仅展示教务服务端返回且当前教师有权查看的教学班信息，不生成模拟班级记录。</p>
    </section>

    <div v-if="selectedClass" class="modal-backdrop" role="presentation" @click.self="selectedClass = null" @keydown.esc.window="selectedClass = null">
      <section class="detail-modal" role="dialog" aria-modal="true" aria-labelledby="detail-title">
        <header class="detail-header">
          <div class="detail-avatar"><svg viewBox="0 0 24 24"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M20 8v6M23 11h-6"/></svg></div>
          <div class="detail-title"><small>TEACHING CLASS DETAILS</small><h2 id="detail-title">{{ selectedClass.className || selectedClass.courseName || '教学班详情' }}</h2><p>{{ selectedClass.courseName || '课程名称暂未提供' }}</p></div>
          <button class="close-button" type="button" aria-label="关闭详情" @click="selectedClass = null">×</button>
        </header>
        <div class="detail-body">
          <div class="detail-section-title"><span></span> 教学班信息</div>
          <div class="detail-grid">
            <div class="detail-field"><small>教学班名称</small><strong>{{ selectedClass.className || '暂未提供' }}</strong></div>
            <div class="detail-field"><small>课程名称</small><strong>{{ selectedClass.courseName || '暂未提供' }}</strong></div>
            <div class="detail-field"><small>课程代码</small><strong>{{ selectedClass.courseCode || '暂未提供' }}</strong></div>
            <div class="detail-field"><small>所属学期</small><strong>{{ selectedClass.semesterName || '暂未提供' }}</strong></div>
            <div class="detail-field"><small>上课时间</small><strong>{{ selectedClass.schedule || '暂未提供' }}</strong></div>
            <div class="detail-field"><small>教学地点</small><strong>{{ selectedClass.classroom || '暂未提供' }}</strong></div>
            <div class="detail-field"><small>任课教师</small><strong>{{ selectedClass.teacherName || '当前登录教师授权范围' }}</strong></div>
          </div>
          <p class="detail-note">未显示的字段代表当前接口没有返回相应信息；本页面不会用虚构内容填充。</p>
        </div>
        <footer class="detail-footer"><button type="button" @click="selectedClass = null">关闭</button></footer>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '@/api/index'

interface TeachingClass {
  id: number | string
  className: string
  courseName: string
  courseCode: string
  semesterName: string
  schedule: string
  classroom: string
  teacherName: string
}

interface ListResult<T> { count: number; results: T[] }

function textValue(...values: unknown[]): string {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) return value.trim()
    if (typeof value === 'number') return String(value)
  }
  return ''
}

function normalizeList(payload: any): ListResult<TeachingClass> {
  const source = payload?.data ?? payload
  const rows = Array.isArray(source) ? source : Array.isArray(source?.results) ? source.results : []
  const results = rows.map((row: any, index: number) => ({
    id: row?.id ?? `teaching-class-${index}`,
    className: textValue(row?.class_name, row?.teaching_class_name, row?.name, row?.title),
    courseName: textValue(row?.course_name, row?.course?.name, row?.course?.title),
    courseCode: textValue(row?.course_code, row?.course?.code, row?.code),
    semesterName: textValue(row?.semester_name, row?.semester?.name, row?.semester?.title),
    schedule: textValue(row?.schedule, row?.schedule_text, row?.time_description, row?.weekly_schedule),
    classroom: textValue(row?.classroom, row?.room, row?.location),
    teacherName: textValue(row?.teacher_name, row?.teacher?.name),
  }))
  return { count: Number(source?.count ?? results.length), results }
}

const classes = ref<TeachingClass[]>([])
const loading = ref(false)
const loaded = ref(false)
const errorMessage = ref('')
const keyword = ref('')
const selectedSemester = ref('all')
const selectedClass = ref<TeachingClass | null>(null)

const semesterOptions = computed(() => [...new Set(classes.value.map(item => item.semesterName).filter(Boolean))].sort())
const uniqueCourseCount = computed(() => new Set(classes.value.map(item => item.courseName || item.courseCode).filter(Boolean)).size)
const scheduledCount = computed(() => classes.value.filter(item => item.schedule || item.classroom).length)
const filteredClasses = computed(() => {
  const q = keyword.value.toLocaleLowerCase()
  return classes.value.filter(item => {
    const matchesKeyword = !q || [item.className, item.courseName, item.courseCode, item.semesterName, item.schedule, item.classroom]
      .some(value => value.toLocaleLowerCase().includes(q))
    const matchesSemester = selectedSemester.value === 'all' || item.semesterName === selectedSemester.value
    return matchesKeyword && matchesSemester
  })
})

function clearFilters() {
  keyword.value = ''
  selectedSemester.value = 'all'
}

async function loadClasses() {
  loading.value = true
  errorMessage.value = ''
  try {
    const payload = await api.get('/teaching-classes/', { params: { page_size: 100 } })
    const result = normalizeList(payload)
    classes.value = result.results
  } catch (error) {
    console.error('加载教师教学班失败：', error)
    errorMessage.value = '请确认后端服务正常，并检查当前教师账号是否已关联教学班。'
    classes.value = []
  } finally {
    loaded.value = true
    loading.value = false
  }
}

onMounted(loadClasses)
</script>

<style scoped>
.classes-page{max-width:1500px;margin:0 auto;color:#172b4d;padding-bottom:8px}.page-hero{position:relative;display:flex;justify-content:space-between;align-items:center;gap:24px;overflow:hidden;padding:30px 32px;border-radius:18px;background:linear-gradient(115deg,#102e63 0%,#18548e 62%,#236a9f 100%);color:#fff;box-shadow:0 12px 30px #0b2a5b18}.page-hero:after{content:"";position:absolute;width:260px;height:260px;right:70px;top:-130px;border:1px solid #ffffff16;border-radius:50%;box-shadow:0 0 0 34px #ffffff08,0 0 0 70px #ffffff05;pointer-events:none}.hero-copy,.hero-side{position:relative;z-index:1}.eyebrow{display:flex;align-items:center;gap:9px;margin:0 0 13px;color:#b9dcff;font-size:10px;font-weight:700;letter-spacing:2px}.eyebrow svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.page-hero h1{margin:0;font-size:29px;font-weight:750;letter-spacing:.3px}.page-hero p{margin:11px 0 0;color:#d8e9fb;font-size:13px;line-height:1.7}.hero-tags{display:flex;gap:9px;flex-wrap:wrap;margin-top:17px}.hero-tags span{display:inline-flex;align-items:center;gap:7px;padding:6px 10px;border:1px solid #ffffff26;border-radius:20px;background:#ffffff0d;color:#e1efff;font-size:11px}.hero-tags i,.record-tag i{width:6px;height:6px;border-radius:50%;background:#42d5b0;display:inline-block}.hero-side{display:flex;align-items:center;gap:16px;min-width:160px;justify-content:flex-end}.hero-emblem{display:grid;place-items:center;width:96px;height:96px;border-radius:24px;background:#ffffff12;border:1px solid #ffffff20;transform:rotate(-4deg)}.hero-emblem svg{width:72px;height:72px;fill:none;stroke:#a8d3fb;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}.hero-side-caption{position:absolute;right:0;bottom:-27px;color:#c8e1fb;font-size:9px;letter-spacing:2px}.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:18px 0}.summary-card{display:flex;align-items:center;gap:14px;min-width:0;padding:18px 19px;border:1px solid #e7edf5;border-radius:15px;background:#fff;box-shadow:0 4px 16px #173b6508}.summary-icon{display:grid;place-items:center;flex:0 0 44px;width:44px;height:44px;border-radius:13px}.summary-icon svg,.info-icon svg,.empty-icon svg{width:21px;height:21px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.summary-icon-blue,.info-icon{background:#edf5ff;color:#2674cf}.summary-icon-teal,.info-icon-teal{background:#eaf8f5;color:#159c88}.summary-icon-violet,.info-icon-violet{background:#f2efff;color:#8067e8}.summary-icon-amber,.info-icon-amber{background:#fff4e6;color:#c58a30}.summary-copy{min-width:0}.summary-copy span,.summary-copy small{display:block;color:#8190a6;font-size:11px}.summary-copy strong{display:block;margin:5px 0;color:#1a5d9b;font-size:26px;line-height:1.1}.summary-copy small{font-size:10px;line-height:1.5}.classes-panel{padding:23px;border:1px solid #e6edf5;border-radius:16px;background:#fff;box-shadow:0 4px 16px #173b6508}.panel-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:15px}.heading-title-row{display:flex;align-items:center;gap:10px}.heading-accent{width:4px;height:20px;border-radius:3px;background:#2f7bd2}.panel-heading h2{margin:0;color:#203753;font-size:18px}.panel-heading p{margin:8px 0 0 14px;color:#8a98aa;font-size:12px}.refresh-button{display:flex;align-items:center;gap:8px;padding:9px 13px;border:1px solid #dce7f4;border-radius:9px;background:#fff;color:#2868a8;font-size:12px;cursor:pointer;white-space:nowrap}.refresh-button:disabled{opacity:.6;cursor:wait}.refresh-button svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.spinning{animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}.filter-bar{display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin:22px 0 17px;padding:13px 14px;border:1px solid #edf1f7;border-radius:11px;background:#f8fafd}.search-box{display:flex;align-items:center;gap:9px;flex:1 1 280px;max-width:500px;padding:0 12px;border:1px solid #e0e8f2;border-radius:8px;background:#fff}.search-box svg{width:17px;height:17px;flex-shrink:0;fill:none;stroke:#8b9bb0;stroke-width:1.7;stroke-linecap:round}.search-box input{width:100%;height:38px;border:0;outline:none;background:transparent;color:#263b55;font-size:12px}.search-box input::placeholder{color:#a0acbc}.semester-filter{display:flex;align-items:center;gap:10px;color:#7c8ba0;font-size:12px}.semester-filter select{min-width:160px;padding:10px 28px 10px 11px;border:1px solid #e0e8f2;border-radius:8px;background:#fff;color:#344a64;font-size:12px;outline:none}.result-meta{display:flex;justify-content:space-between;gap:12px;margin:0 2px 12px;color:#91a0b3;font-size:11px}.class-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px}.class-card{min-width:0;padding:19px;border:1px solid #e8eef6;border-radius:14px;background:linear-gradient(180deg,#fff 0%,#fcfdff 100%);transition:border-color .18s,box-shadow .18s,transform .18s}.class-card:hover{border-color:#c7daf3;box-shadow:0 8px 24px #1d4d7c0d;transform:translateY(-1px)}.class-card-top{display:flex;align-items:center;justify-content:space-between;gap:10px}.class-number{display:grid;place-items:center;width:34px;height:34px;border-radius:10px;background:#edf4ff;color:#316bb5;font-size:12px;font-weight:700}.record-tag{display:inline-flex;align-items:center;gap:6px;padding:5px 8px;border-radius:20px;background:#edf8f4;color:#2d8c70;font-size:10px}.class-card h3{margin:17px 0 5px;color:#203753;font-size:18px;line-height:1.4;overflow-wrap:anywhere}.course-name{margin:0;color:#6f8199;font-size:12px;line-height:1.6}.class-info{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:15px;margin-top:20px;padding:16px 0;border-top:1px solid #edf1f6;border-bottom:1px solid #edf1f6}.class-info>div{display:flex;align-items:center;gap:10px;min-width:0}.info-icon{display:grid;place-items:center;flex:0 0 34px;width:34px;height:34px;border-radius:10px}.info-icon svg{width:17px;height:17px}.class-info>div>span:last-child{display:block;min-width:0}.class-info small,.class-info b{display:block;overflow-wrap:anywhere}.class-info small{margin-bottom:5px;color:#94a0b0;font-size:10px}.class-info b{color:#425872;font-size:11px;font-weight:600;line-height:1.5}.card-footer{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-top:15px}.card-footer>span{color:#9aa6b5;font-size:10px}.card-footer button{border:0;background:transparent;color:#286db4;font-size:11px;font-weight:600;cursor:pointer;white-space:nowrap}.card-footer button span{margin-left:4px;font-size:15px}.state-message,.empty-state{padding:48px 16px;text-align:center;color:#8b99ab;font-size:12px}.state-error{display:flex;flex-direction:column;align-items:center;gap:10px;margin-top:15px;border:1px solid #f4dfd7;border-radius:12px;background:#fff9f7;color:#9e594a}.state-error strong{font-size:14px}.state-error button,.empty-state button{padding:8px 14px;border:1px solid #d9e5f4;border-radius:8px;background:#fff;color:#2868a8;cursor:pointer}.empty-state{margin-top:8px;border:1px dashed #dfe7f1;border-radius:13px;background:#fafcfe}.empty-icon{display:grid;place-items:center;width:52px;height:52px;margin:0 auto 13px;border-radius:15px;background:#edf5ff;color:#4283c9}.empty-state strong{display:block;color:#4a5f79;font-size:14px}.empty-state p{margin:8px 0 17px;color:#97a4b4;line-height:1.7}.footnote{margin:18px 2px 0;color:#9aa6b5;font-size:10px;line-height:1.7}.modal-backdrop{position:fixed;z-index:1000;inset:0;display:flex;justify-content:flex-end;background:#0b183066;backdrop-filter:blur(2px)}.detail-modal{display:flex;flex-direction:column;width:min(520px,100%);height:100%;overflow:auto;background:#fff;box-shadow:-14px 0 40px #0b18301a;animation:slide-in .2s ease-out}@keyframes slide-in{from{transform:translateX(20px);opacity:.7}to{transform:translateX(0);opacity:1}}.detail-header{display:flex;align-items:center;gap:14px;padding:25px 24px;border-bottom:1px solid #edf1f6}.detail-avatar{display:grid;place-items:center;flex:0 0 48px;width:48px;height:48px;border-radius:15px;background:#eaf2ff;color:#2a68b2}.detail-avatar svg{width:25px;height:25px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}.detail-title{flex:1;min-width:0}.detail-title small{color:#8a9bb1;font-size:9px;letter-spacing:1.5px}.detail-title h2{margin:5px 0;color:#203753;font-size:19px;overflow-wrap:anywhere}.detail-title p{margin:0;color:#8190a6;font-size:12px}.close-button{align-self:flex-start;width:32px;height:32px;border:1px solid #e2e8f0;border-radius:9px;background:#fff;color:#6d7d91;font-size:23px;line-height:1;cursor:pointer}.detail-body{flex:1;padding:23px 24px}.detail-section-title{display:flex;align-items:center;gap:8px;margin-bottom:15px;color:#344a64;font-size:13px;font-weight:700}.detail-section-title span{width:3px;height:16px;border-radius:3px;background:#2f7bd2}.detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.detail-field{min-width:0;padding:14px;border-radius:10px;background:#f7f9fc}.detail-field small,.detail-field strong{display:block;overflow-wrap:anywhere}.detail-field small{margin-bottom:8px;color:#8c9aab;font-size:10px}.detail-field strong{color:#34465d;font-size:12px;line-height:1.6}.detail-note{margin:18px 0 0;color:#9aa6b5;font-size:10px;line-height:1.7}.detail-footer{display:flex;justify-content:flex-end;padding:16px 24px;border-top:1px solid #edf1f6}.detail-footer button{padding:9px 20px;border:1px solid #dce6f2;border-radius:8px;background:#fff;color:#3b5b7c;cursor:pointer}
@media(max-width:1100px){.summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.class-grid{grid-template-columns:1fr}.hero-emblem{width:76px;height:76px}.hero-emblem svg{width:60px;height:60px}}
@media(max-width:650px){.page-hero{align-items:flex-start;flex-direction:column;padding:23px}.page-hero h1{font-size:24px}.hero-side{display:none}.summary-grid{gap:10px}.summary-card{padding:14px;gap:10px}.summary-icon{flex-basis:36px;width:36px;height:36px}.summary-copy strong{font-size:23px}.summary-copy small{font-size:9px}.classes-panel{padding:16px}.panel-heading{align-items:flex-start}.panel-heading h2{font-size:16px}.panel-heading p{max-width:240px;line-height:1.6}.filter-bar{align-items:stretch;flex-direction:column}.search-box{max-width:none;flex-basis:auto}.semester-filter{justify-content:space-between}.semester-filter select{flex:1;min-width:0}.class-card{padding:15px}.class-info{gap:13px 8px}.class-info>div{gap:7px}.info-icon{flex-basis:29px;width:29px;height:29px}.card-footer{align-items:flex-start}.detail-header,.detail-body{padding-left:17px;padding-right:17px}.detail-grid{gap:8px}.detail-field{padding:11px}}
</style>
