from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

# Форма для реєстрації
class MyRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "bio")