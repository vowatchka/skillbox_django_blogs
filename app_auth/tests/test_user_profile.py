import os

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.core.files import File as DjangoFile

from ..models import Avatar

from app_blogs.models import Blog
from app_blogs.tests.utils import TestCaseMixin


class UserProfileTest(TestCaseMixin, TestCase):
    tested_template = "user-profile.html"
    tested_url_name = "user_profile"

    blogs_context_name = "blogs"
    avatar_context_name = "avatar"

    def test_page(self):
        """
        Проверка, что страница находится по нужному адресу и использует правильный шаблон
        """
        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username,)))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.tested_template)
        return response

    def test_context(self):
        """
        Проверка, что на странице профиля вообще возможен вывод блогов и аватара
        """
        response = self.test_page()
        self.assertTrue(self.blogs_context_name in response.context)
        self.assertTrue(self.avatar_context_name in response.context)

    def test_no_blogs(self):
        """
        Проверка, что блогов нет на странице
        """
        response = self.test_page()
        self.assertEquals(len(response.context[self.blogs_context_name]), 0)

    def test_blogs(self):
        """
        Проверка, что блоги есть на странице
        """
        count = 10
        for i in range(0, count):
            Blog.objects.create(
                title=f"Blog {i}",
                profile=self.profile
            )

        response = self.test_page()
        self.assertEquals(len(response.context[self.blogs_context_name]), count)

    def test_no_avatar(self):
        """
        Проверка, что аватара нет на странице
        """
        response = self.test_page()
        self.assertIsNone(response.context[self.avatar_context_name])

    def test_avatar(self):
        """
        Проверка, что аватар есть на странице
        """
        avatar = Avatar.objects.create(
            avatar=DjangoFile(
                open(os.path.join(os.path.dirname(__file__), "me-30.jpg"), mode="rb"),
                "me-30.jpg"
            ),
            profile=self.profile
        )

        response = self.test_page()

        self.assertIsNotNone(response.context[self.avatar_context_name])
        self.assertIn(
            r'<img src="{url}"'.format(url=avatar.avatar.url),
            response.content.decode("utf-8")
        )

    def test_has_not_access_on_page(self):
        """
        Проверка, что для неавторизованному пользователю форма для редактирования профиля не доступна
        """
        response = self.test_page()

        self.not_access_in_html_test(
            response,
            r'<form method="post" action="{url}" enctype="multipart/form-data">'.format(
                url=reverse(self.tested_url_name, args=(self.profile.user.username,))
            )
        )

    def test_authorized_user_has_not_access(self):
        """
        Проверка, что авторизованному пользователю не доступна форма редактирования чужого профиля
        """
        user = get_user_model().objects.create(username="some_user")
        user.set_password(self.user_raw_password)
        user.save()

        logged_in = self.client.login(username=user.username, password=self.user_raw_password)
        self.assertTrue(logged_in, f"not logged {user.username}")

        self.test_has_not_access_on_page()

    def test_can_edit(self):
        """
        Проверка, что для авторизованному пользователю доступна форма редактирования профиля
        """
        self.login_test()

        self.assertIn(
            r'<form method="post" action="{url}" enctype="multipart/form-data">'.format(
                url=reverse(self.tested_url_name, args=(self.profile.user.username,))
            ),
            self.test_page().content.decode("utf-8"),
        )

    def test_edit(self):
        """
        Проверка, что редактирование работает
        """
        self.login_test()

        data = {"first_name": "Vladimir", "phone": "100500", "city": "Калуга"}
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username,)),
            data
        )
        self.profile.refresh_from_db()

        self.assertEquals(self.profile.user.first_name, data["first_name"])
        self.assertEquals(self.profile.phone, data["phone"])
        self.assertEquals(self.profile.city, data["city"])

        return response

    def test_not_access_edit(self):
        """
        Проверка, что редактирование не доступно неавторизованным пользователям и происходит редирект
        на страницу авторизации
        """
        data = {"first_name": "New name", "city": "New city"}
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username,)),
            data
        )

        self.assertEquals(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_forbidden(self):
        """
        Проверка, что редактирование не доступно авторизованным пользователям, если это не их профиль
        """
        user = get_user_model().objects.create(username="some_user")
        user.set_password(self.user_raw_password)
        user.save()

        logged_in = self.client.login(username=user.username, password=self.user_raw_password)
        self.assertTrue(logged_in, f"not logged {user.username}")

        data = {"first_name": "New name", "city": "New city"}
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username,)),
            data
        )

        self.assertEquals(response.status_code, 403)

    def test_redirect_to_profile_after_edit(self):
        """
        Проверка, что после редактирования происходит редирект обратно в профиль
        """
        response = self.test_edit()
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse(self.tested_url_name, args=(self.profile.user.username,)))

    def test_upload_avatar(self):
        """
        Проверка, что загрузка аватара работает
        """
        self.login_test()

        avatar = SimpleUploadedFile(
            "me-30.jpg",
            open(os.path.join(os.path.dirname(__file__), "me-30.jpg"), mode="rb").read(),
            content_type="image/*"
        )

        data = {
            "first_name": "Vladimir",
            "avatar": avatar
        }
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username,)),
            data
        )
        self.profile.refresh_from_db()

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse(self.tested_url_name, args=(self.profile.user.username,)))
        self.assertIsNotNone(Avatar.objects.filter(profile=self.profile).first())
