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

function severityCell(text, widthPct) {
  let color = "333333";
  if (text.includes("致命")) color = "c0392b";
  else if (text.includes("严重")) color = "e67e22";
  else if (text.includes("中等")) color = "f1c40f";
  else if (text.includes("低风险")) color = "27ae60";

  const runs = [];
  if (typeof text === "string" && text) {
    const parts = text.split(/(←|→|✅|`[^`]+`)/g);
    for (const part of parts) {
      if (!part) continue;
      if (part.startsWith("`") && part.endsWith("`")) {
        runs.push(new TextRun({ text: part.slice(1, -1), size: 18, font: "Consolas", color: "c0392b" }));
      } else if (part === "←" || part === "→") {
        runs.push(new TextRun({ text: part, size: 18, font: "微软雅黑", color: "8e44ad", bold: true }));
      } else {
        runs.push(new TextRun({ text: part, size: 18, font: "微软雅黑", color }));
      }
    }
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

function statusCell(text, widthPct) {
  let color = "333333";
  if (text.includes("✅")) color = "27ae60";
  else if (text.includes("⚠")) color = "e67e22";

  return new TableCell({
    width: { size: widthPct, type: WidthType.PERCENTAGE },
    borders: thinBorder,
    children: [
      new Paragraph({
        spacing: { before: 20, after: 20 },
        children: [
          new TextRun({ text: text || "", size: 18, font: "微软雅黑", color }),
        ],
      }),
    ],
  });
}

function makeTable(titleText, colPcts, headerNames, dataRows, opts = {}) {
  const rows = [];

  // Title row (optional)
  if (titleText) {
    rows.push(
      new TableRow({
        children: [
          new TableCell({
            width: { size: 100, type: WidthType.PERCENTAGE },
            columnSpan: headerNames.length,
            shading: { type: ShadingType.SOLID, color: "2c3e50", fill: "2c3e50" },
            borders: thinBorder,
            children: [
              new Paragraph({
                alignment: AlignmentType.LEFT,
                spacing: { before: 60, after: 60 },
                children: [
                  new TextRun({
                    text: titleText,
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
      })
    );
  }

  // Header row
  rows.push(
    new TableRow({
      tableHeader: true,
      children: headerNames.map((h, i) => headerCell(h, colPcts[i])),
    })
  );

  // Data rows
  dataRows.forEach((row) => {
    if (opts.cellFn) {
      rows.push(
        new TableRow({
          children: row.map((val, i) => opts.cellFn(val, colPcts[i])),
        })
      );
    } else {
      rows.push(
        new TableRow({
          children: row.map((val, i) => bodyCell(val, colPcts[i])),
        })
      );
    }
  });

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    rows,
  });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 200 },
    children: [
      new TextRun({
        text,
        bold: true,
        size: 36,
        font: "微软雅黑",
        color: "2c3e50",
      }),
    ],
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 300, after: 150 },
    children: [
      new TextRun({
        text,
        bold: true,
        size: 28,
        font: "微软雅黑",
        color: "2c3e50",
      }),
    ],
  });
}

function normalPara(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [
      new TextRun({
        text,
        size: 22,
        font: "微软雅黑",
        color: "333333",
        ...opts,
      }),
    ],
  });
}

function codeBlock(text) {
  return new Paragraph({
    spacing: { before: 100, after: 100 },
    shading: { type: ShadingType.SOLID, color: "F5F5F5", fill: "F5F5F5" },
    border: {
      top: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
      bottom: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
      left: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
      right: { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" },
    },
    children: [new TextRun({ text, size: 16, font: "Consolas", color: "2c3e50" })],
  });
}

// ==================== 内容构建 ====================
const children = [];

// -------------------- 封面标题 --------------------
children.push(
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [
      new TextRun({
        text: "Django Models 工程审查报告",
        bold: true,
        size: 48,
        font: "微软雅黑",
        color: "1a1a2e",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 100 },
    children: [
      new TextRun({
        text: "教学系统后端模型层审计 · 问题修复 · 架构梳理",
        size: 24,
        font: "微软雅黑",
        color: "7f8c8d",
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 400 },
    children: [
      new TextRun({ text: "审查日期：2026-06-08", size: 20, font: "微软雅黑", color: "95a5a6" }),
    ],
  })
);

// ==================== 一、审查概述 ====================
children.push(heading1("一、审查概述"));

children.push(normalPara("本次审查对教学系统 Django 后端的 apps/ 目录下全部 9 个 Django App 的所有模型文件进行了全面通读和分析。发现 4 个致命/严重问题并已全部修复，同时识别出若干中等/低风险问题供后续迭代参考。"));

// ==================== 二、现有 Model 架构总览 ====================
children.push(heading1("二、现有 Model 架构总览"));

children.push(normalPara("当前 apps/ 目录包含以下 9 个 Django App（colleges 为本次新建）："));

const modelTree = `apps/
├── colleges/          ← 【新建】学院
│   └── College
├── users/             ← 用户 (Django AbstractBaseUser)
│   └── User
├── courses/           ← 课程管理
│   ├── Course
│   ├── CourseCategory
│   ├── CourseOffering
│   ├── CourseHotScore
│   └── CourseEvaluation
├── teachers/          ← 教师管理
│   ├── Teacher
│   └── TeachingTeam
├── students/          ← 学生管理
│   ├── Student
│   └── StudentProfile
├── grades/            ← 成绩管理
│   ├── Grade
│   └── GradeTrend
├── exams/             ← 考试管理
│   └── Exam
├── analysis/          ← 教学分析
│   ├── TeachingKPI
│   ├── TeachingQuality
│   ├── SatisfactionSurvey
│   ├── RiskEvent
│   └── AISuggestion
└── notifications/     ← 通知系统
    ├── Notification
    └── UserNotification`;

children.push(codeBlock(modelTree));

// ==================== 三、实体关系图 (ER) ====================
children.push(heading1("三、实体关系图 (ER)"));

const erDiagram = `College ──┬── Course (归属学院)
          ├── Teacher (所属学院)
          ├── Student (所属学院)
          ├── GradeTrend (学院维度聚合)
          ├── TeachingKPI (学院维度快照)
          ├── TeachingQuality (学院维度趋势)
          ├── SatisfactionSurvey (学院维度调查)
          ├── RiskEvent (关联学院)
          └── AISuggestion (关联学院)

Teacher  ──┬── User (1:1, 登录账户)
           └── TeachingTeam (中间表, 关联 CourseOffering)

Student  ──┬── User (1:1, 登录账户)
           └── Grade (成绩)

Course ──┬── CourseCategory (M:1 分类)
         ├── CourseOffering (开课记录)
         ├── CourseHotScore (热度快照)
         └── CourseEvaluation (教学评价)

CourseOffering ──┬── Teacher + TeachingTeam (多对多)
                 ├── Exam (考试安排)
                 ├── Grade (选课学生成绩)
                 └── RiskEvent (关联预警)

User ──┬── UserNotification (接收通知)
       └── AISuggestion (采纳AI建议)`;

children.push(codeBlock(erDiagram));

// ==================== 四、问题清单 ====================
children.push(heading1("四、问题清单"));

// 致命问题
children.push(heading2("4.1 致命问题 (已修复)"));
children.push(
  makeTable(
    "致命问题清单",
    [8, 30, 42, 20],
    ["编号", "问题描述", "涉及模型", "修复状态"],
    [
      [
        "P0-1",
        "colleges 应用缺失 — apps/colleges/ 目录不存在，College 模型未定义。10 个模型通过 `ForeignKey(\"colleges.College\")` 引用不存在的模型。makemigrations 会直接报错 `LookupError`。",
        "TeachingKPI, TeachingQuality,\nSatisfactionSurvey, RiskEvent,\nAISuggestion, Course,\nTeacher, TeachingTeam,\nStudent, GradeTrend\n（共 10 个模型）",
        "✅ 已修复\n新建 colleges 应用",
      ],
      [
        "P0-2",
        "notifications/models.py 中 TypeChoices 的 ANNOUNCEMENT 和 OTHER 各出现两次，导致 Python 类定义错误 `duplicate key`。",
        "Notification",
        "✅ 已修复\n重写文件，移除重复",
      ],
    ],
    { cellFn: (val, pct) => {
      if (pct === 20) return statusCell(val, pct);
      return bodyCell(val, pct);
    }}
  )
);

