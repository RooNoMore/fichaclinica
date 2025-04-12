from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),  # Página principal
    path('camas/', views.lista_camas, name='lista_camas'),
    path('pacientes/nuevo/', views.nuevo_paciente, name='nuevo_paciente'),
    path('pacientes/<int:id>/', views.detalle_paciente, name='detalle_paciente'),  # Nueva ruta para detalles del paciente
    path('pacientes/<int:id>/exportar_pdf/', views.exportar_pdf, name='exportar_pdf'),
]
