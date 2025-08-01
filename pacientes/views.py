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
    SignoVitalForm,
    EvaluacionEnfermeriaForm,
    SolicitudForm,
    PlantillaTextoForm,
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
    PlantillaTexto,
    SignoVital,
    EvaluacionEnfermeria,
    SolicitudExamen,
    Solicitud,
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
    signos_form = SignoVitalForm()
    evaluacion_form = EvaluacionEnfermeriaForm()
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
        elif accion == 'guardar_signos' and episodio_activo:
            signos_form = SignoVitalForm(request.POST)
            if signos_form.is_valid():
                sv = signos_form.save(commit=False)
                sv.episodio = episodio_activo
                sv.responsable = request.user.perfilusuario
                sv.save()
                messages.success(request, 'Signos vitales guardados correctamente.')
                return redirect('detalle_paciente', paciente_id=paciente.id)
            else:
                messages.error(request, 'Error al guardar signos vitales.')
        elif accion == 'guardar_evaluacion_enfermeria' and episodio_activo:
            evaluacion_form = EvaluacionEnfermeriaForm(request.POST)
            if evaluacion_form.is_valid():
                ev = evaluacion_form.save(commit=False)
                ev.episodio = episodio_activo
                ev.responsable = request.user.perfilusuario
                ev.save()
                messages.success(request, 'Evaluación guardada correctamente.')
                return redirect('detalle_paciente', paciente_id=paciente.id)
            else:
                messages.error(request, 'Error al guardar evaluación.')
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
    if not epicrisis_existente:
        epicrisis_existente = (
            Epicrisis.objects.filter(episodio__paciente=paciente, finalizado=False)
            .order_by('-fecha_creacion')
            .first()
        )
    epicrisis_form = EpicrisisForm() if not epicrisis_existente else None
    indicaciones = episodio_activo.indicaciones.all().order_by('-fecha') if episodio_activo else []
    signos_vitales = episodio_activo.signos_vitales.all().order_by('-fecha') if episodio_activo else []
    evaluaciones = episodio_activo.evaluaciones_enfermeria.all().order_by('-fecha') if episodio_activo else []
    examen_form = SolicitudExamenForm()

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
        'signos_form': signos_form,
        'evaluacion_form': evaluacion_form,
        'signos_vitales': signos_vitales,
        'evaluaciones': evaluaciones,
        'epicrisis_form': epicrisis_form,
        'epicrisis_existente': epicrisis_existente,
        'episodios_previos': episodios_previos,
        'examen_form': examen_form,
        'IMAGENES': SolicitudExamenForm.IMAGENES,
        'LABORATORIO': SolicitudExamenForm.LABORATORIO,
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
def interconsulta_pdf(request, interconsulta_id):
    interconsulta = get_object_or_404(Interconsulta, id=interconsulta_id)
    context = {
        'interconsulta': interconsulta,
    }

    html_string = render_to_string('pacientes/interconsulta_pdf.html', context)
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename=interconsulta_{interconsulta.id}.pdf'
    )
    return response


