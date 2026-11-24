<template>
  <!-- ============================================================
       教师资源与教学能力中心 — 专家库风格 / 人员画像 / 学术感
       布局：统计卡片 → 教师画像卡片+职称分布 → 工作量排行+科研成果
             → 课程关系图+本月优秀教师 → 年龄结构+考核评分 → 课时热力图+教学团队
  ============================================================ -->
  <div class="faculty-hub">
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
           教师资源与教学能力中心
         </h2>
         <p class="hub-subtitle">政治学与公共管理学院 · 专家人才库 · 师资画像 · 学术能力评估 · 教学团队管理</p>
      </div>
      <div class="hub-actions">
        <div class="chip-group" style="flex-wrap:wrap" role="group" aria-label="按所属系所筛选官网教师画像">
          <button v-for="option in majorOptions" :key="option" type="button"
            class="chip-filter" :class="{ active: majorFilter === option }"
            :title="option || '全部系所'" :aria-pressed="majorFilter === option" @click="majorFilter = option">
            {{ option === '科社系、当代社会主义研究基地' ? '科社系/基地' : option || '全部系所' }}
          </button>
        </div>
        <button class="btn-primary" type="button" @click="openTalentModal">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          引进人才
        </button>
        <button class="btn-outline" type="button" :disabled="facultyExporting" @click="exportFacultyReport">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          {{ facultyExporting ? '正在生成报表…' : '导出师资报表' }}
        </button>
      </div>
    </div>
    <div v-if="facultyNotice" class="faculty-operation-notice" role="status">
      <span>{{ facultyNotice }}</span>
      <button type="button" aria-label="关闭提示" @click="facultyNotice = ''">×</button>
    </div>

    <!-- ========== 第1行：4 统计卡片 ========== -->
    <div class="hub-stats-row">
      <div class="hub-stat-card" v-for="stat in facultyStats" :key="stat.label">
        <div class="hub-stat-icon" :style="{ background: stat.bg, color: stat.color }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path :d="stat.icon"/></svg>
        </div>
        <div class="hub-stat-body">
          <div class="hub-stat-label">{{ stat.label }}</div>
          <div class="hub-stat-value">
            <span class="hub-stat-num">{{ stat.value }}</span>
            <span class="hub-stat-unit">{{ stat.unit }}</span>
          </div>
          <div class="hub-stat-sub">{{ stat.sub }}</div>
        </div>
        <div class="hub-stat-spark">
          <svg viewBox="0 0 80 28" class="spark-svg">
            <polyline :points="stat.sparkline" fill="none" :stroke="stat.color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
    </div>

    <!-- ========== 第2行：教师画像卡片(3列) + 职称分布图 ========== -->
    <div class="hub-row-2col">
      <!-- 1. 教师信息卡片 (3列网格) -->
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            教师画像（官网档案）
          </span>
          <span class="hub-panel-badge">{{ directoryReady ? filteredDirectory.length : '—' }} 位</span>
        </div>
        <div class="profile-grid">
          <div
            class="profile-card"
            v-for="tp in filteredTeacherProfiles"
            :key="tp.id"
            role="button"
            tabindex="0"
            :aria-label="'查看' + tp.name + '的教师详细资料'"
            @click="openTeacherDetail(tp)"
            @keydown.enter.prevent="openTeacherDetail(tp)"
            @keydown.space.prevent="openTeacherDetail(tp)"
          >
            <div class="profile-avatar" :class="'avatar-' + tp.level">
              <img v-if="tp.photoUrl && !failedPortraits[tp.photoUrl]" :src="tp.photoUrl" alt="" class="teacher-official-portrait" loading="lazy" @error="markPortraitFailed(tp.photoUrl)" />
              <span v-else class="profile-initials">{{ tp.name.slice(0, 2) }}</span>
              <div class="profile-level-dot"></div>
            </div>
            <div class="profile-info">
              <span class="profile-name">{{ tp.name }}</span>
              <span class="profile-title-tag">{{ tp.title }}</span>
              <span class="profile-college">{{ tp.major }}</span>
            </div>
            <div class="profile-meta">
              <div class="pm-item"><span class="pm-num">{{ tp.courses }}</span><span class="pm-label">授课</span></div>
              <div class="pm-item"><span class="pm-num">{{ tp.students }}</span><span class="pm-label">学生</span></div>
              <div class="pm-item"><span class="pm-num" :class="tp.rating !== null && tp.rating >= 4.5 ? 'pm-high' : ''">{{ tp.rating ?? '—' }}</span><span class="pm-label">评分</span></div>
            </div>
            <div class="profile-bar">
              <div class="profile-bar-fill" :style="{ width: tp.rating === null ? '0%' : (tp.rating / 5 * 100) + '%', background: tp.barColor }"></div>
            </div>
          </div>
          <div v-if="filteredTeacherProfiles.length === 0" class="profile-filter-empty">
            {{ directoryLoading ? '正在读取官网师资档案…' : directoryError || '当前系所暂无官网师资档案。' }}
          </div>
        </div>
        <div v-if="filteredDirectory.length > 6" style="display:flex;align-items:center;justify-content:flex-end;gap:8px;padding-top:10px">
          <button type="button" class="chip-filter" :disabled="profilePage <= 1" @click="profilePage--">上一页</button>
          <span class="hub-panel-badge">{{ profilePage }} / {{ profilePageCount }}</span>
          <button type="button" class="chip-filter" :disabled="profilePage >= profilePageCount" @click="profilePage++">下一页</button>
        </div>
      </div>

      <!-- 2. 职称分布图 (ECharts 南丁格尔玫瑰饼图) -->
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <path d="M21.21 15.89A10 10 0 1 1 8 2.83"/>
              <path d="M22 12A10 10 0 0 0 12 2v10z"/>
            </svg>
            职称结构分布
          </span>
          <span class="hub-panel-badge">共 {{ totalTeachers }} 人</span>
        </div>
        <div class="hub-chart-wrap" ref="titleDistChartRef"></div>
      </div>
    </div>

    <!-- ========== 第3行：教学工作量排行 + 科研成果统计 ========== -->
    <div class="hub-row-2col">
      <!-- 3. 教学工作量排行 (ECharts 横向排序柱状) -->
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
            </svg>
            教学工作量排行
          </span>
          <span class="hub-panel-badge">周课时 · 演示</span>
        </div>
        <div class="hub-chart-wrap" ref="workloadChartRef"></div>
      </div>

      <!-- 4. 科研成果统计 (科研驾驶舱风格) -->
      <div class="hub-panel hub-panel--research">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            科研成果统计
          </span>
          <span class="hub-panel-badge">2025年度 · 演示数据</span>
        </div>
        <!-- 上方：科研成果总览 — 6 横向指标卡片 -->
        <div class="research-overview">
          <div class="research-indicator" v-for="ind in researchIndicators" :key="ind.label">
            <div class="ri-header">
              <span class="ri-label">{{ ind.label }}</span>
              <span class="ri-trend" :class="ind.trendUp ? 'trend-up' : 'trend-down'">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ri-trend-icon">
                  <polyline v-if="ind.trendUp" points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                  <polyline v-else points="23 18 13.5 8.5 8.5 13.5 1 6"/>
                </svg>
                {{ ind.trendText }}
              </span>
            </div>
            <div class="ri-value-row">
              <span class="ri-value">{{ ind.value }}</span>
              <span class="ri-unit">{{ ind.unit }}</span>
            </div>
            <div class="ri-progress-wrap">
              <div class="ri-progress-bar">
                <div class="ri-progress-fill" :style="{ width: ind.progress + '%', background: ind.color }"></div>
              </div>
              <span class="ri-progress-label">{{ ind.progressLabel }}</span>
            </div>
            <div class="ri-sparkline">
              <svg viewBox="0 0 100 24" class="ri-spark-svg">
                <polyline :points="ind.sparkline" fill="none" :stroke="ind.color" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polygon :points="ind.sparkline + ' 100,24 0,24'" :fill="ind.color" opacity="0.08"/>
              </svg>
            </div>
          </div>
        </div>
        <!-- 下方：科研成果趋势图 + 教师科研贡献排行 -->
        <div class="research-charts-row">
          <!-- 科研成果趋势图 -->
          <div class="research-chart-panel">
            <div class="rch-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="rch-title-icon">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
              科研成果趋势
            </div>
            <div class="rch-chart-wrap" ref="researchTrendChartRef"></div>
          </div>
          <!-- 教师科研贡献排行 -->
          <div class="research-chart-panel">
            <div class="rch-title">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="rch-title-icon">
                <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
              教师科研贡献排行
            </div>
            <div class="rch-chart-wrap" ref="researchRankChartRef"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 第4行：教师课程关系图 + 本月优秀教师 ========== -->
    <div class="hub-row-2col">
      <!-- 5. 教师课程关系图 (ECharts 力导向图) -->
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>
              <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
            </svg>
            教师-课程关系网络
          </span>
          <span class="hub-panel-badge">演示图谱</span>
        </div>
        <div class="hub-chart-wrap" ref="relationChartRef"></div>
      </div>

      <!-- 6. 本月优秀教师 -->
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            本月优秀教师
          </span>
          <span class="hub-panel-badge">2025年5月 · 演示</span>
        </div>
        <div class="star-teachers">
          <div class="star-item" v-for="(st, idx) in starTeachers" :key="st.name">
            <div class="star-medal" :class="'medal-' + (idx + 1)">
              <span v-if="idx === 0">🏆</span>
              <span v-else-if="idx === 1">🥈</span>
              <span v-else-if="idx === 2">🥉</span>
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <div class="star-info">
              <span class="star-name">{{ st.name }}</span>
              <span class="star-college">{{ st.college }}</span>
            </div>
            <div class="star-metrics">
              <div class="sm-col">
                <span class="sm-val">{{ st.rating }}</span>
                <span class="sm-label">评分</span>
              </div>
              <div class="sm-col">
                <span class="sm-val">{{ st.courses }}</span>
                <span class="sm-label">课程</span>
              </div>
              <div class="sm-col">
                <span class="sm-val">{{ st.students }}</span>
                <span class="sm-label">学生</span>
              </div>
            </div>
            <div class="star-comment">"{{ st.comment }}"</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 第5行：教师年龄结构 + 考核评分 ========== -->
    <div class="hub-row-2col">
      <!-- 7. 教师年龄结构 (ECharts 金字塔/双向柱状) -->
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/>
            </svg>
            教师年龄结构
          </span>
          <span class="hub-panel-badge">演示 · 平均 {{ avgAge }} 岁</span>
        </div>
        <div class="hub-chart-wrap" ref="ageChartRef"></div>
      </div>

      <!-- 8. 教师考核评分 (ECharts 散点/气泡图风格) -->
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/>
            </svg>
            教师考核评分
          </span>
          <span class="hub-panel-badge">综合考评 · 演示</span>
        </div>
        <div class="hub-chart-wrap" ref="evalChartRef"></div>
      </div>
    </div>

    <!-- ========== 第6行：课时热力图 + 教学团队分析 ========== -->
    <div class="hub-row-2col">
      <!-- 9. 教师课时热力图 (CSS 网格热力图) -->
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            教师课时热力图（演示）
          </span>
          <div class="heatmap-legend">
            <span>低</span>
            <span class="heatmap-legend-bar" v-for="i in 5" :key="i" :class="'hl-' + i"></span>
            <span>高</span>
          </div>
        </div>
        <div class="heatmap-grid">
          <div class="heatmap-row" v-for="(row, ri) in heatmapData" :key="ri">
            <span class="hm-teacher">{{ row.teacher }}</span>
            <span class="hm-cell" v-for="(cell, ci) in row.hours" :key="ci"
              :class="'hm-level-' + getHeatLevel(cell)"
              :title="row.teacher + ' ' + weekLabels[ci] + ': ' + cell + '课时'">
              {{ cell }}
            </span>
          </div>
          <div class="heatmap-header-row">
            <span class="hm-teacher"></span>
            <span class="hm-col-label" v-for="(wl, wi) in weekLabels" :key="wi">{{ wl }}</span>
          </div>
        </div>
      </div>

      <!-- 10. 教学团队分析 -->
      <div class="hub-panel">
        <div class="hub-panel-header">
          <span class="hub-panel-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="panel-title-icon">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            教学团队分析
          </span>
          <span class="hub-panel-badge">{{ teams.length }} 个演示团队</span>
        </div>
        <div class="team-list">
          <div class="team-item" v-for="team in teams" :key="team.name">
            <div class="team-header-row">
              <span class="team-name">{{ team.name }}</span>
              <span class="team-leader">负责人：{{ team.leader }}</span>
            </div>
            <div class="team-members">
              <span class="team-avatar-sm" v-for="m in team.members" :key="m" :title="m">{{ m.slice(-2) }}</span>
            </div>
            <div class="team-stats">
              <div class="ts-item">
                <span class="ts-val">{{ team.courses }}</span><span class="ts-label">课程</span>
              </div>
              <div class="ts-item">
                <span class="ts-val">¥{{ team.funding }}</span><span class="ts-label">经费(万)</span>
              </div>
              <div class="ts-item">
                <span class="ts-val">{{ team.papers }}</span><span class="ts-label">论文</span>
              </div>
              <div class="team-strength">
                <div class="ts-bar-bg"><div class="ts-bar-fill" :style="{ width: team.strength + '%' }"></div></div>
                <span class="ts-strength-label">实力 {{ team.strength }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  <Teleport to="body">
    <div
      v-if="selectedProfile"
      class="teacher-drawer-overlay"
      @click.self="closeTeacherDetail"
    >
      <aside
        class="teacher-drawer-panel"
        role="dialog"
        aria-modal="true"
        :aria-label="selectedProfile.name + '教师详细资料'"
      >
        <header class="teacher-drawer-header">
          <div class="teacher-drawer-header-main">
            <div class="teacher-drawer-avatar" :class="'avatar-' + selectedProfile.level">
              <img v-if="selectedProfile.photoUrl && !failedPortraits[selectedProfile.photoUrl]" :src="selectedProfile.photoUrl" alt="" class="teacher-official-portrait" @error="markPortraitFailed(selectedProfile.photoUrl)" />
              <span v-else>{{ selectedProfile.name.slice(0, 2) }}</span>
            </div>
            <div class="teacher-drawer-title">
              <h3>{{ selectedProfile.name }}</h3>
              <p>{{ selectedProfile.teacherNo }} · {{ selectedProfile.title }}</p>
              <div class="teacher-drawer-status-row">
                <span class="teacher-drawer-status">官网档案</span>
                <span class="teacher-drawer-title-badge">{{ selectedProfile.title }}</span>
              </div>
            </div>
            <button
              type="button"
              class="teacher-drawer-close"
              aria-label="关闭教师详情"
              title="关闭"
              @click="closeTeacherDetail"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </header>

        <div class="teacher-drawer-body">
          <section class="teacher-drawer-section">
            <h4 class="teacher-drawer-section-title">基本信息</h4>
            <div class="teacher-drawer-info-grid">
              <div class="teacher-drawer-info-item">
                <span>所属学院</span>
                <strong>政治学与公共管理学院</strong>
              </div>
              <div class="teacher-drawer-info-item">
                <span>所属系所</span>
                <strong>{{ selectedProfile.major }}</strong>
              </div>
              <div class="teacher-drawer-info-item">
                <span>职称</span>
                <strong>{{ selectedProfile.title }}</strong>
              </div>
              <div class="teacher-drawer-info-item">
                <span>本地档案编号</span>
                <strong>{{ selectedProfile.teacherNo }}</strong>
              </div>
              <div class="teacher-drawer-info-item">
                <span>入职年份</span>
                <strong>{{ selectedProfile.joinYear }}</strong>
              </div>
              <div class="teacher-drawer-info-item">
                <span>办公地点</span>
                <strong>{{ selectedProfile.office }}</strong>
              </div>
              <div class="teacher-drawer-info-item teacher-drawer-info-wide">
                <span>研究方向</span>
                <strong>{{ selectedProfile.researchFocus }}</strong>
              </div>
            </div>
            <p class="teacher-drawer-intro" style="white-space:pre-line">{{ selectedProfile.researchSummary }}</p>
            <p v-if="selectedProfile.profileUrl" class="teacher-drawer-intro"><a :href="selectedProfile.profileUrl" target="_blank" rel="noopener noreferrer">查看官方个人主页</a></p>
          </section>

          <section class="teacher-drawer-section">
            <h4 class="teacher-drawer-section-title">教学数据（未核实指标显示 —）</h4>
            <div class="teacher-drawer-metrics">
              <div class="teacher-drawer-metric">
                <span>授课门次</span>
                <strong>{{ selectedProfile.courses }}</strong>
              </div>
              <div class="teacher-drawer-metric">
                <span>授课学生</span>
                <strong>{{ selectedProfile.students }}</strong>
              </div>
              <div class="teacher-drawer-metric">
                <span>学生评教</span>
                <strong>{{ selectedProfile.rating === null ? '—' : selectedProfile.rating.toFixed(1) }}<small>/5.0</small></strong>
              </div>
              <div class="teacher-drawer-metric">
                <span>学期课时</span>
                <strong>{{ selectedProfile.teachingHours }}<small>课时</small></strong>
              </div>
            </div>
            <div class="teacher-drawer-score">
              <div class="teacher-drawer-score-head">
                <span>教学考核参考分</span>
                <strong>{{ selectedProfile.teachingScore ?? '—' }}<small>/100</small></strong>
              </div>
              <div class="teacher-drawer-progress">
                <span :style="{ width: (selectedProfile.teachingScore ?? 0) + '%' }"></span>
              </div>
            </div>
          </section>

          <section class="teacher-drawer-section teacher-current-courses">
            <div class="teacher-current-courses-heading">
              <h4 class="teacher-drawer-section-title">本学期授课课程</h4>
              <span class="teacher-current-term">2026—2027学年 第一学期</span>
            </div>
            <p class="teacher-current-tip">依据教务系统中的教师、课程和教学班记录核对。相同课程的不同教学班分别列出。</p>
            <div v-if="teacherCoursesLoading" class="teacher-course-empty" role="status">正在查询本学期教学安排…</div>
            <div v-else-if="teacherCoursesError" class="teacher-course-empty teacher-course-error" role="alert">
              {{ teacherCoursesError }}
            </div>
            <div v-else-if="!teacherIdentityVerified" class="teacher-course-empty">
              当前教师画像尚未与教务系统中的教师档案完成准确关联，无法确认本学期授课课程。
            </div>
            <div v-else-if="teacherCurrentCourses.length === 0" class="teacher-course-empty">
              教务系统中暂无该教师在本学期的授课记录（不代表实际未授课）。
            </div>
            <template v-else>
              <div class="teacher-course-count">本学期 {{ teacherCurrentCourses.length }} 个教学班 · {{ teacherCurrentCourseNames }} 门不同课程</div>
              <div class="teacher-course-list">
                <article v-for="row in teacherCurrentCourses" :key="row.key" class="teacher-course-card">
                  <div class="teacher-course-card-top">
                    <div>
                      <h5>{{ row.name }}</h5>
                      <span>{{ row.code || '课程代码未录入' }}</span>
                    </div>
                    <span class="teacher-course-type">{{ row.courseType || '性质未录入' }}</span>
                  </div>
                  <div class="teacher-course-fields">
                    <div><span>教学班</span><strong>{{ row.className || '未录入' }}</strong></div>
                    <div><span>学分 / 学时</span><strong>{{ row.credit || '—' }} / {{ row.hours || '—' }}</strong></div>
                    <div><span>上课时间</span><strong>{{ row.schedule || '未录入' }}</strong></div>
                    <div><span>上课地点</span><strong>{{ row.location || '未录入' }}</strong></div>
                    <div><span>教学周</span><strong>{{ row.weeks || '未录入' }}</strong></div>
                    <div><span>选课人数 / 容量</span><strong>{{ row.enrolled ?? '—' }} / {{ row.capacity ?? '—' }}</strong></div>
                  </div>
                </article>
              </div>
            </template>
          </section>
        </div>

        <footer class="teacher-drawer-footer">
          <button type="button" class="teacher-drawer-export" @click="exportTeacherProfile">导出档案</button>
          <button type="button" class="teacher-drawer-confirm" @click="closeTeacherDetail">关闭资料卡</button>
        </footer>
      </aside>
    </div>
  </Teleport>

  <!-- 引进人才：真实教师档案登记，沿用 /api/teachers/，与官网导入档案区分 -->
  <Teleport to="body">
    <div v-if="talentModalOpen" class="talent-modal-backdrop" @click.self="closeTalentModal">
      <section class="talent-modal" role="dialog" aria-modal="true" aria-labelledby="talent-modal-title">
        <header class="talent-modal-header">
          <div>
            <h3 id="talent-modal-title">引进人才 · 教师信息登记</h3>
            <p>登记正式教师基本档案，提交后写入现有教务数据库。</p>
          </div>
          <button type="button" class="talent-close" aria-label="关闭登记窗口" @click="closeTalentModal">×</button>
        </header>
        <div v-if="talentSaved" class="talent-modal-body talent-saved" role="status">
          <div class="talent-saved-icon">✓</div>
          <h4>教师档案已保存</h4>
          <p>{{ talentSaved.name }}（{{ talentSaved.teacherNo }}）已写入教务系统教师名册。</p>
          <p class="talent-muted">新增登记档案不会自动成为官网师资档案；可通过上方「导出师资报表」查看数据库记录。</p>
          <button type="button" class="talent-submit" @click="closeTalentModal">完成</button>
        </div>
        <form v-else class="talent-modal-body" @submit.prevent="submitTalent">
          <div v-if="talentLoading" class="talent-muted">正在读取学院信息…</div>
          <div v-if="talentError" class="talent-error" role="alert">{{ talentError }}</div>
          <div class="talent-form-grid">
            <label class="talent-field">
              <span>教师工号 <b>*</b></span>
              <input v-model.trim="talentForm.teacher_no" maxlength="32" required placeholder="请输入唯一教师工号" />
            </label>
            <label class="talent-field">
              <span>姓名 <b>*</b></span>
              <input v-model.trim="talentForm.name" maxlength="40" required placeholder="请输入教师姓名" />
            </label>
            <label class="talent-field">
              <span>所属专业 <b>*</b></span>
              <select v-model="talentForm.major" required>
                <option value="">请选择专业</option>
                <option v-for="major in talentMajorOptions.slice(1)" :key="major" :value="major">{{ major }}</option>
              </select>
            </label>
            <label class="talent-field">
              <span>职称 <b>*</b></span>
              <select v-model="talentForm.title" required>
                <option value="">请选择职称</option>
                <option value="教授">教授</option>
                <option value="副教授">副教授</option>
                <option value="讲师">讲师</option>
                <option value="助教">助教</option>
              </select>
            </label>
            <label class="talent-field">
              <span>性别</span>
              <select v-model="talentForm.gender">
                <option value="男">男</option>
                <option value="女">女</option>
                <option value="未说明">未说明</option>
              </select>
            </label>
            <label class="talent-field">
              <span>所属学院 <b>*</b></span>
              <select v-model="talentForm.college" required :disabled="talentLoading || !talentColleges.length">
                <option value="">请选择学院</option>
                <option v-for="item in talentColleges" :key="item.id" :value="String(item.id)">{{ item.name }}</option>
              </select>
            </label>
            <label class="talent-field">
              <span>联系电话</span>
              <input v-model.trim="talentForm.phone" type="tel" maxlength="30" placeholder="可选" />
            </label>
            <label class="talent-field">
              <span>电子邮箱</span>
              <input v-model.trim="talentForm.email" type="email" maxlength="120" placeholder="可选" />
            </label>
            <label class="talent-field talent-field-full">
              <span>个人简介 / 引进备注</span>
              <textarea v-model.trim="talentForm.description" rows="3" maxlength="800" placeholder="可填写研究方向、人才引进备注等内容"></textarea>
            </label>
          </div>
          <p class="talent-muted">为兼容现有后端，所属专业目前与备注一起保存在教师简介字段中，不新增数据库表或字段；教务接口如扩展独立专业字段，可再统一迁移。</p>
          <div class="talent-modal-footer">
            <button class="talent-cancel" type="button" @click="closeTalentModal">取消</button>
            <button class="talent-submit" type="submit" :disabled="talentSaving || talentLoading || !talentColleges.length">
              {{ talentSaving ? '正在保存…' : '确认登记' }}
            </button>
          </div>
        </form>
      </section>
    </div>
  </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import api from '@/api/index'
import { teacherPortraits } from './teacherPortraits'

const failedPortraits = ref<Record<string, boolean>>({})
function markPortraitFailed(url: string) { failedPortraits.value[url] = true }

// ========== Reactive State ==========
const majorFilter = ref('')
const majorOptions = ['', '科社系、当代社会主义研究基地', '政治学系', '国际政治系', '公共管理系', '公共治理研究院'] as const
const talentMajorOptions = ['', '行政管理', '政治学', '科学社会主义', '国际政治', ...majorOptions.slice(1)]
const selectedProfile = ref<any>(null)

// 教师画像详情：只读取本学期已有教务记录，不改变其它教师管理模块的演示数据。
const TEACHER_CURRENT_TERM = '2026—2027学年 第一学期'
type TeacherApiRow = Record<string, unknown>
interface CurrentTeacherCourse {
  key: string
  name: string
  code: string
  className: string
  courseType: string
  credit: string
  hours: string
  weeks: string
  schedule: string
  location: string
  enrolled: number | null
  capacity: number | null
}
const teacherCurrentCourses = ref<CurrentTeacherCourse[]>([])
const teacherCoursesLoading = ref(false)
const teacherCoursesError = ref('')
const teacherIdentityVerified = ref(false)
const teacherCurrentCourseNames = computed(() => new Set(teacherCurrentCourses.value.map(x => x.code || x.name)).size)
let teacherCoursesRequestId = 0

function teacherApiObject(value: unknown): TeacherApiRow {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value as TeacherApiRow : {}
}
function teacherApiText(value: unknown): string {
  return value === null || value === undefined ? '' : String(value).trim()
}
function teacherApiNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null
  const number = Number(value)
  return Number.isFinite(number) ? number : null
}
function teacherLinkedId(value: unknown): number | null {
  return teacherApiNumber(typeof value === 'object' && value !== null ? teacherApiObject(value).id : value)
}
function teacherNormalizeName(value: unknown): string {
  return teacherApiText(value).replace(/\s+/g, '').toLowerCase()
}
function teacherDisplayName(row: TeacherApiRow): string {
  return teacherApiText(row.name || row.full_name || row.teacher_name)
}
function teacherNumber(row: TeacherApiRow): string {
  return teacherApiText(row.teacher_no || row.teacher_number || row.employee_no || row.employee_id || row.staff_no || row.code)
}
async function fetchTeacherApiAll(path: string): Promise<TeacherApiRow[]> {
  const rows: TeacherApiRow[] = []
  // 读取所有分页，避免只展示第一页而遗漏教师的授课教学班。
  for (let page = 1; page <= 200; page++) {
    const payload = await api.get(path, { params: { page, page_size: 100 } }) as unknown
    if (Array.isArray(payload)) return payload.map(teacherApiObject)
    const response = teacherApiObject(payload)
    const values = Array.isArray(response.results) ? response.results.map(teacherApiObject) : []
    rows.push(...values)
    if (!Array.isArray(response.results)) throw new Error('Unexpected API list format')
    const count = teacherApiNumber(response.count)
    if (values.length === 0) {
      if (count !== null && rows.length < count) throw new Error('Incomplete API list')
      break
    }
    if (count !== null && rows.length >= count) break
    if (!response.next) {
      if (count !== null && rows.length < count) throw new Error('Incomplete teacher API pagination')
      break
    }
    if (page === 200) throw new Error('API pagination limit reached')
  }
  return rows
}
function teacherSemesterIsCurrent(row: TeacherApiRow): boolean {
  const text = [row.name, row.code, row.academic_year, row.term, row.semester_term, row.year]
    .map(teacherApiText).filter(Boolean).join(' ')
  const normalized = text.replace(/[—–_\s/]/g, '-')
  return /2026[^0-9]*2027/.test(normalized) &&
    (/第一|一学期|秋|上学期|fall|autumn|2027-1/i.test(text) ||
      /2026[^0-9]*2027[^0-9]*1(?:[^0-9]|$)/.test(normalized))
}
function teacherGetClassTeacherId(cls: TeacherApiRow): number | null {
  return teacherLinkedId(cls.teacher ?? cls.teacher_id)
}
function teacherGetClassCourseId(cls: TeacherApiRow): number | null {
  return teacherLinkedId(cls.course ?? cls.course_id)
}
function teacherGetClassSemesterId(cls: TeacherApiRow): number | null {
  return teacherLinkedId(cls.semester ?? cls.semester_id)
}
function teacherGetCourseSemesterId(course: TeacherApiRow): number | null {
  return teacherLinkedId(course.semester ?? course.semester_id)
}
function teacherApiError(error: unknown): string {
  const value = error as { response?: { status?: number }; message?: string }
  if (value?.response?.status === 403) return '当前账号无权读取教学任务数据。'
  if (value?.response?.status === 401) return '登录状态已失效，请重新登录后查看。'
  return '本学期课程接口读取失败，请检查教务服务后重试。'
}
async function loadTeacherCurrentCourses(profile: { name: string; teacherNo: string }): Promise<void> {
  const requestId = ++teacherCoursesRequestId
  teacherCoursesLoading.value = true
  teacherCoursesError.value = ''
  teacherIdentityVerified.value = false
  teacherCurrentCourses.value = []
  try {
    const [teachers, courses, classes, semesters] = await Promise.all([
      fetchTeacherApiAll('/teachers/'),
      fetchTeacherApiAll('/courses/'),
      fetchTeacherApiAll('/teaching-classes/'),
      fetchTeacherApiAll('/semesters/'),
    ])
    if (requestId !== teacherCoursesRequestId) return

    // 同名教师不能凭姓名猜测身份；有工号时还需避免工号与画像姓名冲突。
    const requestedNo = teacherApiText(profile.teacherNo).toLowerCase()
    const requestedName = teacherNormalizeName(profile.name)
    const exactNumber = teachers.filter(t => teacherNumber(t).toLowerCase() === requestedNo && requestedNo)
    const exactName = teachers.filter(t => teacherNormalizeName(teacherDisplayName(t)) === requestedName)
    const matches = exactNumber.length === 1 &&
      (!teacherDisplayName(exactNumber[0]!) || teacherNormalizeName(teacherDisplayName(exactNumber[0]!)) === requestedName)
      ? exactNumber
      : !requestedNo && exactName.length === 1 ? exactName : []
    if (matches.length !== 1) return
    const teacher = matches[0]!
    const teacherId = teacherLinkedId(teacher.id)
    if (teacherId === null) return
    teacherIdentityVerified.value = true

    const termIds = new Set(semesters.filter(teacherSemesterIsCurrent).map(s => teacherLinkedId(s.id)).filter((id): id is number => id !== null))
    const courseMap = new Map(courses.map(c => [teacherLinkedId(c.id), c]))
    const rows: CurrentTeacherCourse[] = []
    for (const cls of classes) {
      if (teacherGetClassTeacherId(cls) !== teacherId) continue
      const courseId = teacherGetClassCourseId(cls)
      const course = courseMap.get(courseId) || teacherApiObject(cls.course)
      const classSemester = teacherGetClassSemesterId(cls)
      const courseSemester = teacherGetCourseSemesterId(course)
      const embeddedClassSemester = teacherApiObject(cls.semester)
      const embeddedCourseSemester = teacherApiObject(course.semester)
      const classSemesterNamed = teacherSemesterIsCurrent({
        name: cls.semester_name || embeddedClassSemester.name ||
          (typeof cls.semester === 'string' ? cls.semester : ''),
      })
      const courseSemesterNamed = teacherSemesterIsCurrent({
        name: course.semester_name || embeddedCourseSemester.name ||
          (typeof course.semester === 'string' ? course.semester : ''),
      })
      const isInTerm = (classSemester !== null && (termIds.has(classSemester) || classSemesterNamed)) ||
        (classSemester === null && (courseSemester !== null
          ? termIds.has(courseSemester) || courseSemesterNamed
          : classSemesterNamed || courseSemesterNamed))
      if (!isInTerm) continue
      const id = teacherLinkedId(cls.id)
      rows.push({
        key: id === null ? `${courseId ?? 'unknown'}-${rows.length}` : `class-${id}`,
        name: teacherApiText(course.name || cls.course_name) || '未命名课程',
        code: teacherApiText(course.code || cls.course_code),
        className: teacherApiText(cls.class_name || cls.name),
        courseType: teacherApiText(course.course_type),
        credit: teacherApiText(course.credit),
        hours: teacherApiText(course.hours),
        weeks: teacherApiText(cls.weeks || cls.teaching_weeks),
        schedule: teacherApiText(cls.schedule || cls.class_time),
        location: teacherApiText(cls.location || cls.classroom),
        enrolled: teacherApiNumber(cls.enrolled_count),
        capacity: teacherApiNumber(cls.capacity),
      })
    }
    rows.sort((a,b) => a.name.localeCompare(b.name,'zh-CN') || a.className.localeCompare(b.className,'zh-CN'))
    if (requestId === teacherCoursesRequestId) teacherCurrentCourses.value = rows
  } catch (error) {
    if (requestId === teacherCoursesRequestId) teacherCoursesError.value = teacherApiError(error)
  } finally {
    if (requestId === teacherCoursesRequestId) teacherCoursesLoading.value = false
  }
}
const titleDistChartRef = ref<HTMLElement | null>(null)
const workloadChartRef = ref<HTMLElement | null>(null)
const relationChartRef = ref<HTMLElement | null>(null)
const ageChartRef = ref<HTMLElement | null>(null)
const evalChartRef = ref<HTMLElement | null>(null)
const researchTrendChartRef = ref<HTMLElement | null>(null)
const researchRankChartRef = ref<HTMLElement | null>(null)

