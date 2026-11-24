<template>
  <!-- ============================================================
       学生画像与成长分析中心 — 用户画像平台
       布局：年级/专业筛选 → 统计卡片 → 学生档案管理 → 年级与专业分布 + 预警名单
             → 就业趋势 + 学业成绩分析 → 成长时间轴 + 优秀学生 → 班级对比 → 详情抽屉
  ============================================================ -->
  <div class="student-hub">
    <!-- ========== 顶部标题栏 ========== -->
    <div class="hub-topbar">
      <div class="hub-title-area">
        <h2 class="hub-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="hub-title-icon">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          学生画像与成长分析中心
        </h2>
        <p class="hub-subtitle">用户画像平台 · 全周期学业追踪 · 个性化成长分析</p>
      </div>
      <div class="hub-actions">
        <div class="student-filter-group">
          <label class="student-filter">
            <span>年级</span>
            <select v-model="currentGrade" aria-label="按年级筛选学生">
              <option v-for="grade in gradeOptions" :key="grade" :value="grade">
                {{ grade === '全部' ? '全部年级' : grade }}
              </option>
            </select>
          </label>
          <label class="student-filter">
            <span>专业</span>
            <select v-model="currentMajor" aria-label="按专业筛选学生">
              <option v-for="major in majorOptions" :key="major" :value="major">
                {{ major === '全部' ? '全部专业' : major }}
              </option>
            </select>
          </label>
        </div>
        <button class="btn-primary" :disabled="!archiveCollegeId" @click="openCreateStudent">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          新增学生
        </button>
        <button class="btn-outline" @click="triggerArchiveImport">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
          导入名单
        </button>
      </div>
    </div>

    <!-- ========== 第1行：4 统计卡片 ========== -->
    <div class="hub-stats-row">
      <div class="hub-stat-card" v-for="stat in studentStats" :key="stat.label">
        <div class="hub-stat-icon" :style="{ background: stat.bg, color: stat.color }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path :d="stat.icon"/></svg>
        </div>
        <div class="hub-stat-body">
          <div class="hub-stat-label">{{ stat.label }}</div>
          <div class="hub-stat-value">
            <span class="hub-stat-num">{{ stat.value }}</span>
            <span class="hub-stat-unit">{{ stat.unit }}</span>
          </div>
          <div class="hub-stat-sub">
            <span class="stat-scope">{{ stat.sub }}</span>
          </div>
        </div>
        <div class="hub-stat-spark">
          <svg viewBox="0 0 80 28" class="spark-svg">
            <polyline :points="stat.sparkline" fill="none" :stroke="stat.color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- ========== 第2行：全院学生信息档案管理（替换原学生画像卡） ========== -->
    <div class="hub-row-profile">
      <div id="module-student-profile-card" class="hub-panel archive-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <rect x="3" y="4" width="18" height="16" rx="2"/>
              <path d="M7 8h10M7 12h6M7 16h4"/>
            </svg>
            全院学生信息档案管理
          </span>
          <span class="hub-panel-badge">数据库档案 {{ archiveStudents.length.toLocaleString('zh-CN') }} 人</span>
        </div>

        <div class="archive-filter-row">
          <label class="archive-filter">
            <span>年级</span>
            <select v-model="archiveGradeFilter">
              <option value="全部">全部年级</option>
              <option v-for="grade in archiveGradeOptions" :key="grade" :value="grade">{{ grade }}</option>
            </select>
          </label>
          <label class="archive-filter">
            <span>专业</span>
            <select v-model="archiveMajorFilter">
              <option value="全部">全部专业</option>
              <option v-for="major in archiveMajorOptions" :key="major" :value="major">{{ major }}</option>
            </select>
          </label>
          <label class="archive-filter">
            <span>班级</span>
            <select v-model="archiveClassFilter">
              <option value="全部">全部班级</option>
              <option v-for="className in archiveClassOptions" :key="className" :value="className">{{ className }}</option>
            </select>
          </label>
          <label class="archive-filter">
            <span>学籍状态</span>
            <select v-model="archiveStatusFilter">
              <option value="全部">全部状态</option>
              <option value="在籍">在籍</option>
              <option value="非在籍">非在籍</option>
            </select>
          </label>
          <label class="archive-search">
            <span>学生搜索</span>
            <input v-model.trim="archiveSearch" type="search" placeholder="输入学号、姓名或联系方式">
          </label>
        </div>

        <div class="archive-action-row">
          <div class="archive-result-hint">
            <span>当前筛选结果 <strong>{{ archiveTotal.toLocaleString('zh-CN') }}</strong> 人</span>
            <span v-if="archiveLoading" class="archive-loading-text">正在读取学生档案…</span>
            <span v-else-if="archiveError" class="archive-error-text">{{ archiveError }}</span>
          </div>
          <div class="archive-actions">
            <button class="btn-outline archive-action-btn" @click="downloadStudentTemplate">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12m0 0l-4-4m4 4l4-4"/><path d="M4 17v3h16v-3"/></svg>
              下载模板
            </button>
            <button class="btn-outline archive-action-btn" @click="triggerArchiveImport">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 16V4m0 0L8 8m4-4l4 4"/><path d="M4 16v4h16v-4"/></svg>
              导入 Excel
            </button>
            <button class="btn-primary archive-action-btn" @click="exportArchiveExcel">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v12m0 0l-4-4m4 4l4-4"/><path d="M4 17v3h16v-3"/></svg>
              导出 Excel
            </button>
          </div>
        </div>

        <input
          ref="archiveImportInputRef"
          class="archive-file-input"
          type="file"
          accept=".xlsx,.xls"
          @change="handleArchiveFileChange"
        >

        <div class="archive-table-wrap">
          <table class="archive-table">
            <thead>
              <tr>
                <th>学号</th>
                <th>学生姓名</th>
                <th>所属专业</th>
                <th>年级 / 班级</th>
                <th>平均 GPA</th>
                <th>已修课程</th>
                <th>未通过课程</th>
                <th>学籍状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody v-if="archiveLoading">
              <tr><td colspan="9" class="archive-empty-cell">正在读取数据库中的学生档案…</td></tr>
            </tbody>
            <tbody v-else-if="archivePageRows.length">
              <tr v-for="student in archivePageRows" :key="student.id">
                <td class="archive-student-no">{{ student.student_no }}</td>
                <td>
                  <div class="archive-student-name">{{ student.name }}</div>
                  <div class="archive-secondary">{{ student.gender || '未说明' }}</div>
                </td>
                <td>{{ student.major || '未填写' }}</td>
                <td>
                  <div>{{ student.grade || '未填写' }}</div>
                  <div class="archive-secondary">{{ student.class_name || '未分班' }}</div>
                </td>
                <td class="archive-gpa-cell">{{ studentSummaryMap.get(student.id)?.gpaText || '--' }}</td>
                <td>{{ studentSummaryMap.get(student.id)?.courseCount ?? '--' }}</td>
                <td>
                  <span
                    class="archive-failed-count"
                    :class="{ 'has-failed': (studentSummaryMap.get(student.id)?.failedCount || 0) > 0 }"
                    :title="studentSummaryMap.get(student.id)?.failedCourseNames || '暂无已发布期末成绩记录'"
                  >
                    {{ studentSummaryMap.get(student.id)?.failedCount ?? '--' }}
                  </span>
                </td>
                <td>
                  <span class="archive-status-tag" :class="student.is_active === false ? 'archive-status-off' : 'archive-status-on'">
                    {{ student.is_active === false ? '非在籍' : '在籍' }}
                  </span>
                </td>
                <td>
                  <div class="archive-row-actions">
                    <button class="archive-link-btn" @click="openArchiveDetail(student)">详情</button>
                    <button class="archive-link-btn" @click="openEditStudent(student)">编辑</button>
                  </div>
                </td>
              </tr>
            </tbody>
            <tbody v-else>
              <tr>
                <td colspan="9" class="archive-empty-cell">
                  {{ archiveError ? '学生档案读取失败，请检查接口连接和登录权限。' : '当前筛选条件下暂无学生档案记录。' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="archive-pagination">
          <span>显示 {{ archivePageStart }}—{{ archivePageEnd }} 条，共 {{ archiveTotal }} 条</span>
          <div class="archive-pagination-controls">
            <button class="archive-page-btn" :disabled="archivePage <= 1" @click="archivePage--">上一页</button>
            <span>{{ archivePage }} / {{ archivePageCount }}</span>
            <button class="archive-page-btn" :disabled="archivePage >= archivePageCount" @click="archivePage++">下一页</button>
          </div>
        </div>

        <div class="archive-data-note">
          档案信息及成绩汇总来自教务数据库；GPA 按已发布期末成绩中的绩点与课程学分加权计算，未通过课程依据最新已发布期末成绩判断，无有效记录时显示“--”。
        </div>
      </div>
    </div>

    <!-- ========== 第3行：年级分布图 + 学业预警名单 ========== -->
    <div class="hub-row-2col">
      <!-- 3. 年级分布图 (ECharts 甜甜圈 + 嵌套饼图) -->
      <div id="module-grade-major-distribution" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
            年级与专业分布
          </span>
          <span class="hub-panel-badge">{{ filteredStudents.length.toLocaleString('zh-CN') }} 人</span>
        </div>
        <div class="hub-chart-wrap" ref="gradeChartRef"></div>
      </div>

      <!-- 4. 学业预警名单 -->
      <div id="module-academic-warning-list" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            学业预警名单
          </span>
          <span class="hub-panel-badge hover-tip" title="需重点关注的学生">
            <span class="warning-dot"></span>
            {{ warningCount }} 人
          </span>
        </div>
        <div class="warning-list" v-if="warningStudents.length">
          <div class="warning-item" v-for="(w, idx) in warningStudents" :key="w.id" :class="'severity-' + w.severity">
            <div class="warning-rank">{{ idx + 1 }}</div>
            <div class="warning-info">
              <span class="warning-name">{{ w.name }}</span>
              <span class="warning-college">{{ w.college }} · {{ w.grade }}</span>
            </div>
            <div class="warning-metrics">
              <div class="warning-metric-row">
                <span class="warning-m-label">GPA</span>
                <span class="warning-m-value danger-val">{{ w.gpa.toFixed(1) }}</span>
              </div>
              <div class="warning-metric-row">
                <span class="warning-m-label">挂科</span>
                <span class="warning-m-value" :class="w.failedCourses >= 3 ? 'danger-val' : 'warn-val'">{{ w.failedCourses }} 门</span>
              </div>
              <div class="warning-metric-row">
                <span class="warning-m-label">出勤</span>
                <span class="warning-m-value" :class="w.attendance < 70 ? 'danger-val' : 'warn-val'">{{ w.attendance }}%</span>
              </div>
            </div>
            <div class="warning-severity-tag" :class="'sev-' + w.severity">
              {{ w.severity === 'high' ? '高风险' : w.severity === 'mid' ? '中风险' : '关注' }}
            </div>
            <button class="warning-action-btn" @click="openStudentDetail(w.id)">跟进</button>
          </div>
        </div>
        <div v-else class="student-empty-state">当前筛选条件下暂无学业预警学生</div>
      </div>
    </div>

    <!-- ========== 第4行：就业趋势分析 + 学生活跃度热力图 ========== -->
    <div class="hub-row-2col">
      <!-- 5. 就业趋势分析 (ECharts) -->
      <div id="module-employment-further-study" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
            历届毕业生就业与深造趋势
          </span>
          <div class="trend-legend">
            <span class="legend-dot" style="background: #1E3A8A"></span>就业率
            <span class="legend-dot" style="background: #3B82F6"></span>深造率
            <span class="legend-dot" style="background: #60A5FA"></span>平均薪资
          </div>
        </div>
        <div class="hub-chart-wrap" ref="employmentChartRef"></div>
      </div>

      <!-- 6. 全院学生学业成绩与课程分析（替换原学生活跃度热力图） -->
      <div id="module-activity-heatmap" class="hub-panel academic-analysis-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <path d="M3 3v18h18"/>
              <path d="M7 14l4-4 3 3 6-7"/>
            </svg>
            全院学生学业成绩与课程分析
          </span>
          <span class="hub-panel-badge">{{ scoreSemesterLabel }}</span>
        </div>

        <div class="academic-filter-row">
          <label>
            <span>统计学期</span>
            <select v-model="scoreSemesterFilter">
              <option value="">全部学期</option>
              <option v-for="semester in semesterRecords" :key="semester.id" :value="String(semester.id)">
                {{ semester.name }}
              </option>
            </select>
          </label>
          <label>
            <span>专业</span>
            <select v-model="scoreMajorFilter">
              <option value="全部">全部专业</option>
              <option v-for="major in academicMajorOptions" :key="major" :value="major">{{ major }}</option>
            </select>
          </label>
          <label>
            <span>年级</span>
            <select v-model="scoreGradeFilter">
              <option value="全部">全部年级</option>
              <option v-for="grade in academicGradeOptions" :key="grade" :value="grade">{{ grade }}</option>
            </select>
          </label>
        </div>

        <div class="academic-kpi-grid">
          <div class="academic-kpi-card">
            <span class="academic-kpi-label">有正式成绩学生</span>
            <strong>{{ academicSummary.studentCount.toLocaleString('zh-CN') }}</strong>
          </div>
          <div class="academic-kpi-card">
            <span class="academic-kpi-label">涉及课程</span>
            <strong>{{ academicSummary.courseCount.toLocaleString('zh-CN') }}</strong>
          </div>
          <div class="academic-kpi-card">
            <span class="academic-kpi-label">有效成绩记录</span>
            <strong>{{ academicSummary.recordCount.toLocaleString('zh-CN') }}</strong>
          </div>
          <div class="academic-kpi-card">
            <span class="academic-kpi-label">成绩平均分</span>
            <strong>{{ academicSummary.averageScoreText }}</strong>
          </div>
        </div>

        <div v-if="academicLoading" class="academic-state-message">正在读取成绩记录…</div>
        <div v-else-if="academicError" class="academic-state-message academic-state-error">{{ academicError }}</div>

        <div class="academic-chart-grid">
          <div class="academic-chart-card">
            <div class="academic-chart-title">成绩区间分布</div>
            <div ref="scoreDistributionChartRef" class="academic-chart"></div>
          </div>
          <div class="academic-chart-card">
            <div class="academic-chart-title">各专业平均成绩</div>
            <div ref="majorScoreChartRef" class="academic-chart"></div>
          </div>
          <div class="academic-chart-card academic-chart-card-wide">
            <div class="academic-chart-title">各年级平均成绩</div>
            <div ref="gradeScoreChartRef" class="academic-chart academic-chart-short"></div>
          </div>
        </div>

        <div class="academic-course-section">
          <div class="academic-course-heading">
            <strong>课程成绩汇总</strong>
            <span>{{ courseScoreStats.length }} 门课程</span>
          </div>
          <div class="academic-course-table-wrap">
            <table class="academic-course-table">
              <thead>
                <tr>
                  <th>课程</th>
                  <th>成绩人数</th>
                  <th>平均分</th>
                  <th>最高分</th>
                  <th>最低分</th>
                  <th>未通过人数</th>
                  <th>及格率</th>
                </tr>
              </thead>
              <tbody v-if="courseScoreStats.length">
                <tr v-for="course in courseScoreStats" :key="course.courseId">
                  <td>
                    <div class="academic-course-name">{{ course.courseName }}</div>
                    <div class="archive-secondary">{{ course.courseCode || '无课程代码' }}</div>
                  </td>
                  <td>{{ course.studentCount }}</td>
                  <td class="academic-score-strong">{{ course.averageScore.toFixed(1) }}</td>
                  <td>{{ course.highestScore.toFixed(1) }}</td>
                  <td>{{ course.lowestScore.toFixed(1) }}</td>
                  <td><span :class="course.failedCount > 0 ? 'academic-low-rate' : ''">{{ course.failedCount }}</span></td>
                  <td>
                    <span :class="course.passRate >= 60 ? 'academic-pass-rate' : 'academic-low-rate'">
                      {{ course.passRate.toFixed(1) }}%
                    </span>
                  </td>
                </tr>
              </tbody>
              <tbody v-else>
                <tr><td colspan="7" class="archive-empty-cell">当前筛选条件下暂无已发布的期末成绩记录。</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="academicUnpublishedCount > 0" class="academic-unpublished-note">
          当前筛选范围内另有 {{ academicUnpublishedCount }} 条未发布成绩记录，未纳入正式成绩统计。
        </div>
        <div v-if="!academicLoading && !academicError && academicSummary.recordCount === 0" class="academic-data-note">
          当前筛选范围暂无已发布的期末成绩。系统不会使用模拟数据填充图表。
        </div>
      </div>

    </div>

    <!-- ========== 第5行：学生成长时间轴 + 优秀学生展示 ========== -->
    <div class="hub-row-2col">
      <!-- 7. 学生成长时间轴 -->
      <div id="module-student-growth-timeline" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            学生成长时间轴
          </span>
          <span class="hub-panel-badge">2026-2027学年</span>
        </div>
        <div class="timeline-wrap">
          <div class="timeline-item" v-for="(evt, idx) in growthTimeline" :key="idx" :class="{ 'timeline-active': evt.active }">
            <div class="timeline-marker">
              <div class="timeline-dot" :class="{ 'dot-active': evt.active, 'dot-done': evt.done }"></div>
              <div class="timeline-line" v-if="idx < growthTimeline.length - 1" :class="{ 'line-done': evt.done }"></div>
            </div>
            <div class="timeline-content">
              <div class="timeline-date">{{ evt.date }}</div>
              <div class="timeline-title">{{ evt.title }}</div>
              <div class="timeline-desc">{{ evt.desc }}</div>
              <div class="timeline-stats" v-if="evt.stats">
                <span class="timeline-stat" v-for="(v, k) in evt.stats" :key="k">{{ k }} <strong>{{ v }}</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 8. 优秀学生展示 (带荣誉徽章) -->
      <div id="module-honor-roll" class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/></svg>
            优秀学生荣誉榜
          </span>
          <span class="hub-panel-badge">TOP 6</span>
        </div>
        <div class="honor-grid">
          <div class="honor-card" v-for="(s, idx) in honorStudents" :key="s.id" :class="'honor-rank-' + (idx + 1)" @click="openStudentDetail(s.id)">
            <div class="honor-badge-wrap">
              <div class="honor-badge" :class="'badge-' + (idx + 1)">
                <svg v-if="idx === 0" viewBox="0 0 24 24" fill="currentColor" stroke="none" class="honor-crown"><path d="M5 16L3 5l5.5 5L12 4l3.5 6L21 5l-2 11H5zm14 3v2H5v-2h14z"/></svg>
                <span v-else class="honor-num">{{ idx + 1 }}</span>
              </div>
            </div>
            <div class="honor-avatar" :style="{ background: s.avatarBg }">{{ s.name.charAt(0) }}</div>
            <h4 class="honor-name">{{ s.name }}</h4>
            <p class="honor-college">{{ s.college }}</p>
            <div class="honor-highlight">
              <span class="honor-gpa">GPA {{ s.gpa.toFixed(1) }}</span>
              <span class="honor-award">{{ s.award }}</span>
            </div>
            <div class="honor-tags">
              <span class="honor-tag" v-for="tag in s.honorTags" :key="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 第6行：班级数据对比 ========== -->
    <div class="hub-panel">
      <div class="hub-panel-header">
        <span class="hub-panel-title">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          班级数据对比
        </span>
        <span class="hub-panel-badge">{{ classComparison.length }} 个班级</span>
      </div>
      <div class="class-compare-scroll" >
        <table class="class-compare-table">
          <thead>
            <tr>
              <th>班级</th>
              <th>人数</th>
              <th>平均 GPA</th>
              <th>优秀率</th>
              <th>预警人数</th>
              <th>四六级通过</th>
              <th>竞赛获奖</th>
              <th>综合排名</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(c, idx) in classComparison" :key="c.name" :class="{ 'top-row': idx === 0 }">
              <td class="class-name-cell">
                <span class="class-rank-dot" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span>
                {{ c.name }}
              </td>
              <td>{{ c.students }}</td>
              <td>
                <span class="compare-gpa" :class="gpaColorClass(c.avgGpa)">{{ c.avgGpa.toFixed(2) }}</span>
              </td>
              <td>
                <div class="compare-bar-mini">
                  <div class="compare-bar-fill" :style="{ width: c.excellentRate + '%', background: c.excellentRate >= 30 ? '#1E3A8A' : c.excellentRate >= 20 ? '#3B82F6' : '#93C5FD' }"></div>
                </div>
                <span class="compare-pct">{{ c.excellentRate }}%</span>
              </td>
              <td>
                <span class="compare-warn" :class="{ 'has-warning': c.warningCount > 0 }">{{ c.warningCount }}</span>
              </td>
              <td>
                <div class="compare-bar-mini">
                  <div class="compare-bar-fill" :style="{ width: c.cetPassRate + '%', background: c.cetPassRate >= 80 ? '#1E3A8A' : c.cetPassRate >= 60 ? '#3B82F6' : '#93C5FD' }"></div>
                </div>
                <span class="compare-pct">{{ c.cetPassRate }}%</span>
              </td>
              <td><span class="compare-award-num">{{ c.competitionAwards }}</span></td>
              <td>
                <span class="compare-rank-badge" :class="'overall-' + (idx <= 2 ? 'top' : 'normal')">#{{ idx + 1 }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ========== 10. 学生详情抽屉 ========== -->
    <Teleport to="body">
      <div class="drawer-overlay" v-if="drawerVisible" @click.self="closeDrawer">
        <div class="drawer-panel" :class="{ 'drawer-open': drawerVisible }">
          <div class="drawer-header">
            <div class="drawer-header-top">
              <div class="drawer-avatar-lg" :style="{ background: detailStudent?.avatarBg || '#1E3A8A' }">
                {{ detailStudent?.name?.charAt(0) || '?' }}
              </div>
              <div class="drawer-title-area">
                <h3 class="drawer-name">{{ detailStudent?.name }}</h3>
                <p class="drawer-id">{{ detailStudent?.code }}</p>
                <div class="drawer-status-row">
                  <span class="drawer-status-tag" :class="statusClass(detailStudent?.status || '')">{{ detailStudent?.status }}</span>
                  <span class="drawer-risk-tag" :class="'risk-' + (detailStudent?.riskLevel || 'low')" v-if="detailStudent?.riskLevel">{{ riskLabel(detailStudent?.riskLevel || 'low') }}</span>
                </div>
              </div>
              <button class="drawer-close-btn" @click="closeDrawer">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>
          <div class="drawer-body">
            <div class="drawer-section">
              <h4 class="drawer-section-title">基本信息</h4>
              <div class="drawer-info-grid">
                <div class="drawer-info-item"><span class="di-label">学院</span><span class="di-value">{{ detailStudent?.college }}</span></div>
                <div class="drawer-info-item"><span class="di-label">专业</span><span class="di-value">{{ detailStudent?.major }}</span></div>
                <div class="drawer-info-item"><span class="di-label">年级</span><span class="di-value">{{ detailStudent?.grade }}</span></div>
                <div class="drawer-info-item"><span class="di-label">班级</span><span class="di-value">{{ detailStudent?.className || '未分配' }}</span></div>
                <div class="drawer-info-item"><span class="di-label">培养学制</span><span class="di-value">{{ detailStudent?.studyLength || '-' }}</span></div>
                <div class="drawer-info-item"><span class="di-label">手机</span><span class="di-value">{{ detailStudent?.phone || '-' }}</span></div>
              </div>
            </div>
            <div class="drawer-section">
              <h4 class="drawer-section-title">学业数据</h4>
              <div class="drawer-metrics-row">
                <div class="drawer-metric-card">
                  <span class="dm-label">GPA</span>
                  <span class="dm-value" :class="gpaColorClass(detailStudent?.gpa || 0)">{{ detailStudent?.gpa?.toFixed(1) }}</span>
                </div>
                <div class="drawer-metric-card">
                  <span class="dm-label">已修学分</span>
                  <span class="dm-value">{{ detailStudent?.credits }}/{{ detailStudent?.totalCredits }}</span>
                </div>
                <div class="drawer-metric-card">
                  <span class="dm-label">挂科数</span>
                  <span class="dm-value" :class="(detailStudent?.failedCourses || 0) > 0 ? 'danger-val' : ''">{{ detailStudent?.failedCourses || 0 }}</span>
                </div>
                <div class="drawer-metric-card">
                  <span class="dm-label">出勤率</span>
                  <span class="dm-value">{{ detailStudent?.attendance || '-' }}{{ detailStudent?.attendance ? '%' : '' }}</span>
                </div>
              </div>
            </div>
            <div class="drawer-section" v-if="detailStudent?.tags && detailStudent.tags.length">
              <h4 class="drawer-section-title">能力标签</h4>
              <div class="drawer-tags-wrap">
                <span class="profile-tag" v-for="tag in detailStudent.tags" :key="tag" :style="tagStyle(tag)">{{ tag }}</span>
              </div>
            </div>
            <div class="drawer-section">
              <h4 class="drawer-section-title">成长记录</h4>
              <div class="drawer-timeline-mini">
                <div class="dtm-item" v-for="rec in studentGrowthRecords" :key="rec.date">
                  <div class="dtm-dot"></div>
                  <div class="dtm-content">
                    <span class="dtm-date">{{ rec.date }}</span>
                    <span class="dtm-text">{{ rec.text }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="drawer-footer">
            <button class="btn-outline">导出档案</button>
            <button class="btn-primary">编辑信息</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ========== 学生档案新增 / 编辑对话框 ========== -->
    <Teleport to="body">
      <div v-if="studentDialogVisible" class="archive-dialog-overlay" @click.self="closeStudentDialog">
        <div class="archive-dialog archive-dialog-wide">
          <div class="archive-dialog-header">
            <div>
              <h3>{{ studentDialogMode === 'create' ? '新增学生档案' : '编辑学生档案' }}</h3>
              <p>档案保存至教务数据库，学号必须唯一。</p>
            </div>
            <button class="archive-dialog-close" type="button" @click="closeStudentDialog">×</button>
          </div>
          <form @submit.prevent="submitStudentForm">
            <div class="archive-form-grid">
              <label class="archive-form-field">
                <span>学号 <em>*</em></span>
                <input v-model.trim="studentForm.student_no" required maxlength="40" placeholder="请输入学号">
              </label>
              <label class="archive-form-field">
                <span>姓名 <em>*</em></span>
                <input v-model.trim="studentForm.name" required maxlength="80" placeholder="请输入学生姓名">
              </label>
              <label class="archive-form-field">
                <span>性别</span>
                <select v-model="studentForm.gender">
                  <option value="男">男</option>
                  <option value="女">女</option>
                  <option value="未说明">未说明</option>
                </select>
              </label>
              <label class="archive-form-field">
                <span>所属专业 <em>*</em></span>
                <select v-model="studentForm.major" required>
                  <option value="" disabled>请选择专业</option>
                  <option v-for="major in formMajorOptions" :key="major" :value="major">{{ major }}</option>
                </select>
              </label>
              <label class="archive-form-field">
                <span>年级 <em>*</em></span>
                <select v-model="studentForm.grade" required>
                  <option value="" disabled>请选择年级</option>
                  <option v-for="grade in formGradeOptions" :key="grade" :value="grade">{{ grade }}</option>
                </select>
              </label>
              <label class="archive-form-field">
                <span>班级</span>
                <input v-model.trim="studentForm.class_name" maxlength="60" placeholder="例如：23行管班">
              </label>
              <label class="archive-form-field">
                <span>入学年份 <em>*</em></span>
                <input v-model.number="studentForm.enrollment_year" type="number" min="2000" max="2100" required>
              </label>
              <label class="archive-form-field">
                <span>联系电话</span>
                <input v-model.trim="studentForm.phone" maxlength="30" placeholder="请输入联系电话">
              </label>
              <label class="archive-form-field">
                <span>电子邮箱</span>
                <input v-model.trim="studentForm.email" type="email" maxlength="254" placeholder="请输入电子邮箱">
              </label>
              <label class="archive-form-field archive-checkbox-field">
                <input v-model="studentForm.is_active" type="checkbox">
                <span>在籍学生</span>
              </label>
            </div>
            <div class="archive-dialog-footer">
              <span class="archive-form-required">* 为必填字段</span>
              <div>
                <button class="btn-outline" type="button" @click="closeStudentDialog">取消</button>
                <button class="btn-primary" type="submit" :disabled="studentSaving">
                  {{ studentSaving ? '正在保存…' : '保存档案' }}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <!-- ========== 学生档案详情对话框 ========== -->
    <Teleport to="body">
      <div v-if="archiveDetailVisible && archiveDetailStudent" class="archive-dialog-overlay" @click.self="closeArchiveDetail">
        <div class="archive-dialog archive-dialog-detail">
          <div class="archive-dialog-header">
            <div>
              <h3>{{ archiveDetailStudent.name }} · 学生档案</h3>
              <p>{{ archiveDetailStudent.student_no }} · {{ archiveDetailStudent.major }} · {{ archiveDetailStudent.grade }}</p>
            </div>
            <button class="archive-dialog-close" type="button" @click="closeArchiveDetail">×</button>
          </div>
          <div class="archive-detail-section">
            <h4>基本信息</h4>
            <div class="archive-detail-grid">
              <div><span>所属学院</span><strong>{{ archiveDetailStudent.college_name || archiveCollegeName }}</strong></div>
              <div><span>专业</span><strong>{{ archiveDetailStudent.major || '--' }}</strong></div>
              <div><span>年级 / 班级</span><strong>{{ archiveDetailStudent.grade || '--' }} / {{ archiveDetailStudent.class_name || '--' }}</strong></div>
              <div><span>性别</span><strong>{{ archiveDetailStudent.gender || '未说明' }}</strong></div>
              <div><span>入学年份</span><strong>{{ archiveDetailStudent.enrollment_year || '--' }}</strong></div>
              <div><span>学籍状态</span><strong>{{ archiveDetailStudent.is_active === false ? '非在籍' : '在籍' }}</strong></div>
              <div><span>联系电话</span><strong>{{ archiveDetailStudent.phone || '--' }}</strong></div>
              <div><span>电子邮箱</span><strong>{{ archiveDetailStudent.email || '--' }}</strong></div>
            </div>
          </div>
          <div class="archive-detail-section">
            <h4>学业汇总 <small>仅根据已发布的期末成绩计算</small></h4>
            <div class="archive-detail-kpis">
              <div><span>平均 GPA</span><strong>{{ archiveDetailSummary?.gpaText || '--' }}</strong></div>
              <div><span>已修课程</span><strong>{{ archiveDetailSummary?.courseCount ?? '--' }}</strong></div>
              <div><span>未通过课程</span><strong>{{ archiveDetailSummary?.failedCount ?? '--' }}</strong></div>
            </div>
            <p v-if="archiveDetailSummary?.failedCourseNames" class="archive-failed-course-list">
              未通过课程：{{ archiveDetailSummary.failedCourseNames }}
            </p>
          </div>
          <div class="archive-detail-section">
            <h4>课程成绩明细 <small>未发布成绩会单独标记，不纳入正式统计</small></h4>
            <div class="archive-detail-table-wrap">
              <table class="archive-table archive-detail-table">
                <thead>
                  <tr><th>学期</th><th>课程</th><th>考核类型</th><th>成绩</th><th>绩点</th><th>发布状态</th></tr>
                </thead>
                <tbody v-if="archiveDetailGrades.length">
                  <tr v-for="grade in archiveDetailGrades" :key="grade.id">
                    <td>{{ grade.semester_name || '--' }}</td>
                    <td>{{ grade.course_name || '--' }}</td>
                    <td>{{ grade.exam_type || '--' }}</td>
                    <td>{{ Number(grade.score).toFixed(1) }}</td>
                    <td>{{ grade.grade_point === null || grade.grade_point === undefined ? '--' : Number(grade.grade_point).toFixed(2) }}</td>
                    <td><span class="archive-status-tag" :class="grade.is_published ? 'archive-status-on' : 'archive-status-off'">{{ grade.is_published ? '已发布' : '未发布' }}</span></td>
                  </tr>
                </tbody>
                <tbody v-else><tr><td colspan="6" class="archive-empty-cell">暂无成绩记录</td></tr></tbody>
              </table>
            </div>
          </div>
          <div class="archive-dialog-footer">
            <span class="archive-form-required">成绩明细以教务系统记录为准</span>
            <div>
              <button class="btn-outline" type="button" @click="closeArchiveDetail">关闭</button>
              <button class="btn-primary" type="button" @click="editArchiveDetailStudent">编辑档案</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ========== Excel 导入预览对话框 ========== -->
    <Teleport to="body">
      <div v-if="importPreview" class="archive-dialog-overlay" @click.self="closeImportPreview">
        <div class="archive-dialog archive-dialog-wide">
          <div class="archive-dialog-header">
            <div>
              <h3>{{ importResultText ? 'Excel 导入结果' : 'Excel 导入预览' }}</h3>
              <p>{{ importResultText || '请先核对新增、更新及成绩明细数量，确认后才会写入数据库。' }}</p>
            </div>
            <button class="archive-dialog-close" type="button" @click="closeImportPreview">×</button>
          </div>
          <div class="archive-import-summary">
            <div><span>新增学生</span><strong>{{ importPreview.studentRows.filter(row => row.action === 'create').length }}</strong></div>
            <div><span>更新档案</span><strong>{{ importPreview.studentRows.filter(row => row.action === 'update').length }}</strong></div>
            <div><span>新增成绩</span><strong>{{ importPreview.gradeRows.filter(row => row.action === 'create').length }}</strong></div>
            <div><span>更新未发布成绩</span><strong>{{ importPreview.gradeRows.filter(row => row.action === 'update').length }}</strong></div>
          </div>
          <div v-if="importPreview.errors.length" class="archive-import-errors">
            <h4>未通过校验的记录（{{ importPreview.errors.length }}）</h4>
            <ul>
              <li v-for="(error, index) in importPreview.errors.slice(0, 12)" :key="index">{{ error }}</li>
            </ul>
            <p v-if="importPreview.errors.length > 12">另有 {{ importPreview.errors.length - 12 }} 条问题未展开，请修正 Excel 后重新导入。</p>
          </div>
          <div class="archive-import-note">
            成绩导入后默认保持“未发布”状态，不会自动向学生公布；已发布成绩不会通过本功能覆盖。
          </div>
          <div class="archive-dialog-footer">
            <span class="archive-form-required">有效记录可以先导入；异常记录不会写入。</span>
            <div>
              <button class="btn-outline" type="button" @click="closeImportPreview">取消</button>
              <button
                v-if="importPreview.studentRows.length + importPreview.gradeRows.length > 0"
                class="btn-primary"
                type="button"
                :disabled="isImporting"
                @click="confirmArchiveImport"
              >
                {{ isImporting ? '正在导入…' : '确认导入有效记录' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import * as XLSX from 'xlsx'
import { ElMessage } from 'element-plus'
import { getStudents, createStudent, updateStudent, type StudentItem } from '../../api/student'
import { getGrades, createGrade, updateGrade, type GradeItem } from '../../api/grade'
import { getCourses, type CourseItem } from '../../api/course'
import { getColleges, getSemesters, type CollegeItem, type SemesterItem } from '../../api/dashboard'

type RiskLevel = 'low' | 'mid' | 'high'

interface StudentRecord {
  id: number
  code: string
  name: string
  college: string
  grade: string
  major: string
  gpa: number
  credits: number
  totalCredits: number
  status: string
  riskLevel: RiskLevel
  severity: RiskLevel
  tags: string[]
  profileGradient: string
  avatarBg: string
  className: string
  phone: string
  failedCourses: number
  attendance: number
  scholarship: boolean
  award: string
  honorTags: string[]
  cetPassed: boolean
  competitionAwards: number
  studyLength: string
}

interface GrowthRecord {
  studentId: number
  date: string
  text: string
}

type ApiStudent = StudentItem & { is_active?: boolean }
type ApiGrade = GradeItem & { is_published?: boolean; exam?: number | null; exam_name?: string }
type ApiCourse = CourseItem & { is_active?: boolean }
type ApiCollege = CollegeItem
type ApiSemester = SemesterItem & {
  academic_year?: string | number
  term?: string | number
  is_current?: boolean
}

interface StudentPayload {
  student_no: string
  name: string
  gender: string
  college: number
  major: string
  grade: string
  class_name: string
  email: string
  phone: string
  enrollment_year: number
  is_active: boolean
}

interface StudentForm {
  id?: number
  student_no: string
  name: string
  gender: string
  major: string
  grade: string
  class_name: string
  email: string
  phone: string
  enrollment_year: number
  is_active: boolean
}

interface StudentAcademicSummary {
  gpaText: string
  gpa: number | null
  courseCount: number | null
  failedCount: number | null
  failedCourseNames: string
}

interface GradePayload {
  student: number
  course: number
  semester: number
  exam: number | null
  score: number
  grade_point: number | null
  exam_type: string
  exam_date: string | null
  remark: string
  is_published: boolean
}

interface ImportStudentRow {
  rowNo: number
  studentNo: string
  action: 'create' | 'update'
  existingId?: number
  payload: StudentPayload
}

interface ImportGradeRow {
  rowNo: number
  studentNo: string
  action: 'create' | 'update'
  existingId?: number
  payload: Omit<GradePayload, 'student'>
}

interface ArchiveImportPreview {
  studentRows: ImportStudentRow[]
  gradeRows: ImportGradeRow[]
  errors: string[]
}

// ========== 1. 筛选条件与培养方案约束 ==========
const GRADE_VALUES = ['2026级', '2025级', '2024级', '2023级', '2022级']
const MAJORS = [
  '行政管理',
  '政治学与行政学',
  '国际政治',
  '行政管理+电子科学与技术双学位',
  '科学社会主义',
  '国际政治＋英语双学位',
]
const DOUBLE_DEGREE_MAJORS = [
  '行政管理+电子科学与技术双学位',
  '国际政治＋英语双学位',
]
const MAJOR_COLORS = ['#1E3A8A', '#2563EB', '#60A5FA', '#93C5FD', '#BFDBFE', '#DBEAFE']
const GRADE_COLORS = ['#1E3A8A', '#2563EB', '#3B82F6', '#60A5FA', '#93C5FD']

const currentGrade = ref('全部')
const currentMajor = ref('全部')
const drawerVisible = ref(false)
const detailStudent = ref<StudentRecord | null>(null)
const gradeChartRef = ref<HTMLElement | null>(null)
const employmentChartRef = ref<HTMLElement | null>(null)
const scoreDistributionChartRef = ref<HTMLElement | null>(null)
const majorScoreChartRef = ref<HTMLElement | null>(null)
const gradeScoreChartRef = ref<HTMLElement | null>(null)

let gradeChart: echarts.ECharts | null = null
let employmentChart: echarts.ECharts | null = null
let scoreDistributionChart: echarts.ECharts | null = null
let majorScoreChart: echarts.ECharts | null = null
let gradeScoreChart: echarts.ECharts | null = null

const gradeOptions = computed(() => {
  const allowedGrades = currentMajor.value !== '全部' && !DOUBLE_DEGREE_MAJORS.includes(currentMajor.value)
    ? GRADE_VALUES.filter(grade => grade !== '2022级')
    : GRADE_VALUES
  return ['全部', ...allowedGrades]
})

const majorOptions = computed(() => {
  const allowedMajors = currentGrade.value === '2022级' ? DOUBLE_DEGREE_MAJORS : MAJORS
  return ['全部', ...allowedMajors]
})

watch(currentGrade, (grade) => {
  if (grade === '2022级' && currentMajor.value !== '全部' && !DOUBLE_DEGREE_MAJORS.includes(currentMajor.value)) {
    currentMajor.value = '全部'
  }
})

watch(currentMajor, (major) => {
  if (major !== '全部' && !DOUBLE_DEGREE_MAJORS.includes(major) && currentGrade.value === '2022级') {
    currentGrade.value = '全部'
  }
})

// ========== 2. 统一学生主数据（演示数据底表） ==========
// 所有统计卡片、学生画像、年级/专业分布、预警名单、荣誉榜和班级对比均由该底表聚合。
// 2022级仅包含两个五年制双学位专业；其余四个专业从2023级开始。
// 26个行政班，总人数严格为600人；每个“年级 × 专业”仅对应一个班级。
// 四个普通专业覆盖2023—2026级；两个五年制双学位专业覆盖2022—2026级。
// 各班人数均控制在10—40人之间。
const COHORT_MAJOR_COUNTS: Record<string, Record<string, number>> = {
  '2026级': {
    '行政管理': 28,
    '政治学与行政学': 27,
    '国际政治': 24,
    '行政管理+电子科学与技术双学位': 20,
    '科学社会主义': 22,
    '国际政治＋英语双学位': 20,
  },
  '2025级': {
    '行政管理': 27,
    '政治学与行政学': 26,
    '国际政治': 24,
    '行政管理+电子科学与技术双学位': 19,
    '科学社会主义': 21,
    '国际政治＋英语双学位': 19,
  },
  '2024级': {
    '行政管理': 26,
    '政治学与行政学': 25,
    '国际政治': 23,
    '行政管理+电子科学与技术双学位': 19,
    '科学社会主义': 20,
    '国际政治＋英语双学位': 19,
  },
  '2023级': {
    '行政管理': 25,
    '政治学与行政学': 24,
    '国际政治': 22,
    '行政管理+电子科学与技术双学位': 18,
    '科学社会主义': 20,
    '国际政治＋英语双学位': 18,
  },
  '2022级': {
    '行政管理+电子科学与技术双学位': 33,
    '国际政治＋英语双学位': 31,
  },
}

const FAMILY_NAMES = [
  '张', '李', '王', '刘', '陈', '杨', '赵', '黄', '周', '吴',
  '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗',
  '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧',
  '程', '曹', '袁', '邓', '许', '傅', '沈', '曾', '彭', '吕',
]
const GIVEN_NAME_CHARS = [
  '知', '行', '文', '澜', '思', '齐', '子', '恒', '清', '源',
  '远', '航', '语', '晴', '明', '哲', '嘉', '宁', '亦', '安',
  '书', '瑶', '景', '然', '星', '辰', '若', '溪', '承', '宇',
  '可', '欣', '致', '昕', '一', '诺', '佳', '乐', '启', '妍',
]
const FEATURED_NAMES: Record<string, string> = {
  '2023级|政治学与行政学|1': '张知行',
  '2023级|行政管理|1': '李文澜',
  '2024级|国际政治|1': '陈思齐',
  '2023级|国际政治|1': '周子恒',
  '2024级|国际政治＋英语双学位|1': '林清源',
  '2023级|行政管理|2': '吴思远',
  '2023级|科学社会主义|1': '赵远航',
  '2023级|行政管理+电子科学与技术双学位|1': '孙语晴',
}
const MAJOR_META: Record<string, { prefix: string; baseGpa: number; totalCredits: number; studyLength: string }> = {
  '行政管理': { prefix: '行管', baseGpa: 3.28, totalCredits: 160, studyLength: '四年制本科' },
  '政治学与行政学': { prefix: '政行', baseGpa: 3.25, totalCredits: 160, studyLength: '四年制本科' },
  '国际政治': { prefix: '国政', baseGpa: 3.22, totalCredits: 160, studyLength: '四年制本科' },
  // “公信班” = 行政管理 + 电子科学与技术（电子信息方向）双学位班
  '行政管理+电子科学与技术双学位': { prefix: '公信', baseGpa: 3.31, totalCredits: 180, studyLength: '五年制双学位' },
  '科学社会主义': { prefix: '科社', baseGpa: 3.18, totalCredits: 160, studyLength: '四年制本科' },
  '国际政治＋英语双学位': { prefix: '国英', baseGpa: 3.35, totalCredits: 180, studyLength: '五年制双学位' },
}
const PROFILE_GRADIENTS = [
  'linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%)',
  'linear-gradient(135deg, #1E40AF 0%, #60A5FA 100%)',
  'linear-gradient(135deg, #2563EB 0%, #93C5FD 100%)',
  'linear-gradient(135deg, #0F766E 0%, #5EEAD4 100%)',
  'linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%)',
  'linear-gradient(135deg, #D97706 0%, #F59E0B 100%)',
]
const AVATAR_COLORS = ['#1E3A8A', '#1E40AF', '#2563EB', '#0F766E', '#7C3AED', '#D97706']

const RESERVED_FEATURED_NAMES = new Set(Object.values(FEATURED_NAMES))

function makeStudentName(serial: number, usedNames: Set<string>): string {
  let candidateSerial = serial
  let candidate = ''
  do {
    const index = candidateSerial - 1
    const surname = FAMILY_NAMES[index % FAMILY_NAMES.length] || '张'
    const givenIndex = Math.floor(index / FAMILY_NAMES.length)
    const first = GIVEN_NAME_CHARS[Math.floor(givenIndex / GIVEN_NAME_CHARS.length) % GIVEN_NAME_CHARS.length] || '知'
    const second = GIVEN_NAME_CHARS[givenIndex % GIVEN_NAME_CHARS.length] || '行'
    candidate = `${surname}${first}${second}`
    candidateSerial += 1
  } while (RESERVED_FEATURED_NAMES.has(candidate) || usedNames.has(candidate))
  return candidate
}

function buildStudentRecords(): StudentRecord[] {
  const records: StudentRecord[] = []
  const gradeSerials: Record<string, number> = {}
  const usedStudentNames = new Set<string>()

  for (const grade of [...GRADE_VALUES].reverse()) {
    const year = Number(grade.slice(0, 4))
    const gradeMajorCounts = COHORT_MAJOR_COUNTS[grade] || {}

    for (const [majorIndex, major] of MAJORS.entries()) {
      const count = gradeMajorCounts[major] || 0
      if (!count) continue

      const meta = MAJOR_META[major]
      if (!meta) continue
      for (let index = 1; index <= count; index++) {
        const serial = (gradeSerials[grade] || 0) + 1
        gradeSerials[grade] = serial
        const id = records.length + 1
        const seed = (serial * 37 + year * 13 + majorIndex * 71) % 997
        const gpaWave = ((seed % 81) - 40) / 100
        const cohortAdjustment = grade === '2022级' ? 0.04 : grade === '2026级' ? -0.04 : 0
        const gpa = Math.max(1.6, Math.min(4, Number((meta.baseGpa + gpaWave + cohortAdjustment).toFixed(2))))
        const failedCourses = seed % 37 === 0 ? 5 : seed % 19 === 0 ? 3 : seed % 11 === 0 ? 2 : seed % 7 === 0 ? 1 : 0
        const attendance = 68 + ((seed * 17) % 33)
        const riskLevel: RiskLevel = gpa < 2.3 || failedCourses >= 5 || attendance < 62
          ? 'high'
          : gpa < 2.75 || failedCourses >= 3 || attendance < 70
            ? 'mid'
            : 'low'
        const scholarship = gpa >= 3.3 && seed % 3 === 0
        const award = scholarship
          ? (seed % 3 === 0 ? '国家奖学金' : seed % 3 === 1 ? '国家励志奖学金' : '校级奖学金')
          : '学业优秀'
        const tags: string[] = []
        if (scholarship) tags.push(award)
        if (seed % 9 === 0) tags.push('专业竞赛')
        if (seed % 13 === 0) tags.push('科研实践')
        if (riskLevel === 'high') tags.push('重点帮扶', '学业预警')
        else if (riskLevel === 'mid') tags.push('学业指导')
        if (!tags.length) tags.push('专业学习')

        // 政管学院当前规则：同一年级、同一专业仅设置一个行政班。
        // 班名统一使用“年级后两位 + 专业简称 + 班”，如：23公信班、24国政班、25政行班。
        const className = `${String(year).slice(-2)}${meta.prefix}班`
        const credits = Math.min(
          meta.totalCredits,
          20 + (2026 - year) * 32 + (seed % 28),
        )
        const status = riskLevel === 'high'
          ? (failedCourses >= 5 ? '留级' : '警告')
          : riskLevel === 'mid' && attendance < 72
            ? '休学'
            : '在读'
        const featuredKey = `${grade}|${major}|${index}`
        let name = FEATURED_NAMES[featuredKey] || makeStudentName(id, usedStudentNames)
        if (usedStudentNames.has(name)) name = `${name}${id}`
        usedStudentNames.add(name)
        const phoneTail = String((seed * 7919) % 10000).padStart(4, '0')

        records.push({
          id,
          code: `S${year}${String(serial).padStart(4, '0')}`,
          name,
          college: '政治学与公共管理学院',
          grade,
          major,
          gpa,
          credits,
          totalCredits: meta.totalCredits,
          status,
          riskLevel,
          severity: riskLevel,
          tags,
          profileGradient: PROFILE_GRADIENTS[(seed + majorIndex) % PROFILE_GRADIENTS.length] || PROFILE_GRADIENTS[0] || '',
          avatarBg: AVATAR_COLORS[(seed + majorIndex) % AVATAR_COLORS.length] || '#1E3A8A',
          className,
          phone: `13${String(seed % 100).padStart(2, '0')}****${phoneTail}`,
          failedCourses,
          attendance,
          scholarship,
          award,
          honorTags: [seed % 2 === 0 ? '专业竞赛' : '科研实践', seed % 3 === 0 ? '综合测评优秀' : '学业表现突出'],
          cetPassed: seed % 100 < 82 + (majorIndex % 3) * 3,
          competitionAwards: seed % 8 === 0 ? 2 : seed % 5 === 0 ? 1 : 0,
          studyLength: meta.studyLength,
        })
      }
    }
  }

  return records
}

const studentRecords = buildStudentRecords()
const studentById = new Map<number, StudentRecord>(studentRecords.map(student => [student.id, student]))


// ========== 新增：真实学生档案与成绩数据（仅供本次替换的两个模块使用） ==========
const ARCHIVE_COLLEGE_KEYWORD = '政治学与公共管理学院'
const ARCHIVE_PAGE_SIZE = 10
const archiveLoading = ref(false)
const academicLoading = ref(false)
const archiveError = ref('')
const academicError = ref('')
const archiveCollegeId = ref<number | null>(null)
const archiveCollegeName = ref(ARCHIVE_COLLEGE_KEYWORD)
const allStudentRecords = ref<ApiStudent[]>([])
const archiveStudents = ref<ApiStudent[]>([])
const gradeRecords = ref<ApiGrade[]>([])
const courseRecords = ref<ApiCourse[]>([])
const semesterRecords = ref<ApiSemester[]>([])
const collegeRecords = ref<ApiCollege[]>([])

const archiveGradeFilter = ref('全部')
const archiveMajorFilter = ref('全部')
const archiveClassFilter = ref('全部')
const archiveStatusFilter = ref('全部')
const archiveSearch = ref('')
const archivePage = ref(1)

const archiveImportInputRef = ref<HTMLInputElement | null>(null)
const studentDialogVisible = ref(false)
const studentDialogMode = ref<'create' | 'edit'>('create')
const studentSaving = ref(false)
const studentForm = ref<StudentForm>(createEmptyStudentForm())
const archiveDetailVisible = ref(false)
const archiveDetailStudent = ref<ApiStudent | null>(null)
const importPreview = ref<ArchiveImportPreview | null>(null)
const importResultText = ref('')
const isImporting = ref(false)

const scoreSemesterFilter = ref('')
const scoreMajorFilter = ref('全部')
const scoreGradeFilter = ref('全部')

function createEmptyStudentForm(): StudentForm {
  const year = new Date().getFullYear()
  return {
    student_no: '',
    name: '',
    gender: '未说明',
    major: '',
    grade: '',
    class_name: '',
    email: '',
    phone: '',
    enrollment_year: year,
    is_active: true,
  }
}

function getApiErrorMessage(error: unknown): string {
  const err = error as {
    response?: { data?: { detail?: string; message?: string } }
    message?: string
  }
  return err?.response?.data?.detail
    || err?.response?.data?.message
    || err?.message
    || '请求失败，请检查网络连接和接口权限。'
}

async function fetchAllPages<T>(
  fetchPage: (params: { page: number; page_size: number }) => Promise<{ count: number; results: T[] }>,
): Promise<T[]> {
  const collected: T[] = []
  let page = 1
  let total = Number.POSITIVE_INFINITY

  while (collected.length < total && page <= 300) {
    const response = await fetchPage({ page, page_size: 100 })
    const rows = Array.isArray(response?.results) ? response.results : []
    total = Number(response?.count ?? (collected.length + rows.length))
    if (!rows.length) break
    collected.push(...rows)
    page += 1
  }

  return collected
}

async function runInBatches<T>(
  items: T[],
  batchSize: number,
  worker: (item: T) => Promise<void>,
): Promise<void> {
  for (let index = 0; index < items.length; index += batchSize) {
    const batch = items.slice(index, index + batchSize)
    await Promise.all(batch.map(worker))
  }
}

function isFinalGradeType(value: unknown): boolean {
  const type = String(value || '').trim().toLowerCase()
  return type === 'final'
    || type.includes('期末')
    || type.includes('最终成绩')
    || type.includes('final')
}

function semesterOrder(grade: ApiGrade): number {
  const name = String(grade.semester_name || '')
  const numbers = name.match(/\d+/g)?.map(Number) || []
  if (numbers.length >= 3) return (numbers[0] ?? 0) * 1000000 + (numbers[1] ?? 0) * 1000 + (numbers[2] ?? 0)
  if (numbers.length >= 2) return (numbers[0] ?? 0) * 1000 + (numbers[1] ?? 0)
  return Number(grade.semester || 0)
}

function isNewerGrade(candidate: ApiGrade, current: ApiGrade): boolean {
  return semesterOrder(candidate) >= semesterOrder(current)
}

function latestFinalGradeRows(records: ApiGrade[]): ApiGrade[] {
  const latest = new Map<string, ApiGrade>()
  for (const grade of records) {
    const key = `${Number(grade.student)}|${Number(grade.course)}|${Number(grade.semester || 0)}`
    const previous = latest.get(key)
    if (!previous || isNewerGrade(grade, previous)) latest.set(key, grade)
  }
  return [...latest.values()]
}

const courseById = computed(() => new Map<number, ApiCourse>(
  courseRecords.value.map(course => [Number(course.id), course]),
))

const studentSummaryMap = computed(() => {
  const gradesByStudent = new Map<number, ApiGrade[]>()
  for (const grade of gradeRecords.value) {
    const studentId = Number(grade.student)
    if (!studentId || grade.is_published !== true || !isFinalGradeType(grade.exam_type)) continue
    const list = gradesByStudent.get(studentId) || []
    list.push(grade)
    gradesByStudent.set(studentId, list)
  }

  const summaries = new Map<number, StudentAcademicSummary>()
  for (const student of archiveStudents.value) {
    const studentGrades = gradesByStudent.get(Number(student.id)) || []
    const latestByCourse = new Map<number, ApiGrade>()

    for (const grade of studentGrades) {
      const courseId = Number(grade.course)
      if (!courseId) continue
      const previous = latestByCourse.get(courseId)
      if (!previous || isNewerGrade(grade, previous)) latestByCourse.set(courseId, grade)
    }

    const latestGrades = [...latestByCourse.values()]
    const weightedRows = latestGrades
      .map(grade => {
        const credit = Number(courseById.value.get(Number(grade.course))?.credit || 0)
        const point = grade.grade_point === null || grade.grade_point === undefined
          ? Number.NaN
          : Number(grade.grade_point)
        return { credit, point }
      })
      .filter(row => Number.isFinite(row.point) && row.credit > 0)

    const totalCredit = weightedRows.reduce((sum, row) => sum + row.credit, 0)
    const gpa = totalCredit > 0
      ? weightedRows.reduce((sum, row) => sum + row.point * row.credit, 0) / totalCredit
      : null

    const failedGrades = latestGrades.filter(grade => Number(grade.score) < 60)
    const failedCourseNames = [...new Set(failedGrades.map(grade => grade.course_name || `课程ID ${grade.course}`))]

    summaries.set(Number(student.id), {
      gpa,
      gpaText: gpa === null ? '--' : gpa.toFixed(2),
      courseCount: latestGrades.length || null,
      failedCount: latestGrades.length ? failedCourseNames.length : null,
      failedCourseNames: failedCourseNames.join('、'),
    })
  }

  return summaries
})

const archiveGradeOptions = computed(() => {
  const values = [...new Set(archiveStudents.value.map(student => String(student.grade || '').trim()).filter(Boolean))]
  return values.sort((a, b) => a.localeCompare(b, 'zh-CN', { numeric: true }))
})

const archiveMajorOptions = computed(() => {
  const values = [...new Set(archiveStudents.value.map(student => String(student.major || '').trim()).filter(Boolean))]
  return values.sort((a, b) => a.localeCompare(b, 'zh-CN'))
})

const archiveClassOptions = computed(() => {
  const values = archiveStudents.value
    .filter(student => archiveGradeFilter.value === '全部' || student.grade === archiveGradeFilter.value)
    .filter(student => archiveMajorFilter.value === '全部' || student.major === archiveMajorFilter.value)
    .map(student => String(student.class_name || '').trim())
    .filter(Boolean)
  return [...new Set(values)].sort((a, b) => a.localeCompare(b, 'zh-CN', { numeric: true }))
})

const formMajorOptions = computed(() => {
  const values = archiveMajorOptions.value.length ? archiveMajorOptions.value : MAJORS
  return [...new Set([...values, ...MAJORS])]
})

const formGradeOptions = computed(() => {
  const values = [...new Set([...archiveGradeOptions.value, ...GRADE_VALUES])]
  return values.sort((a, b) => a.localeCompare(b, 'zh-CN', { numeric: true }))
})

const archiveFilteredStudents = computed(() => {
  const keyword = archiveSearch.value.trim().toLowerCase()
  return archiveStudents.value
    .filter(student => archiveGradeFilter.value === '全部' || student.grade === archiveGradeFilter.value)
    .filter(student => archiveMajorFilter.value === '全部' || student.major === archiveMajorFilter.value)
    .filter(student => archiveClassFilter.value === '全部' || student.class_name === archiveClassFilter.value)
    .filter(student => {
      if (archiveStatusFilter.value === '在籍') return student.is_active !== false
      if (archiveStatusFilter.value === '非在籍') return student.is_active === false
      return true
    })
    .filter(student => {
      if (!keyword) return true
      return [
        student.student_no,
        student.name,
        student.phone,
        student.email,
      ].some(value => String(value || '').toLowerCase().includes(keyword))
    })
    .sort((a, b) => String(a.student_no).localeCompare(String(b.student_no), 'zh-CN', { numeric: true }))
})

const archiveTotal = computed(() => archiveFilteredStudents.value.length)
const archivePageCount = computed(() => Math.max(1, Math.ceil(archiveTotal.value / ARCHIVE_PAGE_SIZE)))
const archivePageRows = computed(() => {
  const start = (archivePage.value - 1) * ARCHIVE_PAGE_SIZE
  return archiveFilteredStudents.value.slice(start, start + ARCHIVE_PAGE_SIZE)
})
const archivePageStart = computed(() => archiveTotal.value ? (archivePage.value - 1) * ARCHIVE_PAGE_SIZE + 1 : 0)
const archivePageEnd = computed(() => Math.min(archivePage.value * ARCHIVE_PAGE_SIZE, archiveTotal.value))

watch(
  [archiveGradeFilter, archiveMajorFilter, archiveClassFilter, archiveStatusFilter, archiveSearch],
  () => { archivePage.value = 1 },
)

watch(archiveGradeFilter, () => {
  if (archiveClassFilter.value !== '全部' && !archiveClassOptions.value.includes(archiveClassFilter.value)) {
    archiveClassFilter.value = '全部'
  }
})

watch(archiveMajorFilter, () => {
  if (archiveClassFilter.value !== '全部' && !archiveClassOptions.value.includes(archiveClassFilter.value)) {
    archiveClassFilter.value = '全部'
  }
})

async function loadArchiveData() {
  archiveLoading.value = true
  archiveError.value = ''
  try {
    const [colleges, students] = await Promise.all([
      getColleges(),
      fetchAllPages<ApiStudent>(params => getStudents(params)),
    ])

    collegeRecords.value = colleges as ApiCollege[]
    allStudentRecords.value = students as ApiStudent[]

    const targetCollege = collegeRecords.value.find(college =>
      String(college.name || '').includes(ARCHIVE_COLLEGE_KEYWORD),
    )
    const studentCollege = allStudentRecords.value.find(student =>
      String(student.college_name || '').includes(ARCHIVE_COLLEGE_KEYWORD),
    )

    archiveCollegeId.value = targetCollege?.id
      ? Number(targetCollege.id)
      : studentCollege?.college
        ? Number(studentCollege.college)
        : null

    archiveCollegeName.value = targetCollege?.name
      || studentCollege?.college_name
      || ARCHIVE_COLLEGE_KEYWORD

    if (archiveCollegeId.value !== null) {
      archiveStudents.value = allStudentRecords.value.filter(student =>
        Number(student.college) === Number(archiveCollegeId.value),
      )
    } else {
      archiveStudents.value = allStudentRecords.value.filter(student =>
        String(student.college_name || '').includes(ARCHIVE_COLLEGE_KEYWORD),
      )
    }

    if (allStudentRecords.value.length && !archiveStudents.value.length) {
      archiveError.value = `未找到“${ARCHIVE_COLLEGE_KEYWORD}”的学生档案，请检查学院基础数据。`
    }
  } catch (error) {
    archiveStudents.value = []
    archiveError.value = getApiErrorMessage(error)
  } finally {
    archiveLoading.value = false
  }
}

async function loadAcademicData() {
  academicLoading.value = true
  academicError.value = ''
  try {
    const [grades, courses, semesters] = await Promise.all([
      fetchAllPages<ApiGrade>(params => getGrades(params)),
      fetchAllPages<ApiCourse>(params => getCourses(params)),
      getSemesters(),
    ])

    gradeRecords.value = grades as ApiGrade[]
    courseRecords.value = courses as ApiCourse[]
    semesterRecords.value = semesters as ApiSemester[]

    const currentSemester = semesterRecords.value.find(semester => semester.is_current)
    if (currentSemester) {
      scoreSemesterFilter.value = String(currentSemester.id)
    } else if (!scoreSemesterFilter.value && semesterRecords.value.length) {
      const sorted = [...semesterRecords.value].sort((a, b) => {
        const aKey = `${a.academic_year || a.name}-${a.term || ''}`
        const bKey = `${b.academic_year || b.name}-${b.term || ''}`
        return bKey.localeCompare(aKey, 'zh-CN', { numeric: true })
      })
      const newestSemester = sorted[0]
      if (newestSemester) scoreSemesterFilter.value = String(newestSemester.id)
    }
  } catch (error) {
    gradeRecords.value = []
    academicError.value = getApiErrorMessage(error)
  } finally {
    academicLoading.value = false
  }
}

const scoreSemesterLabel = computed(() => {
  if (!scoreSemesterFilter.value) return '全部学期'
  return semesterRecords.value.find(semester => String(semester.id) === scoreSemesterFilter.value)?.name || '所选学期'
})

const academicMajorOptions = computed(() => archiveMajorOptions.value)
const academicGradeOptions = computed(() => archiveGradeOptions.value)

function gradeMatchesAcademicScope(grade: ApiGrade, options: { ignoreMajor?: boolean; ignoreGrade?: boolean } = {}): boolean {
  if (scoreSemesterFilter.value && String(grade.semester || '') !== scoreSemesterFilter.value) return false
  const student = archiveStudents.value.find(item => Number(item.id) === Number(grade.student))
  if (!student) return false
  if (!options.ignoreMajor && scoreMajorFilter.value !== '全部' && student.major !== scoreMajorFilter.value) return false
  if (!options.ignoreGrade && scoreGradeFilter.value !== '全部' && student.grade !== scoreGradeFilter.value) return false
  return true
}

const academicPublishedGrades = computed(() => latestFinalGradeRows(gradeRecords.value.filter(grade =>
  grade.is_published === true
  && isFinalGradeType(grade.exam_type)
  && gradeMatchesAcademicScope(grade),
)))

const academicUnpublishedCount = computed(() => latestFinalGradeRows(gradeRecords.value.filter(grade =>
  grade.is_published !== true
  && isFinalGradeType(grade.exam_type)
  && gradeMatchesAcademicScope(grade),
)).length)

const academicSummary = computed(() => {
  const grades = academicPublishedGrades.value
  const studentIds = new Set(grades.map(grade => Number(grade.student)))
  const courseIds = new Set(grades.map(grade => Number(grade.course)))
  const average = grades.length
    ? grades.reduce((sum, grade) => sum + Number(grade.score || 0), 0) / grades.length
    : null

  return {
    studentCount: studentIds.size,
    courseCount: courseIds.size,
    recordCount: grades.length,
    averageScore: average,
    averageScoreText: average === null ? '--' : average.toFixed(1),
  }
})

const scoreDistribution = computed(() => {
  const buckets = [
    { name: '60分以下', count: 0 },
    { name: '60—69分', count: 0 },
    { name: '70—79分', count: 0 },
    { name: '80—89分', count: 0 },
    { name: '90—100分', count: 0 },
  ]
  for (const grade of academicPublishedGrades.value) {
    const score = Number(grade.score)
    if (!Number.isFinite(score)) continue
    const bucketIndex = score < 60 ? 0 : score < 70 ? 1 : score < 80 ? 2 : score < 90 ? 3 : score <= 100 ? 4 : -1
    if (bucketIndex >= 0) {
      const bucket = buckets[bucketIndex]
      if (bucket) bucket.count += 1
    }
  }
  return buckets
})

const courseScoreStats = computed(() => {
  const groups = new Map<number, ApiGrade[]>()
  for (const grade of academicPublishedGrades.value) {
    const courseId = Number(grade.course)
    if (!courseId) continue
    const list = groups.get(courseId) || []
    list.push(grade)
    groups.set(courseId, list)
  }

  return [...groups.entries()].map(([courseId, grades]) => {
    const scores = grades.map(grade => Number(grade.score)).filter(Number.isFinite)
    const averageScore = scores.length ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 0
    const passCount = scores.filter(score => score >= 60).length
    const course = courseById.value.get(courseId)

    return {
      courseId,
      courseCode: course?.code || '',
      courseName: grades[0]?.course_name || course?.name || `课程 ${courseId}`,
      studentCount: new Set(grades.map(grade => Number(grade.student))).size,
      averageScore,
      highestScore: scores.length ? Math.max(...scores) : 0,
      lowestScore: scores.length ? Math.min(...scores) : 0,
      failedCount: scores.filter(score => score < 60).length,
      passRate: scores.length ? passCount / scores.length * 100 : 0,
    }
  }).sort((a, b) => b.studentCount - a.studentCount || b.averageScore - a.averageScore)
})

const majorScoreStats = computed(() => {
  const groups = new Map<string, number[]>()
  const rows = latestFinalGradeRows(gradeRecords.value.filter(grade =>
    grade.is_published === true
    && isFinalGradeType(grade.exam_type)
    && gradeMatchesAcademicScope(grade, { ignoreMajor: true }),
  ))
  for (const grade of rows) {
    const student = archiveStudents.value.find(item => Number(item.id) === Number(grade.student))
    if (!student?.major) continue
    const list = groups.get(student.major) || []
    list.push(Number(grade.score))
    groups.set(student.major, list)
  }
  return [...groups.entries()].map(([major, scores]) => ({
    name: major,
    average: scores.reduce((sum, score) => sum + score, 0) / Math.max(scores.length, 1),
    count: scores.length,
  })).sort((a, b) => b.average - a.average)
})

const gradeScoreStats = computed(() => {
  const groups = new Map<string, number[]>()
  const rows = latestFinalGradeRows(gradeRecords.value.filter(grade =>
    grade.is_published === true
    && isFinalGradeType(grade.exam_type)
    && gradeMatchesAcademicScope(grade, { ignoreGrade: true }),
  ))
  for (const grade of rows) {
    const student = archiveStudents.value.find(item => Number(item.id) === Number(grade.student))
    if (!student?.grade) continue
    const list = groups.get(student.grade) || []
    list.push(Number(grade.score))
    groups.set(student.grade, list)
  }
  return [...groups.entries()].map(([grade, scores]) => ({
    name: grade,
    average: scores.reduce((sum, score) => sum + score, 0) / Math.max(scores.length, 1),
    count: scores.length,
  })).sort((a, b) => a.name.localeCompare(b.name, 'zh-CN', { numeric: true }))
})

const archiveDetailSummary = computed(() => {
  const studentId = archiveDetailStudent.value?.id
  return studentId ? studentSummaryMap.value.get(Number(studentId)) || null : null
})

const archiveDetailGrades = computed(() => {
  const studentId = archiveDetailStudent.value?.id
  if (!studentId) return []
  return gradeRecords.value
    .filter(grade => Number(grade.student) === Number(studentId))
    .sort((a, b) => semesterOrder(b) - semesterOrder(a) || String(a.course_name || '').localeCompare(String(b.course_name || ''), 'zh-CN'))
})

function openCreateStudent() {
  if (!archiveCollegeId.value) {
    ElMessage.warning('尚未识别学院档案，请先检查学院基础数据。')
    return
  }
  studentDialogMode.value = 'create'
  studentForm.value = createEmptyStudentForm()
  studentDialogVisible.value = true
}

function openEditStudent(student: ApiStudent) {
  studentDialogMode.value = 'edit'
  studentForm.value = {
    id: Number(student.id),
    student_no: student.student_no || '',
    name: student.name || '',
    gender: student.gender || '未说明',
    major: student.major || '',
    grade: student.grade || '',
    class_name: student.class_name || '',
    email: student.email || '',
    phone: student.phone || '',
    enrollment_year: Number(student.enrollment_year || String(student.grade || '').match(/\d{4}/)?.[0] || new Date().getFullYear()),
    is_active: student.is_active !== false,
  }
  studentDialogVisible.value = true
}

function closeStudentDialog() {
  studentDialogVisible.value = false
  studentForm.value = createEmptyStudentForm()
}

async function submitStudentForm() {
  const form = studentForm.value
  if (!archiveCollegeId.value) {
    ElMessage.error('缺少学院基础数据，无法保存学生档案。')
    return
  }
  if (!form.student_no.trim() || !form.name.trim() || !form.major.trim() || !form.grade.trim()) {
    ElMessage.warning('请填写学号、姓名、专业和年级。')
    return
  }
  if (!Number.isInteger(Number(form.enrollment_year)) || Number(form.enrollment_year) < 2000) {
    ElMessage.warning('请填写正确的入学年份。')
    return
  }

  const payload: StudentPayload = {
    student_no: form.student_no.trim(),
    name: form.name.trim(),
    gender: form.gender || '未说明',
    college: Number(archiveCollegeId.value),
    major: form.major.trim(),
    grade: form.grade.trim(),
    class_name: form.class_name.trim(),
    email: form.email.trim(),
    phone: form.phone.trim(),
    enrollment_year: Number(form.enrollment_year),
    is_active: Boolean(form.is_active),
  }

  studentSaving.value = true
  try {
    if (studentDialogMode.value === 'create') {
      await createStudent(payload as any)
      ElMessage.success('学生档案新增成功。')
    } else if (form.id) {
      await updateStudent(form.id, payload as any)
      ElMessage.success('学生档案更新成功。')
    }
    closeStudentDialog()
    await loadArchiveData()
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error))
  } finally {
    studentSaving.value = false
  }
}

function openArchiveDetail(student: ApiStudent) {
  archiveDetailStudent.value = student
  archiveDetailVisible.value = true
}

function closeArchiveDetail() {
  archiveDetailVisible.value = false
  archiveDetailStudent.value = null
}

function editArchiveDetailStudent() {
  const student = archiveDetailStudent.value
  if (!student) return
  closeArchiveDetail()
  openEditStudent(student)
}

function triggerArchiveImport() {
  archiveImportInputRef.value?.click()
}

function downloadStudentTemplate() {
  const workbook = XLSX.utils.book_new()
  const studentSheet = XLSX.utils.aoa_to_sheet([[
    '学号', '姓名', '性别', '专业', '年级', '班级', '入学年份', '联系电话', '电子邮箱', '在籍状态',
  ]])
  const gradeSheet = XLSX.utils.aoa_to_sheet([[
    '学号', '课程代码', '学期', '考核类型', '成绩', '绩点', '考核日期', '备注',
  ]])
  const guideSheet = XLSX.utils.aoa_to_sheet([
    ['工作表', '字段', '填写说明'],
    ['学生基本信息', '学号', '必填；全院唯一，已存在学号将按原档案更新'],
    ['学生基本信息', '性别', '填写男、女或未说明'],
    ['学生基本信息', '专业 / 年级', '必须与学院实际专业、年级一致'],
    ['学生基本信息', '在籍状态', '填写是或否；更新已有档案时留空保留原状态，新建档案留空默认在籍'],
    ['成绩明细', '学号 / 课程代码 / 学期', '必须能在系统中找到对应学生、课程和学期'],
    ['成绩明细', '考核类型', '填写期末、期中、平时等系统使用的考核类型'],
    ['成绩明细', '成绩 / 绩点', '成绩填写数值；绩点可留空；成绩导入后默认未发布'],
    ['成绩明细', '考核日期', '可留空；填写 YYYY-MM-DD'],
    ['注意事项', '成绩覆盖', '已发布成绩不会通过本导入功能覆盖；未发布成绩可按学号、课程、学期和考核类型更新'],
  ])
  XLSX.utils.book_append_sheet(workbook, studentSheet, '学生基本信息')
  XLSX.utils.book_append_sheet(workbook, gradeSheet, '成绩明细')
  XLSX.utils.book_append_sheet(workbook, guideSheet, '填写说明')
  XLSX.writeFile(workbook, '学生档案导入模板.xlsx')
}

function exportArchiveExcel() {
  const students = archiveFilteredStudents.value
  if (!students.length) {
    ElMessage.warning('当前筛选条件下没有可导出的学生档案。')
    return
  }

  const studentIds = new Set(students.map(student => Number(student.id)))
  const basicRows = students.map(student => {
    const summary = studentSummaryMap.value.get(Number(student.id))
    return {
      学号: student.student_no,
      姓名: student.name,
      性别: student.gender || '未说明',
      学院: student.college_name || archiveCollegeName.value,
      专业: student.major,
      年级: student.grade,
      班级: student.class_name || '',
      入学年份: student.enrollment_year,
      联系电话: student.phone || '',
      电子邮箱: student.email || '',
      在籍状态: student.is_active === false ? '否' : '是',
      平均GPA: summary?.gpaText || '--',
      已修课程数: summary?.courseCount ?? '--',
      未通过课程数: summary?.failedCount ?? '--',
      未通过课程名称: summary?.failedCourseNames || '',
    }
  })

  const courseMap = new Map(courseRecords.value.map(course => [Number(course.id), course]))
  const semesterMap = new Map(semesterRecords.value.map(semester => [Number(semester.id), semester]))
  const studentMap = new Map(allStudentRecords.value.map(student => [Number(student.id), student]))
  const gradeRows = gradeRecords.value
    .filter(grade => studentIds.has(Number(grade.student)))
    .map(grade => {
      const course = courseMap.get(Number(grade.course))
      const student = studentMap.get(Number(grade.student))
      const semester = semesterMap.get(Number(grade.semester))
      return {
        学号: student?.student_no || grade.student_id || '',
        姓名: grade.student_name || student?.name || '',
        课程代码: course?.code || '',
        课程名称: grade.course_name || course?.name || '',
        学期: grade.semester_name || semester?.name || '',
        考核类型: grade.exam_type || '',
        成绩: grade.score,
        绩点: grade.grade_point ?? '',
        考核日期: grade.exam_date || '',
        发布状态: grade.is_published ? '已发布' : '未发布',
        备注: grade.remark || '',
      }
    })

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(basicRows), '学生基本信息')
  XLSX.utils.book_append_sheet(workbook, XLSX.utils.json_to_sheet(gradeRows), '成绩明细')
  XLSX.utils.book_append_sheet(workbook, XLSX.utils.aoa_to_sheet([
    ['导出时间', new Date().toLocaleString('zh-CN')],
    ['学院', archiveCollegeName.value],
    ['年级筛选', archiveGradeFilter.value],
    ['专业筛选', archiveMajorFilter.value],
    ['班级筛选', archiveClassFilter.value],
    ['学籍状态筛选', archiveStatusFilter.value],
    ['学生数量', students.length],
    ['成绩记录数量', gradeRows.length],
    ['说明', 'GPA 与未通过课程按已发布期末成绩及课程学分汇总；成绩明细包含已发布和未发布记录并明确标记。'],
  ]), '导出说明')
  XLSX.writeFile(workbook, `学生档案_${new Date().toISOString().slice(0, 10)}.xlsx`)
  ElMessage.success(`已导出 ${students.length} 名学生及其成绩明细。`)
}

function readExcelCell(row: Record<string, unknown>, ...keys: string[]): unknown {
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(row, key)) return row[key]
  }
  return ''
}

