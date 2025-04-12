from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User



class Unidad(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Paciente(models.Model):
    ficha = models.IntegerField(unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    diagnostico = models.CharField(max_length=200)
    cama = models.OneToOneField('Cama', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'Ficha {self.ficha} - {self.nombre}'
    
class Paciente(models.Model):
    ficha = models.IntegerField(unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fono = models.CharField(max_length=20, null=True, blank=True)
    domicilio = models.CharField(max_length=255, null=True, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    fecha_egreso = models.DateField(null=True, blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diagnostico = models.CharField(max_length=200, null=True, blank=True)
    unidad = models.ForeignKey(Unidad, on_delete=models.SET_NULL, null=True, blank=True)
    cama = models.OneToOneField('Cama', on_delete=models.SET_NULL, null=True, blank=True)

    def edad(self):
        from datetime import date
        if self.fecha_nacimiento:
            return date.today().year - self.fecha_nacimiento.year - (
                (date.today().month, date.today().day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None

    def __str__(self):
        return f'Ficha {self.ficha} - {self.nombre}'
    

class Cama(models.Model):
    numero = models.CharField()
    unidad = models.ForeignKey(Unidad, related_name='camas', on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Cama {self.numero}'
    

class Evolucion(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE, related_name='evoluciones')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contenido = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.fecha.strftime("%d-%m-%Y %H:%M")} - {self.autor}'    