let titleDistChart: echarts.ECharts | null = null
let workloadChart: echarts.ECharts | null = null
let relationChart: echarts.ECharts | null = null
let ageChart: echarts.ECharts | null = null
let evalChart: echarts.ECharts | null = null
let researchTrendChart: echarts.ECharts | null = null
let researchRankChart: echarts.ECharts | null = null

// ========== 计算属性 ==========
const directoryRows = ref<TeacherApiRow[]>([])
const directoryLoading = ref(true)
const directoryError = ref('')
const directoryReady = computed(() => !directoryLoading.value && !directoryError.value)
const totalTeachers = computed(() => directoryReady.value ? directoryRows.value.length : '—')
const titleCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const row of directoryRows.value) {
    const title = teacherApiText(row.title) || '未说明'
    counts.set(title, (counts.get(title) || 0) + 1)
  }
  return counts
})
function descriptionField(row: TeacherApiRow, label: string): string {
  const line = teacherApiText(row.description).split(/\r?\n/).find(x => x.startsWith(label + '：') || x.startsWith(label + ':'))
  return line ? line.slice(label.length + 1).trim() : ''
}
function isOfficialDirectory(row: TeacherApiRow): boolean {
  return teacherNumber(row).startsWith('DIR-') &&
    teacherApiText(row.description).includes('【官网公开师资档案】') &&
    teacherApiText(row.college_name || teacherApiObject(row.college).name) === '政治学与公共管理学院'
}
async function loadFacultyDirectory(): Promise<void> {
  directoryLoading.value = true
  directoryError.value = ''
  try {
    const rows = await fetchTeacherApiAll('/teachers/')
    directoryRows.value = rows.filter(isOfficialDirectory)
  } catch (err) {
    directoryRows.value = []
    directoryError.value = '教师名录读取失败：' + teacherApiError(err)
  } finally {
    directoryLoading.value = false
    if (titleDistChart) initTitleDistChart()
  }
}
const avgAge = computed(() => '43.2')

