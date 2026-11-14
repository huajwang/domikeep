from django import template

from catalog.pricing import format_cad

register = template.Library()


@register.filter
def cad(cents) -> str:
    return format_cad(cents)
