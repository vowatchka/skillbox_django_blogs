from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Blog, BlogArticle


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ("title", "description")


class BlogArticleForm(forms.ModelForm):
    attachments = forms.FileField(label=_("Вложения"), required=False,
                                  widget=forms.ClearableFileInput(attrs={"multiple": True, "accept": "image/*"}))

    class Meta:
        model = BlogArticle
        fields = ("title", "content")


class UploadBlogArticlesForm(forms.Form):
    file = forms.FileField(label=_("Файл"), widget=forms.ClearableFileInput(attrs={"accept": ".csv"}))
