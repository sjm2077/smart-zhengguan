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
            <div class="mc-header">📄 近六年科研论文总数</div>
            <div ref="overallPaperChart" class="mc-body"></div>
          </div>
          <div class="mini-chart-card">
            <div class="mc-header">📋 近六年科研项目总数</div>
            <div ref="overallProjectChart" class="mc-body"></div>
          </div>
          <div class="mini-chart-card">
            <div class="mc-header">💰 近六年科研经费合计</div>
            <div ref="overallFeeChart" class="mc-body"></div>
          </div>
          <div class="mini-chart-card">
            <div class="mc-header">👥 教师总人数趋势</div>
            <div ref="overallTeacherChart" class="mc-body"></div>
          </div>
        </div>

        <!-- 第二行：师资力量（手动布局） + 主要研究词云 -->
        <div class="overall-charts-row">
          <div class="half-chart-card">
            <div class="mc-header">
              <span>📊 师资力量</span>
              <div class="strength-legend">
                <span class="legend-item"><span class="legend-dot" style="background:#7b2cbf"></span>博士</span>
                <span class="legend-item"><span class="legend-dot" style="background:#00d4ff"></span>硕士</span>
                <span class="legend-item"><span class="legend-dot" style="background:#52c41a"></span>学士</span>
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

        <!-- 第三行：培养经历3D地球 + 绩效指标雷达 -->
        <div class="overall-charts-row">
          <div class="wide-chart-card">
            <div class="mc-header">🌍 培养经历（教师教育背景全球分布）</div>
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
            <option value="教授">教授</option>
            <option value="副教授">副教授</option>
            <option value="讲师">讲师</option>
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
              <p class="teacher-email">{{ currentTeacher.email }}</p>
            </div>
          </div>
          <div class="info-cards-row">
            <div class="info-mini-card wide">
              <span class="info-mini-label">入职时间</span>
              <span class="info-mini-value">{{ currentTeacher.joinYear }}年</span>
            </div>
            <div class="info-mini-card wide">
              <span class="info-mini-label">研究方向</span>
              <span class="info-mini-value">{{ currentTeacher.research }}</span>
            </div>
            <div class="info-mini-card">
              <span class="info-mini-label">学历</span>
              <span class="info-mini-value">{{ currentTeacher.education }}</span>
            </div>
            <div class="info-mini-card">
              <span class="info-mini-label">指导学生</span>
              <span class="info-mini-value">{{ currentTeacher.students }}人</span>
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
                  <span class="bar-stat-label">授课课时</span>
                  <span class="bar-stat-value">{{ currentTeacher.courses * 48 }}课时</span>
                </div>
                <div class="bar-stat-track">
                  <div class="bar-stat-fill bar-1" :style="{ width: (currentTeacher.courses / 12 * 100) + '%' }"></div>
                </div>
              </div>
              <div class="bar-stat-item">
                <div class="bar-stat-header">
                  <span class="bar-stat-label">项目数量</span>
                  <span class="bar-stat-value">{{ currentTeacher.projects }}项</span>
                </div>
                <div class="bar-stat-track">
                  <div class="bar-stat-fill bar-2" :style="{ width: (currentTeacher.projects / 20 * 100) + '%' }"></div>
                </div>
              </div>
              <div class="bar-stat-item">
                <div class="bar-stat-header">
                  <span class="bar-stat-label">论文成果</span>
                  <span class="bar-stat-value">{{ currentTeacher.papers }}篇</span>
                </div>
                <div class="bar-stat-track">
                  <div class="bar-stat-fill bar-3" :style="{ width: (currentTeacher.papers / 70 * 100) + '%' }"></div>
                </div>
              </div>
              <div class="bar-stat-item">
                <div class="bar-stat-header">
                  <span class="bar-stat-label">获奖情况</span>
                  <span class="bar-stat-value">{{ currentTeacher.awards }}项</span>
                </div>
                <div class="bar-stat-track">
                  <div class="bar-stat-fill bar-4" :style="{ width: (currentTeacher.awards / 15 * 100) + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bottom-charts-row">
          <div class="chart-card level1-card">
            <div class="card-topline"></div>
            <h4 class="card-title">纵向职称分布</h4>
            <div ref="titleDistributionChart" class="chart-container"></div>
          </div>
          <div class="chart-card level1-card">
            <div class="card-topline"></div>
            <h4 class="card-title">科研项目等级</h4>
            <div ref="projectLevelChart" class="chart-container"></div>
          </div>
        </div>

        <div class="bottom-charts-row">
          <div class="chart-card level1-card">
            <div class="card-topline"></div>
            <h4 class="card-title">历年招生趋势</h4>
            <div ref="enrollmentChart" class="chart-container"></div>
          </div>
          <div class="chart-card level1-card">
            <div class="card-topline"></div>
            <h4 class="card-title">学生评价评分</h4>
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
import { ref, onMounted, nextTick, watch, computed } from 'vue'
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

