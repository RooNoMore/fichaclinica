from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfilusuario')
    cargo = models.CharField(max_length=100, blank=True, null=True)
    servicio = models.ForeignKey('pacientes.Servicio', on_delete=models.SET_NULL, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        nombre = self.first_name or self.user.first_name or "Nombre"
        apellido = self.last_name or self.user.last_name or "Apellido"
        rol = self.cargo or "Cargo"
        return f"{nombre} {apellido} - {rol} - {self.servicio}"

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    instance.perfilusuario.save()