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

// ==================== 辅助函数 ====================
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

function titleCell(text, widthPct, opts = {}) {
  return new TableCell({
    width: { size: widthPct, type: WidthType.PERCENTAGE },
    shading: { type: ShadingType.SOLID, color: "2c3e50", fill: "2c3e50" },
    borders: thinBorder,
    children: [
      new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { before: 80, after: 80 },
        children: [
          new TextRun({
            text,
            bold: true,
            size: 20,
            font: "微软雅黑",
            color: "FFFFFF",
            ...opts,
          }),
        ],
      }),
    ],
  });
}

function headerCell(text, widthPct) {
  return new TableCell({
    width: { size: widthPct, type: WidthType.PERCENTAGE },
    shading: headerShading,
    borders: thinBorder,
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 40, after: 40 },
        children: [new TextRun({ text, bold: true, size: 18, font: "微软雅黑" })],
      }),
    ],
  });
}

function bodyCell(text, widthPct, opts = {}) {
  const runs = [];
  if (typeof text === "string" && text) {
    // colorize special markers
    const parts = text.split(/(←|→|✅|`[^`]+`)/g);
    for (const part of parts) {
      if (!part) continue;
      if (part.startsWith("`") && part.endsWith("`")) {
        runs.push(new TextRun({ text: part.slice(1, -1), size: 18, font: "Consolas", color: "c0392b" }));
      } else if (part === "←" || part === "→") {
        runs.push(new TextRun({ text: part, size: 18, font: "微软雅黑", color: "8e44ad", bold: true }));
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

// ==================== 内容构建 ====================
const children = [];

// -------------------- 大标题 --------------------
children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [
      new TextRun({
        text: "Django 项目架构设计",
        bold: true,
        size: 44,
        font: "微软雅黑",
        color: "1a1a2e",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
    children: [
      new TextRun({ text: "teaching_system", size: 28, font: "Consolas", color: "7f8c8d" }),
      new TextRun({ text: "    山东大学政治学与公共管理学院", size: 22, font: "微软雅黑", color: "95a5a6" }),
    ],
  })
);

// ==================== 一、项目目录树 ====================
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 300, after: 200 },
    children: [
      new TextRun({
        text: "一、项目目录树",
        bold: true,
        size: 36,
        font: "微软雅黑",
        color: "2c3e50",
      }),
    ],
  })
);

const directoryTree = `teaching_system/
├── manage.py
├── requirements.txt
├── config/                          # Django 项目配置
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py                      # 根 URL 路由
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                            # 业务应用
│   ├── __init__.py
│   │
│   ├── core/                        # ① 组织机构基础数据
│   │   ├── __init__.py
│   │   ├── models.py                # College, Major, Class
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── users/                       # ② 认证与用户
│   │   ├── __init__.py
│   │   ├── models.py                # User
│   │   ├── serializers.py
│   │   ├── views.py                 # 登录/登出/当前用户信息
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── auth.py                  # JWT 认证配置
│   │
│   ├── teachers/                    # ③ 教师管理
│   │   ├── __init__.py
│   │   ├── models.py                # Teacher, ResearchOutput, TeacherTeam
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── students/                    # ④ 学生管理
│   │   ├── __init__.py
│   │   ├── models.py                # Student, StudentGrowthRecord,
│   │   │                            #   StudentActivity, LibraryRecord, Scholarship
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── courses/                     # ⑤ 课程管理（8张表 — 核心枢纽）
│   │   ├── __init__.py
│   │   ├── models.py                # Course, CourseCategory, CourseOffering,
│   │   │                            #   CourseEnrollment, CourseSchedule,
│   │   │                            #   CourseChange, TeachingPlan,
│   │   │                            #   TeachingEvaluation
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── grades/                      # ⑥ 成绩管理
│   │   ├── __init__.py
│   │   ├── models.py                # Grade
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── exams/                       # ⑦ 考试管理
│   │   ├── __init__.py
│   │   ├── models.py                # Exam, ExamVenue, ExamInvigilator, ExamAbsence
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   ├── analysis/                    # ⑧ 教学分析 + 数据总览
│   │   ├── __init__.py
│   │   ├── models.py                # TeachingQualityIndex, KeywordHotspot,
│   │   │                            #   EmploymentStats, CourseHotScore,
│   │   │                            #   ActivityHeatmapData, TimelineEvent,
│   │   │                            #   OperationLog
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   │
│   └── notifications/              # ⑨ 通知预警
│       ├── __init__.py
│       ├── models.py                # Notice, Alert
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       └── admin.py
│
├── utils/                           # 公共工具
│   ├── __init__.py
│   ├── permissions.py               # 角色权限控制
│   ├── pagination.py                # 统一分页
│   ├── response.py                  # 统一响应格式
│   └── mixins.py                    # 公共 ViewSet Mixin（软删除等）
│
└── media/                           # 上传文件（头像等）`;

children.push(
  new Paragraph({
    spacing: { before: 100, after: 100 },
    shading: { type: ShadingType.SOLID, color: "F5F5F5", fill: "F5F5F5" },
    border: {
      top: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
      bottom: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
      left: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
      right: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
    },
    children: [new TextRun({ text: directoryTree, size: 16, font: "Consolas", color: "2c3e50" })],
  })
);

// ==================== 二、9 个 Django App 及对应数据表 ====================
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [
      new TextRun({
        text: "二、9 个 Django App 及对应数据表",
        bold: true,
        size: 36,
        font: "微软雅黑",
        color: "2c3e50",
      }),
    ],
  })
);

