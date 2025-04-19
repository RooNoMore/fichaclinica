from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.templatetags.static import static
from weasyprint import HTML
from .models import Unidad, Paciente, Evolucion, Cama, Interconsulta, Servicio
from .forms import PacienteForm, EvolucionForm, InterconsultaForm, SolicitudExamenForm, RecetaForm
from django.utils import timezone


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
    evoluciones = paciente.evoluciones.order_by('-fecha')

    if request.method == 'POST':
        form = EvolucionForm(request.POST)
        if form.is_valid():
            nueva_evolucion = form.save(commit=False)
            nueva_evolucion.paciente = paciente
            nueva_evolucion.autor = request.user
            nueva_evolucion.save()
            return redirect('detalle_paciente', paciente_id=paciente_id)
    else:
        form = EvolucionForm()

    contexto = {
        'paciente': paciente,
        'evoluciones': evoluciones,
        'form': form,
    }

    return render(request, 'pacientes/detalle_paciente.html', contexto)

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


from weasyprint import HTML
from django.template.loader import render_to_string

@login_required
def crear_epicrisis(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    if request.method == 'POST':
        data = {key: request.POST.get(key, '') for key in [
            'diagnostico', 'AM', 'AQx', 'Alergias', 'Fcos',
            'ingreso', 'LabIngreso', 'PlanIngreso', 'intraop',
            'evolucion', 'dgegreso', 'indicacionesSegunDgPH', 'peso'
        ]}

        context = {
            'paciente': paciente,
            'rut': paciente.rut if hasattr(paciente, 'rut') else '',
            'FN': paciente.fecha_nacimiento.strftime('%d/%m/%Y') if hasattr(paciente, 'fecha_nacimiento') else '',
            'fono': paciente.telefonos if hasattr(paciente, 'telefonos') else '',
            'dom': paciente.domicilio if hasattr(paciente, 'domicilio') else '',
            'FE': timezone.now().strftime('%d/%m/%Y'),
            'ficha': paciente.ficha,
            'logo_url': request.build_absolute_uri(static('img/logo.png')),
            'mdtte': str(request.user.perfilusuario),
            **data
        }

        html_string = render_to_string('pacientes/epicrisis_template.html', context)
        pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="epicrisis_{paciente.nombre}.pdf"'
        return response

    # 🚀 Agregado para manejar GET
    return redirect('detalle_paciente', paciente_id=paciente_id)


@login_required
def exportar_epicrisis_pdf(request, epicrisis_id):
    epicrisis = get_object_or_404(Epicrisis, id=epicrisis_id)
    paciente = epicrisis.paciente

    context = {
        'paciente': paciente,
        'rut': paciente.rut if hasattr(paciente, 'rut') else '',
        'FN': paciente.fecha_nacimiento.strftime('%d/%m/%Y') if hasattr(paciente, 'fecha_nacimiento') else '',
        'fono': paciente.telefonos if hasattr(paciente, 'telefonos') else '',
        'dom': paciente.domicilio if hasattr(paciente, 'domicilio') else '',
        'FE': epicrisis.fecha.strftime('%d/%m/%Y'),
        'ficha': paciente.ficha,
        'logo_url': request.build_absolute_uri(static('img/logo.png')),
        'mdtte': str(epicrisis.autor),
        'AM': epicrisis.am if hasattr(epicrisis, 'am') else '',
        'AQx': epicrisis.aqx if hasattr(epicrisis, 'aqx') else '',
        'Alergias': epicrisis.alergias if hasattr(epicrisis, 'alergias') else '',
        'Fcos': epicrisis.fcos if hasattr(epicrisis, 'fcos') else '',
        'ingreso': epicrisis.ingreso,
        'LabIngreso': epicrisis.lab_ingreso,
        'PlanIngreso': epicrisis.plan_ingreso,
        'intraop': epicrisis.intraop,
        'evolucion': epicrisis.evolucion,
        'dgegreso': epicrisis.diagnostico_egreso,
        'indicacionesSegunDgPH': epicrisis.indicaciones_alta,
        'peso': epicrisis.peso if hasattr(epicrisis, 'peso') else ''
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