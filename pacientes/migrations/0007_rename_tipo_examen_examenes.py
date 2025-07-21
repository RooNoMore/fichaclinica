from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('pacientes', '0006_solicitudexamen_categoria_evaluacionenfermeria_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='solicitudexamen',
            old_name='tipo_examen',
            new_name='examenes',
        ),
        migrations.AlterField(
            model_name='solicitudexamen',
            name='examenes',
            field=models.TextField(),
        ),
    ]
