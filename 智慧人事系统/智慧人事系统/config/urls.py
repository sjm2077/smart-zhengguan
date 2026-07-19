from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    # 首页
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    # API 接口
    path('api/', include('personnel.urls')),
]
