from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class HealthEndpointTests(APITestCase):
    def test_health_is_public(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")


class AuthenticationTests(APITestCase):
    def test_login_rejects_missing_credentials(self):
        response = self.client.post("/api/auth/login/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_frontend_compatible_fields(self):
        User.objects.create_user(username="demo-test", password="StrongPass123!")
        response = self.client.post("/api/auth/login/", {
            "username": "demo-test", "password": "StrongPass123!"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
