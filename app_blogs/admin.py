from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Blog, BlogArticle, File


class BlogArticlesInline(admin.StackedInline):
    model = BlogArticle
    extra = 0


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "articles_view")
    list_display, list_display_links = (("title", "profile", "created_at", "articles_view"),) * 2
    list_filter = ("profile__user__username", "created_at")
    inlines = (BlogArticlesInline,)

    def articles_view(self, obj):
        return obj.articles_count()

    articles_view.short_description = _("Кол-во записей в блоге")


@admin.register(BlogArticle)
class BlogArticleAdmin(admin.ModelAdmin):
    readonly_fields = ("created_at", "edit_at", "files_view")
    list_display, list_display_links = (("title", "blog", "author_view", "content_view", "created_at", "edit_at", "files_view"),) * 2
    list_filter = ("blog__title", "blog__profile__user__username", "created_at", "edit_at")

    def content_view(self, obj):
        return obj.short_content()

    def files_view(self, obj):
        return obj.files_count()

    def author_view(self, obj):
        return obj.blog.profile.user.username

    content_view.short_description = _("Содержимое записи")
    files_view.short_description = _("Кол-во файлов")
    author_view.short_description = _("Автор блога")


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    readonly_fields = ("blog_view",)
    list_display, list_display_links = (("file", "blog_view", "author_view", "blog_article"),) * 2
    list_filter = ("blog_article__blog__title", "blog_article__blog__profile__user__username", "blog_article__title")

    def blog_view(self, obj):
        return obj.blog_article.blog.title

    def author_view(self, obj):
        return obj.blog_article.blog.profile.user.username

    blog_view.short_description = _("Блог")
    author_view.short_description = _("Автор блога")