function excelDateToIso(value: unknown): string | null {
  if (value === null || value === undefined || value === '') return null
  if (value instanceof Date && !Number.isNaN(value.getTime())) return value.toISOString().slice(0, 10)
  if (typeof value === 'number') {
    const parsed = XLSX.SSF.parse_date_code(value)
    if (parsed) {
      const month = String(parsed.m).padStart(2, '0')
      const day = String(parsed.d).padStart(2, '0')
      return `${parsed.y}-${month}-${day}`
    }
  }
  const text = String(value).trim()
  if (!text) return null
  const normalized = text.replace(/\//g, '-')
  return /^\d{4}-\d{1,2}-\d{1,2}$/.test(normalized) ? normalized : null
}

function parseActiveValue(value: unknown): boolean {
  const text = String(value ?? '').trim().toLowerCase()
  return !['否', '非在籍', '离校', '毕业', '停用', 'false', '0'].includes(text)
}

function buildGradeKey(studentId: number, courseId: number, semesterId: number, examType: string): string {
  return `${studentId}|${courseId}|${semesterId}|${examType.trim()}`
}

async function handleArchiveFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  try {
    importResultText.value = ''
    if (!allStudentRecords.value.length && !archiveLoading.value) await loadArchiveData()
    if (!courseRecords.value.length || !semesterRecords.value.length) await loadAcademicData()

    const workbook = XLSX.read(await file.arrayBuffer(), { type: 'array', cellDates: true })
    const studentSheet = workbook.Sheets['学生基本信息']
    const gradeSheet = workbook.Sheets['成绩明细']
    if (!studentSheet) {
      throw new Error('Excel 中缺少“学生基本信息”工作表，请先下载系统模板。')
    }

    const studentRows = XLSX.utils.sheet_to_json<Record<string, unknown>>(studentSheet, { defval: '' })
    const gradeRows = gradeSheet
      ? XLSX.utils.sheet_to_json<Record<string, unknown>>(gradeSheet, { defval: '' })
      : []

    const errors: string[] = []
    const parsedStudents: ImportStudentRow[] = []
    const parsedGrades: ImportGradeRow[] = []
    const currentByNo = new Map(allStudentRecords.value.map(student => [String(student.student_no), student]))
    const seenStudentNos = new Set<string>()
    const importStudentNos = new Set<string>()

    if (!archiveCollegeId.value) {
      importPreview.value = {
        studentRows: [],
        gradeRows: [],
        errors: ['未识别到政治学与公共管理学院的学院编号，不能导入学生档案或成绩。'],
      }
      return
    }

    studentRows.forEach((row, index) => {
      const rowNo = index + 2
      if (!archiveCollegeId.value) return
      const studentNo = String(readExcelCell(row, '学号', 'student_no') || '').trim()
      const name = String(readExcelCell(row, '姓名', 'name') || '').trim()
      const genderRaw = String(readExcelCell(row, '性别', 'gender') || '').trim()
      const major = String(readExcelCell(row, '专业', '所属专业', 'major') || '').trim()
      let grade = String(readExcelCell(row, '年级', 'grade') || '').trim()
      const classNameRaw = String(readExcelCell(row, '班级', 'class_name') || '').trim()
      const emailRaw = String(readExcelCell(row, '电子邮箱', '邮箱', 'email') || '').trim()
      const phoneRaw = String(readExcelCell(row, '联系电话', '手机号', 'phone') || '').trim()
      const activeRaw = readExcelCell(row, '在籍状态', 'is_active')
      const enrollmentRaw = readExcelCell(row, '入学年份', 'enrollment_year')
      const enrollmentYearText = String(enrollmentRaw || '').match(/\d{4}/)?.[0] || grade.match(/\d{4}/)?.[0] || ''
      const enrollmentYear = Number(enrollmentYearText)

      if (!studentNo || !name || !major || !grade || !enrollmentYear) {
        errors.push(`学生基本信息第 ${rowNo} 行：学号、姓名、专业、年级和入学年份为必填项。`)
        return
      }
      if (/^\d{4}$/.test(grade)) grade = `${grade}级`
      if (seenStudentNos.has(studentNo)) {
        errors.push(`学生基本信息第 ${rowNo} 行：文件中学号 ${studentNo} 重复。`)
        return
      }
      seenStudentNos.add(studentNo)

      const existing = currentByNo.get(studentNo)
      if (existing && archiveCollegeId.value && Number(existing.college) !== Number(archiveCollegeId.value)) {
        errors.push(`学生基本信息第 ${rowNo} 行：学号 ${studentNo} 已属于其他学院，不能在本学院覆盖。`)
        return
      }
      importStudentNos.add(studentNo)

      const gender = genderRaw
        ? (['男', '女', '未说明'].includes(genderRaw) ? genderRaw : '未说明')
        : (existing?.gender || '未说明')
      parsedStudents.push({
        rowNo,
        studentNo,
        action: existing ? 'update' : 'create',
        existingId: existing?.id,
        payload: {
          student_no: studentNo,
          name,
          gender,
          college: Number(archiveCollegeId.value || existing?.college || 0),
          major,
          grade,
          class_name: classNameRaw || existing?.class_name || '',
          email: emailRaw || existing?.email || '',
          phone: phoneRaw || existing?.phone || '',
          enrollment_year: enrollmentYear,
          is_active: activeRaw === '' || activeRaw === null || activeRaw === undefined
            ? (existing ? existing.is_active !== false : true)
            : parseActiveValue(activeRaw),
        },
      })
    })

    const studentIdByNo = new Map(allStudentRecords.value.map(student => [String(student.student_no), Number(student.id)]))
    const courseByCode = new Map(courseRecords.value.map(course => [String(course.code).trim(), course]))
    const semesterByName = new Map(semesterRecords.value.map(semester => [String(semester.name).trim(), semester]))
    const existingGradeByKey = new Map<string, ApiGrade>()
    for (const grade of gradeRecords.value) {
      if (grade.semester === null || grade.semester === undefined) continue
      existingGradeByKey.set(buildGradeKey(Number(grade.student), Number(grade.course), Number(grade.semester), String(grade.exam_type || '')), grade)
    }
    const seenGradeKeys = new Set<string>()

    gradeRows.forEach((row, index) => {
      const rowNo = index + 2
      const studentNo = String(readExcelCell(row, '学号', 'student_no') || '').trim()
      const courseCode = String(readExcelCell(row, '课程代码', 'course_code') || '').trim()
      const semesterName = String(readExcelCell(row, '学期', 'semester') || '').trim()
      const examType = String(readExcelCell(row, '考核类型', '成绩类型', 'exam_type') || '').trim()
      const scoreRaw = readExcelCell(row, '成绩', 'score')
      const score = Number(scoreRaw)
      const gradePointRaw = readExcelCell(row, '绩点', 'grade_point')
      const gradePoint = gradePointRaw === '' || gradePointRaw === null || gradePointRaw === undefined
        ? null
        : Number(gradePointRaw)
      const course = courseByCode.get(courseCode)
      const semester = semesterByName.get(semesterName)

      if (!studentNo || !courseCode || !semesterName || !examType || scoreRaw === '' || scoreRaw === null || scoreRaw === undefined || !Number.isFinite(score)) {
        errors.push(`成绩明细第 ${rowNo} 行：学号、课程代码、学期、考核类型和数值成绩均为必填项。`)
        return
      }
      if (score < 0 || score > 100 || (gradePoint !== null && (!Number.isFinite(gradePoint) || gradePoint < 0 || gradePoint > 5))) {
        errors.push(`成绩明细第 ${rowNo} 行：成绩须为 0—100，绩点须为 0—5。`)
        return
      }
      const existingStudent = currentByNo.get(studentNo)
      if (existingStudent && archiveCollegeId.value && Number(existingStudent.college) !== Number(archiveCollegeId.value)) {
        errors.push(`成绩明细第 ${rowNo} 行：学号 ${studentNo} 不属于本学院，不能导入其成绩。`)
        return
      }
      if (!existingStudent && !importStudentNos.has(studentNo)) {
        errors.push(`成绩明细第 ${rowNo} 行：学号 ${studentNo} 不存在，也未出现在学生基本信息工作表中。`)
        return
      }
      if (!course) {
        errors.push(`成绩明细第 ${rowNo} 行：系统中不存在课程代码 ${courseCode}。`)
        return
      }
      if (!semester) {
        errors.push(`成绩明细第 ${rowNo} 行：系统中不存在学期“${semesterName}”，请使用系统中的完整学期名称。`)
        return
      }

      const studentId = studentIdByNo.get(studentNo)
      const existing = studentId
        ? existingGradeByKey.get(buildGradeKey(studentId, Number(course.id), Number(semester.id), examType))
        : undefined
      if (existing?.is_published === true) {
        errors.push(`成绩明细第 ${rowNo} 行：${studentNo} 的该课程成绩已发布，不能通过档案导入覆盖。`)
        return
      }

      const key = `${studentNo}|${courseCode}|${semesterName}|${examType}`
      if (seenGradeKeys.has(key)) {
        errors.push(`成绩明细第 ${rowNo} 行：同一学生、课程、学期和考核类型在文件中重复。`)
        return
      }
      seenGradeKeys.add(key)

      parsedGrades.push({
        rowNo,
        studentNo,
        action: existing ? 'update' : 'create',
        existingId: existing?.id,
        payload: {
          course: Number(course.id),
          semester: Number(semester.id),
          exam: null,
          score,
          grade_point: gradePointRaw === '' || gradePointRaw === null || gradePointRaw === undefined
            ? (existing?.grade_point === undefined ? null : existing.grade_point)
            : gradePoint,
          exam_type: examType,
          exam_date: excelDateToIso(readExcelCell(row, '考核日期', 'exam_date')) || existing?.exam_date || null,
          remark: String(readExcelCell(row, '备注', 'remark') || '').trim() || existing?.remark || '',
          is_published: false,
        },
      })
    })

    importPreview.value = {
      studentRows: parsedStudents,
      gradeRows: parsedGrades,
      errors,
    }
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error))
  } finally {
    input.value = ''
  }
}

