<template>
  <div class="portrait-page">
    <div class="page-header">
      <div class="header-row">
        <h2>师生画像分析</h2>
        <div class="tab-container-inline">
          <button 
            v-for="tab in tabs" 
            :key="tab.key"
            :class="['tab-btn', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>
     
    </div>

    <div v-if="activeTab === 'teacher'" class="teacher-section">
      <!-- 教师子标签：整体画像 / 个人画像 -->
      <div class="data-source-bar">
        <span class="src-tag src-a">A 官网真实</span>
        <span>教师 93 人 / 个人主页 88 人、学术成果 597 条、通知 899 条</span>
        <span class="src-tag src-b">B 真实采集</span>
        <span>学院绩效评分 CSV 103 人（按姓名匹配 88 人）、官网论文题录 375 篇</span>
        <span v-if="portraitLoading" class="src-loading">正在加载…</span>
        <span v-else-if="portraitError" class="src-error">{{ portraitError }}</span>
      </div>
      <div class="sub-tab-container">
        <button
          :class="['sub-tab-btn', { active: teacherView === 'overall' }]"
          @click="teacherView = 'overall'"
        >
          📊 教师整体画像
        </button>
        <button
          :class="['sub-tab-btn', { active: teacherView === 'individual' }]"
          @click="teacherView = 'individual'"
        >
          👨‍🏫 教师个人画像
        </button>
      </div>

      <!-- ========== 教师整体画像 ========== -->
      <div v-if="teacherView === 'overall'" class="overall-teacher-section">
        <div class="overall-kpi-row">
          <div class="okpi-card" v-for="kpi in overallKpi" :key="kpi.label">
            <div class="okpi-icon" :style="{ background: kpi.bg }">{{ kpi.icon }}</div>
            <div class="okpi-info">
              <span class="okpi-value">{{ kpi.value }}<i>{{ kpi.unit }}</i></span>
              <span class="okpi-label">{{ kpi.label }}</span>
              <span class="okpi-trend" :style="{ color: kpi.trendColor }">{{ kpi.trend }}</span>
            </div>
          </div>
        </div>

        <!-- 第一行：4个Mini图表 -->
        <div class="overall-charts-row four-cols">
          <div class="mini-chart-card">
            <div class="mc-header">📄 官网学术成果年度新增</div>
            <div ref="overallPaperChart" class="mc-body"></div>
          </div>
          <div class="mini-chart-card">
            <div class="mc-header">📋 官网学术成果类别</div>
            <div ref="overallProjectChart" class="mc-body"></div>
          </div>
          <div class="mini-chart-card">
            <div class="mc-header">🏛️ 官网教师职称构成</div>
            <div ref="overallFeeChart" class="mc-body"></div>
          </div>
          <div class="mini-chart-card">
            <div class="mc-header">📣 官网通知公告年度发布</div>
            <div ref="overallTeacherChart" class="mc-body"></div>
          </div>
        </div>

        <!-- 第二行：师资力量（手动布局） + 主要研究词云 -->
        <div class="overall-charts-row">
          <div class="half-chart-card">
            <div class="mc-header">
              <span>📊 师资力量</span>
              <div class="strength-legend">
                <span class="legend-item"><span class="legend-dot" style="background:#7b2cbf"></span>已纳入绩效评分</span>
                <span class="legend-item"><span class="legend-dot" style="background:rgba(0,212,255,0.45)"></span>未纳入评分</span>
              </div>
            </div>
            <div class="strength-body">
              <div class="strength-row" v-for="s in teacherStrength" :key="s.title">
                <div class="s-left">
                  <span class="s-icon">{{ s.icon }}</span>
                  <div>
                    <div class="s-title">{{ s.title }}</div>
                    <div class="s-total">{{ s.total }}人</div>
                  </div>
                </div>
                <div class="s-bar-area">
                  <div class="s-bar-bg">
                    <div class="s-seg" v-for="b in s.bars" :key="b.label"
                      :style="{ width: b.percent + '%', background: b.color, boxShadow: 'inset 0 0 6px rgba(255,255,255,0.25)' }">
                    </div>
                  </div>
                </div>
                <div class="s-right">
                  <span class="s-num" v-for="b in s.bars" :key="b.label"
                    :style="{ color: b.color }">{{ b.count }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="half-chart-card">
            <div class="mc-header">
              <span>🔬 主要研究领域</span>
              <div class="zoom-controls">
                <button class="zoom-btn" @click="adjustWordCloudZoom(-0.2)" title="缩小">−</button>
                <span class="zoom-label">{{ Math.round(wordCloudZoom * 100) }}%</span>
                <button class="zoom-btn" @click="adjustWordCloudZoom(0.2)" title="放大">+</button>
              </div>
            </div>
            <div ref="overallWordCloud" class="mc-body wordcloud-body"></div>
          </div>
        </div>

        <!-- 第三行：培养经历世界地图 + 绩效指标雷达 -->
        <div class="overall-charts-row">
          <div class="wide-chart-card">
            <div class="mc-header">
              <span>🌍 培养经历（教师教育背景全球分布）</span>
              <span v-if="globeStat" class="mc-sub">{{ globeStat }}</span>
            </div>
            <div ref="overallGlobeChart" class="mc-body globe-body"></div>
          </div>
          <div class="half-chart-card">
            <div class="mc-header">
              <span>🎯 绩效指标分析</span>
              <div class="zoom-controls">
                <button class="zoom-btn" @click="adjustRadarZoom(-0.15)" title="缩小">−</button>
                <span class="zoom-label">{{ Math.round(radarZoom * 100) }}%</span>
                <button class="zoom-btn" @click="adjustRadarZoom(0.15)" title="放大">+</button>
              </div>
            </div>
            <div ref="overallRadarChart" class="mc-body radar-body"></div>
          </div>
        </div>

        <!-- 第四行：绩效成绩总览 -->
        <div class="score-card">
          <div class="mc-header">🏆 绩效成绩总览</div>
          <div class="score-table-wrap">
            <table class="score-table">
              <thead><tr><th>姓名</th><th>综合得分</th></tr></thead>
              <tbody>
                <tr v-for="(s, i) in scoreData" :key="i" :class="{ even: i % 2 === 0 }">
                  <td>{{ s.name }}</td>
                  <td>{{ s.score }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ========== 教师个人画像 ========== -->
      <div v-if="teacherView === 'individual'">
        <div class="filter-bar">
          <div class="search-box">
            <span class="search-icon">🔍</span>
            <input 
              type="text" 
              v-model="teacherSearch.name" 
              placeholder="搜索教师姓名..."
              @input="filterTeachers"
            />
          </div>
          <select v-model="teacherSearch.title" @change="filterTeachers">
            <option value="">全部职称</option>
            <option v-for="t in ((portraitMeta && portraitMeta.titles) || [])" :key="t.name" :value="t.name">
              {{ t.name }}（{{ t.value }}人）
            </option>
          </select>
          <select v-model="teacherSearch.research" @change="filterTeachers">
            <option value="">全部研究方向</option>
            <option v-for="r in teacherResearchOptions" :key="r" :value="r">{{ r }}</option>
          </select>
          <select v-model="selectedTeacher" @change="loadTeacherData" class="select-teacher">
            <option value="">选择教师</option>
            <option v-for="teacher in filteredTeachers" :key="teacher.id" :value="teacher.id">
              {{ teacher.name }} - {{ teacher.title }}
            </option>
          </select>
        </div>

        <div v-if="currentTeacher" class="portrait-content">
        <div class="info-card level2-card">
          <div class="card-topline"></div>
          <div class="info-header">
            <div class="avatar-ring">
              <div class="avatar">👨‍🏫</div>
            </div>
            <div class="basic-info">
              <h2 class="teacher-name">{{ currentTeacher.name }}</h2>
              <p class="teacher-title">{{ currentTeacher.title }} · {{ currentTeacher.department }}</p>
              <p class="teacher-email">
                <a v-if="currentTeacher.homepage" :href="currentTeacher.homepage" target="_blank" rel="noopener">学院官网个人主页 ↗</a>
                <span v-else>{{ currentTeacher.email }}</span>
              </p>
            </div>
          </div>
          <div class="info-cards-row">
            <div class="info-mini-card wide">
              <span class="info-mini-label">绩效评分年度</span>
              <span class="info-mini-value">{{ currentTeacher.joinYear }}</span>
            </div>
            <div class="info-mini-card wide">
              <span class="info-mini-label">研究方向</span>
              <span class="info-mini-value">{{ currentTeacher.research }}</span>
            </div>
            <div class="info-mini-card">
              <span class="info-mini-label">评分状态</span>
              <span class="info-mini-value">{{ currentTeacher.education }}</span>
            </div>
            <div class="info-mini-card">
              <span class="info-mini-label">收录论文</span>
              <span class="info-mini-value">{{ currentTeacher.students }}篇</span>
            </div>
          </div>
        </div>

        <div class="main-charts-row">
          <div class="chart-card level1-card radar-card">
            <div class="card-topline"></div>
            <h4 class="card-title">教师综合能力雷达图</h4>
            <div ref="radarChart" class="chart-container radar-container"></div>
          </div>

          <div class="chart-card level1-card stats-card">
            <div class="card-topline"></div>
            <h4 class="card-title">教学科研统计</h4>
            <div class="bar-stats-list">
              <div class="bar-stat-item">
                <div class="bar-stat-header">
                  <span class="bar-stat-label">教学绩效分</span>
                  <span class="bar-stat-value">{{ currentTeacher.courses }} / {{ scoreMax.course }}</span>
                </div>
                <div class="bar-stat-track">
                  <div class="bar-stat-fill bar-1" :style="{ width: Math.min(100, currentTeacher.courses / (scoreMax.course || 1) * 100) + '%' }"></div>
                </div>
              </div>
              <div class="bar-stat-item">
                <div class="bar-stat-header">
                  <span class="bar-stat-label">科研项目数</span>
                  <span class="bar-stat-value">{{ currentTeacher.projects }}项</span>
                </div>
                <div class="bar-stat-track">
                  <div class="bar-stat-fill bar-2" :style="{ width: Math.min(100, currentTeacher.projects / 10 * 100) + '%' }"></div>
                </div>
              </div>
              <div class="bar-stat-item">
                <div class="bar-stat-header">
                  <span class="bar-stat-label">论文绩效分</span>
                  <span class="bar-stat-value">{{ currentTeacher.papers }} / {{ scoreMax.paper }}</span>
                </div>
                <div class="bar-stat-track">
                  <div class="bar-stat-fill bar-3" :style="{ width: Math.min(100, currentTeacher.papers / (scoreMax.paper || 1) * 100) + '%' }"></div>
                </div>
              </div>
              <div class="bar-stat-item">
                <div class="bar-stat-header">
                  <span class="bar-stat-label">获奖绩效分</span>
                  <span class="bar-stat-value">{{ currentTeacher.awardScore }} / {{ scoreMax.award }}</span>
                </div>
                <div class="bar-stat-track">
                  <div class="bar-stat-fill bar-4" :style="{ width: Math.min(100, currentTeacher.awardScore / (scoreMax.award || 1) * 100) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bottom-charts-row">
          <div class="chart-card level1-card">
            <div class="card-topline"></div>
            <h4 class="card-title">全院职称分布（高亮本人）</h4>
            <div ref="titleDistributionChart" class="chart-container"></div>
          </div>
          <div class="chart-card level1-card">
            <div class="card-topline"></div>
            <h4 class="card-title">论文分级（A+/A/B/C/D）</h4>
            <div ref="projectLevelChart" class="chart-container"></div>
          </div>
        </div>

        <div class="bottom-charts-row">
          <div class="chart-card level1-card">
            <div class="card-topline"></div>
            <h4 class="card-title">绩效六维评分</h4>
            <div ref="enrollmentChart" class="chart-container"></div>
          </div>
          <div class="chart-card level1-card">
            <div class="card-topline"></div>
            <h4 class="card-title">与全院均值对比</h4>
            <div ref="studentEvalChart" class="chart-container"></div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <span class="empty-icon">👥</span>
        <p>请选择一位教师查看画像</p>
      </div>
      </div>
    </div>

    <div v-if="activeTab === 'student'" class="student-section">
      <p class="demo-note">
        数据说明：学生个体明细（姓名 / 学号 / 绩点 / 导师）不属于官网公开信息，本页为<b>结构演示</b>——
        姓名统一为“示例学生A–L”、学号统一为“示例学号”、导师一栏留待研究生系统接入；
        招生规模可对照官网《学院简介》：每年本科 150 人、学术硕士 120 人、博士 35 人、MPA 400 人、留学生 40 人。
      </p>
      <div class="sub-tab-container">
        <button 
          :class="['sub-tab-btn', { active: studentView === 'individual' }]"
          @click="studentView = 'individual'"
        >
          🧑‍🎓 个人画像
        </button>
        <button 
          :class="['sub-tab-btn', { active: studentView === 'grade' }]"
          @click="studentView = 'grade'"
        >
          📅 年级画像
        </button>
        <button 
          :class="['sub-tab-btn', { active: studentView === 'major' }]"
          @click="studentView = 'major'"
        >
          📚 专业画像
        </button>
        <button 
          :class="['sub-tab-btn', { active: studentView === 'class' }]"
          @click="studentView = 'class'"
        >
          👨‍👩‍👧‍👦 班级画像
        </button>
        <button 
          :class="['sub-tab-btn', { active: studentView === 'undergraduate' }]"
          @click="studentView = 'undergraduate'"
        >
          👨‍🎓 本科生画像
        </button>
        <button 
          :class="['sub-tab-btn', { active: studentView === 'graduate' }]"
          @click="studentView = 'graduate'"
        >
          🎓 研究生画像
        </button>
      </div>

      <div v-if="studentView === 'individual'" class="individual-view">
        <div class="filter-bar">
          <div class="search-box">
            <span class="search-icon">🔍</span>
            <input 
              type="text" 
              v-model="studentSearch.name" 
              placeholder="搜索学生姓名..."
              @input="filterStudents"
            />
          </div>
          <select v-model="studentSearch.major" @change="filterStudents">
            <option value="">全部专业</option>
            <option v-for="m in studentMajorOptions" :key="m" :value="m">{{ m }}</option>
          </select>
          <select v-model="studentSearch.grade" @change="filterStudents">
            <option value="">全部年级</option>
            <option value="2022">2022级</option>
            <option value="2023">2023级</option>
            <option value="2024">2024级</option>
          </select>
          <select v-model="selectedStudent" @change="loadStudentData" class="select-student">
            <option value="">选择学生</option>
            <option v-for="student in filteredStudents" :key="student.id" :value="student.id">
              {{ student.name }} - {{ student.major }}
            </option>
          </select>
        </div>

        <div v-if="currentStudent" class="portrait-content">
          <div class="info-card level2-card">
            <div class="card-topline"></div>
            <div class="info-header">
              <div class="avatar-ring">
                <div class="avatar">👨‍🎓</div>
              </div>
              <div class="basic-info">
                <h3 class="teacher-name">{{ currentStudent.name }}</h3>
                <p class="teacher-title">{{ currentStudent.major }} | {{ currentStudent.level }}</p>
                <p class="teacher-email">{{ currentStudent.studentId }}</p>
              </div>
            </div>
            <div class="info-cards-row">
              <div class="info-mini-card">
                <span class="info-mini-label">入学时间</span>
                <span class="info-mini-value">{{ currentStudent.enrollYear }}年</span>
              </div>
              <div class="info-mini-card">
                <span class="info-mini-label">生源地</span>
                <span class="info-mini-value">{{ currentStudent.origin }}</span>
              </div>
              <div class="info-mini-card">
                <span class="info-mini-label">导师</span>
                <span class="info-mini-value">{{ currentStudent.supervisor }}</span>
              </div>
              <div class="info-mini-card">
                <span class="info-mini-label">GPA</span>
                <span class="info-mini-value">{{ currentStudent.gpa }}</span>
              </div>
            </div>
          </div>

          <div class="main-charts-row">
            <div class="chart-card level1-card radar-card">
              <h4 class="card-title">能力雷达图</h4>
              <div ref="studentRadarChart" class="chart-container radar-container"></div>
            </div>

            <div class="chart-card level1-card stats-card">
              <h4 class="card-title">学业成果统计</h4>
              <div class="bar-stats-list">
                <div class="bar-stat-item">
                  <div class="bar-stat-header">
                    <span class="bar-stat-label">已修课程</span>
                    <span class="bar-stat-value">{{ currentStudent.coursesCompleted }}门</span>
                  </div>
                  <div class="bar-stat-track">
                    <div class="bar-stat-fill bar-1" :style="{ width: Math.min(100, currentStudent.coursesCompleted * 3) + '%' }"></div>
                  </div>
                </div>
                <div class="bar-stat-item">
                  <div class="bar-stat-header">
                    <span class="bar-stat-label">获得奖学金</span>
                    <span class="bar-stat-value">{{ currentStudent.scholarships }}次</span>
                  </div>
                  <div class="bar-stat-track">
                    <div class="bar-stat-fill bar-2" :style="{ width: Math.min(100, currentStudent.scholarships * 25) + '%' }"></div>
                  </div>
                </div>
                <div class="bar-stat-item">
                  <div class="bar-stat-header">
                    <span class="bar-stat-label">阅读书籍</span>
                    <span class="bar-stat-value">{{ currentStudent.booksRead }}本</span>
                  </div>
                  <div class="bar-stat-track">
                    <div class="bar-stat-fill bar-3" :style="{ width: Math.min(100, currentStudent.booksRead * 1.5) + '%' }"></div>
                  </div>
                </div>
                <div class="bar-stat-item">
                  <div class="bar-stat-header">
                    <span class="bar-stat-label">活动参与</span>
                    <span class="bar-stat-value">{{ currentStudent.activities }}次</span>
                  </div>
                  <div class="bar-stat-track">
                    <div class="bar-stat-fill bar-4" :style="{ width: Math.min(100, currentStudent.activities * 6) + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="bottom-charts-row">
            <div class="chart-card level1-card">
              <h4 class="card-title">成绩分布</h4>
              <div ref="studentGradeChart" class="chart-container"></div>
            </div>
            <div class="chart-card level1-card">
              <h4 class="card-title">奖学金统计</h4>
              <div ref="studentScholarshipChart" class="chart-container"></div>
            </div>
          </div>

          <div class="bottom-charts-row">
            <div class="chart-card level1-card">
              <h4 class="card-title">活动参与趋势</h4>
              <div ref="studentActivityChart" class="chart-container"></div>
            </div>
            <div class="chart-card level1-card">
              <h4 class="card-title">实习经历</h4>
              <div ref="studentInternChart" class="chart-container"></div>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <span class="empty-icon">👥</span>
          <p>请选择一位学生查看画像</p>
        </div>
      </div>

      <div v-if="studentView === 'grade'" class="grade-view">
        <div class="filter-bar">
          <select v-model="selectedGrade" @change="loadGradeData">
            <option value="">选择年级</option>
            <option value="2022">2022级</option>
            <option value="2023">2023级</option>
            <option value="2024">2024级</option>
          </select>
        </div>

        <div v-if="currentGradeData" class="group-portrait">
          <div class="summary-card">
            <div class="summary-header">
              <h3>{{ selectedGrade }}级学生群体画像</h3>
            </div>
            <div class="summary-stats">
              <div class="summary-item">
                <span class="summary-value">{{ currentGradeData.total }}</span>
                <span class="summary-label">学生总数</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ currentGradeData.male }}人</span>
                <span class="summary-label">男生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ currentGradeData.female }}人</span>
                <span class="summary-label">女生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ currentGradeData.avgGpa }}</span>
                <span class="summary-label">平均GPA</span>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <h4>专业分布</h4>
            <div ref="gradeMajorChart" class="chart-container"></div>
          </div>

          <div class="chart-card">
            <h4>能力雷达图</h4>
            <div ref="gradeRadarChart" class="chart-container"></div>
          </div>

          <div class="stats-card">
            <h4>学业统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon">🎖️</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentGradeData.scholarships }}</div>
                  <div class="stat-label">获得奖学金人次</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📚</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentGradeData.avgCourses }}</div>
                  <div class="stat-label">平均已修课程</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🏆</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentGradeData.activities }}</div>
                  <div class="stat-label">活动参与人次</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📝</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentGradeData.papers }}</div>
                  <div class="stat-label">发表论文数</div>
                </div>
              </div>
            </div>
          </div>

          <div class="tags-card">
            <h4>热门标签</h4>
            <div class="tags-grid">
              <span v-for="tag in currentGradeData.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <span class="empty-icon">📅</span>
          <p>请选择一个年级查看群体画像</p>
        </div>
      </div>

      <div v-if="studentView === 'major'" class="major-view">
        <div class="filter-bar">
          <select v-model="selectedMajor" @change="loadMajorData">
            <option value="">选择专业</option>
            <option v-for="m in studentMajorOptions" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>

        <div v-if="currentMajorData" class="group-portrait">
          <div class="summary-card">
            <div class="summary-header">
              <h3>{{ selectedMajor }}专业学生群体画像</h3>
            </div>
            <div class="summary-stats">
              <div class="summary-item">
                <span class="summary-value">{{ currentMajorData.total }}</span>
                <span class="summary-label">学生总数</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ currentMajorData.male }}人</span>
                <span class="summary-label">男生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ currentMajorData.female }}人</span>
                <span class="summary-label">女生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ currentMajorData.avgGpa }}</span>
                <span class="summary-label">平均GPA</span>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <h4>年级分布</h4>
            <div ref="majorGradeChart" class="chart-container"></div>
          </div>

          <div class="chart-card">
            <h4>能力雷达图</h4>
            <div ref="majorRadarChart" class="chart-container"></div>
          </div>

          <div class="stats-card">
            <h4>学业统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon">🎖️</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentMajorData.scholarships }}</div>
                  <div class="stat-label">获得奖学金人次</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📚</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentMajorData.avgCourses }}</div>
                  <div class="stat-label">平均已修课程</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🏆</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentMajorData.activities }}</div>
                  <div class="stat-label">活动参与人次</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📝</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentMajorData.papers }}</div>
                  <div class="stat-label">发表论文数</div>
                </div>
              </div>
            </div>
          </div>

          <div class="tags-card">
            <h4>热门标签</h4>
            <div class="tags-grid">
              <span v-for="tag in currentMajorData.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <span class="empty-icon">📚</span>
          <p>请选择一个专业查看群体画像</p>
        </div>
      </div>

      <div v-if="studentView === 'class'" class="class-view">
        <div class="filter-bar">
          <select v-model="selectedClass" @change="loadClassData">
            <option value="">选择班级</option>
            <option value="行政管理2022级1班">行政管理2022级1班</option>
            <option value="行政管理2022级2班">行政管理2022级2班</option>
            <option value="政治学2023级1班">政治学2023级1班</option>
            <option value="国际政治2023级1班">国际政治2023级1班</option>
            <option value="公共管理2024级1班">公共管理2024级1班</option>
          </select>
        </div>

        <div v-if="currentClassData" class="group-portrait">
          <div class="summary-card">
            <div class="summary-header">
              <h3>{{ selectedClass }}群体画像</h3>
            </div>
            <div class="summary-stats">
              <div class="summary-item">
                <span class="summary-value">{{ currentClassData.total }}</span>
                <span class="summary-label">学生总数</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ currentClassData.male }}人</span>
                <span class="summary-label">男生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ currentClassData.female }}人</span>
                <span class="summary-label">女生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ currentClassData.avgGpa }}</span>
                <span class="summary-label">平均GPA</span>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <h4>生源地分布</h4>
            <div ref="classOriginChart" class="chart-container"></div>
          </div>

          <div class="chart-card">
            <h4>能力雷达图</h4>
            <div ref="classRadarChart" class="chart-container"></div>
          </div>

          <div class="stats-card">
            <h4>学业统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon">🎖️</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentClassData.scholarships }}</div>
                  <div class="stat-label">获得奖学金人次</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📚</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentClassData.avgCourses }}</div>
                  <div class="stat-label">平均已修课程</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🏆</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentClassData.activities }}</div>
                  <div class="stat-label">活动参与人次</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📝</div>
                <div class="stat-info">
                  <div class="stat-value">{{ currentClassData.papers }}</div>
                  <div class="stat-label">发表论文数</div>
                </div>
              </div>
            </div>
          </div>

          <div class="tags-card">
            <h4>班级特色标签</h4>
            <div class="tags-grid">
              <span v-for="tag in currentClassData.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          <span class="empty-icon">👨‍👩‍👧‍👦</span>
          <p>请选择一个班级查看群体画像</p>
        </div>
      </div>

      <div v-if="studentView === 'undergraduate'" class="undergraduate-view">
        <div v-if="undergraduateData" class="group-portrait">
          <div class="summary-card">
            <div class="summary-header">
              <h3>📊 本科生群体画像</h3>
            </div>
            <div class="summary-stats">
              <div class="summary-item">
                <span class="summary-value">{{ undergraduateData.total }}</span>
                <span class="summary-label">本科生总数</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ undergraduateData.male }}人</span>
                <span class="summary-label">男生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ undergraduateData.female }}人</span>
                <span class="summary-label">女生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ undergraduateData.avgGpa }}</span>
                <span class="summary-label">平均GPA</span>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <h4>专业分布</h4>
            <div ref="undergraduateMajorChart" class="chart-container"></div>
          </div>

          <div class="chart-card">
            <h4>年级分布</h4>
            <div ref="undergraduateGradeChart" class="chart-container"></div>
          </div>

          <div class="stats-card">
            <h4>学业统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon">🎖️</div>
                <div class="stat-info">
                  <div class="stat-value">{{ undergraduateData.scholarships }}</div>
                  <div class="stat-label">获得奖学金人次</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📚</div>
                <div class="stat-info">
                  <div class="stat-value">{{ undergraduateData.avgCourses }}</div>
                  <div class="stat-label">平均已修课程</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🏆</div>
                <div class="stat-info">
                  <div class="stat-value">{{ undergraduateData.activities }}</div>
                  <div class="stat-label">活动参与人次</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📝</div>
                <div class="stat-info">
                  <div class="stat-value">{{ undergraduateData.papers }}</div>
                  <div class="stat-label">发表论文数</div>
                </div>
              </div>
            </div>
          </div>

          <div class="tags-card">
            <h4>本科生特色标签</h4>
            <div class="tags-grid">
              <span v-for="tag in undergraduateData.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="studentView === 'graduate'" class="graduate-view">
        <div v-if="graduateData" class="group-portrait">
          <div class="summary-card">
            <div class="summary-header">
              <h3>🎓 研究生群体画像</h3>
            </div>
            <div class="summary-stats">
              <div class="summary-item">
                <span class="summary-value">{{ graduateData.total }}</span>
                <span class="summary-label">研究生总数</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ graduateData.male }}人</span>
                <span class="summary-label">男生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ graduateData.female }}人</span>
                <span class="summary-label">女生</span>
              </div>
              <div class="summary-item">
                <span class="summary-value">{{ graduateData.avgGpa }}</span>
                <span class="summary-label">平均GPA</span>
              </div>
            </div>
          </div>

          <div class="chart-card">
            <h4>学历层次分布</h4>
            <div ref="graduateLevelChart" class="chart-container"></div>
          </div>

          <div class="chart-card">
            <h4>能力雷达图</h4>
            <div ref="graduateRadarChart" class="chart-container"></div>
          </div>

          <div class="stats-card">
            <h4>科研与学业统计</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-icon">🎖️</div>
                <div class="stat-info">
                  <div class="stat-value">{{ graduateData.scholarships }}</div>
                  <div class="stat-label">获得奖学金人次</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🔬</div>
                <div class="stat-info">
                  <div class="stat-value">{{ graduateData.projects }}</div>
                  <div class="stat-label">参与科研项目</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">📝</div>
                <div class="stat-info">
                  <div class="stat-value">{{ graduateData.papers }}</div>
                  <div class="stat-label">发表论文数</div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-icon">🧑‍🏫</div>
                <div class="stat-info">
                  <div class="stat-value">{{ graduateData.avgSupervisor }}</div>
                  <div class="stat-label">平均导师指导</div>
                </div>
              </div>
            </div>
          </div>

          <div class="tags-card">
            <h4>研究生特色标签</h4>
            <div class="tags-grid">
              <span v-for="tag in graduateData.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import 'echarts-gl'
