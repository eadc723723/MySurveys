# custom_filters.py
from django import template

register = template.Library()

@register.filter(name='stars')
def stars(value):
    return range(value)

@register.filter
def stars(value):
    try:
        value = int(value)
        return "★" * value + "☆" * (5 - value)
    except (TypeError, ValueError):
        return ""
