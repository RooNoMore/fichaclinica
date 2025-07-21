from datetime import date, timedelta
from django.utils import timezone

from django.contrib.auth.models import User
from django.test import TestCase

from administrador.models import PerfilUsuario
from django.urls import reverse
from pacientes.models import Paciente, Episodio, Epicrisis, Antecedente, Evolucion


class PacienteEdadTests(TestCase):
    def test_edad_devuelta_correctamente(self):
        nacimiento = date(2000, 1, 1)
        paciente = Paciente.objects.create(nombre="Test", fecha_nacimiento=nacimiento)

        today = date.today()
        expected_age = (
            today.year
            - nacimiento.year
            - ((today.month, today.day) < (nacimiento.month, nacimiento.day))
        )

        self.assertEqual(paciente.edad(), expected_age)


class PerfilUsuarioSignalTests(TestCase):
    def test_creacion_automatica_perfil_usuario(self):
        user = User.objects.create_user(username="jdoe", password="secret")
        self.assertTrue(PerfilUsuario.objects.filter(user=user).exists())


class EpicrisisPacientePropertyTests(TestCase):
    def test_epicrisis_paciente_property(self):
        paciente = Paciente.objects.create(nombre="PropTest")
        episodio = Episodio.objects.create(paciente=paciente)
        epicrisis = Epicrisis.objects.create(
            episodio=episodio,
            diagnostico_egreso="dg",
            comentario_evolucion="c",
        )

        self.assertEqual(epicrisis.paciente, paciente)


class EpicrisisAntecedentesTests(TestCase):
    def test_ver_epicrisis_incluye_antecedentes_paciente(self):
        paciente = Paciente.objects.create(nombre="AnteTest")
        episodio = Episodio.objects.create(paciente=paciente)
        Epicrisis.objects.create(
            episodio=episodio,
            diagnostico_egreso="dg",
            comentario_evolucion="c",
        )
        Antecedente.objects.create(paciente=paciente, tipo="morbido", descripcion="HTA")
        Antecedente.objects.create(paciente=paciente, tipo="quirurgico", descripcion="Apendicectomía")

        user = User.objects.create_user(username="u", password="pw")
        self.client.login(username="u", password="pw")

        epicrisis = episodio.epicrisis
        url = reverse('ver_epicrisis', args=[epicrisis.id])
        response = self.client.get(url)
        self.assertContains(response, "HTA")
        self.assertContains(response, "Apendicectomía")


class EpisodiosPreviosTests(TestCase):
    def test_detalle_paciente_muestra_episodios_previos(self):
        user = User.objects.create_user(username="user", password="pw")
        self.client.login(username="user", password="pw")

        paciente = Paciente.objects.create(nombre="HospTest")
        ingreso = timezone.now() - timedelta(days=10)
        egreso = ingreso + timedelta(days=5)
        antiguo = Episodio.objects.create(
            paciente=paciente,
            fecha_ingreso=ingreso,
            fecha_egreso=egreso,
        )
        activo = Episodio.objects.create(paciente=paciente)

        url = reverse("detalle_paciente", args=[paciente.id])
        response = self.client.get(url)

        episodios = list(response.context["episodios_previos"])
        self.assertEqual(episodios, [antiguo])


class DarDeAltaTests(TestCase):
    def test_dar_de_alta_actualiza_episodio(self):
        paciente = Paciente.objects.create(nombre="Alta")
        episodio = Episodio.objects.create(paciente=paciente)

        paciente.dar_de_alta()

        episodio.refresh_from_db()
        self.assertIsNotNone(episodio.fecha_egreso)
        self.assertTrue(episodio.finalizado)


class DetalleEpisodioTests(TestCase):
    def test_detalle_episodio_muestra_evoluciones(self):
        user = User.objects.create_user(username="u", password="pw")
        paciente = Paciente.objects.create(nombre="EvoTest")
        episodio = Episodio.objects.create(paciente=paciente)
        Evolucion.objects.create(episodio=episodio, contenido="nota")

        paciente.dar_de_alta()
        self.client.login(username="u", password="pw")

        url = reverse('detalle_episodio', args=[episodio.id])
        response = self.client.get(url)
        self.assertContains(response, "nota")


class EpicrisisAutorTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="med", password="pw")
        self.client.login(username="med", password="pw")
        self.paciente = Paciente.objects.create(nombre="Aut")
        self.episodio = Episodio.objects.create(paciente=self.paciente)

    def _post_data(self, accion):
        url = reverse('crear_epicrisis', args=[self.paciente.id])
        data = {
            'diagnostico_egreso': 'dg',
            'comentario_evolucion': 'c',
            'indicaciones_generales': '',
            'indicaciones_controles': '',
            'examenes_pendientes': 'False',
            'detalle_examenes_pendientes': '',
            'examenes_realizados': 'False',
            'detalle_examenes_realizados': '',
            'condicion_mejorado': 'True',
            'accion': accion,
        }
        self.client.post(url, data)

    def test_borrador_sin_autor(self):
        self._post_data('guardar')
        epicrisis = Epicrisis.objects.get(episodio=self.episodio)
        self.assertIsNone(epicrisis.autor)
        self.assertFalse(epicrisis.finalizado)

    def test_finalizar_asigna_autor(self):
        self._post_data('finalizar')
        epicrisis = Epicrisis.objects.get(episodio=self.episodio)
        self.assertEqual(epicrisis.autor, self.user)
        self.assertTrue(epicrisis.finalizado)