const teacherResearchOptions = ['公共政策', '政府治理', '政治学理论', '比较政治', '国际关系', '国际安全', '公共管理', '社会保障']
const studentMajorOptions = ['行政管理', '政治学理论', '国际政治', '公共管理', '政治学与行政学']

const teachers = [
  {
    id: 1,
    name: '张伟',
    title: '教授',
    department: '行政管理系',
    email: 'zhangwei@sdu.edu.cn',
    phone: '0531-88366001',
    office: '逸夫楼A座301室',
    joinYear: 2008,
    research: '公共政策、政府治理',
    education: '博士',
    degree: '北京大学政府管理学院',
    students: 25,
    phdStudents: 12,
    masterStudents: 13,
    courses: 8,
    projects: 12,
    nationalProjects: 5,
    provincialProjects: 7,
    papers: 45,
    sciePapers: 8,
    cssciPapers: 30,
    awards: 8,
    nationalAwards: 2,
    provincialAwards: 6,
    tags: ['公共政策', '政府治理', '博士生导师', '长江学者', '国家级项目', '教学名师'],
    radarData: [85, 92, 88, 90, 85, 80],
    teachingCourses: ['公共政策分析', '公共管理学', '政策评估'],
    achievements: ['主持国家社科基金重大项目1项', '发表SSCI论文5篇', '获省部级教学成果一等奖'],
    honors: ['长江学者特聘教授', '国务院特殊津贴专家', '山东省教学名师']
  },
  {
    id: 2,
    name: '李娜',
    title: '副教授',
    department: '政治学系',
    email: 'lina@sdu.edu.cn',
    phone: '0531-88366002',
    office: '逸夫楼B座205室',
    joinYear: 2015,
    research: '政治学理论、比较政治',
    education: '博士',
    degree: '复旦大学国际关系与公共事务学院',
    students: 15,
    phdStudents: 0,
    masterStudents: 15,
    courses: 6,
    projects: 8,
    nationalProjects: 2,
    provincialProjects: 6,
    papers: 28,
    sciePapers: 3,
    cssciPapers: 20,
    awards: 5,
    nationalAwards: 0,
    provincialAwards: 5,
    tags: ['政治学理论', '比较政治', '硕士生导师', '省部级项目', '青年学者'],
    radarData: [78, 85, 90, 82, 88, 75],
    teachingCourses: ['政治学原理', '比较政治学', '西方政治思想史'],
    achievements: ['主持国家社科基金青年项目1项', '发表CSSCI论文20篇'],
    honors: ['山东大学青年教学能手', '山东省社科优秀成果奖']
  },
  {
    id: 3,
    name: '王强',
    title: '教授',
    department: '国际政治系',
    email: 'wangqiang@sdu.edu.cn',
    phone: '0531-88366003',
    office: '逸夫楼C座402室',
    joinYear: 2010,
    research: '国际关系、国际安全',
    education: '博士',
    degree: '中国人民大学国际关系学院',
    students: 20,
    phdStudents: 8,
    masterStudents: 12,
    courses: 7,
    projects: 10,
    nationalProjects: 4,
    provincialProjects: 6,
    papers: 35,
    sciePapers: 6,
    cssciPapers: 25,
    awards: 6,
    nationalAwards: 1,
    provincialAwards: 5,
    tags: ['国际关系', '国际安全', '博士生导师', '国家级项目', '智库专家'],
    radarData: [88, 80, 85, 92, 82, 88],
    teachingCourses: ['国际政治学', '国际关系理论', '国际安全研究'],
    achievements: ['主持国家社科基金重点项目2项', '参与外交部政策咨询'],
    honors: ['山东省智库专家', '中国国际关系学会理事']
  },
  {
    id: 4,
    name: '赵敏',
    title: '讲师',
    department: '公共管理系',
    email: 'zhaomin@sdu.edu.cn',
    phone: '0531-88366004',
    office: '逸夫楼A座108室',
    joinYear: 2018,
    research: '公共管理、社会保障',
    education: '博士',
    degree: '中山大学政治与公共事务管理学院',
    students: 8,
    phdStudents: 0,
    masterStudents: 8,
    courses: 5,
    projects: 4,
    nationalProjects: 0,
    provincialProjects: 4,
    papers: 15,
    sciePapers: 1,
    cssciPapers: 10,
    awards: 2,
    nationalAwards: 0,
    provincialAwards: 2,
    tags: ['公共管理', '社会保障', '青年教师', '博士后'],
    radarData: [72, 88, 80, 75, 90, 82],
    teachingCourses: ['公共管理学', '社会保障概论', '公共经济学'],
    achievements: ['主持山东省社科规划项目1项', '发表CSSCI论文10篇'],
    honors: ['山东大学优秀博士后', '青年教师讲课比赛三等奖']
  },
  {
    id: 5,
    name: '陈建国',
    title: '教授',
    department: '行政管理系',
    email: 'chenjg@sdu.edu.cn',
    phone: '0531-88366005',
    office: '逸夫楼A座305室',
    joinYear: 2005,
    research: '公共政策、行政管理',
    education: '博士',
    degree: '武汉大学政治与公共管理学院',
    students: 32,
    phdStudents: 15,
    masterStudents: 17,
    courses: 10,
    projects: 18,
    nationalProjects: 6,
    provincialProjects: 12,
    papers: 60,
    sciePapers: 10,
    cssciPapers: 40,
    awards: 12,
    nationalAwards: 3,
    provincialAwards: 9,
    tags: ['公共政策', '行政管理', '博士生导师', '泰山学者', '国家级项目'],
    radarData: [92, 95, 90, 88, 85, 87],
    teachingCourses: ['行政管理学', '公共政策学', '电子政务'],
    achievements: ['主持国家自然科学基金项目3项', '发表SCI/SSCI论文10篇'],
    honors: ['泰山学者特聘教授', '山东省有突出贡献中青年专家']
  },
  {
    id: 6,
    name: '刘洋',
    title: '副教授',
    department: '国际政治系',
    email: 'liuyang@sdu.edu.cn',
    phone: '0531-88366006',
    office: '逸夫楼C座303室',
    joinYear: 2012,
    research: '国际关系、全球治理',
    education: '博士',
    degree: '清华大学国际关系学院',
    students: 18,
    phdStudents: 5,
    masterStudents: 13,
    courses: 7,
    projects: 9,
    nationalProjects: 3,
    provincialProjects: 6,
    papers: 32,
    sciePapers: 5,
    cssciPapers: 22,
    awards: 7,
    nationalAwards: 1,
    provincialAwards: 6,
    tags: ['国际关系', '全球治理', '硕士生导师', '省部级项目', '青年拔尖'],
    radarData: [85, 82, 88, 90, 86, 84],
    teachingCourses: ['当代中国外交', '全球治理', '国际组织'],
    achievements: ['主持国家社科基金一般项目2项', '发表SSCI论文5篇'],
    honors: ['山东大学青年拔尖人才', '山东省优秀青年知识分子']
  },
  {
    id: 7,
    name: '王芳',
    title: '讲师',
    department: '政治学系',
    email: 'wangf@sdu.edu.cn',
    phone: '0531-88366007',
    office: '逸夫楼B座106室',
    joinYear: 2020,
    research: '政治学理论、中国政治',
    education: '博士',
    degree: '南京大学政府管理学院',
    students: 6,
    phdStudents: 0,
    masterStudents: 6,
    courses: 4,
    projects: 3,
    nationalProjects: 1,
    provincialProjects: 2,
    papers: 12,
    sciePapers: 0,
    cssciPapers: 8,
    awards: 1,
    nationalAwards: 0,
    provincialAwards: 1,
    tags: ['政治学理论', '中国政治', '青年教师', '新锐学者'],
    radarData: [78, 80, 85, 82, 88, 76],
    teachingCourses: ['中国政府与政治', '政治学方法论', '政治社会学'],
    achievements: ['主持国家社科基金青年项目1项', '发表CSSCI论文8篇'],
    honors: ['山东大学新锐青年学者', '优秀班主任']
  },
  {
    id: 8,
    name: '马丽',
    title: '副教授',
    department: '公共管理系',
    email: 'mali@sdu.edu.cn',
    phone: '0531-88366008',
    office: '逸夫楼A座209室',
    joinYear: 2016,
    research: '社会保障、社会政策',
    education: '博士',
    degree: '南开大学周恩来政府管理学院',
    students: 14,
    phdStudents: 3,
    masterStudents: 11,
    courses: 6,
    projects: 7,
    nationalProjects: 2,
    provincialProjects: 5,
    papers: 25,
    sciePapers: 2,
    cssciPapers: 18,
    awards: 4,
    nationalAwards: 0,
    provincialAwards: 4,
    tags: ['社会保障', '社会政策', '硕士生导师', '省部级项目'],
    radarData: [82, 86, 84, 88, 80, 85],
    teachingCourses: ['社会保障学', '社会政策', '社会工作概论'],
    achievements: ['主持国家社科基金一般项目1项', '发表CSSCI论文18篇'],
    honors: ['山东省社会科学优秀成果奖', '山东大学优秀教师']
  },
  {
    id: 9,
    name: '刘建国',
    title: '教授',
    department: '政治学与行政学系',
    email: 'liujg@sdu.edu.cn',
    phone: '0531-88366009',
    office: '逸夫楼B座401室',
    joinYear: 2006,
    research: '政治学方法论、定量研究',
    education: '博士',
    degree: '香港大学政治与公共行政学系',
    students: 28,
    phdStudents: 10,
    masterStudents: 18,
    courses: 9,
    projects: 15,
    nationalProjects: 5,
    provincialProjects: 10,
    papers: 55,
    sciePapers: 12,
    cssciPapers: 35,
    awards: 10,
    nationalAwards: 2,
    provincialAwards: 8,
    tags: ['政治学方法论', '定量研究', '博士生导师', '国家级项目', '大数据'],
    radarData: [88, 90, 85, 95, 82, 86],
    teachingCourses: ['政治学研究方法', '统计分析', '数据可视化'],
    achievements: ['主持国家自然科学基金项目3项', '发表SCI论文12篇'],
    honors: ['教育部新世纪优秀人才', '山东省优秀研究生导师']
  },
  {
    id: 10,
    name: '孙丽华',
    title: '副教授',
    department: '行政管理系',
    email: 'sunlh@sdu.edu.cn',
    phone: '0531-88366010',
    office: '逸夫楼A座307室',
    joinYear: 2014,
    research: '行政法学、政府法制',
    education: '博士',
    degree: '中国政法大学法学院',
    students: 12,
    phdStudents: 2,
    masterStudents: 10,
    courses: 6,
    projects: 6,
    nationalProjects: 1,
    provincialProjects: 5,
    papers: 22,
    sciePapers: 0,
    cssciPapers: 15,
    awards: 3,
    nationalAwards: 0,
    provincialAwards: 3,
    tags: ['行政法学', '政府法制', '硕士生导师', '法律顾问'],
    radarData: [80, 84, 88, 82, 86, 83],
    teachingCourses: ['行政法学', '行政诉讼法', '公务员法'],
    achievements: ['主持司法部项目1项', '出版专著2部'],
    honors: ['山东省政府法律顾问', '山东大学优秀共产党员']
  }
]

