

from django import template

register = template.Library()

@register.filter(name='dictkey')
def dictkey(value, key):
    """Devuelve el valor asociado con 'key' en un diccionario."""
    if isinstance(value, dict):
        return value.get(key, None)
    return None