const appTables = [
  ["①", "core", "无独立页面\n（被所有页面引用）", "colleges  majors  classes", "学院/教研室/专业/班级基础数据，下拉选项数据源"],
  ["②", "users", "/login\n+ 顶栏用户区", "users", "登录认证、JWT 令牌、当前用户信息、角色绑定"],
  ["③", "teachers", "/teacher", "teachers  research_outputs  teacher_teams", "教师 CRUD、科研成果管理、教学团队管理"],
  ["④", "students", "/student", "students  student_growth_records  student_activities\nlibrary_records  scholarships", "学生 CRUD、成长记录时间轴、活动记录、图书馆、奖学金"],
  ["⑤", "courses", "/course", "courses  course_categories  course_offerings\ncourse_enrollments  course_schedules  course_changes\nteaching_plans  teaching_evaluations", "课程库管理、每学期开课、选课、排课、调课记录、\n教学计划、6 维度评教"],
  ["⑥", "grades", "/grade", "grades", "成绩录入/提交/审核、绩点计算、挂科统计"],
  ["⑦", "exams", "/exam", "exams  exam_venues  exam_invigilators\nexam_absence", "考试安排、考场管理、监考分配、缺考记录"],
  ["⑧", "analysis", "/analysis\n+ /dashboard", "teaching_quality_index  keyword_hotspots\nemployment_stats  course_hot_scores\nactivity_heatmap_data  timeline_events\noperation_logs", "教学质量综合指数、热点关键词、就业统计、\n课程热度排行、热力图、时间轴事件、操作日志"],
  ["⑨", "notifications", "顶栏通知图标", "notices  alerts", "通知公告 CRUD、教学异常预警管理"],
];

// Create the big table
const headerCols = ["序号", "App", "对应前端路由", "包含数据表", "职责"];
const pcts = [6, 14, 16, 36, 28];

const titleRow = new TableRow({
  children: [
    new TableCell({
      width: { size: 100, type: WidthType.PERCENTAGE },
      columnSpan: 5,
      shading: { type: ShadingType.SOLID, color: "2c3e50", fill: "2c3e50" },
      borders: thinBorder,
      children: [
        new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { before: 60, after: 60 },
          children: [
            new TextRun({
              text: "9 个 Django App 及对应数据表",
              bold: true,
              size: 22,
              font: "微软雅黑",
              color: "FFFFFF",
            }),
          ],
        }),
      ],
    }),
  ],
});