// 严重问题
children.push(heading2("4.2 严重问题 (已修复)"));
children.push(
  makeTable(
    "严重问题清单",
    [8, 30, 42, 20],
    ["编号", "问题描述", "涉及模型", "修复状态"],
    [
      [
        "P1-1",
        "RiskEvent.Meta.ordering 使用 Python `@property` `level_order`（非数据库列），查询时抛出 `OperationalError: Unknown column`。",
        "RiskEvent",
        "✅ 已修复\n改为 `[\"-triggered_at\"]`",
      ],
      [
        "P1-2",
        "AISuggestion.Meta.ordering 使用 Python `@property` `priority_order`（非数据库列），同上。",
        "AISuggestion",
        "✅ 已修复\n改为 `[\"-confidence\"]`",
      ],
    ],
    { cellFn: (val, pct) => {
      if (pct === 20) return statusCell(val, pct);
      return bodyCell(val, pct);
    }}
  )
);

// 中等问题
children.push(heading2("4.3 中等问题 (建议关注)"));
children.push(
  makeTable(
    "中等问题清单",
    [8, 30, 42, 20],
    ["编号", "问题描述", "涉及模型", "建议"],
    [
      [
        "P2-1",
        "索引名 `idx_semester` 跨多个表重复 — MySQL 中索引名按表隔离，不影响运行，但跨库迁移或 DBA 工具扫描时可能产生混淆（共 8 张表使用 `idx_semester`）。",
        "CourseHotScore, GradeTrend,\nExam, TeachingKPI,\nTeachingQuality,\nSatisfactionSurvey,\nRiskEvent, AISuggestion",
        "⚠ 不影响运行\n无需修改",
      ],
      [
        "P2-2",
        "User 模型使用 `BigIntegerField` 存储 `teacher_id` / `student_id` 而非 `ForeignKey` — 无数据库级引用完整性。若 Teacher/Student 被删除，User 表中 ID 会成为悬空引用。",
        "User",
        "⚠ 需在序列化器层\n做存在性校验",
      ],
    ],
    { cellFn: (val, pct) => {
      if (pct === 20) return statusCell(val, pct);
      return bodyCell(val, pct);
    }}
  )
);

