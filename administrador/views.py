from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import CrearUsuarioForm
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, get_object_or_404, redirect
from .models import PerfilUsuario
from .forms import PerfilUsuarioForm  # Crearemos este formulario a continuación

def crear_usuario(request):
    if request.method == 'POST':
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            nuevo_usuario = form.save()  # Guarda y devuelve el objeto User
            return redirect('editar', user_id=nuevo_usuario.id)  # Redirige a editar perfil
    else:
        form = CrearUsuarioForm()
    return render(request, 'administrador/crear_usuario.html', {'form': form})

    
def editar_perfil(request, user_id):
    perfil_usuario = get_object_or_404(PerfilUsuario, user__id=user_id)
    
    if request.method == 'POST':
        form = PerfilUsuarioForm(request.POST, instance=perfil_usuario)
        if form.is_valid():
            form.save()
            return redirect('listar')  # Cambia esto por la vista de éxito o perfil
    else:
        form = PerfilUsuarioForm(instance=perfil_usuario)

    return render(request, 'administrador/editar_perfil.html', {'form': form, 'perfil_usuario': perfil_usuario})


def menu_view(request):
    return render(request, 'administrador/menu.html')

def listar_usuarios(request):
    usuarios = User.objects.all()
    return render(request, 'administrador/listar.html', {'usuarios': usuarios})
    
    