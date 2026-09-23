import json

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .suporte_chat import responder_suporte_chat, SuporteChatIndisponivel


def home(request):
    """
    Antes mostrava uma página de "Bem-vindo ao WeCharge". Agora vai direto
    pra tela de entrar na conta — quem já está logado é mandado pro painel
    certo (pos_login decide entre operador ou usuário comum).
    """
    if request.user.is_authenticated:
        return redirect('contas:pos_login')
    return redirect('contas:login')


def suporte(request):
    """Página de Suporte: perguntas frequentes + chat de dúvidas."""
    contexto = {
        'titulo': 'Suporte',
    }
    return render(request, 'paginas/suporte.html', contexto)


def api_suporte_chat(request):
    """Endpoint do chat de Suporte: recebe a pergunta e devolve a resposta."""
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

    try:
        resposta = responder_suporte_chat(mensagem)
    except SuporteChatIndisponivel as exc:
        return JsonResponse({"erro": str(exc)}, status=503)

    return JsonResponse({"resposta": resposta})

# Para criar uma nova página:
# 1. Escreva uma função aqui, seguindo o mesmo padrão (recebe request, retorna render)
# 2. Crie o template correspondente em paginas/templates/paginas/
# 3. Adicione a rota em paginas/urls.py
