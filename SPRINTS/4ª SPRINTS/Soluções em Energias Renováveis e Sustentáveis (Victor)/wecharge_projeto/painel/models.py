"""
Modelo de dados dos carregadores de veículos elétricos.

Esta é a "tradução" para Django do protótipo Flask original
(wecharge_site/app.py). A lógica de cálculo de energia/custo é a mesma,
só trocando o dicionário em memória (CHARGERS = {}) por um modelo real
salvo no banco (SQLite por padrão) e ligado ao usuário logado
(request.user), em vez do usuário simulado (SIMULATED_USER).

Ver REGISTRO_INTEGRACAO.md na raiz do projeto para o histórico completo
de como os dois projetos originais foram unidos.
"""
import random
import string
import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

# ---------------------------------------------------------------------------
# CONSTANTES DE ENERGIA
# Mesmos valores pesquisados no projeto original (ver CONTEXT_LOG.md do
# projeto wecharge_site) — mantidos aqui centralizados para fácil ajuste
# quando o time tiver os dados reais do carregador físico do GoodWe Challenge.
# ---------------------------------------------------------------------------
CHARGER_POWER_KW = 7.4          # potência média de carregador AC (wallbox monofásica)
TARIFA_KWH = 0.79               # R$/kWh — tarifa residencial convencional Enel SP (Grupo B1), 2026
BATTERY_CAPACITY_KWH = 40.0     # capacidade média de bateria de VE popular

# Token do carregador: exatamente 5 caracteres, letras e/ou números.
TOKEN_TAMANHO = 5
validar_token_fisico = RegexValidator(
    regex=rf"^[A-Z0-9]{{{TOKEN_TAMANHO}}}$",
    message=f"O token deve ter exatamente {TOKEN_TAMANHO} caracteres (letras e números).",
)

# Caracteres usados para gerar o token automaticamente. Evitamos 0/O e 1/I
# para não confundir o operador na hora de imprimir/ler o QR Code.
_ALFABETO_TOKEN = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def gerar_token_fisico_aleatorio():
    """Gera um token de TOKEN_TAMANHO caracteres, aleatório e ainda não
    usado por nenhum outro carregador. Quem cadastra o carregador não
    escolhe mais o token — ele é gerado aqui e salvo no banco."""
    while True:
        candidato = "".join(random.choices(_ALFABETO_TOKEN, k=TOKEN_TAMANHO))
        if not PontoCarregamento.objects.filter(identificador_fisico=candidato).exists():
            return candidato


class PontoCarregamento(models.Model):
    """Carregador físico cadastrado e administrado por um operador."""

    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pontos_carregamento",
        limit_choices_to={"is_staff": True},
    )
    nome = models.CharField(max_length=80)
    identificador_fisico = models.CharField(
        max_length=TOKEN_TAMANHO,
        unique=True,
        blank=True,
        validators=[validar_token_fisico],
        help_text=(
            "Token de 5 caracteres, gerado automaticamente ao cadastrar o "
            "carregador e impresso no QR Code."
        ),
    )
    endereco = models.CharField(max_length=200)
    latitude = models.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    longitude = models.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    preco_kwh = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Preço por kWh",
        help_text="Valor em reais cobrado do motorista por kWh consumido.",
    )
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Ponto de carregamento"
        verbose_name_plural = "Pontos de carregamento"

    def __str__(self):
        return f"{self.nome} ({self.identificador_fisico})"

    def save(self, *args, **kwargs):
        if self.identificador_fisico:
            self.identificador_fisico = self.identificador_fisico.strip().upper()
        else:
            # Ninguém escolhe mais o token na hora de cadastrar: ele é
            # sorteado aqui e persistido no banco.
            self.identificador_fisico = gerar_token_fisico_aleatorio()
        super().save(*args, **kwargs)

    @property
    def sessao_ativa(self):
        return self.sessoes.exclude(status=Carregador.STATUS_CONCLUIDO).first()

    @property
    def disponivel(self):
        return self.ativo and self.sessao_ativa is None