async function confirmArchiveImport() {
  const preview = importPreview.value
  if (!preview || (!preview.studentRows.length && !preview.gradeRows.length)) return

  isImporting.value = true
  const failures: string[] = []
  let createdStudents = 0
  let updatedStudents = 0
  let createdGrades = 0
  let updatedGrades = 0
  const studentIdByNo = new Map(allStudentRecords.value.map(student => [String(student.student_no), Number(student.id)]))

  try {
    await runInBatches(preview.studentRows, 10, async row => {
      try {
        if (row.action === 'create') {
          const created = await createStudent(row.payload as any) as ApiStudent
          if (!created?.id) throw new Error('接口未返回新学生档案编号。')
          studentIdByNo.set(row.studentNo, Number(created.id))
          createdStudents += 1
        } else if (row.existingId) {
          await updateStudent(row.existingId, row.payload as any)
          studentIdByNo.set(row.studentNo, Number(row.existingId))
          updatedStudents += 1
        }
      } catch (error) {
        failures.push(`学生档案第 ${row.rowNo} 行（${row.studentNo}）：${getApiErrorMessage(error)}`)
      }
    })

    await runInBatches(preview.gradeRows, 10, async row => {
      const studentId = studentIdByNo.get(row.studentNo)
      if (!studentId) {
        failures.push(`成绩明细第 ${row.rowNo} 行（${row.studentNo}）：学生档案未成功保存，成绩未导入。`)
        return
      }
      try {
        const payload = { ...row.payload, student: studentId } as GradePayload
        if (row.action === 'update' && row.existingId) {
          await updateGrade(row.existingId, payload as any)
          updatedGrades += 1
        } else {
          await createGrade(payload as any)
          createdGrades += 1
        }
      } catch (error) {
        failures.push(`成绩明细第 ${row.rowNo} 行（${row.studentNo}）：${getApiErrorMessage(error)}`)
      }
    })

    await Promise.all([loadArchiveData(), loadAcademicData()])

    const summary = `新增学生 ${createdStudents} 人，更新学生 ${updatedStudents} 人，新增成绩 ${createdGrades} 条，更新未发布成绩 ${updatedGrades} 条。`
    const allErrors = [...preview.errors, ...failures]
    if (allErrors.length) {
      importResultText.value = summary
      importPreview.value = { studentRows: [], gradeRows: [], errors: allErrors }
      ElMessage.warning(`${summary}另有 ${allErrors.length} 条记录未导入，请查看导入结果。`)
    } else {
      importPreview.value = null
      importResultText.value = ''
      ElMessage.success(summary)
    }
  } catch (error) {
    ElMessage.error(getApiErrorMessage(error))
  } finally {
    isImporting.value = false
  }
}

