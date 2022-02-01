from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import UserProfile, Avatar


@admin.register(UserProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display, list_display_links = (("user", "city", "phone"),) * 2
    list_filter = ("user", "city")


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display, list_display_links = (("avatar", "profile_view"),) * 2
    list_filter = ("profile__user__username",)

    def profile_view(self, obj):
        return obj.profile.user.username

    profile_view.short_description = _("Пользователь")