// 低风险问题
children.push(heading2("4.4 低风险问题 (无需修改)"));
children.push(
  makeTable(
    "低风险问题清单",
    [8, 30, 42, 20],
    ["编号", "问题描述", "涉及模型", "处理方式"],
    [
      [
        "P3-1",
        "`unique_together` 在 Django 5 中已标记为待弃用 — 建议迁移到 `UniqueConstraint`（后续迭代）。",
        "TeachingKPI, TeachingQuality,\nSatisfactionSurvey,\nCourseOffering,\nCourseCategory",
        "✅ 不影响功能\n建议后续迭代",
      ],
      [
        "P3-2",
        "多个 `unique_together` 包含可空 FK 字段 — MySQL 允许键中包含 NULL 且多个 NULL 被视为不相等。可能导致多条 `(semester=X, college=NULL)` 记录并存。",
        "TeachingKPI, TeachingQuality,\nSatisfactionSurvey,\nCourseOffering,\nCourseCategory",
        "✅ 预期行为\n如不需多 NULL 记录\n可加 `UniqueConstraint`\n配合 `condition`",
      ],
      [
        "P3-3",
        "Teacher 和 Student 的 `user` 字段使用 `on_delete=SET_NULL` — 若 User 被删除，教师/学生记录失去登录关联但数据保留。",
        "Teacher, Student",
        "✅ 合理设计\n需确认业务逻辑\n支持 user=None",
      ],
    ],
    { cellFn: (val, pct) => {
      if (pct === 20) return statusCell(val, pct);
      return bodyCell(val, pct);
    }}
  )
);

// ==================== 五、修复操作记录 ====================
children.push(heading1("五、修复操作记录"));

children.push(
  makeTable(
    "修复操作记录",
    [25, 15, 60],
    ["文件", "操作类型", "说明"],
    [
      [
        "apps/colleges/__init__.py",
        "新建",
        "创建 colleges 应用包的空 `__init__.py` 文件",
      ],
      [
        "apps/colleges/models.py",
        "新建",
        "包含 College 模型，字段：`code`（学院代码）、`name`（学院名称）、`short_name`（简称）、`sort_order`（排序权重）、`logo_url`（Logo 链接）、`is_active`（是否启用）、`created_at`、`updated_at`",
      ],
      [
        "apps/notifications/models.py",
        "重写",
        "移除 Notification.TypeChoices 中重复的 `ANNOUNCEMENT` 和 `OTHER` 定义，消除 Python 类定义错误 `duplicate key`",
      ],
      [
        "apps/analysis/models.py",
        "修改",
        "RiskEvent.Meta.ordering: `[\"-level_order\", \"-triggered_at\"]` → `[\"-triggered_at\"]`\nAISuggestion.Meta.ordering: `[\"-priority_order\", \"-confidence\"]` → `[\"-confidence\"]`\n\n原因：`level_order` 和 `priority_order` 是 Python `@property`，非数据库列，在 SQL 层面无法使用",
      ],
    ],
  )
);

// ==================== 六、各 App 模型字段总览 ====================
children.push(heading1("六、各 App 模型字段总览"));

