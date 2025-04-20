from django.contrib import admin

# Register your models here.
from .models import Unidad, Cama, Paciente, Servicio, MedicamentoEpicrisis, Medicamento 

admin.site.register(Unidad)
admin.site.register(Cama)
admin.site.register(Paciente)
admin.site.register(Servicio)
admin.site.register(MedicamentoEpicrisis)
admin.site.register(Medicamento)