const headerRow = new TableRow({
  tableHeader: true,
  children: headerCols.map((h, i) => headerCell(h, pcts[i])),
});

const dataRows = appTables.map((row) => {
  return new TableRow({
    children: row.map((val, i) => bodyCell(val, pcts[i])),
  });
});

children.push(
  new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    rows: [titleRow, headerRow, ...dataRows],
  })
);

// ==================== 三、App 之间的依赖关系 ====================
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [
      new TextRun({
        text: "三、App 之间的依赖关系",
        bold: true,
        size: 36,
        font: "微软雅黑",
        color: "2c3e50",
      }),
    ],
  })
);

// ASCII dependency diagram
const asciiDiagram = `                    ┌──────────┐
                    │   core   │  ← 零依赖（最底层基础数据）
                    │ (1)      │
                    └────┬─────┘
                         │  colleges / majors / classes
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────┴─────┐  ┌────┴─────┐  ┌────┴─────┐
     │ teachers │  │ students │  │ courses  │
     │ (3)      │  │ (4)      │  │ (5)      │
     └────┬─────┘  └────┬─────┘  └────┬─────┘
          │              │              │
          │         ┌────┴─────┐        │
          │         │  grades  │ ←──────┤  grades 依赖 courses + students
          │         │ (6)      │        │
          │         └──────────┘        │
          │                             │
          │         ┌──────────┐        │
          │         │  exams   │ ←──────┤  exams 依赖 courses + teachers
          │         │ (7)      │        │
          │         └──────────┘        │
          │              │              │
          └──────────────┼──────────────┘
                         │
                   ┌─────┴──────┐
                   │  analysis  │  ← 依赖 core + courses + teachers + students
                   │ (8)        │
                   └────────────┘

     ┌──────────┐                    ┌───────────────┐
     │  users   │ ← 依赖 teachers +  │ notifications │ ← 依赖 users
     │ (2)      │    students + core │ (9)           │
     └──────────┘                    └───────────────┘`;

children.push(
  new Paragraph({
    spacing: { before: 100, after: 100 },
    shading: { type: ShadingType.SOLID, color: "F5F5F5", fill: "F5F5F5" },
    border: {
      top: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
      bottom: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
      left: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
      right: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
    },
    children: [new TextRun({ text: asciiDiagram, size: 14, font: "Consolas", color: "2c3e50" })],
  })
);

// Dependency detail table
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 100 },
    children: [
      new TextRun({
        text: "依赖明细",
        bold: true,
        size: 28,
        font: "微软雅黑",
        color: "2c3e50",
      }),
    ],
  })
);

const deps = [
  ["users → core", "colleges", "users.teacher_id / users.student_id 需关联存在"],
  ["users → teachers", "teachers.id", "role=teacher 时绑定教师记录"],
  ["users → students", "students.id", "role=student 时绑定学生记录"],
  ["teachers → core", "colleges", "teachers.college_id 外键"],
  ["students → core", "colleges, majors, classes", "students 的三个外键"],
  ["courses → core", "colleges", "courses.college_id 外键"],
  ["courses → teachers", "teachers.id", "course_offerings.teacher_id 外键"],
  ["courses → students", "students.id", "course_enrollments.student_id / teaching_evaluations.student_id"],
  ["grades → core", "—", "仅通过 student 间接依赖"],
  ["grades → courses", "course_offerings.id", "grades.course_offering_id 外键"],
  ["grades → students", "students.id", "grades.student_id 外键"],
  ["exams → core", "—", "仅间接依赖"],
  ["exams → courses", "course_offerings.id", "exams.course_offering_id 外键"],
  ["exams → teachers", "teachers.id", "exam_invigilators.teacher_id 外键"],
  ["analysis → core", "colleges, majors, classes", "各维度的统计分析关联"],
  ["analysis → courses", "course_offerings", "teaching_quality_index / course_hot_scores"],
  ["analysis → teachers", "teachers.id", "科研成果 / 团队分析"],
  ["analysis → students", "students.id", "学生活跃度热力图 / 就业统计"],
  ["notifications → users", "users.id", "notices.publisher_id 外键"],
];

