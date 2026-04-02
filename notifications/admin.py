from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    # Відображаємо основну інформацію
    list_display = ('actor', 'notification_text', 'user', 'created_at', 'target', 'is_read')
    
    # Оптимізація запитів: підтягуємо все за один раз
    list_select_related = ('user', 'actor', 'target')
    
    # Пагінація, щоб не вантажити 1000 нотіфікацій зразу
    list_per_page = 20
    
    # Фільтри для швидкого пошуку
    list_filter = ('is_read', 'created_at')
    
    # Пошук по іменах користувачів
    search_fields = ('user__username', 'actor__username', 'type')

    # Кастомне поле, щоб бачити текст сповіщення прямо в списку
    def notification_text(self, obj):
        return f"{obj.actor.username}{obj.get_message()}"
    notification_text.short_description = 'Content'