# Remove a funcionalidade de "Distribuidora de energia da região".
# O campo era usado só para calcular o custo/lucro do operador; como o
# lucro deixou de ser exibido (agora o painel mostra só a Receita),
# o campo e o modelo inteiro podem ser removidos com segurança.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("painel", "0005_pontocarregamento_carregador_ponto_e_tarifa"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="carregador",
            name="distribuidora",
        ),
        migrations.RemoveField(
            model_name="pontocarregamento",
            name="distribuidora",
        ),
        migrations.DeleteModel(
            name="Distribuidora",
        ),
    ]
