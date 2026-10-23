"""
Views do painel do usuário comum (motorista): fluxo completo do
carregador (adicionar -> carregar -> finalizar -> pagar).

Portado do protótipo Flask original (wecharge_site/app.py). A diferença
principal é que aqui os carregadores pertencem de verdade ao usuário
logado (request.user) e ficam salvos no banco de dados (modelo
Carregador), em vez de um dicionário em memória com um usuário simulado.
"""
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Carregador, CHARGER_POWER_KW, PontoCarregamento
from .ioi_chat import responder_ioi_chat, IoIChatIndisponivel


def _gerar_apelido(identificador_fisico):
    return f"Carregador {identificador_fisico}"


def _formatar_tempo(total_segundos):
    total_segundos = int(total_segundos or 0)
    h, resto = divmod(total_segundos, 3600)
    m, s = divmod(resto, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ---------------------------------------------------------------------------
# PÁGINAS
# ---------------------------------------------------------------------------

@login_required
def painel(request):
    """Lista os carregadores ativos do usuário logado (sem os já concluídos,
    que agora ficam no histórico)."""
    carregadores_qs = Carregador.objects.filter(usuario=request.user).exclude(
        status=Carregador.STATUS_CONCLUIDO
    )
    carregadores = [c.estado_atual() for c in carregadores_qs]

    contexto = {
        "titulo": "Meu Painel",
        "carregadores": carregadores,
        "ioi_chat_disponivel": bool(settings.OPENAI_API_KEY),
    }
    return render(request, "painel/index.html", contexto)


@login_required
def historico(request):
    """Lista os carregamentos já concluídos e pagos do usuário logado."""
    carregadores = Carregador.objects.filter(
        usuario=request.user, status=Carregador.STATUS_CONCLUIDO
    ).order_by("-concluido_em", "-criado_em")

    contexto = {
        "titulo": "Histórico de carregamentos",
        "carregadores": carregadores,
    }
    return render(request, "painel/historico.html", contexto)


@login_required
def adicionar(request):
    return render(request, "painel/adicionar.html")


@login_required
def detalhe_carregador(request, charger_id):
    c = get_object_or_404(Carregador, id=charger_id, usuario=request.user)
    contexto = {"carregador": c.estado_atual()}

    if c.status == Carregador.STATUS_CONCLUIDO:
        r = c.resumo_final or {}
        tempo_excedente_s = r.get("tempo_excedente_s") or 0
        contexto.update({
            "resumo": r,
            "tempo_decorrido_fmt": _formatar_tempo(r.get("tempo_decorrido_s") or 0),
            "excedente_min": tempo_excedente_s // 60,
            "excedente_seg": tempo_excedente_s % 60,
            "forma_pagamento": c.forma_pagamento,
            "concluido_em": c.concluido_em,
        })

    return render(request, "painel/carregador.html", contexto)


@login_required
def pagamento(request, charger_id):
    c = get_object_or_404(Carregador, id=charger_id, usuario=request.user)
    if c.status != Carregador.STATUS_AGUARDANDO_PAGAMENTO:
        return redirect("painel:painel")

    r = c.resumo_final or {}
    tempo_excedente_s = r.get("tempo_excedente_s") or 0
    contexto = {
        "carregador": c,
        "r": r,
        "excedente_min": tempo_excedente_s // 60,
        "excedente_seg": tempo_excedente_s % 60,
    }
    return render(request, "painel/pagamento.html", contexto)


@login_required
def pagamento_sucesso(request, charger_id):
    c = get_object_or_404(Carregador, id=charger_id, usuario=request.user)
    contexto = {"carregador": c}
    return render(request, "painel/sucesso.html", contexto)


# ---------------------------------------------------------------------------
# API (chamada via fetch() pelo JS das páginas acima)
# ---------------------------------------------------------------------------

@login_required
def api_carregadores_proximos(request):
    """
    Devolve os pontos físicos ativos cadastrados pelos operadores, com
    localização, preço e disponibilidade para o mapa do motorista.
    """
    pontos = PontoCarregamento.objects.filter(ativo=True).prefetch_related("sessoes")

    dados = []
    for ponto in pontos:
        em_uso = any(
            sessao.status != Carregador.STATUS_CONCLUIDO
            for sessao in ponto.sessoes.all()
        )
        dados.append(
            {
                "id": ponto.id,
                "apelido": ponto.nome,
                "identificador_fisico": ponto.identificador_fisico,
                "endereco": ponto.endereco,
                "latitude": ponto.latitude,
                "longitude": ponto.longitude,
                "preco_kwh": float(ponto.preco_kwh),
                "status": "em_uso" if em_uso else "disponivel",
                "status_label": "Em uso" if em_uso else "Disponível",
            }
        )
    return JsonResponse({"carregadores": dados})


@login_required
def api_ioi_chat(request):
    """Endpoint do IoI Chat: recebe a pergunta do usuário (e, se
    disponível, sua localização atual) e devolve a resposta da IA."""
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)

    try:
        dados = json.loads(request.body or "{}")
    except (ValueError, TypeError):
        return JsonResponse({"erro": "Corpo da requisição inválido."}, status=400)

    mensagem = (dados.get("mensagem") or "").strip()
    if not mensagem:
        return JsonResponse({"erro": "Digite uma pergunta."}, status=400)
    if len(mensagem) > 500:
        return JsonResponse({"erro": "Mensagem muito longa."}, status=400)

    latitude = dados.get("latitude")
    longitude = dados.get("longitude")

    try:
        resposta, destaque = responder_ioi_chat(mensagem, latitude, longitude)
    except IoIChatIndisponivel as exc:
        return JsonResponse({"erro": str(exc)}, status=503)

    return JsonResponse({"resposta": resposta, "destaque": destaque})


