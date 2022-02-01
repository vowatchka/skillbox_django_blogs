from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import RegisterView, Login, Logout, UserProfileView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", Login.as_view(), name="login"),
    path("logout/", Logout.as_view(), name="logout"),
    path("<slug:username>/", UserProfileView.as_view(), name="user_profile"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