const students = [
  {
    id: 1001,
    name: '陈小明',
    major: '行政管理',
    level: '博士研究生',
    studentId: '2023001',
    enrollYear: 2023,
    origin: '山东济南',
    supervisor: '张伟',
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
    name: '刘芳',
    major: '政治学理论',
    level: '硕士研究生',
    studentId: '2024002',
    enrollYear: 2024,
    origin: '河南郑州',
    supervisor: '李娜',
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
    name: '孙浩',
    major: '国际政治',
    level: '本科生',
    studentId: '2022003',
    enrollYear: 2022,
    origin: '江苏南京',
    supervisor: '王强',
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
    name: '周婷',
    major: '公共管理',
    level: 'MPA',
    studentId: '2023004',
    enrollYear: 2023,
    origin: '广东深圳',
    supervisor: '赵敏',
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
    name: '赵磊',
    major: '行政管理',
    level: '硕士研究生',
    studentId: '2023005',
    enrollYear: 2023,
    origin: '山东青岛',
    supervisor: '陈建国',
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
    name: '孙梦瑶',
    major: '政治学与行政学',
    level: '本科生',
    studentId: '2022006',
    enrollYear: 2022,
    origin: '山东烟台',
    supervisor: '王芳',
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
    name: '李伟',
    major: '国际政治',
    level: '博士研究生',
    studentId: '2022007',
    enrollYear: 2022,
    origin: '北京',
    supervisor: '刘洋',
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
    name: '张雪',
    major: '公共管理',
    level: '硕士研究生',
    studentId: '2024008',
    enrollYear: 2024,
    origin: '山东潍坊',
    supervisor: '马丽',
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
    name: '王建国',
    major: '行政管理',
    level: 'MPA',
    studentId: '2023009',
    enrollYear: 2023,
    origin: '山东淄博',
    supervisor: '陈建国',
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
    name: '李娜',
    major: '政治学理论',
    level: '本科生',
    studentId: '2024010',
    enrollYear: 2024,
    origin: '山东临沂',
    supervisor: '李娜',
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
    name: '赵强',
    major: '国际政治',
    level: '硕士研究生',
    studentId: '2023011',
    enrollYear: 2023,
    origin: '山东济宁',
    supervisor: '王强',
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
    name: '陈静',
    major: '公共管理',
    level: '博士研究生',
    studentId: '2022012',
    enrollYear: 2022,
    origin: '山东泰安',
    supervisor: '赵敏',
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
  return teachers.filter(t => {
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

const initTeacherRadar = (data) => {
  if (!radarChart.value) return
  
  const chart = echarts.init(radarChart.value)
  
  const option = {
    backgroundColor: 'transparent',
    radar: {
      indicator: [
        { name: '教学能力', max: 100 },
        { name: '科研能力', max: 100 },
        { name: '学术影响力', max: 100 },
        { name: '团队协作', max: 100 },
        { name: '创新能力', max: 100 },
        { name: '社会服务', max: 100 }
      ],
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#fff',
        fontSize: 12
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
  
  chart.setOption(option)
  
  window.addEventListener('resize', () => chart.resize())
}

const initTitleDistributionChart = () => {
  if (!titleDistributionChart.value) return
  
  const chart = echarts.init(titleDistributionChart.value)
  
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
      itemGap: 15
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
      data: [
        { value: 37, name: '教授', itemStyle: { color: '#7b2cbf' } },
        { value: 35, name: '副教授', itemStyle: { color: '#00d4ff' } },
        { value: 28, name: '讲师', itemStyle: { color: '#52c41a' } }
      ],
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
    grid: { left: 80, right: 50, top: 20, bottom: 30 },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: ['国家级', '省部级', '市厅级', '横向合作'],
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 16,
      data: [
        { value: teacher.nationalProjects || 5, itemStyle: { color: '#7b2cbf', borderRadius: [0, 6, 6, 0] } },
        { value: teacher.provincialProjects || 7, itemStyle: { color: '#00d4ff', borderRadius: [0, 6, 6, 0] } },
        { value: Math.floor((teacher.projects - (teacher.nationalProjects || 5) - (teacher.provincialProjects || 7)) * 0.6) || 3, itemStyle: { color: '#faad14', borderRadius: [0, 6, 6, 0] } },
        { value: Math.floor((teacher.projects - (teacher.nationalProjects || 5) - (teacher.provincialProjects || 7)) * 0.4) || 2, itemStyle: { color: '#52c41a', borderRadius: [0, 6, 6, 0] } }
      ],
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
  
  const years = ['2020', '2021', '2022', '2023', '2024']
  const base = Math.floor(teacher.students / 3)
  
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
      data: years,
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
      data: [base - 2, base, base + 1, base + 2, base + 3],
      lineStyle: { color: '#00d4ff', width: 3 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0,212,255,0.3)' },
          { offset: 1, color: 'rgba(0,212,255,0.02)' }
        ])
      },
      symbolSize: 8,
      itemStyle: { color: '#00d4ff' }
    }]
  }
  
  chart.setOption(option)
  window.addEventListener('resize', () => chart.resize())
}

