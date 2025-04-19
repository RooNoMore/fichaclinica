# forms.py
from django import forms
from .models import Paciente, Cama, Unidad

class PacienteForm(forms.ModelForm):
    unidad = forms.ModelChoiceField(queryset=Unidad.objects.all(), required=False, label="Unidad")

    class Meta:
        model = Paciente
        fields = ['ficha', 'nombre', 'diagnostico', 'unidad', 'cama', 'fecha_nacimiento', 'rut', 'fono', 'domicilio', 'fecha_ingreso', 'fecha_egreso']

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

from django import forms
from .models import Evolucion

class EvolucionForm(forms.ModelForm):
    class Meta:
        model = Evolucion
        fields = ['contenido', 'plan_indicaciones']
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Detalle de la evolución'}),
            'plan_indicaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Plan o indicaciones del paciente'}),
        }

from .models import Interconsulta, SolicitudExamen, Receta

class InterconsultaForm(forms.ModelForm):
    class Meta:
        model = Interconsulta
        fields = ['servicio_destino', 'motivo']

class SolicitudExamenForm(forms.ModelForm):
    class Meta:
        model = SolicitudExamen
        fields = ['tipo_examen', 'indicaciones']

class RecetaForm(forms.ModelForm):
    class Meta:
        model = Receta
        fields = ['medicamento', 'dosis', 'frecuencia', 'duracion', 'indicaciones_extra']
