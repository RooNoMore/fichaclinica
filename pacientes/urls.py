from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),  # Página principal
    path('camas/', views.lista_camas, name='lista_camas'),
    path('pacientes/nuevo/', views.nuevo_paciente, name='nuevo_paciente'),
    path('pacientes/<int:paciente_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('pacientes/<int:paciente_id>/exportar_pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('pacientes/<int:paciente_id>/interconsulta/', views.crear_interconsulta, name='crear_interconsulta'),
    path('pacientes/<int:paciente_id>/examenes/', views.solicitar_examenes, name='solicitar_examenes'),
    path('pacientes/<int:paciente_id>/receta/', views.crear_receta, name='crear_receta'),
    path('pacientes/<int:paciente_id>/epicrisis/nueva/', views.crear_epicrisis, name='crear_epicrisis'),
    path('epicrisis/<int:epicrisis_id>/pdf/', views.exportar_epicrisis_pdf, name='exportar_epicrisis_pdf'),
    path('interconsultas/', views.interconsultas_recibidas, name='interconsultas_recibidas'),
    path('interconsultas/<int:interconsulta_id>/responder/', views.responder_interconsulta, name='responder_interconsulta'),
    path('camas-disponibles/', views.camas_disponibles, name='camas_disponibles'),

]