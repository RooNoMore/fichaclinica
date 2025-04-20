from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from administrador.models import PerfilUsuario



class Unidad(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

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
    
    def dar_de_alta(self):
        self.hospitalizado = False
        self.fecha_alta = timezone.now()

        # Desocupar la cama si tiene una asignada
        if self.cama:
            self.cama.disponible = True
            self.cama.save()
            self.cama = None  # Quitar la cama del paciente

        self.save()

        
class Cama(models.Model):
    numero = models.CharField()
    unidad = models.ForeignKey(Unidad, related_name='camas', on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Cama {self.numero}'
    

class Evolucion(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE, related_name='evoluciones')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contenido = models.TextField()
    plan_indicaciones = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        nombre_autor = f'{self.autor.first_name} {self.autor.last_name.split()[0]} - {self.autor.perfilusuario.cargo}' if self.autor else 'Autor desconocido'
        return f'{self.fecha.strftime("%d-%m-%Y %H:%M")} - {nombre_autor}'

# PARA LAS INTERCONSULTAS

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Interconsulta(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE, related_name='interconsultas')
    solicitante = models.ForeignKey('administrador.PerfilUsuario', on_delete=models.PROTECT, related_name='interconsultas_realizadas')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    servicio_destino = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name='interconsultas_recibidas')
    motivo = models.TextField()
    respuesta = models.TextField(blank=True, null=True)
    atendido = models.BooleanField(default=False)
    fecha_respuesta = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Interconsulta a {self.servicio_destino} - {self.paciente.nombre} solicitada por {self.solicitante}"




class SolicitudExamen(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE, related_name='solicitudes_examenes')
    solicitante = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='examenes_solicitados')
    tipo_examen = models.CharField(max_length=100)
    indicaciones = models.TextField(blank=True, null=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_examen} solicitado por {self.solicitante} para {self.paciente}"


class Receta(models.Model):
    paciente = models.ForeignKey('Paciente', on_delete=models.CASCADE, related_name='recetas')
    medico = models.ForeignKey(PerfilUsuario, on_delete=models.PROTECT, related_name='recetas_emitidas')
    medicamento = models.CharField(max_length=100)
    dosis = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=50)
    duracion = models.CharField(max_length=50)
    indicaciones_extra = models.TextField(blank=True, null=True)
    fecha_receta = models.DateTimeField(auto_now_add=True)    


class Epicrisis(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    diagnostico_egreso = models.TextField()
    comentario_evolucion = models.TextField()
    indicaciones_generales = models.TextField(blank=True)
    indicaciones_controles = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    finalizado = models.BooleanField(default=False)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Epicrisis de {self.paciente.nombre} - {self.fecha_creacion.strftime('%d/%m/%Y')}"



class Medicamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class MedicamentoEpicrisis(models.Model):
    epicrisis = models.ForeignKey(Epicrisis, related_name='medicamentos_indicados', on_delete=models.CASCADE)
    medicamento = models.ForeignKey(Medicamento, on_delete=models.PROTECT)
    frecuencia = models.CharField(max_length=100)
    duracion = models.CharField(max_length=100)
    via = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.medicamento.nombre} - {self.frecuencia}, {self.duracion}, {self.via}"


        