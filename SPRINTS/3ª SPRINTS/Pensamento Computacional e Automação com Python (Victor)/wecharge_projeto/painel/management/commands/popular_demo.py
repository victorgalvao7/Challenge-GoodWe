"""
Comando de demonstração: deixa o banco pronto para gravar um vídeo do
WeCharge, com contas com senha conhecida, carregadores em uso agora e
histórico de recargas já concluídas e pagas.

Uso:
    python manage.py popular_demo

Pode rodar quantas vezes quiser: ele apaga só os dados de demonstração
anteriores (motoristas de exemplo e as sessões deles) e recria tudo com
horários atualizados. Rode de novo logo antes de gravar para que as
recargas "em andamento" tenham começado há poucos minutos.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from contas.models import Perfil
from painel.models import (
    BATTERY_CAPACITY_KWH,
    CHARGER_POWER_KW,
    Carregador,
    PontoCarregamento,
)

SENHA_DEMO = "Wecharge2026"

ADMINS = [
    ("adm1", "adm1@wecharge.exemplo", "Operador Tatuapé"),
    ("adm2", "adm2@wecharge.exemplo", "Operador Zona Sul"),
    ("adm3", "adm3@wecharge.exemplo", "Operador Centro"),
]

MOTORISTAS = [
    ("motorista1", "ana.souza@wecharge.exemplo", "Ana", "Souza", "BYD Dolphin"),
    ("motorista2", "bruno.lima@wecharge.exemplo", "Bruno", "Lima", "Renault Kwid E-Tech"),
    ("motorista3", "carla.mendes@wecharge.exemplo", "Carla", "Mendes", "GWM Ora 03"),
    ("motorista4", "diego.rocha@wecharge.exemplo", "Diego", "Rocha", "Volvo EX30"),
]

SUPERUSUARIO = ("admin", "admin@wecharge.exemplo")


class Command(BaseCommand):
    help = "Popula o banco com contas, recargas em andamento e histórico para demonstração."

    def handle(self, *args, **opcoes):
        random.seed(2026)
        User = get_user_model()
        agora = timezone.now()

        with transaction.atomic():
            # 1) Administradores (donos dos carregadores) com senha conhecida
            admins = []
            for username, email, nome in ADMINS:
                u, _ = User.objects.get_or_create(username=username, defaults={"email": email})
                u.email = email
                u.is_staff = True
                u.is_active = True
                u.set_password(SENHA_DEMO)
                u.save()
                Perfil.objects.update_or_create(usuario=u, defaults={"nome_completo": nome, "cidade": "São Paulo"})
                admins.append(u)

            # 2) Superusuário para o /admin do Django
            username, email = SUPERUSUARIO
            su, _ = User.objects.get_or_create(username=username, defaults={"email": email})
            su.email = email
            su.is_staff = True
            su.is_superuser = True
            su.is_active = True
            su.set_password(SENHA_DEMO)
            su.save()

            # 3) Motoristas de exemplo (recriados do zero a cada execução;
            #    apagar o usuário apaga junto as sessões dele)
            User.objects.filter(username__in=[m[0] for m in MOTORISTAS]).delete()
            motoristas = []
            for username, email, nome, sobrenome, carro in MOTORISTAS:
                u = User.objects.create_user(
                    username=username, email=email, password=SENHA_DEMO,
                    first_name=nome, last_name=sobrenome,
                )
                Perfil.objects.create(
                    usuario=u, nome_completo=f"{nome} {sobrenome}",
                    telefone="(11) 9" + "".join(random.choices("0123456789", k=8)),
                    cidade="São Paulo",
                )
                motoristas.append((u, carro))

            # Garante que todos os pontos estão ativos e sem sessão presa
            PontoCarregamento.objects.update(ativo=True)
            Carregador.objects.exclude(status=Carregador.STATUS_CONCLUIDO).filter(
                ponto__isnull=False
            ).delete()

            pontos = list(PontoCarregamento.objects.select_related("dono").order_by("id"))
            if not pontos:
                self.stdout.write(self.style.ERROR("Nenhum ponto de carregamento no banco."))
                return

            # 4) Histórico: recargas concluídas e pagas nos últimos 30 dias
            total_hist = 0
            for ponto in pontos:
                qtd = random.randint(6, 12) if ponto.dono.username == "adm1" else random.randint(3, 7)
                for _ in range(qtd):
                    usuario, carro = random.choice(motoristas)
                    inicio = agora - timedelta(
                        days=random.randint(1, 30),
                        hours=random.randint(0, 12),
                        minutes=random.randint(0, 59),
                    )
                    self._criar_concluida(ponto, usuario, carro, inicio)
                    total_hist += 1

            # 5) Recargas acontecendo agora (aparecem como "Em uso" no painel
            #    do operador e com progresso ao vivo no painel do motorista)
            pontos_adm1 = [p for p in pontos if p.dono.username == "adm1"]
            ativos = [
                (pontos_adm1[0], motoristas[0], 35),   # Ana, começou há 35 min
                (pontos_adm1[2], motoristas[1], 12),   # Bruno, começou há 12 min
            ]
            for ponto, (usuario, carro), minutos in ativos:
                c = Carregador.objects.create(
                    usuario=usuario, ponto=ponto,
                    identificador_fisico=ponto.identificador_fisico,
                    metodo_identificacao="qrcode", apelido=carro,
                    status=Carregador.STATUS_CARREGANDO,
                    inicio_carregamento=agora - timedelta(minutes=minutos),
                    endereco=ponto.endereco, latitude=ponto.latitude, longitude=ponto.longitude,
                    tarifa_kwh_aplicada=ponto.preco_kwh,
                )
                Carregador.objects.filter(pk=c.pk).update(
                    criado_em=agora - timedelta(minutes=minutos + 2)
                )

        self.stdout.write(self.style.SUCCESS(
            f"Pronto! {total_hist} recargas no histórico e {len(ativos)} carregando agora.\n"
            f"Senha de todas as contas de demonstração: {SENHA_DEMO}\n"
            "  Operador (painel /operador/): adm1, adm2, adm3\n"
            "  Motoristas (painel /painel/): motorista1 (com recarga em andamento), motorista2, motorista3, motorista4\n"
            "  Superusuário (/admin/): admin"
        ))

    def _criar_concluida(self, ponto, usuario, carro, inicio):
        duracao_min = random.randint(20, 330)
        horas = duracao_min / 60
        energia = min(CHARGER_POWER_KW * horas, BATTERY_CAPACITY_KWH)
        tarifa = float(ponto.preco_kwh)

        # Tempo que o carro ficou plugado depois da bateria cheia (paga taxa)
        horas_para_encher = BATTERY_CAPACITY_KWH / CHARGER_POWER_KW
        excedente_h = max(horas - horas_para_encher, 0)
        custo_energia = energia * tarifa
        custo_excedente = CHARGER_POWER_KW * tarifa * excedente_h

        fim = inicio + timedelta(minutes=duracao_min)
        pago_em = fim + timedelta(minutes=random.randint(1, 5))

        c = Carregador.objects.create(
            usuario=usuario, ponto=ponto,
            identificador_fisico=ponto.identificador_fisico,
            metodo_identificacao=random.choice(["qrcode", "token"]),
            apelido=carro,
            status=Carregador.STATUS_CONCLUIDO,
            inicio_carregamento=inicio,
            momento_bateria_cheia=(inicio + timedelta(hours=horas_para_encher)) if excedente_h else None,
            resumo_final={
                "energia_kwh": round(energia, 3),
                "tarifa_kwh": tarifa,
                "custo_energia": round(custo_energia, 2),
                "tempo_decorrido_s": duracao_min * 60,
                "tempo_excedente_s": int(excedente_h * 3600),
                "custo_excedente": round(custo_excedente, 2),
                "custo_total": round(custo_energia + custo_excedente, 2),
                "potencia_kw": CHARGER_POWER_KW,
            },
            forma_pagamento=random.choice(["pix", "pix", "credito", "debito"]),
            concluido_em=pago_em,
            endereco=ponto.endereco, latitude=ponto.latitude, longitude=ponto.longitude,
            tarifa_kwh_aplicada=Decimal(str(ponto.preco_kwh)),
        )
        # criado_em é auto_now_add: ajusta depois para a data "real" da recarga
        Carregador.objects.filter(pk=c.pk).update(criado_em=inicio - timedelta(minutes=1))
