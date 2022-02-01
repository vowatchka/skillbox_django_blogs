from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, DetailView

from app_blogs.models import Blog
from app_blogs.access import has_access

from .forms import RegisterForm, ProfileForm
from .models import UserProfile, Avatar


class RegisterView(TemplateView):
    template_name = "register.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.context_data["reg_form"] = RegisterForm()
        return response

    def post(self, request, *args, **kwargs):
        form = RegisterForm(request.POST)

        if form.is_valid():
            form_user = form.save()

            username = form.cleaned_data.get("username")
            raw_pass = form.cleaned_data.get("password1")

            user = authenticate(username=username, password=raw_pass)
            login(request, user)

            UserProfile.objects.create(
                user=form_user,
                phone=form.cleaned_data.get("phone", ""),
                city=form.cleaned_data.get("city", "")
            )

            return redirect("/")
        else:
            return render(request, self.template_name, {"reg_form": form})


class Login(LoginView):
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        next = request.GET.get("next")
        if next:
            response.context_data["next_page"] = next
        else:
            response.context_data["next_page"] = "/"
        return response


class Logout(LogoutView):
    template_name = "logout.html"


class UserProfileDetailMixin(DetailView):
    model = UserProfile
    context_object_name = "user_profile"
    slug_field = "user__username"
    slug_url_kwarg = "username"


class UserProfileView(UserProfileDetailMixin, DetailView):
    template_name = "user-profile.html"

    def init_form(self, request):
        profile = self.get_object()

        args = []
        if request.POST:
            args.append(request.POST)
        if request.FILES:
            args.append(request.FILES)

        return ProfileForm(*args, instance=profile.user, phone=profile.phone, city=profile.city)

    def ctx_avatar(self):
        return Avatar.objects.filter(profile=self.get_object()).first()

    def ctx_blogs(self):
        return Blog.objects.filter(profile=self.get_object()).order_by("-created_at").all()

    def get(self, request, *args, **kwargs):
        response = super().get(request)

        response.context_data["avatar"] = self.ctx_avatar()
        response.context_data["blogs"] = self.ctx_blogs()
        response.context_data["form"] = self.init_form(request)
        return response

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        if not has_access(request):
            raise PermissionDenied()

        form = self.init_form(request)

        if form.is_valid():
            form.save()

            profile = self.get_object()
            profile.phone = form.cleaned_data.get("phone", "")
            profile.city = form.cleaned_data.get("city", "")
            profile.save()

            if form.cleaned_data["avatar"]:
                Avatar.objects.update_or_create(profile=profile, defaults={"avatar": form.cleaned_data["avatar"]})

            return HttpResponseRedirect(reverse("user_profile", args=(profile.user.username, )))

        ctx = dict()
        ctx["avatar"] = self.ctx_avatar()
        ctx["blogs"] = self.ctx_blogs()
        ctx["form"] = self.init_form(request)
        return render(request, self.template_name, ctx)
