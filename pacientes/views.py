from django.shortcuts import render, redirect, get_object_or_404
from pacientes.forms import PacienteForm
from .models import Unidad, Paciente, Evolucion
from django.http import HttpResponse
from weasyprint import HTML
from django.templatetags.static import static
from django.template.loader import render_to_string
from .forms import EvolucionForm
from django.contrib.auth.decorators import login_required


def lista_camas(request):
    unidades = Unidad.objects.prefetch_related('camas').all()
    pacientes = Paciente.objects.select_related('cama').all()

    pacientes_por_cama = {
        paciente.cama.id: paciente
        for paciente in pacientes
        if paciente.cama is not None
    }

    return render(request, 'pacientes/lista_camas.html', {
        'unidades': unidades,
        'pacientes_por_cama': pacientes_por_cama,
    })

def nuevo_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_camas')  # Redirige a donde quieras
    else:
        form = PacienteForm()

    return render(request, 'pacientes/nuevo_paciente.html', {'form': form})

def detalle_paciente(request, id):
    # Obtener el paciente por id
    paciente = get_object_or_404(Paciente, pk=id)
    
    # Pasar los datos del paciente a la plantilla
    return render(request, 'pacientes/detalle_paciente.html', {'paciente': paciente})

def inicio(request):
    return render(request, 'pacientes/inicio.html')




def exportar_pdf(request, id):
    paciente = Paciente.objects.get(id=id)

    context = {
        'paciente': paciente,
        'ficha': paciente.ficha,
        'rut': '12.345.678-9',  # Reemplaza o calcula según tu modelo
        'FN': '01/01/2010',  # Reemplaza según tu modelo
        'fono': '987654321',
        'dom': 'Dirección ejemplo',
        'FE': '12/04/2025',
        'AM': 'Asma, DBT',
        'AQx': 'Apendicectomía',
        'Alergias': 'Penicilina',
        'Fcos': 'Paracetamol',
        'ingreso': 'Comentario de ingreso...',
        'LabIngreso': 'Exámenes al ingreso...',
        'PlanIngreso': 'Plan médico...',
        'intraop': 'Sin complicaciones',
        'evolucion': 'Buena evolución...',
        'peso': 25.3,
        'dgegreso': 'Dx final...',
        'indicacionesSegunDgPH': 'Reposo y control en 7 días',
        'mdtte': 'Dr. Roberto Leiva',
        'logo_url': request.build_absolute_uri(static('img/logo.png')),
    }

    html_string = render_to_string('pacientes/epicrisis_template.html', context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="paciente_{paciente.id}.pdf"'
    return response





@login_required
def detalle_paciente(request, id):
    paciente = get_object_or_404(Paciente, id=id)
    evoluciones = paciente.evoluciones.order_by('-fecha')

    if request.method == 'POST':
        form = EvolucionForm(request.POST)
        if form.is_valid():
            nueva = form.save(commit=False)
            nueva.paciente = paciente
            nueva.autor = request.user
            nueva.save()
            return redirect('detalle_paciente', id=id)
    else:
        form = EvolucionForm()

    context = {
        'paciente': paciente,
        'evoluciones': evoluciones,
        'form': form
    }
    return render(request, 'pacientes/detalle_paciente.html', context)