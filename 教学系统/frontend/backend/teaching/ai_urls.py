"""只被 backend/teaching/urls.py 的 path('ai/', include('teaching.ai_urls')) 引入。"""
from django.urls import path
from .ai_views import (
    AIDemoReplayView, AIOverviewView, AIChatView, AIWarningListView, AIWarningSyncView, AIWarningDetailView,
)

urlpatterns = [
    path("demo-replay/", AIDemoReplayView.as_view(), name="ai-demo-replay"),
    path("overview/", AIOverviewView.as_view(), name="ai-overview"),
    path("chat/", AIChatView.as_view(), name="ai-chat"),
    path("warnings/", AIWarningListView.as_view(), name="ai-warnings"),
    path("warnings/sync/", AIWarningSyncView.as_view(), name="ai-warnings-sync"),
    path("warnings/<int:case_id>/", AIWarningDetailView.as_view(), name="ai-warning-detail"),
]
