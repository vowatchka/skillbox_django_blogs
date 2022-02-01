from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class RegisterForm(UserCreationForm):
    phone = forms.CharField(max_length=20, required=False, label=_("Телефон"))
    city = forms.CharField(max_length=100, required=False, label=_("Город"))

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "phone", "city", "password1", "password2")


class ProfileForm(forms.ModelForm):
    avatar = forms.FileField(label=_("Аватарка"), required=False, widget=forms.ClearableFileInput(attrs={"accept": "image/*"}))
    phone = forms.CharField(max_length=20, required=False, label=_("Телефон"))
    city = forms.CharField(max_length=100, required=False, label=_("Город"))

    def __init__(self, *args, **kwargs):
        phone = kwargs.pop("phone", None)
        city = kwargs.pop("city", None)

        super().__init__(*args, **kwargs)

        if phone is not None:
            self.fields["phone"].initial = phone
        if city is not None:
            self.fields["city"].initial = city

    class Meta:
        model = User
        fields = ("avatar", "first_name", "last_name", "email", "phone", "city")