const initStudentEvalChart = (teacher) => {
  if (!studentEvalChart.value) return
  
  const chart = echarts.init(studentEvalChart.value)
  
  const categories = ['教学态度', '教学内容', '教学方法', '教学效果', '师生互动']
  const scores = [95, 92, 90, 93, 88].map(s => Math.min(99, s + Math.floor(Math.random() * 5)))
  
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
      min: 70,
      max: 100,
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(0,212,255,0.08)' } }
    },
    yAxis: {
      type: 'category',
      data: categories.reverse(),
      axisLine: { lineStyle: { color: 'rgba(0,212,255,0.25)' } },
      axisLabel: { color: 'rgba(255,255,255,0.85)', fontSize: 12 }
    },
    series: [{
      type: 'bar',
      barWidth: 14,
      data: scores.reverse().map((val, i) => ({
        value: val,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: 'rgba(123,44,191,0.3)' },
            { offset: 1, color: '#7b2cbf' }
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
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#fff',
        fontSize: 12
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

// ====== 整体教师画像数据 ======
const overallKpi = [
  { icon: '📄', value: '268', unit: '篇', label: '近六年科研论文总数', trend: '↑ 同比增长12%', trendColor: '#52c41a', bg: 'linear-gradient(135deg, rgba(0,212,255,0.2), rgba(0,212,255,0.05))' },
  { icon: '📋', value: '96', unit: '项', label: '近六年科研项目总数', trend: '↑ 同比增长18%', trendColor: '#52c41a', bg: 'linear-gradient(135deg, rgba(123,44,191,0.2), rgba(123,44,191,0.05))' },
  { icon: '💰', value: '3010', unit: '万元', label: '近六年科研经费合计', trend: '↑ 同比增长7%', trendColor: '#52c41a', bg: 'linear-gradient(135deg, rgba(54,207,201,0.2), rgba(54,207,201,0.05))' },
  { icon: '👥', value: '103', unit: '人', label: '2026年教师总人数', trend: '↑ 较去年+1人', trendColor: '#52c41a', bg: 'linear-gradient(135deg, rgba(82,196,26,0.2), rgba(82,196,26,0.05))' }
]

const teacherStrength = [
  { title: '教授', total: 37, icon: '👨‍🏫', bars: [{ label: '博士', count: 27, percent: 73, color: '#7b2cbf' }, { label: '硕士', count: 10, percent: 27, color: '#00d4ff' }] },
  { title: '副教授', total: 30, icon: '👨‍🔬', bars: [{ label: '博士', count: 19, percent: 63.33, color: '#7b2cbf' }, { label: '硕士', count: 10, percent: 33.33, color: '#00d4ff' }, { label: '学士', count: 1, percent: 3.34, color: '#52c41a' }] },
  { title: '副研究员', total: 1, icon: '🔬', bars: [{ label: '博士', count: 1, percent: 100, color: '#7b2cbf' }] },
  { title: '讲师', total: 5, icon: '📖', bars: [{ label: '博士', count: 2, percent: 40, color: '#7b2cbf' }, { label: '硕士', count: 2, percent: 40, color: '#00d4ff' }, { label: '学士', count: 1, percent: 20, color: '#52c41a' }] },
  { title: '助理研究员', total: 16, icon: '💡', bars: [{ label: '博士', count: 10, percent: 62.5, color: '#7b2cbf' }, { label: '硕士', count: 4, percent: 25, color: '#00d4ff' }, { label: '学士', count: 2, percent: 12.5, color: '#52c41a' }] },
  { title: '博士后', total: 14, icon: '🎓', bars: [{ label: '博士', count: 14, percent: 100, color: '#7b2cbf' }] }
]

const scoreData = [
  { name: '张伟', score: 95 }, { name: '李娜', score: 88 }, { name: '王强', score: 92 },
  { name: '赵敏', score: 78 }, { name: '陈建国', score: 97 }, { name: '刘洋', score: 86 },
  { name: '王芳', score: 75 }, { name: '马丽', score: 84 }, { name: '刘建国', score: 93 },
  { name: '孙丽华', score: 82 }, { name: '陈小明', score: 72 }, { name: '刘芳', score: 79 },
  { name: '孙浩', score: 70 }, { name: '周婷', score: 76 }, { name: '赵磊', score: 81 },
  { name: '孙梦瑶', score: 83 }, { name: '李伟', score: 90 }, { name: '张雪', score: 74 },
  { name: '王建国', score: 68 }, { name: '赵强', score: 77 }
]

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
  radarZoom.value = Math.max(0.4, Math.min(2.5, radarZoom.value + delta))
  const chart = overallRadarChart.value?._chart
  if (chart) {
    const el = overallRadarChart.value
    el.style.height = (240 * radarZoom.value) + 'px'
    chart.resize()
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
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(24,141,240,0.4)', textStyle: { color: '#fff', fontWeight: 'bold' }, formatter: p => `<div style="padding:4px 8px"><span>年份: ${p[0].name}</span><br><span>数值: ${p[0].value}</span></div>` },
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
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(24,141,240,0.4)', textStyle: { color: '#fff', fontWeight: 'bold' }, formatter: p => `<div style="padding:4px 8px"><span>年份: ${p[0].name}</span><br><span>数值: ${p[0].value}</span></div>` },
    series: [{ type: 'line', data: data.map(d => d.count), smooth: true, symbol: 'circle', symbolSize: 5, lineStyle: { color, width: 3 }, itemStyle: { color, borderColor: '#fff', borderWidth: 2 } }]
  })
  return chart
}

const initOverallCharts = () => {
  // 师资力量 - 手动HTML布局（无ECharts图表）
  // 数据由 teacherStrength 驱动，模板直接渲染

  // 论文柱状图
  initMiniBarChart(overallPaperChart.value, [
    { year: 2019, count: 34 }, { year: 2020, count: 23 }, { year: 2021, count: 42 },
    { year: 2022, count: 48 }, { year: 2023, count: 66 }, { year: 2024, count: 55 }
  ])
  // 项目折线图
  initMiniLineChart(overallProjectChart.value, [
    { year: 2019, count: 12 }, { year: 2020, count: 15 }, { year: 2021, count: 14 },
    { year: 2022, count: 18 }, { year: 2023, count: 17 }, { year: 2024, count: 20 }
  ])
  // 经费柱状图
  initMiniBarChart(overallFeeChart.value, [
    { year: 2019, count: 46 }, { year: 2020, count: 48 }, { year: 2021, count: 51 },
    { year: 2022, count: 49 }, { year: 2023, count: 52 }, { year: 2024, count: 55 }
  ], '#36cfc9')
  // 教师人数折线图
  initMiniLineChart(overallTeacherChart.value, [
    { year: 2019, count: 94 }, { year: 2020, count: 95 }, { year: 2021, count: 97 },
    { year: 2022, count: 105 }, { year: 2023, count: 102 }, { year: 2024, count: 103 }
  ], '#52c41a')
  
  // 研究领域词云
  if (overallWordCloud.value) {
    const wc = echarts.init(overallWordCloud.value)
    overallWordCloud.value._chart = wc
    const wordData = {
      "治理": 400, "发展": 338, "中国": 314, "社会": 294, "制度": 240, "政治": 237, "研究": 218,
      "政策": 213, "国家": 202, "政府": 160, "影响": 155, "组织": 142, "建设": 139, "全球": 137,
      "体系": 137, "现代化": 137, "理论": 136, "国际": 126, "城市": 122, "政党": 121, "技术": 119,
      "关系": 114, "机制": 114, "安全": 113, "问题": 110, "分析": 109, "能力": 103, "创新": 101,
      "实践": 100, "基层": 98, "乡村": 97, "社会主义": 97, "数字": 96, "路径": 94, "战略": 93,
      "推进": 92, "经济": 92, "能源": 91, "转型": 88, "提升": 87, "推动": 87, "构建": 86,
      "基础": 84, "时代": 82, "风险": 79, "气候": 79, "公共服务": 60, "民主": 53, "回应": 52
    }
    wc.setOption({
      backgroundColor: 'transparent',
      series: [{
        type: 'wordCloud', shape: 'circle', width: '90%', height: '90%',
        sizeRange: [10, 34], rotationRange: [-30, 30], gridSize: 4,
        textStyle: { fontFamily: 'Microsoft YaHei', color: () => `hsl(${Math.random() * 360}, 100%, 70%)` },
        emphasis: { textStyle: { color: '#fff', fontSize: 36, textShadowBlur: 20, textShadowColor: '#00d4ff' } },
        data: Object.entries(wordData).map(([name, value]) => ({ name, value }))
      }]
    })
  }

  // 雷达图
  if (overallRadarChart.value) {
    const radar = echarts.init(overallRadarChart.value)
    overallRadarChart.value._chart = radar
    radar.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      radar: {
        indicator: [
          { name: '教学', max: 12 }, { name: '科研论文', max: 55 }, { name: '科研项目', max: 50 },
          { name: '兼职工作', max: 3 }, { name: '荣誉表彰', max: 15 }, { name: '教育成果', max: 16 }
        ],
        name: { textStyle: { color: '#fff', fontSize: 11 } },
        axisLine: { lineStyle: { color: 'rgba(0,212,255,0.3)' } },
        splitLine: { lineStyle: { color: 'rgba(0,255,255,0.5)' } },
        splitArea: { areaStyle: { color: ['rgba(0,212,255,0.02)', 'rgba(0,212,255,0.05)'] } }
      },
      series: [{
        type: 'radar', symbolSize: 6,
        data: [{ value: [1.9, 19.7, 21.1, 0.4, 1.1, 3.8], name: '平均分', lineStyle: { color: '#11e5fc' }, areaStyle: { color: 'rgba(0,212,255,0.15)' }, itemStyle: { color: '#e7feb8' } }]
      }]
    })
    // 自动轮播
    const indv = {
      '张伟': [0.0, 10.2, 30.0, 0.0, 0.0, 11.8], '李娜': [0.0, 27.2, 16.0, 0.0, 0.0, 5.9],
      '王强': [0.0, 49.3, 16.1, 0.0, 1.6, 0.0], '陈建国': [4.8, 10.0, 14.1, 1.0, 1.0, 0.0],
      '刘洋': [0.0, 6.8, 23.1, 0.0, 0.5, 0.5], '赵敏': [0.0, 19.9, 10.8, 0.0, 1.6, 9.7]
    }
    const names = Object.keys(indv)
    let idx = 0
    setInterval(() => {
      const name = names[idx]
      radar.setOption({
        series: [{
          data: [
            { value: [1.9, 19.7, 21.1, 0.4, 1.1, 3.8], name: '平均分', lineStyle: { color: '#11e5fc', opacity: 0.5 }, areaStyle: { color: '#e7feb8' }, itemStyle: { color: '#e7feb8' } },
            { value: indv[name], name, lineStyle: { color: '#0ef9fe', width: 3 }, areaStyle: { color: '#d890fa' }, itemStyle: { color: '#8ff9f8' } }
          ]
        }]
      })
      idx = (idx + 1) % names.length
    }, 3500)
  }

  // 3D地球 - 使用真实教师数据
  if (overallGlobeChart.value) {
    // 注册世界地图
    registerWorldMap(echarts)
    
    const globe = echarts.init(overallGlobeChart.value)
    
    // 加载教师数据
    fetch('/data/teachers.json')
      .then(res => res.json())
      .catch(() => ({ teachers: [] }))
      .then(data => {
        const teachers = data.teachers || []
        
        // 提取所有院校点
        const points = []
        const routeData = []
        
        teachers.forEach(t => {
          const insts = []
          if (t.undergraduate) {
            points.push({ value: [t.undergraduate.longitude, t.undergraduate.latitude], name: t.undergraduate.name })
            insts.push([t.undergraduate.longitude, t.undergraduate.latitude])
          }
          if (t.graduate) {
            points.push({ value: [t.graduate.longitude, t.graduate.latitude], name: t.graduate.name })
            insts.push([t.graduate.longitude, t.graduate.latitude])
          }
          if (t.doctorate) {
            points.push({ value: [t.doctorate.longitude, t.doctorate.latitude], name: t.doctorate.name })
            insts.push([t.doctorate.longitude, t.doctorate.latitude])
          }
          if (t['other institutions']) {
            points.push({ value: [t['other institutions'].longitude, t['other institutions'].latitude], name: t['other institutions'].name })
            insts.push([t['other institutions'].longitude, t['other institutions'].latitude])
          }
          if (insts.length >= 2) routeData.push(insts)
        })
      globe.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          show: true,
          trigger: 'item',
          formatter: p => p.data?.name || '',
          backgroundColor: 'rgba(24,141,240,0.4)',
          textStyle: { color: '#ffffff' }
        },
        geo3D: {
          map: 'world',
          environment: 'none',
          shading: 'realistic',
          realisticMaterial: { roughness: 0.6, metalness: 0.2 },
          light: {
            main: { intensity: 2, alpha: 50, beta: 10 },
            ambient: { intensity: 0.4 }
          },
          viewControl: {
            distance: 15,
            alpha: 50,
            beta: 0,
            autoRotate: true,
            autoRotateSpeed: 3,
            panMouseButton: 'left',
            rotateMouseButton: 'right'
          },
          itemStyle: {
            color: 'rgb(24,141,240)',
            opacity: 0.8
          },
          regionHeight: 1.5
        },
        series: [
          {
            type: 'lines3D',
            coordinateSystem: 'geo3D',
            effect: {
              show: true,
              trailWidth: 1,
              trailOpacity: 0.8,
              trailLength: 0.5,
              constantSpeed: 6
            },
            blendMode: 'lighter',
            lineStyle: {
              width: 1,
              opacity: 1,
              color: 'rgb(255,0,0)'
            },
            data: routeData
          },
          {
            type: 'scatter3D',
            coordinateSystem: 'geo3D',
            symbolSize: 8,
            itemStyle: {
              color: 'rgba(255,255,255,0.7)',
              opacity: 1
            },
            data: points
          }
        ]
      })
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
  
  const teacher = teachers.find(t => t.id == selectedTeacher.value)
  currentTeacher.value = teacher
  
  nextTick(() => {
    if (teacher) {
      initTeacherRadar(teacher.radarData)
      initTitleDistributionChart()
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
      shape: 'polygon',
      splitNumber: 5,
      axisName: {
        color: '#fff',
        fontSize: 12
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
  nextTick(() => {
    // 处理URL参数
    if (route.query.type && route.query.name) {
      if (route.query.type === 'teacher') {
        activeTab.value = 'teacher'
        teacherSearch.value.name = route.query.name
        const teacher = teachers.find(t => t.name.includes(route.query.name))
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
    if (!selectedTeacher.value && teachers.length > 0) {
      selectedTeacher.value = teachers[0].id.toString()
    }
    if (!selectedStudent.value && students.length > 0) {
      selectedStudent.value = students[0].id.toString()
    }
    
    loadTeacherData()
    loadStudentData()
    loadOverallTeacher()
  })
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
  height: 280px;
  width: 100%;
}

.radar-body {
  height: 240px;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
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
