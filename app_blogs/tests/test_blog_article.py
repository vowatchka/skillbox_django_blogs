import os

from django.core.files import File as DjangoFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import Blog, BlogArticle, File

from .utils import TestCaseMixin


class BlogArticleTestMixin(TestCaseMixin):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        blog = Blog.objects.create(
            title="Blog",
            description="Blog",
            profile=cls.profile
        )

        cls.blog_article = BlogArticle.objects.create(
            title="Article",
            content="Article content",
            blog=blog
        )

    def page_test(self):
        """
        Проверка, что страница находится по нужному адресу и использует правильный шаблон
        """
        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.tested_template)
        return response


class BlogArticleTest(BlogArticleTestMixin):
    tested_template = "blog-article.html"
    tested_url_name = "blog_article"

    def test_page(self):
        self.page_test()

    def test_has_not_access_on_page(self):
        """
        Проверка, что для неавторизованного пользователя ссылки на удаление и редактирование недоступны
        """
        response = self.page_test()

        self.not_access_in_html_test(
            response,
            r'<a href="{url}">Редактировать</a>'.format(
                url=reverse("edit_blog_article", args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id))
            )
        )
        self.not_access_in_html_test(
            response,
            r'<a href="{url}">Удалить</a>'.format(
                url=reverse("delete_blog_article", args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id))
            )
        )

    def test_authorized_user_has_not_access(self):
        """
        Проверка, что авторизованный пользователь не видит ссылки на удаление и редактирование
        не в своем статье блога
        """
        user = get_user_model().objects.create(username="some_user")

        user.set_password(self.user_raw_password)
        user.save()

        logged_in = self.client.login(username=user.username, password=self.user_raw_password)
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
                url=reverse("edit_blog_article", args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id))
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
                url=reverse("delete_blog_article", args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id))
            )
        )


class CreateBlogArticleTest(TestCaseMixin):
    tested_template = "create-blog-article.html"
    tested_url_name = "create_blog_article"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.blog = Blog.objects.create(
            title="Blog",
            description="Blog",
            profile=cls.profile
        )

    def test_page(self):
        """
        Проверка, что страница доступна по правильному адресу и использует правильный шаблон,
        но доступна только авторизованным пользователям
        """
        self.login_test()

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, self.tested_template)
        return response

    def test_not_access(self):
        """
        Проверка, что неавторизованные пользователи будут перенаправлены на страницу авторизации
        """
        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)))
        self.assertEquals(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_forbidden(self):
        """
        Проверка, что авторизованные пользователи не могут создавать статьи не в своих блогах
        """
        user = get_user_model().objects.create(username="some_user")
        user.set_password(self.user_raw_password)
        user.save()

        logged_in = self.client.login(username=user.username, password=self.user_raw_password)
        self.assertTrue(logged_in, f"not logged {user.username}")

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)))
        self.assertEquals(response.status_code, 403)

    def test_create(self):
        """
        Проверка, что создание статьи работает
        """
        self.login_test()

        data = {"title": "New Article", "content": "New Article Content"}
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)),
            data
        )

        blog_article = BlogArticle.objects.latest("id")

        self.assertEquals(blog_article.title, data["title"])
        self.assertEquals(blog_article.content, data["content"])

        return response, blog_article

    def test_redirect_to_article_after_create(self):
        """
        Проверка, что после создания статьи происходит редирект на ее страницу
        """
        response, blog_article = self.test_create()
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("blog_article", args=(self.profile.user.username, blog_article.blog.id, blog_article.id)))

    def test_upload_attachments(self):
        """
        Проверка, что добавление вложений работает
        """
        self.login_test()

        files_count = 10
        attachments = []

        for _ in range(files_count):
            attachments.append(
                SimpleUploadedFile(
                    "me-30.jpg",
                    open(os.path.join(os.path.dirname(__file__), "me-30.jpg"), mode="rb").read(),
                    content_type="image/*"
                )
            )

        data = {
            "title": "New Article",
            "content": "New Article Content",
            "attachments": attachments
        }
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username, self.blog.id)),
            data
        )

        blog_article = BlogArticle.objects.latest("id")

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("blog_article", args=(self.profile.user.username, blog_article.blog.id, blog_article.id)))
        self.assertEquals(blog_article.files_count(), files_count)
        self.assertEquals(File.objects.filter(blog_article=blog_article).count(), files_count)