import 'echarts-wordcloud'
import registerWorldMap from '../utils/world.js'

const tabs = [
  { key: 'teacher', label: '教师画像' },
  { key: 'student', label: '学生画像' }
]

const route = useRoute()
const activeTab = ref('teacher')
const teacherView = ref('overall')
const selectedTeacher = ref('')
const selectedStudent = ref('')
const currentTeacher = ref(null)
const currentStudent = ref(null)
const radarChart = ref(null)
const titleDistributionChart = ref(null)
const projectLevelChart = ref(null)
const enrollmentChart = ref(null)
const studentEvalChart = ref(null)
const studentRadarChart = ref(null)
const studentGradeChart = ref(null)
const studentScholarshipChart = ref(null)
const studentActivityChart = ref(null)
const studentInternChart = ref(null)
const studentView = ref('individual')
const selectedGrade = ref('')
const selectedMajor = ref('')
const selectedClass = ref('')
const currentGradeData = ref(null)
const currentMajorData = ref(null)
const currentClassData = ref(null)
const gradeMajorChart = ref(null)
const gradeRadarChart = ref(null)
const majorGradeChart = ref(null)
const majorRadarChart = ref(null)
const classOriginChart = ref(null)
const classRadarChart = ref(null)
const undergraduateMajorChart = ref(null)
const undergraduateGradeChart = ref(null)
const graduateLevelChart = ref(null)
const graduateRadarChart = ref(null)
const overallPaperChart = ref(null)
const overallProjectChart = ref(null)
const overallFeeChart = ref(null)
const overallTeacherChart = ref(null)
const overallWordCloud = ref(null)
const overallGlobeChart = ref(null)
const globeStat = ref('')
const overallRadarChart = ref(null)
const undergraduateData = ref(null)
const graduateData = ref(null)

