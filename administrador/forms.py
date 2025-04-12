from django import forms
from django.contrib.auth.models import User
from administrador.models import PerfilUsuario


class CrearUsuarioForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'is_staff', 'is_active']



class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['especialidad', 'telefono']        