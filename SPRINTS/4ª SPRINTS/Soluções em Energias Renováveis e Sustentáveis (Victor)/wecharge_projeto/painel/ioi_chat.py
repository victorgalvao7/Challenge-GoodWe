"""
IoI Chat — assistente de IA da área do usuário.

O usuário pergunta coisas como "qual carregador mais próximo de um
McDonald's?" e a IA:
  1) primeiro tenta achar o lugar mencionado batendo direto contra o
     NOME/ENDEREÇO dos próprios carregadores cadastrados (ex.: "FIAP
     Paulista", "Shopping Anália Franco") — cobre nomes específicos
     (faculdades, academias, marcas) que o Nominatim não conhece;
  2) se não achar nada assim, cai para o Nominatim (geocodificação
     gratuita do OpenStreetMap, o mesmo serviço por trás do mapa) para
     achar esse lugar perto do usuário;
  3) compara a localização encontrada com a de todos os carregadores
     que já têm local cadastrado no banco (o mesmo campo que o
     administrador preenche);
  4) responde qual é o mais próximo e a que distância.

A IA (OpenAI) só entra para interpretar a pergunta em linguagem natural
e formatar a resposta — a busca de lugar e o cálculo de distância são
feitos aqui em Python, de forma determinística, para não haver risco de
a IA "inventar" uma distância ou um carregador que não existe.
"""
import logging
import math
import re

import requests
from django.conf import settings
from django.db.models import Q

from .models import Carregador, PontoCarregamento

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Exigência do Nominatim: um User-Agent identificando a aplicação.
# Troque o e-mail de contato antes de colocar em produção de verdade.
NOMINATIM_HEADERS = {"User-Agent": "WeCharge-App/1.0 (contato@wecharge.exemplo)"}

SYSTEM_PROMPT = (
    "Você é o Wechat, o assistente da WeCharge, um app de carregadores de "
    "veículo elétrico. Você ajuda o usuário a achar carregadores WeCharge "
    "de duas formas: (1) o carregador mais próximo de UM LUGAR DE "
    "REFERÊNCIA que ele mencionar (ex.: um McDonald's, uma farmácia, um "
    "endereço, um bairro) — nesse caso use a ferramenta "
    "carregador_mais_proximo_de; (2) o carregador mais próximo da PRÓPRIA "
    "localização atual do usuário, quando ele não citar nenhum lugar "
    "específico (ex.: 'qual o carregador mais próximo?', 'tem carregador "
    "perto de mim?', 'o mais próximo de mim') — nesse caso use a "
    "ferramenta carregador_mais_proximo_do_usuario. NUNCA diga que só "
    "consegue ajudar com um ponto de referência: se o usuário não deu "
    "nenhum lugar, é justamente o caso de usar a segunda ferramenta. "
    "Sempre que a pergunta for sobre achar carregador, use uma das duas "
    "ferramentas — nunca invente distâncias, endereços ou nomes de "
    "carregadores por conta própria. Responda em português do Brasil, de "
    "forma curta e direta (2-3 frases), como uma mensagem de chat. Se a "
    "pergunta não tiver nada a ver com localização de carregadores, "
    "explique educadamente que você só ajuda com isso."
)

