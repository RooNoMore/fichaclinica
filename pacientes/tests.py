from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase

from administrador.models import PerfilUsuario
from .models import Paciente


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