const depHeaderCols = ["依赖方", "被依赖方", "依赖原因"];
const depPcts = [20, 30, 50];

const depTitleRow = new TableRow({
  children: [
    new TableCell({
      width: { size: 100, type: WidthType.PERCENTAGE },
      columnSpan: 3,
      shading: { type: ShadingType.SOLID, color: "2c3e50", fill: "2c3e50" },
      borders: thinBorder,
      children: [
        new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { before: 60, after: 60 },
          children: [
            new TextRun({
              text: "依赖明细",
              bold: true,
              size: 22,
              font: "微软雅黑",
              color: "FFFFFF",
            }),
          ],
        }),
      ],
    }),
  ],
});

const depHeaderRow = new TableRow({
  tableHeader: true,
  children: depHeaderCols.map((h, i) => headerCell(h, depPcts[i])),
});

const depDataRows = deps.map((row) => {
  return new TableRow({
    children: row.map((val, i) => bodyCell(val, depPcts[i])),
  });
});

children.push(
  new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    rows: [depTitleRow, depHeaderRow, ...depDataRows],
  })
);

// ==================== 四、关键设计说明 ====================
children.push(
  new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [
      new TextRun({
        text: "四、关键设计说明",
        bold: true,
        size: 36,
        font: "微软雅黑",
        color: "2c3e50",
      }),
    ],
  })
);

const notes = [
  {
    point: "1.",
    title: "`courses` App 承担最大业务量",
    detail:
      "（8 张表），因为课程管理是教学系统的核心枢纽，课程库 → 开课 → 选课 → 排课 → 调课 → 评教 → 教学计划形成完整链条，不宜拆分。",
  },
  {
    point: "2.",
    title: "`analysis` App 不做外键约束",
    detail:
      "（仅通过应用层 ID 关联），其所有表为聚合/快照/分析结果数据，通过后端定时任务或手动触发从业务表汇总生成，避免分析查询拖慢业务库。",
  },
  {
    point: "3.",
    title: "`core` App 无依赖",
    detail:
      "，所有基础字典数据（学院/专业/班级）由它提供，其他 App 通过外键引用。数据初始化时必须最先填充。",
  },
  {
    point: "4.",
    title: "`users` App 初始化顺序",
    detail:
      "：先有 teachers / students 记录，再创建对应的 users 绑定记录。",
  },
  {
    point: "5.",
    title: "跨 App API 调用",
    detail:
      "：后端通过 Django ORM 直接跨 App 导入 Model，不做微服务/HTTP 调用，保持单体 Django 应用的简洁性。例如 `grades` 需要查询 `students` 的 GPA 汇总，直接 `from apps.students.models import Student` 即可。",
  },
];

notes.forEach((note) => {
  children.push(
    new Paragraph({
      spacing: { before: 80, after: 80 },
      children: [
        new TextRun({ text: note.point + " ", bold: true, size: 20, font: "微软雅黑", color: "2c3e50" }),
        new TextRun({ text: note.title, bold: true, size: 20, font: "微软雅黑", color: "2c3e50" }),
        new TextRun({ text: note.detail, size: 20, font: "微软雅黑" }),
      ],
    })
  );
});

// ==================== 创建文档 ====================
const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "微软雅黑", size: 20 },
      },
    },
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

Packer.toBuffer(doc).then((buffer) => {
  const outPath = "d:/Personal/Desktop/教学系统/Django项目架构设计文档.docx";
  fs.writeFileSync(outPath, buffer);
  console.log("✅ Word 文档已生成: " + outPath);
});