@login_required
def solicitar_examenes(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == 'POST':
        form = SolicitudExamenForm(request.POST)
        if form.is_valid():
            categoria = form.cleaned_data["categoria"]
            tipos = form.cleaned_data["tipo_examen"]
            indicaciones = form.cleaned_data["indicaciones"]

            SolicitudExamen.objects.create(
                paciente=paciente,
                solicitante=request.user.perfilusuario,
                categoria=categoria,
                examenes="\n".join(tipos),
                indicaciones=indicaciones,
            )

            context = {
                'paciente': paciente,
                'examenes': tipos,
                'categoria': categoria,
                'indicaciones': indicaciones,
            }
            html_string = render_to_string(
                'pacientes/examenes_pdf.html', context
            )
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename=examenes_{paciente.id}.pdf'
            return response
    else:
        form = SolicitudExamenForm()

    return render(request, 'pacientes/solicitar_examenes.html', {
        'form': form,
        'paciente': paciente,
        'IMAGENES': SolicitudExamenForm.IMAGENES,
        'LABORATORIO': SolicitudExamenForm.LABORATORIO,
    })


@login_required
def imprimir_solicitud_examen(request, solicitud_id):
    solicitud = get_object_or_404(SolicitudExamen, id=solicitud_id)
    examenes = solicitud.lista_examenes()
    context = {
        "paciente": solicitud.paciente,
        "examenes": examenes,
        "categoria": solicitud.categoria,
        "indicaciones": solicitud.indicaciones,
    }
    html_string = render_to_string(
        "pacientes/examenes_pdf.html",
        context,
    )
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = f"attachment; filename=examenes_{solicitud.paciente.id}_{solicitud.id}.pdf"
    return response


@login_required
def crear_solicitud(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    if request.method == "POST":
        form = SolicitudForm(request.POST)
        if form.is_valid():
            solicitud = form.save(commit=False)
            solicitud.paciente = paciente
            solicitud.solicitante = request.user.perfilusuario
            solicitud.save()

            context = {"paciente": paciente, "solicitud": solicitud}
            html_string = render_to_string(
                "pacientes/solicitud_pdf.html", context
            )
            pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

            response = HttpResponse(pdf, content_type="application/pdf")
            response[
                "Content-Disposition"
            ] = f"attachment; filename=solicitud_{solicitud.id}.pdf"
            return response
    else:
        form = SolicitudForm()

    return render(
        request, "pacientes/crear_solicitud.html", {"form": form, "paciente": paciente}
    )


@login_required
def imprimir_solicitud(request, solicitud_id):
    solicitud = get_object_or_404(Solicitud, id=solicitud_id)
    context = {"paciente": solicitud.paciente, "solicitud": solicitud}
    html_string = render_to_string(
        "pacientes/solicitud_pdf.html", context
    )
    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf, content_type="application/pdf")
    response[
        "Content-Disposition"
    ] = f"attachment; filename=solicitud_{solicitud.id}.pdf"
    return response

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
            finalizar = request.POST.get('accion') == 'finalizar'
            if finalizar:
                epicrisis.finalizado = True
                epicrisis.autor = request.user
            epicrisis.save()
            messages.success(request, "Epicrisis creada correctamente.")
            if finalizar:
                return redirect('exportar_epicrisis_pdf', epicrisis_id=epicrisis.id)
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
            epicrisis = form.save(commit=False)
            finalizar = request.POST.get('accion') == 'finalizar'
            if finalizar:
                epicrisis.finalizado = True
                if epicrisis.autor is None:
                    epicrisis.autor = request.user
                episodio = epicrisis.episodio
                episodio.fecha_egreso = timezone.now()
                episodio.finalizado = True
                episodio.cama = None
                episodio.save()
                epicrisis.paciente.fecha_egreso = now().date()
                epicrisis.paciente.save()
                epicrisis.save()
                return redirect('exportar_epicrisis_pdf', epicrisis_id=epicrisis.id)
            epicrisis.save()
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
        'condicion_alta': 'Mejorado' if epicrisis.condicion_mejorado else 'No',
        'examenes_pendientes': 'Sí' if epicrisis.examenes_pendientes else 'No',
        'detalle_examenes_pendientes': epicrisis.detalle_examenes_pendientes,
        'examenes_realizados': 'Sí' if epicrisis.examenes_realizados else 'No',
        'detalle_examenes_realizados': epicrisis.detalle_examenes_realizados,
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
        'condicion_alta': 'Mejorado' if epicrisis.condicion_mejorado else 'No',
        'examenes_pendientes': 'Sí' if epicrisis.examenes_pendientes else 'No',
        'detalle_examenes_pendientes': epicrisis.detalle_examenes_pendientes,
        'examenes_realizados': 'Sí' if epicrisis.examenes_realizados else 'No',
        'detalle_examenes_realizados': epicrisis.detalle_examenes_realizados,
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
def perfil_usuario(request):
    perfil = request.user.perfilusuario
    plantillas = PlantillaTexto.objects.filter(usuario=request.user)
    return render(request, 'pacientes/perfil_usuario.html', {
        'perfil': perfil,
        'plantillas': plantillas,
    })


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


@login_required
def detalle_episodio(request, episodio_id):
    episodio = get_object_or_404(Episodio, id=episodio_id)
    evoluciones = episodio.evoluciones.all().order_by('-fecha')
    return render(request, 'pacientes/detalle_episodio.html', {
        'episodio': episodio,
        'evoluciones': evoluciones,
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


@login_required
def ultima_indicacion(request, paciente_id):
    paciente = get_object_or_404(Paciente, id=paciente_id)
    ultima = Indicacion.objects.filter(episodio__paciente=paciente).order_by('-fecha').first()
    data = {}
    if ultima:
        data = {
            'fecha': ultima.fecha.strftime('%Y-%m-%dT%H:%M'),
            'reposo': ultima.reposo,
            'regimen': ultima.regimen,
            'medicamentos': ultima.medicamentos,
            'infusiones': ultima.infusiones,
            'dispositivos': ultima.dispositivos,
            'otras': ultima.otras,
        }
    return JsonResponse(data)


@login_required
def obtener_plantillas(request):
    tipo = request.GET.get('tipo')
    plantillas = PlantillaTexto.objects.filter(usuario=request.user, tipo=tipo).values('id', 'titulo', 'contenido')
    return JsonResponse({'plantillas': list(plantillas)})


@login_required
def guardar_plantilla(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        contenido = request.POST.get('contenido', '')
        titulo = request.POST.get('titulo', '')
        PlantillaTexto.objects.create(usuario=request.user, tipo=tipo, contenido=contenido, titulo=titulo)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
def editar_plantilla(request, plantilla_id):
    plantilla = get_object_or_404(PlantillaTexto, id=plantilla_id, usuario=request.user)
    if request.method == 'POST':
        form = PlantillaTextoForm(request.POST, instance=plantilla)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plantilla modificada correctamente.')
            return redirect('perfil_usuario')
    else:
        form = PlantillaTextoForm(instance=plantilla)
    return render(request, 'pacientes/editar_plantilla.html', {'form': form})


@login_required
def eliminar_plantilla(request, plantilla_id):
    plantilla = get_object_or_404(PlantillaTexto, id=plantilla_id, usuario=request.user)
    if request.method == 'POST':
        plantilla.delete()
        messages.success(request, 'Plantilla eliminada correctamente.')
    return redirect('perfil_usuario')