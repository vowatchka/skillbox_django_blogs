from django.urls import path

from .views import AllBlogArticlesView, BlogView, BlogArticleView, CreateBlogView, CreateBlogArticleView, \
    EditBlogView, EditBlogArticleView, \
    delete_blog, delete_blog_article


urlpatterns = [
    path("", AllBlogArticlesView.as_view(), name="home"),
    path("<slug:username>/blog/create/", CreateBlogView.as_view(), name="create_blog"),
    path("<slug:username>/blog/<int:pk>/", BlogView.as_view(), name="blog"),
    path("<slug:username>/blog/<int:pk>/edit/", EditBlogView.as_view(), name="edit_blog"),
    path("<slug:username>/blog/<int:pk>/delete/", delete_blog, name="delete_blog"),
    path("<slug:username>/blog/<int:blogid>/article/create/", CreateBlogArticleView.as_view(), name="create_blog_article"),
    path("<slug:username>/blog/<int:blogid>/article/<int:pk>/", BlogArticleView.as_view(), name="blog_article"),
    path("<slug:username>/blog/<int:blogid>/article/<int:pk>/edit/", EditBlogArticleView.as_view(), name="edit_blog_article"),
    path("<slug:username>/blog/<int:blogid>/article/<int:pk>/delete/", delete_blog_article, name="delete_blog_article"),
]
