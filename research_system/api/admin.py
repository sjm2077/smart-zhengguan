from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Dept, User, Project, FundDetail, Achievement, TeacherScore, Cooperation, DeptResource, RiskWarning

admin.site.register(Dept)
admin.site.register(User)
admin.site.register(Project)
admin.site.register(FundDetail)
admin.site.register(Achievement)
admin.site.register(TeacherScore)
admin.site.register(Cooperation)
admin.site.register(DeptResource)
admin.site.register(RiskWarning)