function closeImportPreview() {
  if (isImporting.value) return
  importPreview.value = null
  importResultText.value = ''
}

function initAcademicCharts() {
  if (scoreDistributionChartRef.value) {
    scoreDistributionChart = echarts.init(scoreDistributionChartRef.value)
  }
  if (majorScoreChartRef.value) {
    majorScoreChart = echarts.init(majorScoreChartRef.value)
  }
  if (gradeScoreChartRef.value) {
    gradeScoreChart = echarts.init(gradeScoreChartRef.value)
  }
  updateAcademicCharts()
}

function updateAcademicCharts() {
  if (scoreDistributionChart) {
    scoreDistributionChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#374151', fontSize: 12 } },
      grid: { top: 18, left: 34, right: 12, bottom: 38 },
      xAxis: {
        type: 'category',
        data: scoreDistribution.value.map(item => item.name),
        axisLabel: { color: '#6B7280', fontSize: 9, interval: 0 },
        axisLine: { lineStyle: { color: '#E5E7EB' } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { color: '#9CA3AF', fontSize: 9 },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      },
      series: [{
        type: 'bar',
        data: scoreDistribution.value.map(item => item.count),
        barMaxWidth: 24,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3B82F6' },
            { offset: 1, color: '#93C5FD' },
          ]),
          borderRadius: [5, 5, 0, 0],
        },
        label: { show: true, position: 'top', color: '#475569', fontSize: 9 },
      }],
    }, true)
  }

  if (majorScoreChart) {
    majorScoreChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#374151', fontSize: 12 } },
      grid: { top: 18, left: 34, right: 12, bottom: 48 },
      xAxis: {
        type: 'category',
        data: majorScoreStats.value.map(item => item.name),
        axisLabel: { color: '#6B7280', fontSize: 9, interval: 0, rotate: 18 },
        axisLine: { lineStyle: { color: '#E5E7EB' } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { color: '#9CA3AF', fontSize: 9 },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      },
      series: [{
        type: 'bar',
        data: majorScoreStats.value.map(item => ({ value: Number(item.average.toFixed(1)), name: item.name })),
        barMaxWidth: 24,
        itemStyle: { color: '#2563EB', borderRadius: [5, 5, 0, 0] },
        label: { show: true, position: 'top', color: '#1E3A8A', fontSize: 9, formatter: '{c}' },
      }],
    }, true)
  }

  if (gradeScoreChart) {
    gradeScoreChart.setOption({
      tooltip: { trigger: 'axis', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#374151', fontSize: 12 } },
      grid: { top: 16, left: 34, right: 12, bottom: 32 },
      xAxis: {
        type: 'category',
        data: gradeScoreStats.value.map(item => item.name),
        axisLabel: { color: '#6B7280', fontSize: 9, interval: 0 },
        axisLine: { lineStyle: { color: '#E5E7EB' } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { color: '#9CA3AF', fontSize: 9 },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      },
      series: [{
        type: 'line',
        data: gradeScoreStats.value.map(item => Number(item.average.toFixed(1))),
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { color: '#60A5FA', width: 3 },
        itemStyle: { color: '#2563EB' },
        areaStyle: { color: 'rgba(96, 165, 250, 0.12)' },
        label: { show: true, color: '#1E3A8A', fontSize: 9, formatter: '{c}' },
      }],
    }, true)
  }
}

watch(
  [scoreSemesterFilter, scoreMajorFilter, scoreGradeFilter],
  async () => {
    await nextTick()
    updateAcademicCharts()
  },
)


const filteredStudents = computed(() => studentRecords.filter(student => {
  const gradeMatched = currentGrade.value === '全部' || student.grade === currentGrade.value
  const majorMatched = currentMajor.value === '全部' || student.major === currentMajor.value
  return gradeMatched && majorMatched
}))

const warningCount = computed(() => filteredStudents.value.filter(student => student.riskLevel !== 'low').length)

const studentStats = computed(() => {
  const students = filteredStudents.value
  const total = students.length
  const averageGpa = total
    ? students.reduce((sum, student) => sum + student.gpa, 0) / total
    : 0
  const scholarshipCount = students.filter(student => student.scholarship).length

  return [
    {
      label: '在校学生',
      value: total.toLocaleString('zh-CN'),
      unit: '人',
      sub: '当前筛选范围',
      icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
      bg: '#EFF6FF',
      color: '#1E3A8A',
      sparkline: '0,14 10,18 20,13 30,19 40,15 50,20 60,16 70,19 80,15',
    },
    {
      label: '平均 GPA',
      value: averageGpa.toFixed(2),
      unit: '',
      sub: '按当前学生计算',
      icon: 'M12 20v-6 M6 20V10 M18 20V4',
      bg: '#DBEAFE',
      color: '#3B82F6',
      sparkline: '0,12 10,16 20,13 30,17 40,14 50,18 60,15 70,17 80,14',
    },
    {
      label: '奖学金获得者',
      value: scholarshipCount.toLocaleString('zh-CN'),
      unit: '人',
      sub: total ? `${(scholarshipCount / total * 100).toFixed(1)}% 获得率` : '暂无学生数据',
      icon: 'M12 15l-2 2l1-3.5l-2-1.5h2.5L12 8.5l.5 3.5H15l-2 1.5l1 3.5z',
      bg: '#BFDBFE',
      color: '#2563EB',
      sparkline: '0,11 10,14 20,12 30,16 40,13 50,17 60,14 70,18 80,15',
    },
    {
      label: '学业预警',
      value: warningCount.value.toLocaleString('zh-CN'),
      unit: '人',
      sub: total ? `${(warningCount.value / total * 100).toFixed(1)}% 预警比例` : '暂无学生数据',
      icon: 'M22 12h-4l-3 9L9 3l-3 9H2',
      bg: '#F3F4F6',
      color: '#64748B',
      sparkline: '0,16 10,13 20,18 30,11 40,15 50,10 60,14 70,9 80,12',
    },
  ]
})

const warningStudents = computed(() => filteredStudents.value
  .filter(student => student.riskLevel !== 'low')
  .sort((a, b) => {
    const riskOrder = { high: 0, mid: 1, low: 2 }
    return riskOrder[a.riskLevel] - riskOrder[b.riskLevel] || a.gpa - b.gpa
  })
  .slice(0, 8))

const honorStudents = computed(() => filteredStudents.value
  .filter(student => student.scholarship || student.gpa >= 3.62)
  .sort((a, b) => b.gpa - a.gpa)
  .slice(0, 6))

const classComparison = computed(() => {
  const groups = new Map<string, StudentRecord[]>()
  for (const student of filteredStudents.value) {
    const group = groups.get(student.className) || []
    group.push(student)
    groups.set(student.className, group)
  }

  return [...groups.entries()]
    .map(([name, students]) => {
      const count = students.length
      const avgGpa = students.reduce((sum, student) => sum + student.gpa, 0) / count
      const excellentRate = students.filter(student => student.gpa >= 3.5).length / count * 100
      const warningCount = students.filter(student => student.riskLevel !== 'low').length
      const cetPassRate = students.filter(student => student.cetPassed).length / count * 100
      const competitionAwards = students.reduce((sum, student) => sum + student.competitionAwards, 0)
      return {
        name,
        students: count,
        avgGpa,
        excellentRate: Math.round(excellentRate),
        warningCount,
        cetPassRate: Math.round(cetPassRate),
        competitionAwards,
      }
    })
    .sort((a, b) => b.avgGpa - a.avgGpa)
})

const chartGradeDistribution = computed(() => GRADE_VALUES
  .map((grade, index) => ({
    name: grade,
    value: filteredStudents.value.filter(student => student.grade === grade).length,
    itemStyle: { color: GRADE_COLORS[index] || '#93C5FD' },
  }))
  .filter(item => item.value > 0))

const chartMajorDistribution = computed(() => MAJORS
  .map((major, index) => ({
    name: major,
    value: filteredStudents.value.filter(student => student.major === major).length,
    itemStyle: { color: MAJOR_COLORS[index] || '#DBEAFE' },
  }))
  .filter(item => item.value > 0))

function updateGradeChart() {
  if (!gradeChart) return
  const total = filteredStudents.value.length
  gradeChart.setOption({
    legend: {
      data: [...chartGradeDistribution.value.map(item => item.name), ...chartMajorDistribution.value.map(item => item.name)],
    },
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '43%',
        style: {
          text: total.toLocaleString('zh-CN'),
          textAlign: 'center',
          fill: '#1E3A8A',
          fontSize: 22,
          fontWeight: 700,
        },
      },
      {
        type: 'text',
        left: 'center',
        top: '54%',
        style: {
          text: '筛选人数',
          textAlign: 'center',
          fill: '#9CA3AF',
          fontSize: 11,
        },
      },
    ],
    series: [
      { data: chartGradeDistribution.value },
      { data: chartMajorDistribution.value },
    ],
  })
}

