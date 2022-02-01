from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AppBlogsConfig(AppConfig):
    name = 'app_blogs'
    verbose_name = _("Блоги")
