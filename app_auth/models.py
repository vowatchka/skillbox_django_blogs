import os
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Телефон"))
    city = models.CharField(max_length=100, blank=True, verbose_name=_("Город"))
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, verbose_name=_("Пользователь"))

    def __str__(self):
        return str(self.user)

    class Meta:
        verbose_name = _("профиль пользователя")
        verbose_name_plural = _("профили пользователей")


class Avatar(models.Model):
    avatar = models.FileField(upload_to="files/", verbose_name=_("Аватар"))
    profile = models.OneToOneField(UserProfile, default=None, on_delete=models.CASCADE, verbose_name=_("Пользователь"))

    def __str__(self):
        return os.path.basename(str(self.avatar))

    class Meta:
        verbose_name = _("аватар")
        verbose_name_plural = _("аватары")