function initGradeChart() {
  if (!gradeChartRef.value) return
  gradeChart = echarts.init(gradeChartRef.value)
  gradeChart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 13 },
      formatter: '{b}: {c} 人 ({d}%)',
    },
    legend: {
      type: 'scroll',
      bottom: 0,
      textStyle: { color: '#6B7280', fontSize: 10 },
      itemWidth: 9,
      itemHeight: 9,
      itemGap: 10,
    },
    series: [
      {
        name: '年级分布',
        type: 'pie',
        radius: ['60%', '82%'],
        center: ['50%', '46%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#FFF', borderWidth: 3 },
        label: { show: true, position: 'inside', formatter: '{d}%', fontSize: 10, fontWeight: 600, color: '#FFF' },
        emphasis: { label: { fontSize: 14, fontWeight: 'bold' }, scaleSize: 6 },
        data: [],
      },
      {
        name: '专业分布',
        type: 'pie',
        radius: ['32%', '52%'],
        center: ['50%', '46%'],
        itemStyle: { borderRadius: 4, borderColor: '#FFF', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 10 } },
        data: [],
      },
    ],
  })
  updateGradeChart()
}

function riskLabel(level: string) {
  if (level === 'high') return '高风险'
  if (level === 'mid') return '中风险'
  return '正常'
}