const teacherSearch = ref({
  name: '',
  title: '',
  research: ''
})

const studentSearch = ref({
  name: '',
  major: '',
  grade: '',
  level: ''
})

const studentMajorOptions = ['行政管理', '政治学理论', '国际政治', '公共管理', '政治学与行政学']

const teachers = ref([])
const portraitMeta = ref(null)
const portraitRank = ref([])
const portraitLoading = ref(true)
const portraitError = ref('')
const scoreMax = ref({ course: 20, paper: 100, research: 84, partjob: 5, award: 25, eduachievement: 29 })
const teacherResearchOptions = ref([])

// 教师画像数据：官网名录（93 人）+ 学院真实绩效评分 CSV（103 人，姓名去空格后匹配 88 人）
const loadPortraitData = async () => {
  portraitLoading.value = true
  portraitError.value = ''
  try {
    const res = await fetch('/api-research/api/real/pspa-faculty-portrait')
    if (!res.ok) throw new Error('HTTP ' + res.status)
    const json = await res.json()
    const overall = json.overall || {}
    portraitMeta.value = overall
    portraitRank.value = json.rank || []
    scoreMax.value = overall.score_max || scoreMax.value
    scoreData.value = (json.rank || []).slice(0, 20).map(r => ({ name: r.name, score: r.score }))

    teachers.value = (json.faculty || []).map((f, i) => {
      const sc = f.score || null
      const pg = f.paper_grade || {}
      const paperTotal = (pg.a_plus || 0) + (pg.a || 0) + (pg.b || 0) + (pg.c || 0) + (pg.d || 0)
      return {
        id: i + 1,
        name: f.name,
        title: f.title,
        department: f.dept,
        homepage: f.url || '',
        email: f.url ? '学院官网个人主页' : '学院官网未收录个人主页',
        joinYear: sc ? (sc.year + ' 年度') : '未纳入绩效评分',
        research: f.research || '官网未采集到研究方向',
        education: sc ? '已纳入绩效评分' : '未纳入绩效评分',
        students: paperTotal,
        courses: sc ? sc.course : 0,
        projects: f.project ? f.project.project_count : 0,
        papers: sc ? sc.paper : 0,
        awards: f.award ? f.award.count : 0,
        awardScore: sc ? sc.award : 0,
        matched: !!f.matched,
        hasProfile: !!f.has_profile,
        score: sc,
        paperGrade: pg,
        projectInfo: f.project || null,
        awardInfo: f.award || null,
        radarData: sc ? [sc.course, sc.paper, sc.research, sc.partjob, sc.award, sc.eduachievement] : [0, 0, 0, 0, 0, 0]
      }
    })

    // 研究方向筛选项：从官网真实研究方向里取高频词
    const counter = {}
    teachers.value.forEach(t => {
      if (!t.research || t.research.startsWith('官网未')) return
      t.research.split(/[、，,；;\/]+/).forEach(w => {
        w = w.trim().slice(0, 12)
        if (w.length >= 2) counter[w] = (counter[w] || 0) + 1
      })
    })
    teacherResearchOptions.value = Object.entries(counter)
      .sort((a, b) => b[1] - a[1]).slice(0, 12).map(x => x[0])
  } catch (e) {
    portraitError.value = '教师画像数据加载失败：' + e.message
  } finally {
    portraitLoading.value = false
  }
}

const students = [
  {
    id: 1001,
    name: '示例学生A',
    major: '行政管理',
    level: '博士研究生',
    studentId: '示例学号',
    enrollYear: 2023,
    origin: '山东济南',
    supervisor: '待接入研究生系统',
    gpa: '3.85',
    coursesCompleted: 28,
    scholarships: 3,
    booksRead: 65,
    activities: 12,
    tags: ['优秀学生', '学术之星', '学生会主席', '发表论文'],
    radarData: [90, 85, 88, 92, 80, 85]
  },
  {
    id: 1002,
    name: '示例学生B',
    major: '政治学理论',
    level: '硕士研究生',
    studentId: '示例学号',
    enrollYear: 2024,
    origin: '河南郑州',
    supervisor: '待接入研究生系统',
    gpa: '3.92',
    coursesCompleted: 20,
    scholarships: 2,
    booksRead: 45,
    activities: 8,
    tags: ['一等奖学金', '三好学生', '科研积极分子'],
    radarData: [88, 92, 85, 80, 90, 88]
  },
  {
    id: 1003,
    name: '示例学生C',
    major: '国际政治',
    level: '本科生',
    studentId: '示例学号',
    enrollYear: 2022,
    origin: '江苏南京',
    supervisor: '待接入研究生系统',
    gpa: '3.78',
    coursesCompleted: 35,
    scholarships: 1,
    booksRead: 55,
    activities: 15,
    tags: ['班长', '社团活动', '体育特长', '英语六级'],
    radarData: [82, 78, 90, 88, 85, 92]
  },
  {
    id: 1004,
    name: '示例学生D',
    major: '公共管理',
    level: 'MPA',
    studentId: '示例学号',
    enrollYear: 2023,
    origin: '广东深圳',
    supervisor: '待接入研究生系统',
    gpa: '3.88',
    coursesCompleted: 18,
    scholarships: 1,
    booksRead: 35,
    activities: 6,
    tags: ['在职研究生', '公务员', '工作经验丰富'],
    radarData: [85, 88, 92, 78, 82, 80]
  },
  {
    id: 1005,
    name: '示例学生E',
    major: '行政管理',
    level: '硕士研究生',
    studentId: '示例学号',
    enrollYear: 2023,
    origin: '山东青岛',
    supervisor: '待接入研究生系统',
    gpa: '3.75',
    coursesCompleted: 22,
    scholarships: 2,
    booksRead: 50,
    activities: 10,
    tags: ['二等奖学金', '优秀学生干部', '科研骨干'],
    radarData: [80, 85, 82, 88, 86, 84]
  },
  {
    id: 1006,
    name: '示例学生F',
    major: '政治学与行政学',
    level: '本科生',
    studentId: '示例学号',
    enrollYear: 2022,
    origin: '山东烟台',
    supervisor: '待接入研究生系统',
    gpa: '3.82',
    coursesCompleted: 32,
    scholarships: 2,
    booksRead: 48,
    activities: 18,
    tags: ['一等奖学金', '社团负责人', '文艺特长', '英语六级'],
    radarData: [85, 78, 88, 90, 82, 87]
  },
  {
    id: 1007,
    name: '示例学生G',
    major: '国际政治',
    level: '博士研究生',
    studentId: '示例学号',
    enrollYear: 2022,
    origin: '北京',
    supervisor: '待接入研究生系统',
    gpa: '3.95',
    coursesCompleted: 30,
    scholarships: 4,
    booksRead: 70,
    activities: 9,
    tags: ['国家奖学金', '学术精英', '发表SCI论文', '留学经历'],
    radarData: [92, 95, 90, 85, 88, 90]
  },
  {
    id: 1008,
    name: '示例学生H',
    major: '公共管理',
    level: '硕士研究生',
    studentId: '示例学号',
    enrollYear: 2024,
    origin: '山东潍坊',
    supervisor: '待接入研究生系统',
    gpa: '3.70',
    coursesCompleted: 16,
    scholarships: 1,
    booksRead: 40,
    activities: 7,
    tags: ['三等奖学金', '志愿服务', '社会实践先进个人'],
    radarData: [78, 80, 85, 82, 86, 79]
  },
  {
    id: 1009,
    name: '示例学生I',
    major: '行政管理',
    level: 'MPA',
    studentId: '示例学号',
    enrollYear: 2023,
    origin: '山东淄博',
    supervisor: '待接入研究生系统',
    gpa: '3.65',
    coursesCompleted: 15,
    scholarships: 0,
    booksRead: 25,
    activities: 4,
    tags: ['在职研究生', '企业高管', '管理经验丰富'],
    radarData: [75, 72, 88, 85, 80, 78]
  },
  {
    id: 1010,
    name: '示例学生J',
    major: '政治学理论',
    level: '本科生',
    studentId: '示例学号',
    enrollYear: 2024,
    origin: '山东临沂',
    supervisor: '待接入研究生系统',
    gpa: '3.68',
    coursesCompleted: 12,
    scholarships: 0,
    booksRead: 30,
    activities: 11,
    tags: ['新生', '学生会干事', '绘画特长'],
    radarData: [76, 74, 82, 86, 80, 83]
  },
  {
    id: 1011,
    name: '示例学生K',
    major: '国际政治',
    level: '硕士研究生',
    studentId: '示例学号',
    enrollYear: 2023,
    origin: '山东济宁',
    supervisor: '待接入研究生系统',
    gpa: '3.80',
    coursesCompleted: 21,
    scholarships: 2,
    booksRead: 52,
    activities: 8,
    tags: ['一等奖学金', '科研积极分子', '英语专业八级'],
    radarData: [84, 86, 87, 83, 89, 85]
  },
  {
    id: 1012,
    name: '示例学生L',
    major: '公共管理',
    level: '博士研究生',
    studentId: '示例学号',
    enrollYear: 2022,
    origin: '山东泰安',
    supervisor: '待接入研究生系统',
    gpa: '3.90',
    coursesCompleted: 29,
    scholarships: 3,
    booksRead: 68,
    activities: 13,
    tags: ['国家奖学金', '学术之星', '博士生助理', '发表核心论文'],
    radarData: [89, 91, 89, 87, 84, 88]
  }
]