// ========== 1. 统计卡片 ==========
const facultyStats = computed(() => [
  {
    label: '官网师资档案',
    value: String(totalTeachers.value),
    unit: '人',
    sub: directoryLoading.value ? '正在读取名录' : directoryError.value ? '名录读取失败' : `教授 ${titleCounts.value.get('教授') || 0} 人 · 副教授 ${titleCounts.value.get('副教授') || 0} 人`,
    icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
    bg: '#EFF6FF', color: '#1E3A8A',
    sparkline: '',
  },
  {
    label: '授课总门次（演示）',
    value: '186',
    unit: '门',
    sub: '人均 2.2 门',
    icon: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20 M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z',
    bg: '#DBEAFE', color: '#3B82F6',
    sparkline: '0,12 10,15 20,11 30,16 40,13 50,17 60,14 70,18 80,15',
  },
  {
    label: '评教均分（演示）',
    value: '4.52',
    unit: '/5.0',
    sub: '较上学期 +0.08',
    icon: 'M12 15l-2 2l1-3.5l-2-1.5h2.5L12 8.5l.5 3.5H15l-2 1.5l1 3.5z',
    bg: '#BFDBFE', color: '#2563EB',
    sparkline: '0,10 10,13 20,9 30,14 40,11 50,15 60,12 70,16 80,13',
  },
  {
    label: '指导学生数（演示）',
    value: '4,200',
    unit: '人次',
    sub: '同比 +6.5%',
    icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
    bg: '#F3F4F6', color: '#64748B',
    sparkline: '0,16 10,14 20,17 30,13 40,18 50,14 60,19 70,15 80,17',
  },
])