function gpaColorClass(gpa: number) {
  if (gpa >= 3.7) return 'gpa-excellent'
  if (gpa >= 3.0) return 'gpa-good'
  if (gpa >= 2.0) return 'gpa-warning'
  return 'gpa-danger'
}

function tagStyle(tag: string) {
  if (tag.includes('奖学金') || tag.includes('竞赛') || tag.includes('科研') || tag.includes('论文') || tag.includes('编程') || tag.includes('助教') || tag.includes('新生') || tag.includes('班委')) {
    return { background: '#EFF6FF', color: '#1E3A8A' }
  }
  if (tag.includes('困难') || tag.includes('帮扶') || tag.includes('留级') || tag.includes('重点') || tag.includes('预警')) {
    return { background: '#FEF2F2', color: '#DC2626' }
  }
  if (tag.includes('波动') || tag.includes('休学') || tag.includes('指导')) {
    return { background: '#FFFBEB', color: '#D97706' }
  }
  return { background: '#F3F4F6', color: '#6B7280' }
}

function statusClass(status: string) {
  if (status === '在读') return 'status-progress'
  if (status === '警告') return 'status-pending'
  if (status === '休学') return 'status-suspended'
  return 'status-ended'
}

// ========== 3. 就业与深造趋势（全院历年汇总） ==========
function initEmploymentChart() {
  if (!employmentChartRef.value) return
  employmentChart = echarts.init(employmentChartRef.value)
  const years = ['2020', '2021', '2022', '2023', '2024']
  employmentChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 13 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 11 }, itemWidth: 14, itemHeight: 8, itemGap: 24 },
    grid: { top: 10, right: 50, bottom: 40, left: 50 },
    xAxis: {
      type: 'category',
      data: years,
      axisLabel: { color: '#6B7280', fontSize: 11 },
      axisLine: { lineStyle: { color: '#E5E7EB' } },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: '百分比(%)',
        min: 0,
        max: 100,
        nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
        axisLabel: { color: '#6B7280', fontSize: 10 },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      },
      {
        type: 'value',
        name: '薪资(千元)',
        nameTextStyle: { color: '#9CA3AF', fontSize: 10 },
        axisLabel: { color: '#6B7280', fontSize: 10, formatter: '{value}k' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '就业率',
        type: 'bar',
        data: [91.2, 92.8, 93.5, 94.1, 95.2],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#1E3A8A' },
            { offset: 1, color: '#3B82F6' },
          ]),
          borderRadius: [6, 6, 0, 0],
          shadowBlur: 4,
          shadowColor: 'rgba(30, 58, 138, 0.2)',
          shadowOffsetY: 2,
        },
        barWidth: 28,
        label: { show: true, position: 'top', color: '#1E3A8A', fontSize: 10, fontWeight: 600, formatter: '{c}%' },
      },
      {
        name: '深造率',
        type: 'bar',
        data: [35.1, 36.8, 38.2, 40.5, 42.1],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3B82F6' },
            { offset: 1, color: '#93C5FD' },
          ]),
          borderRadius: [6, 6, 0, 0],
          shadowBlur: 4,
          shadowColor: 'rgba(59, 130, 246, 0.15)',
          shadowOffsetY: 2,
        },
        barWidth: 28,
        label: { show: true, position: 'top', color: '#3B82F6', fontSize: 10, fontWeight: 600, formatter: '{c}%' },
      },
      {
        name: '平均薪资',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: [8.5, 9.2, 10.1, 11.5, 13.2],
        itemStyle: { color: '#60A5FA' },
        lineStyle: { width: 3 },
        symbol: 'circle',
        symbolSize: 8,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(96, 165, 250, 0.2)' },
            { offset: 1, color: 'rgba(96, 165, 250, 0.02)' },
          ]),
        },
        label: { show: true, color: '#60A5FA', fontSize: 10, fontWeight: 600, formatter: '{c}k' },
      },
    ],
  })
}