@login_required
def api_add_charger(request):
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)

    try:
        data = json.loads(request.body or "{}")
    except (ValueError, TypeError):
        return JsonResponse({"erro": "Dados inválidos."}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"erro": "Dados inválidos."}, status=400)
    metodo = data.get("metodo")
    valor = (data.get("valor") or "").strip().upper()

    if metodo == "token":
        if not valor or len(valor) > 5 or not valor.isalnum():
            return JsonResponse(
                {"erro": "Token inválido. Use até 5 letras/números."}, status=400
            )
        identificador_fisico = valor
    elif metodo == "qrcode":
        if not valor:
            return JsonResponse({"erro": "QR Code não pôde ser lido."}, status=400)
        identificador_fisico = valor[:40]
    else:
        return JsonResponse({"erro": "Método de identificação inválido."}, status=400)

    ponto = PontoCarregamento.objects.filter(
        identificador_fisico__iexact=identificador_fisico,
        ativo=True,
    ).first()
    if ponto is None:
        return JsonResponse(
            {"erro": "Carregador não cadastrado ou indisponível."}, status=404
        )

    # O usuário só pode ter UM carregador em andamento por vez — inclusive
    # com pagamento pendente. Sem isso, dava pra sair usando carregador
    # atrás de carregador sem nunca fechar a conta do anterior.
    sessao_pendente = (
        Carregador.objects.filter(usuario=request.user)
        .exclude(status=Carregador.STATUS_CONCLUIDO)
        .first()
    )
    if sessao_pendente is not None:
        if sessao_pendente.status == Carregador.STATUS_AGUARDANDO_PAGAMENTO:
            mensagem = (
                "Você tem um pagamento pendente. Finalize o pagamento do "
                "carregador anterior antes de usar outro."
            )
        else:
            mensagem = (
                "Você já tem um carregamento em andamento. Finalize-o antes "
                "de usar outro carregador."
            )
        return JsonResponse(
            {
                "erro": mensagem,
                "carregador_pendente_id": str(sessao_pendente.id),
            },
            status=409,
        )

    try:
        with transaction.atomic():
            ponto = PontoCarregamento.objects.select_for_update().get(pk=ponto.pk)
            if ponto.sessoes.exclude(status=Carregador.STATUS_CONCLUIDO).exists():
                return JsonResponse(
                    {"erro": "Este carregador já está em uso."}, status=409
                )
            c = Carregador.objects.create(
                usuario=request.user,
                ponto=ponto,
                identificador_fisico=ponto.identificador_fisico,
                metodo_identificacao=metodo,
                apelido=ponto.nome,
                endereco=ponto.endereco,
                latitude=ponto.latitude,
                longitude=ponto.longitude,
                tarifa_kwh_aplicada=ponto.preco_kwh,
            )
    except IntegrityError:
        return JsonResponse({"erro": "Este carregador já está em uso."}, status=409)
    return JsonResponse({"ok": True, "carregador": c.estado_atual()})


@login_required
def api_iniciar(request, charger_id):
    """Conecta e já inicia o carregamento numa única ação — antes exigia
    "liberar" e depois "iniciar" em dois cliques separados, sem necessidade
    real (não existe hardware físico esperando a liberação nesta simulação),
    então agora vai direto de "adicionado" para "carregando"."""
    c = get_object_or_404(Carregador, id=charger_id, usuario=request.user)
    if c.status not in (Carregador.STATUS_ADICIONADO, Carregador.STATUS_LIBERADO):
        return JsonResponse(
            {"erro": "Este carregador não pode ser iniciado agora."}, status=400
        )
    c.status = Carregador.STATUS_CARREGANDO
    c.inicio_carregamento = timezone.now()
    c.momento_bateria_cheia = None
    c.save(update_fields=["status", "inicio_carregamento", "momento_bateria_cheia"])
    return JsonResponse({"ok": True, "carregador": c.estado_atual()})


