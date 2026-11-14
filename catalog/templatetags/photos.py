from django import template

register = template.Library()

_KNOWN = {"cameras", "alarms", "locks", "lighting", "services"}


@register.simple_tag
def category_photo(slug: str) -> str:
    name = slug if slug in _KNOWN else "services"
    return f"photos/cat-{name}.jpg"