// ========== 5. 学生成长时间轴 ==========
// ========== 8. 成长时间轴 ==========
interface GrowthTimelineEvent {
  date: string
  title: string
  desc: string
  done: boolean
  active: boolean
  stats?: Record<string, string | number>
}

const growthTimeline: GrowthTimelineEvent[] = [
  { date: '9月', title: '新生入学教育', desc: '新生报到注册，开展入学教育与专业导学', done: true, active: false },
  { date: '10月', title: '期中教学检查', desc: '开展期中教学评估、学业情况筛查与导师交流', done: true, active: false },
  { date: '11月', title: '学业跟踪与学习指导', desc: '持续跟踪学生学习状态，为需要帮助的学生制定阶段性指导计划', done: false, active: true },
  { date: '12月', title: '期末考核与论文', desc: '组织课程期末考核、学术论文提交与教学质量检查', done: false, active: false },
  { date: '1月', title: '学期综合测评', desc: '开展综合素质测评、学业评价与奖学金评定', done: false, active: false },
  { date: '3月', title: '春季学期开学', desc: '完成新学期课程注册，开展社会实践与专业实训', done: false, active: false },
  { date: '5月', title: '毕业论文中期答辩与实训', desc: '组织毕业论文中期答辩、专业实训与就业指导活动', done: false, active: false },
  { date: '7月', title: '毕业季与夏季学期', desc: '开展毕业资格审核、毕业典礼与夏季学期教学活动', done: false, active: false },
]

// ========== 6. 学生详情：主档与成长记录按 studentId 关联 ==========
const growthRecordStore: GrowthRecord[] = studentRecords.flatMap(student => {
  const year = Number(student.grade.slice(0, 4))
  const records: GrowthRecord[] = [
    { studentId: student.id, date: `${year}.09`, text: `${student.grade}入学注册，完成专业导学与培养方案确认` },
    { studentId: student.id, date: `${year}.10`, text: '参加学期学习情况检查，与学业导师进行阶段沟通' },
  ]
  if (year < 2026) {
    records.push({
      studentId: student.id,
      date: '2026.09',
      text: student.riskLevel === 'low' ? '完成本学年阶段性学业评估，保持良好学习状态' : '完成本学年学业评估，纳入后续学习指导跟进',
    })
  }
  if (student.scholarship) {
    records.push({ studentId: student.id, date: year === 2026 ? '2026.11' : '2026.10', text: `获得${student.award}，综合表现得到认可` })
  }
  return records
})

const studentGrowthRecords = computed(() => {
  const studentId = detailStudent.value?.id
  return studentId ? growthRecordStore.filter(record => record.studentId === studentId) : []
})

function openStudentDetail(studentId: number) {
  const student = studentById.get(studentId)
  if (!student) return
  detailStudent.value = student
  drawerVisible.value = true
  document.body.style.overflow = 'hidden'
}

function closeDrawer() {
  drawerVisible.value = false
  detailStudent.value = null
  document.body.style.overflow = ''
}

// ========== 7. 筛选变化时同步更新图表 ==========
watch([currentGrade, currentMajor], async () => {
  await nextTick()
  updateGradeChart()
}, { flush: 'post' })

// ========== Lifecycle ==========
// 图表应在 DOM 就绪后立即初始化，不得等待学生档案 / 成绩接口返回。
// 接口可能包含多页请求，等待它们会让静态年级分布、就业趋势图也长期空白。
let chartsMounted = false
let chartResizeObserver: ResizeObserver | null = null
let chartResizeFrame: number | null = null

function scheduleChartResize() {
  if (!chartsMounted || chartResizeFrame !== null) return
  chartResizeFrame = requestAnimationFrame(() => {
    chartResizeFrame = null
    if (chartsMounted) handleResize()
  })
}

onMounted(async () => {
  chartsMounted = true
  await nextTick()
  if (!chartsMounted) return

  // 不阻塞首屏：先画图，再异步加载学生和成绩记录。
  initGradeChart()
  initEmploymentChart()
  initAcademicCharts()

  // 图表宽度随父容器、侧边栏和浏览器布局变化时自动校正。
  if (typeof ResizeObserver !== 'undefined') {
    chartResizeObserver = new ResizeObserver(scheduleChartResize)
    const containers = [
      gradeChartRef.value,
      employmentChartRef.value,
      scoreDistributionChartRef.value,
      majorScoreChartRef.value,
      gradeScoreChartRef.value,
    ]
    for (const container of containers) {
      if (container) chartResizeObserver.observe(container)
    }
  }
  window.addEventListener('resize', scheduleChartResize)
  scheduleChartResize()

  // 成绩数据加载完成后及时刷新，而不是等用户滚动或缩放窗口。
  void Promise.allSettled([loadArchiveData(), loadAcademicData()]).then(async () => {
    await nextTick()
    if (!chartsMounted) return
    updateAcademicCharts()
    scheduleChartResize()
  })
})

onUnmounted(() => {
  chartsMounted = false
  chartResizeObserver?.disconnect()
  chartResizeObserver = null
  if (chartResizeFrame !== null) {
    cancelAnimationFrame(chartResizeFrame)
    chartResizeFrame = null
  }
  window.removeEventListener('resize', scheduleChartResize)
  gradeChart?.dispose()
  employmentChart?.dispose()
  scoreDistributionChart?.dispose()
  majorScoreChart?.dispose()
  gradeScoreChart?.dispose()
  document.body.style.overflow = ''
})

function handleResize() {
  gradeChart?.resize()
  employmentChart?.resize()
  scoreDistributionChart?.resize()
  majorScoreChart?.resize()
  gradeScoreChart?.resize()
}
</script>

<style scoped>
/* ============================================================
   STUDENT HUB — 学生画像与成长分析中心 样式
   设计方向：智慧校园用户画像平台 / 数据化 / 卡片化
   主色调：蓝系 (#1E3A8A → #93C5FD) 与课程管理保持一致
   ============================================================ */

/* ---- Layout ---- */
.student-hub {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0;
}

/* ---- Topbar (shared with course-hub) ---- */
.hub-topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}
.hub-title-area {
  flex: 1;
  min-width: 260px;
}
.hub-title {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-title);
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  line-height: 1.3;
}
.hub-title-icon {
  width: 22px;
  height: 22px;
  color: var(--color-primary);
  flex-shrink: 0;
}
.hub-subtitle {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 4px;
}
.hub-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

/* ---- Linked grade / major filters ---- */
.student-filter-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.student-filter {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 36px;
  padding: 5px 10px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  background: #FFFFFF;
}

.student-filter > span {
  flex-shrink: 0;
  color: #64748B;
  font-size: 12px;
  font-weight: 600;
}

.student-filter select {
  min-width: 116px;
  max-width: 230px;
  border: 0;
  outline: 0;
  background: transparent;
  color: #1F2937;
  font-size: 12px;
  cursor: pointer;
}

.student-filter:nth-child(2) select {
  min-width: 190px;
}

.hub-row-profile {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 16px;
}

/* ---- Buttons ---- */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: none;
  background: #1E3A8A;
  color: #FFF;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary svg {
  width: 16px;
  height: 16px;
}
.btn-primary:hover {
  background: #1E40AF;
  box-shadow: 0 2px 8px rgba(30, 58, 138, 0.3);
}
.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid #D1D5DB;
  background: #FFF;
  color: #374151;
  padding: 8px 18px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-outline svg {
  width: 16px;
  height: 16px;
}
.btn-outline:hover {
  background: #F9FAFB;
  border-color: #9CA3AF;
}

/* ---- Stat Row (4 cards) ---- */
.hub-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.hub-stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px 22px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
  transition: all 0.25s;
  cursor: default;
}
.hub-stat-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.hub-stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.hub-stat-icon svg {
  width: 20px;
  height: 20px;
}
.hub-stat-body {
  flex: 1;
  min-width: 0;
}
.hub-stat-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}
.hub-stat-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-top: 2px;
}
.hub-stat-num {
  font-size: 30px;
  font-weight: 700;
  color: var(--text-title);
  line-height: 1.1;
}
.hub-stat-unit {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 500;
}
.hub-stat-sub {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-scope {
  color: var(--text-muted);
  font-size: 11px;
}
.hub-stat-spark {
  position: absolute;
  bottom: 8px;
  right: 16px;
  opacity: 0.35;
  pointer-events: none;
}
.spark-svg {
  width: 60px;
  height: 22px;
}

/* ---- Grid Layouts ---- */
.hub-row-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* ---- Panel ---- */
.hub-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 20px 22px;
  display: flex;
  flex-direction: column;
}
.hub-cover-panel {
  overflow: hidden;
}
.hub-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}
.hub-panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-title);
  display: flex;
  align-items: center;
  gap: 8px;
}
.panel-title-icon {
  width: 16px;
  height: 16px;
  color: var(--color-primary);
  flex-shrink: 0;
}
.hub-panel-badge {
  font-size: 11px;
  background: #EFF6FF;
  color: var(--color-primary);
  padding: 3px 10px;
  border-radius: 6px;
  font-weight: 500;
  white-space: nowrap;
}
.hub-panel-badge.hover-tip {
  cursor: help;
  display: flex;
  align-items: center;
  gap: 4px;
}
.warning-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #DC2626;
  animation: pulse-dot 1.5s ease-in-out infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

/* ---- Chart Wrap ---- */
.hub-chart-wrap {
  flex: 1;
  min-height: 280px;
  width: 100%;
}

/* ---- Student Archive Management ---- */
.archive-panel {
  overflow: hidden;
}
.archive-filter-row {
  display: grid;
  grid-template-columns: 1fr 1.25fr 1fr 1fr 1.7fr;
  gap: 10px;
  padding: 14px;
  margin-bottom: 12px;
  border-radius: 10px;
  background: #F8FAFC;
  border: 1px solid #EEF2F7;
}
.archive-filter,
.archive-search {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
.archive-filter > span,
.archive-search > span {
  color: #64748B;
  font-size: 11px;
  font-weight: 600;
}
.archive-filter select,
.archive-search input,
.archive-form-field input,
.archive-form-field select {
  width: 100%;
  min-width: 0;
  height: 36px;
  border: 1px solid #E2E8F0;
  border-radius: 7px;
  padding: 0 10px;
  background: #FFF;
  color: #334155;
  font-size: 12px;
  outline: none;
  transition: border-color .15s, box-shadow .15s;
}
.archive-filter select:focus,
.archive-search input:focus,
.archive-form-field input:focus,
.archive-form-field select:focus {
  border-color: #60A5FA;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, .10);
}
.archive-action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}
.archive-result-hint {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  color: #64748B;
  font-size: 11px;
}
.archive-result-hint strong {
  color: #1E3A8A;
  font-size: 13px;
}
.archive-loading-text { color: #2563EB; }
.archive-error-text { color: #DC2626; }
.archive-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.archive-action-btn {
  min-height: 34px;
  padding: 7px 12px;
  font-size: 11px;
}
.archive-action-btn svg {
  width: 14px;
  height: 14px;
}
.archive-file-input {
  display: none;
}
.archive-table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid #E8EDF4;
  border-radius: 9px;
}
.archive-table {
  width: 100%;
  min-width: 1040px;
  border-collapse: collapse;
  font-size: 12px;
  color: #475569;
}
.archive-table th {
  padding: 12px 11px;
  background: #F8FAFC;
  color: #64748B;
  font-size: 11px;
  font-weight: 600;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid #E8EDF4;
}
.archive-table td {
  padding: 12px 11px;
  border-bottom: 1px solid #F1F5F9;
  vertical-align: middle;
  white-space: nowrap;
}
.archive-table tbody tr:last-child td { border-bottom: 0; }
.archive-table tbody tr:hover { background: #FAFCFF; }
.archive-student-no {
  color: #1E3A8A;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
.archive-student-name {
  color: #1E293B;
  font-weight: 650;
}
.archive-secondary {
  margin-top: 3px;
  color: #94A3B8;
  font-size: 10px;
}
.archive-gpa-cell,
.academic-score-strong {
  color: #2563EB;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.archive-failed-count {
  color: #64748B;
  font-weight: 600;
}
.archive-failed-count.has-failed { color: #DC2626; }
.archive-status-tag {
  display: inline-flex;
  align-items: center;
  border-radius: 5px;
  padding: 3px 8px;
  font-size: 10px;
  font-weight: 600;
}
.archive-status-on {
  color: #059669;
  background: #ECFDF5;
}
.archive-status-off {
  color: #64748B;
  background: #F1F5F9;
}
.archive-row-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}
.archive-link-btn {
  border: 0;
  padding: 2px 0;
  background: transparent;
  color: #2563EB;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}
.archive-link-btn:hover { color: #1E3A8A; text-decoration: underline; }
.archive-empty-cell {
  padding: 28px 12px !important;
  text-align: center;
  color: #94A3B8;
}
.archive-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 12px;
  color: #94A3B8;
  font-size: 11px;
}
.archive-pagination-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}
.archive-page-btn {
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  background: #FFF;
  color: #475569;
  padding: 5px 10px;
  font-size: 11px;
  cursor: pointer;
}
.archive-page-btn:disabled {
  color: #CBD5E1;
  background: #F8FAFC;
  cursor: not-allowed;
}
.archive-data-note {
  margin-top: 10px;
  color: #94A3B8;
  font-size: 10px;
  line-height: 1.6;
}

/* Existing detail drawer still uses these tags. */
.profile-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
}

/* ---- Archive Dialogs ---- */
.archive-dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(15, 23, 42, .48);
  backdrop-filter: blur(2px);
}
.archive-dialog {
  width: min(620px, calc(100vw - 32px));
  max-height: min(90vh, 900px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, .9);
  border-radius: 14px;
  background: #FFF;
  box-shadow: 0 20px 60px rgba(15, 23, 42, .22);
}
.archive-dialog-wide { width: min(780px, calc(100vw - 32px)); }
.archive-dialog-detail { width: min(920px, calc(100vw - 32px)); }
.archive-dialog-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border-bottom: 1px solid #EEF2F7;
}
.archive-dialog-header h3 {
  margin: 0;
  color: #1E293B;
  font-size: 17px;
  font-weight: 700;
}
.archive-dialog-header p {
  margin: 6px 0 0;
  color: #94A3B8;
  font-size: 11px;
}
.archive-dialog-close {
  width: 30px;
  height: 30px;
  flex-shrink: 0;
  border: 1px solid #E2E8F0;
  border-radius: 7px;
  background: #FFF;
  color: #64748B;
  font-size: 21px;
  line-height: 1;
  cursor: pointer;
}
.archive-dialog-close:hover { background: #F8FAFC; color: #1E293B; }
.archive-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  padding: 20px 22px;
  overflow-y: auto;
}
.archive-form-field {
  display: flex;
  flex-direction: column;
  gap: 7px;
  min-width: 0;
  color: #64748B;
  font-size: 11px;
  font-weight: 600;
}
.archive-form-field em {
  color: #DC2626;
  font-style: normal;
}
.archive-checkbox-field {
  flex-direction: row;
  align-items: center;
  align-self: end;
  min-height: 36px;
}
.archive-checkbox-field input {
  width: 15px;
  height: 15px;
  accent-color: #2563EB;
}
.archive-dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 22px;
  border-top: 1px solid #EEF2F7;
  background: #FFF;
}
.archive-dialog-footer > div {
  display: flex;
  gap: 8px;
}
.archive-dialog-footer .btn-primary,
.archive-dialog-footer .btn-outline {
  min-height: 34px;
  padding: 7px 14px;
  font-size: 11px;
}
.archive-form-required {
  color: #94A3B8;
  font-size: 10px;
}
.archive-detail-section {
  padding: 16px 22px 0;
}
.archive-detail-section h4 {
  margin: 0 0 12px;
  color: #1E293B;
  font-size: 13px;
  font-weight: 700;
}
.archive-detail-section h4 small {
  margin-left: 6px;
  color: #94A3B8;
  font-size: 10px;
  font-weight: 400;
}
.archive-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.archive-detail-grid > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #F8FAFC;
  min-width: 0;
}
.archive-detail-grid span,
.archive-detail-kpis span {
  color: #94A3B8;
  font-size: 10px;
}
.archive-detail-grid strong {
  color: #334155;
  font-size: 12px;
  overflow-wrap: anywhere;
}
.archive-detail-kpis {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.archive-detail-kpis > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 12px;
  border-radius: 8px;
  background: #F8FAFC;
}
.archive-detail-kpis strong {
  color: #1E3A8A;
  font-size: 18px;
  font-weight: 700;
}
.archive-failed-course-list {
  margin: 10px 0 0;
  color: #DC2626;
  font-size: 11px;
}
.archive-detail-table-wrap {
  max-height: 260px;
  overflow: auto;
  border: 1px solid #E8EDF4;
  border-radius: 8px;
}
.archive-detail-table { min-width: 650px; }
.archive-import-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  padding: 18px 22px;
}
.archive-import-summary > div {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  border-radius: 8px;
  background: #F8FAFC;
}
.archive-import-summary span {
  color: #94A3B8;
  font-size: 10px;
}
.archive-import-summary strong {
  color: #1E3A8A;
  font-size: 20px;
}
.archive-import-errors {
  margin: 0 22px;
  padding: 12px 14px;
  border: 1px solid #FECACA;
  border-radius: 8px;
  background: #FEF2F2;
}
.archive-import-errors h4 {
  margin: 0 0 8px;
  color: #B91C1C;
  font-size: 12px;
}
.archive-import-errors ul {
  max-height: 140px;
  overflow: auto;
  margin: 0;
  padding-left: 18px;
  color: #991B1B;
  font-size: 10px;
  line-height: 1.7;
}
.archive-import-errors p {
  margin: 8px 0 0;
  color: #B91C1C;
  font-size: 10px;
}
.archive-import-note {
  padding: 14px 22px;
  color: #64748B;
  font-size: 11px;
  line-height: 1.6;
}

