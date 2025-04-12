
from django.urls import path
from . import views

urlpatterns = [
    # path('editar_perfil/<int:user_id>/', views.editar_perfil, name='editar_perfil'),
    path('crear/', views.crear_usuario, name='crear'),
    path('menu/', views.menu_view, name='menu'),  # Ruta para menu.html
    # path('perfil_exito/', views.perfil_exito, name='perfil_exito'),  # Ruta para la vista de éxito
    path('listar/', views.listar_usuarios, name='listar'),  # Ruta para listar usuarios
    path('perfil/<int:user_id>/editar/', views.editar_perfil, name='editar'),  # Ruta para editar el perfil
]