const filteredTeachers = computed(() => {
  return teachers.value.filter(t => {
    const nameMatch = !teacherSearch.value.name || t.name.includes(teacherSearch.value.name)
    const titleMatch = !teacherSearch.value.title || t.title === teacherSearch.value.title
    const researchMatch = !teacherSearch.value.research || t.research.includes(teacherSearch.value.research)
    return nameMatch && titleMatch && researchMatch
  })
})

const filteredStudents = computed(() => {
  return students.filter(s => {
    const nameMatch = !studentSearch.value.name || s.name.includes(studentSearch.value.name)
    const majorMatch = !studentSearch.value.major || s.major === studentSearch.value.major
    const gradeMatch = !studentSearch.value.grade || s.enrollYear.toString() === studentSearch.value.grade
    const levelMatch = !studentSearch.value.level || s.level === studentSearch.value.level
    return nameMatch && majorMatch && gradeMatch && levelMatch
  })
})

const filterTeachers = () => {
  selectedTeacher.value = ''
  currentTeacher.value = null
}

const filterStudents = () => {
  selectedStudent.value = ''
  currentStudent.value = null
}

const initTeacherRadar = (data, maxes = {}) => {
  if (!radarChart.value) return
  
  const el = radarChart.value
  // 复用已有实例，切换教师时不再重复 init（否则会叠加多个 canvas 并造成尺寸错乱）
  const chart = echarts.getInstanceByDom(el) || echarts.init(el)
  el._chart = chart
  const m = {
    course: maxes.course || 20,
    paper: maxes.paper || 100,
    research: maxes.research || 84,
    partjob: maxes.partjob || 5,
    award: maxes.award || 25,
    eduachievement: maxes.eduachievement || 29
  }
  
  const option = {
    backgroundColor: 'transparent',
    radar: {
      center: ['50%', '48%'],
      radius: '58%',
      axisNameGap: 8,
      indicator: [
        { name: '教学绩效', max: m.course },
        { name: '论文绩效', max: m.paper },
        { name: '科研绩效', max: m.research },
        { name: '兼职绩效', max: m.partjob },
        { name: '获奖绩效', max: m.award },
        { name: '教育成果', max: m.eduachievement }
      ],
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: 'rgba(255,255,255,0.88)',
        fontSize: 11,
        padding: [2, 4]
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 212, 255, 0.2)'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(0, 212, 255, 0.05)', 'rgba(0, 212, 255, 0.1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 212, 255, 0.3)'
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: data,
        name: '能力指标',
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          color: '#00d4ff',
          width: 2
        },
        areaStyle: {
          color: 'rgba(0, 212, 255, 0.3)',
          opacity: 0.3
        },
        itemStyle: {
          color: '#00d4ff',
          borderColor: '#fff',
          borderWidth: 2
        }
      }]
    }]
  }
  
  chart.setOption(option, true)

  // 只绑定一次 resize，避免切换教师时不断累积监听
  if (!el._resizeBound) {
    el._resizeBound = true
    window.addEventListener('resize', () => chart.resize())
  }
}

const initTitleDistributionChart = (teacher) => {
  if (!titleDistributionChart.value) return
  
  const chart = echarts.init(titleDistributionChart.value)
  const titles = (portraitMeta.value || {}).titles || []
  const palette = ['#7b2cbf', '#00d4ff', '#52c41a', '#faad14', '#ff7a45', '#36cfc9']
  const currentTitle = teacher?.title || ''
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10, 25, 50, 0.95)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: p => `${p.name}：${p.value} 人（${p.percent}%）`
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 12 },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 12
    },
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['32%', '50%'],
      label: {
        show: true,
        position: 'inside',
        formatter: '{d}%',
        color: '#fff',
        fontSize: 13,
        fontWeight: 'bold'
      },
      labelLine: { show: false },
      data: titles.map((t, i) => ({
        value: t.value,
        name: t.name,
        itemStyle: {
          color: t.name === currentTitle ? '#ff4d4f' : palette[i % palette.length],
          borderColor: t.name === currentTitle ? '#fff' : 'transparent',
          borderWidth: t.name === currentTitle ? 3 : 0
        }
      })),
      emphasis: {
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0, 212, 255, 0.5)' }
      }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initProjectLevelChart = (teacher) => {
  if (!projectLevelChart.value) return
  
  const chart = echarts.init(projectLevelChart.value)
  const pg = teacher.paperGrade || {}
  const labels = ['A+', 'A', 'B', 'C', 'D']
  const values = [pg.a_plus || 0, pg.a || 0, pg.b || 0, pg.c || 0, pg.d || 0]
  const colors = ['#7b2cbf', '#00d4ff', '#36cfc9', '#faad14', '#ff7a45']
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(10, 25, 50, 0.95)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 12 }
    },
    grid: { left: 60, right: 50, top: 20, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: labels.slice().reverse(),
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 16,
      data: values.slice().reverse().map((v, i) => ({
        value: v,
        itemStyle: { color: colors[labels.length - 1 - i], borderRadius: [0, 6, 6, 0] }
      })),
      label: {
        show: true,
        position: 'right',
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold'
      }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initEnrollmentChart = (teacher) => {
  if (!enrollmentChart.value) return
  
  const chart = echarts.init(enrollmentChart.value)
  const sc = teacher.score || {}
  const labels = ['教学', '论文', '科研', '兼职', '获奖', '教育成果']
  const values = [sc.course || 0, sc.paper || 0, sc.research || 0, sc.partjob || 0, sc.award || 0, sc.eduachievement || 0]
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 25, 50, 0.95)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: p => `${p[0].name}绩效：<b>${p[0].value}</b> 分`
    },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: 'category',
      data: labels,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    series: [{
      type: 'bar',
      barWidth: '45%',
      data: values,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0,212,255,0.9)' },
          { offset: 1, color: 'rgba(0,212,255,0.15)' }
        ]),
        borderRadius: [4, 4, 0, 0]
      },
      label: { show: true, position: 'top', color: '#fff', fontSize: 11 }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initStudentEvalChart = (teacher) => {
  if (!studentEvalChart.value) return
  
  const chart = echarts.init(studentEvalChart.value)
  const sc = teacher.score || {}
  const avg = (portraitMeta.value || {}).score_avg || {}
  const categories = ['教育成果', '获奖', '兼职', '科研', '论文', '教学']
  const mine = [sc.eduachievement || 0, sc.award || 0, sc.partjob || 0, sc.research || 0, sc.paper || 0, sc.course || 0]
  const means = [avg.eduachievement || 0, avg.award || 0, avg.partjob || 0, avg.research || 0, avg.paper || 0, avg.course || 0]
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(10, 25, 50, 0.95)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 12 }
    },
    legend: {
      top: 0,
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 11 },
      itemWidth: 12,
      itemHeight: 10
    },
    grid: { left: 90, right: 40, top: 35, bottom: 25 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [
      {
        name: '本人',
        type: 'bar',
        barWidth: 10,
        data: mine,
        itemStyle: { color: '#00d4ff', borderRadius: [0, 6, 6, 0] }
      },
      {
        name: '全院均值',
        type: 'bar',
        barWidth: 10,
        data: means,
        itemStyle: { color: 'rgba(123,44,191,0.75)', borderRadius: [0, 6, 6, 0] }
      }
    ]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initStudentRadar = (data) => {
  if (!studentRadarChart.value) return
  
  const chart = echarts.init(studentRadarChart.value)
  
  const option = {
    backgroundColor: 'transparent',
    radar: {
      indicator: [
        { name: '专业成绩', max: 100 },
        { name: '科研能力', max: 100 },
        { name: '创新实践', max: 100 },
        { name: '综合素质', max: 100 },
        { name: '外语能力', max: 100 },
        { name: '团队协作', max: 100 }
      ],
      center: ['50%', '48%'],
      radius: '58%',
      axisNameGap: 8,
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: 'rgba(255,255,255,0.88)',
        fontSize: 11,
        padding: [2, 4]
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(123, 44, 191, 0.2)'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(123, 44, 191, 0.05)', 'rgba(123, 44, 191, 0.1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(123, 44, 191, 0.3)'
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: data,
        name: '能力指标',
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          color: '#7b2cbf',
          width: 2
        },
        areaStyle: {
          color: 'rgba(123, 44, 191, 0.3)',
          opacity: 0.3
        },
        itemStyle: {
          color: '#7b2cbf',
          borderColor: '#fff',
          borderWidth: 2
        }
      }]
    }]
  }
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => chart.resize())
}

const initStudentGradeChart = (student) => {
  if (!studentGradeChart.value) return
  
  const chart = echarts.init(studentGradeChart.value)
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(10, 25, 50, 0.95)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 12 }
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 12 },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 12
    },
    series: [{
      type: 'pie',
      radius: ['40%', '68%'],
      center: ['35%', '50%'],
      label: {
        show: true,
        position: 'inside',
        formatter: '{d}%',
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold'
      },
      labelLine: { show: false },
      data: [
        { value: 35, name: '优秀', itemStyle: { color: '#7b2cbf' } },
        { value: 45, name: '良好', itemStyle: { color: '#00d4ff' } },
        { value: 15, name: '中等', itemStyle: { color: '#faad14' } },
        { value: 5, name: '及格', itemStyle: { color: '#52c41a' } }
      ],
      emphasis: {
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0, 212, 255, 0.5)' }
      }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initStudentScholarshipChart = (student) => {
  if (!studentScholarshipChart.value) return
  
  const chart = echarts.init(studentScholarshipChart.value)
  
  const types = ['国家奖学金', '一等奖学金', '二等奖学金', '三等奖学金']
  const values = [student.scholarships >= 3 ? 1 : 0, student.scholarships >= 2 ? 1 : 0, student.scholarships >= 1 ? 1 : 0, student.scholarships > 0 ? Math.floor(Math.random() * 2) : 0]
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(10, 25, 50, 0.95)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 12 }
    },
    grid: { left: 70, right: 40, top: 20, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: types,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 14,
      data: values.map((val, i) => ({
        value: val,
        itemStyle: {
          color: ['#7b2cbf', '#00d4ff', '#faad14', '#52c41a'][i],
          borderRadius: [0, 6, 6, 0]
        }
      })),
      label: {
        show: true,
        position: 'right',
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold'
      }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initStudentActivityChart = (student) => {
  if (!studentActivityChart.value) return
  
  const chart = echarts.init(studentActivityChart.value)
  
  const months = ['9月', '10月', '11月', '12月', '1月', '2月']
  const base = Math.floor(student.activities / 6)
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 25, 50, 0.95)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 12 }
    },
    grid: { left: 50, right: 20, top: 25, bottom: 30 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: months,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    series: [{
      type: 'line',
      smooth: true,
      data: [base, base + 1, base - 1, base + 2, base, base + 1],
      lineStyle: { color: '#7b2cbf', width: 3 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(123,44,191,0.3)' },
          { offset: 1, color: 'rgba(123,44,191,0.02)' }
        ])
      },
      symbolSize: 8,
      itemStyle: { color: '#7b2cbf' }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initStudentInternChart = (student) => {
  if (!studentInternChart.value) return
  
  const chart = echarts.init(studentInternChart.value)
  
  const internTypes = ['政府实习', '企业实习', '科研机构', 'NGO组织']
  const values = [1, 1, Math.floor(Math.random() * 2), Math.floor(Math.random() * 2)]
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 25, 50, 0.95)',
      borderColor: 'rgba(0, 212, 255, 0.4)',
      borderWidth: 1,
      textStyle: { color: '#fff', fontSize: 12 }
    },
    grid: { left: 80, right: 20, top: 25, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: internTypes,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 14,
      data: values.map((val, i) => ({
        value: val,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: ['rgba(0,212,255,0.3)', 'rgba(123,44,191,0.3)', 'rgba(250,173,20,0.3)', 'rgba(82,196,26,0.3)'][i] },
            { offset: 1, color: ['#00d4ff', '#7b2cbf', '#faad14', '#52c41a'][i] }
          ]),
          borderRadius: [0, 6, 6, 0]
        }
      })),
      label: {
        show: true,
        position: 'right',
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold'
      }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

