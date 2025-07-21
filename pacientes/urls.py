from django.urls import path
from . import views
from pacientes.views import obtener_datos_catalogo

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
    path('episodios/<int:episodio_id>/', views.detalle_episodio, name='detalle_episodio'),
    path('epicrisis/<int:epicrisis_id>/pdf/', views.exportar_epicrisis_pdf, name='exportar_epicrisis_pdf'),
    path('epicrisis/<int:epicrisis_id>/ver/', views.ver_epicrisis, name='ver_epicrisis'),
    path('interconsultas/', views.interconsultas_recibidas, name='interconsultas_recibidas'),
    path('interconsultas/<int:interconsulta_id>/responder/', views.responder_interconsulta, name='responder_interconsulta'),
    path('interconsultas/<int:interconsulta_id>/pdf/', views.interconsulta_pdf, name='interconsulta_pdf'),
    path('camas-disponibles/', views.camas_disponibles, name='camas_disponibles'),
    path('epicrisis/<int:epicrisis_id>/editar/', views.editar_epicrisis, name='editar_epicrisis'),
    path('pacientes/<int:paciente_id>/alta/', views.dar_de_alta_paciente, name='dar_de_alta_paciente'),
    path('antecedentes/<int:antecedente_id>/eliminar/', views.eliminar_antecedente, name='eliminar_antecedente'),
    path('buscar/', views.buscar_pacientes, name='buscar_pacientes'),
    path('estudios/', views.estudios, name='estudios'),
    path('ajax/cargar-opciones-medicamento/', views.cargar_opciones_medicamento, name='cargar_opciones_medicamento'),
    path('api/medicamento-catalogo/<int:pk>/', views.obtener_datos_catalogo, name='obtener_datos_catalogo'),
    path('api/buscar-paciente/', views.buscar_paciente_api, name='buscar_paciente_api'),
    path('api/plantillas/', views.obtener_plantillas, name='obtener_plantillas'),
    path('api/plantillas/guardar/', views.guardar_plantilla, name='guardar_plantilla'),
    path('api/pacientes/<int:paciente_id>/ultima-indicacion/', views.ultima_indicacion, name='ultima_indicacion'),
]
