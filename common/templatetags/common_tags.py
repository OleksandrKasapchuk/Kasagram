from django import template
from ..utils import format_date

register = template.Library()

@register.filter
def custom_date(value):
    format_date(value)