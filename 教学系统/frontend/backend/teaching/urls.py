from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    LoginView, MeView, CollegeViewSet, SemesterViewSet, TeacherViewSet,
    StudentViewSet, CourseViewSet, TeachingClassViewSet, ExamViewSet,
    GradeViewSet, NoticeViewSet, DashboardSummaryView, ScoreDistributionView,
    CourseScoresView, SemesterTrendView, StudentRankingView,
    GradeTypeComparisonView, DashboardAlertsView, DashboardLiveFeedView,
    GraduateEmploymentDashboardView,
)

router = DefaultRouter()
router.register("colleges", CollegeViewSet, basename="college")
router.register("semesters", SemesterViewSet, basename="semester")
router.register("teachers", TeacherViewSet, basename="teacher")
router.register("students", StudentViewSet, basename="student")
router.register("courses", CourseViewSet, basename="course")
router.register("teaching-classes", TeachingClassViewSet, basename="teaching-class")
router.register("exams", ExamViewSet, basename="exam")
router.register("grades", GradeViewSet, basename="grade")
router.register("notices", NoticeViewSet, basename="notice")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("dashboard/graduate-employment/", GraduateEmploymentDashboardView.as_view(), name="dashboard-graduate-employment"),
    path("dashboard/alerts/", DashboardAlertsView.as_view(), name="dashboard-alerts"),
    path("dashboard/live-feed/", DashboardLiveFeedView.as_view(), name="dashboard-live-feed"),
    path("dashboard/semesters/", SemesterViewSet.as_view({"get": "list"}), name="dashboard-semesters"),
    path("dashboard/colleges/", CollegeViewSet.as_view({"get": "list"}), name="dashboard-colleges"),
    path("analysis/score-distribution/", ScoreDistributionView.as_view(), name="score-distribution"),
    path("analysis/course-scores/", CourseScoresView.as_view(), name="course-scores"),
    path("analysis/semester-trend/", SemesterTrendView.as_view(), name="semester-trend"),
    path("analysis/student-ranking/", StudentRankingView.as_view(), name="student-ranking"),
    path("ai/", include("teaching.ai_urls")),
    path("", include(router.urls)),
    path(
    "analysis/grade-type-comparison/",
    GradeTypeComparisonView.as_view(),
    name="grade-type-comparison",
),
]
