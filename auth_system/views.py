from django.contrib.auth import login
from chat.models import *
from .models import *
from django.views.generic import CreateView
from .forms import MyRegisterForm


class RegisterView(CreateView):
    form_class = MyRegisterForm
    template_name = "form.html"
    success_url = '/'

    def form_valid(self, form):
        valid = super().form_valid(form)
        login(self.request, self.object)
        return valid