// ========== 2. 教师画像卡片（官网档案，保留六卡片布局） ==========
const teacherProfiles = computed(() => directoryRows.value.map(row => {
  const title = teacherApiText(row.title) || '未说明'
  const level = title === '教授' ? 1 : 2
  const profileUrl = descriptionField(row, '个人主页')
  let safeUrl = ''
  try {
    const parsed = new URL(profileUrl)
    if (parsed.protocol === 'https:' && parsed.hostname.endsWith('.sdu.edu.cn') && !parsed.username && !parsed.password) safeUrl = parsed.href
  } catch { /* 无公开链接 */ }
  return {
    id: teacherLinkedId(row.id), name: teacherDisplayName(row), title,
    college: teacherApiText(row.college_name), major: descriptionField(row, '所属系所') || '未说明',
    teacherNo: teacherNumber(row),
    photoUrl: teacherPortraits[teacherNumber(row)]?.name === teacherDisplayName(row) ? import.meta.env.BASE_URL + teacherPortraits[teacherNumber(row)]!.path : '',
    level, barColor: level === 1 ? '#1E3A8A' : '#3B82F6',
    courses: '—', students: '—', rating: null as number | null, teachingHours: '—', teachingScore: null as number | null,
    joinYear: '未采集', office: '未采集', researchFocus: descriptionField(row, '研究方向') || '未采集',
    researchSummary: teacherApiText(row.description), profileUrl: safeUrl,
  }
}))
const filteredDirectory = computed(() => majorFilter.value ? teacherProfiles.value.filter(t => t.major === majorFilter.value) : teacherProfiles.value)
const profilePage = ref(1)
const profilePageCount = computed(() => Math.max(1, Math.ceil(filteredDirectory.value.length / 6)))
const filteredTeacherProfiles = computed(() => filteredDirectory.value.slice((profilePage.value - 1) * 6, profilePage.value * 6))
watch(majorFilter, () => { profilePage.value = 1 })
watch(profilePageCount, n => { if (profilePage.value > n) profilePage.value = n })

type TalentCollege = { id: number; name: string }
type TalentForm = {
  teacher_no: string; name: string; major: string; title: string; gender: string
  college: string; phone: string; email: string; description: string
}
function emptyTalentForm(): TalentForm {
  return { teacher_no: '', name: '', major: '', title: '', gender: '未说明', college: '', phone: '', email: '', description: '' }
}
const talentModalOpen = ref(false)
const talentLoading = ref(false)
const talentSaving = ref(false)
const talentForm = ref<TalentForm>(emptyTalentForm())
const talentColleges = ref<TalentCollege[]>([])
const talentError = ref('')
const talentSaved = ref<{ name: string; teacherNo: string } | null>(null)
const facultyNotice = ref('')
const facultyExporting = ref(false)

async function openTalentModal(): Promise<void> {
  talentModalOpen.value = true
  talentForm.value = emptyTalentForm()
  talentError.value = ''
  talentSaved.value = null
  talentColleges.value = []
  talentLoading.value = true
  try {
    const rows = await fetchTeacherApiAll('/colleges/')
    if (!talentModalOpen.value) return
    talentColleges.value = rows
      .map(r => ({ id: teacherLinkedId(r.id), name: teacherApiText(r.name) }))
      .filter((r): r is TalentCollege => r.id !== null && r.name.length > 0)
    const school = talentColleges.value.find(c => c.name.includes('政治学与公共管理'))
    if (school) talentForm.value.college = String(school.id)
    else if (talentColleges.value.length === 1) talentForm.value.college = String(talentColleges.value[0]!.id)
    if (!talentColleges.value.length) talentError.value = '未获取到学院名录，当前无法登记教师，请检查后端学院接口。'
  } catch (err: unknown) {
    if (!talentModalOpen.value) return
    talentError.value = facultyApiMessage(err, '读取学院列表失败，请检查教务接口及登录状态。')
  } finally {
    talentLoading.value = false
  }
}
function closeTalentModal(): void {
  if (talentSaving.value) return
  talentModalOpen.value = false
}
function facultyApiMessage(err: unknown, fallback: string): string {
  const e = err as { response?: { status?: number; data?: { detail?: unknown; [field: string]: unknown } }; message?: string }
  const fields = e?.response?.data
  if (e?.response?.status === 403) return '当前账号没有教师名册维护权限。'
  if (e?.response?.status === 401) return '登录已失效，请重新登录。'
  if (fields) {
    if (typeof fields.detail === 'string') return fields.detail
    const first = Object.entries(fields).find(([, value]) => value !== null)
    if (first) return `${first[0]}：${Array.isArray(first[1]) ? first[1].join('；') : String(first[1])}`
  }
  return e?.message || fallback
}

// 复用已有 /api/teachers/ 的字段。专业信息通过可读的简介前缀保存（目前未新增 major 模型字段）。
async function submitTalent(): Promise<void> {
  if (talentSaving.value) return
  const form = talentForm.value
  if (!form.teacher_no || !form.name || !form.title || !form.major || !talentMajorOptions.includes(form.major)) {
    talentError.value = '请完整填写教师工号、姓名、职称及所属专业。'
    return
  }
  const collegeId = Number(form.college)
  if (!Number.isInteger(collegeId) || collegeId <= 0 || !talentColleges.value.some(c => c.id === collegeId)) {
    talentError.value = '请选择有效的所属学院。'
    return
  }
  talentError.value = ''
  talentSaving.value = true
  try {
    const description = `所属专业：${form.major}${form.description ? `\n${form.description.trim()}` : ''}`
    const payload = {
      teacher_no: form.teacher_no.trim(),
      name: form.name.trim(),
      gender: form.gender,
      college: collegeId,
      title: form.title,
      phone: form.phone.trim(),
      email: form.email.trim(),
      description,
    }
    await api.post('/teachers/', payload)
    if (!talentModalOpen.value) return
    talentSaved.value = { name: payload.name, teacherNo: payload.teacher_no }
    facultyNotice.value = `${payload.name}已保存到教务教师名册；官网师资画像仅展示官网导入档案，新登记档案可通过报表查看。`
  } catch (err: unknown) {
    talentError.value = facultyApiMessage(err, '教师登记失败，请检查表单后重试。')
  } finally {
    talentSaving.value = false
  }
}

function facultyMajorFromApi(row: TeacherApiRow): string {
  const department = descriptionField(row, '所属系所')
  if (department) return department
  const direct = teacherApiText(row.major || row.major_name || row.specialty)
  if (talentMajorOptions.some(m => m && m === direct)) return direct
  const description = teacherApiText(row.description)
  const matched = description.match(/(?:^|\n)所属专业[：:]\s*([^\r\n]+)/)
  const savedMajor = matched?.[1]?.trim() || ''
  return talentMajorOptions.some(m => m && m === savedMajor) ? savedMajor : ''
}
function facultyDescriptionWithoutMajor(row: TeacherApiRow): string {
  return teacherApiText(row.description).replace(/(?:^|\n)所属专业[：:]\s*[^\r\n]+\n?/, '').trim()
}

// 单文件 XLSX 导出，无需新增前端依赖；每行标注“教务接口”或“画像演示”。
const facultyEncoder = new TextEncoder()
function facultyXmlEscape(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;')
}
function facultyExcelColumn(index: number): string {
  let n = index + 1, result = ''
  while (n > 0) { n--; result = String.fromCharCode(65 + (n % 26)) + result; n = Math.floor(n / 26) }
  return result
}
function facultyCrc32(bytes: Uint8Array): number {
  let crc = 0xFFFFFFFF
  for (const b of bytes) {
    crc ^= b
    for (let i = 0; i < 8; i++) crc = (crc >>> 1) ^ (crc & 1 ? 0xEDB88320 : 0)
  }
  return (crc ^ 0xFFFFFFFF) >>> 0
}
function facultyZipStored(files: Array<{ name: string; data: Uint8Array }>): Uint8Array {
  const entries: Uint8Array[] = [], indexes: Uint8Array[] = []
  let offset = 0
  for (const file of files) {
    const name = facultyEncoder.encode(file.name), len = file.data.byteLength, checksum = facultyCrc32(file.data)
    const local = new Uint8Array(30 + name.length), lv = new DataView(local.buffer)
    lv.setUint32(0, 0x04034b50, true); lv.setUint16(4, 20, true); lv.setUint16(6, 0x0800, true)
    lv.setUint32(14, checksum, true); lv.setUint32(18, len, true); lv.setUint32(22, len, true)
    lv.setUint16(26, name.length, true); local.set(name, 30)
    entries.push(local, file.data)
    const central = new Uint8Array(46 + name.length), cv = new DataView(central.buffer)
    cv.setUint32(0, 0x02014b50, true); cv.setUint16(4, 20, true); cv.setUint16(6, 20, true)
    cv.setUint16(8, 0x0800, true); cv.setUint32(16, checksum, true)
    cv.setUint32(20, len, true); cv.setUint32(24, len, true); cv.setUint16(28, name.length, true)
    cv.setUint32(42, offset, true); central.set(name, 46); indexes.push(central)
    offset += local.length + len
  }
  const centralLength = indexes.reduce((total, bytes) => total + bytes.length, 0)
  const end = new Uint8Array(22), e = new DataView(end.buffer)
  e.setUint32(0, 0x06054b50, true); e.setUint16(8, files.length, true); e.setUint16(10, files.length, true)
  e.setUint32(12, centralLength, true); e.setUint32(16, offset, true)
  const result = new Uint8Array(offset + centralLength + end.length)
  let pos = 0
  for (const chunk of [...entries, ...indexes, end]) { result.set(chunk, pos); pos += chunk.length }
  return result
}
function facultyXlsx(rows: string[][]): Uint8Array {
  const sheet = rows.map((row, r) => `<row r="${r + 1}">${row.map((value, col) =>
    `<c r="${facultyExcelColumn(col)}${r + 1}" t="inlineStr"><is><t xml:space="preserve">${facultyXmlEscape(value)}</t></is></c>`
  ).join('')}</row>`).join('')
  const files = [
    { name: '[Content_Types].xml', text: '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>' },
    { name: '_rels/.rels', text: '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>' },
    { name: 'xl/workbook.xml', text: '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="师资报表" sheetId="1" r:id="rId1"/></sheets></workbook>' },
    { name: 'xl/_rels/workbook.xml.rels', text: '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>' },
    { name: 'xl/worksheets/sheet1.xml', text: `<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${sheet}</sheetData></worksheet>` },
  ]
  return facultyZipStored(files.map(f => ({ name: f.name, data: facultyEncoder.encode(f.text) })))
}
function facultyDownloadXlsx(bytes: Uint8Array, name: string): void {
  const copy = new Uint8Array(bytes.byteLength)
  copy.set(bytes)
  const blob = new Blob([copy.buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
async function exportFacultyReport(): Promise<void> {
  if (facultyExporting.value) return
  facultyExporting.value = true
  facultyNotice.value = ''
  let teachers: TeacherApiRow[] = []
  let listError = ''
  try { teachers = await fetchTeacherApiAll('/teachers/') }
  catch (err: unknown) { listError = facultyApiMessage(err, '教师名册接口不可用。') }
  try {
    const selected = majorFilter.value
    const confirmed = teachers.filter(t => !selected || facultyMajorFromApi(t) === selected)
    const missingMajor = teachers.filter(t => !facultyMajorFromApi(t)).length
    const rows: string[][] = [
      ['山东大学政治学与公共管理学院 · 师资报表'],
      [`系所筛选：${selected || '全部系所'}`, `导出日期：${new Date().toLocaleDateString('zh-CN')}`],
      ['说明：教务名册来自 /api/teachers/；官网师资、演示业务档案及其他登记档案分别标识；DIR- 为本地编号。'],
      ['说明：按教师简介中的所属系所或所属专业筛选；扩展信息为官网自动采集，待核实。'],
      [],
      ['数据类型', '档案编号 / 工号', '姓名', '职称', '所属系所 / 专业', '学院', '性别', '电话', '邮箱', '说明'],
      ...confirmed.map(row => [
        isOfficialDirectory(row) ? '官网公开师资' : teacherApiText(row.description).includes('【演示教师】') ? '演示业务档案' : '其他教务档案', teacherNumber(row), teacherDisplayName(row), teacherApiText(row.title),
        facultyMajorFromApi(row) || '未登记专业', teacherApiText(row.college_name || teacherApiObject(row.college).name),
        teacherApiText(row.gender), teacherApiText(row.phone), teacherApiText(row.email), facultyDescriptionWithoutMajor(row),
      ]),
    ]
    if (confirmed.length === 0) {
      facultyNotice.value = listError || '当前筛选没有可导出的教师记录。'
      return
    }
    facultyDownloadXlsx(facultyXlsx(rows), `师资报表_${selected || '全部系所'}_${new Date().toISOString().slice(0, 10)}.xlsx`)
    const warnings: string[] = []
    if (listError) warnings.push(`教师名册未能读取：${listError}，本次无可用教务名册`)
    if (selected && missingMajor > 0) warnings.push(`教务名册有 ${missingMajor} 条记录缺少专业归属，未纳入专业筛选结果`)
    facultyNotice.value = `报表已导出：教务名册 ${confirmed.length} 条。${warnings.join('；')}`
  } catch (err: unknown) {
    facultyNotice.value = facultyApiMessage(err, '生成 Excel 报表失败，请重试。')
  } finally {
    facultyExporting.value = false
  }
}

const previousBodyOverflow = ref('')

function openTeacherDetail(teacher: any) {
  if (!selectedProfile.value) {
    previousBodyOverflow.value = document.body.style.overflow
  }
  selectedProfile.value = teacher
  void loadTeacherCurrentCourses(teacher)
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', handleTeacherDrawerKeydown)
}

function closeTeacherDetail() {
  teacherCoursesRequestId++
  teacherCoursesLoading.value = false
  selectedProfile.value = null
  document.body.style.overflow = previousBodyOverflow.value
  window.removeEventListener('keydown', handleTeacherDrawerKeydown)
}

function handleTeacherDrawerKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && selectedProfile.value) {
    closeTeacherDetail()
  }
}

function exportTeacherProfile() {
  const teacher = selectedProfile.value
  if (!teacher) return

  const lines = [
    '教师个人档案',
    '',
    `姓名：${teacher.name}`,
    `本地档案编号（非正式工号）：${teacher.teacherNo}`,
    `职称：${teacher.title}`,
    `所属学院：政治学与公共管理学院`,
    `所属系所：${teacher.major}`,
    `入职年份：${teacher.joinYear}`,
    `办公地点：${teacher.office}`,
    `研究方向：${teacher.researchFocus}`,
    '',
    `档案来源及公开资料：${teacher.researchSummary}`,
    '教学数据（未核实指标显示 —）',
    `授课门次：${teacher.courses}`,
    `授课学生：${teacher.students}`,
    `学生评教：${teacher.rating ?? '—'}/5.0`,
    `学期课时：${teacher.teachingHours}`,
    `教学考核参考分：${teacher.teachingScore ?? '—'}/100`,
    '',
    `本学期授课课程（${TEACHER_CURRENT_TERM}）`,
    ...(teacherCoursesError.value ? [teacherCoursesError.value] :
      teacherCoursesLoading.value ? ['课程查询尚未完成'] : !teacherIdentityVerified.value ? ['尚未与教务系统教师档案准确关联，无法核实本学期课程'] :
      teacherCurrentCourses.value.length ? teacherCurrentCourses.value.map((row, index) =>
        `${index + 1}. ${row.name}（${row.code || '无代码'}） | 教学班：${row.className || '未录入'} | 课程性质：${row.courseType || '未录入'} | 学分/学时：${row.credit || '—'}/${row.hours || '—'} | 时间：${row.schedule || '未录入'} | 地点：${row.location || '未录入'} | 教学周：${row.weeks || '未录入'} | 选课/容量：${row.enrolled ?? '—'}/${row.capacity ?? '—'}`
      ) : ['本学期暂无授课记录']),
  ]

  const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `教师档案_${teacher.name}.txt`
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

// ========== 3. 职称分布图 (南丁格尔玫瑰) ==========
function initTitleDistChart() {
  if (!titleDistChartRef.value) return
  titleDistChart = titleDistChart || echarts.init(titleDistChartRef.value)
  titleDistChart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
      formatter: '{b}: {c} 人 ({d}%)',
    },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 10 }, itemWidth: 12, itemHeight: 8, itemGap: 16 },
    series: [{
      type: 'pie',
      radius: ['8%', '72%'],
      center: ['50%', '45%'],
      roseType: 'radius',
      itemStyle: { borderRadius: 6, borderColor: '#FFF', borderWidth: 2 },
      label: { color: '#6B7280', fontSize: 10, formatter: '{b}\n{d}%' },
      labelLine: { lineStyle: { color: '#D1D5DB' } },
      emphasis: { label: { fontSize: 14, fontWeight: 'bold' } },
      data: [...titleCounts.value.entries()].map(([name, value], i) => ({
        name, value, itemStyle: { color: ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#769BCB', '#B9CEE9'][i % 6] },
      })),
    }],
  })
}