// ====== 整体教师画像数据（全部来自画像接口，未加载前显示占位） ======
const overallKpi = computed(() => {
  const m = portraitMeta.value || {}
  return [
    { icon: '👥', value: m.teacher_count ?? '—', unit: '人', label: '官网在职教师总数', trend: `官网个人主页已采集 ${m.profile_count ?? '—'} 人`, trendColor: '#00d4ff', bg: 'linear-gradient(135deg, rgba(0,212,255,0.2), rgba(0,212,255,0.05))' },
    { icon: '📊', value: m.profile_count ?? '—', unit: '人', label: '教师详情页可检索', trend: `覆盖 ${m.teacher_count ? Math.round((m.profile_count || 0) / m.teacher_count * 100) : 0}% 官网名录`, trendColor: '#52c41a', bg: 'linear-gradient(135deg, rgba(82,196,26,0.2), rgba(82,196,26,0.05))' },
    { icon: '🏅', value: m.score_matched ?? '—', unit: '人', label: '匹配到绩效评分', trend: `评分表共 ${m.score_total ?? '—'} 人，按姓名匹配`, trendColor: '#faad14', bg: 'linear-gradient(135deg, rgba(250,173,20,0.2), rgba(250,173,20,0.05))' },
    { icon: '📄', value: m.achievement_count ?? '—', unit: '条', label: '官网学术成果', trend: `官网通知 ${m.notice_count ?? '—'} 条`, trendColor: '#00d4ff', bg: 'linear-gradient(135deg, rgba(123,44,191,0.2), rgba(123,44,191,0.05))' }
  ]
})

const teacherStrength = computed(() => {
  const titles = (portraitMeta.value || {}).titles || []
  return titles.map(t => {
    const matched = t.matched || 0
    const rest = Math.max(0, t.value - matched)
    const bars = [
      { label: '已评分', count: matched, percent: t.value ? +(matched / t.value * 100).toFixed(1) : 0, color: '#7b2cbf' },
      { label: '未评分', count: rest, percent: t.value ? +(rest / t.value * 100).toFixed(1) : 0, color: 'rgba(0,212,255,0.45)' }
    ].filter(b => b.count > 0)
    return { title: t.name, total: t.value, icon: '👨‍🏫', bars }
  })
})


const scoreData = ref([])

const fullscreenChart = ref(null)
const wordCloudZoom = ref(1)
const radarZoom = ref(1)
const overallStrengthChart = ref(null)

const adjustWordCloudZoom = (delta) => {
  wordCloudZoom.value = Math.max(0.3, Math.min(3, wordCloudZoom.value + delta))
  const chart = overallWordCloud.value?._chart
  if (chart) {
    const opt = chart.getOption()
    const baseSize = opt.series[0].data.map(d => d.value)
    const maxVal = Math.max(...baseSize)
    const range = [12 * wordCloudZoom.value, 42 * wordCloudZoom.value]
    chart.setOption({ series: [{ sizeRange: [Math.max(6, range[0]), Math.min(80, range[1])] }] })
  }
}

const adjustRadarZoom = (delta) => {
  radarZoom.value = Math.max(0.7, Math.min(1.4, +(radarZoom.value + delta).toFixed(2)))
  const chart = overallRadarChart.value?._chart
  if (chart) {
    // 缩放只调雷达半径，避免改变容器高度导致图例/轴标签再次错位
    chart.setOption({ radar: { radius: Math.round(55 * radarZoom.value) + '%' } })
  }
}

const toggleFullscreen = (type) => {
  fullscreenChart.value = fullscreenChart.value === type ? null : type
  nextTick(() => {
    const chartRef = type === 'wordcloud' ? overallWordCloud : overallRadarChart
    if (chartRef.value && chartRef.value._chart) {
      chartRef.value._chart.resize()
    }
  })
}

// 教师整体画像图表初始化
const initMiniBarChart = (el, data, color = '#57a8d9') => {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: '1%', right: '1%', top: '5%', bottom: '1%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.year), show: false },
    yAxis: { type: 'value', show: false },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(24,141,240,0.4)', textStyle: { color: '#fff', fontWeight: 'bold' }, formatter: p => `<div style="padding:4px 8px"><span>${p[0].name}</span><br><span>${p[0].value}</span></div>` },
    series: [{ type: 'bar', data: data.map(d => d.count), itemStyle: { color, borderRadius: [3,3,0,0] }, barWidth: '50%', emphasis: { itemStyle: { color: '#f66a64' } } }]
  })
  return chart
}

const initMiniLineChart = (el, data, color = '#57a8d9') => {
  if (!el) return
  const chart = echarts.init(el)
  chart.setOption({
    backgroundColor: 'transparent',
    grid: { left: '1%', right: '1%', top: '10%', bottom: '1%', containLabel: true },
    xAxis: { type: 'category', data: data.map(d => d.year), show: false },
    yAxis: { type: 'value', show: false },
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(24,141,240,0.4)', textStyle: { color: '#fff', fontWeight: 'bold' }, formatter: p => `<div style="padding:4px 8px"><span>${p[0].name}</span><br><span>${p[0].value}</span></div>` },
    series: [{ type: 'line', data: data.map(d => d.count), smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { color, width: 3 }, itemStyle: { color, borderColor: '#fff', borderWidth: 2 } }]
  })
  return chart
}

// 绩效雷达自动轮播定时器
let radarCarouselTimer = null

const initOverallCharts = () => {
  // 绩效雷达自动轮播定时器（重复进入整体画像时先清理，避免叠加）
  // 师资力量 - 手动HTML布局（由 teacherStrength 驱动）
  // 数据来自官网教师名录 + 真实绩效评分匹配结果
  const meta = portraitMeta.value || {}

  // 学术成果年度新增（官网 /xsky/xscg.htm 爬取）
  initMiniBarChart(overallPaperChart.value,
    (meta.achievement_year || []).map(d => ({ year: String(d.year), count: d.count })))
  // 学术成果类别（官网栏目口径）
  initMiniBarChart(overallProjectChart.value,
    (meta.achievement_category || []).map(d => ({ year: d.name, count: d.value })), '#36cfc9')
  // 职称构成（官网 /jytd/qzjs.htm）
  initMiniBarChart(overallFeeChart.value,
    (meta.titles || []).map(d => ({ year: d.name, count: d.value })), '#7b2cbf')
  // 通知公告年度发布（官网 /tzgg1.htm）
  initMiniLineChart(overallTeacherChart.value,
    (meta.notice_year || []).map(d => ({ year: String(d.year), count: d.count })), '#52c41a')

  // 研究方向/论文关键词词云（官网论文题录 375 篇的真实关键词）
  if (overallWordCloud.value) {
    const wc = echarts.init(overallWordCloud.value)
    overallWordCloud.value._chart = wc
    const kw = (meta.paper_keywords || [])
    wc.setOption({
      backgroundColor: 'transparent',
      series: [{
        type: 'wordCloud', shape: 'circle', width: '90%', height: '90%',
        sizeRange: [10, 34], rotationRange: [-30, 30], gridSize: 4,
        textStyle: { fontFamily: 'Microsoft YaHei', color: () => `hsl(${Math.random() * 360}, 100%, 70%)` },
        emphasis: { textStyle: { color: '#fff', fontSize: 36, textShadowBlur: 20, textShadowColor: '#00d4ff' } },
        data: kw.length ? kw : [{ name: '暂无关键词数据', value: 1 }]
      }]
    })
  }

  // 六维绩效雷达（全院均值 vs 自动轮播真实教师）
  if (overallRadarChart.value) {
    const radar = echarts.getInstanceByDom(overallRadarChart.value) || echarts.init(overallRadarChart.value)
    overallRadarChart.value._chart = radar
    if (!overallRadarChart.value._resizeBound) {
      overallRadarChart.value._resizeBound = true
      window.addEventListener('resize', () => radar.resize())
    }
    const avg = meta.score_avg || {}
    const max = meta.score_max || {}
    const avgVal = [avg.course, avg.paper, avg.research, avg.partjob, avg.award, avg.eduachievement].map(v => v || 0)
    radar.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      legend: {
        bottom: 2,
        left: 'center',
        icon: 'circle',
        itemWidth: 8,
        itemHeight: 8,
        itemGap: 24,
        textStyle: { color: 'rgba(255,255,255,0.75)', fontSize: 11 },
        // 长姓名的图例截断，避免小卡片内图例相互挤压
        formatter: name => (name || '').length > 8 ? `${name.slice(0, 8)}…` : name
      },
      radar: {
        center: ['50%', '46%'],
        radius: '55%',
        splitNumber: 4,
        axisNameGap: 8,
        indicator: [
          { name: '教学', max: max.course || 20 }, { name: '论文', max: max.paper || 100 },
          { name: '科研', max: max.research || 84 }, { name: '兼职', max: max.partjob || 5 },
          { name: '获奖', max: max.award || 25 }, { name: '教育成果', max: max.eduachievement || 29 }
        ],
        axisName: {
          color: 'rgba(255,255,255,0.88)',
          fontSize: 11,
          padding: [2, 4]
        },
        axisLine: { lineStyle: { color: 'rgba(0,212,255,0.3)' } },
        splitLine: { lineStyle: { color: 'rgba(0,255,255,0.5)' } },
        splitArea: { areaStyle: { color: ['rgba(0,212,255,0.02)', 'rgba(0,212,255,0.05)'] } }
      },
      series: [{
        type: 'radar', symbolSize: 6,
        data: [{ value: avgVal, name: '全院均值', lineStyle: { color: '#11e5fc' }, areaStyle: { color: 'rgba(0,212,255,0.15)' }, itemStyle: { color: '#e7feb8' } }]
      }]
    })
    // 自动轮播：绩效总分前 6 名的真实教师
    const names = (portraitRank.value || []).slice(0, 6).map(r => r.name)
    let idx = 0
    if (radarCarouselTimer) {
      clearInterval(radarCarouselTimer)
      radarCarouselTimer = null
    }
    if (names.length) {
      radarCarouselTimer = setInterval(() => {
        const name = names[idx]
        const t = teachers.value.find(x => x.name === name)
        const sc = (t && t.score) || {}
        radar.setOption({
          series: [{
            data: [
              { value: avgVal, name: '全院均值', lineStyle: { color: '#11e5fc', opacity: 0.5 }, areaStyle: { color: '#e7feb8' }, itemStyle: { color: '#e7feb8' } },
              {
                value: [sc.course || 0, sc.paper || 0, sc.research || 0, sc.partjob || 0, sc.award || 0, sc.eduachievement || 0],
                name,
                lineStyle: { color: '#0ef9fe', width: 3 },
                areaStyle: { color: '#d890fa' },
                itemStyle: { color: '#8ff9f8' }
              }
            ]
          }]
        })
        idx = (idx + 1) % names.length
      }, 3500)
    }
  }

  // 培养经历：2D 世界地图 + 学缘飞线
  // 原 3D 地球（geo3D distance:15）在小卡片里视角过近，只会显示一块放大的残缺大陆，
  // 因此改为 2D 世界地图 + 飞线动效，保证轮廓完整、院校点与连线清晰可辨。
  if (overallGlobeChart.value) {
    registerWorldMap(echarts)

    const el = overallGlobeChart.value
    const globe = echarts.getInstanceByDom(el) || echarts.init(el)
    el._chart = globe
    if (!el._resizeBound) {
      el._resizeBound = true
      window.addEventListener('resize', () => globe.resize())
    }

    fetch('/data/teachers.json')
      .then(res => res.json())
      .catch(() => ({ teachers: [] }))
      .then(data => {
        const list = data.teachers || []
        const pointMap = new Map()
        const routeData = []

        const isValidInst = inst =>
          inst && Number.isFinite(Number(inst.longitude)) && Number.isFinite(Number(inst.latitude))

        const addPoint = (inst, teacherName) => {
          if (!isValidInst(inst)) return
          const instName = inst.name || `${inst.longitude},${inst.latitude}`
          if (!pointMap.has(instName)) {
            pointMap.set(instName, {
              name: instName,
              value: [Number(inst.longitude), Number(inst.latitude)],
              teachers: []
            })
          }
          pointMap.get(instName).teachers.push(teacherName)
        }

        list.forEach(t => {
          const insts = [t.undergraduate, t.graduate, t.doctorate, t['other institutions']]
            .filter(isValidInst)
          insts.forEach(inst => addPoint(inst, t.name))
          for (let i = 1; i < insts.length; i++) {
            routeData.push({
              coords: [
                [Number(insts[i - 1].longitude), Number(insts[i - 1].latitude)],
                [Number(insts[i].longitude), Number(insts[i].latitude)]
              ]
            })
          }
        })

        const points = Array.from(pointMap.values()).map(p => ({
          name: p.name,
          value: p.value,
          teacherCount: p.teachers.length,
          teachers: p.teachers
        }))

        if (!points.length) {
          globeStat.value = '暂无教育背景数据'
          globe.setOption({
            backgroundColor: 'transparent',
            graphic: {
              type: 'text',
              left: 'center',
              top: 'middle',
              style: { text: '暂无教师教育背景数据', fill: 'rgba(255,255,255,0.45)', fontSize: 13 }
            }
          }, true)
          return
        }

        globeStat.value = `${points.length} 所院校 · ${routeData.length} 条学缘`
        globe.setOption({
          backgroundColor: 'transparent',
          tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(6, 26, 48, 0.92)',
            borderColor: 'rgba(0, 212, 255, 0.45)',
            borderWidth: 1,
            textStyle: { color: '#fff', fontSize: 12 },
            formatter: p => {
              const d = p.data || {}
              if (!d.teacherCount) return ''
              const names = (d.teachers || []).slice(0, 6).join('、')
              const more = (d.teachers || []).length > 6 ? ' 等' : ''
              return `${p.name}<br/>${d.teacherCount} 位教师<br/><span style="color:#9ad8ff">${names}${more}</span>`
            }
          },
          geo: {
            map: 'world',
            roam: true,
            zoom: 1.15,
            center: [40, 26],
            label: { show: false },
            itemStyle: {
              areaColor: 'rgba(10, 58, 102, 0.55)',
              borderColor: 'rgba(0, 212, 255, 0.45)',
              borderWidth: 0.6
            },
            emphasis: {
              label: { show: false },
              itemStyle: { areaColor: 'rgba(0, 212, 255, 0.22)' }
            }
          },
          series: [
            {
              type: 'lines',
              coordinateSystem: 'geo',
              zlevel: 2,
              silent: true,
              effect: {
                show: true,
                period: 5,
                trailLength: 0.45,
                symbol: 'arrow',
                symbolSize: 5
              },
              lineStyle: {
                color: 'rgba(0, 212, 255, 0.55)',
                width: 0.8,
                curveness: 0.25
              },
              data: routeData
            },
            {
              type: 'effectScatter',
              coordinateSystem: 'geo',
              zlevel: 3,
              rippleEffect: { brushType: 'stroke', scale: 3 },
              symbolSize: 5,
              itemStyle: { color: '#ffd666', shadowBlur: 6, shadowColor: '#ffd666' },
              data: points
            }
          ]
        }, true)
      }) // end fetch
  }
}

