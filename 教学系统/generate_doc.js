const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  WidthType,
  AlignmentType,
  HeadingLevel,
  BorderStyle,
  ShadingType,
  TableLayoutType,
} = require("docx");
const fs = require("fs");

// ==================== 数据库表定义 ====================
const tables = [
  {
    name: "users",
    func: "系统登录账号 / 认证",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["username", "VARCHAR(64)", "", "UNIQUE idx_username", "NOT NULL"],
      ["password_hash", "VARCHAR(255)", "", "", "NOT NULL"],
      ["role", "ENUM('admin','teacher','student')", "", "idx_role", "NOT NULL"],
      ["teacher_id", "BIGINT UNSIGNED", "FK → teachers.id (SET NULL)", "idx_teacher_id", "NULL (仅 role=teacher)"],
      ["student_id", "BIGINT UNSIGNED", "FK → students.id (SET NULL)", "idx_student_id", "NULL (仅 role=student)"],
      ["last_login_at", "DATETIME", "", "", "NULL"],
      ["is_active", "TINYINT(1)", "", "", "DEFAULT 1"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
      ["deleted_at", "DATETIME", "", "", "NULL"],
    ],
  },
  {
    name: "colleges",
    func: "学院 / 教研室 / 研究中心",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(128)", "", "UNIQUE idx_name", "NOT NULL"],
      ["short_name", "VARCHAR(32)", "", "", "NULL（如\"政治学\"\"行管\"）"],
      ["type", "ENUM('college','department','research_center')", "", "idx_type", "NOT NULL (college=学院, department=教研室, research_center=研究中心)"],
      ["parent_id", "BIGINT UNSIGNED", "FK → colleges.id (SET NULL)", "idx_parent_id", "NULL (教研单位树形结构)"],
      ["sort_order", "INT", "", "", "DEFAULT 0"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
      ["deleted_at", "DATETIME", "", "", "NULL"],
    ],
  },
  {
    name: "majors",
    func: "专业",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(128)", "", "UNIQUE idx_name", "NOT NULL"],
      ["short_name", "VARCHAR(32)", "", "", "NULL"],
      ["college_id", "BIGINT UNSIGNED", "FK → colleges.id (SET NULL)", "idx_college_id", "NULL"],
      ["degree_level", "ENUM('bachelor','master','doctor')", "", "idx_degree_level", "NOT NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
      ["deleted_at", "DATETIME", "", "", "NULL"],
    ],
  },
  {
    name: "teachers",
    func: "教师基本信息",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(64)", "", "idx_name", "NOT NULL"],
      ["gender", "ENUM('male','female')", "", "idx_gender", "NOT NULL"],
      ["birth_date", "DATE", "", "", "NULL"],
      ["title", "ENUM('professor','associate_professor','lecturer','assistant')", "", "idx_title", "NOT NULL（教授/副教授/讲师/助教）"],
      ["college_id", "BIGINT UNSIGNED", "FK → colleges.id (SET NULL)", "idx_college_id", "NULL"],
      ["research_direction", "VARCHAR(255)", "", "", "NULL"],
      ["phone", "VARCHAR(32)", "", "", "NULL (脱敏)"],
      ["email", "VARCHAR(128)", "", "", "NULL"],
      ["avatar_url", "VARCHAR(255)", "", "", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
      ["deleted_at", "DATETIME", "", "", "NULL"],
    ],
  },
  {
    name: "students",
    func: "学生基本信息",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["student_code", "VARCHAR(32)", "", "UNIQUE idx_student_code", "NOT NULL（学号）"],
      ["name", "VARCHAR(64)", "", "idx_name", "NOT NULL"],
      ["gender", "ENUM('male','female')", "", "idx_gender", "NOT NULL"],
      ["college_id", "BIGINT UNSIGNED", "FK → colleges.id (SET NULL)", "idx_college_id", "NULL"],
      ["major_id", "BIGINT UNSIGNED", "FK → majors.id (SET NULL)", "idx_major_id", "NULL"],
      ["class_name", "VARCHAR(64)", "", "idx_class_name", "NULL（班级名称，如\"2023级行政管理1班\"）"],
      ["grade", "VARCHAR(16)", "", "idx_grade", "NULL（如\"2023\"）"],
      ["degree_level", "ENUM('bachelor','master','doctor')", "", "idx_degree_level", "NOT NULL"],
      ["region", "VARCHAR(64)", "", "idx_region", "NULL（生源地省份/直辖市）"],
      ["phone", "VARCHAR(32)", "", "", "NULL (脱敏)"],
      ["status", "ENUM('active','suspended','retained','warning','graduated','withdrawn')", "", "idx_status", "NOT NULL DEFAULT 'active' (在读/休学/留级/警告/毕业/退学)"],
      ["gpa", "DECIMAL(4,2)", "", "idx_gpa", "NULL"],
      ["earned_credits", "DECIMAL(5,1)", "", "", "DEFAULT 0（已修学分）"],
      ["total_credits", "DECIMAL(5,1)", "", "", "DEFAULT 0（总学分要求）"],
      ["failed_courses", "INT UNSIGNED", "", "", "DEFAULT 0（挂科门数）"],
      ["risk_level", "ENUM('normal','yellow','orange','red')", "", "idx_risk_level", "DEFAULT 'normal'（学业预警级别）"],
      ["attendance_rate", "DECIMAL(5,2)", "", "", "NULL（出勤率百分比）"],
      ["is_international", "TINYINT(1)", "", "", "DEFAULT 0"],
      ["is_party_member", "TINYINT(1)", "", "", "DEFAULT 0"],
      ["avatar_bg", "VARCHAR(32)", "", "", "NULL（前端头像背景色标识）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
      ["deleted_at", "DATETIME", "", "", "NULL"],
    ],
  },
  {
    name: "classes",
    func: "班级汇总数据",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(64)", "", "UNIQUE idx_name", "NOT NULL"],
      ["college_id", "BIGINT UNSIGNED", "FK → colleges.id (SET NULL)", "idx_college_id", "NULL"],
      ["major_id", "BIGINT UNSIGNED", "FK → majors.id (SET NULL)", "idx_major_id", "NULL"],
      ["grade", "VARCHAR(16)", "", "idx_grade", "NOT NULL"],
      ["student_count", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["avg_gpa", "DECIMAL(4,2)", "", "", "NULL"],
      ["excellent_rate", "DECIMAL(5,2)", "", "", "NULL"],
      ["warning_count", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["cet4_pass_rate", "DECIMAL(5,2)", "", "", "NULL"],
      ["cet6_pass_rate", "DECIMAL(5,2)", "", "", "NULL"],
      ["competition_awards", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["semester", "VARCHAR(32)", "", "idx_semester", "NOT NULL（如\"2024-2025-2\"）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "courses",
    func: "课程库（课程基本信息）",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["code", "VARCHAR(32)", "", "UNIQUE idx_code", "NOT NULL（课程代码）"],
      ["name", "VARCHAR(128)", "", "idx_name", "NOT NULL"],
      ["credit", "DECIMAL(3,1)", "", "", "NOT NULL"],
      ["hours", "INT UNSIGNED", "", "", "NOT NULL（总学时）"],
      ["category_id", "BIGINT UNSIGNED", "FK → course_categories.id (SET NULL)", "idx_category_id", "NULL"],
      ["college_id", "BIGINT UNSIGNED", "FK → colleges.id (SET NULL)", "idx_college_id", "NULL（开课学院）"],
      ["type", "ENUM('required','elective','general')", "", "idx_type", "NOT NULL（必修/选修/通识）"],
      ["campus", "VARCHAR(64)", "", "", "NULL（开课校区）"],
      ["description", "TEXT", "", "", "NULL（课程简介）"],
      ["cover_color", "VARCHAR(32)", "", "", "NULL（前端封面主色）"],
      ["cover_gradient", "VARCHAR(64)", "", "", "NULL（前端封面渐变色）"],
      ["cover_icon", "VARCHAR(64)", "", "", "NULL（前端封面图标类型）"],
      ["status", "ENUM('active','inactive')", "", "idx_status", "DEFAULT 'active'"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
      ["deleted_at", "DATETIME", "", "", "NULL"],
    ],
  },
  {
    name: "course_categories",
    func: "课程分类树",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(64)", "", "", "NOT NULL"],
      ["color", "VARCHAR(16)", "", "", "NULL（前端分类颜色）"],
      ["parent_id", "BIGINT UNSIGNED", "FK → course_categories.id (SET NULL)", "idx_parent_id", "NULL"],
      ["sort_order", "INT", "", "", "DEFAULT 0"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "course_offerings",
    func: "每学期实际开课",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["course_id", "BIGINT UNSIGNED", "FK → courses.id (CASCADE)", "idx_course_id", "NOT NULL"],
      ["teacher_id", "BIGINT UNSIGNED", "FK → teachers.id (SET NULL)", "idx_teacher_id", "NULL"],
      ["semester", "VARCHAR(32)", "", "idx_semester", "NOT NULL（如\"2024-2025-2\"）"],
      ["weeks", "INT UNSIGNED", "", "", "NOT NULL（教学总周数）"],
      ["completed_weeks", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["capacity", "INT UNSIGNED", "", "", "NOT NULL（课容量上限）"],
      ["enrolled", "INT UNSIGNED", "", "", "DEFAULT 0（当前选课人数）"],
      ["waitlist", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["class_location", "VARCHAR(255)", "", "", "NULL（上课地点）"],
      ["class_time", "VARCHAR(255)", "", "", "NULL（上课时间描述）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "course_enrollments",
    func: "学生选课",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["course_offering_id", "BIGINT UNSIGNED", "FK → course_offerings.id (CASCADE)", "idx_offering_id", "NOT NULL"],
      ["student_id", "BIGINT UNSIGNED", "FK → students.id (CASCADE)", "idx_student_id", "NOT NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["", "", "", "UNIQUE (course_offering_id, student_id)", "一个学生同一门课只选一次"],
    ],
  },
  {
    name: "course_schedules",
    func: "课程上课时间地点（详细排课）",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["course_offering_id", "BIGINT UNSIGNED", "FK → course_offerings.id (CASCADE)", "idx_offering_id", "NOT NULL"],
      ["day_of_week", "TINYINT UNSIGNED", "", "", "NOT NULL (1=周一~7=周日)"],
      ["start_period", "TINYINT UNSIGNED", "", "", "NOT NULL（开始节次）"],
      ["end_period", "TINYINT UNSIGNED", "", "", "NOT NULL（结束节次）"],
      ["location", "VARCHAR(128)", "", "", "NOT NULL（教室/地点）"],
      ["campus", "VARCHAR(64)", "", "", "NULL"],
      ["week_pattern", "VARCHAR(32)", "", "", "DEFAULT '1-18'（如\"1-8,10-18\"）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "course_changes",
    func: "课程变更记录",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["course_offering_id", "BIGINT UNSIGNED", "FK → course_offerings.id (SET NULL)", "idx_offering_id", "NULL"],
      ["course_name", "VARCHAR(128)", "", "", "NOT NULL"],
      ["change_type", "VARCHAR(32)", "", "", "NOT NULL（变更类型：调课/停课/换教师/换教室）"],
      ["change_time", "DATETIME", "", "idx_change_time", "NOT NULL"],
      ["reason", "TEXT", "", "", "NULL（变更原因）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "teaching_plans",
    func: "教学计划进度",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(128)", "", "", "NOT NULL（教学计划名称）"],
      ["semester", "VARCHAR(32)", "", "idx_semester", "NOT NULL"],
      ["total_weeks", "INT UNSIGNED", "", "", "NOT NULL"],
      ["completed_weeks", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["milestones", "JSON", "", "", "NULL（里程碑列表）"],
      ["college_id", "BIGINT UNSIGNED", "FK → colleges.id (SET NULL)", "idx_college_id", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "grades",
    func: "学生成绩",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["student_id", "BIGINT UNSIGNED", "FK → students.id (CASCADE)", "idx_student_id", "NOT NULL"],
      ["course_offering_id", "BIGINT UNSIGNED", "FK → course_offerings.id (CASCADE)", "idx_offering_id", "NOT NULL"],
      ["score", "DECIMAL(5,2)", "", "idx_score", "NULL（百分制成绩，NULL=未录入）"],
      ["gpa_points", "DECIMAL(3,1)", "", "", "NULL（绩点值）"],
      ["grade_level", "ENUM('excellent','good','medium','pass','fail')", "", "idx_grade_level", "NULL（优秀/良好/中等/及格/不及格）"],
      ["status", "ENUM('draft','submitted','verified')", "", "", "DEFAULT 'draft'（录入状态）"],
      ["semester", "VARCHAR(32)", "", "idx_semester", "NOT NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
      ["", "", "", "UNIQUE (student_id, course_offering_id)", "一个学生一门课只有一条成绩"],
    ],
  },
  {
    name: "exams",
    func: "考试信息",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["course_offering_id", "BIGINT UNSIGNED", "FK → course_offerings.id (SET NULL)", "idx_offering_id", "NULL"],
      ["name", "VARCHAR(128)", "", "", "NOT NULL（考试名称）"],
      ["course_name", "VARCHAR(128)", "", "", "NULL"],
      ["exam_date", "DATE", "", "idx_exam_date", "NOT NULL"],
      ["start_time", "TIME", "", "", "NOT NULL"],
      ["end_time", "TIME", "", "", "NOT NULL"],
      ["venue_id", "BIGINT UNSIGNED", "FK → exam_venues.id (SET NULL)", "idx_venue_id", "NULL"],
      ["venue_name", "VARCHAR(128)", "", "", "NULL"],
      ["exam_type", "ENUM('final','midterm','makeup','retake')", "", "", "DEFAULT 'final'（期末/期中/补考/重修考）"],
      ["capacity", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["enrolled_count", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["status", "ENUM('pending','ongoing','finished','archived')", "", "idx_status", "DEFAULT 'pending'（待考/进行中/已结束/已归档）"],
      ["semester", "VARCHAR(32)", "", "idx_semester", "NOT NULL"],
      ["grade_deadline", "DATE", "", "", "NULL（成绩录入截止日期）"],
      ["makeup_date", "DATE", "", "", "NULL（补考日期）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "exam_venues",
    func: "考场/教室",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(128)", "", "UNIQUE idx_name", "NOT NULL"],
      ["building", "VARCHAR(64)", "", "", "NULL"],
      ["capacity", "INT UNSIGNED", "", "", "NOT NULL"],
      ["campus", "VARCHAR(64)", "", "", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "exam_invigilators",
    func: "监考安排",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["exam_id", "BIGINT UNSIGNED", "FK → exams.id (CASCADE)", "idx_exam_id", "NOT NULL"],
      ["teacher_id", "BIGINT UNSIGNED", "FK → teachers.id (SET NULL)", "idx_teacher_id", "NULL"],
      ["role", "ENUM('main','assistant','patrol')", "", "", "NOT NULL（主监考/副监考/巡考）"],
      ["teacher_name", "VARCHAR(64)", "", "", "NULL（冗余字段方便前端）"],
      ["teacher_college", "VARCHAR(64)", "", "", "NULL（冗余字段）"],
      ["arrive_time", "TIME", "", "", "NULL（到达时间）"],
      ["phone", "VARCHAR(32)", "", "", "NULL"],
      ["status", "VARCHAR(16)", "", "", "DEFAULT 'confirmed'（confirmed/pending）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "exam_absence",
    func: "缺考统计",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["exam_id", "BIGINT UNSIGNED", "FK → exams.id (CASCADE)", "idx_exam_id", "NOT NULL"],
      ["student_id", "BIGINT UNSIGNED", "FK → students.id (CASCADE)", "idx_student_id", "NOT NULL"],
      ["reason", "VARCHAR(255)", "", "", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["", "", "", "UNIQUE (exam_id, student_id)", ""],
    ],
  },
  {
    name: "notices",
    func: "通知公告",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["title", "VARCHAR(255)", "", "", "NOT NULL"],
      ["content", "TEXT", "", "", "NULL（内容摘要/详情）"],
      ["type", "ENUM('academic','research','admin','student')", "", "idx_type", "NOT NULL（教务/科研/行政/学工）"],
      ["publisher_id", "BIGINT UNSIGNED", "FK → users.id (SET NULL)", "", "NULL"],
      ["publish_time", "DATETIME", "", "idx_publish_time", "NOT NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "alerts",
    func: "教学异常预警",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["title", "VARCHAR(255)", "", "", "NOT NULL"],
      ["description", "TEXT", "", "", "NULL"],
      ["level", "ENUM('red','orange','yellow')", "", "idx_level", "NOT NULL（高/中/低风险）"],
      ["scope", "VARCHAR(128)", "", "", "NULL（涉及范围/课程/专业）"],
      ["suggested_action", "TEXT", "", "", "NULL（建议措施）"],
      ["is_resolved", "TINYINT(1)", "", "", "DEFAULT 0"],
      ["created_at", "DATETIME", "", "idx_created_at", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "operation_logs",
    func: "实时动态 / 操作日志",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["text", "VARCHAR(255)", "", "", "NOT NULL（动态内容）"],
      ["action_time", "DATETIME", "", "idx_action_time", "NOT NULL"],
      ["user_id", "BIGINT UNSIGNED", "FK → users.id (SET NULL)", "", "NULL"],
      ["log_type", "VARCHAR(32)", "", "idx_log_type", "DEFAULT 'system'（system/teacher/student/exam）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "research_outputs",
    func: "科研成果",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["teacher_id", "BIGINT UNSIGNED", "FK → teachers.id (CASCADE)", "idx_teacher_id", "NOT NULL"],
      ["year", "YEAR", "", "idx_year", "NOT NULL"],
      ["type", "ENUM('paper','project','horizontal','national_fund','think_tank','policy_report','monograph')", "", "idx_type", "NOT NULL"],
      ["count", "INT UNSIGNED", "", "", "DEFAULT 1"],
      ["funding_amount", "DECIMAL(12,2)", "", "", "NULL（科研经费，万元）"],
      ["description", "VARCHAR(255)", "", "", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
    note: "type 枚举说明: paper=论文(CSSCI/SSCI), project=国家级课题, horizontal=横向项目, national_fund=国家社科基金, think_tank=智库成果, policy_report=政策咨询报告, monograph=专著教材",
  },
  {
    name: "teaching_evaluations",
    func: "教学评价（6维度学生评教）",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["course_offering_id", "BIGINT UNSIGNED", "FK → course_offerings.id (CASCADE)", "idx_offering_id", "NOT NULL"],
      ["student_id", "BIGINT UNSIGNED", "FK → students.id (CASCADE)", "idx_student_id", "NOT NULL"],
      ["semester", "VARCHAR(32)", "", "idx_semester", "NOT NULL"],
      ["content_score", "TINYINT UNSIGNED", "", "", "NULL（教学内容 1-5）"],
      ["method_score", "TINYINT UNSIGNED", "", "", "NULL（教学方法 1-5）"],
      ["atmosphere_score", "TINYINT UNSIGNED", "", "", "NULL（课堂氛围 1-5）"],
      ["tutoring_score", "TINYINT UNSIGNED", "", "", "NULL（教学辅导 1-5）"],
      ["exam_score", "TINYINT UNSIGNED", "", "", "NULL（考核方式 1-5）"],
      ["material_score", "TINYINT UNSIGNED", "", "", "NULL（教材选用 1-5）"],
      ["overall_score", "DECIMAL(3,1)", "", "", "NULL（综合评分）"],
      ["comment", "TEXT", "", "", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["", "", "", "UNIQUE (course_offering_id, student_id)", ""],
    ],
  },
  {
    name: "student_activities",
    func: "学生活动记录",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(128)", "", "", "NOT NULL"],
      ["activity_date", "DATE", "", "idx_activity_date", "NOT NULL"],
      ["participant_count", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["organizer", "VARCHAR(128)", "", "", "NULL（主办方）"],
      ["description", "TEXT", "", "", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "library_records",
    func: "图书馆刷卡记录",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["student_id", "BIGINT UNSIGNED", "FK → students.id (CASCADE)", "idx_student_id", "NOT NULL"],
      ["entry_time", "DATETIME", "", "idx_entry_time", "NOT NULL"],
      ["exit_time", "DATETIME", "", "", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "employment_stats",
    func: "就业统计（按年）",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["year", "YEAR", "", "UNIQUE idx_year", "NOT NULL"],
      ["total_graduates", "INT UNSIGNED", "", "", "NOT NULL（毕业总人数）"],
      ["employed_count", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["employment_rate", "DECIMAL(5,2)", "", "", "NULL（就业率%）"],
      ["further_study_count", "INT UNSIGNED", "", "", "DEFAULT 0（升学深造人数）"],
      ["further_study_rate", "DECIMAL(5,2)", "", "", "NULL（深造率%）"],
      ["avg_starting_salary", "DECIMAL(8,2)", "", "", "NULL（平均起薪，千元/月）"],
      ["career_distribution", "JSON", "", "", "NULL（就业去向分布）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "scholarships",
    func: "奖学金记录",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["student_id", "BIGINT UNSIGNED", "FK → students.id (CASCADE)", "idx_student_id", "NOT NULL"],
      ["name", "VARCHAR(128)", "", "", "NOT NULL（奖学金名称）"],
      ["level", "VARCHAR(32)", "", "", "NULL（校级/省级/国家级）"],
      ["award_year", "YEAR", "", "idx_award_year", "NOT NULL"],
      ["award_name", "VARCHAR(255)", "", "", "NULL（奖项名称）"],
      ["honor_tags", "JSON", "", "", "NULL（荣誉标签）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "teacher_teams",
    func: "教学团队",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(128)", "", "", "NOT NULL"],
      ["leader_id", "BIGINT UNSIGNED", "FK → teachers.id (SET NULL)", "idx_leader_id", "NULL"],
      ["members", "JSON", "", "", "NULL（成员ID列表）"],
      ["courses", "JSON", "", "", "NULL（负责课程ID列表）"],
      ["funding", "DECIMAL(12,2)", "", "", "NULL（经费万元）"],
      ["papers", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["strength", "DECIMAL(3,1)", "", "", "NULL（团队综合实力评分）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "student_growth_records",
    func: "学生成长记录时间轴",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["student_id", "BIGINT UNSIGNED", "FK → students.id (CASCADE)", "idx_student_id", "NOT NULL"],
      ["record_date", "DATE", "", "idx_record_date", "NOT NULL"],
      ["title", "VARCHAR(255)", "", "", "NOT NULL"],
      ["description", "TEXT", "", "", "NULL"],
      ["is_done", "TINYINT(1)", "", "", "DEFAULT 0"],
      ["is_active", "TINYINT(1)", "", "", "DEFAULT 0（当前进行中的事件）"],
      ["stats", "JSON", "", "", "NULL（统计数据快照）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "keyword_hotspots",
    func: "教学热点关键词",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["name", "VARCHAR(64)", "", "idx_name", "NOT NULL"],
      ["weight", "INT UNSIGNED", "", "idx_weight DESC", "NOT NULL（热度权重 0-100）"],
      ["semester", "VARCHAR(32)", "", "idx_semester", "NOT NULL"],
      ["category", "VARCHAR(32)", "", "", "DEFAULT 'teaching'（teaching/research/reform）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "teaching_quality_index",
    func: "教学质量综合指数",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["semester", "VARCHAR(32)", "", "UNIQUE idx_semester", "NOT NULL"],
      ["quality_index", "DECIMAL(5,2)", "", "", "NOT NULL（综合质量指数）"],
      ["student_satisfaction", "DECIMAL(5,2)", "", "", "NULL（学生满意度%）"],
      ["course_qualification_rate", "DECIMAL(5,2)", "", "", "NULL（课程达标率%）"],
      ["supervisor_score", "DECIMAL(5,2)", "", "", "NULL（督导综合评分）"],
      ["course_opening_count", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["active_teacher_count", "INT UNSIGNED", "", "", "DEFAULT 0"],
      ["avg_teaching_hours", "DECIMAL(5,1)", "", "", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["updated_at", "DATETIME", "", "", "ON UPDATE CURRENT_TIMESTAMP"],
    ],
  },
  {
    name: "activity_heatmap_data",
    func: "学生活跃度热力图数据",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["record_date", "DATE", "", "idx_record_date", "NOT NULL"],
      ["hour_index", "TINYINT UNSIGNED", "", "", "NOT NULL（0-14，代表 8:00-22:00）"],
      ["day_index", "TINYINT UNSIGNED", "", "", "NOT NULL（0-13，代表最近14天）"],
      ["activity_count", "INT UNSIGNED", "", "", "DEFAULT 0（活跃人次）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["", "", "", "UNIQUE (record_date, hour_index, day_index)", ""],
    ],
  },
  {
    name: "course_hot_scores",
    func: "课程热度排行（每学期）",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["course_offering_id", "BIGINT UNSIGNED", "FK → course_offerings.id (CASCADE)", "idx_offering_id", "NOT NULL"],
      ["semester", "VARCHAR(32)", "", "idx_semester", "NOT NULL"],
      ["hot_score", "DECIMAL(5,1)", "", "idx_hot_score DESC", "NOT NULL（热度评分）"],
      ["ranking", "INT UNSIGNED", "", "", "NULL（排名）"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
      ["", "", "", "UNIQUE (course_offering_id, semester)", ""],
    ],
  },
  {
    name: "timeline_events",
    func: "通用时间轴事件（课程/考试/成长）",
    fields: [
      ["id", "BIGINT UNSIGNED", "✅ PK", "", "AUTO_INCREMENT"],
      ["event_type", "ENUM('course','exam','student')", "", "idx_event_type", "NOT NULL"],
      ["ref_id", "BIGINT UNSIGNED", "", "idx_ref_id", "NOT NULL（关联对应表的ID）"],
      ["title", "VARCHAR(255)", "", "", "NOT NULL"],
      ["description", "TEXT", "", "", "NULL"],
      ["event_date", "DATE", "", "idx_event_date", "NOT NULL"],
      ["is_done", "TINYINT(1)", "", "", "DEFAULT 0"],
      ["is_active", "TINYINT(1)", "", "", "DEFAULT 0"],
      ["meta_data", "JSON", "", "", "NULL"],
      ["tags", "JSON", "", "", "NULL"],
      ["created_at", "DATETIME", "", "", "DEFAULT CURRENT_TIMESTAMP"],
    ],
  },
];

// ==================== 学院需提供数据 ====================
const collegeData = {
  "课程管理": [
    "课程库基本信息（名称、代码、学分、学时、简介） — 学院教务办提供现有课程清单 Excel/数据库",
    "课程分类体系（必修/选修/通识 / 分类树） — 学院培养方案文件",
    "每学期实际开课列表（哪门课由哪位教师上） — 每学期排课表",
    "课程上课时间、地点、校区 — 教务处排课系统导出",
    "课程变更记录（调课/停课等） — 教务处调课审批记录",
    "教学计划及里程碑节点 — 学院教学大纲",
  ],
  "教师管理": [
    "全院教师名单（姓名、职称、所属教研室、研究方向） — 学院人事信息表",
    "教师出生年月、性别 — 人事档案",
    "教师联系方式（邮箱、电话） — 学院通讯录",
    "教师科研成果（论文、课题、项目、经费） — 学院科研系统 / 年度科研成果统计表",
    "每月/每学期优秀教师评选结果 — 学院评优记录",
  ],
  "学生管理": [
    "在校学生名册（学号、姓名、性别、年级、专业、班级、生源地） — 学籍管理系统导出",
    "学位层次（本科/硕士/博士） — 学籍系统",
    "国际生标识、党员标识 — 学院学工办",
    "学生联系方式（脱敏手机号） — 学籍系统（脱敏后提供）",
    "图书馆刷卡记录（进馆/离馆时间） — 图书馆系统接口 / 导出",
  ],
  "考试管理": [
    "每学期考试安排（课程、时间、地点、类型） — 教务处考试安排表",
    "考场/教室信息（名称、位置、容量） — 教务处教室资源表",
    "监考教师安排（主监/副监/巡考） — 学院教务办排定",
    "缺考学生名单及原因 — 考务记录",
  ],
  "成绩管理": [
    "每门课程每位学生的期末成绩 — 成绩录入系统 / 教师提交",
    "成绩等级划分标准（优/良/中/及格/不及格分数线） — 学院教学管理规定",
    "GPA 计算公式及绩点对照表 — 学院教学管理规定",
    "挂科学生详细信息 — 成绩系统导出",
  ],
  "教学分析": [
    "每学期每门课程的教学评价（6维度评分） — 评教系统导出",
    "教学热点关键词及权重 — 学院教学改革文件 / 专家评审",
    "督导听课评分 — 教学督导记录",
    "课程覆盖率数据 — 培养方案对比",
    "AI 分析建议 — 系统自动生成 / 教学院长审核",
  ],
  "通知公告": [
    "通知公告标题、内容、类型、发布时间 — 学院网站 / OA系统",
    "发布人信息 — 学院办公室",
  ],
  "权限管理": [
    "用户账号、初始密码 — 系统管理员创建",
    "角色分配（管理员/教师/学生） — 学院人事/学籍系统对应",
    "教师-用户绑定 — 按工号对应",
    "学生-用户绑定 — 按学号对应",
  ],
};

// ==================== 辅助函数 ====================

// 轻灰底色
const headerShading = {
  type: ShadingType.SOLID,
  color: "D9D9D9",
  fill: "D9D9D9",
};

const thinBorder = {
  top: { style: BorderStyle.SINGLE, size: 1, color: "999999" },
  bottom: { style: BorderStyle.SINGLE, size: 1, color: "999999" },
  left: { style: BorderStyle.SINGLE, size: 1, color: "999999" },
  right: { style: BorderStyle.SINGLE, size: 1, color: "999999" },
};

function headerCell(text, widthPct) {
  return new TableCell({
    width: { size: widthPct, type: WidthType.PERCENTAGE },
    shading: headerShading,
    borders: thinBorder,
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 40, after: 40 },
        children: [new TextRun({ text, bold: true, size: 20, font: "微软雅黑" })],
      }),
    ],
  });
}

function bodyCell(text, widthPct, opts = {}) {
  const runs = [];
  if (typeof text === "string" && text) {
    const parts = text.split(/(✅|NULL|NOT NULL|DEFAULT|CURRENT_TIMESTAMP|AUTO_INCREMENT|CASCADE|SET NULL|UNIQUE|ENUM|VARCHAR|INT|BIGINT|DECIMAL|TINYINT|DATE|DATETIME|JSON|TEXT|TIME|YEAR|FK →|idx_)/);
    for (const part of parts) {
      if (!part) continue;
      if (/^(✅|FK →|UNIQUE)/.test(part)) {
        runs.push(new TextRun({ text: part, size: 18, font: "微软雅黑", color: "1a7a1a" }));
      } else if (/^(NULL|NOT NULL|DEFAULT|CURRENT_TIMESTAMP|AUTO_INCREMENT|CASCADE|SET NULL)/.test(part)) {
        runs.push(new TextRun({ text: part, size: 18, font: "微软雅黑", color: "c0392b" }));
      } else if (/^(VARCHAR|INT|BIGINT|DECIMAL|TINYINT|DATE|DATETIME|JSON|TEXT|TIME|YEAR|ENUM)/.test(part)) {
        runs.push(new TextRun({ text: part, size: 18, font: "Consolas", color: "2c3e50" }));
      } else if (/^idx_/.test(part)) {
        runs.push(new TextRun({ text: part, size: 18, font: "Consolas", color: "8e44ad" }));
      } else {
        runs.push(new TextRun({ text: part, size: 18, font: "微软雅黑" }));
      }
    }
  } else {
    runs.push(new TextRun({ text: text || "", size: 18, font: "微软雅黑" }));
  }
  return new TableCell({
    width: { size: widthPct, type: WidthType.PERCENTAGE },
    borders: thinBorder,
    children: [
      new Paragraph({
        spacing: { before: 20, after: 20 },
        children: runs,
      }),
    ],
  });
}

function createDbTable(td) {
  const headerCols = ["字段", "类型", "主键", "外键", "索引", "约束"];
  const pcts = [16, 24, 8, 22, 16, 14];

  // Title row spanning all columns
  const titleRow = new TableRow({
    children: [
      new TableCell({
        width: { size: 100, type: WidthType.PERCENTAGE },
        columnSpan: 6,
        shading: { type: ShadingType.SOLID, color: "2c3e50", fill: "2c3e50" },
        borders: thinBorder,
        children: [
          new Paragraph({
            alignment: AlignmentType.LEFT,
            spacing: { before: 60, after: 60 },
            children: [
              new TextRun({ text: `表: `, bold: true, size: 22, font: "微软雅黑", color: "FFFFFF" }),
              new TextRun({ text: td.name, bold: true, size: 22, font: "Consolas", color: "F39C12" }),
              new TextRun({ text: `  — ${td.func}`, bold: false, size: 20, font: "微软雅黑", color: "BDC3C7" }),
            ],
          }),
        ],
      }),
    ],
  });

  // Header row
  const headerRow = new TableRow({
    tableHeader: true,
    children: headerCols.map((h, i) => headerCell(h, pcts[i])),
  });

  // Data rows
  const dataRows = td.fields.map((f) => {
    // f = [field, type, pk, fk, index, constraint]
    const vals = [f[0] || "", f[1] || "", f[2] || "", f[3] || "", f[4] || "", f[5] || ""];
    return new TableRow({
      children: vals.map((v, i) => bodyCell(v, pcts[i])),
    });
  });

  const rows = [titleRow, headerRow, ...dataRows];
  if (td.note) {
    rows.push(
      new TableRow({
        children: [
          new TableCell({
            width: { size: 100, type: WidthType.PERCENTAGE },
            columnSpan: 6,
            borders: thinBorder,
            children: [
              new Paragraph({
                spacing: { before: 40, after: 40 },
                children: [new TextRun({ text: `📝 ${td.note}`, size: 18, font: "微软雅黑", italics: true, color: "7f8c8d" })],
              }),
            ],
          }),
        ],
      })
    );
  }

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    rows,
  });
}

// ==================== 主文档构建 ====================
const children = [];

// 标题
children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({ text: "教学系统数据库设计文档", bold: true, size: 44, font: "微软雅黑", color: "1a1a2e" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
    children: [
      new TextRun({ text: "teaching_system", size: 28, font: "Consolas", color: "7f8c8d" }),
      new TextRun({ text: "    2021—2026    山东大学政治学与公共管理学院", size: 22, font: "微软雅黑", color: "95a5a6" }),
    ],
  })
);

// ===== 一、数据库总体设计 =====
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 300, after: 200 },
    children: [new TextRun({ text: "一、数据库总体设计", bold: true, size: 36, font: "微软雅黑", color: "2c3e50" })],
  })
);

const dbInfo = [
  ["数据库名称", "teaching_system"],
  ["字符集", "utf8mb4"],
  ["排序规则", "utf8mb4_unicode_ci"],
  ["引擎", "InnoDB"],
  ["时区", "系统时区（北京时间 UTC+8）"],
];

children.push(
  new Table({
    width: { size: 70, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    rows: dbInfo.map(
      ([k, v]) =>
        new TableRow({
          children: [
            new TableCell({
              width: { size: 30, type: WidthType.PERCENTAGE },
              shading: headerShading,
              borders: thinBorder,
              children: [new Paragraph({ spacing: { before: 40, after: 40 }, children: [new TextRun({ text: k, bold: true, size: 20, font: "微软雅黑" })] })],
            }),
            new TableCell({
              width: { size: 70, type: WidthType.PERCENTAGE },
              borders: thinBorder,
              children: [new Paragraph({ spacing: { before: 40, after: 40 }, children: [new TextRun({ text: v, size: 20, font: "微软雅黑" })] })],
            }),
          ],
        })
    ),
  })
);

children.push(
  new Paragraph({
    spacing: { before: 200, after: 100 },
    children: [new TextRun({ text: "设计原则：", bold: true, size: 22, font: "微软雅黑", color: "2c3e50" })],
  })
);

const principles = [
  "所有表包含 created_at、updated_at 两个审计时间戳",
  "软删除使用 deleted_at (DATETIME NULL)",
  "所有主键使用 BIGINT UNSIGNED AUTO_INCREMENT",
  "金额类字段使用 DECIMAL(12,2)，分数/比率/百分比使用 DECIMAL(5,2)",
  "JSON 类型字段仅用于前端需要的动态数组数据",
  "数据覆盖时间范围统一：2021-2026",
];

principles.forEach((p) => {
  children.push(
    new Paragraph({
      spacing: { before: 40, after: 40 },
      numbering: { reference: "principles", level: 0 },
      children: [new TextRun({ text: p, size: 20, font: "微软雅黑" })],
    })
  );
});

// ===== 二、所有数据表 =====
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text: "二、所有数据表", bold: true, size: 36, font: "微软雅黑", color: "2c3e50" })],
  })
);

// 每个表
tables.forEach((td) => {
  children.push(
    new Paragraph({
      spacing: { before: 200, after: 100 },
      children: [new TextRun({ text: `表: ${td.name}`, bold: true, size: 26, font: "微软雅黑", color: "2c3e50" })],
    }),
    new Paragraph({
      spacing: { before: 0, after: 100 },
      children: [new TextRun({ text: `功能: ${td.func}`, size: 20, font: "微软雅黑", color: "7f8c8d" })],
    })
  );
  children.push(createDbTable(td));
});

// ===== 三、表关系图 =====
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text: "三、表关系图（Mermaid ER 图）", bold: true, size: 36, font: "微软雅黑", color: "2c3e50" })],
  })
);

const erDiagram = `erDiagram
    users ||--o| teachers : "teacher_id"
    users ||--o| students : "student_id"
    
    colleges ||--o{ teachers : "college_id"
    colleges ||--o{ majors : "college_id"
    colleges ||--o{ students : "college_id"
    colleges ||--o{ courses : "college_id"
    colleges ||--o{ teaching_plans : "college_id"
    colleges ||--o{ classes : "college_id"

    majors ||--o{ students : "major_id"
    majors ||--o{ classes : "major_id"

    teachers ||--o{ course_offerings : "teacher_id"
    teachers ||--o{ exam_invigilators : "teacher_id"
    teachers ||--o{ research_outputs : "teacher_id"
    teachers ||--o{ teacher_teams : "leader_id"

    students ||--o{ course_enrollments : "student_id"
    students ||--o{ grades : "student_id"
    students ||--o{ teaching_evaluations : "student_id"
    students ||--o{ exam_absence : "student_id"
    students ||--o{ library_records : "student_id"
    students ||--o{ scholarships : "student_id"
    students ||--o{ student_growth_records : "student_id"

    course_categories ||--o{ courses : "category_id"
    courses ||--o{ course_offerings : "course_id"

    course_offerings ||--o{ course_enrollments : "course_offering_id"
    course_offerings ||--o{ course_schedules : "course_offering_id"
    course_offerings ||--o{ course_changes : "course_offering_id"
    course_offerings ||--o{ grades : "course_offering_id"
    course_offerings ||--o{ teaching_evaluations : "course_offering_id"
    course_offerings ||--o{ exams : "course_offering_id"
    course_offerings ||--o{ course_hot_scores : "course_offering_id"

    exams ||--o{ exam_invigilators : "exam_id"
    exams ||--o{ exam_absence : "exam_id"

    exam_venues ||--o{ exams : "venue_id"

    employment_stats {
        BIGINT id PK
        YEAR year UK
    }

    notices {
        BIGINT id PK
        BIGINT publisher_id FK
    }

    alerts {
        BIGINT id PK
    }

    operation_logs {
        BIGINT id PK
        BIGINT user_id FK
    }

    teaching_quality_index {
        BIGINT id PK
        VARCHAR semester UK
    }

    keyword_hotspots {
        BIGINT id PK
    }

    student_activities {
        BIGINT id PK
    }

    classes {
        BIGINT id PK
        BIGINT college_id FK
        BIGINT major_id FK
    }

    activity_heatmap_data {
        BIGINT id PK
    }

    timeline_events {
        BIGINT id PK
    }`;

children.push(
  new Paragraph({
    spacing: { before: 100, after: 100 },
    children: [new TextRun({ text: "以下为 Mermaid ER 图代码，可在支持 Mermaid 的编辑器（如 VS Code + Markdown Preview Mermaid Support）中渲染：", size: 20, font: "微软雅黑", color: "7f8c8d" })],
  }),
  new Paragraph({
    spacing: { before: 100, after: 100 },
    shading: { type: ShadingType.SOLID, color: "F5F5F5", fill: "F5F5F5" },
    border: { top: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" }, bottom: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" }, left: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" }, right: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" } },
    children: [new TextRun({ text: erDiagram, size: 16, font: "Consolas", color: "2c3e50" })],
  })
);

// ===== 四、哪些数据需要学院提供 =====
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text: "四、哪些数据需要学院提供", bold: true, size: 36, font: "微软雅黑", color: "2c3e50" })],
  })
);

for (const [moduleName, items] of Object.entries(collegeData)) {
  children.push(
    new Paragraph({
      heading: HeadingLevel.HEADING_2,
      spacing: { before: 200, after: 100 },
      children: [new TextRun({ text: moduleName, bold: true, size: 28, font: "微软雅黑", color: "2c3e50" })],
    })
  );

  // Table: 数据项 | 提供方式
  const headerRow2 = new TableRow({
    tableHeader: true,
    children: [
      headerCell("数据项", 50),
      headerCell("提供方式", 50),
    ],
  });

  const dataRows2 = items.map((item) => {
    const [dataItem, provider] = item.split(" — ");
    return new TableRow({
      children: [
        bodyCell(dataItem.trim(), 50),
        bodyCell(provider ? provider.trim() : "", 50),
      ],
    });
  });

  children.push(
    new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      layout: TableLayoutType.FIXED,
      rows: [headerRow2, ...dataRows2],
    })
  );
}

