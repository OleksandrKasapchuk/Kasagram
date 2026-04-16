from django import forms
from auth_system.models import CustomUser


# Форма для редагування профілю
class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ("username", "first_name", "last_name", "email", "bio", "avatar")