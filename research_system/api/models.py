from django.db import models

# Create your models here.

class Dept(models.Model):
    dept_name = models.CharField(max_length=50, verbose_name="系别名称")

class User(models.Model):
    ROLE_CHOICES = [('admin', '管理员'), ('teacher', '教师')]
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)  # 实际开发应加密
    real_name = models.CharField(max_length=50)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    title = models.CharField(max_length=50, blank=True)
    dept = models.ForeignKey(Dept, on_delete=models.SET_NULL, null=True)

class Project(models.Model):
    TYPE_CHOICES = [('国家级','国家级'),('省部级','省部级'),('横向','横向'),('校级','校级')]
    STATUS_CHOICES = [('在研','在研'),('结题','结题'),('立项','立项'),('审核中','审核中')]
    project_no = models.CharField(max_length=50)
    project_name = models.CharField(max_length=200)
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    dept = models.ForeignKey(Dept, on_delete=models.SET_NULL, null=True)
    project_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    fund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    actual_progress = models.IntegerField(default=0)
    subject = models.CharField(max_length=50, blank=True, null=True, verbose_name="学科分类")

class FundDetail(models.Model):
    SOURCE_CHOICES = [('国家社科','国家社科'),('教育部','教育部'),('省级项目','省级项目'),('横向课题','横向课题'),('政府委托','政府委托')]
    USAGE_CHOICES = [('设备费','设备费'),('业务费','业务费'),('劳务费','劳务费'),('会议费','会议费'),('出版费','出版费'),('其他','其他')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='funds')
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    year = models.IntegerField()
    usage_type = models.CharField(max_length=20, choices=USAGE_CHOICES)

class Achievement(models.Model):
    TYPE_CHOICES = [('期刊论文','期刊论文'),('学术著作','学术著作'),('研究报告','研究报告'),('专利','专利'),('获奖','获奖'),('决策咨询','决策咨询')]
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    dept = models.ForeignKey(Dept, on_delete=models.SET_NULL, null=True)
    achievement_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    level = models.CharField(max_length=50, blank=True)
    publish_year = models.IntegerField()
    citation_count = models.IntegerField(default=0)
    is_international = models.BooleanField(default=False)
    subject = models.CharField(max_length=50, blank=True, null=True, verbose_name="学科分类")

class TeacherScore(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scores')
    year = models.IntegerField()
    research_score = models.DecimalField(max_digits=5, decimal_places=2)
    teaching_score = models.DecimalField(max_digits=5, decimal_places=2)
    service_score = models.DecimalField(max_digits=5, decimal_places=2)
    comprehensive_score = models.DecimalField(max_digits=5, decimal_places=2)

class Cooperation(models.Model):
    source = models.CharField(max_length=100)   # 可为教师名或外部机构名
    target = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    coop_count = models.IntegerField(default=1)

class DeptResource(models.Model):
    dept = models.ForeignKey(Dept, on_delete=models.CASCADE)
    year = models.IntegerField()
    input_amount = models.DecimalField(max_digits=10, decimal_places=2)
    output_amount = models.DecimalField(max_digits=10, decimal_places=2)
    lab_count = models.IntegerField(default=0)

class RiskWarning(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    warning_date = models.DateField()
    risk_level = models.CharField(max_length=10, choices=[('低','低'),('中','中'),('高','高')])
    reason = models.CharField(max_length=255)
    suggested_action = models.TextField()
    is_resolved = models.BooleanField(default=False)