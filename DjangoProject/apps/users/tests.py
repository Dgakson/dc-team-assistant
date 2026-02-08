from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class UserAuthTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )

    def test_admin_can_register_user(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse("register")
        payload = {"email": "user1@example.com", "password": "pass12345"}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["email"], "user1@example.com")

    def test_token_obtain_pair_with_email(self):
        User.objects.create_user(email="user2@example.com", password="pass12345")
        url = reverse("token_obtain_pair")
        response = self.client.post(url, {"email": "user2@example.com", "password": "pass12345"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_me_requires_auth(self):
        url = reverse("me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