FERRAMENTAS = [
    {
        "type": "function",
        "function": {
            "name": "carregador_mais_proximo_de",
            "description": (
                "Use quando o usuário citar um LUGAR DE REFERÊNCIA (ex: "
                "'McDonald's', 'Shopping Ibirapuera', 'FIAP Paulista', "
                "'Av. Paulista 1000'). Funciona tanto com lugares que já "
                "têm um carregador WeCharge cadastrado bem ali (faculdades, "
                "academias, marcas) quanto com lugares genéricos perto do "
                "usuário. Retorna qual carregador WeCharge cadastrado está "
                "mais próximo desse lugar, com a distância em km."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lugar_referencia": {
                        "type": "string",
                        "description": "Nome, tipo ou endereço do lugar mencionado pelo usuário.",
                    }
                },
                "required": ["lugar_referencia"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "carregador_mais_proximo_do_usuario",
            "description": (
                "Use quando o usuário quiser o carregador mais próximo dele "
                "mesmo, SEM citar nenhum lugar de referência (ex.: 'qual o "
                "carregador mais próximo?', 'tem carregador perto de mim?', "
                "'o mais próximo de mim'). Retorna o carregador WeCharge "
                "cadastrado mais próximo da localização atual do usuário, "
                "com a distância em km. Não precisa de nenhum argumento."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


class IoIChatIndisponivel(Exception):
    """Erro amigável para quando o chat não pode ser usado agora."""


class BuscaDeLocalIndisponivel(Exception):
    """Erro amigável específico para quando o Nominatim (busca de local)
    falha — para não misturar com erros da OpenAI."""


def _haversine_km(lat1, lon1, lat2, lon2):
    """Distância em linha reta entre dois pontos (fórmula de Haversine)."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _geocodificar_local(nome_lugar, lat_usuario, lon_usuario):
    """Busca o 'nome_lugar' mais próximo da localização do usuário via
    Nominatim (OpenStreetMap). Retorna dict com nome/lat/lon ou None.

    Importante: o Nominatim NÃO ordena os resultados por distância até o
    usuário — ele ordena por "importância"/relevância interna. Por isso
    pedimos vários resultados (não só o primeiro) e escolhemos aqui, nós
    mesmos, o que está fisicamente mais perto do usuário. Sem isso, uma
    busca genérica (ex.: "hamburgueria") podia devolver um lugar famoso
    do outro lado da cidade em vez do mais próximo de verdade.
    """
    params = {"q": nome_lugar, "format": "json", "limit": 8}

    if lat_usuario is not None and lon_usuario is not None:
        # Restringe a busca a uma caixa de ~8km ao redor do usuário — raio
        # que ainda cobre bairros vizinhos, mas evita trazer resultados de
        # longe só porque são mais "importantes" pro Nominatim.
        delta = 0.07
        params["viewbox"] = (
            f"{lon_usuario - delta},{lat_usuario + delta},"
            f"{lon_usuario + delta},{lat_usuario - delta}"
        )
        params["bounded"] = 1

    try:
        resp = requests.get(
            NOMINATIM_URL, params=params, headers=NOMINATIM_HEADERS, timeout=6
        )
        resp.raise_for_status()
        resultados = resp.json()
    except requests.RequestException:
        logger.exception("Falha ao consultar o Nominatim no IoI Chat")
        raise BuscaDeLocalIndisponivel(
            "Não consegui consultar o serviço de mapas agora."
        )

    if not resultados:
        return None

    if lat_usuario is not None and lon_usuario is not None:
        # Entre os resultados encontrados, pega o mais próximo do usuário
        # (e não o primeiro da lista, que é só o "mais relevante").
        item = min(
            resultados,
            key=lambda r: _haversine_km(
                lat_usuario, lon_usuario, float(r["lat"]), float(r["lon"])
            ),
        )
    else:
        item = resultados[0]

    return {
        "nome": item.get("display_name", nome_lugar),
        "latitude": float(item["lat"]),
        "longitude": float(item["lon"]),
    }


def _info_carregador(ponto, distancia_km):
    """Monta o dicionário de resposta para um PontoCarregamento, dada a
    distância (em km) até o lugar de referência."""
    return {
        "id": ponto.id,
        "apelido": ponto.nome,
        "endereco": ponto.endereco,
        "identificador_fisico": ponto.identificador_fisico,
        "latitude": ponto.latitude,
        "longitude": ponto.longitude,
        "status": (
            "Em uso"
            if any(
                sessao.status != Carregador.STATUS_CONCLUIDO
                for sessao in ponto.sessoes.all()
            )
            else "Disponível"
        ),
        "preco_kwh": float(ponto.preco_kwh),
        "distancia_km": round(distancia_km, 2),
    }


def _buscar_carregador_por_nome(termo):
    """Tenta achar um carregador cadastrado cujo NOME ou ENDEREÇO batam
    com o lugar que o usuário mencionou (ex.: "FIAP Paulista",
    "McDonald's Tatuapé"). Isso cobre nomes de faculdades, academias,
    marcas etc. que o Nominatim não conhece como lugar geocodificável,
    mas que a gente já tem cadastrado com nome e endereço reais.
    Retorna o PontoCarregamento com melhor pontuação, ou None."""
    termo = (termo or "").strip()
    if not termo:
        return None

    # Palavras com 3+ letras evitam falso-positivo em conectores curtos
    # ("de", "da", "do") e ainda pegam nomes próprios e siglas (ex. FIAP).
    palavras = [p for p in re.split(r"\s+", termo) if len(p) >= 3]
    if not palavras:
        return None

    filtro = Q()
    for palavra in palavras:
        filtro |= Q(nome__icontains=palavra) | Q(endereco__icontains=palavra)

    melhor = None
    melhor_pontuacao = 0
    for candidato in PontoCarregamento.objects.filter(filtro, ativo=True).prefetch_related("sessoes"):
        alvo = f"{candidato.nome} {candidato.endereco}".lower()
        pontuacao = sum(1 for p in palavras if p.lower() in alvo)
        if pontuacao > melhor_pontuacao:
            melhor_pontuacao = pontuacao
            melhor = candidato

    # Exige pelo menos metade das palavras do termo pra evitar bater com
    # qualquer coisa por coincidência de uma palavra solta.
    if melhor is not None and melhor_pontuacao >= max(1, len(palavras) / 2):
        return melhor
    return None


def _carregador_mais_proximo(lat, lon):
    """Entre os carregadores com localização cadastrada, acha o mais
    próximo do ponto (lat, lon). Retorna dict ou None se não houver
    nenhum carregador com local cadastrado ainda."""
    carregadores = PontoCarregamento.objects.filter(ativo=True).prefetch_related("sessoes")

    melhor = None
    menor_distancia = None
    for c in carregadores:
        distancia = _haversine_km(lat, lon, c.latitude, c.longitude)
        if menor_distancia is None or distancia < menor_distancia:
            menor_distancia = distancia
            melhor = c

    if melhor is None:
        return None

    return _info_carregador(melhor, menor_distancia)


def _executar_ferramenta(nome_ferramenta, argumentos, lat_usuario, lon_usuario):
    if nome_ferramenta not in ("carregador_mais_proximo_de", "carregador_mais_proximo_do_usuario"):
        return {"erro": "Ferramenta desconhecida."}

    if lat_usuario is None or lon_usuario is None:
        return {
            "erro": (
                "A localização do usuário não está disponível. Peça para "
                "ele ativar a permissão de localização no navegador."
            )
        }

    # --- Sem lugar de referência: mais próximo do próprio usuário --------
    if nome_ferramenta == "carregador_mais_proximo_do_usuario":
        carregador = _carregador_mais_proximo(lat_usuario, lon_usuario)
        if carregador is None:
            return {
                "aviso": (
                    "Ainda não há nenhum carregador com localização "
                    "cadastrada no sistema."
                ),
            }
        return {"local_encontrado": "sua localização atual", "carregador_mais_proximo": carregador}

    # --- Com lugar de referência (McDonald's, endereço, etc.) -------------
    lugar = argumentos.get("lugar_referencia", "").strip()
    if not lugar:
        return {"erro": "Nenhum lugar de referência foi informado."}

    # 1) Primeiro tenta achar o lugar batendo direto no nome/endereço dos
    # carregadores já cadastrados — cobre nomes específicos (faculdades,
    # academias, marcas) que o Nominatim não tem como geocodificar.
    carregador_direto = _buscar_carregador_por_nome(lugar)
    if carregador_direto is not None:
        carregador = _info_carregador(carregador_direto, 0.0)
        return {"local_encontrado": carregador_direto.nome, "carregador_mais_proximo": carregador}

    # 2) Se não achou direto, geocodifica o lugar via Nominatim e procura
    # o carregador mais próximo dele.
    try:
        local = _geocodificar_local(lugar, lat_usuario, lon_usuario)
    except BuscaDeLocalIndisponivel as exc:
        return {"erro": str(exc)}

    if local is None:
        return {"erro": f"Não encontrei '{lugar}' perto da localização do usuário."}

    carregador = _carregador_mais_proximo(local["latitude"], local["longitude"])
    if carregador is None:
        return {
            "local_encontrado": local["nome"],
            "aviso": (
                "Ainda não há nenhum carregador com localização cadastrada "
                "no sistema."
            ),
        }

    return {"local_encontrado": local["nome"], "carregador_mais_proximo": carregador}


def responder_ioi_chat(mensagem_usuario, lat_usuario=None, lon_usuario=None):
    """Ponto de entrada: recebe a pergunta do usuário e devolve uma tupla
    (texto_resposta, destaque). ``destaque`` é um dicionário com o
    carregador encontrado (lat/lon/id/token/etc.) para o front-end plotar
    no mapa e traçar a rota até ele, ou None quando a pergunta não era
    sobre localização/carregador (ou nada foi encontrado)."""
    if not settings.OPENAI_API_KEY:
        raise IoIChatIndisponivel(
            "O Wechat ainda não foi configurado (falta a OPENAI_API_KEY)."
        )

    from openai import OpenAI

    mensagens = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": mensagem_usuario},
    ]

    destaque = None

    try:
        cliente = OpenAI(api_key=settings.OPENAI_API_KEY)
        resposta = cliente.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=mensagens,
            tools=FERRAMENTAS,
            tool_choice="auto",
        )
        aviso_msg = resposta.choices[0].message

        if aviso_msg.tool_calls:
            mensagens.append(aviso_msg)
            for chamada in aviso_msg.tool_calls:
                import json as _json

                argumentos = _json.loads(chamada.function.arguments or "{}")
                resultado = _executar_ferramenta(
                    chamada.function.name, argumentos, lat_usuario, lon_usuario
                )
                if resultado.get("carregador_mais_proximo"):
                    # Guarda o último carregador encontrado pela ferramenta
                    # para devolver junto da resposta em texto — é o que o
                    # mapa usa pra já mostrar o marcador e traçar a rota.
                    destaque = {
                        "carregador": resultado["carregador_mais_proximo"],
                        "local_referencia": resultado.get("local_encontrado"),
                    }
                mensagens.append(
                    {
                        "role": "tool",
                        "tool_call_id": chamada.id,
                        "content": _json.dumps(resultado, ensure_ascii=False),
                    }
                )

            resposta_final = cliente.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=mensagens,
            )
            return resposta_final.choices[0].message.content.strip(), destaque

        return aviso_msg.content.strip(), destaque

    except IoIChatIndisponivel:
        raise
    except Exception as exc:  # erro de rede, chave inválida, etc.
        # Registra o erro DE VERDADE no terminal do servidor (o usuário
        # só vê a mensagem genérica abaixo, por segurança) — é isso que
        # aparece no console de quem está rodando `manage.py runserver`.
        logger.exception("Falha ao chamar a API da OpenAI no IoI Chat")
        raise IoIChatIndisponivel(
            "Não consegui falar com a IA agora. Tente de novo em instantes."
        ) from exc
