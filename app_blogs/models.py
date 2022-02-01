import os

from django.db import models
from django.utils.translation import gettext_lazy as _

from app_auth.models import UserProfile


class Blog(models.Model):
    title = models.CharField(max_length=200, verbose_name=_("Название блога"))
    description = models.TextField(max_length=1000, blank=True, default="", verbose_name=_("Краткое описание"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, verbose_name=_("Автор блога"))

    def articles_count(self):
        return BlogArticle.objects.filter(blog=self).count()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name= _("блог")
        verbose_name_plural = _("блоги")


class BlogArticle(models.Model):
    title = models.CharField(max_length=200, verbose_name=_("Заголовок записи блога"))
    content = models.TextField(null=False, verbose_name=_("Содержимое записи"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    edit_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата последнего изменения"))
    blog = models.ForeignKey("Blog", on_delete=models.CASCADE, verbose_name=_("Блог"))

    def files_count(self):
        return File.objects.filter(blog_article=self).count()

    def short_content(self):
        return self.content[:100]

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = _("статья блога")
        verbose_name_plural = _("статьи блога")


class File(models.Model):
    file = models.FileField(upload_to="files/", verbose_name=_("Файл"))
    blog_article = models.ForeignKey("BlogArticle", on_delete=models.CASCADE, verbose_name=_("Статья блога"))

    def __str__(self):
        return os.path.basename(str(self.file))

    class Meta:
        verbose_name = _("файл")
        verbose_name_plural = _("файлы")
