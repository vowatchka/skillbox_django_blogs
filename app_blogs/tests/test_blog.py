from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Blog, BlogArticle

from .utils import TestCaseMixin


class BlogTestMixin(TestCaseMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.blog = Blog.objects.create(
            title="Blog",
            description="Blog",
            profile=cls.profile
        )

    def page_test(self):
        """
        Проверка, что страница находится по нужному адресу и использует правильный шаблон
        """
        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.tested_template)
        return response


class BlogTest(BlogTestMixin):
    tested_template = "blog.html"
    tested_url_name = "blog"

    articles_context_name = "blog_articles"

    def test_page(self):
        self.page_test()

    def test_articles_context(self):
        """
        Проверка, что на странице блогов вообще возможен вывод статей
        """
        response = self.page_test()
        self.assertTrue(self.articles_context_name in response.context)

    def test_no_articles(self):
        """
        Проверка, что статей нет на странице
        """
        response = self.page_test()
        self.assertEquals(len(response.context[self.articles_context_name]), 0)

    def test_articles(self):
        """
        Проверка, что статьи есть на странице
        """
        count = 10
        for i in range(0, count):
            BlogArticle.objects.create(
                title=f"Article {i}",
                content=f"Article {i} content",
                blog=self.blog
            )

        response = self.page_test()
        self.assertEquals(len(response.context[self.articles_context_name]), self.blog.articles_count())

    def test_has_not_access_on_page(self):
        """
        Проверка, что для неавторизованного пользователя ссылки на удаление и редактирование недоступны
        """
        response = self.page_test()

        self.not_access_in_html_test(
            response,
            r'<a href="{url}">Редактировать</a>'.format(
                url=reverse("edit_blog", args=(self.profile.user.username, self.blog.id))
            )
        )
        self.not_access_in_html_test(
            response,
            r'<a href="{url}">Удалить</a>'.format(
                url=reverse("delete_blog", args=(self.profile.user.username, self.blog.id))
            )
        )

    def test_authorized_user_has_not_access(self):
        """
        Проверка, что авторизованный пользователь не видит ссылки на удаление и редактирование
        не в своем блоге
        """
        user = get_user_model().objects.create(
            username="some_user"
        )

        password = "bobah12345"
        user.set_password(password)
        user.save()

        logged_in = self.client.login(username=user.username, password=password)
        self.assertTrue(logged_in, f"not logged {user.username}")

        self.test_has_not_access_on_page()

    def test_can_edit(self):
        """
        Проверка, что для авторизованного пользователя ссылка на редактирование доступна
        """
        self.login_test()

        self.has_access_in_html_test(
            self.page_test(),
            r'<a href="{url}">Редактировать</a>'.format(
                url=reverse("edit_blog", args=(self.profile.user.username, self.blog.id))
            )
        )

    def test_can_delete(self):
        """
        Проверка, что для авторизованного пользователя ссылка на удаление доступна
        """
        self.login_test()

        self.has_access_in_html_test(
            self.page_test(),
            r'<a href="{url}">Удалить</a>'.format(
                url=reverse("delete_blog", args=(self.profile.user.username, self.blog.id))
            )
        )


class CreateBlogTest(TestCaseMixin):
    tested_template = "create-blog.html"
    tested_url_name = "create_blog"

    def test_page(self):
        """
        Проверка, что страница доступна по правильному адресу и использует правильный шаблон,
        но доступна только авторизованным пользователям
        """
        self.login_test()

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username,)))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.tested_template)
        return response

    def test_not_access(self):
        """
        Проверка, что неавторизованные пользователи будут перенаправлены на страницу авторизации
        """
        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username,)))
        self.assertEquals(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_forbidden(self):
        """
        Проверка, что авторизованные пользователи не могут создавать блоги от чужого имени
        """
        user = get_user_model().objects.create(
            username="some_user"
        )
        user.set_password(self.user_raw_password)
        user.save()

        logged_in = self.client.login(username=user.username, password=self.user_raw_password)
        self.assertTrue(logged_in, f"not logged {user.username}")

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username,)))
        self.assertEquals(response.status_code, 403)

    def test_create(self):
        """
        Проверка, что создание блога работает
        """
        self.login_test()

        data = {"title": "New Blog", "description": "New Blog Description"}
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username,)),
            data
        )
        blog = Blog.objects.latest("id")

        self.assertEquals(blog.title, data["title"])
        self.assertEquals(blog.description, data["description"])

        return response, blog

    def test_redirect_to_blog_after_create(self):
        """
        Проверка, что после создания блога происходит редирект в блог
        """
        response, blog = self.test_create()
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("blog", args=(blog.profile.user.username, blog.id)))


class EditBlogTest(BlogTestMixin):
    tested_template = "edit-blog.html"
    tested_url_name = "edit_blog"

    def test_page(self):
        """
        Проверка, что страница доступна по правильному адресу и использует правильный шаблон,
        но доступна только авторизованным пользователям и если это их блог
        """
        self.login_test()
        self.page_test()

    def test_not_access(self):
        """
        Проверка, что неавторизованные пользователи будут перенаправлены на страницу авторизации
        """
        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)))
        self.assertEquals(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_forbidden(self):
        """
        Проверка, что авторизованные пользователи не могут редактировать чужие блоги
        """
        user = get_user_model().objects.create(
            username="some_user"
        )
        user.set_password(self.user_raw_password)
        user.save()

        logged_in = self.client.login(username=user.username, password=self.user_raw_password)
        self.assertTrue(logged_in, f"not logged {user.username}")

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)))
        self.assertEquals(response.status_code, 403)

    def test_edit(self):
        """
        Проверка, что редактирование работает
        """
        self.login_test()

        data = {"title": "new title", "description": "new description"}
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)),
            data
        )
        self.blog.refresh_from_db()

        self.assertEquals(self.blog.title, data["title"])
        self.assertEquals(self.blog.description, data["description"])

        return response

    def test_redirect_to_blog_after_edit(self):
        """
        Проверка, что после редактирования происходит редирект обратно в блог
        """
        response = self.test_edit()
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("blog", args=(self.profile.user.username, self.blog.id)))


class DeleteBlogTest(BlogTestMixin):
    tested_url_name = "delete_blog"

    def test_page(self):
        """
        Проверка, что страница находится по правильному адресу, но доступна только авторизованным пользователям,
        если это их блог
        """
        self.login_test()

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)))

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("user_profile", args=(self.profile.user.username,)))

        return response

    def test_not_access(self):
        """
        Проверка, что неавторизованные пользователи редиректятся на страницу авторизации
        """
        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)))

        self.assertEquals(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_not_delete(self):
        """
        Проверка, что авторизованные пользователи не могут удалить не свой блог
        """
        user = get_user_model().objects.create(username="some_user")
        user.set_password(self.user_raw_password)
        user.save()

        logged_in = self.client.login(username=user.username, password=self.user_raw_password)
        self.assertTrue(logged_in, f"not logged {user.username}")

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)))

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("user_profile", args=(self.profile.user.username,)))

        self.assertTrue(Blog.objects.filter(id=self.blog.id).exists())

    def test_delete(self):
        """
        Проверка, что удаление работает, и не забыли настроить кскадное уделение статей
        """
        count = 10
        for i in range(0, count):
            BlogArticle.objects.create(
                title=f"Article {i}",
                content=f"Article {i} content",
                blog=self.blog
            )

        self.assertEquals(BlogArticle.objects.filter(blog=self.blog).count(), count)

        self.test_page()
        self.assertEquals(BlogArticle.objects.filter(blog=self.blog).count(), 0)