@login_required
def api_status(request, charger_id):
    c = get_object_or_404(Carregador, id=charger_id, usuario=request.user)
    return JsonResponse({"ok": True, "carregador": c.estado_atual()})


@login_required
def api_finalizar(request, charger_id):
    c = get_object_or_404(Carregador, id=charger_id, usuario=request.user)
    if c.status != Carregador.STATUS_CARREGANDO:
        return JsonResponse(
            {"erro": "Este carregador não está carregando."}, status=400
        )

    estado = c.estado_atual()
    c.resumo_final = {
        "energia_kwh": estado["energia_kwh"],
        "tarifa_kwh": estado["tarifa_kwh"],
        "custo_energia": estado["custo_energia"],
        "tempo_decorrido_s": estado["tempo_decorrido_s"],
        "tempo_excedente_s": estado["tempo_excedente_s"],
        "custo_excedente": estado["custo_excedente"],
        "custo_total": estado["custo_total_parcial"],
        "potencia_kw": CHARGER_POWER_KW,
    }
    c.status = Carregador.STATUS_AGUARDANDO_PAGAMENTO
    c.save(update_fields=["resumo_final", "status"])
    return JsonResponse({"ok": True, "resumo": c.resumo_final})


@login_required
def api_pagar(request, charger_id):
    c = get_object_or_404(Carregador, id=charger_id, usuario=request.user)
    if c.status != Carregador.STATUS_AGUARDANDO_PAGAMENTO:
        return JsonResponse(
            {"erro": "Não há pagamento pendente para este carregador."}, status=400
        )

    data = json.loads(request.body or "{}")
    metodo = data.get("metodo")
    if metodo not in ("pix", "credito", "debito"):
        return JsonResponse({"erro": "Forma de pagamento inválida."}, status=400)

    c.forma_pagamento = metodo
    c.status = Carregador.STATUS_CONCLUIDO
    c.concluido_em = timezone.now()
    c.save(update_fields=["forma_pagamento", "status", "concluido_em"])
    return JsonResponse({"ok": True})


@login_required
def api_reutilizar(request, charger_id):
    """Libera de novo o mesmo carregador físico para uma nova sessão,
    a partir do histórico. Mantém o mesmo registro (apelido, identificador
    físico), só reinicia o ciclo de carregamento."""
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)

    c = get_object_or_404(Carregador, id=charger_id, usuario=request.user)
    if c.status != Carregador.STATUS_CONCLUIDO:
        return JsonResponse(
            {"erro": "Este carregador não está concluído."}, status=400
        )

    if c.ponto and not c.ponto.ativo:
        return JsonResponse(
            {"erro": "Este carregador está temporariamente indisponível."}, status=409
        )

    # Mesma regra do api_add_charger: não pode reabrir este carregador se
    # já existe outro em andamento (nem com pagamento pendente).
    sessao_pendente = (
        Carregador.objects.filter(usuario=request.user)
        .exclude(status=Carregador.STATUS_CONCLUIDO)
        .exclude(pk=c.pk)
        .first()
    )
    if sessao_pendente is not None:
        if sessao_pendente.status == Carregador.STATUS_AGUARDANDO_PAGAMENTO:
            mensagem = (
                "Você tem um pagamento pendente. Finalize o pagamento do "
                "carregador anterior antes de usar outro."
            )
        else:
            mensagem = (
                "Você já tem um carregamento em andamento. Finalize-o antes "
                "de usar outro carregador."
            )
        return JsonResponse(
            {
                "erro": mensagem,
                "carregador_pendente_id": str(sessao_pendente.id),
            },
            status=409,
        )

    try:
        with transaction.atomic():
            if c.ponto:
                ponto = PontoCarregamento.objects.select_for_update().get(pk=c.ponto_id)
                if ponto.sessoes.exclude(
                    status=Carregador.STATUS_CONCLUIDO
                ).exclude(pk=c.pk).exists():
                    return JsonResponse(
                        {"erro": "Este carregador já está em uso."}, status=409
                    )
                c.tarifa_kwh_aplicada = ponto.preco_kwh

            c.status = Carregador.STATUS_LIBERADO
            c.inicio_carregamento = None
            c.momento_bateria_cheia = None
            c.resumo_final = None
            c.forma_pagamento = None
            c.concluido_em = None
            c.save(update_fields=[
                "status", "inicio_carregamento", "momento_bateria_cheia",
                "resumo_final", "forma_pagamento", "concluido_em",
                "tarifa_kwh_aplicada",
            ])
    except IntegrityError:
        return JsonResponse({"erro": "Este carregador já está em uso."}, status=409)
    return JsonResponse({"ok": True, "carregador": c.estado_atual()})
