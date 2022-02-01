from django.contrib.auth import get_user_model
from django.test import TestCase

from app_auth.models import UserProfile


class TestCaseMixin(TestCase):
    tested_template = None
    tested_url_name = None

    username = "bloger"
    user_raw_password = "bobah12345"

    @classmethod
    def setUpTestData(cls):
        cls.profile = UserProfile.objects.create(
            user=get_user_model().objects.create(
                username=cls.username,
            )
        )
        cls.profile.user.set_password(cls.user_raw_password)
        cls.profile.user.save()

    def login_test(self):
        """
        Авторизация
        """
        logged_in = self.client.login(username=self.profile.user.username, password=self.user_raw_password)
        self.assertTrue(logged_in, f"not logged {self.profile.user.username}")

    def not_access_in_html_test(self, response, url):
        self.assertNotContains(response, url, html=True)

    def has_access_in_html_test(self, response, url):
        self.assertContains(response, url, html=True)

