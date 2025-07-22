# forms.py
from django import forms
from .models import (
    Paciente,
    Cama,
    Unidad,
    Evolucion,
    Episodio,
    Medicamento,
    MedicamentoCatalogo,
    Via,
    Frecuencia,
    Antecedente,
    Indicacion,
    PlantillaTexto,
)

from django import forms
from django.forms import inlineformset_factory

from .utils import normalizar_rut





class PacienteForm(forms.ModelForm):
    unidad = forms.ModelChoiceField(
        queryset=Unidad.objects.all(),
        required=False,
        label="Unidad",
        widget=forms.Select(attrs={'id': 'id_unidad'})  # NECESARIO PARA EL JS
    )

    class Meta:
        model = Paciente
        fields = ['ficha', 'nombre', 'diagnostico', 'unidad', 'cama', 'fecha_nacimiento', 'rut', 'fono', 'domicilio', 'fecha_ingreso']
        widgets = {
            'cama': forms.Select(attrs={'id': 'id_cama'})  # NECESARIO TAMBIÉN
            
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['cama'].queryset = Cama.objects.none()

        if 'unidad' in self.data:
            try:
                unidad_id = int(self.data.get('unidad'))
                camas_ocupadas = Paciente.objects.exclude(cama=None).values_list('cama_id', flat=True)
                self.fields['cama'].queryset = Cama.objects.filter(unidad_id=unidad_id).exclude(id__in=camas_ocupadas)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.cama:
            self.fields['cama'].queryset = Cama.objects.filter(unidad=self.instance.cama.unidad)
            self.fields['unidad'].initial = self.instance.cama.unidad

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        return normalizar_rut(rut)

            
from django import forms
from .models import Evolucion
from django.forms import inlineformset_factory

class EvolucionForm(forms.ModelForm):
    class Meta:
        model = Evolucion
        fields = ['contenido', 'plan_indicaciones']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalle de la evolución'
            }),
            'plan_indicaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Plan o indicaciones del paciente'
            }),
        }

from .models import (
    Interconsulta,
    SolicitudExamen,
    Receta,
    SignoVital,
    EvaluacionEnfermeria,
    Solicitud,
)

class InterconsultaForm(forms.ModelForm):
    class Meta:
        model = Interconsulta
        fields = ['servicio_destino', 'motivo']
        widgets = {
            'servicio_destino': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SolicitudExamenForm(forms.Form):
    IMAGENES = [
        'Radiografía de tórax',
        'Ecografía abdominal',
        'Tomografía computada de abdomen',
        'Resonancia magnética cerebral',
        'Radiografía de extremidad',
    ]

    LABORATORIO = [
        'Hemograma',
        'Perfil bioquímico',
        'Perfil lipídico',
        'Función renal',
        'Gases arteriales',
        'Urocultivo',
        'Orina completa',
        'Pruebas de coagulación',
        'Glicemia',
        'Creatinina',
    ]
    categoria = forms.ChoiceField(
        choices=[('imagen', 'Imagenología'), ('laboratorio', 'Laboratorio')],
        label='Sección'
    )
    tipo_examen = forms.MultipleChoiceField(
        choices=[],
        label='Exámenes',
        widget=forms.CheckboxSelectMultiple,
    )
    indicaciones = forms.CharField(
        widget=forms.Textarea, required=False, label='Indicaciones'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categoria = self.data.get('categoria') or self.initial.get('categoria')
        if categoria == 'imagen':
            opciones = self.IMAGENES
        else:
            opciones = self.LABORATORIO
        self.fields['tipo_examen'].choices = [(o, o) for o in opciones]

class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['medicamento', 'dosis', 'frecuencia', 'duracion', 'indicaciones_extra']


class RecetaPDFForm(forms.Form):
    dias_tratamiento = forms.IntegerField(
        min_value=1,
        label="Días de tratamiento",
        help_text="Duración total de la terapia en días",
    )


class AntecedenteForm(forms.ModelForm):
    class Meta:
        model = Antecedente
        fields = ['tipo', 'descripcion']


class AntecedentesPacienteForm(forms.Form):
    morbido = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Antecedentes mórbidos"
    )
    quirurgico = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Antecedentes quirúrgicos"
    )
    alergia = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Alergias"
    )
    familiar = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Antecedentes familiares"
    )
    otro = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Otros antecedentes"
    )


