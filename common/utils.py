from django.utils import timezone
import datetime

def format_date(value):
    if not value:
        return ""
    
    now = timezone.now()
    # Якщо сьогодні — показуємо тільки час (14:30)
    if value.date() == now.date():
        return value.strftime("%H:%M")
    
    # Якщо на цьому тижні (останні 7 днів) — показуємо день тижня (Mon, Tue...)
    if now - value < datetime.timedelta(days=7):
        return value.strftime("%a") # Пн, Вт... (залежить від мови системи)
    
    # Якщо раніше — показуємо дату (25 Mar)
    return value.strftime("%d %b")