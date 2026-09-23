import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("painel", "0006_remove_distribuidora"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pontocarregamento",
            name="identificador_fisico",
            field=models.CharField(
                help_text="Token de 5 caracteres (letras e números), impresso no QR Code do carregador.",
                max_length=5,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        message="O token deve ter exatamente 5 caracteres (letras e números).",
                        regex="^[A-Z0-9]{5}$",
                    )
                ],
            ),
        ),
    ]