// ========== 4. 教学工作量排行 ==========
function initWorkloadChart() {
  if (!workloadChartRef.value) return
  workloadChart = echarts.init(workloadChartRef.value)
  const data = [
    { name: '示例01', hours: 22 }, { name: '示例04', hours: 20 },
    { name: '示例02', hours: 18 }, { name: '示例03', hours: 16 },
    { name: '示例06', hours: 14 }, { name: '示例05', hours: 14 },
    { name: '示例07', hours: 12 }, { name: '示例08', hours: 10 },
  ]
  const sorted = [...data].sort((a, b) => a.hours - b.hours)
  const barColors = ['#93C5FD', '#7CB7FB', '#60A5FA', '#4B8EF1', '#3B82F6', '#2563EB', '#1E40AF', '#1E3A8A']

  workloadChart.setOption({
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: '#FFFFFF', borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    },
    grid: { top: 10, right: 40, bottom: 10, left: 56 },
    xAxis: { type: 'value', max: 30, name: 'h/周', nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, axisLabel: { color: '#6B7280', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } } },
    yAxis: { type: 'category', data: sorted.map(d => d.name), axisLabel: { color: '#6B7280', fontSize: 10 }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar',
      data: sorted.map((d, i) => ({
        value: d.hours,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: barColors[i] || '#3B82F6' },
            { offset: 1, color: '#EFF6FF' },
          ]),
          borderRadius: [0, 6, 6, 0],
        },
      })),
      barWidth: 16,
      label: { show: true, position: 'right', color: '#374151', fontSize: 10, fontWeight: 600, formatter: '{c}h' },
    }],
  })
}

// ========== 5. 教师课程关系图 (力导向) ==========
function initRelationChart() {
  if (!relationChartRef.value) return
  relationChart = echarts.init(relationChartRef.value)
  const nodes = [
    { id: 't1', name: '示例01', symbolSize: 36, category: 0, itemStyle: { color: '#1E3A8A' } },
    { id: 't2', name: '示例02', symbolSize: 32, category: 0, itemStyle: { color: '#2563EB' } },
    { id: 't3', name: '示例03', symbolSize: 34, category: 0, itemStyle: { color: '#1E40AF' } },
    { id: 't4', name: '示例04', symbolSize: 30, category: 0, itemStyle: { color: '#3B82F6' } },
    { id: 't5', name: '示例05', symbolSize: 28, category: 0, itemStyle: { color: '#3B82F6' } },
    { id: 'c1', name: '公共政策分析', symbolSize: 24, category: 1, itemStyle: { color: '#60A5FA' } },
    { id: 'c2', name: '政治学原理', symbolSize: 22, category: 1, itemStyle: { color: '#60A5FA' } },
    { id: 'c3', name: '公共管理学', symbolSize: 24, category: 1, itemStyle: { color: '#60A5FA' } },
    { id: 'c4', name: '国际关系理论', symbolSize: 28, category: 1, itemStyle: { color: '#60A5FA' } },
    { id: 'c5', name: '中国政治制度', symbolSize: 22, category: 1, itemStyle: { color: '#60A5FA' } },
    { id: 'c6', name: '行政管理学', symbolSize: 22, category: 1, itemStyle: { color: '#60A5FA' } },
    { id: 'c7', name: '数字政府与治理', symbolSize: 20, category: 1, itemStyle: { color: '#93C5FD' } },
  ]
  const links = [
    { source: 't1', target: 'c1' }, { source: 't1', target: 'c3' }, { source: 't1', target: 'c5' }, { source: 't1', target: 'c6' },
    { source: 't2', target: 'c2' }, { source: 't2', target: 'c5' }, { source: 't2', target: 'c6' },
    { source: 't3', target: 'c3' }, { source: 't3', target: 'c6' }, { source: 't3', target: 'c1' },
    { source: 't4', target: 'c3' }, { source: 't5', target: 'c4' }, { source: 't5', target: 'c7' },
  ]

  relationChart.setOption({
    tooltip: { trigger: 'item', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#374151' } },
    legend: { bottom: 0, data: ['教师', '课程'], textStyle: { color: '#6B7280', fontSize: 10 }, itemWidth: 10, itemHeight: 10 },
    animationDuration: 1500,
    animationEasingUpdate: 'quinticInOut',
    series: [{
      type: 'graph', layout: 'force', roam: true, draggable: true,
      force: { repulsion: 400, edgeLength: [120, 200], gravity: 0.1 },
      categories: [
        { name: '教师', itemStyle: { color: '#1E3A8A' }, symbol: 'roundRect', symbolSize: 14 },
        { name: '课程', itemStyle: { color: '#60A5FA' }, symbol: 'circle', symbolSize: 10 },
      ],
      nodes: nodes,
      links: links.map(l => ({ ...l, lineStyle: { color: '#D1D5DB', curveness: 0.2 } })),
      label: { show: true, fontSize: 10, color: '#374151', fontWeight: 500 },
      emphasis: { focus: 'adjacency', lineStyle: { width: 3 } },
    }],
  })
}

// ========== 6. 教师年龄结构 (左右对比柱状) ==========
function initAgeChart() {
  if (!ageChartRef.value) return
  ageChart = echarts.init(ageChartRef.value)
  const ageGroups = ['<30', '30-35', '35-40', '40-45', '45-50', '50-55', '≥55']
  const maleData = [6, 10, 14, 12, 8, 5, 3]
  const femaleData = [5, 8, 10, 7, 4, 2, 1]

  ageChart.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#FFFFFF', borderColor: '#E5E7EB', textStyle: { color: '#374151', fontSize: 12 }, boxShadow: '0 4px 16px rgba(0,0,0,0.08)' },
    legend: { bottom: 0, textStyle: { color: '#6B7280', fontSize: 10 }, itemWidth: 12, itemHeight: 8, itemGap: 24 },
    grid: { top: 10, right: 30, bottom: 40, left: 50 },
    xAxis: { type: 'category', data: ageGroups, axisLabel: { color: '#6B7280', fontSize: 10 }, axisTick: { show: false } },
    yAxis: { type: 'value', name: '人数', nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, axisLabel: { color: '#6B7280', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } } },
    series: [
      {
        name: '男教师', type: 'bar', data: maleData.map(v => ({
          value: v,
          itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#1E3A8A' }, { offset: 1, color: '#60A5FA' }]), borderRadius: [6, 6, 0, 0] },
        })),
        barWidth: 20, barGap: '20%',
        label: { show: true, position: 'top', color: '#1E3A8A', fontSize: 9, fontWeight: 600 },
      },
      {
        name: '女教师', type: 'bar', data: femaleData.map(v => ({
          value: v,
          itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: '#93C5FD' }, { offset: 1, color: '#DBEAFE' }]), borderRadius: [6, 6, 0, 0] },
        })),
        barWidth: 20,
        label: { show: true, position: 'top', color: '#93C5FD', fontSize: 9, fontWeight: 600 },
      },
    ],
  })
}

