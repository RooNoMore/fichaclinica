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

from .utils import normalizar_rut

# Locales (de tu app)
from .forms import (
    EvolucionForm,
    InterconsultaForm,
    PacienteForm,
    RecetaPDFForm,
    SolicitudExamenForm,
    EpicrisisForm,
    MedicamentoFormSet,
    AntecedenteForm,
    AntecedentesPacienteForm,
    IndicacionForm,
)
from .models import (
    Cama,
    Epicrisis,
    Evolucion,
    Interconsulta,
    Paciente,
    Servicio,
    Unidad,
    Episodio,
    MedicamentoCatalogo,
    Antecedente,
    Indicacion,
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
        # Obtener valores sin validar para buscar coincidencias previas
        rut_raw = request.POST.get('rut')
        ficha_raw = request.POST.get('ficha')

        rut_norm = normalizar_rut(rut_raw) if rut_raw else None
        paciente = None
        if rut_norm:
            paciente = Paciente.objects.filter(rut=rut_norm).first()
        if not paciente and ficha_raw:
            try:
                ficha_int = int(ficha_raw)
                paciente = Paciente.objects.filter(ficha=ficha_int).first()
            except ValueError:
                pass

        # Si existe, instanciamos el formulario con ese paciente para evitar la
        # validación de unicidad y actualizar sus datos
        form = PacienteForm(request.POST, instance=paciente)

        if form.is_valid():
            paciente = form.save(commit=False)
            paciente.rut = normalizar_rut(form.cleaned_data.get('rut')) if form.cleaned_data.get('rut') else None
            paciente.hospitalizado = True
            paciente.save()

            Episodio.objects.create(
                paciente=paciente,
                fecha_ingreso=form.cleaned_data.get('fecha_ingreso') or timezone.now(),
                cama=paciente.cama,
                motivo_ingreso='Ingreso inicial',
                finalizado=False,
            )

            return redirect('lista_camas')
    else:
        form = PacienteForm()

    return render(request, 'pacientes/nuevo_paciente.html', {'form': form})


@login_required
def detalle_paciente(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    episodio_activo = (
        paciente.episodios.filter(fecha_egreso__isnull=True).first()
    )
    evoluciones = (
        episodio_activo.evoluciones.all().order_by('-fecha') if episodio_activo else []
    )
    episodios_previos = (
        paciente.episodios.exclude(id=episodio_activo.id)
        if episodio_activo
        else paciente.episodios.all()
    ).order_by('-fecha_ingreso')

    form = EvolucionForm()
    formset = MedicamentoFormSet(request.POST or None, instance=episodio_activo) if episodio_activo else None
    antecedentes_form = AntecedentesPacienteForm()
    indicacion_form = IndicacionForm()
    antecedentes = paciente.antecedentes.all()
    antecedentes_por_tipo = [
        {
            "label": label,
            "lista": antecedentes.filter(tipo=tipo),
        }
        for tipo, label in Antecedente.TIPO_CHOICES
    ]

    if request.method == 'POST':
        accion = request.POST.get('accion')

        if accion == 'guardar_meds' and formset:
            if formset.is_valid():
                formset.save()
                messages.success(request, "Medicamentos guardados correctamente.")
                return redirect('detalle_paciente', paciente_id=paciente.id)
            else:
                print("ERRORES DEL FORMSET:")
                for i, errors in enumerate(formset.errors):
                    print(f"Formulario #{i}: {errors}")
                    messages.error(request, "Error al guardar medicamentos. Revisa los campos.")

        elif accion == 'guardar_evolucion' and episodio_activo:
            form = EvolucionForm(request.POST)
            if form.is_valid():
                evolucion = form.save(commit=False)
                evolucion.episodio = episodio_activo
                evolucion.autor = request.user
                evolucion.save()
                messages.success(request, "Evolución guardada correctamente.")
                return redirect('detalle_paciente', paciente_id=paciente.id)
            else:
                messages.error(request, "Error al guardar evolución.")
        elif accion == 'guardar_indicacion' and episodio_activo:
            indicacion_form = IndicacionForm(request.POST)
            if indicacion_form.is_valid():
                indicacion = indicacion_form.save(commit=False)
                indicacion.episodio = episodio_activo
                indicacion.save()
                messages.success(request, "Indicaciones guardadas correctamente.")
                return redirect('detalle_paciente', paciente_id=paciente.id)
            else:
                messages.error(request, "Error al guardar indicaciones.")
        elif accion == 'guardar_antecedente':
            antecedentes_form = AntecedentesPacienteForm(request.POST)
            if antecedentes_form.is_valid():
                for tipo in ['morbido', 'quirurgico', 'alergia', 'familiar', 'otro']:
                    desc = antecedentes_form.cleaned_data.get(tipo)
                    if desc:
                        Antecedente.objects.create(
                            paciente=paciente,
                            tipo=tipo,
                            descripcion=desc
                        )
                messages.success(request, "Antecedentes guardados correctamente.")
                return redirect('detalle_paciente', paciente_id=paciente.id)
            else:
                messages.error(request, "Error al guardar antecedente.")

    # Epicrisis: obtener la epicrisis del episodio activo, si existe
    epicrisis_existente = None
    if episodio_activo:
        epicrisis_existente = Epicrisis.objects.filter(
            episodio=episodio_activo
        ).first()
    epicrisis_form = EpicrisisForm() if not epicrisis_existente else None
    indicaciones = episodio_activo.indicaciones.all().order_by('-fecha') if episodio_activo else []

    context = {
        'paciente': paciente,
        'episodio_activo': episodio_activo,
        'evoluciones': evoluciones,
        'form': form,
        'formset': formset,
        'antecedente_form': antecedentes_form,
        'antecedentes': antecedentes,
        'antecedentes_por_tipo': antecedentes_por_tipo,
        'indicacion_form': indicacion_form,
        'indicaciones': indicaciones,
        'epicrisis_form': epicrisis_form,
        'epicrisis_existente': epicrisis_existente,
        'episodios_previos': episodios_previos,
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
    """Genera una receta en PDF utilizando los medicamentos guardados."""
    paciente = get_object_or_404(Paciente, id=paciente_id)

    episodio = paciente.episodios.filter(fecha_egreso__isnull=True).first()
    medicamentos = episodio.medicamentos.all() if episodio else []

    if request.method == 'POST':
        form = RecetaPDFForm(request.POST)
        if form.is_valid():
            dias = form.cleaned_data["dias_tratamiento"]

            context = {
                "paciente": paciente,
                "edad": paciente.edad(),
                "dias_tratamiento": dias,
                "medicamentos": medicamentos,
            }

            html_string = render_to_string(
                "pacientes/receta_pdf.html", context
            )
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

            response = HttpResponse(pdf, content_type="application/pdf")
            response["Content-Disposition"] = (
                f"attachment; filename=receta_{paciente.id}.pdf"
            )
            return response
    else:
        form = RecetaPDFForm()

    return render(
        request,
        "pacientes/crear_receta.html",
        {"form": form, "paciente": paciente, "medicamentos": medicamentos},
    )

@login_required
def inicio(request):
    return render(request, 'pacientes/inicio.html')


@login_required
def estudios(request):
    return render(request, 'pacientes/estudios.html')





@login_required
def crear_epicrisis(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)

    # 1) Tomamos el episodio más reciente de ese paciente
    episodio = (Episodio.objects
                .filter(paciente=paciente)
                .order_by('-fecha_ingreso')  # o '-id' si no tienes fecha_inicio
                .first())
    if not episodio:
        messages.error(request, "Este paciente no tiene ningún episodio activo.")
        return redirect('detalle_paciente', paciente_id)

    # 2) Validamos si ya existe una epicrisis asociada al episodio
    existing_epicrisis = Epicrisis.objects.filter(episodio=episodio).first()
    if existing_epicrisis:
        if existing_epicrisis.finalizado:
            messages.warning(request, "Ya existe una epicrisis finalizada para este episodio.")
        else:
            messages.warning(request, "Ya existe una epicrisis en borrador para este episodio.")
        return redirect('detalle_paciente', paciente_id)

    # 3) Procesamos el formulario
    if request.method == 'POST':
        form = EpicrisisForm(request.POST)
        if form.is_valid():
            epicrisis = form.save(commit=False)
            epicrisis.episodio = episodio
            epicrisis.autor = request.user
            if request.POST.get('accion') == 'finalizar':
                epicrisis.finalizado = True
            epicrisis.save()
            messages.success(request, "Epicrisis creada correctamente.")
            return redirect('detalle_paciente', paciente_id)
    else:
        form = EpicrisisForm()

    return render(request, 'pacientes/crear_epicrisis.html', {
        'form': form,
        'paciente': paciente,
    })

def editar_epicrisis(request, epicrisis_id):
    epicrisis = get_object_or_404(Epicrisis, id=epicrisis_id)

    if epicrisis.finalizado and not epicrisis.paciente.hospitalizado:
        messages.warning(request, "No se puede editar una epicrisis de un paciente dado de alta.")
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

    antecedentes = paciente.antecedentes.all()
    def _join(tipo):
        return ', '.join(a.descripcion for a in antecedentes.filter(tipo=tipo))

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
        'AM': _join('morbido'),
        'AQx': _join('quirurgico'),
        'Alergias': _join('alergia'),
        'Fcos': getattr(epicrisis, 'fcos', ''),
        'ingreso': getattr(epicrisis, 'ingreso', ''),
        'LabIngreso': getattr(epicrisis, 'lab_ingreso', ''),
        'PlanIngreso': getattr(epicrisis, 'plan_ingreso', ''),
        'intraop': getattr(epicrisis, 'intraop', ''),
        'evolucion': getattr(epicrisis, 'comentario_evolucion', ''),
        'dgegreso': epicrisis.diagnostico_egreso,
        'indicacionesSegunDgPH': epicrisis.indicaciones_generales,
        'indicacionesControles': epicrisis.indicaciones_controles,
        'medicamentos': epicrisis.episodio.medicamentos.all(),
        'peso': getattr(epicrisis, 'peso', ''),
    }

    html_string = render_to_string('pacientes/epicrisis_template.html', context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="epicrisis_{paciente.nombre}.pdf"'
    return response


@login_required
def ver_epicrisis(request, epicrisis_id):
    epicrisis = get_object_or_404(Epicrisis, id=epicrisis_id)
    paciente = epicrisis.paciente

    antecedentes = paciente.antecedentes.all()
    def _join(tipo):
        return ', '.join(a.descripcion for a in antecedentes.filter(tipo=tipo))

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
        'AM': _join('morbido'),
        'AQx': _join('quirurgico'),
        'Alergias': _join('alergia'),
        'Fcos': getattr(epicrisis, 'fcos', ''),
        'ingreso': getattr(epicrisis, 'ingreso', ''),
        'LabIngreso': getattr(epicrisis, 'lab_ingreso', ''),
        'PlanIngreso': getattr(epicrisis, 'plan_ingreso', ''),
        'intraop': getattr(epicrisis, 'intraop', ''),
        'evolucion': getattr(epicrisis, 'comentario_evolucion', ''),
        'dgegreso': epicrisis.diagnostico_egreso,
        'indicacionesSegunDgPH': epicrisis.indicaciones_generales,
        'indicacionesControles': epicrisis.indicaciones_controles,
        'medicamentos': epicrisis.episodio.medicamentos.all(),
        'peso': getattr(epicrisis, 'peso', ''),
    }

    return render(request, 'pacientes/epicrisis_template.html', context)


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


@login_required
def eliminar_antecedente(request, antecedente_id):
    antecedente = get_object_or_404(Antecedente, id=antecedente_id)
    paciente_id = antecedente.paciente.id

    if request.method == 'POST':
        antecedente.delete()
        messages.success(request, 'Antecedente eliminado correctamente.')

    return redirect('detalle_paciente', paciente_id=paciente_id)


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

def cargar_opciones_medicamento(request):
    medicamento_id = request.GET.get('medicamento_id')
    data = {"vias": [], "frecuencias": []}

    if medicamento_id:
        try:
            m = MedicamentoCatalogo.objects.get(pk=medicamento_id)
            # Usa .via y .frecuencia (ManyToMany) para obtener nombres
            data["vias"] = list(m.via.values_list('nombre', flat=True))
            data["frecuencias"] = list(m.frecuencia.values_list('nombre', flat=True))
        except MedicamentoCatalogo.DoesNotExist:
            pass

    return JsonResponse(data)

def obtener_datos_catalogo(request, pk):
    try:
        catalogo = MedicamentoCatalogo.objects.get(pk=pk)
        data = {
            'nombre': catalogo.nombre,
            'vias': list(catalogo.via.values_list('nombre', flat=True)),
            'frecuencias': list(catalogo.frecuencia.values_list('nombre', flat=True)),
        }
    except MedicamentoCatalogo.DoesNotExist:
        data = {}

    return JsonResponse(data)


@login_required
def buscar_paciente_api(request):
    """Devuelve los datos de un paciente si existe para autocompletar el formulario."""
    rut = request.GET.get("rut")
    ficha = request.GET.get("ficha")

    rut = normalizar_rut(rut) if rut else None
    paciente = None

    if rut:
        paciente = Paciente.objects.filter(rut=rut).first()

    if not paciente and ficha:
        try:
            ficha_int = int(ficha)
            paciente = Paciente.objects.filter(ficha=ficha_int).first()
        except ValueError:
            pass

    if paciente:
        data = {
            "existe": True,
            "id": paciente.id,
            "nombre": paciente.nombre,
            "rut": paciente.rut,
            "fecha_nacimiento": paciente.fecha_nacimiento.strftime("%Y-%m-%d") if paciente.fecha_nacimiento else "",
            "fono": paciente.fono or "",
            "domicilio": paciente.domicilio or "",
            "diagnostico": paciente.diagnostico or "",
        }
    else:
        data = {"existe": False}

    return JsonResponse(data)