class Carregador(models.Model):
    """Uma sessão de recarga associada a um usuário e a um ponto físico."""

    STATUS_ADICIONADO = "adicionado"
    STATUS_LIBERADO = "liberado"
    STATUS_CARREGANDO = "carregando"
    STATUS_AGUARDANDO_PAGAMENTO = "aguardando_pagamento"
    STATUS_CONCLUIDO = "concluido"

    STATUS_CHOICES = [
        (STATUS_ADICIONADO, "Aguardando liberação"),
        (STATUS_LIBERADO, "Liberado"),
        (STATUS_CARREGANDO, "Carregando"),
        (STATUS_AGUARDANDO_PAGAMENTO, "Pagamento pendente"),
        (STATUS_CONCLUIDO, "Concluído"),
    ]

    METODO_CHOICES = [
        ("token", "Token"),
        ("qrcode", "QR Code"),
    ]

    FORMA_PAGAMENTO_CHOICES = [
        ("pix", "Pix"),
        ("credito", "Cartão de crédito"),
        ("debito", "Cartão de débito"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carregadores",
    )
    ponto = models.ForeignKey(
        PontoCarregamento,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sessoes",
    )
    identificador_fisico = models.CharField(max_length=40)
    metodo_identificacao = models.CharField(max_length=10, choices=METODO_CHOICES)
    apelido = models.CharField(max_length=80)
    status = models.CharField(
        max_length=25, choices=STATUS_CHOICES, default=STATUS_ADICIONADO
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    inicio_carregamento = models.DateTimeField(null=True, blank=True)
    momento_bateria_cheia = models.DateTimeField(null=True, blank=True)
    resumo_final = models.JSONField(null=True, blank=True)
    forma_pagamento = models.CharField(
        max_length=10, choices=FORMA_PAGAMENTO_CHOICES, null=True, blank=True
    )
    concluido_em = models.DateTimeField(null=True, blank=True)

    # Cópia da localização mantida para compatibilidade com sessões antigas.
    # Novos cadastros usam PontoCarregamento como fonte oficial do mapa.
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    endereco = models.CharField(max_length=200, blank=True)
    tarifa_kwh_aplicada = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Preço por kWh congelado no início desta sessão.",
    )

    class Meta:
        ordering = ["-criado_em"]
        constraints = [
            models.UniqueConstraint(
                fields=["ponto"],
                condition=Q(ponto__isnull=False) & ~Q(status="concluido"),
                name="uma_sessao_ativa_por_ponto",
            )
        ]

    def __str__(self):
        return f"{self.apelido} ({self.usuario})"

    def tarifa_cliente_kwh(self):
        if self.tarifa_kwh_aplicada is not None:
            return float(self.tarifa_kwh_aplicada)
        if self.ponto_id:
            return float(self.ponto.preco_kwh)
        return TARIFA_KWH

    # -----------------------------------------------------------------
    # Cálculo em tempo real (equivalente à função charger_publico do
    # protótipo Flask original)
    # -----------------------------------------------------------------
    def estado_atual(self):
        """
        Retorna um dicionário com o estado do carregador, calculando os
        valores de energia/custo em tempo real quando está carregando.
        """
        out = {
            "id": str(self.id),
            "apelido": self.apelido,
            "identificador_fisico": self.identificador_fisico,
            "status": self.status,
            "ponto": self.ponto.nome if self.ponto else None,
            "endereco": self.ponto.endereco if self.ponto else self.endereco,
            "tarifa_kwh": self.tarifa_cliente_kwh(),
        }

        if self.status == self.STATUS_CARREGANDO and self.inicio_carregamento:
            agora = timezone.now()
            elapsed_h = (agora - self.inicio_carregamento).total_seconds() / 3600.0
            energia_kwh = min(CHARGER_POWER_KW * elapsed_h, BATTERY_CAPACITY_KWH)
            bateria_cheia = energia_kwh >= BATTERY_CAPACITY_KWH

            horas_para_encher = BATTERY_CAPACITY_KWH / CHARGER_POWER_KW
            momento_bateria_cheia = self.inicio_carregamento + timezone.timedelta(
                hours=horas_para_encher
            )
            if bateria_cheia and not self.momento_bateria_cheia:
                self.momento_bateria_cheia = momento_bateria_cheia
                self.save(update_fields=["momento_bateria_cheia"])

            tempo_excedente_h = 0.0
            if bateria_cheia:
                tempo_excedente_h = (
                    agora - (self.momento_bateria_cheia or momento_bateria_cheia)
                ).total_seconds() / 3600.0
                tempo_excedente_h = max(tempo_excedente_h, 0.0)

            tarifa_kwh = self.tarifa_cliente_kwh()
            custo_energia = energia_kwh * tarifa_kwh
            custo_excedente = CHARGER_POWER_KW * tarifa_kwh * tempo_excedente_h

            out["energia_kwh"] = round(energia_kwh, 3)
            out["percentual_bateria"] = round(
                min(energia_kwh / BATTERY_CAPACITY_KWH * 100, 100), 1
            )
            out["bateria_cheia"] = bateria_cheia
            out["tempo_decorrido_s"] = int((agora - self.inicio_carregamento).total_seconds())
            out["tempo_excedente_s"] = int(tempo_excedente_h * 3600)
            out["custo_energia"] = round(custo_energia, 2)
            out["custo_excedente"] = round(custo_excedente, 2)
            out["custo_total_parcial"] = round(custo_energia + custo_excedente, 2)

        return out
