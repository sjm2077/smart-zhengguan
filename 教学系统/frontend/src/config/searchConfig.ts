/**
 * 全局搜索配置
 * 将搜索关键词映射到具体的路由路径和页面内模块
 */

export interface SearchModuleEntry {
  /** 搜索关键词（支持模糊匹配，命中任一关键词即匹配） */
  keywords: string[]
  /** 目标路由路径 */
  path: string
  /** 页面内模块 ID（用于滚动定位和高亮），不填则仅跳转路由 */
  moduleId?: string
  /** 模块名称（用于搜索建议显示） */
  label: string
}

export const searchModuleMap: SearchModuleEntry[] = [
  // ======================== 数据总览 Dashboard ========================
  { keywords: ['教学运行分析', '运行分析'], path: '/', moduleId: 'module-teaching-analysis', label: '教学运行分析' },
  { keywords: ['学院课程结构', '课程结构分布', '学院课程结构分布'], path: '/', moduleId: 'module-college-course-structure', label: '学院课程结构分布' },
  { keywords: ['教学质量评分', '质量评分排行', '教学质量评分排行'], path: '/', moduleId: 'module-teaching-quality-ranking', label: '教学质量评分排行' },
  { keywords: ['各专业课程', '课程开设趋势', '各专业课程开设趋势', '专业课程趋势'], path: '/', moduleId: 'module-major-course-trend', label: '各专业课程开设趋势' },
  { keywords: ['学生培养', '教学热点', '学生培养与教学热点'], path: '/', moduleId: 'module-student-cultivation', label: '学生培养与教学热点' },
  { keywords: ['学生成绩分布', '成绩分布'], path: '/', moduleId: 'module-grade-distribution', label: '学生成绩分布' },
  { keywords: ['毕业生就业', '就业去向', '毕业生就业去向'], path: '/', moduleId: 'module-graduate-employment', label: '毕业生就业去向' },
  { keywords: ['教学热点分析', '热点分析', '课程关键词', '评教热词'], path: '/', moduleId: 'module-teaching-hotspot', label: '教学热点分析' },
  { keywords: ['教师发展', '科研分析', '教师发展与科研分析'], path: '/', moduleId: 'module-teacher-development', label: '教师发展与科研分析' },
  { keywords: ['教师职称结构', '职称结构'], path: '/', moduleId: 'module-teacher-title-structure', label: '教师职称结构' },
  { keywords: ['科研成果趋势', '科研成果'], path: '/', moduleId: 'module-research-trend', label: '科研成果趋势' },
  { keywords: ['通知与预警', '通知公告', '异常预警'], path: '/', moduleId: 'module-notification-alert', label: '通知与预警' },
  { keywords: ['学院通知公告'], path: '/', moduleId: 'module-college-notices', label: '学院通知公告' },
  { keywords: ['教学异常预警', '异常预警'], path: '/', moduleId: 'module-teaching-alerts', label: '教学异常预警' },
  { keywords: ['实时动态', '动态'], path: '/', moduleId: 'module-live-stream', label: '实时动态' },

  // ======================== 教学预警 WarningCenter ========================
  { keywords: ['教学预警', '预警中心', '学业预警'], path: '/dashboard/warning', label: '教学预警' },
  { keywords: ['学业预警与风险分析', '风险分析'], path: '/dashboard/warning', moduleId: 'module-academic-risk', label: '学业预警与风险分析' },
  { keywords: ['风险等级学生数量', '风险等级趋势', '各风险等级学生数量趋势'], path: '/dashboard/warning', moduleId: 'module-risk-trend', label: '各风险等级学生数量趋势' },
  { keywords: ['当前风险等级分布', '风险等级分布'], path: '/dashboard/warning', moduleId: 'module-risk-distribution', label: '当前风险等级分布' },
  { keywords: ['学院预警排行', '预警排行', '学院预警排行与重点学生'], path: '/dashboard/warning', moduleId: 'module-college-ranking', label: '学院预警排行与重点学生' },
  { keywords: ['各学院预警学生数量排行', '预警学生排行'], path: '/dashboard/warning', moduleId: 'module-college-warning-ranking', label: '各学院预警学生数量排行' },
  { keywords: ['重点预警学生', '预警学生', '重点预警'], path: '/dashboard/warning', moduleId: 'module-key-warning-students', label: '重点预警学生' },
  { keywords: ['教学异常事件记录', '异常事件', '异常记录'], path: '/dashboard/warning', moduleId: 'module-exception-events', label: '教学异常事件记录' },
  { keywords: ['异常事件列表'], path: '/dashboard/warning', moduleId: 'module-exception-list', label: '异常事件列表' },

  // ======================== 课程管理 CourseManage ========================
  { keywords: ['课程管理', '课程'], path: '/course', label: '课程管理' },
  { keywords: ['教研室课程分布图', '课程分布图', '教研室课程分布'], path: '/course', moduleId: 'module-dept-course-distribution', label: '教研室课程分布图' },
  { keywords: ['课程热度排行', '热度排行', '课程热度'], path: '/course', moduleId: 'module-course-hot-ranking', label: '课程热度排行' },
  { keywords: ['课程分类树', '分类树'], path: '/course', moduleId: 'module-course-category-tree', label: '课程分类树' },
  { keywords: ['教学计划进度', '计划进度'], path: '/course', moduleId: 'module-teaching-plan-progress', label: '教学计划进度' },
  { keywords: ['课程容量分析', '容量分析'], path: '/course', moduleId: 'module-course-capacity', label: '课程容量分析' },
  { keywords: ['课程封面展示', '封面展示'], path: '/course', moduleId: 'module-course-cover', label: '课程封面展示' },
  { keywords: ['热门课程趋势', '热门课程'], path: '/course', moduleId: 'module-hot-course-trend', label: '热门课程趋势' },
  { keywords: ['课程时间轴', '时间轴'], path: '/course', moduleId: 'module-course-timeline', label: '课程时间轴' },

  // ======================== 教师管理 TeacherManage ========================
  { keywords: ['教师管理', '教师', '老师', '师资'], path: '/teacher', label: '教师管理' },
  { keywords: ['教师资源', '教学能力', '教师资源与教学能力中心'], path: '/teacher', label: '教师资源与教学能力中心' },
  { keywords: ['骨干教师画像', '教师画像', '骨干教师', '专家画像'], path: '/teacher', moduleId: 'module-key-teacher-profiles', label: '骨干教师画像' },
  { keywords: ['教师职称分布', '职称分布'], path: '/teacher', moduleId: 'module-title-distribution', label: '教师职称分布' },
  { keywords: ['教师工作量排行', '工作量排行'], path: '/teacher', moduleId: 'module-workload-ranking', label: '教师工作量排行' },
  { keywords: ['教师科研成果', '教师科研'], path: '/teacher', moduleId: 'module-teacher-research', label: '教师科研成果' },
  { keywords: ['课程关系图'], path: '/teacher', moduleId: 'module-course-relation', label: '课程关系图' },
  { keywords: ['本月优秀教师', '优秀教师'], path: '/teacher', moduleId: 'module-outstanding-teachers', label: '本月优秀教师' },
  { keywords: ['教师年龄结构', '年龄结构'], path: '/teacher', moduleId: 'module-age-structure', label: '教师年龄结构' },
  { keywords: ['教师考核评分', '考核评分'], path: '/teacher', moduleId: 'module-evaluation-score', label: '教师考核评分' },
  { keywords: ['课时热力图', '热力图'], path: '/teacher', moduleId: 'module-teaching-hours-heatmap', label: '课时热力图' },
  { keywords: ['教学团队'], path: '/teacher', moduleId: 'module-teaching-team', label: '教学团队' },

  // ======================== 学生管理 StudentManage ========================
  { keywords: ['学生管理', '学生'], path: '/student', label: '学生管理' },
  { keywords: ['学生画像卡', '学生画像', '画像卡'], path: '/student', moduleId: 'module-student-profile-card', label: '学生画像卡' },
  { keywords: ['学生地区来源', '地区来源', '生源地区'], path: '/student', moduleId: 'module-student-region-source', label: '学生地区来源' },
  { keywords: ['年级与专业分布', '年级分布', '专业分布'], path: '/student', moduleId: 'module-grade-major-distribution', label: '年级与专业分布' },
  { keywords: ['学业预警名单', '预警名单', '学生预警'], path: '/student', moduleId: 'module-academic-warning-list', label: '学业预警名单' },
  { keywords: ['就业与深造趋势', '就业深造', '就业趋势', '深造趋势'], path: '/student', moduleId: 'module-employment-further-study', label: '就业与深造趋势' },
  { keywords: ['学生活跃度热力图', '活跃度', '学生活跃度'], path: '/student', moduleId: 'module-activity-heatmap', label: '学生活跃度热力图' },
  { keywords: ['学生成长时间轴', '成长时间轴', '成长记录'], path: '/student', moduleId: 'module-student-growth-timeline', label: '学生成长时间轴' },
  { keywords: ['优秀学生荣誉榜', '荣誉榜', '优秀学生'], path: '/student', moduleId: 'module-honor-roll', label: '优秀学生荣誉榜' },
  { keywords: ['班级数据对比', '班级对比'], path: '/student', moduleId: 'module-class-comparison', label: '班级数据对比' },

  // ======================== 考试管理 ExamManage ========================
  { keywords: ['考试管理', '考试', '考核', '测验'], path: '/exam', label: '考试管理' },
  { keywords: ['考试日历'], path: '/exam', moduleId: 'module-exam-calendar', label: '考试日历' },
  { keywords: ['今日考试'], path: '/exam', moduleId: 'module-today-exams', label: '今日考试' },
  { keywords: ['考场分布图', '考场分布'], path: '/exam', moduleId: 'module-exam-room-distribution', label: '考场分布图' },
  { keywords: ['冲突预警', '考试冲突'], path: '/exam', moduleId: 'module-conflict-warning', label: '冲突预警' },
  { keywords: ['监考安排'], path: '/exam', moduleId: 'module-invigilation-arrangement', label: '监考安排' },
  { keywords: ['考试时间轴', '考试时间'], path: '/exam', moduleId: 'module-exam-timeline', label: '考试时间轴' },
  { keywords: ['考试进度状态', '考试进度', '进度状态'], path: '/exam', moduleId: 'module-exam-progress', label: '考试进度状态' },
  { keywords: ['缺考统计'], path: '/exam', moduleId: 'module-absence-statistics', label: '缺考统计' },
  { keywords: ['考场利用率'], path: '/exam', moduleId: 'module-room-utilization', label: '考场利用率' },
  { keywords: ['实时考试监控', '考试监控', '实时监控'], path: '/exam', moduleId: 'module-live-exam-monitor', label: '实时考试监控' },

  // ======================== 成绩管理 GradeManage ========================
  { keywords: ['成绩管理', '成绩', '分数', '绩点'], path: '/grade', label: '成绩管理' },
  { keywords: ['成绩分析', '教学质量', '成绩分析与教学质量中心'], path: '/grade', label: '成绩分析与教学质量中心' },
  { keywords: ['GPA 分布图', 'GPA分布', 'GPA'], path: '/grade', moduleId: 'module-gpa-distribution', label: 'GPA 分布图' },
  { keywords: ['成绩区间分析', '区间分析'], path: '/grade', moduleId: 'module-score-interval', label: '成绩区间分析' },
  { keywords: ['不及格率', '不及格'], path: '/grade', moduleId: 'module-fail-rate', label: '不及格率' },
  { keywords: ['成绩趋势'], path: '/grade', moduleId: 'module-grade-trend', label: '成绩趋势' },
  { keywords: ['学院排行', '平均分排行'], path: '/grade', moduleId: 'module-college-avg-rank', label: '各学院平均分排行' },
  { keywords: ['优秀率'], path: '/grade', moduleId: 'module-excellence-rate', label: '优秀率' },
  { keywords: ['挂科预警', '挂科'], path: '/grade', moduleId: 'module-fail-warning', label: '挂科预警' },
  { keywords: ['成绩波动分析', '波动分析'], path: '/grade', moduleId: 'module-volatility', label: '成绩波动分析' },
  { keywords: ['教学评分', '评分'], path: '/grade', moduleId: 'module-teaching-score', label: '教学评分' },
  { keywords: ['AI 建议', 'AI建议', '成绩分析建议'], path: '/grade', moduleId: 'module-ai-suggestions', label: 'AI 成绩分析建议' },

  // ======================== 教学分析 TeachingAnalysis ========================
  { keywords: ['教学分析', '分析', '统计', '报表'], path: '/analysis', label: '教学分析' },
  { keywords: ['数据驾驶舱', '驾驶舱'], path: '/analysis', moduleId: 'module-data-cockpit', label: '数据驾驶舱' },
  { keywords: ['AI 分析建议', '人工智能分析', 'AI分析'], path: '/analysis', moduleId: 'module-ai-analysis', label: 'AI 分析建议' },
  { keywords: ['教研室对比雷达图', '对比雷达图', '教研室对比'], path: '/analysis', moduleId: 'module-dept-radar', label: '教研室对比雷达图' },
  { keywords: ['教学热点词云', '热点词云', '词云'], path: '/analysis', moduleId: 'module-hot-word-cloud', label: '教学热点词云' },
  { keywords: ['教学质量分析与趋势预测', '质量分析', '趋势预测'], path: '/analysis', moduleId: 'module-quality-trend', label: '教学质量分析与趋势预测' },
  { keywords: ['风险预警'], path: '/analysis', moduleId: 'module-risk-warning', label: '风险预警' },
  { keywords: ['教学满意度分析', '满意度分析', '满意度'], path: '/analysis', moduleId: 'module-satisfaction-analysis', label: '教学满意度分析' },
  { keywords: ['教师教学质量分布', '质量分布'], path: '/analysis', moduleId: 'module-teacher-quality-distribution', label: '教师教学质量分布' },
]

/**
 * 根据搜索关键词查找匹配的模块
 */
export function findSearchMatch(keyword: string): SearchModuleEntry | null {
  if (!keyword.trim()) return null
  const lowerKeyword = keyword.toLowerCase()
  // 按关键词长度降序排列，优先匹配更具体的搜索词
  const sorted = [...searchModuleMap].sort(
    (a, b) => Math.max(...b.keywords.map(k => k.length)) - Math.max(...a.keywords.map(k => k.length))
  )
  for (const entry of sorted) {
    const matched = entry.keywords.some(k => lowerKeyword.includes(k.toLowerCase()))
    if (matched) return entry
  }
  return null
}

/**
 * 根据搜索关键词获取搜索建议列表
 */
export function getSearchSuggestions(keyword: string): SearchModuleEntry[] {
  if (!keyword.trim()) return []
  const lowerKeyword = keyword.toLowerCase()
  return searchModuleMap
    .filter(entry => entry.keywords.some(k => k.toLowerCase().includes(lowerKeyword)))
    .slice(0, 8) // 最多返回8条建议
}