// ========== 7. 教师考核评分 (散点图) ==========
function initEvalChart() {
  if (!evalChartRef.value) return
  evalChart = echarts.init(evalChartRef.value)
  const evals = [
    { name: '示例01', value: [88, 4.9], papers: 12 }, { name: '示例02', value: [82, 4.7], papers: 8 },
    { name: '示例03', value: [90, 4.6], papers: 10 }, { name: '示例04', value: [78, 4.5], papers: 9 },
    { name: '示例05', value: [84, 4.8], papers: 6 }, { name: '示例06', value: [72, 4.4], papers: 5 },
    { name: '示例07', value: [76, 4.4], papers: 7 }, { name: '示例08', value: [70, 4.1], papers: 6 },
    { name: '示例09', value: [86, 4.5], papers: 9 }, { name: '示例10', value: [65, 4.0], papers: 3 },
    { name: '示例11', value: [80, 4.3], papers: 8 }, { name: '示例12', value: [68, 4.0], papers: 4 },
  ]

  evalChart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: '#FFFFFF', borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 12 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
      formatter: (p: any) => {
        const d = p.data
        return `<b>${d.name}</b><br/>教学评分：${d.value[0]}<br/>学生评价：${d.value[1]}<br/>论文产出：${d.papers} 篇`
      },
    },
    grid: { top: 10, right: 30, bottom: 30, left: 55 },
    xAxis: { name: '教学评分', nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, min: 55, max: 95, axisLabel: { color: '#6B7280', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } } },
    yAxis: { name: '学生评价', nameTextStyle: { color: '#9CA3AF', fontSize: 10 }, min: 3.5, max: 5, axisLabel: { color: '#6B7280', fontSize: 10 }, splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } } },
    series: [{
      type: 'scatter',
      data: evals.map((e) => {
        const score = e.value[0] as number
        return {
          ...e,
          symbolSize: Math.max(12, e.papers * 2),
          itemStyle: {
            color: score >= 80 ? '#1E3A8A' : score >= 70 ? '#3B82F6' : '#93C5FD',
            shadowBlur: 8,
            shadowColor: 'rgba(30, 58, 138, 0.15)',
            opacity: 0.85,
          },
        }
      }),
      emphasis: { focus: 'series', itemStyle: { shadowBlur: 16, shadowColor: 'rgba(30, 58, 138, 0.35)' } },
      markLine: {
        silent: true,
        symbol: 'none',
        label: { fontSize: 10, color: '#6B7280' },
        lineStyle: { color: '#E5E7EB', type: 'dashed' },
        data: [
          { xAxis: 80, label: { formatter: '优秀线 80' } },
          { yAxis: 4.5, label: { formatter: '高评 4.5' } },
        ],
      },
    }],
  })
}

// ========== 8. 本月优秀教师 ==========
const starTeachers = [
  { name: '示例01', college: '公共政策研究中心', rating: 4.9, courses: 4, students: 380, comment: '政策案例分析深入，学生评教全院第一' },
  { name: '示例05', college: '国际政治教研室', rating: 4.8, courses: 2, students: 160, comment: '小班研讨教学，国际视野开阔，个性化辅导到位' },
  { name: '示例02', college: '政治学教研室', rating: 4.7, courses: 3, students: 280, comment: '理论基础扎实，科研成果与教学深度融合' },
  { name: '示例03', college: '公共管理教研室', rating: 4.6, courses: 3, students: 220, comment: '案例教学法创新，实践导向性强，深受学生欢迎' },
]

// ========== 9. 课时热力图数据 ==========
const weekLabels = ['周一', '周二', '周三', '周四', '周五']
const heatmapData = [
  { teacher: '示例01', hours: [4, 4, 6, 6, 2] },
  { teacher: '示例02', hours: [4, 6, 4, 4, 0] },
  { teacher: '示例03', hours: [4, 2, 4, 4, 2] },
  { teacher: '示例04', hours: [2, 4, 4, 6, 4] },
  { teacher: '示例05', hours: [4, 2, 4, 4, 0] },
  { teacher: '示例06', hours: [2, 4, 2, 4, 2] },
  { teacher: '示例07', hours: [3, 2, 4, 2, 1] },
  { teacher: '示例08', hours: [2, 2, 4, 2, 0] },
]
function getHeatLevel(h: number): number {
  if (h >= 6) return 5
  if (h >= 4) return 4
  if (h >= 3) return 3
  if (h >= 2) return 2
  return 1
}

// ========== 10. 教学团队 ==========
const teams = [
  { name: '政治学理论教学团队', leader: '示例02', members: ['示例02', '示例06', '示例09', '示例12'], courses: 10, funding: 280, papers: 32, strength: 90 },
  { name: '公共管理教学团队', leader: '示例03', members: ['示例03', '示例04', '示例07', '示例11'], courses: 12, funding: 420, papers: 38, strength: 88 },
  { name: '国际政治与外交团队', leader: '示例05', members: ['示例05', '示例08', '示例10'], courses: 6, funding: 180, papers: 22, strength: 76 },
]

// ========== 10. 科研成果统计 (科研驾驶舱数据) ==========
const researchIndicators = [
  {
    label: 'CSSCI/SSCI 论文', value: '156', unit: '篇', progress: 82, progressLabel: '完成年度目标 82%',
    trendUp: true, trendText: '同比 +12.4%', color: '#1E3A8A',
    sparkline: '0,18 14,16 28,17 42,15 56,18 70,16 84,19 100,14',
  },
  {
    label: '国家级课题', value: '28', unit: '项', progress: 75, progressLabel: '含国家社科基金 18 项',
    trendUp: true, trendText: '同比 +8.2%', color: '#2563EB',
    sparkline: '0,20 14,18 28,19 42,17 56,20 70,18 84,21 100,16',
  },
  {
    label: '横向科研项目', value: '42', unit: '项', progress: 68, progressLabel: '到账经费 ¥2,860 万',
    trendUp: true, trendText: '同比 +15.6%', color: '#3B82F6',
    sparkline: '0,16 14,14 28,17 42,15 56,18 70,16 84,19 100,14',
  },
  {
    label: '智库成果', value: '35', unit: '篇', progress: 70, progressLabel: '省部级以上采纳 28 篇',
    trendUp: false, trendText: '同比 -3.1%', color: '#64748B',
    sparkline: '0,12 14,14 28,11 42,15 56,12 70,14 84,10 100,13',
  },
  {
    label: '政策咨询报告', value: '48', unit: '份', progress: 85, progressLabel: '服务数字政府与基层治理',
    trendUp: true, trendText: '同比 +22.0%', color: '#0891B2',
    sparkline: '0,10 14,13 28,9 42,14 56,11 70,15 84,12 100,16',
  },
  {
    label: '专著教材', value: '38', unit: '部', progress: 62, progressLabel: '国家级规划教材 12 部',
    trendUp: true, trendText: '同比 +5.8%', color: '#4B5563',
    sparkline: '0,18 14,15 28,17 42,16 56,18 70,15 84,19 100,14',
  },
]

// ========== 11. 科研成果趋势图 (折线 + 面积图) ==========
function initResearchTrendChart() {
  if (!researchTrendChartRef.value) return
  researchTrendChart = echarts.init(researchTrendChartRef.value)
  const years = ['2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025']
  researchTrendChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 11 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
    },
    legend: {
      bottom: 0,
      textStyle: { color: '#6B7280', fontSize: 10 },
      itemWidth: 16,
      itemHeight: 2,
      itemGap: 16,
    },
    grid: { top: 15, right: 20, bottom: 38, left: 48 },
    xAxis: {
      type: 'category',
      data: years,
      axisLabel: { color: '#6B7280', fontSize: 10 },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: '#E5E7EB' } },
    },
    yAxis: [
      {
        type: 'value',
        name: '论文(篇)',
        nameTextStyle: { color: '#9CA3AF', fontSize: 9 },
        axisLabel: { color: '#6B7280', fontSize: 9 },
        splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
      },
      {
        type: 'value',
        name: '项目(项)',
        nameTextStyle: { color: '#9CA3AF', fontSize: 9 },
        axisLabel: { color: '#6B7280', fontSize: 9 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: 'CSSCI/SSCI 论文',
        type: 'line',
        data: [68, 76, 82, 95, 108, 122, 139, 156],
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5, color: '#1E3A8A' },
        itemStyle: { color: '#1E3A8A', borderColor: '#FFF', borderWidth: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(30,58,138,0.18)' },
            { offset: 1, color: 'rgba(30,58,138,0.0)' },
          ]),
        },
      },
      {
        name: '国家社科基金',
        type: 'line',
        yAxisIndex: 1,
        data: [8, 9, 10, 12, 14, 16, 18, 22],
        smooth: true,
        symbol: 'diamond',
        symbolSize: 7,
        lineStyle: { width: 2.5, color: '#3B82F6' },
        itemStyle: { color: '#3B82F6', borderColor: '#FFF', borderWidth: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59,130,246,0.15)' },
            { offset: 1, color: 'rgba(59,130,246,0.0)' },
          ]),
        },
      },
      {
        name: '横向科研项目',
        type: 'line',
        yAxisIndex: 1,
        data: [14, 18, 20, 24, 28, 32, 36, 42],
        smooth: true,
        symbol: 'triangle',
        symbolSize: 8,
        lineStyle: { width: 2, color: '#64748B', type: 'dashed' },
        itemStyle: { color: '#64748B', borderColor: '#FFF', borderWidth: 1.5 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(100,116,139,0.12)' },
            { offset: 1, color: 'rgba(100,116,139,0.0)' },
          ]),
        },
      },
    ],
  })
}

// ========== 12. 教师科研贡献排行 (横向条形图) ==========
function initResearchRankChart() {
  if (!researchRankChartRef.value) return
  researchRankChart = echarts.init(researchRankChartRef.value)
  const rankData = [
    { name: '示例01', papers: 28, projects: 8, funding: 580 },
    { name: '示例02', papers: 24, projects: 7, funding: 420 },
    { name: '示例03', papers: 22, projects: 6, funding: 390 },
    { name: '示例04', papers: 18, projects: 5, funding: 280 },
    { name: '示例05', papers: 16, projects: 4, funding: 220 },
    { name: '示例06', papers: 14, projects: 3, funding: 180 },
    { name: '示例07', papers: 12, projects: 3, funding: 150 },
  ]
  const sorted = [...rankData].sort((a, b) => {
    const sa = a.papers * 2 + a.projects * 5 + a.funding * 0.1
    const sb = b.papers * 2 + b.projects * 5 + b.funding * 0.1
    return sa - sb
  })

  researchRankChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E7EB',
      textStyle: { color: '#374151', fontSize: 11 },
      boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
      formatter: (params: any) => {
        const found = sorted.find((s: any) => s.name === params[0].name)
        if (!found) return ''
        return `<b>${found.name}</b><br/>论文：${found.papers} 篇<br/>项目：${found.projects} 项<br/>科研经费：¥${found.funding} 万`
      },
    },
    grid: { top: 10, right: 30, bottom: 10, left: 50 },
    xAxis: {
      type: 'value',
      name: '综合指数',
      nameTextStyle: { color: '#9CA3AF', fontSize: 9 },
      axisLabel: { color: '#6B7280', fontSize: 9 },
      splitLine: { lineStyle: { color: '#F3F4F6', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: sorted.map(d => d.name),
      axisLabel: { color: '#6B7280', fontSize: 10, fontWeight: 500 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: sorted.map((d, i) => {
          const score = d.papers * 2 + d.projects * 5 + d.funding * 0.1
          const alpha = 1 - i * 0.08
          return {
            value: score,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: `rgba(30,58,138,${alpha})` },
                { offset: 1, color: `rgba(147,197,253,${alpha * 0.6})` },
              ]),
              borderRadius: [0, 4, 4, 0],
            },
          }
        }),
        barWidth: 14,
        label: {
          show: true,
          position: 'right',
          color: '#374151',
          fontSize: 10,
          fontWeight: 600,
          formatter: (p: any) => {
            const d = sorted[p.dataIndex]
           return `${d?.papers ?? 0}篇 ${d?.projects ?? 0}项`
          },
        },
      },
    ],
  })
}

// ========== Lifecycle ==========
onMounted(async () => {
  await nextTick()
  initTitleDistChart()
  void loadFacultyDirectory()
  initWorkloadChart()
  initRelationChart()
  initAgeChart()
  initEvalChart()
  initResearchTrendChart()
  initResearchRankChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (selectedProfile.value) closeTeacherDetail()
  titleDistChart?.dispose()
  workloadChart?.dispose()
  relationChart?.dispose()
  ageChart?.dispose()
  evalChart?.dispose()
  researchTrendChart?.dispose()
  researchRankChart?.dispose()
  window.removeEventListener('resize', handleResize)
})

function handleResize() {
  titleDistChart?.resize()
  workloadChart?.resize()
  relationChart?.resize()
  ageChart?.resize()
  evalChart?.resize()
  researchTrendChart?.resize()
  researchRankChart?.resize()
}
</script>

<style scoped>
/* ============================================================
   FACULTY HUB — 教师资源与教学能力中心 样式
   设计方向：专家库 / 人员画像 / 学术感
   主色调：蓝系 (#1E3A8A → #93C5FD)
   ============================================================ */

/* ---- Layout ---- */
.faculty-hub {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 0;
}

