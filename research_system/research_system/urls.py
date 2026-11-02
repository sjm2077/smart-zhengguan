"""
URL configuration for research_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.contrib import admin
from api import views
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('', views.index, name='index'),
    path('project/', views.project_page, name='project_page'),
    path('fund/', views.fund_page,name='fund_page'),
    path('achievement/', views.achievement_page, name='achievement_page'),
    path('analysis/teacher/', views.teacher_analysis_page, name='teacher_analysis'),
    path('analysis/admin/', views.admin_analysis_page, name='admin_analysis'),
    path('dept/science/', views.science_socialism_page),
    path('dept/political/', views.political_science_page),
    path('dept/international/', views.international_politics_page),
    path('dept/public/', views.public_management_page),
]
