from django.db import models


class Student(models.Model):
    """学生基本信息"""

    class GenderChoices(models.TextChoices):
        MALE = "male", "男"
        FEMALE = "female", "女"

    class StatusChoices(models.TextChoices):
        ACTIVE = "active", "在读"
        WARNING = "warning", "预警"
        GRADUATED = "graduated", "已毕业"
        SUSPENDED = "suspended", "休学"

    class EducationLevelChoices(models.TextChoices):
        BACHELOR = "bachelor", "本科"
        MASTER = "master", "硕士"
        DOCTOR = "doctor", "博士"

    # ============ 学籍信息 ============
    student_no = models.CharField(
        max_length=32,
        unique=True,
        verbose_name="学号",
    )
    name = models.CharField(
        max_length=64,
        verbose_name="姓名",
    )
    gender = models.CharField(
        max_length=8,
        choices=GenderChoices.choices,
        blank=True,
        default="",
        verbose_name="性别",
    )
    college = models.ForeignKey(
        "colleges.College",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name="所属学院",
    )
    major = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="专业",
    )
    grade = models.CharField(
        max_length=16,
        blank=True,
        default="",
        verbose_name="年级",
        help_text="例如 2023、2024",
    )
    class_name = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="班级",
    )
    education_level = models.CharField(
        max_length=16,
        choices=EducationLevelChoices.choices,
        default=EducationLevelChoices.BACHELOR,
        verbose_name="学历层次",
    )
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        verbose_name="学籍状态",
    )

    # ============ 联系方式 ============
    email = models.EmailField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="邮箱",
    )
    phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="电话",
    )

    # ============ 学业概况 (由成绩系统聚合更新) ============
    gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        verbose_name="累计 GPA",
    )
    total_credits = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=0.0,
        verbose_name="已修总学分",
    )

    # ============ 关联账户 ============
    user = models.OneToOneField(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
        verbose_name="关联登录账户",
        help_text="与 users.User 一对一绑定，仅 role=student 时有值",
    )

    # ============ 时间戳 ============
    enrollment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="入学日期",
    )
    graduation_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="毕业日期",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="删除时间",
    )

    class Meta:
        db_table = "students"
        verbose_name = "学生"
        verbose_name_plural = verbose_name
        ordering = ["college__name", "student_no"]
        indexes = [
            models.Index(fields=["college_id"], name="idx_student_college_id"),
            models.Index(fields=["student_no"], name="idx_student_no"),
            models.Index(fields=["status"], name="idx_student_status"),
            models.Index(fields=["grade"], name="idx_student_grade"),
            models.Index(fields=["major"], name="idx_student_major"),
            models.Index(fields=["user_id"], name="idx_student_user_id"),
            models.Index(fields=["name"], name="idx_student_name"),
            models.Index(fields=["gpa"], name="idx_student_gpa"),
        ]

    def __str__(self):
        college_name = self.college.name if self.college else "未分配学院"
        return f"{self.student_no} {self.name} — {college_name}"


class StudentProfile(models.Model):
    """学生扩展档案"""

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="学生",
    )
    avatar = models.URLField(
        max_length=512,
        blank=True,
        default="",
        verbose_name="头像地址",
    )
    id_card = models.CharField(
        max_length=18,
        blank=True,
        default="",
        verbose_name="身份证号",
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="出生日期",
    )
    nationality = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="民族",
    )
    political_status = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="政治面貌",
    )
    native_place = models.CharField(
        max_length=128,
        blank=True,
        default="",
        verbose_name="生源地",
    )
    address = models.TextField(
        blank=True,
        default="",
        verbose_name="家庭地址",
    )
    emergency_contact = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="紧急联系人",
    )
    emergency_phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        verbose_name="紧急联系电话",
    )
    dormitory = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="宿舍号",
    )

    class Meta:
        db_table = "student_profiles"
        verbose_name = "学生扩展档案"
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.student.name} 的扩展档案"