class EditBlogArticleTest(BlogArticleTestMixin):
    tested_template = "edit-blog-article.html"
    tested_url_name = "edit_blog_article"

    def test_page(self):
        """
        Проверка, что страница доступна по правильному адресу и использует правильный шаблон,
        но доступна только авторизованным пользователям и если это их статья блога
        """
        self.login_test()
        self.page_test()

    def test_not_access(self):
        """
        Проверка, что неавторизованные пользователи будут перенаправлены на страницу авторизации
        """
        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)))
        self.assertEquals(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_forbidden(self):
        """
        Проверка, что авторизованные пользователи не могут редактировать чужие статьи блогов
        """
        user = get_user_model().objects.create(username="some_user")
        user.set_password(self.user_raw_password)
        user.save()

        logged_in = self.client.login(username=user.username, password=self.user_raw_password)
        self.assertTrue(logged_in, f"not logged {user.username}")

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)))
        self.assertEquals(response.status_code, 403)

    def test_edit(self):
        """
        Проверка, что редактирование работает
        """
        self.login_test()

        data = {"title": "new article", "content": "new content"}
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)),
            data
        )
        self.blog_article.refresh_from_db()

        self.assertEquals(self.blog_article.title, data["title"])
        self.assertEquals(self.blog_article.content, data["content"])

        return response

    def test_redirect_to_article_after_edit(self):
        """
        Проверка, что после редактирования происходит редирект обратно в статью блога
        """
        response = self.test_edit()
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("blog_article", args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)))

    def test_upload_attachments(self):
        """
        Проверка, что добавление вложений работает
        """
        self.login_test()

        files_count = 10
        attachments = []

        for _ in range(files_count):
            attachments.append(
                SimpleUploadedFile(
                    "me-30.jpg",
                    open(os.path.join(os.path.dirname(__file__), "me-30.jpg"), mode="rb").read(),
                    content_type="image/*"
                )
            )

        data = {
            "title": self.blog_article.title,
            "content": self.blog_article.content,
            "attachments": attachments
        }
        response = self.client.post(
            reverse(self.tested_url_name, args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)),
            data
        )
        self.blog_article.refresh_from_db()

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("blog_article", args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)))
        self.assertEquals(self.blog_article.files_count(), files_count)
        self.assertEquals(File.objects.filter(blog_article=self.blog_article).count(), files_count)


class DeleteBlogArticleTest(BlogArticleTestMixin):
    tested_url_name = "delete_blog_article"

    def test_page(self):
        """
        Проверка, что страница находится по правильному адресу, но доступна только авторизованным пользователям,
        если это их статья блога
        """
        self.login_test()

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)))

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("blog", args=(self.profile.user.username, self.blog_article.blog.id)))

        return response

    def test_not_access(self):
        """
        Проверка, что неавторизованные пользователи редиректятся на страницу авторизации
        """
        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)))

        self.assertEquals(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login"))

    def test_not_delete(self):
        """
        Проверка, что авторизованные пользователи не могут удалить не свою статью блога
        """
        user = get_user_model().objects.create(username="some_user")
        user.set_password(self.user_raw_password)
        user.save()

        logged_in = self.client.login(username=user.username, password=self.user_raw_password)
        self.assertTrue(logged_in, f"not logged {user.username}")

        response = self.client.get(reverse(self.tested_url_name, args=(self.profile.user.username, self.blog_article.blog.id, self.blog_article.id)))

        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, reverse("blog", args=(self.profile.user.username, self.blog_article.blog.id)))

        self.assertTrue(BlogArticle.objects.filter(id=self.blog_article.id).exists())

    def test_delete(self):
        """
        Проверка, что удаление работает, и не забыли настроить каскадное удаление вложений
        """
        count = 10
        for i in range(0, count):
            File.objects.create(
                file=DjangoFile(
                    open(os.path.join(os.path.dirname(__file__), "me-30.jpg"), mode="rb"),
                    "me-30.jpg"
                ),
                blog_article=self.blog_article
            )

        self.assertEquals(File.objects.filter(blog_article=self.blog_article).count(), count)

        self.test_page()
        self.assertEquals(File.objects.filter(blog_article=self.blog_article).count(), 0)
