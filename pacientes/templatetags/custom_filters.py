
from django import template

register = template.Library()

@register.filter(name='dictkey')
def dictkey(value, key):
    """Devuelve el valor asociado con 'key' en un diccionario."""
    if isinstance(value, dict):
        return value.get(key, None)
    return None

@register.filter
def get_unidad_nombre(unidades, unidad_id):
    for unidad in unidades:
        if unidad.id == unidad_id:
            return unidad.nombre
    return 'Unidad no encontrada'

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})