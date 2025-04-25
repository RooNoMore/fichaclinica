# Python estándar
from datetime import datetime

# Terceros
from weasyprint import HTML

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.utils import timezone
from django.utils.timezone import now

# Locales (de tu app)
from .forms import (
    EvolucionForm, InterconsultaForm, PacienteForm,
    RecetaForm, SolicitudExamenForm, EpicrisisForm
)
from .models import (
    Cama, Epicrisis, Evolucion, Interconsulta,
    Paciente, Servicio, Unidad
)

@login_required
def lista_camas(request):
    unidad_id = request.GET.get('unidad')
    unidades = Unidad.objects.all()

    camas = Cama.objects.filter(unidad_id=unidad_id) if unidad_id else Cama.objects.none()
    pacientes = Paciente.objects.filter(cama__unidad_id=unidad_id).select_related('cama') if unidad_id else Paciente.objects.none()

    pacientes_por_cama = {paciente.cama.id: paciente for paciente in pacientes if paciente.cama}

    return render(request, 'pacientes/lista_camas.html', {
        'unidades': unidades,
        'camas': camas,
        'pacientes_por_cama': pacientes_por_cama,
        'unidad_seleccionada': int(unidad_id) if unidad_id else None,
    })

@login_required
def nuevo_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_camas')
    else:
        form = PacienteForm()

    return render(request, 'pacientes/nuevo_paciente.html', {'form': form})



@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    evoluciones = paciente.evoluciones.all().order_by('-fecha')
    
    hay_borrador_epicrisis = Epicrisis.objects.filter(paciente=paciente, finalizado=False).exists()
    epicrisis_form = EpicrisisForm() if not hay_borrador_epicrisis else None
    
    # Medicamentos formset
    # formset = MedicamentoFormSet(request.POST or None, instance=paciente)
    if not Epicrisis.objects.filter(episodio=episodio).exists():
        Epicrisis.objects.create(episodio=episodio, ...)
    else:
        messages.warning(request, "Ya existe una epicrisis para este episodio.")

        
    if request.method == 'POST':
        if formset.is_valid():
            formset.save()
            return redirect('detalle_paciente', paciente_id=paciente.id)

    context = {
        'paciente': paciente,
        'evoluciones': evoluciones,
        'epicrisis_form': epicrisis_form,
        'mostrar_formulario_epicrisis': not hay_borrador_epicrisis,
        # 'formset': formset,  # Agregamos el formset al contexto
    }
    return render(request, 'pacientes/detalle_paciente.html', context)


