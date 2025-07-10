from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from administrador.models import PerfilUsuario
from django.urls import reverse
from pacientes.models import Paciente, Episodio, Epicrisis, Antecedente


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

