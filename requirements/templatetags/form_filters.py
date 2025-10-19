from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"class": css})
    return field  # return unchanged if not a form field

@register.filter(name='attr')
def add_attr(field, arg):
    """Set a single HTML attribute on a form field: usage {{ field|attr:"name=value" }}"""
    if not isinstance(field, BoundField):
        return field
    try:
        key, value = str(arg).split('=', 1)
    except ValueError:
        return field
    return field.as_widget(attrs={key: value})

@register.filter(name='attrs')
def add_attrs(field, args_str):
    """
    Set multiple HTML attributes on a form field.
    Usage: {{ field|attrs:"class=... , list=kerala-locations" }} (comma-separated key=value pairs)
    """
    if not isinstance(field, BoundField):
        return field
    attrs = {}
    for pair in str(args_str).split(','):
        pair = pair.strip()
        if not pair:
            continue
        if '=' in pair:
            k, v = pair.split('=', 1)
            attrs[k.strip()] = v.strip()
    return field.as_widget(attrs=attrs)