class StudentWarning(models.Model):
    """学生预警记录"""

    class LevelChoices(models.TextChoices):
        HIGH = "high", "高"
        MEDIUM = "medium", "中"
        LOW = "low", "低"

    class TypeChoices(models.TextChoices):
        GRADE = "grade", "成绩预警"
        ATTENDANCE = "attendance", "出勤预警"
        CREDIT = "credit", "学分预警"
        BEHAVIOR = "behavior", "行为预警"
        MENTAL = "mental", "心理预警"
        FINANCIAL = "financial", "经济预警"
        OTHER = "other", "其他"

    class StatusChoices(models.TextChoices):
        ACTIVE = "active", "生效中"
        RESOLVED = "resolved", "已解除"
        DISMISSED = "dismissed", "已驳回"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="warnings",
        verbose_name="学生",
    )
    level = models.CharField(
        max_length=16,
        choices=LevelChoices.choices,
        verbose_name="预警级别",
    )
    warning_type = models.CharField(
        max_length=16,
        choices=TypeChoices.choices,
        verbose_name="预警类型",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="预警标题",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="预警描述",
    )
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.ACTIVE,
        verbose_name="状态",
    )
    issued_by = models.ForeignKey(
        "teachers.Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issued_warnings",
        verbose_name="发出人",
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="解除时间",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )

    class Meta:
        db_table = "student_warnings"
        verbose_name = "学生预警记录"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student_id"], name="idx_warn_student_id"),
            models.Index(fields=["level"], name="idx_warn_level"),
            models.Index(fields=["warning_type"], name="idx_warn_type"),
            models.Index(fields=["status"], name="idx_warn_status"),
            models.Index(fields=["created_at"], name="idx_warn_created_at"),
        ]

    def __str__(self):
        return f"[{self.get_level_display()}] {self.title} — {self.student.name}"


class StudentHonor(models.Model):
    """学生荣誉与获奖"""

    class LevelChoices(models.TextChoices):
        NATIONAL = "national", "国家级"
        PROVINCIAL = "provincial", "省部级"
        MUNICIPAL = "municipal", "市级"
        SCHOOL = "school", "校级"
        COLLEGE = "college", "院级"
        OTHER = "other", "其他"

    class TypeChoices(models.TextChoices):
        SCHOLARSHIP = "scholarship", "奖学金"
        COMPETITION = "competition", "竞赛获奖"
        PUBLICATION = "publication", "论文发表"
        PATENT = "patent", "专利"
        VOLUNTEER = "volunteer", "志愿服务"
        LEADERSHIP = "leadership", "干部表彰"
        OTHER = "other", "其他"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="honors",
        verbose_name="学生",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="荣誉名称",
    )
    honor_type = models.CharField(
        max_length=32,
        choices=TypeChoices.choices,
        verbose_name="荣誉类型",
    )
    level = models.CharField(
        max_length=32,
        choices=LevelChoices.choices,
        verbose_name="获奖级别",
    )
    issuing_authority = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="颁发机构",
    )
    award_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="获奖日期",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="荣誉描述",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )

    class Meta:
        db_table = "student_honors"
        verbose_name = "学生荣誉获奖"
        verbose_name_plural = verbose_name
        ordering = ["-award_date"]
        indexes = [
            models.Index(fields=["student_id"], name="idx_honor_student_id"),
            models.Index(fields=["honor_type"], name="idx_honor_type"),
            models.Index(fields=["level"], name="idx_honor_level"),
        ]

    def __str__(self):
        return f"[{self.get_honor_type_display()}] {self.name} — {self.student.name}"


class StudentActivity(models.Model):
    """学生课外活动与社团参与"""

    class ActivityTypeChoices(models.TextChoices):
        CLUB = "club", "社团活动"
        COMPETITION = "competition", "学科竞赛"
        VOLUNTEER = "volunteer", "志愿服务"
        INTERNSHIP = "internship", "实习实践"
        SPORTS = "sports", "体育活动"
        CULTURE = "culture", "文艺活动"
        LECTURE = "lecture", "学术讲座"
        OTHER = "other", "其他"

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name="学生",
    )
    name = models.CharField(
        max_length=255,
        verbose_name="活动名称",
    )
    activity_type = models.CharField(
        max_length=32,
        choices=ActivityTypeChoices.choices,
        verbose_name="活动类型",
    )
    organizer = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="主办单位",
    )
    role = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="担任角色",
        help_text="例如队长、成员、志愿者等",
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="开始日期",
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="结束日期",
    )
    duration_hours = models.DecimalField(
        max_digits=8,
        decimal_places=1,
        default=0.0,
        verbose_name="参与时长(小时)",
    )
    description = models.TextField(
        blank=True,
        default="",
        verbose_name="活动描述",
    )
    achievement = models.TextField(
        blank=True,
        default="",
        verbose_name="活动成果",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="更新时间",
    )

    class Meta:
        db_table = "student_activities"
        verbose_name = "学生课外活动"
        verbose_name_plural = verbose_name
        ordering = ["-start_date", "-created_at"]
        indexes = [
            models.Index(fields=["student_id"], name="idx_act_student_id"),
            models.Index(fields=["activity_type"], name="idx_act_type"),
            models.Index(fields=["start_date"], name="idx_act_start_date"),
        ]

    def __str__(self):
        return f"[{self.get_activity_type_display()}] {self.name} — {self.student.name}"