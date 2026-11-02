from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.graduate.api_security import PredictionApiSecurityMixin


class ApiIndexView(PredictionApiSecurityMixin, APIView):
    permission_classes = [AllowAny]
    security_scope = "public_meta"

    def get(self, request):
        return Response(
            {
                "name": "Graduate Management API",
                "version": "v1",
                "modules": {
                    "auth": "/api/v1/auth/",
                    "health": "/api/v1/health/",
                    "sharedOptions": "/api/v1/shared-options/",
                    "home": "/api/v1/home/",
                    "admission": "/api/v1/admission/",
                    "academicStatus": "/api/v1/academic-status/",
                    "academicChange": "/api/v1/academic-change/",
                    "training": "/api/v1/training/",
                    "trainingCourse": "/api/v1/training-course/",
                    "degree": "/api/v1/degree/",
                    "degreeDefense": "/api/v1/degree-defense/",
                    "scholarship": "/api/v1/scholarship/",
                    "employment": "/api/v1/employment/",
                    "intelligentPrediction": "/api/v1/intelligent-prediction/",
                },
            }
        )


class HealthCheckView(PredictionApiSecurityMixin, APIView):
    permission_classes = [AllowAny]
    security_scope = "public_meta"

    def get(self, request):
        return Response({"status": "ok"})
