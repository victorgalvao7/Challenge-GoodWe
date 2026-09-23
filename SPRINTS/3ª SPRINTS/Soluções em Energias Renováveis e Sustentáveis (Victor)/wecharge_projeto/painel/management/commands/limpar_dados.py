"""
Comando de manutenção: apaga TODOS os dados de contas e carregadores do
banco (útil pra zerar o ambiente de testes/demo antes de recomeçar).

Uso:
    python manage.py limpar_dados
        Apaga sessões de carregamento, pontos físicos, perfis e todas as
        contas de usuário QUE NÃO SEJAM superusuário (assim você não fica
        trancado para fora do /admin).

    python manage.py limpar_dados --incluir-superusuarios
        Igual ao acima, mas apaga literalmente tudo, incluindo
        superusuários. Depois disso você vai precisar rodar
        `python manage.py createsuperuser` de novo para acessar o /admin.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from contas.models import Perfil
from painel.models import Carregador, PontoCarregamento


class Command(BaseCommand):
    help = "Apaga todos os dados de contas e carregadores do banco de dados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--incluir-superusuarios",
            action="store_true",
            help="Também apaga contas de superusuário (cuidado: você perde o acesso ao /admin).",
        )

    def handle(self, *args, **opcoes):
        User = get_user_model()
        incluir_superusuarios = opcoes["incluir_superusuarios"]

        with transaction.atomic():
            qtd_sessoes, _ = Carregador.objects.all().delete()
            qtd_pontos, _ = PontoCarregamento.objects.all().delete()
            qtd_perfis, _ = Perfil.objects.all().delete()

            usuarios_qs = User.objects.all()
            if not incluir_superusuarios:
                usuarios_qs = usuarios_qs.exclude(is_superuser=True)
            qtd_usuarios, _ = usuarios_qs.delete()

        self.stdout.write(self.style.SUCCESS("Banco de dados limpo:"))
        self.stdout.write(f"  - {qtd_sessoes} sessão(ões) de carregamento removida(s)")
        self.stdout.write(f"  - {qtd_pontos} ponto(s) de carregamento removido(s)")
        self.stdout.write(f"  - {qtd_perfis} perfil(is) removido(s)")
        self.stdout.write(f"  - {qtd_usuarios} conta(s) de usuário removida(s)")
        if not incluir_superusuarios:
            restantes = User.objects.filter(is_superuser=True).count()
            if restantes:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ({restantes} superusuário(s) mantido(s) para você não perder o acesso ao /admin. "
                        "Use --incluir-superusuarios para apagar também.)"
                    )
                )