from .models import Epicrisis

class EpicrisisForm(forms.ModelForm):
    EXAM_CHOICES = [(False, 'No'), (True, 'Sí')]
    MEJORADO_CHOICES = [(True, 'Mejorado'), (False, 'No')]

    examenes_pendientes = forms.TypedChoiceField(
        choices=EXAM_CHOICES,
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        label='Exámenes pendientes'
    )
    detalle_examenes_pendientes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 1}),
        label='Detalle exámenes pendientes'
    )
    examenes_realizados = forms.TypedChoiceField(
        choices=EXAM_CHOICES,
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        label='Exámenes realizados'
    )
    detalle_examenes_realizados = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 1}),
        label='Detalle exámenes realizados'
    )
    condicion_mejorado = forms.TypedChoiceField(
        choices=MEJORADO_CHOICES,
        coerce=lambda x: x == 'True',
        widget=forms.RadioSelect,
        label='Condición al alta'
    )
    class Meta:
        model = Epicrisis
        fields = [
            'diagnostico_egreso',
            'comentario_evolucion',
            'indicaciones_generales',
            'indicaciones_controles',
            'examenes_pendientes',
            'detalle_examenes_pendientes',
            'examenes_realizados',
            'detalle_examenes_realizados',
            'condicion_mejorado',
        ]
        widgets = {
            'diagnostico_egreso': forms.Textarea(attrs={'rows': 1}),
            'comentario_evolucion': forms.Textarea(attrs={'rows': 3}),
            'indicaciones_generales': forms.Textarea(attrs={'rows': 2}),
            'indicaciones_controles': forms.Textarea(attrs={'rows': 1}),
        }

class MedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = ['catalogo', 'nombre', 'dosis', 'frecuencia', 'via']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'catalogo' in self.fields:
            self.fields['catalogo'].queryset = MedicamentoCatalogo.objects.all()
            self.fields['catalogo'].required = False
            # Aquí agregamos los atributos de cada opción
            self.fields['catalogo'].widget.attrs.update({'class': 'catalogo-select'})

        
MedicamentoFormSet = inlineformset_factory(
    Episodio, Medicamento,  # <--- CORREGIDO
    fields=('catalogo', 'nombre', 'dosis', 'frecuencia', 'via'),
    form=MedicamentoForm,
    extra=1,
    can_delete=True
)

class IndicacionForm(forms.ModelForm):
    class Meta:
        model = Indicacion
        fields = [
            'fecha',
            'reposo',
            'regimen',
            'medicamentos',
            'infusiones',
            'dispositivos',
            'otras',
        ]
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'reposo': forms.Textarea(attrs={'rows': 1, 'class': 'form-control'}),
            'regimen': forms.Textarea(attrs={'rows': 1, 'class': 'form-control'}),
            'medicamentos': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'infusiones': forms.Textarea(attrs={'rows': 1, 'class': 'form-control'}),
            'dispositivos': forms.Textarea(attrs={'rows': 1, 'class': 'form-control'}),
            'otras': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }


class SignoVitalForm(forms.ModelForm):
    class Meta:
        model = SignoVital
        fields = [
            'fecha',
            'temperatura',
            'presion_arterial',
            'frecuencia_cardiaca',
            'frecuencia_respiratoria',
            'saturacion',
        ]
        widgets = {
            'fecha': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control form-control-sm'
            }),
            'temperatura': forms.NumberInput(attrs={
                'step': '0.1',
                'class': 'form-control form-control-sm'
            }),
            'presion_arterial': forms.TextInput(attrs={
                'class': 'form-control form-control-sm'
            }),
            'frecuencia_cardiaca': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm'
            }),
            'frecuencia_respiratoria': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm'
            }),
            'saturacion': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm'
            }),
        }


class EvaluacionEnfermeriaForm(forms.ModelForm):
    class Meta:
        model = EvaluacionEnfermeria
        fields = ['fecha', 'contenido']
        widgets = {
            'fecha': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'contenido': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        fields = ['tipo', 'detalle']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'detalle': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class PlantillaTextoForm(forms.ModelForm):
    class Meta:
        model = PlantillaTexto
        fields = ['titulo', 'contenido']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'contenido': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

