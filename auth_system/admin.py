from django.contrib import admin
from .models import *


@admin.register(CustomUser)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'is_online', 'last_seen')

    list_per_page = 20 

admin.site.register(Subscription)