const loadOverallTeacher = () => {
  nextTick(() => initOverallCharts())
}

const loadTeacherData = () => {
  if (!selectedTeacher.value) {
    currentTeacher.value = null
    return
  }
  
  const teacher = teachers.value.find(t => t.id == selectedTeacher.value)
  currentTeacher.value = teacher
  
  nextTick(() => {
    if (teacher) {
      initTeacherRadar(teacher.radarData, scoreMax.value)
      initTitleDistributionChart(teacher)
      initProjectLevelChart(teacher)
      initEnrollmentChart(teacher)
      initStudentEvalChart(teacher)
    }
  })
}

const loadStudentData = () => {
  if (!selectedStudent.value) {
    currentStudent.value = null
    return
  }
  
  const student = students.find(s => s.id == selectedStudent.value)
  currentStudent.value = student
  
  nextTick(() => {
    if (student) {
      initStudentRadar(student.radarData)
      initStudentGradeChart(student)
      initStudentScholarshipChart(student)
      initStudentActivityChart(student)
      initStudentInternChart(student)
    }
  })
}

const gradeData = {
  '2022': {
    total: 450,
    male: 180,
    female: 270,
    avgGpa: '3.78',
    scholarships: 120,
    avgCourses: 32,
    activities: 580,
    papers: 45,
    tags: ['学术氛围浓厚', '就业率高', '考研率高', '社团活跃', '体育强'],
    majorDistribution: [
      { name: '行政管理', value: 150 },
      { name: '政治学理论', value: 120 },
      { name: '国际政治', value: 100 },
      { name: '公共管理', value: 50 },
      { name: '政治学与行政学', value: 30 }
    ],
    radarData: [85, 78, 82, 88, 80, 85]
  },
  '2023': {
    total: 420,
    male: 168,
    female: 252,
    avgGpa: '3.82',
    scholarships: 130,
    avgCourses: 25,
    activities: 520,
    papers: 38,
    tags: ['综合素质高', '科研潜力大', '英语水平好', '实践能力强', '创新意识'],
    majorDistribution: [
      { name: '行政管理', value: 140 },
      { name: '政治学理论', value: 110 },
      { name: '国际政治', value: 95 },
      { name: '公共管理', value: 55 },
      { name: '政治学与行政学', value: 20 }
    ],
    radarData: [88, 82, 85, 86, 84, 82]
  },
  '2024': {
    total: 400,
    male: 160,
    female: 240,
    avgGpa: '3.85',
    scholarships: 85,
    avgCourses: 12,
    activities: 380,
    papers: 12,
    tags: ['新生力量', '数字化能力强', '视野开阔', '学习积极性高', '团队协作'],
    majorDistribution: [
      { name: '行政管理', value: 130 },
      { name: '政治学理论', value: 100 },
      { name: '国际政治', value: 90 },
      { name: '公共管理', value: 50 },
      { name: '政治学与行政学', value: 30 }
    ],
    radarData: [82, 75, 80, 88, 86, 84]
  }
}

const majorData = {
  '行政管理': {
    total: 420,
    male: 168,
    female: 252,
    avgGpa: '3.80',
    scholarships: 140,
    avgCourses: 28,
    activities: 620,
    papers: 55,
    tags: ['公务员摇篮', '就业面广', '实践导向', '专业基础扎实', '校友网络强'],
    gradeDistribution: [
      { name: '2022级', value: 150 },
      { name: '2023级', value: 140 },
      { name: '2024级', value: 130 }
    ],
    radarData: [88, 78, 85, 86, 82, 84]
  },
  '政治学理论': {
    total: 330,
    male: 132,
    female: 198,
    avgGpa: '3.85',
    scholarships: 110,
    avgCourses: 26,
    activities: 450,
    papers: 78,
    tags: ['学术前沿', '理论深度', '研究方法', '批判性思维', '学术交流活跃'],
    gradeDistribution: [
      { name: '2022级', value: 120 },
      { name: '2023级', value: 110 },
      { name: '2024级', value: 100 }
    ],
    radarData: [85, 92, 88, 82, 80, 86]
  },
  '国际政治': {
    total: 285,
    male: 114,
    female: 171,
    avgGpa: '3.78',
    scholarships: 95,
    avgCourses: 27,
    activities: 380,
    papers: 62,
    tags: ['国际视野', '外语能力', '全球治理', '时事分析', '跨文化交流'],
    gradeDistribution: [
      { name: '2022级', value: 100 },
      { name: '2023级', value: 95 },
      { name: '2024级', value: 90 }
    ],
    radarData: [82, 88, 85, 84, 88, 82]
  },
  '公共管理': {
    total: 155,
    male: 62,
    female: 93,
    avgGpa: '3.82',
    scholarships: 45,
    avgCourses: 22,
    activities: 220,
    papers: 35,
    tags: ['MPA专业', '在职学习', '实践经验', '管理能力', '政策分析'],
    gradeDistribution: [
      { name: '2022级', value: 50 },
      { name: '2023级', value: 55 },
      { name: '2024级', value: 50 }
    ],
    radarData: [80, 85, 90, 88, 82, 86]
  },
  '政治学与行政学': {
    total: 80,
    male: 32,
    female: 48,
    avgGpa: '3.88',
    scholarships: 30,
    avgCourses: 28,
    activities: 180,
    papers: 25,
    tags: ['复合型人才', '政治学基础', '行政能力', '法律素养', '领导力'],
    gradeDistribution: [
      { name: '2022级', value: 30 },
      { name: '2023级', value: 20 },
      { name: '2024级', value: 30 }
    ],
    radarData: [86, 82, 84, 86, 85, 88]
  }
}

const classData = {
  '行政管理2022级1班': {
    total: 35,
    male: 14,
    female: 21,
    avgGpa: '3.82',
    scholarships: 12,
    avgCourses: 35,
    activities: 85,
    papers: 8,
    tags: ['优秀班集体', '学风优良', '凝聚力强', '考研率高', '社会实践'],
    originDistribution: [
      { name: '山东济南', value: 8 },
      { name: '山东青岛', value: 6 },
      { name: '山东烟台', value: 5 },
      { name: '山东潍坊', value: 4 },
      { name: '其他省份', value: 12 }
    ],
    radarData: [88, 80, 85, 90, 82, 88]
  },
  '行政管理2022级2班': {
    total: 33,
    male: 13,
    female: 20,
    avgGpa: '3.75',
    scholarships: 10,
    avgCourses: 34,
    activities: 78,
    papers: 6,
    tags: ['团结友爱', '文体活动丰富', '创新创业', '志愿服务', '班级文化'],
    originDistribution: [
      { name: '山东济南', value: 7 },
      { name: '山东淄博', value: 5 },
      { name: '山东临沂', value: 4 },
      { name: '山东济宁', value: 4 },
      { name: '其他省份', value: 13 }
    ],
    radarData: [85, 78, 82, 88, 84, 85]
  },
  '政治学2023级1班': {
    total: 30,
    male: 12,
    female: 18,
    avgGpa: '3.88',
    scholarships: 11,
    avgCourses: 26,
    activities: 65,
    papers: 12,
    tags: ['学术氛围浓', '科研能力强', '读书会活跃', '学术竞赛', '论文发表'],
    originDistribution: [
      { name: '山东济南', value: 6 },
      { name: '山东泰安', value: 5 },
      { name: '山东日照', value: 4 },
      { name: '河南郑州', value: 3 },
      { name: '其他省份', value: 12 }
    ],
    radarData: [86, 92, 88, 84, 80, 86]
  },
  '国际政治2023级1班': {
    total: 28,
    male: 11,
    female: 17,
    avgGpa: '3.80',
    scholarships: 9,
    avgCourses: 25,
    activities: 72,
    papers: 8,
    tags: ['国际视野', '外语优秀', '模拟联合国', '国际交流', '全球治理'],
    originDistribution: [
      { name: '山东青岛', value: 5 },
      { name: '山东济南', value: 5 },
      { name: '北京', value: 3 },
      { name: '上海', value: 2 },
      { name: '其他省份', value: 13 }
    ],
    radarData: [82, 88, 85, 86, 90, 82]
  },
  '公共管理2024级1班': {
    total: 25,
    male: 10,
    female: 15,
    avgGpa: '3.90',
    scholarships: 7,
    avgCourses: 12,
    activities: 45,
    papers: 3,
    tags: ['新生力量', '朝气蓬勃', '学习积极', '创新意识', '团队协作'],
    originDistribution: [
      { name: '山东济南', value: 6 },
      { name: '山东潍坊', value: 4 },
      { name: '山东威海', value: 3 },
      { name: '广东深圳', value: 2 },
      { name: '其他省份', value: 10 }
    ],
    radarData: [84, 80, 86, 88, 86, 84]
  }
}

