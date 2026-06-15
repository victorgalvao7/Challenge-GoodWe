"""
WeCharge — Simulação do Sistema de Gerenciamento Inteligente de Eletropostos
Sprint 2 | GoodWe EV Challenge 2026 | FIAP

Equipe:
- Victor Vieira Galvao     (RM 571483)
- Miguel Silverio de Avila (RM 568873)
- Isabela Camargo Souza    (RM 569196)
- Gustavo Gamba Zancopé    (RM 569287)
- Artur Souza Pereira      (RM 570880)

Pilares simulados:
  1. Identificação de Carregador (código ou QR Code simulado)
  2. Estado da Bateria do Veículo
  3. Dynamic Load Balancing (controle dinâmico de demanda)
  4. IA via Groq API (dicas personalizadas por sessão)
  5. Billing Integrado (cobrança por kWh, tarifa única)
  6. Impacto Ambiental via eficiência da IA
  7. Cobrança por tempo adicional após conclusão
"""

import os
import re
import random
import math
import time
import json
import urllib.request
from datetime import datetime

# ─────────────────────────────────────────────
#  CONFIGURAÇÕES DO SISTEMA
# ─────────────────────────────────────────────
LIMITE_DEMANDA_KW       = 100.0
MARGEM_SEGURANCA        = 0.90
POTENCIA_MAX_CARREGADOR = 22.0
CAPACIDADE_BATERIA_KWH  = 60.0
VELOCIDADE_CARGA_KW     = 7.3
TARIFA_KWH              = 1.20
TARIFA_EXTRA_MIN        = 0.20

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_API_KEY = "COLE_SUA_CHAVE_GROQ_AQUI"
GROQ_MODEL   = "llama3-8b-8192"

FORMAS_PAGAMENTO = {"1": "PIX", "2": "Cartão de crédito", "3": "Cartão de débito"}

# ─────────────────────────────────────────────
#  UTILITÁRIOS
# ─────────────────────────────────────────────
def sep(titulo=""):
    if titulo:
        os.system("cls" if os.name == "nt" else "clear")
        print(f"{'═'*62}")
        print(f"  {titulo}")
        print(f"{'═'*62}")
    else:
        print(f"  {'─'*58}")

def pausar():
    input("\n  [ Pressione ENTER para continuar... ]\n")

def formatar_brl(valor):
    return f"R$ {valor:.2f}".replace(".", ",")

def calcular_kwh(bat_atual, bat_meta):
    return round(max(0, (bat_meta - bat_atual) / 100 * CAPACIDADE_BATERIA_KWH), 2)

def calcular_tempo(kwh):
    horas = kwh / VELOCIDADE_CARGA_KW
    h = int(horas)
    m = round((horas - h) * 60)
    return f"{h}h {m}min" if h > 0 else f"{m}min"

# ─────────────────────────────────────────────
#  MÓDULO 1: IDENTIFICAÇÃO DO CARREGADOR
# ─────────────────────────────────────────────
def identificar_carregador():
    sep("MÓDULO 1 — IDENTIFICAÇÃO DO CARREGADOR")
    print()
    print("  Como deseja identificar seu carregador?")
    print()
    print("  [1] Digitar o código do carregador")
    print("  [2] Simular leitura de QR Code")
    print()

    opcao = input("  Escolha (1 ou 2): ").strip()

    if opcao == "2":
        print()
        print("  📷 Simulando leitura do QR Code...")
        for i in range(3):
            time.sleep(0.5)
            print(f"     {'█' * (i+1) * 5}{'░' * (15 - (i+1)*5)}")
        carregador = f"{random.choice('ABCDEFG')}-{random.randint(1,9999):04d}"
        print(f"\n  ✅ QR Code lido com sucesso!")
        print(f"     Carregador identificado: {carregador}")
        print(f"     Potência: {POTENCIA_MAX_CARREGADOR} kW AC | Status: Disponível")
        return carregador

    padrao = re.compile(r"^[A-Z]-\d{4}$")
    while True:
        codigo = input("\n  Digite o código do carregador (ex: A-0042): ").strip().upper()
        if not codigo:
            continue
        if padrao.match(codigo):
            print(f"\n  ✅ Carregador {codigo} encontrado!")
            print(f"     Potência: {POTENCIA_MAX_CARREGADOR} kW AC | Status: Disponível")
            return codigo
        else:
            print("  ❌ Formato inválido. Use: letra + hífen + 4 números (ex: A-0042, B-9999).")

