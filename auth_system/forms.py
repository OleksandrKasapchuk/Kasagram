from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser

# Форма для реєстрації
class MyRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "bio")

# Форма для редагування профілю
class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "bio", "avatar")