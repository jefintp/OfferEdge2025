from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        # Try exact key, then stringified key for convenience
        return dictionary.get(key) if key in dictionary else dictionary.get(str(key))
    return None