/* ---- GPA Color System ---- */
.gpa-excellent { color: #1E3A8A; }
.gpa-good { color: #3B82F6; }
.gpa-warning { color: #D97706; }
.gpa-danger { color: #DC2626; }

/* ---- Warning List ---- */
.warning-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 480px;
  overflow-y: auto;
  scrollbar-width: thin;
}

.student-empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 180px;
  color: #94A3B8;
  font-size: 13px;
  text-align: center;
}
.warning-list::-webkit-scrollbar {
  width: 4px;
}
.warning-list::-webkit-scrollbar-thumb {
  background: #D1D5DB;
  border-radius: 2px;
}
.warning-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}
.warning-item:hover {
  background: #F9FAFB;
}
.warning-item.severity-high {
  border-left-color: #DC2626;
  background: #FEF2F2;
}
.warning-item.severity-mid {
  border-left-color: #F59E0B;
  background: #FFFBEB;
}
.warning-item.severity-low {
  border-left-color: #3B82F6;
}
.warning-rank {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #F3F4F6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.severity-high .warning-rank {
  background: #DC2626;
  color: #FFF;
}
.severity-mid .warning-rank {
  background: #F59E0B;
  color: #FFF;
}
.warning-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}
.warning-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-title);
}
.warning-college {
  font-size: 11px;
  color: var(--text-muted);
}
.warning-metrics {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}
.warning-metric-row {
  text-align: center;
}
.warning-m-label {
  display: block;
  font-size: 9px;
  color: var(--text-muted);
}
.warning-m-value {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-title);
}
.warning-m-value.danger-val {
  color: #DC2626;
}
.warning-m-value.warn-val {
  color: #D97706;
}
.warning-severity-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}
.sev-high { background: #FEF2F2; color: #DC2626; }
.sev-mid { background: #FFFBEB; color: #D97706; }
.sev-low { background: #EFF6FF; color: #3B82F6; }
.warning-action-btn {
  border: 1px solid #D1D5DB;
  background: #FFF;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
  color: #374151;
  flex-shrink: 0;
  transition: all 0.15s;
}
.warning-action-btn:hover {
  background: #F3F4F6;
  border-color: #9CA3AF;
}

/* ---- Trend Legend ---- */
.trend-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-muted);
  flex-wrap: wrap;
}
.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* ---- Academic Grade Analysis ---- */
.academic-analysis-panel {
  overflow: hidden;
}
.academic-filter-row {
  display: grid;
  grid-template-columns: 1.3fr 1fr 1fr;
  gap: 8px;
  padding: 10px;
  margin-bottom: 12px;
  border: 1px solid #EEF2F7;
  border-radius: 9px;
  background: #F8FAFC;
}
.academic-filter-row label {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}
.academic-filter-row label span {
  color: #64748B;
  font-size: 10px;
  font-weight: 600;
}
.academic-filter-row select {
  width: 100%;
  min-width: 0;
  height: 32px;
  padding: 0 8px;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  background: #FFF;
  color: #334155;
  font-size: 10px;
  outline: none;
}
.academic-filter-row select:focus {
  border-color: #60A5FA;
}
.academic-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}
.academic-kpi-card {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
  padding: 10px;
  border: 1px solid #EEF2F7;
  border-radius: 8px;
  background: #F8FAFC;
}
.academic-kpi-label {
  color: #94A3B8;
  font-size: 10px;
  line-height: 1.4;
}
.academic-kpi-card strong {
  color: #1E3A8A;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}
.academic-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}
.academic-chart-card {
  min-width: 0;
  padding: 9px 10px 4px;
  border: 1px solid #EEF2F7;
  border-radius: 8px;
  background: #FFF;
}
.academic-chart-card-wide {
  grid-column: 1 / -1;
}
.academic-chart-title {
  color: #334155;
  font-size: 11px;
  font-weight: 650;
}
.academic-chart {
  width: 100%;
  height: 150px;
}
.academic-chart-short {
  height: 125px;
}
.academic-course-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #EEF2F7;
}
.academic-course-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.academic-course-heading strong {
  color: #1E293B;
  font-size: 12px;
}
.academic-course-heading span {
  color: #94A3B8;
  font-size: 10px;
}
.academic-course-table-wrap {
  max-height: 210px;
  overflow: auto;
  border: 1px solid #E8EDF4;
  border-radius: 8px;
}
.academic-course-table {
  width: 100%;
  min-width: 610px;
  border-collapse: collapse;
  color: #475569;
  font-size: 10px;
}
.academic-course-table th {
  padding: 9px 8px;
  background: #F8FAFC;
  color: #64748B;
  font-size: 10px;
  font-weight: 600;
  text-align: left;
  white-space: nowrap;
  border-bottom: 1px solid #E8EDF4;
}
.academic-course-table td {
  padding: 9px 8px;
  border-bottom: 1px solid #F1F5F9;
  white-space: nowrap;
}
.academic-course-table tbody tr:last-child td { border-bottom: 0; }
.academic-course-name {
  color: #334155;
  font-weight: 600;
}
.academic-pass-rate {
  color: #059669;
  font-weight: 650;
}
.academic-low-rate {
  color: #DC2626;
  font-weight: 650;
}
.academic-unpublished-note,
.academic-data-note,
.academic-state-message {
  margin-top: 9px;
  padding: 9px 10px;
  border-radius: 7px;
  background: #F8FAFC;
  color: #64748B;
  font-size: 10px;
  line-height: 1.6;
}
.academic-unpublished-note {
  background: #FFFBEB;
  color: #B45309;
}
.academic-state-error {
  background: #FEF2F2;
  color: #B91C1C;
}

/* ---- Timeline ---- */
.timeline-wrap {
  display: flex;
  flex-direction: column;
}
.timeline-item {
  display: flex;
  gap: 14px;
  position: relative;
}
.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 24px;
}
.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #E5E7EB;
  border: 2px solid #FFF;
  box-shadow: 0 0 0 2px #E5E7EB;
  flex-shrink: 0;
  margin-top: 4px;
  z-index: 1;
  transition: all 0.3s;
}
.timeline-dot.dot-active {
  background: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.25);
  animation: pulse-ring 2s ease-in-out infinite;
}
.timeline-dot.dot-done {
  background: #3B82F6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}
@keyframes pulse-ring {
  0%, 100% { box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.25); }
  50% { box-shadow: 0 0 0 8px rgba(30, 58, 138, 0.05); }
}
.timeline-line {
  width: 2px;
  flex: 1;
  min-height: 28px;
  background: #E5E7EB;
  margin-top: 4px;
}
.timeline-line.line-done {
  background: #3B82F6;
}
.timeline-content {
  flex: 1;
  padding-bottom: 16px;
  min-width: 0;
}
.timeline-item:last-child .timeline-content {
  padding-bottom: 0;
}
.timeline-date {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 500;
}
.timeline-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-title);
  margin-top: 2px;
}
.timeline-desc {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.4;
}
.timeline-stats {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.timeline-stat {
  font-size: 10px;
  background: #EFF6FF;
  color: var(--text-secondary);
  padding: 2px 8px;
  border-radius: 4px;
}
.timeline-stat strong {
  color: var(--color-primary);
}
.timeline-active .timeline-title {
  color: var(--color-primary);
}
.timeline-active .timeline-content {
  background: linear-gradient(135deg, rgba(239, 246, 255, 0.6), transparent);
  border-radius: 8px;
  padding: 8px 10px;
  margin-left: -10px;
}

/* ---- Honor Grid ---- */
.honor-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.honor-card {
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 16px 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s;
  position: relative;
  overflow: hidden;
}
.honor-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  transform: translateY(-3px);
}
.honor-card.honor-rank-1 {
  border-color: #1E3A8A;
  box-shadow: 0 2px 12px rgba(30, 58, 138, 0.12);
}
.honor-badge-wrap {
  position: absolute;
  top: 0;
  right: 0;
}
.honor-badge {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0 0 0 12px;
  font-size: 14px;
  font-weight: 800;
  color: #FFF;
}
.badge-1 { background: #1E3A8A; }
.badge-2 { background: #2563EB; }
.badge-3 { background: #3B82F6; }
.badge-4, .badge-5, .badge-6 { background: #93C5FD; }
.honor-crown {
  width: 18px;
  height: 18px;
}
.honor-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 8px;
  color: #FFF;
  font-size: 18px;
  font-weight: 700;
}
.honor-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-title);
  margin: 0 0 2px;
}
.honor-college {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0 0 8px;
}
.honor-highlight {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 8px;
}
.honor-gpa {
  font-size: 14px;
  font-weight: 700;
  color: #1E3A8A;
  background: #EFF6FF;
  padding: 2px 10px;
  border-radius: 6px;
}
.honor-award {
  font-size: 11px;
  color: #D97706;
  background: #FFFBEB;
  padding: 2px 10px;
  border-radius: 6px;
  font-weight: 600;
}
.honor-tags {
  display: flex;
  gap: 4px;
  justify-content: center;
  flex-wrap: wrap;
}
.honor-tag {
  font-size: 10px;
  background: #F3F4F6;
  color: var(--text-secondary);
  padding: 2px 7px;
  border-radius: 4px;
  font-weight: 500;
}

/* ---- Class Comparison Table ---- */
.class-compare-scroll {
  overflow-x: auto;
  scrollbar-width: thin;
}
.class-compare-scroll::-webkit-scrollbar {
  height: 4px;
}
.class-compare-scroll::-webkit-scrollbar-thumb {
  background: #D1D5DB;
  border-radius: 2px;
}
.class-compare-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}
.class-compare-table th {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #F3F4F6;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  white-space: nowrap;
}
.class-compare-table td {
  padding: 12px;
  border-bottom: 1px solid #F9FAFB;
  font-size: 13px;
  color: var(--text-body);
}
.class-compare-table tbody tr {
  transition: background 0.15s;
}
.class-compare-table tbody tr:hover {
  background: #F9FAFB;
}
.class-compare-table tbody tr.top-row {
  background: #EFF6FF;
}
.class-name-cell {
  font-weight: 600;
  color: var(--text-title);
  display: flex;
  align-items: center;
  gap: 8px;
}
.class-rank-dot {
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: #F3F4F6;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.class-rank-dot.rank-1 { background: #1E3A8A; color: #FFF; }
.class-rank-dot.rank-2 { background: #2563EB; color: #FFF; }
.class-rank-dot.rank-3 { background: #3B82F6; color: #FFF; }
.compare-gpa {
  font-weight: 700;
}
.compare-bar-mini {
  display: inline-block;
  width: 60px;
  height: 6px;
  background: #F3F4F6;
  border-radius: 3px;
  overflow: hidden;
  vertical-align: middle;
  margin-right: 6px;
}
.compare-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}
.compare-pct {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 600;
}
.compare-warn {
  font-weight: 700;
}
.compare-warn.has-warning {
  color: #DC2626;
}
.compare-award-num {
  font-weight: 700;
  color: #D97706;
}
.compare-rank-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 6px;
}
.compare-rank-badge.overall-top {
  background: #EFF6FF;
  color: #1E3A8A;
}
.compare-rank-badge.overall-normal {
  background: #F3F4F6;
  color: #6B7280;
}

/* ---- ======== DRAWER ======== ---- */
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
  animation: fadeIn 0.2s ease;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.drawer-panel {
  width: 480px;
  max-width: 90vw;
  background: #FFF;
  height: 100%;
  overflow-y: auto;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.12);
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
}
.drawer-panel.drawer-open {
  transform: translateX(0);
}
.drawer-header {
  padding: 24px;
  border-bottom: 1px solid #F3F4F6;
  flex-shrink: 0;
}
.drawer-header-top {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}
.drawer-avatar-lg {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #FFF;
  font-size: 28px;
  font-weight: 700;
  flex-shrink: 0;
}
.drawer-title-area {
  flex: 1;
  min-width: 0;
}
.drawer-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-title);
  margin: 0 0 2px;
}
.drawer-id {
  font-size: 12px;
  color: var(--text-muted);
  margin: 0 0 8px;
}
.drawer-status-row {
  display: flex;
  gap: 8px;
}
.drawer-status-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 6px;
}
.drawer-status-tag.status-progress { background: #ECFDF5; color: #059669; }
.drawer-status-tag.status-pending { background: #FEF3C7; color: #D97706; }
.drawer-status-tag.status-ended { background: #FEF2F2; color: #DC2626; }
.drawer-status-tag.status-suspended { background: #F3F4F6; color: #6B7280; }
.drawer-risk-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 6px;
}
.drawer-risk-tag.risk-high { background: #FEF2F2; color: #DC2626; }
.drawer-risk-tag.risk-mid { background: #FFFBEB; color: #D97706; }
.drawer-risk-tag.risk-low { background: #ECFDF5; color: #059669; }
.drawer-close-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  background: #FFF;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}
.drawer-close-btn svg {
  width: 18px;
  height: 18px;
  color: #6B7280;
}
.drawer-close-btn:hover {
  background: #F9FAFB;
  border-color: #D1D5DB;
}
.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.drawer-section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-title);
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.drawer-section-title::before {
  content: '';
  display: block;
  width: 4px;
  height: 14px;
  background: var(--color-primary);
  border-radius: 2px;
}
.drawer-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.drawer-info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  background: #F9FAFB;
  border-radius: 8px;
}
.di-label {
  font-size: 10px;
  color: var(--text-muted);
  font-weight: 500;
}
.di-value {
  font-size: 13px;
  color: var(--text-title);
  font-weight: 600;
}
.drawer-metrics-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 8px;
}
.drawer-metric-card {
  text-align: center;
  background: #F9FAFB;
  border-radius: 8px;
  padding: 10px 6px;
}
.dm-label {
  display: block;
  font-size: 10px;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.dm-value {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-title);
}
.dm-value.danger-val {
  color: #DC2626;
}
.drawer-tags-wrap {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.drawer-timeline-mini {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 4px;
}
.dtm-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}
.dtm-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  flex-shrink: 0;
  margin-top: 4px;
}
.dtm-content {
  display: flex;
  flex-direction: column;
}
.dtm-date {
  font-size: 10px;
  color: var(--text-muted);
}
.dtm-text {
  font-size: 12px;
  color: var(--text-body);
}
.drawer-footer {
  padding: 16px 24px;
  border-top: 1px solid #F3F4F6;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  flex-shrink: 0;
}

/* ---- Responsive ---- */
@media (max-width: 1600px) {
  .hub-stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .honor-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 1200px) {
  .hub-row-2col {
    grid-template-columns: 1fr;
  }
  .honor-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
@media (max-width: 768px) {
  .hub-actions {
    width: 100%;
  }
  .student-filter-group {
    width: 100%;
  }
  .student-filter {
    flex: 1;
    min-width: 0;
  }
  .student-filter select,
  .student-filter:nth-child(2) select {
    min-width: 0;
    width: 100%;
    max-width: none;
  }
  .hub-stats-row {
    grid-template-columns: 1fr;
  }
  .hub-stat-card {
    padding: 14px 16px;
  }
  .hub-stat-num {
    font-size: 24px;
  }
  .honor-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .drawer-panel {
    width: 100vw;
    max-width: 100vw;
  }
  .drawer-metrics-row {
    grid-template-columns: 1fr 1fr;
  }
}

.archive-import-result {
  margin: 0 22px 10px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #ECFDF5;
  color: #047857;
  font-size: 11px;
  line-height: 1.6;
}
.archive-dialog-detail {
  overflow-y: auto;
}
.archive-dialog-detail .archive-dialog-header {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #FFF;
}
.archive-dialog-detail .archive-dialog-footer {
  position: sticky;
  bottom: 0;
  z-index: 2;
}
.archive-dialog-wide form {
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.archive-dialog-wide .archive-form-grid {
  flex: 1;
}

@media (max-width: 1200px) {
  .archive-filter-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .archive-search {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .archive-filter-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    padding: 10px;
  }
  .archive-search {
    grid-column: 1 / -1;
  }
  .archive-action-row {
    align-items: flex-start;
    flex-direction: column;
  }
  .archive-actions {
    width: 100%;
  }
  .archive-action-btn {
    flex: 1;
    justify-content: center;
  }
  .archive-pagination {
    align-items: flex-start;
    flex-direction: column;
  }
  .academic-filter-row {
    grid-template-columns: 1fr;
  }
  .academic-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .academic-chart-grid {
    grid-template-columns: 1fr;
  }
  .academic-chart-card-wide {
    grid-column: auto;
  }
  .archive-dialog-overlay {
    padding: 10px;
  }
  .archive-form-grid,
  .archive-detail-grid {
    grid-template-columns: 1fr;
  }
  .archive-import-summary {
    grid-template-columns: repeat(2, 1fr);
  }
  .archive-dialog-footer {
    align-items: flex-start;
    flex-direction: column;
  }
  .archive-dialog-footer > div {
    width: 100%;
  }
  .archive-dialog-footer > div button {
    flex: 1;
  }
}

</style>