const undergraduateDataValue = {
  total: 850,
  male: 340,
  female: 510,
  avgGpa: '3.79',
  scholarships: 245,
  avgCourses: 28,
  activities: 1250,
  papers: 68,
  tags: ['本科生群体', '基础扎实', '全面发展', '创新能力', '社会实践', '就业导向'],
  majorDistribution: [
    { name: '行政管理', value: 280 },
    { name: '政治学与行政学', value: 220 },
    { name: '国际政治', value: 180 },
    { name: '政治学理论', value: 120 },
    { name: '公共管理', value: 50 }
  ],
  gradeDistribution: [
    { name: '2022级', value: 300 },
    { name: '2023级', value: 280 },
    { name: '2024级', value: 270 }
  ],
  radarData: [85, 78, 82, 86, 84, 88]
}

const graduateDataValue = {
  total: 380,
  male: 152,
  female: 228,
  avgGpa: '3.85',
  scholarships: 185,
  projects: 240,
  papers: 156,
  avgSupervisor: '1对6',
  tags: ['研究生群体', '科研能力强', '学术潜力', '创新研究', '导师制', '论文发表'],
  levelDistribution: [
    { name: '硕士研究生', value: 260 },
    { name: '博士研究生', value: 80 },
    { name: 'MPA', value: 40 }
  ],
  radarData: [88, 92, 86, 90, 85, 88]
}

const initGradeCharts = () => {
  initPieChart(gradeMajorChart.value, currentGradeData.value.majorDistribution, '专业分布')
  initGroupRadar(gradeRadarChart.value, currentGradeData.value.radarData)
}

const initMajorCharts = () => {
  initPieChart(majorGradeChart.value, currentMajorData.value.gradeDistribution, '年级分布')
  initGroupRadar(majorRadarChart.value, currentMajorData.value.radarData)
}

const initClassCharts = () => {
  initPieChart(classOriginChart.value, currentClassData.value.originDistribution, '生源地分布')
  initGroupRadar(classRadarChart.value, currentClassData.value.radarData)
}

const initUndergraduateCharts = () => {
  initPieChart(undergraduateMajorChart.value, undergraduateData.value.majorDistribution, '专业分布')
  initPieChart(undergraduateGradeChart.value, undergraduateData.value.gradeDistribution, '年级分布')
}

const initGraduateCharts = () => {
  initPieChart(graduateLevelChart.value, graduateData.value.levelDistribution, '学历层次')
  initGroupRadar(graduateRadarChart.value, graduateData.value.radarData)
}

const initPieChart = (el, data, title) => {
  if (!el) return
  
  const chart = echarts.init(el)
  
  const option = {
    backgroundColor: 'transparent',
    title: {
      text: title,
      left: 'center',
      textStyle: {
        color: '#fff',
        fontSize: 14
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'horizontal',
      bottom: '5%',
      textStyle: {
        color: 'rgba(255, 255, 255, 0.7)'
      }
    },
    series: [
      {
        name: title,
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: 'rgba(0, 212, 255, 0.3)',
          borderWidth: 2
        },
        label: {
          show: true,
          color: '#fff',
          fontSize: 12
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 212, 255, 0.5)'
          }
        },
        labelLine: {
          show: true,
          lineStyle: {
            color: 'rgba(255, 255, 255, 0.5)'
          }
        },
        data: data.map((item, index) => ({
          ...item,
          itemStyle: {
            color: ['#00d4ff', '#7b2cbf', '#ff6b6b', '#4ecdc4', '#ffe66d'][index % 5]
          }
        }))
      }
    ]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initGroupRadar = (el, data) => {
  if (!el) return
  
  const chart = echarts.init(el)
  
  const option = {
    backgroundColor: 'transparent',
    radar: {
      indicator: [
        { name: '专业成绩', max: 100 },
        { name: '科研能力', max: 100 },
        { name: '创新实践', max: 100 },
        { name: '综合素质', max: 100 },
        { name: '外语能力', max: 100 },
        { name: '团队协作', max: 100 }
      ],
      center: ['50%', '48%'],
      radius: '58%',
      axisNameGap: 8,
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: 'rgba(255,255,255,0.88)',
        fontSize: 11,
        padding: [2, 4]
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(123, 44, 191, 0.2)'
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(123, 44, 191, 0.05)', 'rgba(123, 44, 191, 0.1)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(123, 44, 191, 0.3)'
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: data,
        name: '群体能力指标',
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          color: '#7b2cbf',
          width: 2
        },
        areaStyle: {
          color: 'rgba(123, 44, 191, 0.3)',
          opacity: 0.3
        },
        itemStyle: {
          color: '#7b2cbf',
          borderColor: '#fff',
          borderWidth: 2
        }
      }]
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const loadGradeData = () => {
  if (!selectedGrade.value) {
    currentGradeData.value = null
    return
  }
  
  currentGradeData.value = gradeData[selectedGrade.value]
  
  nextTick(() => {
    initGradeCharts()
  })
}

const loadMajorData = () => {
  if (!selectedMajor.value) {
    currentMajorData.value = null
    return
  }
  
  currentMajorData.value = majorData[selectedMajor.value]
  
  nextTick(() => {
    initMajorCharts()
  })
}

const loadClassData = () => {
  if (!selectedClass.value) {
    currentClassData.value = null
    return
  }
  
  currentClassData.value = classData[selectedClass.value]
  
  nextTick(() => {
    initClassCharts()
  })
}

const loadUndergraduateData = () => {
  undergraduateData.value = undergraduateDataValue
  
  nextTick(() => {
    initUndergraduateCharts()
  })
}

const loadGraduateData = () => {
  graduateData.value = graduateDataValue
  
  nextTick(() => {
    initGraduateCharts()
  })
}

watch(activeTab, () => {
  if (activeTab.value === 'teacher') {
    if (teacherView.value === 'overall') loadOverallTeacher()
    else if (selectedTeacher.value) loadTeacherData()
  } else if (activeTab.value === 'student' && selectedStudent.value) {
    loadStudentData()
  }
})

watch(teacherView, () => {
  if (activeTab.value === 'teacher') {
    if (teacherView.value === 'overall') loadOverallTeacher()
  }
})

watch(studentView, () => {
  if (studentView.value === 'grade' && selectedGrade.value) {
    loadGradeData()
  } else if (studentView.value === 'major' && selectedMajor.value) {
    loadMajorData()
  } else if (studentView.value === 'class' && selectedClass.value) {
    loadClassData()
  } else if (studentView.value === 'undergraduate') {
    loadUndergraduateData()
  } else if (studentView.value === 'graduate') {
    loadGraduateData()
  }
})

onMounted(() => {
  loadPortraitData().then(() => {
    nextTick(() => {
      // 处理URL参数
      if (route.query.type && route.query.name) {
        if (route.query.type === 'teacher') {
          activeTab.value = 'teacher'
          teacherSearch.value.name = route.query.name
          const teacher = teachers.value.find(t => t.name.includes(route.query.name))
          if (teacher) {
            selectedTeacher.value = teacher.id.toString()
          }
        } else if (route.query.type === 'student') {
          activeTab.value = 'student'
          studentView.value = 'individual'
          studentSearch.value.name = route.query.name
          const student = students.find(s => s.name.includes(route.query.name))
          if (student) {
            selectedStudent.value = student.id.toString()
          }
        }
      }

      // 默认选择
      if (!selectedTeacher.value && teachers.value.length > 0) {
        selectedTeacher.value = teachers.value[0].id.toString()
      }
      if (!selectedStudent.value && students.length > 0) {
        selectedStudent.value = students[0].id.toString()
      }

      loadTeacherData()
      loadStudentData()
      loadOverallTeacher()
    })
  })
})

onBeforeUnmount(() => {
  if (radarCarouselTimer) {
    clearInterval(radarCarouselTimer)
    radarCarouselTimer = null
  }
})
</script>

<style scoped>
.portrait-page {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 数据来源条 / 示例说明 */
.data-source-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  background: rgba(0, 212, 255, 0.06);
  border: 1px solid rgba(0, 212, 255, 0.18);
  border-radius: 10px;
}

.src-tag {
  padding: 2px 8px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 11px;
}

.src-tag.src-a {
  background: rgba(82, 196, 26, 0.18);
  color: #73d13d;
  border: 1px solid rgba(82, 196, 26, 0.35);
}

.src-tag.src-b {
  background: rgba(0, 212, 255, 0.16);
  color: #00d4ff;
  border: 1px solid rgba(0, 212, 255, 0.35);
}

.src-loading {
  color: rgba(0, 212, 255, 0.8);
}

.src-error {
  color: #ff7875;
}

.demo-note {
  margin-bottom: 14px;
  padding: 12px 16px;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.6);
  background: rgba(250, 173, 20, 0.08);
  border: 1px solid rgba(250, 173, 20, 0.28);
  border-radius: 10px;
}

.demo-note b {
  color: #faad14;
}

.page-header {
  text-align: center;
  margin-bottom: 6px;
}

.header-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 30px;
}

.page-header h2 {
  font-size: 40px;
  color: #fff;
  margin: 0;
  background: linear-gradient(135deg, #ffffff 0%, #00d4ff 50%, #7b2cbf 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
  letter-spacing: 4px;
}

.page-header p {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 2px;
  margin: 8px 0 0;
}

.tab-container-inline {
  display: flex;
  gap: 14px;
}

.tab-btn {
  position: relative;
  padding: 14px 42px;
  border-radius: 10px;
  border: 1px solid rgba(0, 212, 255, 0.4);
  background: rgba(0, 212, 255, 0.06);
  color: rgba(255, 255, 255, 0.75);
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 600;
  letter-spacing: 2px;
  overflow: hidden;
}

.tab-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.5s ease;
}

.tab-btn:hover {
  background: rgba(0, 212, 255, 0.12);
  border-color: rgba(0, 212, 255, 0.6);
  transform: translateY(-2px);
  color: rgba(255, 255, 255, 0.95);
}

.tab-btn:hover::before {
  left: 100%;
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(123, 44, 191, 0.3) 100%);
  border-color: #00d4ff;
  color: #fff;
  box-shadow: 
    0 0 25px rgba(0, 212, 255, 0.45),
    0 0 50px rgba(0, 212, 255, 0.2),
    inset 0 0 20px rgba(0, 212, 255, 0.15);
  transform: translateY(-2px);
}

.sub-tab-container {
  display: flex;
  gap: 10px;
  justify-content: center;
  padding: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  margin-bottom: 16px;
}

.sub-tab-btn {
  padding: 10px 24px;
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.3);
  background: rgba(0, 212, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sub-tab-btn:hover {
  background: rgba(0, 212, 255, 0.15);
}

.sub-tab-btn.active {
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border-color: transparent;
  color: #fff;
}

.filter-bar {
  padding: 18px 22px;
  background: linear-gradient(180deg, rgba(16, 32, 64, 0.7) 0%, rgba(10, 22, 44, 0.85) 100%);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.25);
  display: grid;
  grid-template-columns: 1.3fr 1fr 1fr 1.2fr;
  gap: 16px;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.filter-bar select,
.select-teacher,
.select-student {
  width: 100%;
  padding: 12px 18px;
  border-radius: 8px;
  border: 1px solid rgba(0, 212, 255, 0.35);
  background: rgba(0, 212, 255, 0.06);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  height: 44px;
  box-sizing: border-box;
}

.filter-bar select:hover,
.select-teacher:hover,
.select-student:hover {
  border-color: rgba(0, 212, 255, 0.65);
  background: rgba(0, 212, 255, 0.1);
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.15);
}

.filter-bar select:focus,
.select-teacher:focus,
.select-student:focus {
  outline: none;
  border-color: rgba(0, 212, 255, 0.8);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.25);
}

.filter-bar select option,
.select-teacher option,
.select-student option {
  background: #0a1f44;
  color: #fff;
  padding: 10px;
}

.search-box {
  width: 100%;
  display: flex;
  align-items: center;
  padding: 0 18px;
  background: rgba(0, 212, 255, 0.06);
  border: 1px solid rgba(0, 212, 255, 0.35);
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  height: 44px;
  box-sizing: border-box;
}

.search-box:focus-within {
  border-color: rgba(0, 212, 255, 0.8);
  box-shadow: 0 0 20px rgba(0, 212, 255, 0.25);
  background: rgba(0, 212, 255, 0.1);
}

