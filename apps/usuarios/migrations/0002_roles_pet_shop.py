"""Actualiza los roles de usuario al alcance de pet shop."""
from django.db import migrations, models


def migrar_roles(apps, schema_editor):
    Usuario = apps.get_model("usuarios", "Usuario")
    Usuario.objects.filter(rol="VETERINARIO").update(rol="VENDEDOR")


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(migrar_roles, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="usuario",
            name="rol",
            field=models.CharField(
                choices=[
                    ("CLIENTE", "Cliente"),
                    ("VENDEDOR", "Vendedor / Staff"),
                    ("ADMINISTRATIVO", "Administrativo"),
                ],
                default="CLIENTE",
                max_length=20,
                verbose_name="Rol institucional",
            ),
        ),
    ]
