from django.contrib import admin
from .models import *

admin.site.register(Chat)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat', 'timestamp', 'is_read')
    list_select_related = ('user', 'chat') # ОБОВ'ЯЗКОВО для швидкості
    
    # Виводити по 20 повідомлень на сторінку
    list_per_page = 20 
    
    # Додай фільтри справа, щоб швидко знайти повідомлення від тролів
    list_filter = ('user', 'timestamp', 'chat')
    
    # Додай пошук за змістом повідомлення або юзером
    search_fields = ('content', 'user__username')