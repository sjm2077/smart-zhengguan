from django.urls import path

from apps.graduate import views


urlpatterns = [
    path("shared-options/", views.SharedOptionsView.as_view(), name="shared-options"),
    path("home/", views.HomeDataView.as_view(), name="home-data"),
    path("admission/", views.AdmissionDataView.as_view(), name="admission-data"),
    path("academic-status/", views.AcademicStatusDataView.as_view(), name="academic-status-data"),
    path("academic-change/", views.AcademicChangeDataView.as_view(), name="academic-change-data"),
    path("training/", views.TrainingDataView.as_view(), name="training-data"),
    path("training-course/", views.TrainingCourseDataView.as_view(), name="training-course-data"),
    path("degree/", views.DegreeDataView.as_view(), name="degree-data"),
    path("degree-defense/", views.DegreeDefenseDataView.as_view(), name="degree-defense-data"),
    path("scholarship/", views.ScholarshipDataView.as_view(), name="scholarship-data"),
    path("employment/", views.EmploymentDataView.as_view(), name="employment-data"),
    path("search/", views.GlobalSearchView.as_view(), name="global-search"),
    path("cross-module-query/", views.CrossModuleQueryView.as_view(), name="cross-module-query"),
    path(
        "intelligent-prediction/context/",
        views.PredictionContextView.as_view(),
        name="intelligent-prediction-context",
    ),
    path(
        "intelligent-prediction/analyze/",
        views.PredictionAnalyzeView.as_view(),
        name="intelligent-prediction-analyze",
    ),
    path(
        "intelligent-prediction/chat/",
        views.PredictionChatView.as_view(),
        name="intelligent-prediction-chat",
    ),
    path(
        "intelligent-prediction/chat/stream/",
        views.PredictionChatStreamView.as_view(),
        name="intelligent-prediction-chat-stream",
    ),
    path(
        "intelligent-prediction/",
        views.IntelligentPredictionDataView.as_view(),
        name="intelligent-prediction-data",
    ),
    # R05: Data Upload URLs
    path("upload/file/", views.UploadFileView.as_view(), name="upload-file"),
    path("upload/identify/", views.SheetIdentifyView.as_view(), name="upload-identify"),
    path("upload/mapping/", views.FieldMappingView.as_view(), name="upload-mapping"),
    path("upload/validate-preview/", views.ValidateAndPreviewView.as_view(), name="upload-validate-preview"),
    path("upload/confirm/", views.ConfirmImportView.as_view(), name="upload-confirm"),
    path("upload/batches/", views.ImportBatchListView.as_view(), name="upload-batches"),
    path("upload/batches/<int:pk>/", views.ImportBatchDetailView.as_view(), name="upload-batch-detail"),
    path("upload/revert/", views.RevertBatchView.as_view(), name="upload-revert"),
    path("upload/templates/", views.MappingTemplateView.as_view(), name="upload-templates"),
    # R06: Export URLs
    path("export/fields/", views.ExportFieldsView.as_view(), name="export-fields"),
    path("export/student-list/", views.StudentListExportView.as_view(), name="export-student-list"),
    path("export/summary-table/", views.SummaryTableExportView.as_view(), name="export-summary-table"),
    path("export/records/", views.ExportRecordListView.as_view(), name="export-records"),
    path("export/templates/", views.ExportTemplateView.as_view(), name="export-templates"),
    # R07: Warning Rule Engine URLs
    path("warning/rules/", views.WarningRuleListView.as_view(), name="warning-rules"),
    path("warning/rules/<int:pk>/", views.WarningRuleDetailView.as_view(), name="warning-rule-detail"),
    path("warning/scan/", views.WarningScanView.as_view(), name="warning-scan"),
    path("warning/instances/", views.WarningInstanceListView.as_view(), name="warning-instances"),
    path("warning/instances/<int:pk>/", views.WarningInstanceDetailView.as_view(), name="warning-instance-detail"),
    path("warning/instances/<int:pk>/treat/", views.WarningTreatmentView.as_view(), name="warning-treatment"),
    path("warning/stats/", views.WarningStatsView.as_view(), name="warning-stats"),
]
