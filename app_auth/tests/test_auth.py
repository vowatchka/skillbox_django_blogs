from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import UserProfile

from app_blogs.models import Blog
from app_blogs.tests.utils import TestCaseMixin


class RegistrationTest(TestCase):
    tested_template = "register.html"
    tested_url_name = "register"

    username = "bloger"
    user_raw_password = "bobah12345"

    def test_page(self):
        """
        Проверка, что страница находится по нужному адресу и использует правильный шаблон
        """
        response = self.client.get(reverse(self.tested_url_name))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.tested_template)

        return response

    def test_registration(self):
        """
        Проверка что регистрация работает
        """
        data = {
            "username": self.username, "password1": self.user_raw_password, "password2": self.user_raw_password,
            "phone": "123", "city": "Калуга"
        }

        response = self.client.post(reverse(self.tested_url_name), data)

        qs = UserProfile.objects.filter(user__username=data["username"])

        self.assertTrue(qs.exists())

        profile = qs.first()
        self.assertEquals(profile.phone, data["phone"])
        self.assertEquals(profile.city, data["city"])

        return response

    def test_login_and_redirect_after_registration(self):
        """
        Проверка, что после успешной регистрации происходит автоматическая авторизация и редирект на главную страницу
        """
        response = self.test_registration()

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("home"))

        self.assertTrue(get_user_model().objects.filter(username=self.username).first().is_authenticated)

    def test_login_link(self):
        """
        Проверка, что на странице регистрации есть ссылка на страницу логина
        """
        response = self.test_page()

        self.assertContains(
            response,
            r'<a href="{url}">Войти</>'.format(
                url=reverse("login")
            ),
            html=True
        )


class LoginTest(TestCaseMixin):
    tested_template = "login.html"
    tested_url_name = "login"

    def test_page(self):
        """
        Проверка, что страница находится по нужному адресу и использует правильный шаблон
        """
        response = self.client.get(reverse(self.tested_url_name))

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.tested_template)

        return response

    def test_login(self):
        """
        Проверка логина
        """
        self.login_test()
        self.assertTrue(self.profile.user.is_authenticated)

    def test_next_page_in_context(self):
        """
        Проверка, что адрес редиректа рендерится в шаблон
        """
        redirect_url = reverse("user_profile", args=(self.profile.user.username,))

        response = self.client.get(reverse(self.tested_url_name) + "?next=" + redirect_url)

        self.assertTrue("next_page" in response.context)
        self.assertEquals(response.context["next_page"], redirect_url)

        return response

    def test_redirection_to_home_after_login(self):
        """
        Проверка, что редирект выполняется на главную страницу, если в GET-параметрах нет next
        """
        data = {"username": self.username, "password": self.user_raw_password}

        response = self.client.post(reverse(self.tested_url_name), data)

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("home"))

    def test_redirection_to_next_page_after_login(self):
        """
        Проверка, что редирект выполняется на страницу, указанную в GET-параметре next
        """
        redirect_url = reverse("user_profile", args=(self.profile.user.username,))
        data = {"username": self.username, "password": self.user_raw_password}

        response = self.client.post(
            reverse(self.tested_url_name) + "?next=" + redirect_url,
            data
        )

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, redirect_url)

    def test_registration_link(self):
        """
        Проверка, что на странице логина есть ссылка на страницу регистрации
        """
        response = self.test_page()

        self.assertContains(
            response,
            r'<a href="{url}">Регистрация</>'.format(
                url=reverse("register")
            ),
            html=True
        )


class LogoutTest(TestCaseMixin):
    tested_template = "logout.html"
    tested_url_name = "logout"

    def test_page(self):
        """
        Проверка, что страница находится по нужному адресу и использует правильный шаблон
        """
        response = self.client.get(reverse(self.tested_url_name))

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.tested_template)

        return response

    def test_logout(self):
        """
        Проверка логаута
        """
        self.test_page()

        blog = Blog.objects.create(
            title="Blog",
            profile=self.profile
        )

        response = self.client.get(reverse("edit_blog", args=(self.profile.user.username, blog.id)))
        self.assertEquals(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_home_link(self):
        """
        Проверка, что на странице логаута есть ссылка на главную сьраницу
        """
        response = self.test_page()

        self.assertContains(
            response,
            r'<a href="{url}">Главная</a>'.format(
                url=reverse("home")
            ),
            html=True
        )
