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
)

from django import forms
from django.forms import inlineformset_factory





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
    class Meta:
        model = Epicrisis
        fields = [
            'diagnostico_egreso',
            'comentario_evolucion',
            'indicaciones_generales',
            'indicaciones_controles',
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