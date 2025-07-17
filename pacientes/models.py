from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from administrador.models import PerfilUsuario
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

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
    fecha_egreso = models.DateTimeField(null=True, blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    diagnostico = models.CharField(max_length=200, null=True, blank=True)
    unidad = models.ForeignKey(Unidad, on_delete=models.SET_NULL, null=True, blank=True)
    cama = models.OneToOneField('Cama', on_delete=models.SET_NULL, null=True, blank=True)
    hospitalizado = models.BooleanField(default=True)

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
        self.fecha_egreso = timezone.now()

        episodio_activo = self.episodios.filter(fecha_egreso__isnull=True).first()
        if episodio_activo:
            episodio_activo.fecha_egreso = timezone.now()
            episodio_activo.finalizado = True
            episodio_activo.cama = None
            episodio_activo.save()

        # Desocupar la cama si tiene una asignada
        if self.cama:
            self.cama.disponible = True
            self.cama.save()
            self.cama = None  # Quitar la cama del paciente

        self.save()


# models.py

class Episodio(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="episodios")
    fecha_ingreso = models.DateTimeField(default=timezone.now)
    fecha_egreso = models.DateTimeField(null=True, blank=True)
    cama = models.OneToOneField('Cama', on_delete=models.SET_NULL, null=True, blank=True)
    motivo_ingreso = models.TextField(blank=True)
    finalizado = models.BooleanField(default=False)

    def __str__(self):
        return f"Episodio de {self.paciente} el {self.fecha_ingreso.strftime('%d-%m-%Y')}"



class Cama(models.Model):
    numero = models.CharField()
    unidad = models.ForeignKey(Unidad, related_name='camas', on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Cama {self.numero}'
    

class Evolucion(models.Model):
    episodio = models.ForeignKey(Episodio, on_delete=models.CASCADE, related_name='evoluciones')
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contenido = models.TextField()
    plan_indicaciones = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    
    @property
    def autor_detallado(self):
        if not self.autor:
            return "Desconocido"

        # 1) Intentar sacar el nombre/apellido desde PerfilUsuario
        full_name = ""
        try:
            perfil = self.autor.perfilusuario  # ajusta si tu related_name es diferente
            full_name = " ".join(filter(None, [perfil.first_name, perfil.last_name])).strip()
        except (ObjectDoesNotExist, AttributeError):
            pass

        # 2) Si no hay nada en el perfil, usar get_full_name() de User
        if not full_name:
            full_name = self.autor.get_full_name().strip()
        
        # 3) Si sigue vacío, usar el username
        if not full_name:
            full_name = self.autor.username

        # 4) Obtener cargo y servicio del perfil
        cargo = servicio = None
        try:
            perfil = self.autor.perfilusuario
            cargo = perfil.cargo
            servicio = perfil.servicio
        except (ObjectDoesNotExist, AttributeError):
            pass

        # 5) Construir lista de partes y unir en string
        partes = [full_name]
        if cargo:
            partes.append(str(cargo))
        if servicio:
            partes.append(str(servicio))

        return " — ".join(partes)

    def __str__(self):
        return f'{self.fecha.strftime("%d/%m/%Y %H:%M")} por {self.autor_detallado}'
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
    episodio = models.OneToOneField(Episodio, on_delete=models.CASCADE, related_name='epicrisis')
    diagnostico_egreso = models.TextField()
    comentario_evolucion = models.TextField()
    indicaciones_generales = models.TextField(blank=True)
    indicaciones_controles = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    finalizado = models.BooleanField(default=False)
    autor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Epicrisis de {self.episodio.paciente.nombre} - {self.fecha_creacion.strftime('%d/%m/%Y')}"

    @property
    def paciente(self):
        return self.episodio.paciente


class MedicamentoCatalogo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    via = models.ManyToManyField('Via', related_name='medicamentos')
    frecuencia = models.ManyToManyField('Frecuencia', related_name='medicamentos')

    def __str__(self):
        return f"{self.nombre}"

class Via(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Frecuencia(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Medicamento(models.Model):
    episodio = models.ForeignKey('Episodio', related_name='medicamentos', on_delete=models.CASCADE)
    catalogo = models.ForeignKey(MedicamentoCatalogo, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    dosis = models.CharField(max_length=100)
    frecuencia = models.CharField(max_length=100)
    via = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nombre} ({self.dosis}, {self.frecuencia}, vía {self.via})"


class Indicacion(models.Model):
    episodio = models.ForeignKey('Episodio', related_name='indicaciones', on_delete=models.CASCADE)
    fecha = models.DateTimeField(default=timezone.now)
    reposo = models.CharField(max_length=100, blank=True)
    regimen = models.CharField(max_length=100, blank=True)
    medicamentos = models.TextField(blank=True)
    infusiones = models.TextField(blank=True)
    dispositivos = models.TextField(blank=True)
    otras = models.TextField(blank=True)

    def __str__(self):
        fecha_str = self.fecha.strftime('%d/%m/%Y') if self.fecha else 'Sin fecha'
        return f"Indicaciones {fecha_str} para {self.episodio.paciente}"


class Antecedente(models.Model):
    TIPO_CHOICES = [
        ("morbido", "Mórbido"),
        ("quirurgico", "Quirúrgico"),
        ("alergia", "Alergia"),
        ("familiar", "Familiar"),
        ("otro", "Otro"),
    ]

    paciente = models.ForeignKey(Paciente, related_name="antecedentes", on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.descripcion}"


class PlantillaTexto(models.Model):
    TIPO_CHOICES = [
        ("evolucion", "Evolución"),
        ("indicacion", "Indicación"),
        ("indicacion_general", "Indicación General Epicrisis"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plantillas_texto")
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    titulo = models.CharField(max_length=100, blank=True)
    contenido = models.TextField()

    def __str__(self):
        titulo = self.titulo or "Sin título"
        return f"{self.usuario.username} - {self.get_tipo_display()} - {titulo}"