// ===== 补充说明 =====
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [new TextRun({ text: "补充说明", bold: true, size: 36, font: "微软雅黑", color: "2c3e50" })],
  }),
  new Paragraph({
    spacing: { before: 60, after: 60 },
    numbering: { reference: "notes", level: 0 },
    children: [
      new TextRun({ text: "所有学年/学期数据统一使用 ", size: 20, font: "微软雅黑" }),
      new TextRun({ text: "semester", size: 20, font: "Consolas", bold: true }),
      new TextRun({ text: " 字段，格式为 ", size: 20, font: "微软雅黑" }),
      new TextRun({ text: '"2021-2022-1"', size: 20, font: "Consolas", bold: true }),
      new TextRun({ text: "（2021-2022学年第一学期）或 ", size: 20, font: "微软雅黑" }),
      new TextRun({ text: '"2021-2022-2"', size: 20, font: "Consolas", bold: true }),
      new TextRun({ text: "，年份数据使用 ", size: 20, font: "微软雅黑" }),
      new TextRun({ text: "YEAR", size: 20, font: "Consolas", bold: true }),
      new TextRun({ text: " 类型（2021-2026），与前端 currentSemester/currentPeriod 的值保持一致。", size: 20, font: "微软雅黑" }),
    ],
  }),
  new Paragraph({
    spacing: { before: 60, after: 60 },
    numbering: { reference: "notes", level: 0 },
    children: [
      new TextRun({ text: "JSON 字段使用说明：", size: 20, font: "微软雅黑", bold: true }),
      new TextRun({ text: "仅用于前端需要动态数组/对象的场景（如 employment_stats.career_distribution 就业去向分布、scholarships.honor_tags 荣誉标签列表），不做复杂嵌套查询，复杂查询走关联表。", size: 20, font: "微软雅黑" }),
    ],
  }),
  new Paragraph({
    spacing: { before: 60, after: 60 },
    numbering: { reference: "notes", level: 0 },
    children: [
      new TextRun({ text: "前端图表接口：", size: 20, font: "微软雅黑", bold: true }),
      new TextRun({ text: "后端通过聚合查询直接从各表生成所需格式返回，例如 Dashboard 饼图数据 = SELECT c.name, COUNT(co.id) FROM courses JOIN colleges c ... GROUP BY c.name。", size: 20, font: "微软雅黑" }),
    ],
  }),
  new Paragraph({
    spacing: { before: 60, after: 60 },
    numbering: { reference: "notes", level: 0 },
    children: [
      new TextRun({ text: "数据初始化顺序：", size: 20, font: "微软雅黑", bold: true }),
      new TextRun({ text: "colleges → majors → courses / course_categories → teachers → students → users（绑定关系）→ 各学期业务数据。", size: 20, font: "微软雅黑" }),
    ],
  })
);

// ==================== 创建文档 ====================
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "微软雅黑", size: 20 },
      },
    },
  },
  numbering: {
    config: [
      {
        reference: "principles",
        levels: [
          { level: 0, format: "bullet", text: "●", alignment: AlignmentType.LEFT },
        ],
      },
      {
        reference: "notes",
        levels: [
          { level: 0, format: "decimal", text: "%1.", alignment: AlignmentType.LEFT },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          margin: { top: 1440, right: 1000, bottom: 1440, left: 1000 },
        },
      },
      children,
    },
  ],
});

// ==================== 输出 ====================
Packer.toBuffer(doc).then((buffer) => {
  const outPath = "d:/Personal/Desktop/教学系统/教学系统数据库设计文档.docx";
  fs.writeFileSync(outPath, buffer);
  console.log("✅ Word 文档已生成: " + outPath);
});