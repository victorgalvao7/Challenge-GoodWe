"""
Chat de Suporte — assistente da área pública (Suporte).

Diferente do Wechat (que ajuda a achar carregador perto de um lugar),
esse aqui responde dúvidas gerais sobre como usar o app (como cadastrar
um carregador, como pagar, etc.) e, se a pessoa pedir para falar com um
humano, encaminha o e-mail da equipe de suporte — sem inventar nada e
sem depender só da IA pra essa decisão (a detecção de "quero um
humano" é feita por palavra-chave, de forma determinística).
"""
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)

EMAIL_SUPORTE = "equipe04challenge@gmail.com"

# Palavras/expressões que indicam que a pessoa quer falar com um
# humano de verdade, não com o chatbot.
PADRAO_QUER_HUMANO = re.compile(
    r"\b(humano|atendente|pessoa\s+real|falar\s+com\s+alguem|falar\s+com\s+algu[ée]m|"
    r"suporte\s+humano|equipe\s+de\s+verdade|n[ãa]o\s+quero\s+(falar\s+com\s+)?(o\s+)?(robo|rob[ôo]|chat|bot))\b",
    re.IGNORECASE,
)

MENSAGEM_HUMANO = (
    "Sem problemas! Você pode falar diretamente com a nossa equipe pelo "
    f"e-mail {EMAIL_SUPORTE} — explique sua dúvida ou problema por lá que "
    "alguém da equipe WeCharge te responde."
)

FAQ_TEXTO = """
Perguntas frequentes já respondidas na página (use isso como referência,
não repita tudo de uma vez, responda só o que a pessoa perguntou):

1) Como eu cadastro/adiciono um carregador na minha conta?
   No "Meu Painel", clique em "+ Adicionar carregador" e informe o token
   de 5 caracteres (ou leia o QR Code) que está impresso no carregador
   físico.

2) Como eu libero e inicio a recarga?
   Depois de adicionar o carregador, clique em "Liberar" e depois em
   "Iniciar carregamento" na tela do carregador.

3) Como funciona o pagamento?
   Ao final da recarga, o app calcula o valor (R$/kWh consumido, mais
   eventual cobrança por tempo excedente) e você paga por Pix, crédito
   ou débito na própria tela de pagamento.

4) Esqueci minha senha, e agora?
   Ainda não temos recuperação automática de senha — peça para a equipe
   de suporte redefinir pelo e-mail de contato.

5) Sou dono de um ponto de recarga, como cadastro meu carregador físico
   para outras pessoas usarem?
   Crie uma conta do tipo "Administrador" e cadastre o ponto no
   "Painel do Operador", com nome, token, endereço e preço por kWh.

6) Onde vejo meu histórico de recargas?
   Em "Conta" > "Histórico de carregamentos", ou pelo botão "Histórico"
   no Meu Painel.
"""

SYSTEM_PROMPT = (
    "Você é o assistente de Suporte do WeCharge, um app de carregadores de "
    "veículo elétrico. Responda dúvidas curtas e práticas sobre como usar o "
    "app, em português do Brasil, em 1-3 frases, de forma direta e "
    "simpática. Use como referência o conteúdo de FAQ abaixo, mas não "
    "precisa citar tudo — responda só o que foi perguntado. Se a pergunta "
    "não tiver relação com o WeCharge, diga educadamente que você só ajuda "
    "com dúvidas sobre o app. Se você não souber responder com certeza, "
    f"sugira falar com a equipe pelo e-mail {EMAIL_SUPORTE}.\n\n{FAQ_TEXTO}"
)


class SuporteChatIndisponivel(Exception):
    """Erro amigável para quando o chat de IA não pode ser usado agora."""


def responder_suporte_chat(mensagem_usuario):
    """Ponto de entrada: recebe a pergunta e devolve a resposta do chat
    de suporte. Se a pessoa pedir um humano, nem chama a IA — responde
    direto com o e-mail da equipe."""

    if PADRAO_QUER_HUMANO.search(mensagem_usuario):
        return MENSAGEM_HUMANO

    if not settings.OPENAI_API_KEY:
        # Sem IA configurada: resposta genérica, sempre com o caminho pro
        # humano, pra pessoa nunca ficar sem saída.
        return (
            "Consulte as perguntas frequentes acima — cobrem cadastro de "
            "carregador, liberação, pagamento e histórico. Se sua dúvida "
            f"não estiver lá, escreva pra gente em {EMAIL_SUPORTE}."
        )

    from openai import OpenAI

    try:
        cliente = OpenAI(api_key=settings.OPENAI_API_KEY)
        resposta = cliente.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": mensagem_usuario},
            ],
        )
        return resposta.choices[0].message.content.strip()
    except Exception as exc:  # erro de rede, chave inválida, etc.
        logger.exception("Falha ao chamar a API da OpenAI no Chat de Suporte")
        raise SuporteChatIndisponivel(
            "Não consegui responder agora. Tente de novo em instantes ou "
            f"escreva pra gente em {EMAIL_SUPORTE}."
        ) from exc