// --- colleges ---
children.push(heading2("6.1 colleges — College (新建)"));
children.push(
  makeTable(
    "College 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["code", "CharField(32)", "是", "是", "学院代码，如 CS / MATH"],
      ["name", "CharField(128)", "是", "是", "学院名称，如 计算机科学与技术学院"],
      ["short_name", "CharField(64)", "否", "否", "简称，如 计科院"],
      ["sort_order", "IntegerField", "否", "否", "排序权重，数值越小越靠前"],
      ["logo_url", "URLField(512)", "否", "否", "Logo 图片链接"],
      ["is_active", "BooleanField", "否", "否", "是否启用，默认 True"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

// --- users ---
children.push(heading2("6.2 users — User"));
children.push(
  makeTable(
    "User 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["username", "CharField(128)", "是", "是", "用户名（登录用）"],
      ["email", "EmailField", "否", "否", "邮箱"],
      ["phone", "CharField(16)", "否", "否", "手机号"],
      ["role", "CharField(16)", "是", "否", "角色：admin/teacher/student"],
      ["teacher_id", "BigIntegerField", "否", "否", "关联教师记录 ID"],
      ["student_id", "BigIntegerField", "否", "否", "关联学生记录 ID"],
      ["real_name", "CharField(64)", "否", "否", "真实姓名"],
      ["avatar_url", "URLField(512)", "否", "否", "头像链接"],
      ["is_active", "BooleanField", "否", "否", "是否活跃"],
      ["is_admin", "BooleanField", "否", "否", "是否管理员"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

// --- courses ---
children.push(heading2("6.3 courses — 课程管理（5 个模型）"));
children.push(
  makeTable(
    "Course 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["code", "CharField(32)", "是", "是", "课程代码"],
      ["name", "CharField(255)", "是", "否", "课程名称"],
      ["english_name", "CharField(255)", "否", "否", "英文名称"],
      ["category", "FK→CourseCategory", "否", "否", "课程分类"],
      ["college", "FK→colleges.College", "否", "否", "开课学院"],
      ["credits", "DecimalField(4,1)", "否", "否", "学分"],
      ["hours", "IntegerField", "否", "否", "总学时"],
      ["nature", "CharField(32)", "否", "否", "课程性质：必修/选修/公选"],
      ["description", "TextField", "否", "否", "课程描述"],
      ["cover_color", "CharField(16)", "否", "否", "前端展示主题色"],
      ["cover_gradient", "CharField(64)", "否", "否", "前端渐变色"],
      ["cover_icon", "CharField(32)", "否", "否", "前端图标"],
      ["is_active", "BooleanField", "否", "否", "是否启用"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

children.push(
  makeTable(
    "CourseOffering 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["course", "FK→Course", "是", "否", "关联课程"],
      ["semester", "CharField(32)", "是", "否", "开课学期"],
      ["class_name", "CharField(128)", "否", "否", "教学班名称"],
      ["max_students", "IntegerField", "否", "否", "最大选课人数"],
      ["enrolled_count", "IntegerField", "否", "否", "已选人数"],
      ["schedule", "CharField(255)", "否", "否", "上课时间描述"],
      ["classroom", "CharField(128)", "否", "否", "教室"],
      ["is_active", "BooleanField", "否", "否", "是否启用"],
      ["college", "FK→colleges.College", "否", "否", "开课学院"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

children.push(
  makeTable(
    "CourseCategory 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["name", "CharField(128)", "是", "是", "分类名称"],
      ["code", "CharField(32)", "是", "是", "分类代码"],
      ["college", "FK→colleges.College", "否", "否", "归属学院"],
      ["sort_order", "IntegerField", "否", "否", "排序"],
      ["is_active", "BooleanField", "否", "否", "是否启用"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

children.push(
  makeTable(
    "CourseHotScore 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["course", "FK→Course", "是", "否", "关联课程"],
      ["semester", "CharField(32)", "是", "否", "统计学期"],
      ["hot_score", "DecimalField(5,2)", "是", "否", "热度分数"],
      ["enrollment_rate", "DecimalField(5,2)", "否", "否", "选课率(%)"],
      ["satisfaction_rate", "DecimalField(5,2)", "否", "否", "满意度(%)"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
    ],
  )
);

children.push(
  makeTable(
    "CourseEvaluation 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["course_offering", "FK→CourseOffering", "是", "否", "关联开课记录"],
      ["student", "FK→Student", "是", "否", "评价学生"],
      ["semester", "CharField(32)", "是", "否", "学期"],
      ["teaching_content", "IntegerField", "否", "否", "教学内容评分(1-5)"],
      ["teaching_method", "IntegerField", "否", "否", "教学方法评分(1-5)"],
      ["interaction", "IntegerField", "否", "否", "师生互动评分(1-5)"],
      ["innovation", "IntegerField", "否", "否", "课程创新评分(1-5)"],
      ["research_output", "IntegerField", "否", "否", "科研产出评分(1-5)"],
      ["social_service", "IntegerField", "否", "否", "社会服务评分(1-5)"],
      ["overall_score", "DecimalField(3,2)", "否", "否", "综合评分"],
      ["comment", "TextField", "否", "否", "评语"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

// --- teachers ---
children.push(heading2("6.4 teachers — 教师管理（2 个模型）"));
children.push(
  makeTable(
    "Teacher 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["user", "FK→User", "否", "否", "1:1 登录账户，SET_NULL"],
      ["teacher_id", "CharField(32)", "是", "是", "工号"],
      ["name", "CharField(64)", "是", "否", "姓名"],
      ["gender", "CharField(8)", "否", "否", "性别"],
      ["college", "FK→colleges.College", "否", "否", "所属学院"],
      ["title", "CharField(32)", "否", "否", "职称"],
      ["education", "CharField(32)", "否", "否", "学历"],
      ["email", "EmailField", "否", "否", "邮箱"],
      ["phone", "CharField(16)", "否", "否", "手机号"],
      ["avatar", "URLField(512)", "否", "否", "头像链接"],
      ["description", "TextField", "否", "否", "个人简介"],
      ["is_active", "BooleanField", "否", "否", "是否在职"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

children.push(
  makeTable(
    "TeachingTeam 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["name", "CharField(255)", "是", "否", "团队名称"],
      ["college", "FK→colleges.College", "否", "否", "归属学院"],
      ["leader", "FK→Teacher", "否", "否", "团队负责人"],
      ["teachers", "M2M→Teacher", "否", "否", "团队成员（多对多）"],
      ["course_offerings", "M2M→CourseOffering", "否", "否", "负责课程"],
      ["semester", "CharField(32)", "是", "否", "学期"],
      ["description", "TextField", "否", "否", "团队描述"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

// --- students ---
children.push(heading2("6.5 students — 学生管理（2 个模型）"));
children.push(
  makeTable(
    "Student 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["user", "FK→User", "否", "否", "1:1 登录账户，SET_NULL"],
      ["student_id", "CharField(32)", "是", "是", "学号"],
      ["name", "CharField(64)", "是", "否", "姓名"],
      ["gender", "CharField(8)", "否", "否", "性别"],
      ["college", "FK→colleges.College", "否", "否", "所属学院"],
      ["major", "CharField(128)", "否", "否", "专业"],
      ["class_name", "CharField(128)", "否", "否", "班级"],
      ["grade", "CharField(16)", "否", "否", "年级"],
      ["enrollment_year", "IntegerField", "否", "否", "入学年份"],
      ["email", "EmailField", "否", "否", "邮箱"],
      ["phone", "CharField(16)", "否", "否", "手机号"],
      ["gpa", "DecimalField(4,2)", "否", "否", "平均绩点"],
      ["is_active", "BooleanField", "否", "否", "是否在读"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

children.push(
  makeTable(
    "StudentProfile 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["student", "FK→Student", "是", "是", "1:1 关联学生"],
      ["avatar", "URLField(512)", "否", "否", "头像链接"],
      ["bio", "TextField", "否", "否", "个人简介"],
      ["hobbies", "TextField", "否", "否", "爱好"],
      ["awards", "TextField", "否", "否", "获奖记录"],
      ["counselor", "CharField(64)", "否", "否", "辅导员"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

// --- grades ---
children.push(heading2("6.6 grades — 成绩管理（2 个模型）"));
children.push(
  makeTable(
    "Grade 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["student", "FK→Student", "是", "否", "学生"],
      ["course_offering", "FK→CourseOffering", "是", "否", "开课记录"],
      ["semester", "CharField(32)", "是", "否", "学期"],
      ["score", "DecimalField(5,2)", "否", "否", "成绩"],
      ["grade_point", "DecimalField(4,2)", "否", "否", "绩点"],
      ["grade_level", "CharField(8)", "否", "否", "等级：A/B/C/D/F"],
      ["exam_type", "CharField(16)", "否", "否", "考试类型"],
      ["status", "CharField(16)", "否", "否", "状态：draft/submitted/approved"],
      ["is_makeup", "BooleanField", "否", "否", "是否补考"],
      ["remark", "CharField(255)", "否", "否", "备注"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

children.push(
  makeTable(
    "GradeTrend 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["college", "FK→colleges.College", "否", "否", "学院"],
      ["semester", "CharField(32)", "是", "否", "学期"],
      ["semester_label", "CharField(32)", "否", "否", "显示标签"],
      ["avg_score", "DecimalField(5,2)", "否", "否", "平均分"],
      ["pass_rate", "DecimalField(5,2)", "否", "否", "通过率(%)"],
      ["excellent_rate", "DecimalField(5,2)", "否", "否", "优秀率(%)"],
      ["fail_rate", "DecimalField(5,2)", "否", "否", "挂科率(%)"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

// --- exams ---
children.push(heading2("6.7 exams — 考试管理（1 个模型）"));
children.push(
  makeTable(
    "Exam 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["course_offering", "FK→CourseOffering", "是", "否", "关联开课"],
      ["semester", "CharField(32)", "是", "否", "学期"],
      ["exam_name", "CharField(255)", "是", "否", "考试名称"],
      ["exam_type", "CharField(16)", "是", "否", "类型：期中/期末/补考"],
      ["exam_date", "DateTimeField", "是", "否", "考试时间"],
      ["duration", "IntegerField", "否", "否", "考试时长(分钟)"],
      ["location", "CharField(255)", "否", "否", "考试地点"],
      ["invigilator", "CharField(128)", "否", "否", "监考教师（文本）"],
      ["total_students", "IntegerField", "否", "否", "应考人数"],
      ["attended_students", "IntegerField", "否", "否", "实考人数"],
      ["status", "CharField(16)", "否", "否", "状态：scheduled/ongoing/completed"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

// --- analysis ---
children.push(heading2("6.8 analysis — 教学分析（5 个模型）"));
children.push(
  makeTable(
    "TeachingKPI 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["semester", "CharField(32)", "是", "否", "统计学期，如 2024-2025-2"],
      ["period", "CharField(16)", "是", "否", "统计周期：semester/year/all"],
      ["college", "FK→colleges.College", "否", "否", "学院，空为全院汇总"],
      ["quality_index", "DecimalField(5,2)", "是", "否", "教学质量指数(0-100)"],
      ["quality_index_change", "DecimalField(6,2)", "否", "否", "环比变化(%)"],
      ["satisfaction_rate", "DecimalField(5,2)", "是", "否", "学生满意度(%)"],
      ["satisfaction_rate_change", "DecimalField(6,2)", "否", "否", "环比变化(%)"],
      ["course_pass_rate", "DecimalField(5,2)", "是", "否", "课程达标率(%)"],
      ["course_pass_rate_change", "DecimalField(6,2)", "否", "否", "环比变化(%)"],
      ["seminar_participation", "DecimalField(5,2)", "是", "否", "研讨参与指数"],
      ["seminar_participation_change", "DecimalField(6,2)", "否", "否", "环比变化(%)"],
      ["resource_utilization", "DecimalField(5,2)", "是", "否", "教学资源利用率(%)"],
      ["resource_utilization_change", "DecimalField(6,2)", "否", "否", "环比变化(%)"],
      ["warning_rate", "DecimalField(5,2)", "是", "否", "学业预警率(%)"],
      ["warning_rate_change", "DecimalField(6,2)", "否", "否", "环比变化(%)"],
      ["total_courses", "IntegerField", "否", "否", "开设课程数(驾驶舱)"],
      ["active_teachers", "IntegerField", "否", "否", "在授教师数(驾驶舱)"],
      ["avg_weekly_hours", "DecimalField(5,2)", "否", "否", "人均课时(驾驶舱)"],
      ["supervisor_score", "DecimalField(5,2)", "否", "否", "督导评分(驾驶舱)"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

children.push(
  makeTable(
    "TeachingQuality 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["semester", "CharField(32)", "是", "否", "学期"],
      ["semester_label", "CharField(32)", "是", "否", "显示标签，如 21秋"],
      ["college", "FK→colleges.College", "否", "否", "学院"],
      ["actual_score", "DecimalField(4,2)", "否", "否", "实际质量分(0-5)"],
      ["predicted_score", "DecimalField(4,2)", "否", "否", "AI 预测值"],
      ["target_score", "DecimalField(4,2)", "否", "否", "目标线(默认4.50)"],
      ["teaching_content_score", "DecimalField(4,2)", "否", "否", "教学内容分"],
      ["teaching_method_score", "DecimalField(4,2)", "否", "否", "教学方法分"],
      ["interaction_score", "DecimalField(4,2)", "否", "否", "师生互动分"],
      ["innovation_score", "DecimalField(4,2)", "否", "否", "课程创新分"],
      ["research_output_score", "DecimalField(4,2)", "否", "否", "科研产出分"],
      ["social_service_score", "DecimalField(4,2)", "否", "否", "社会服务分"],
      ["is_prediction", "BooleanField", "是", "否", "是否为AI预测值"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

children.push(
  makeTable(
    "SatisfactionSurvey 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["semester", "CharField(32)", "是", "否", "学期"],
      ["college", "FK→colleges.College", "否", "否", "学院"],
      ["dimension", "CharField(64)", "是", "否", "调查维度（6种：教学内容/教学方法/课堂氛围/课后辅导/考核方式/教材选用）"],
      ["very_satisfied", "IntegerField", "否", "否", "非常满意人数"],
      ["satisfied", "IntegerField", "否", "否", "满意人数"],
      ["neutral", "IntegerField", "否", "否", "一般人数"],
      ["dissatisfied", "IntegerField", "否", "否", "不满意人数"],
      ["total_responses", "IntegerField", "否", "否", "总参与人数"],
      ["satisfaction_score", "DecimalField(5,2)", "否", "否", "综合得分"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

children.push(
  makeTable(
    "RiskEvent 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["level", "CharField(16)", "是", "否", "风险等级：high/medium/low"],
      ["status", "CharField(16)", "是", "否", "状态：active/processing/resolved/dismissed"],
      ["title", "CharField(255)", "是", "否", "风险标题"],
      ["description", "TextField", "是", "否", "风险描述"],
      ["scope", "CharField(255)", "否", "否", "影响范围"],
      ["suggested_action", "CharField(255)", "否", "否", "建议措施"],
      ["semester", "CharField(32)", "否", "否", "关联学期"],
      ["college", "FK→colleges.College", "否", "否", "关联学院"],
      ["course_offering", "FK→CourseOffering", "否", "否", "关联课程"],
      ["triggered_at", "DateTimeField", "是", "否", "触发时间"],
      ["resolved_at", "DateTimeField", "否", "否", "解决时间"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
      ["Meta.ordering", "—", "—", "—", "✅ 已修复：`[\"-triggered_at\"]`"],
    ],
  )
);

children.push(
  makeTable(
    "AISuggestion 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["priority", "CharField(16)", "是", "否", "优先级：high/medium/low"],
      ["status", "CharField(16)", "是", "否", "状态：pending/accepted/rejected/implemented"],
      ["title", "CharField(255)", "是", "否", "建议标题"],
      ["description", "TextField", "是", "否", "建议详述"],
      ["confidence", "IntegerField", "是", "否", "置信度(0-100)"],
      ["semester", "CharField(32)", "否", "否", "关联学期"],
      ["college", "FK→colleges.College", "否", "否", "关联学院"],
      ["accepted_by", "FK→User", "否", "否", "采纳人"],
      ["model_name", "CharField(64)", "否", "否", "AI 模型名称"],
      ["prompt_version", "CharField(32)", "否", "否", "提示词版本"],
      ["source_data_snapshot", "TextField", "否", "否", "数据快照摘要"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
      ["Meta.ordering", "—", "—", "—", "✅ 已修复：`[\"-confidence\"]`"],
    ],
  )
);

// --- notifications ---
children.push(heading2("6.9 notifications — 通知系统（2 个模型）"));
children.push(
  makeTable(
    "Notification 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["title", "CharField(255)", "是", "否", "通知标题"],
      ["content", "TextField", "是", "否", "通知内容"],
      ["notification_type", "CharField(32)", "是", "否", "类型：system/course/exam/grade/risk/ai/announcement/other"],
      ["priority", "CharField(16)", "是", "否", "优先级：low/normal/high/urgent"],
      ["sender", "FK→User", "否", "否", "发送者，系统通知时可为空"],
      ["target_type", "CharField(64)", "否", "否", "关联目标类型"],
      ["target_id", "IntegerField", "否", "否", "关联目标ID"],
      ["target_url", "CharField(512)", "否", "否", "跳转链接"],
      ["is_published", "BooleanField", "否", "否", "是否发布"],
      ["publish_at", "DateTimeField", "否", "否", "定时发布时间"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
      ["TypeChoices", "—", "—", "—", "✅ 已修复：移除重复定义"],
    ],
  )
);

children.push(
  makeTable(
    "UserNotification 模型字段",
    [18, 18, 10, 18, 36],
    ["字段名", "字段类型", "必填", "唯一", "说明"],
    [
      ["notification", "FK→Notification", "是", "否", "通知（CASCADE）"],
      ["user", "FK→User", "是", "否", "接收用户（CASCADE）"],
      ["is_read", "BooleanField", "否", "否", "是否已读"],
      ["read_at", "DateTimeField", "否", "否", "阅读时间"],
      ["is_pinned", "BooleanField", "否", "否", "是否置顶"],
      ["pinned_at", "DateTimeField", "否", "否", "置顶时间"],
      ["is_deleted", "BooleanField", "否", "否", "是否删除（软删除）"],
      ["deleted_at", "DateTimeField", "否", "否", "删除时间"],
      ["created_at", "DateTimeField", "是", "否", "自动创建时间"],
      ["updated_at", "DateTimeField", "是", "否", "自动更新时间"],
    ],
  )
);

// ==================== 七、修复前后对比 ====================
children.push(heading1("七、关键修复前后对比"));

children.push(heading2("7.1 P0-1：colleges 应用缺失"));
children.push(
  makeTable(
    "colleges 应用修复对比",
    [50, 50],
    ["修复前", "修复后"],
    [
      [
        "apps/colleges/ 目录不存在\n\n10 个模型的 ForeignKey(\"colleges.College\")\n引用不存在 → makemigrations 报错 LookupError",
        "✅ 新建 apps/colleges/__init__.py\n✅ 新建 apps/colleges/models.py\n✅ College 模型包含 code, name, short_name,\n   sort_order, logo_url, is_active",
      ],
    ],
  )
);

children.push(heading2("7.2 P0-2：notifications TypeChoices 重复定义"));
children.push(
  makeTable(
    "TypeChoices 修复对比",
    [50, 50],
    ["修复前", "修复后"],
    [
      [
        `class TypeChoices(models.TextChoices):
    SYSTEM = "system", "系统通知"
    ...
    RISK = "risk", "风险预警"
    AI = "ai", "AI 建议"
    ANNOUNCEMENT = "announcement", "公告"
    OTHER = "other", "其他"
    ANNOUNCEMENT = "announcement", "公告"  ← 重复
    OTHER = "other", "其他"                  ← 重复`,
        `class TypeChoices(models.TextChoices):
    SYSTEM = "system", "系统通知"
    ...
    RISK = "risk", "风险预警"
    AI = "ai", "AI 建议"
    ANNOUNCEMENT = "announcement", "公告"
    OTHER = "other", "其他"`,
      ],
    ],
  )
);

children.push(heading2("7.3 P1-1 / P1-2：Meta.ordering 使用 @property"));
children.push(
  makeTable(
    "Meta.ordering 修复对比",
    [30, 35, 35],
    ["编号", "修复前", "修复后"],
    [
      [
        "P1-1\n(RiskEvent)",
        "`ordering = [\"-level_order\", \"-triggered_at\"]`\n\n`level_order` 是 Python @property，\n不在数据库中 → 查询报错",
        "`ordering = [\"-triggered_at\"]`\n\n✅ 使用数据库列排序",
      ],
      [
        "P1-2\n(AISuggestion)",
        "`ordering = [\"-priority_order\", \"-confidence\"]`\n\n`priority_order` 是 Python @property，\n不在数据库中 → 查询报错",
        "`ordering = [\"-confidence\"]`\n\n✅ 使用数据库列排序",
      ],
    ],
  )
);

// ==================== 八、统计汇总 ====================
children.push(heading1("八、统计汇总"));

children.push(
  makeTable(
    "审查统计数据",
    [40, 20, 20, 20],
    ["类别", "数量", "已修复", "待处理"],
    [
      ["Django App 总数", "9 (+1 新建)", "—", "—"],
      ["数据库表（模型）总数", "20", "—", "—"],
      ["致命问题 (P0)", "2", "✅ 2", "0"],
      ["严重问题 (P1)", "2", "✅ 2", "0"],
      ["中等问题 (P2)", "2", "0", "⚠ 2 (不影响运行)"],
      ["低风险问题 (P3)", "3", "0", "⚠ 3 (建议关注)"],
      ["新建文件", "2", "✅ 2", "—"],
      ["修改文件", "2", "✅ 2", "—"],
    ],
  )
);

// ==================== 九、后续建议 ====================
children.push(heading1("九、后续建议"));

children.push(normalPara("1. 确保 apps.colleges 已在项目的 INSTALLED_APPS 中注册。", { bold: false }));
children.push(normalPara("2. 运行 python manage.py makemigrations --dry-run 验证迁移是否成功生成。", { bold: false }));
children.push(normalPara("3. 如需按风险等级（high/medium/low）或优先级排序，可在 DRF 序列化器/视图中使用 Django 的 Case/When 表达式显式排序。", { bold: false }));
children.push(normalPara("4. P2-2：在 User 序列化器中添加 teacher_id/student_id 的存在性校验，防止创建悬空引用。", { bold: false }));
children.push(normalPara("5. P3-1：后续迭代中将 unique_together 迁移为 UniqueConstraint。", { bold: false }));

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
  const outPath = "d:/Personal/Desktop/教学系统/Django_Models_审查报告.docx";
  fs.writeFileSync(outPath, buffer);
  console.log("✅ Word 文档已生成: " + outPath);
}).catch((err) => {
  console.error("❌ 生成失败:", err);
});