/* ---- Topbar ---- */
.hub-topbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
}
.hub-title-area { flex: 1; min-width: 260px; }
.hub-title {
  font-size: 22px; font-weight: 700; color: var(--text-title);
  display: flex; align-items: center; gap: 10px; margin: 0; line-height: 1.3;
}
.hub-title-icon { width: 22px; height: 22px; color: var(--color-primary); flex-shrink: 0; }
.hub-subtitle { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
.hub-actions { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }

/* ---- Chip Filter Group ---- */
.chip-group { display: flex; gap: 4px; background: #F3F4F6; border-radius: 8px; padding: 3px; }
.chip-filter {
  border: none; background: transparent; padding: 6px 14px;
  font-size: 12px; font-weight: 500; color: #6B7280; border-radius: 6px;
  cursor: pointer; transition: all 0.2s;
}
.chip-filter.active { background: #FFF; color: #1E3A8A; box-shadow: 0 1px 3px rgba(0,0,0,0.08); font-weight: 600; }
.chip-filter:hover:not(.active) { color: #374151; }

/* ---- Buttons ---- */
.btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  border: none; background: #1E3A8A; color: #FFF; padding: 8px 18px;
  border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.btn-primary svg { width: 16px; height: 16px; }
.btn-primary:hover { background: #1E40AF; box-shadow: 0 2px 8px rgba(30,58,138,0.3); }
.btn-outline {
  display: inline-flex; align-items: center; gap: 6px;
  border: 1px solid #D1D5DB; background: #FFF; color: #374151;
  padding: 8px 18px; border-radius: 8px; font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
}
.btn-outline svg { width: 16px; height: 16px; }
.btn-outline:hover { background: #F9FAFB; border-color: #9CA3AF; }

/* ---- Stat Row ---- */
.hub-stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.hub-stat-card {
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: 12px; padding: 20px 22px; display: flex; align-items: center;
  gap: 16px; position: relative; overflow: hidden; transition: all 0.25s; cursor: default;
}
.hub-stat-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.08); transform: translateY(-2px); }
.hub-stat-icon {
  width: 46px; height: 46px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.hub-stat-icon svg { width: 20px; height: 20px; }
.hub-stat-body { flex: 1; min-width: 0; }
.hub-stat-label { font-size: 12px; color: var(--text-muted); font-weight: 500; }
.hub-stat-value { display: flex; align-items: baseline; gap: 4px; margin-top: 2px; }
.hub-stat-num { font-size: 30px; font-weight: 700; color: var(--text-title); line-height: 1.1; }
.hub-stat-unit { font-size: 13px; color: var(--text-muted); font-weight: 500; }
.hub-stat-sub { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.hub-stat-spark { position: absolute; bottom: 8px; right: 16px; opacity: 0.35; pointer-events: none; }
.spark-svg { width: 60px; height: 22px; }

/* ---- Grid Layouts ---- */
.hub-row-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

/* ---- Panel ---- */
.hub-panel {
  background: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: 12px; padding: 20px 22px; display: flex; flex-direction: column;
}
.hub-panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-shrink: 0; }
.hub-panel-title { font-size: 15px; font-weight: 600; color: var(--text-title); display: flex; align-items: center; gap: 8px; }
.panel-title-icon { width: 16px; height: 16px; color: var(--color-primary); flex-shrink: 0; }
.hub-panel-badge {
  font-size: 11px; background: #EFF6FF; color: var(--color-primary);
  padding: 3px 10px; border-radius: 6px; font-weight: 500; white-space: nowrap;
}

/* ---- Chart Wrap ---- */
.hub-chart-wrap { flex: 1; min-height: 260px; width: 100%; }

/* ---- Profile Grid ---- */
.profile-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  flex: 1;
}
.profile-card {
  background: #F9FAFB; border: 1px solid #F3F4F6; border-radius: 10px;
  padding: 14px; cursor: pointer; transition: all 0.2s;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.profile-card:hover { background: #EFF6FF; border-color: #BFDBFE; box-shadow: 0 2px 12px rgba(30,58,138,0.06); }
.profile-card:focus-visible { outline: 2px solid #3B82F6; outline-offset: 2px; }
.profile-avatar {
  width: 48px; height: 48px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #FFF; font-size: 14px; font-weight: 700;
  position: relative;
}
.avatar-1 { background: linear-gradient(135deg, #1E3A8A, #3B82F6); }
.avatar-2 { background: linear-gradient(135deg, #3B82F6, #60A5FA); }
.profile-level-dot {
  position: absolute; bottom: 0; right: 0;
  width: 10px; height: 10px; background: #10B981; border: 2px solid #FFF; border-radius: 50%;
}
.profile-info { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.profile-name { font-size: 13px; font-weight: 600; color: var(--text-title); }
.profile-title-tag { font-size: 10px; color: #3B82F6; background: #EFF6FF; padding: 1px 8px; border-radius: 4px; font-weight: 500; }
.profile-college { font-size: 10px; color: var(--text-muted); }
.profile-meta { display: flex; gap: 12px; }
.pm-item { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.pm-num { font-size: 14px; font-weight: 700; color: var(--text-title); }
.pm-high { color: #1E3A8A; }
.pm-label { font-size: 9px; color: var(--text-muted); }
.profile-bar { width: 100%; height: 3px; background: #F3F4F6; border-radius: 2px; overflow: hidden; }
.profile-bar-fill { height: 100%; border-radius: 2px; transition: width 0.4s; }

/* ---- Star Teachers ---- */
.star-teachers { display: flex; flex-direction: column; gap: 4px; }
.star-item {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px; border-radius: 10px; transition: background 0.15s;
}
.star-item:nth-child(1) { background: linear-gradient(135deg, #FFFDF0, #FFFBEB); }
.star-item:nth-child(2) { background: #F9FAFB; }
.star-item:nth-child(3) { background: #F9FAFB; }
.star-item:hover { background: #EFF6FF; }
.star-medal {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; flex-shrink: 0;
  background: #F3F4F6; font-weight: 700; color: #6B7280;
}
.medal-1 { background: #FFFBEB; }
.medal-2 { background: #F3F4F6; }
.medal-3 { background: #FDF2F8; }
.star-info { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.star-name { font-size: 13px; font-weight: 600; color: var(--text-title); }
.star-college { font-size: 10px; color: var(--text-muted); }
.star-metrics { display: flex; gap: 12px; flex-shrink: 0; }
.sm-col { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.sm-val { font-size: 14px; font-weight: 700; color: var(--text-title); }
.sm-label { font-size: 9px; color: var(--text-muted); }
.star-comment { font-size: 11px; color: var(--text-muted); font-style: italic; max-width: 180px; text-align: right; }

/* ---- Research Panel (科研驾驶舱) ---- */
.hub-panel--research {
  overflow-y: auto;
}

/* ---- Research Overview — 6 横向指标卡片 ---- */
.research-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 10px;
}
.research-indicator {
  background: #F9FAFB;
  border: 1px solid #F3F4F6;
  border-radius: 8px;
  padding: 10px 12px;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 98px;
}
.research-indicator:hover {
  background: #F0F5FF;
  border-color: #DBEAFE;
  box-shadow: 0 1px 6px rgba(30,58,138,0.05);
}

.ri-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ri-label {
  font-size: 11px;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ri-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 10px;
  font-weight: 600;
  white-space: nowrap;
}
.trend-up { color: #059669; }
.trend-down { color: #DC2626; }
.ri-trend-icon { width: 14px; height: 14px; flex-shrink: 0; }

.ri-value-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.ri-value {
  font-size: 26px;
  font-weight: 700;
  color: #111827;
  line-height: 1;
  font-feature-settings: "tnum";
  font-variant-numeric: tabular-nums;
}
.ri-unit {
  font-size: 11px;
  color: #9CA3AF;
  font-weight: 500;
}

.ri-progress-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ri-progress-bar {
  width: 100%;
  height: 3px;
  background: #E5E7EB;
  border-radius: 2px;
  overflow: hidden;
}
.ri-progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.6s ease;
}
.ri-progress-label {
  font-size: 9px;
  color: #9CA3AF;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ri-sparkline {
  margin-top: 2px;
  height: 20px;
}
.ri-spark-svg {
  width: 100%;
  height: 20px;
}

/* ---- Research Charts Row ---- */
.research-charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  flex: 1;
  min-height: 240px;
}
.research-chart-panel {
  background: #F9FAFB;
  border: 1px solid #F3F4F6;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  min-height: 240px;
}
.rch-title {
  font-size: 12px;
  font-weight: 600;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  flex-shrink: 0;
}
.rch-title-icon {
  width: 14px;
  height: 14px;
  color: #3B82F6;
  flex-shrink: 0;
}
.rch-chart-wrap {
  flex: 1;
  min-height: 190px;
  width: 100%;
}

/* ---- Research responsive overrides ---- */
@media (max-width: 1600px) {
  .research-overview {
    grid-template-columns: repeat(2, 1fr);
  }
  .research-charts-row {
    grid-template-columns: 1fr;
  }
}

/* ---- Heatmap ---- */
.heatmap-legend { display: flex; align-items: center; gap: 3px; font-size: 10px; color: var(--text-muted); }
.heatmap-legend-bar { width: 14px; height: 14px; border-radius: 2px; }
.hl-1 { background: #DBEAFE; } .hl-2 { background: #93C5FD; } .hl-3 { background: #60A5FA; } .hl-4 { background: #3B82F6; } .hl-5 { background: #1E3A8A; }

.heatmap-grid { display: flex; flex-direction: column; gap: 2px; flex: 1; }
.heatmap-header-row { display: flex; gap: 3px; align-items: center; margin-top: 4px; }
.heatmap-row { display: flex; gap: 3px; align-items: center; }
.hm-teacher { width: 52px; font-size: 10px; color: var(--text-secondary); text-align: right; padding-right: 6px; flex-shrink: 0; }
.hm-col-label { flex: 1; text-align: center; font-size: 9px; color: var(--text-muted); }
.hm-cell {
  flex: 1; text-align: center; font-size: 11px; font-weight: 600; color: #FFF;
  padding: 6px 0; border-radius: 4px; transition: transform 0.15s; cursor: default;
}
.hm-cell:hover { transform: scale(1.15); }
.hm-level-1 { background: #DBEAFE; color: #6B7280; }
.hm-level-2 { background: #93C5FD; color: #1E3A8A; }
.hm-level-3 { background: #60A5FA; color: #FFF; }
.hm-level-4 { background: #3B82F6; color: #FFF; }
.hm-level-5 { background: #1E3A8A; color: #FFF; }

/* ---- Team List ---- */
.team-list { display: flex; flex-direction: column; gap: 10px; flex: 1; }
.team-item {
  background: #F9FAFB; border-radius: 10px; padding: 14px;
  transition: all 0.15s;
}
.team-item:hover { background: #EFF6FF; }
.team-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.team-name { font-size: 13px; font-weight: 600; color: var(--text-title); }
.team-leader { font-size: 10px; color: #3B82F6; }
.team-members { display: flex; gap: 4px; margin-bottom: 8px; }
.team-avatar-sm {
  width: 24px; height: 24px; border-radius: 50%;
  background: #DBEAFE; color: #1E3A8A;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 600; cursor: default;
}
.team-stats { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.ts-item { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.ts-val { font-size: 12px; font-weight: 700; color: var(--text-title); }
.ts-label { font-size: 9px; color: var(--text-muted); }
.team-strength { flex: 1; min-width: 80px; }
.ts-bar-bg { width: 100%; height: 4px; background: #F3F4F6; border-radius: 2px; overflow: hidden; margin-bottom: 2px; }
.ts-bar-fill { height: 100%; border-radius: 2px; background: linear-gradient(90deg, #1E3A8A, #3B82F6); transition: width 0.4s; }
.ts-strength-label { font-size: 9px; color: var(--text-muted); }

/* ---- Teacher detail drawer: aligned with the student profile drawer ---- */
.teacher-drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(1px);
  animation: teacher-drawer-fade-in 0.18s ease-out;
}
@keyframes teacher-drawer-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
.teacher-drawer-panel {
  display: flex;
  flex-direction: column;
  width: 480px;
  max-width: 92vw;
  height: 100%;
  min-height: 0;
  background: #FFF;
  box-shadow: -8px 0 28px rgba(15, 23, 42, 0.16);
  animation: teacher-drawer-slide-in 0.26s cubic-bezier(0.2, 0.75, 0.25, 1);
}
@keyframes teacher-drawer-slide-in {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
.teacher-drawer-header {
  flex-shrink: 0;
  padding: 24px;
  border-bottom: 1px solid #F1F5F9;
}
.teacher-drawer-header-main {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}
.teacher-drawer-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 62px;
  height: 62px;
  flex-shrink: 0;
  border-radius: 15px;
  color: #FFF;
  font-size: 23px;
  font-weight: 700;
  background: linear-gradient(135deg, #1E3A8A, #3B82F6);
}
.teacher-drawer-avatar.avatar-2 {
  background: linear-gradient(135deg, #2563EB, #60A5FA);
}
.teacher-drawer-title {
  flex: 1;
  min-width: 0;
}
.teacher-drawer-title h3 {
  margin: 0 0 4px;
  color: #1F2937;
  font-size: 20px;
  font-weight: 700;
  line-height: 1.4;
}
.teacher-drawer-title p {
  margin: 0 0 9px;
  color: #94A3B8;
  font-size: 12px;
}
.teacher-drawer-status-row {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}
.teacher-drawer-status,
.teacher-drawer-title-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
}
.teacher-drawer-status {
  color: #059669;
  background: #ECFDF5;
}
.teacher-drawer-title-badge {
  color: #2563EB;
  background: #EFF6FF;
}
.teacher-drawer-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  background: #FFF;
  color: #64748B;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.teacher-drawer-close:hover {
  background: #F8FAFC;
  border-color: #CBD5E1;
}
.teacher-drawer-close svg {
  width: 18px;
  height: 18px;
}
.teacher-drawer-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 23px;
  overscroll-behavior: contain;
}
.teacher-drawer-section {
  min-width: 0;
}
.teacher-drawer-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
  color: #1F2937;
  font-size: 13px;
  font-weight: 700;
}
.teacher-drawer-section-title::before {
  content: '';
  display: block;
  width: 4px;
  height: 14px;
  flex-shrink: 0;
  border-radius: 2px;
  background: #1E40AF;
}
.teacher-drawer-info-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.teacher-drawer-info-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
  padding: 10px 11px;
  border-radius: 8px;
  background: #F8FAFC;
}
.teacher-drawer-info-item span,
.teacher-drawer-metric > span {
  color: #94A3B8;
  font-size: 10px;
}
.teacher-drawer-info-item strong {
  overflow-wrap: anywhere;
  color: #334155;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.5;
}
.teacher-drawer-info-wide {
  grid-column: 1 / -1;
}
.teacher-drawer-intro {
  margin: 10px 0 0;
  padding: 10px 12px;
  border-left: 3px solid #BFDBFE;
  border-radius: 0 7px 7px 0;
  background: #F8FAFC;
  color: #64748B;
  font-size: 11px;
  line-height: 1.8;
}
.teacher-drawer-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.teacher-drawer-metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 0;
  min-height: 74px;
  padding: 9px 5px;
  border-radius: 8px;
  background: #F8FAFC;
  text-align: center;
}
.teacher-drawer-metric strong {
  color: #1F2937;
  font-size: 17px;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
}
.teacher-drawer-metric strong small,
.teacher-drawer-score-head strong small {
  margin-left: 2px;
  color: #94A3B8;
  font-size: 10px;
  font-weight: 500;
}
.teacher-drawer-research-metrics {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.teacher-drawer-subsection {
  margin-top: 14px;
}
.teacher-drawer-subsection h5 {
  margin: 0 0 9px;
  color: #475569;
  font-size: 11px;
  font-weight: 700;
}
.teacher-drawer-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.teacher-drawer-tags span {
  display: inline-flex;
  padding: 5px 8px;
  border-radius: 5px;
  background: #EFF6FF;
  color: #1D4ED8;
  font-size: 10px;
  line-height: 1.3;
}
.teacher-drawer-skill-tags span {
  background: #F1F5F9;
  color: #475569;
}
.teacher-drawer-score {
  margin-top: 13px;
}
.teacher-drawer-score-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 7px;
  color: #64748B;
  font-size: 11px;
}
.teacher-drawer-score-head strong {
  color: #1E40AF;
  font-size: 12px;
}
.teacher-drawer-progress {
  width: 100%;
  height: 5px;
  overflow: hidden;
  border-radius: 999px;
  background: #EFF2F7;
}
.teacher-drawer-progress span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #2563EB, #60A5FA);
  transition: width 0.25s ease;
}
.teacher-drawer-team-card {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 12px;
  border: 1px solid #EFF2F7;
  border-radius: 9px;
  background: #FAFBFC;
}
.teacher-drawer-team-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border-radius: 9px;
  background: #E8F0FF;
  color: #1E40AF;
  font-size: 17px;
  font-weight: 700;
}
.teacher-drawer-team-card strong {
  color: #334155;
  font-size: 12px;
}
.teacher-drawer-team-card p {
  margin: 4px 0 0;
  color: #94A3B8;
  font-size: 10px;
}
.teacher-drawer-timeline {
  display: flex;
  flex-direction: column;
  gap: 13px;
}
.teacher-drawer-timeline-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.teacher-drawer-timeline-dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  margin-top: 4px;
  border-radius: 50%;
  background: #1E40AF;
  box-shadow: 0 0 0 3px #EFF6FF;
}
.teacher-drawer-timeline-item > div {
  flex: 1;
  min-width: 0;
}
.teacher-drawer-timeline-item time {
  display: block;
  margin-bottom: 3px;
  color: #94A3B8;
  font-size: 10px;
}
.teacher-drawer-timeline-item p {
  margin: 0;
  color: #475569;
  font-size: 11px;
  line-height: 1.7;
}
.teacher-drawer-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  flex-shrink: 0;
  padding: 14px 24px;
  border-top: 1px solid #F1F5F9;
  background: #FFF;
}
.teacher-drawer-export,
.teacher-drawer-confirm {
  min-height: 38px;
  padding: 0 16px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.teacher-drawer-export {
  border: 1px solid #D8DEE8;
  background: #FFF;
  color: #334155;
}
.teacher-drawer-export:hover {
  border-color: #94A3B8;
  background: #F8FAFC;
}
.teacher-drawer-confirm {
  border: 1px solid #1E40AF;
  background: #1E40AF;
  color: #FFF;
}
.teacher-drawer-confirm:hover {
  border-color: #1D4ED8;
  background: #1D4ED8;
}

/* ---- 教师画像：本学期授课课程详情（只影响右侧教师抽屉） ---- */
.teacher-current-courses-heading { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.teacher-current-courses-heading .teacher-drawer-section-title { margin-bottom: 0; }
.teacher-current-term { color: #1D4ED8; background: #EFF6FF; border-radius: 6px; padding: 5px 8px; font-size: 10px; font-weight: 600; }
.teacher-current-tip { color: #94A3B8; font-size: 11px; line-height: 1.7; margin: 10px 0 12px; }
.teacher-course-empty { padding: 18px 12px; border-radius: 9px; background: #F8FAFC; color: #64748B; font-size: 12px; line-height: 1.8; text-align: center; }
.teacher-course-error { color: #B45309; background: #FFFBEB; }
.teacher-course-count { margin: 0 0 10px; font-size: 11px; color: #475569; }
.teacher-course-list { display: flex; flex-direction: column; gap: 10px; }
.teacher-course-card { padding: 14px 13px; border: 1px solid #E9EFF8; border-radius: 10px; background: #FFF; }
.teacher-course-card-top { display: flex; align-items: start; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
.teacher-course-card-top > div { min-width: 0; }
.teacher-course-card-top h5 { margin: 0 0 5px; color: #1E293B; font-size: 13px; line-height: 1.5; }
.teacher-course-card-top > div > span { color: #94A3B8; font-size: 10px; }
.teacher-course-type { max-width: 42%; padding: 4px 7px; background: #EFF6FF; color: #2563EB; border-radius: 5px; font-size: 10px; text-align: center; }
.teacher-course-fields { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.teacher-course-fields > div { display: flex; flex-direction: column; gap: 5px; padding: 8px 9px; background: #F8FAFC; border-radius: 6px; min-width: 0; }
.teacher-course-fields span { font-size: 10px; color: #94A3B8; }
.teacher-course-fields strong { font-size: 11px; line-height: 1.5; color: #334155; font-weight: 600; overflow-wrap: anywhere; }

/* ---- 顶部专业筛选、教师登记与报表交互（只新增必要样式） ---- */
.profile-filter-empty { grid-column: 1 / -1; padding: 38px 12px; color: #94A3B8; text-align: center; font-size: 12px; }
.faculty-operation-notice { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 14px; border-radius: 8px; background: #EFF6FF; border: 1px solid #DBEAFE; color: #1E40AF; font-size: 12px; line-height: 1.6; }
.faculty-operation-notice button { border: 0; background: transparent; color: inherit; cursor: pointer; font-size: 18px; }
.btn-outline:disabled { opacity: 0.65; cursor: wait; }
.talent-modal-backdrop { position: fixed; z-index: 3000; inset: 0; display: flex; align-items: center; justify-content: center; padding: 18px; background: rgba(11, 22, 43, 0.57); }
.talent-modal { width: min(640px, 100%); max-height: min(92vh, 850px); display: flex; flex-direction: column; overflow: hidden; border-radius: 16px; background: #FFF; color: #1E293B; box-shadow: 0 22px 90px rgba(15, 23, 42, 0.22); }
.talent-modal-header { padding: 23px 26px 17px; border-bottom: 1px solid #EEF2F7; display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; }
.talent-modal-header h3 { margin: 0; color: #142543; font-size: 19px; font-weight: 700; }
.talent-modal-header p { margin: 8px 0 0; color: #94A3B8; font-size: 12px; }
.talent-close { width: 32px; height: 32px; border: 1px solid #E2E8F0; border-radius: 8px; background: #FFF; color: #64748B; font-size: 22px; line-height: 1; cursor: pointer; }
.talent-modal-body { overflow-y: auto; padding: 20px 26px 24px; }
.talent-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.talent-field { min-width: 0; display: flex; flex-direction: column; gap: 7px; color: #475569; font-size: 12px; }
.talent-field span { font-weight: 600; }
.talent-field b { color: #E11D48; }
.talent-field input, .talent-field select, .talent-field textarea { box-sizing: border-box; width: 100%; min-height: 39px; border: 1px solid #DEE6F0; background: #FBFCFE; border-radius: 8px; padding: 8px 11px; outline: none; font-family: inherit; font-size: 13px; color: #334155; }
.talent-field textarea { resize: vertical; line-height: 1.6; }
.talent-field input:focus, .talent-field select:focus, .talent-field textarea:focus { border-color: #3B82F6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
.talent-field-full { grid-column: 1 / -1; }
.talent-error { padding: 10px 12px; margin-bottom: 14px; border-radius: 8px; color: #B91C1C; background: #FEF2F2; font-size: 12px; line-height: 1.7; }
.talent-muted { margin: 13px 0; color: #94A3B8; font-size: 11px; line-height: 1.8; }
.talent-modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding-top: 16px; }
.talent-submit, .talent-cancel { padding: 10px 19px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 12px; }
.talent-submit { border: 1px solid #1E40AF; background: #1E40AF; color: #FFF; }
.talent-submit:hover:not(:disabled) { background: #1D4ED8; }
.talent-submit:disabled { cursor: wait; opacity: 0.55; }
.talent-cancel { background: #FFF; color: #475569; border: 1px solid #DEE6F0; }
.talent-saved { text-align: center; }
.talent-saved h4 { font-size: 18px; margin: 9px 0; }
.talent-saved > p:not(.talent-muted) { color: #334155; font-size: 13px; }
.talent-saved-icon { display: inline-flex; width: 48px; height: 48px; align-items: center; justify-content: center; background: #ECFDF5; color: #059669; border-radius: 50%; font-size: 25px; }
@media (max-width: 560px) { .talent-form-grid { grid-template-columns: 1fr; } .talent-modal-header, .talent-modal-body { padding-left: 17px; padding-right: 17px; } }

/* ---- Responsive ---- */
@media (max-width: 1600px) {
  .hub-stats-row { grid-template-columns: repeat(2, 1fr); }
  .profile-grid { grid-template-columns: repeat(2, 1fr); }
  .research-grid { grid-template-columns: 1fr 1fr; }
  .research-summary { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 1200px) {
  .hub-row-2col { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .teacher-drawer-panel { width: 100%; max-width: 100vw; }
  .teacher-drawer-header { padding: 18px; }
  .teacher-drawer-body { padding: 18px; }
  .teacher-drawer-footer { padding: 12px 18px; }
  .teacher-drawer-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .teacher-drawer-research-metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .hub-stats-row { grid-template-columns: 1fr; }
  .hub-stat-num { font-size: 24px; }
  .hub-stat-card { padding: 14px 16px; }
  .profile-grid { grid-template-columns: 1fr; }
  .research-grid { grid-template-columns: 1fr; }
  .star-item { flex-wrap: wrap; }
  .star-comment { max-width: 100%; text-align: left; }
}
.teacher-official-portrait { width: 100%; height: 100%; object-fit: cover; object-position: center 32%; border-radius: inherit; display: block; }
</style>