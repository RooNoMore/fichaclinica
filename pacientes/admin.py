from django.contrib import admin

# Register your models here.
from .models import Unidad, Cama, Paciente

admin.site.register(Unidad)
admin.site.register(Cama)
admin.site.register(Paciente)
