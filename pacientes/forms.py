# forms.py
from django import forms
from .models import Paciente, Cama

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['ficha', 'nombre', 'diagnostico', 'cama', 'fecha_nacimiento', 'rut', 'fono', 'domicilio', 'fecha_ingreso', 'fecha_egreso']




    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        camas_ocupadas = Paciente.objects.exclude(cama=None).values_list('cama_id', flat=True)
        self.fields['cama'].queryset = Cama.objects.exclude(id__in=camas_ocupadas)


from django import forms
from .models import Evolucion

class EvolucionForm(forms.ModelForm):
    class Meta:
        model = Evolucion
        fields = ['contenido']
        widgets = {
            'contenido': forms.Textarea(attrs={
                'rows': 4, 
                'class': 'form-control',
                'placeholder': 'Escribe aquí la evolución clínica...'
            }),
        }