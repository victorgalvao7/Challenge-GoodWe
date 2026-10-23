from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from painel.models import Carregador, CHARGER_POWER_KW, PontoCarregamento

from .forms import PontoCarregamentoForm


def eh_administrador(user):
    return user.is_authenticated and user.is_staff


def _resumo_financeiro(sessoes):
    energia_total_kwh = 0.0
    receita_total = 0.0

    for sessao in sessoes:
        resumo = sessao.resumo_final or {}
        energia_total_kwh += resumo.get("energia_kwh") or 0
        receita_total += resumo.get("custo_total") or 0

    return {
        "energia_total_kwh": round(energia_total_kwh, 2),
        "receita_total": round(receita_total, 2),
    }


def _criar_pontos_do_formulario(form, dono):
    """Cria 1 ou mais PontoCarregamento com os mesmos dados do formulário
    (nome, endereço, coordenadas, preço), variando só o token, que é
    gerado automaticamente para cada um. Retorna a lista de pontos criados."""
    quantidade = form.cleaned_data.get("quantidade", 1)
    pontos_criados = []
    for _ in range(quantidade):
        ponto = PontoCarregamento(
            dono=dono,
            nome=form.cleaned_data["nome"],
            endereco=form.cleaned_data["endereco"],
            latitude=form.cleaned_data["latitude"],
            longitude=form.cleaned_data["longitude"],
            preco_kwh=form.cleaned_data["preco_kwh"],
            ativo=form.cleaned_data["ativo"],
        )
        ponto.save()  # token gerado automaticamente aqui dentro
        pontos_criados.append(ponto)
    return pontos_criados


@login_required
@user_passes_test(eh_administrador, login_url="painel:painel")
def painel(request):
    """Painel do dono com pontos, sessões em uso e renda da própria conta."""
    if request.method == "POST":
        form = PontoCarregamentoForm(request.POST)
        if form.is_valid():
            pontos = _criar_pontos_do_formulario(form, request.user)
            if len(pontos) == 1:
                messages.success(request, "Carregador cadastrado com sucesso.")
                return redirect("operador:imprimir_qrcode", ponto_id=pontos[0].id)
            messages.success(
                request,
                f"{len(pontos)} carregadores cadastrados com sucesso, cada um com seu próprio token.",
            )
            return redirect("operador:painel")
    else:
        form = PontoCarregamentoForm()

    pontos_qs = (
        PontoCarregamento.objects.filter(dono=request.user)
        .prefetch_related("sessoes")
    )

    pontos = []
    for ponto in pontos_qs:
        sessoes = list(ponto.sessoes.all())
        concluidas = [s for s in sessoes if s.status == Carregador.STATUS_CONCLUIDO]
        ativa = next(
            (s for s in sessoes if s.status != Carregador.STATUS_CONCLUIDO),
            None,
        )
        financeiro = _resumo_financeiro(concluidas)
        pontos.append(
            {
                "objeto": ponto,
                "status": "Em uso" if ativa else ("Disponível" if ponto.ativo else "Inativo"),
                "sessao_ativa": ativa,
                "receita_total": financeiro["receita_total"],
            }
        )

    sessoes_ativas_qs = (
        Carregador.objects.filter(ponto__dono=request.user)
        .select_related("usuario", "ponto")
        .exclude(status=Carregador.STATUS_CONCLUIDO)
    )
    sessoes_ativas = []
    potencia_total_kw = 0
    for sessao in sessoes_ativas_qs:
        em_uso = sessao.status == Carregador.STATUS_CARREGANDO
        estado = sessao.estado_atual() if em_uso else {}
        sessoes_ativas.append(
            {
                "codigo": sessao.identificador_fisico,
                "ponto": sessao.ponto.nome if sessao.ponto else sessao.apelido,
                "usuario": sessao.usuario.get_full_name() or sessao.usuario.username,
                "status": sessao.get_status_display(),
                "potencia_kw": CHARGER_POWER_KW if em_uso else 0,
                "energia_kwh": estado.get("energia_kwh"),
                "custo_total_parcial": estado.get("custo_total_parcial"),
            }
        )
        if em_uso:
            potencia_total_kw += CHARGER_POWER_KW

    concluidas = Carregador.objects.filter(
        ponto__dono=request.user,
        status=Carregador.STATUS_CONCLUIDO,
    )
    financeiro = _resumo_financeiro(concluidas)

    contexto = {
        "titulo": "Painel do Operador",
        "pontos": pontos,
        "carregadores": sessoes_ativas,
        "potencia_total_kw": round(potencia_total_kw, 1),
        "limite_contratado_kw": 60,
        "form": form,
        **financeiro,
    }
    return render(request, "operador/dashboard.html", contexto)


@login_required
@user_passes_test(eh_administrador, login_url="painel:painel")
def adicionar_ponto(request):
    if request.method == "POST":
        form = PontoCarregamentoForm(request.POST)
        if form.is_valid():
            pontos = _criar_pontos_do_formulario(form, request.user)
            if len(pontos) == 1:
                messages.success(request, "Carregador cadastrado com sucesso.")
                return redirect("operador:imprimir_qrcode", ponto_id=pontos[0].id)
            messages.success(
                request,
                f"{len(pontos)} carregadores cadastrados com sucesso, cada um com seu próprio token.",
            )
            return redirect("operador:painel")
    else:
        form = PontoCarregamentoForm()

    return render(
        request,
        "operador/ponto_form.html",
        {"form": form, "titulo": "Cadastrar carregador", "editando": False},
    )


@login_required
@user_passes_test(eh_administrador, login_url="painel:painel")
def editar_ponto(request, ponto_id):
    ponto = get_object_or_404(PontoCarregamento, id=ponto_id, dono=request.user)
    if request.method == "POST":
        form = PontoCarregamentoForm(request.POST, instance=ponto, mostrar_quantidade=False)
        if form.is_valid():
            form.save()
            messages.success(request, "Carregador atualizado com sucesso.")
            return redirect("operador:painel")
    else:
        form = PontoCarregamentoForm(instance=ponto, mostrar_quantidade=False)

    return render(
        request,
        "operador/ponto_form.html",
        {"form": form, "titulo": "Editar carregador", "editando": True, "ponto": ponto},
    )


@login_required
@user_passes_test(eh_administrador, login_url="painel:painel")
def alternar_ponto(request, ponto_id):
    if request.method != "POST":
        return redirect("operador:painel")

    ponto = get_object_or_404(PontoCarregamento, id=ponto_id, dono=request.user)
    ponto.ativo = not ponto.ativo
    ponto.save(update_fields=["ativo", "atualizado_em"])
    estado = "ativado" if ponto.ativo else "desativado"
    messages.success(request, f"Carregador {estado} com sucesso.")
    return redirect("operador:painel")


@login_required
@user_passes_test(eh_administrador, login_url="painel:painel")
def qrcode_png(request, ponto_id):
    """Gera a imagem PNG do QR Code do token deste carregador, pronta
    para ser impressa e colada no equipamento físico."""
    ponto = get_object_or_404(PontoCarregamento, id=ponto_id, dono=request.user)

    imagem = qrcode.make(ponto.identificador_fisico, box_size=10, border=2)
    buffer = BytesIO()
    imagem.save(buffer, format="PNG")
    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_required
@user_passes_test(eh_administrador, login_url="painel:painel")
def imprimir_qrcode(request, ponto_id):
    """Página com o QR Code do token pronta para impressão."""
    ponto = get_object_or_404(PontoCarregamento, id=ponto_id, dono=request.user)
    return render(request, "operador/qrcode.html", {"ponto": ponto})
