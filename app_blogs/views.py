from _csv import reader

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView

from .models import BlogArticle, Blog, File
from .forms import BlogForm, BlogArticleForm, UploadBlogArticlesForm
from .access import UserAccessMixin

from app_auth.models import UserProfile


def save_article_attachments(request, article):
    attachments = request.FILES.getlist("attachments")
    for att in attachments:
        file = File(file=att, blog_article=article)
        file.save()


@login_required
def delete_blog(request, username, pk):
    if request.method == "GET":
        Blog.objects.filter(id=pk, profile__user__username=request.user.username).delete()

        return HttpResponseRedirect(reverse("user_profile", args=(username,)))
    return HttpResponseRedirect(reverse("blog", args=(username, pk)))


@login_required()
def delete_blog_article(request, username, blogid, pk):
    if request.method == "GET":
        BlogArticle.objects.filter(id=pk, blog__id=blogid, blog__profile__user__username=request.user.username).delete()

        return HttpResponseRedirect(reverse("blog", args=(username, blogid)))
    return HttpResponseRedirect(reverse("blog_article", args=(username, blogid, pk)))


class BlogDetailMixin(DetailView):
    model = Blog
    context_object_name = "blog"
    slug_field = "profile__user__username"
    slug_url_kwarg = "username"
    query_pk_and_slug = True


class BlogArticleDetailMixin(DetailView):
    model = BlogArticle
    context_object_name = "blog_article"
    slug_field = ("blog__profile__user__username", "blog__id")
    slug_url_kwarg = ("username", "blogid")
    query_pk_and_slug = True


class AllBlogArticlesView(ListView):
    template_name = "all-blog-articles.html"
    model = BlogArticle
    context_object_name = "blog_articles"

    def get_queryset(self):
        return BlogArticle.objects.order_by("-created_at").all()


class BlogView(BlogDetailMixin):
    template_name = "blog.html"

    def ctx_blog_articles(self):
        return BlogArticle.objects.filter(blog=self.get_object()).order_by("-created_at").all()

    def get(self, request, *args, **kwargs):
        response = super().get(request)
        response.context_data["blog_articles"] = self.ctx_blog_articles()
        response.context_data["form"] = UploadBlogArticlesForm()
        return response

    def post(self, request, *args, **kwargs):
        blog = self.get_object()
        form = UploadBlogArticlesForm(request.POST, request.FILES)

        if form.is_valid():
            file_data = form.cleaned_data["file"].read()

            try:
                records = file_data.decode("utf-8").split("\n")
            except Exception as ex:
                records = file_data.decode("windows-1251").split("\n")

            csv_reader = reader(records, delimiter=";", quotechar='"')
            for row in csv_reader:
                try:
                    BlogArticle.objects.create(title=row[0], content=row[1], blog=blog)
                except Exception as ex:
                    pass

            return HttpResponseRedirect(reverse("blog", args=(blog.profile.user.username, blog.id)))

        ctx = dict()
        ctx["blog_articles"] = self.ctx_blog_articles()
        ctx["form"] = form
        return render(request, self.template_name, ctx)


class BlogArticleView(BlogArticleDetailMixin):
    template_name = "blog-article.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.context_data["attachments"] = File.objects.filter(blog_article=self.get_object()).all()
        return response


class CreateBlogView(UserAccessMixin, TemplateView):
    template_name = "create-blog.html"

    def get(self, request, username, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.context_data["username"] = username
        response.context_data["form"] = BlogForm()
        return response

    def post(self, request, username, *args, **kwargs):
        form = BlogForm(request.POST)

        if form.is_valid():
            new_blog = form.save(commit=False)

            new_blog.profile = UserProfile.objects.get(user__username=username)
            new_blog.save()

            return HttpResponseRedirect(reverse("blog", args=(username, new_blog.id)))

        return render(request, self.template_name, {"form": form, "username": username})


class CreateBlogArticleView(UserAccessMixin, TemplateView):
    template_name = "create-blog-article.html"

    def get(self, request, username, blogid, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.context_data["username"] = username
        response.context_data["blogid"] = blogid
        response.context_data["form"] = BlogArticleForm()
        return response

    def post(self, request, username, blogid, *args, **kwargs):
        form = BlogArticleForm(request.POST, request.FILES)

        if form.is_valid():
            article = form.save(commit=False)

            article.blog = Blog.objects.get(id=blogid, profile__user__username=username)
            article.save()

            save_article_attachments(request, article)

            return HttpResponseRedirect(reverse("blog_article", args=(username, blogid, article.id)))

        return render(request, self.template_name, {"form": form, "username": username, "blogid": blogid})


class EditBlogView(UserAccessMixin, BlogDetailMixin):
    template_name = "edit-blog.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.context_data["form"] = BlogForm(instance=self.get_object())
        return response

    def post(self, request, *args, **kwargs):
        blog = self.get_object()
        form = BlogForm(request.POST, instance=blog)

        if form.is_valid():
            form.save()

            return HttpResponseRedirect(reverse("blog", args=(blog.profile.user.username, blog.id)))

        ctx = dict({"form": form})
        ctx[self.context_object_name] = blog
        return render(request, self.template_name, ctx)


class EditBlogArticleView(UserAccessMixin, BlogArticleDetailMixin):
    template_name = "edit-blog-article.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.context_data["form"] = BlogArticleForm(instance=self.get_object())
        return response

    def post(self, request, *args, **kwargs):
        article = self.get_object()
        form = BlogArticleForm(request.POST, request.FILES, instance=article)

        if form.is_valid():
            form.save()
            save_article_attachments(request, article)

            return HttpResponseRedirect(reverse("blog_article",
                                                args=(article.blog.profile.user.username, article.blog.id, article.id)))

        ctx = dict({"form": form})
        ctx[self.context_object_name] = article
        return render(request, self.template_name, ctx)