# ─────────────────────────────────────────────
#  MÓDULO 2: ESTADO DA BATERIA
# ─────────────────────────────────────────────
def verificar_bateria():
    sep("MÓDULO 2 — ESTADO DA BATERIA DO VEÍCULO")
    print()

    while True:
        try:
            bat = int(input("  Bateria atual do seu veículo (%): ").strip())
            if 0 <= bat <= 100:
                break
            print("  Valor inválido. Digite entre 0 e 100.")
        except ValueError:
            print("  Digite um número válido.")

    print()
    barra = int(bat / 100 * 30)
    cor   = "🔴" if bat < 20 else "🟡" if bat < 50 else "🟢"
    print(f"  {cor} Bateria: [{'█'*barra}{'░'*(30-barra)}] {bat}%")
    print(f"  ⚡ Velocidade de carga  : {VELOCIDADE_CARGA_KW} kW/h")
    print(f"  💡 Tarifa aplicada      : {formatar_brl(TARIFA_KWH)}/kWh")
    print(f"  🤖 Gestão de carga      : IA WeCharge ativa")

    return bat

# ─────────────────────────────────────────────
#  MÓDULO 3: IA GROQ
# ─────────────────────────────────────────────
def perguntar_ia(prompt, fallback):
    if "COLE_SUA_CHAVE" in GROQ_API_KEY:
        return fallback
    payload = json.dumps({
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100
    }).encode("utf-8")
    req = urllib.request.Request(
        GROQ_API_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return fallback

def dica_ia_bateria(bat_atual):
    prompt = (
        f"Você é a IA do app WeCharge para VEs. Bateria atual: {bat_atual}%. "
        f"Nossa IA gerencia a distribuição de carga para minimizar consumo da rede. "
        f"Dê uma dica curta (1-2 frases) em português sobre o estado da bateria."
    )
    if bat_atual < 20:
        fallback = (
            "Bateria abaixo de 20% — recomendamos carregar até pelo menos 60% antes de sair. "
            "Nossa IA já está otimizando a distribuição de carga para minimizar o consumo da rede."
        )
    elif bat_atual < 50:
        fallback = (
            "Bateria em nível médio. Nossa IA gerencia a carga de forma eficiente, "
            "reduzindo o consumo desnecessário da rede elétrica e o impacto ambiental."
        )
    else:
        fallback = (
            "Bateria em bom nível! Nossa IA vai otimizar a distribuição para que o carregamento "
            "use o mínimo necessário da rede — menos desperdício, menor impacto no meio ambiente."
        )
    return perguntar_ia(prompt, fallback)

def dica_ia_meta(bat_atual, meta, kwh, custo):
    prompt = (
        f"Você é a IA do app WeCharge. Bateria atual: {bat_atual}%, meta: {meta}%, "
        f"energia necessária: {kwh} kWh, custo: R${custo:.2f}. "
        f"Nossa IA distribui a carga eficientemente para reduzir impacto na rede. "
        f"Comente a meta em 1-2 frases em português, mencionando eficiência e meio ambiente."
    )
    fallback = (
        f"Meta de {meta}% definida! Nossa IA vai distribuir os {kwh} kWh de forma eficiente "
        f"entre os carregadores — reduzindo o pico de consumo na rede e o impacto ambiental."
    )
    return perguntar_ia(prompt, fallback)

# ─────────────────────────────────────────────
#  MÓDULO 4: DEFINIR META
# ─────────────────────────────────────────────
def definir_meta(bat_atual):
    sep("MÓDULO 4 — META DE CARREGAMENTO")
    print()
    print("  Como deseja definir a meta?")
    print()
    print("  [1] Por percentual de bateria")
    print("  [2] Por valor em R$")
    print()

    modo = input("  Escolha (1 ou 2): ").strip()

    if modo == "2":
        while True:
            try:
                valor = float(input("\n  Quanto deseja investir? R$ ").strip().replace(",", "."))
                if valor > 0:
                    break
                print("  Valor deve ser maior que zero.")
            except ValueError:
                print("  Digite um valor numérico.")
        kwh_possivel = valor / TARIFA_KWH
        pct_possivel = round((kwh_possivel / CAPACIDADE_BATERIA_KWH) * 100)
        meta = min(100, bat_atual + pct_possivel)
        print(f"\n  Com {formatar_brl(valor)} você carrega +{pct_possivel}% → bateria chegará a {meta}%")
    else:
        while True:
            try:
                meta = int(input(f"\n  Carregar até qual %? (atual: {bat_atual}%): ").strip())
                if bat_atual < meta <= 100:
                    break
                print(f"  Meta deve ser entre {bat_atual+1}% e 100%.")
            except ValueError:
                print("  Digite um número válido.")

    kwh   = calcular_kwh(bat_atual, meta)
    tempo = calcular_tempo(kwh)
    custo = round(kwh * TARIFA_KWH, 2)

    print()
    sep()
    print(f"  Bateria atual       : {bat_atual}%")
    print(f"  Meta                : {meta}%")
    print(f"  Energia necessária  : {kwh} kWh")
    print(f"  Tempo estimado      : {tempo}")
    print(f"  Custo estimado      : {formatar_brl(custo)}")
    print(f"  Tarifa aplicada     : {formatar_brl(TARIFA_KWH)}/kWh")

    print("\n  🤖 IA WeCharge analisando sua meta...")
    dica = dica_ia_meta(bat_atual, meta, kwh, custo)
    print(f"\n  💬 {dica}")

    return meta, kwh, tempo, custo

# ─────────────────────────────────────────────
#  MÓDULO 5: DYNAMIC LOAD BALANCING
# ─────────────────────────────────────────────
def dynamic_load_balancing(potencia_solicitada, demanda_base=65.0):
    sep("MÓDULO 5 — DYNAMIC LOAD BALANCING")

    demanda_total = demanda_base + potencia_solicitada
    limite_ativo  = LIMITE_DEMANDA_KW * MARGEM_SEGURANCA

    print(f"\n  Demanda base do estabelecimento : {demanda_base:.1f} kW")
    print(f"  Potência solicitada pelo VE     : {potencia_solicitada:.1f} kW")
    print(f"  Demanda total calculada         : {demanda_total:.1f} kW")
    print(f"  Limite de segurança (90%)       : {limite_ativo:.1f} kW")

    if demanda_total > limite_ativo:
        excesso   = demanda_total - limite_ativo
        pot_final = max(7.4, potencia_solicitada - excesso)
        print(f"\n  ⚠️  Demanda alta! Reduzindo carga de {potencia_solicitada:.1f} → {pot_final:.1f} kW")
        print(f"  ✅ Sistema ajustado — sem risco de multa por ultrapassagem")
        return round(pot_final, 1)
    else:
        print(f"\n  ✅ Demanda dentro do limite. Carga máxima liberada.")
        return potencia_solicitada

# ─────────────────────────────────────────────
#  MÓDULO 6: PAGAMENTO
# ─────────────────────────────────────────────
def processar_pagamento(custo, tempo, meta):
    sep("MÓDULO 6 — PAGAMENTO")
    print()
    print(f"  Valor a pagar: {formatar_brl(custo)}")
    print()
    print("  Forma de pagamento:")
    for k, v in FORMAS_PAGAMENTO.items():
        print(f"  [{k}] {v}")
    print()

    while True:
        escolha = input("  Escolha (1, 2 ou 3): ").strip()
        if escolha in FORMAS_PAGAMENTO:
            break
        print("  Opção inválida.")

    forma = FORMAS_PAGAMENTO[escolha]
    print(f"\n  💳 Pagamento via {forma} autorizado!")
    if forma == "PIX":
        print("  📲 QR Code PIX gerado. Aprovação instantânea.")
    elif "crédito" in forma.lower():
        print("  💳 Cartão pré-autorizado. Cobrança ao final da sessão.")
    else:
        print("  💳 Débito confirmado.")

    print(f"\n  ✅ Sessão iniciada!")
    print(f"     Carregando até {meta}% | Tempo estimado: {tempo}")
    return forma

# ─────────────────────────────────────────────
#  MÓDULO 7: SIMULAÇÃO DO CARREGAMENTO
# ─────────────────────────────────────────────
def simular_carregamento(bat_atual, meta):
    sep("MÓDULO 7 — CARREGAMENTO EM ANDAMENTO")
    print()

    passos = [bat_atual + int((meta - bat_atual) * p) for p in [0.25, 0.5, 0.75, 1.0]]
    passos[-1] = meta

    for pct in passos:
        barra = int(pct / 100 * 35)
        kwh_carregado = calcular_kwh(bat_atual, pct)
        custo_parcial = round(kwh_carregado * TARIFA_KWH, 2)
        print(f"  🔋 {pct:>3}%  [{'█'*barra}{'░'*(35-barra)}]  {formatar_brl(custo_parcial)}")
        time.sleep(0.4)

    print()
    print(f"  ✅ Carregamento concluído! Bateria em {meta}%")


# ─────────────────────────────────────────────
#  MÓDULO 9: TEMPO ADICIONAL
# ─────────────────────────────────────────────
def cobrar_tempo_adicional(custo_base):
    sep("MÓDULO 9 — TEMPO ADICIONAL NA VAGA")
    print()
    print("  ⚠️  Veículo ainda conectado após conclusão do carregamento?")
    print(f"     Tempo adicional é cobrado a {formatar_brl(TARIFA_EXTRA_MIN)}/min.")
    print()

    while True:
        try:
            mins = int(input("  Quantos minutos a mais ficou conectado? (0 se nenhum): ").strip())
            if mins >= 0:
                break
            print("  Valor deve ser 0 ou maior.")
        except ValueError:
            print("  Digite um número inteiro.")

    custo_extra = round(mins * TARIFA_EXTRA_MIN, 2)
    total       = round(custo_base + custo_extra, 2)

    if mins > 0:
        print(f"\n  ⏱️  {mins} min adicionais → {formatar_brl(custo_extra)} cobrado")
    else:
        print("\n  ✅ Nenhum tempo adicional. Sem cobrança extra.")

    return custo_extra, total

# ─────────────────────────────────────────────
#  RESUMO FINAL
# ─────────────────────────────────────────────
def resumo_final(carregador, bat_inicial, meta, kwh, forma_pag, custo_base, custo_extra, total):
    sep("RESUMO FINAL DA SESSÃO")
    print()
    print(f"  {'─'*56}")
    print(f"  Carregador          : {carregador}")
    print(f"  Bateria inicial     : {bat_inicial}%")
    print(f"  Bateria final       : {meta}%")
    print(f"  Energia carregada   : {kwh} kWh")
    print(f"  Forma de pagamento  : {forma_pag}")
    print(f"  {'─'*56}")
    print(f"  Carregamento        : {formatar_brl(custo_base)}")
    print(f"  Tempo adicional     : {formatar_brl(custo_extra)}")
    print(f"  {'─'*56}")
    print(f"  TOTAL PAGO          : {formatar_brl(total)}")
    print(f"  {'─'*56}")
    print()
    print("  ⚡ WeCharge — Tornando eletropostos inteligentes e sustentáveis")
    print()

# ─────────────────────────────────────────────
#  EXECUÇÃO PRINCIPAL
# ─────────────────────────────────────────────
def main():
    os.system("cls" if os.name == "nt" else "clear")
    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║        ⚡ WeCharge — Simulação Interativa Sprint 2       ║")
    print("  ║        GoodWe EV Challenge 2026 | FIAP                   ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print()
    print("  Equipe WeCharge:")
    print("   • Victor Vieira Galvao     — RM 571483")
    print("   • Miguel Silverio de Avila — RM 568873")
    print("   • Isabela Camargo Souza    — RM 569196")
    print("   • Gustavo Gamba Zancopé    — RM 569287")
    print("   • Artur Souza Pereira      — RM 570880")
    print()

    pausar()

    carregador = identificar_carregador()
    if not carregador:
        print("\n  Sessão encerrada. Tente novamente.")
        return

    pausar()

    bat_atual = verificar_bateria()

    print("\n  🤖 IA WeCharge analisando sua bateria...")
    dica_bat = dica_ia_bateria(bat_atual)
    print(f"\n  💬 {dica_bat}")

    pausar()

    meta, kwh, tempo, custo_base = definir_meta(bat_atual)

    pausar()

    dynamic_load_balancing(POTENCIA_MAX_CARREGADOR)

    pausar()

    forma_pag = processar_pagamento(custo_base, tempo, meta)

    pausar()

    simular_carregamento(bat_atual, meta)

    pausar()

    custo_extra, total = cobrar_tempo_adicional(custo_base)

    pausar()

    resumo_final(carregador, bat_atual, meta, kwh, forma_pag, custo_base, custo_extra, total)


if __name__ == "__main__":
    main()