.search-icon {
  font-size: 18px;
  margin-right: 12px;
  opacity: 0.7;
  flex-shrink: 0;
}

.search-box input {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 14px;
  outline: none;
  width: 100%;
}

.search-box input::placeholder {
  color: rgba(255, 255, 255, 0.45);
}

.portrait-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  animation: fadeInUp 0.5s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ========== 基础信息卡片（二级样式） ========== */
.info-card.level2-card {
  position: relative;
  padding: 28px 32px 24px;
  background: linear-gradient(135deg, rgba(16, 32, 64, 0.8) 0%, rgba(10, 22, 44, 0.9) 100%);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.25);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  overflow: hidden;
}

.card-topline {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #00d4ff, transparent);
  opacity: 0.8;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 28px;
  margin-bottom: 24px;
}

.avatar-ring {
  position: relative;
  width: 110px;
  height: 110px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  padding: 3px;
  box-shadow: 0 0 25px rgba(0, 212, 255, 0.35);
}

.avatar-ring .avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(123, 44, 191, 0.15));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
}

.teacher-name {
  font-size: 30px;
  color: #fff;
  margin: 0 0 10px;
  font-weight: 700;
  letter-spacing: 1px;
  background: linear-gradient(135deg, #ffffff, #00d4ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.teacher-title {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 6px;
  font-weight: 500;
}

.teacher-email {
  font-size: 14px;
  color: rgba(0, 212, 255, 0.8);
  margin: 0;
  font-weight: 500;
}

.info-cards-row {
  display: grid;
  grid-template-columns: 2fr 2fr 1fr 1fr;
  gap: 16px;
}

.info-mini-card {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px 20px;
  background: rgba(0, 212, 255, 0.04);
  border-radius: 10px;
  border: 1px solid rgba(0, 212, 255, 0.12);
  overflow: hidden;
  transition: all 0.3s ease;
}

.info-mini-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #00d4ff, rgba(0, 212, 255, 0));
}

.info-mini-card:hover {
  background: rgba(0, 212, 255, 0.08);
  transform: translateY(-2px);
  border-color: rgba(0, 212, 255, 0.3);
}

.info-mini-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  font-weight: 500;
  letter-spacing: 0.5px;
}

.info-mini-value {
  font-size: 18px;
  color: #fff;
  font-weight: 700;
}

/* ========== 图表卡片（一级样式，带外发光） ========== */
.main-charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.bottom-charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.chart-card.level1-card {
  position: relative;
  padding: 20px 24px 18px;
  background: linear-gradient(180deg, rgba(16, 32, 64, 0.75) 0%, rgba(10, 22, 44, 0.9) 100%);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.28);
  box-shadow: 
    0 0 30px rgba(0, 212, 255, 0.08),
    0 6px 24px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  overflow: hidden;
  transition: all 0.3s ease;
}

.chart-card.level1-card:hover {
  border-color: rgba(0, 212, 255, 0.45);
  box-shadow: 
    0 0 40px rgba(0, 212, 255, 0.12),
    0 8px 32px rgba(0, 0, 0, 0.35);
  transform: translateY(-2px);
}

.card-title {
  font-size: 16px;
  color: #fff;
  margin: 0 0 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  letter-spacing: 0.5px;
}

.card-title::before {
  content: '';
  width: 4px;
  height: 18px;
  background: linear-gradient(180deg, #00d4ff, #7b2cbf);
  border-radius: 2px;
}

.chart-container {
  width: 100%;
  height: 280px;
}

.radar-container {
  height: 300px;
}

/* ========== 教学科研统计条形图 ========== */
.bar-stats-list {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 8px 0;
}

.bar-stat-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bar-stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-stat-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.bar-stat-value {
  font-size: 16px;
  color: #00d4ff;
  font-weight: 700;
}

.bar-stat-track {
  height: 10px;
  background: rgba(0, 212, 255, 0.08);
  border-radius: 5px;
  overflow: hidden;
  position: relative;
}

.bar-stat-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.bar-stat-fill::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 20px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3));
  border-radius: 5px;
}

.bar-1 {
  background: linear-gradient(90deg, rgba(0, 212, 255, 0.2), #00d4ff);
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.bar-2 {
  background: linear-gradient(90deg, rgba(123, 44, 191, 0.2), #7b2cbf);
  box-shadow: 0 0 10px rgba(123, 44, 191, 0.5);
}

.bar-3 {
  background: linear-gradient(90deg, rgba(250, 173, 20, 0.2), #faad14);
  box-shadow: 0 0 10px rgba(250, 173, 20, 0.5);
}

.bar-4 {
  background: linear-gradient(90deg, rgba(82, 196, 26, 0.2), #52c41a);
  box-shadow: 0 0 10px rgba(82, 196, 26, 0.5);
}

/* ========== 原有样式保留（学生部分用） ========== */
.chart-card,
.stats-card,
.tags-card {
  padding: 28px;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 16px;
  border: 1px solid rgba(0, 212, 255, 0.25);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.chart-card:hover,
.stats-card:hover,
.tags-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
}

.chart-card h4,
.stats-card h4,
.tags-card h4 {
  font-size: 18px;
  color: #fff;
  margin-bottom: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
}

.chart-card h4::before,
.stats-card h4::before,
.tags-card h4::before {
  content: '';
  width: 4px;
  height: 20px;
  background: linear-gradient(135deg, #00d4ff, #7b2cbf);
  border-radius: 2px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.08), rgba(123, 44, 191, 0.08));
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.15);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.12), rgba(123, 44, 191, 0.12));
}

.stat-icon {
  font-size: 36px;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 28px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #fff, #00d4ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
  font-weight: 500;
  margin-top: 4px;
}

.tags-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.tag {
  padding: 10px 22px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(123, 44, 191, 0.15));
  border: 1px solid rgba(0, 212, 255, 0.35);
  border-radius: 24px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  transition: all 0.3s ease;
  backdrop-filter: blur(5px);
}

.tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.25), rgba(123, 44, 191, 0.25));
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 16px;
  border: 1px solid rgba(0, 212, 255, 0.25);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 20px;
  opacity: 0.6;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

/* ===== 教师整体画像 ===== */
.overall-teacher-section {
  display: flex;
  flex-direction: column;
  gap: 18px;
  animation: fadeInUp 0.5s ease;
}

.overall-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.okpi-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 22px;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 14px;
  border: 1px solid rgba(0, 212, 255, 0.2);
  transition: all 0.3s ease;
}

.okpi-card:hover {
  border-color: rgba(0, 212, 255, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.okpi-icon {
  width: 54px;
  height: 54px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.okpi-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.okpi-value {
  font-size: 26px;
  font-weight: 800;
  color: #fff;
  line-height: 1.2;
}

.okpi-value i {
  font-size: 13px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.5);
  font-style: normal;
  margin-left: 4px;
}

.okpi-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
}

.okpi-trend {
  font-size: 12px;
  font-weight: 500;
}

.overall-charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.overall-charts-row.four-cols {
  grid-template-columns: repeat(4, 1fr);
}

.mini-chart-card,
.half-chart-card,
.wide-chart-card,
.score-card {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.18);
  padding: 16px 18px;
  transition: all 0.3s ease;
}

.mini-chart-card:hover,
.half-chart-card:hover,
.wide-chart-card:hover,
.score-card:hover {
  border-color: rgba(0, 212, 255, 0.35);
}

.mc-header {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.85);
  font-weight: 600;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.mc-sub {
  margin-left: auto;
  font-size: 11px;
  font-weight: 400;
  color: rgba(0, 212, 255, 0.7);
  white-space: nowrap;
}

.mc-body {
  height: 100px;
  width: 100%;
}

.wordcloud-body {
  height: 220px;
  width: 100%;
}

/* 师资力量 - 手动布局 */
.strength-body {
  padding: 0 2px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.strength-legend {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-left: auto;
}

.strength-legend .legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}

.strength-legend .legend-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  box-shadow: 0 0 5px currentColor;
}

.strength-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 4px 0;
}

.strength-row:hover {
  background: rgba(0, 212, 255, 0.03);
  border-radius: 8px;
}

.s-left {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 115px;
  flex-shrink: 0;
}

.s-icon {
  font-size: 20px;
  width: 26px;
  text-align: center;
  filter: drop-shadow(0 0 4px rgba(0, 212, 255, 0.2));
}

.s-title {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  line-height: 1.3;
}

.s-total {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
  line-height: 1.2;
}

.s-bar-area {
  flex: 1;
  min-width: 0;
}

.s-bar-bg {
  display: flex;
  height: 20px;
  border-radius: 10px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
  box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.3);
}

.s-seg {
  height: 100%;
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.s-seg:first-child {
  border-radius: 10px 0 0 10px;
}

.s-seg:last-child {
  border-radius: 0 10px 10px 0;
}

.s-seg:only-child {
  border-radius: 10px;
}

.s-right {
  width: 72px;
  flex-shrink: 0;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.s-num {
  font-size: 13px;
  font-weight: 700;
  line-height: 1;
  text-shadow: 0 0 4px currentColor;
}

.globe-body {
  height: 300px;
  width: 100%;
}

.radar-body {
  height: 300px;
  width: 100%;
  transition: height 0.3s ease;
}

/* 缩放控件 */
.zoom-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.zoom-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid rgba(0, 212, 255, 0.3);
  background: rgba(0, 212, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.zoom-btn:hover {
  background: rgba(0, 212, 255, 0.2);
  border-color: rgba(0, 212, 255, 0.6);
  color: #00d4ff;
  transform: scale(1.12);
}

.zoom-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  min-width: 36px;
  text-align: center;
  font-variant-numeric: tabular-nums;
}

/* 绩效表格 */
.score-table-wrap {
  max-height: 220px;
  overflow-y: auto;
}

.score-table-wrap::-webkit-scrollbar {
  width: 4px;
}

.score-table-wrap::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
}

.score-table-wrap::-webkit-scrollbar-thumb {
  background: rgba(0, 212, 255, 0.3);
  border-radius: 2px;
}

.score-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  color: #fff;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.score-table th {
  background: rgba(0, 212, 255, 0.15);
  padding: 10px 16px;
  text-align: left;
  font-weight: 600;
  color: #00d4ff;
  border-bottom: 1px solid rgba(0, 212, 255, 0.3);
}

.score-table td {
  padding: 8px 16px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.08);
}

.score-table tr.even td {
  background: rgba(0, 212, 255, 0.02);
}

.score-table tr:hover td {
  background: rgba(0, 212, 255, 0.08);
}

@media (max-width: 1200px) {
  .overall-kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .overall-charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .overall-kpi-row {
    grid-template-columns: 1fr;
  }
  .okpi-card {
    padding: 14px 16px;
  }
  .okpi-value {
    font-size: 22px;
  }
}

.empty-state p {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.65);
  font-weight: 500;
}

.group-portrait {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  animation: fadeInUp 0.5s ease;
}

.summary-card {
  grid-column: span 2;
  padding: 24px;
  background: rgba(0, 0, 0, 0.35);
  border-radius: 16px;
  border: 1px solid rgba(0, 212, 255, 0.25);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(10px);
}

.summary-header h3 {
  font-size: 22px;
  color: #fff;
  margin-bottom: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #fff, #00d4ff);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: rgba(0, 212, 255, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(0, 212, 255, 0.15);
}

.summary-value {
  font-size: 32px;
  font-weight: 800;
  color: #00d4ff;
  margin-bottom: 8px;
}

.summary-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
}

@media (max-width: 1400px) {
  .filter-bar {
    justify-content: center;
  }
  
  .search-box {
    max-width: 250px;
  }
}

@media (max-width: 1200px) {
  .portrait-content {
    grid-template-columns: 1fr;
  }
  
  .info-card {
    grid-column: span 1;
  }
  
  .info-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-bar {
    gap: 12px;
  }
  
  .search-box {
    max-width: 100%;
    min-width: 100%;
  }
  
  .filter-bar select,
  .select-teacher,
  .select-student {
    flex: 1;
    min-width: 140px;
  }
}

@media (max-width: 1200px) {
  .group-portrait {
    grid-template-columns: 1fr;
  }
  
  .summary-card {
    grid-column: span 1;
  }
  
  .summary-stats {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .page-header h2 {
    font-size: 24px;
  }
  
  .tab-btn {
    padding: 10px 24px;
    font-size: 14px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .summary-stats {
    grid-template-columns: 1fr;
  }
  
  .summary-value {
    font-size: 24px;
  }
  
  .avatar {
    width: 100px;
    height: 100px;
    font-size: 48px;
  }
  
  .basic-info h3 {
    font-size: 24px;
  }
}
</style>