@login_required
def exportar_pdf(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    context = {'paciente': paciente, 'logo_url': request.build_absolute_uri(static('img/logo.png'))}

    html_string = render_to_string('pacientes/epicrisis_template.html', context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="paciente_{paciente.id}.pdf"'
    return response

@login_required
def interconsultas_recibidas(request):
    perfil = request.user.perfilusuario
    servicio_usuario = perfil.servicio

    interconsultas_pendientes = Interconsulta.objects.filter(
        servicio_destino=servicio_usuario,
        atendido=False
    ).order_by('-fecha_solicitud')

    interconsultas_respondidas = Interconsulta.objects.filter(
        servicio_destino=servicio_usuario,
        atendido=True
    ).order_by('-fecha_respuesta')

    return render(request, 'pacientes/interconsultas_recibidas.html', {
        'interconsultas_pendientes': interconsultas_pendientes,
        'interconsultas_respondidas': interconsultas_respondidas,
        'servicio_usuario': servicio_usuario
    })

@login_required
def crear_interconsulta(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == 'POST':
        form = InterconsultaForm(request.POST)
        if form.is_valid():
            interconsulta = form.save(commit=False)
            interconsulta.paciente = paciente
            interconsulta.solicitante = request.user.perfilusuario
            interconsulta.save()
            return redirect('detalle_paciente', paciente_id=paciente_id)
    else:
        form = InterconsultaForm()

    return render(request, 'pacientes/crear_interconsultas.html', {'form': form, 'paciente': paciente})

@login_required
def responder_interconsulta(request, interconsulta_id):
    interconsulta = get_object_or_404(Interconsulta, id=interconsulta_id)

    if request.method == 'POST':
        interconsulta.respuesta = request.POST.get('respuesta')
        interconsulta.atendido = True
        interconsulta.fecha_respuesta = timezone.now()
        interconsulta.save()
        return redirect('interconsultas_recibidas')

    return render(request, 'pacientes/responder_interconsulta.html', {
        'interconsulta': interconsulta
    })


@login_required
def solicitar_examenes(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == 'POST':
        form = SolicitudExamenForm(request.POST)
        if form.is_valid():
            examen = form.save(commit=False)
            examen.paciente = paciente
            examen.solicitante = request.user.perfilusuario
            examen.save()
            return redirect('detalle_paciente', paciente_id=paciente_id)
    else:
        form = SolicitudExamenForm()

    return render(request, 'pacientes/solicitar_examenes.html', {'form': form, 'paciente': paciente})

@login_required
def crear_receta(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == 'POST':
        form = RecetaForm(request.POST)
        if form.is_valid():
            receta = form.save(commit=False)
            receta.paciente = paciente
            receta.medico = request.user.perfilusuario
            receta.save()
            return redirect('detalle_paciente', paciente_id=paciente_id)
    else:
        form = RecetaForm()

    return render(request, 'pacientes/crear_receta.html', {'form': form, 'paciente': paciente})

@login_required
def inicio(request):
    return render(request, 'pacientes/inicio.html')





@login_required

@login_required
def crear_epicrisis(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    # Verificar si ya existe una epicrisis no finalizada
    epicrisis_existente = Epicrisis.objects.filter(paciente=paciente, finalizado=False).first()
    if epicrisis_existente:
        messages.warning(request, "Ya existe una epicrisis en borrador para este paciente.")
        return redirect('detalle_paciente', paciente_id=paciente.id)  # O a donde quieras redirigir

    # Si no hay borrador previo, permite crear una nueva
    if request.method == 'POST':
        form = EpicrisisForm(request.POST)
        if form.is_valid():
            epicrisis = form.save(commit=False)
            epicrisis.paciente = paciente
            epicrisis.autor = request.user
            epicrisis.save()

            if request.POST.get('accion') == 'finalizar':
                epicrisis.finalizado = True
                epicrisis.save()

            return redirect('detalle_paciente', paciente_id=paciente.id)
    else:
        form = EpicrisisForm()

    return render(request, 'tu_template.html', {
        'form': form,
        'paciente': paciente
    })

def editar_epicrisis(request, epicrisis_id):
    epicrisis = get_object_or_404(Epicrisis, id=epicrisis_id)

    if epicrisis.finalizado:
        messages.warning(request, "No se puede editar una epicrisis ya finalizada.")
        return redirect('detalle_paciente', paciente_id=epicrisis.paciente.id)

    if request.method == 'POST':
        form = EpicrisisForm(request.POST, instance=epicrisis)
        if form.is_valid():
            epicrisis = form.save()
            if request.POST.get('accion') == 'finalizar':
                epicrisis.finalizado = True
                epicrisis.paciente.fecha_egreso = now().date()
                epicrisis.paciente.save()
                epicrisis.save()
                return redirect('exportar_epicrisis_pdf', epicrisis_id=epicrisis.id)
            return redirect('detalle_paciente', paciente_id=epicrisis.paciente.id)
    else:
        form = EpicrisisForm(instance=epicrisis)

    return render(request, 'epicrisis/editar_epicrisis.html', {
        'form': form,
        'epicrisis': epicrisis,
    })


@login_required
def exportar_epicrisis_pdf(request, epicrisis_id):
    epicrisis = get_object_or_404(Epicrisis, id=epicrisis_id)
    paciente = epicrisis.paciente

    context = {
        'paciente': paciente,
        'rut': getattr(paciente, 'rut', ''),
        'FN': paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else '',
        'fono': getattr(paciente, 'telefonos', ''),
        'dom': getattr(paciente, 'domicilio', ''),
        'FE': epicrisis.fecha_creacion.strftime('%d/%m/%Y'),
        'ficha': paciente.ficha,
        'logo_url': request.build_absolute_uri(static('img/logo.png')),
        'mdtte': str(epicrisis.autor),
        'AM': getattr(epicrisis, 'am', ''),
        'AQx': getattr(epicrisis, 'aqx', ''),
        'Alergias': getattr(epicrisis, 'alergias', ''),
        'Fcos': getattr(epicrisis, 'fcos', ''),
        'ingreso': getattr(epicrisis, 'ingreso', ''),
        'LabIngreso': getattr(epicrisis, 'lab_ingreso', ''),
        'PlanIngreso': getattr(epicrisis, 'plan_ingreso', ''),
        'intraop': getattr(epicrisis, 'intraop', ''),
        'evolucion': getattr(epicrisis, 'comentario_evolucion', ''),
        'dgegreso': epicrisis.diagnostico_egreso,
        'indicacionesSegunDgPH': epicrisis.indicaciones_generales,
        'indicacionesControles': epicrisis.indicaciones_controles,
        'medicamentos': epicrisis.medicamentos_indicados.all(),
        'peso': getattr(epicrisis, 'peso', ''),
    }

    html_string = render_to_string('pacientes/epicrisis_template.html', context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="epicrisis_{paciente.nombre}.pdf"'
    return response


from django.http import JsonResponse
from .models import Cama, Paciente

def camas_disponibles(request):
    unidad_id = request.GET.get('unidad')
    camas_ocupadas = Paciente.objects.exclude(cama=None).values_list('cama_id', flat=True)
    camas = Cama.objects.filter(unidad_id=unidad_id).exclude(id__in=camas_ocupadas)
    data = [{'id': cama.id, 'numero': cama.numero} for cama in camas]
    return JsonResponse(data, safe=False)    


@login_required
def dar_de_alta_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == 'POST':
        paciente.dar_de_alta()
        messages.success(request, f'El paciente {paciente.nombre} ha sido dado de alta.')
        return redirect('detalle_paciente', paciente_id=paciente.id)

    messages.error(request, 'Método no permitido.')
    return redirect('detalle_paciente', paciente_id=paciente.id)
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == 'POST':
        paciente.dar_de_alta()
        messages.success(request, f'El paciente {paciente.nombre} ha sido dado de alta.')
        return redirect('detalle_paciente', paciente_id=paciente.id)

    messages.error(request, 'Método no permitido.')
    return redirect('detalle_paciente', paciente_id=paciente.id)    


@login_required
def buscar_pacientes(request):
    query = request.GET.get('q')
    resultados = []

    if query:
        resultados = Paciente.objects.filter(
            Q(nombre__icontains=query) |
            Q(rut__icontains=query) |
            Q(ficha__icontains=query)
        )

    return render(request, 'pacientes/buscar_pacientes.html', {
        'resultados': resultados,
        'query': query
    })
