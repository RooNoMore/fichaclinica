from django.contrib import admin

# Register your models here.
from .models import (
    Unidad,
    Cama,
    Paciente,
    Servicio,
    Medicamento,
    MedicamentoCatalogo,
    Via,
    Frecuencia,
    Solicitud,
)

admin.site.register(Unidad)
admin.site.register(Cama)
admin.site.register(Paciente)
admin.site.register(Servicio)
admin.site.register(Solicitud)


@admin.register(Via)
class ViaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Frecuencia)
class FrecuenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

from django.utils.html import format_html

@admin.register(MedicamentoCatalogo)
class MedicamentoCatalogoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'mostrar_vias', 'mostrar_frecuencias')

    def mostrar_vias(self, obj):
        return ", ".join([str(v) for v in obj.via.all()])

    mostrar_vias.short_description = 'Vías'

    def mostrar_frecuencias(self, obj):
        return ", ".join([str(f) for f in obj.frecuencia.all()])

    mostrar_frecuencias.short_description = 'Frecuencias'

@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'episodio', 'dosis', 'frecuencia', 'via')
    search_fields = ('nombre', 'dosis', 'frecuencia', 'via')
    list_filter = ('via', 'frecuencia')