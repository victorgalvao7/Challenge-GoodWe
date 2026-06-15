# ⚡ WeCharge — ChargeGrid Intelligence

**WeCharge | GoodWe EV Challenge 2026 | FIAP**

Plataforma de gerenciamento inteligente de eletropostos comerciais integrada ao ecossistema GoodWe.

---

## 👥 Equipe

| Nome | RM | Responsabilidade |
|---|---|---|
| Victor Vieira Galvao | 571483 | Pensamento Computacional + Energias Renováveis |
| Miguel Silverio de Avila | 568873 | Computer Organization + Computer Science |
| Isabela Camargo Souza | 569196 | Modelagem Linear + Modelagem Matemática |
| Gustavo Gamba Zancopé | 569287 | Prompt and Artificial Intelligence |
| Artur Souza Pereira | 570880 | Data Structures and Algorithms |

---

## 🎥 Vídeo de Demonstração

🔗 [Assistir no YouTube](https://youtu.be/HmwEoRm2mBw)

---

## 📋 Kanban do Projeto

🔗 [Quadro no Trello](https://trello.com/b/Ce7ulBiH/wecharge-sprint-2)

---

## 🚗 O Problema

A infraestrutura de carregamento de VEs no Brasil enfrenta barreiras críticas para escalar ao ambiente comercial:

- **Sobrecarga elétrica** em horários de pico com múltiplos carregadores simultâneos
- **Ausência de cobrança nativa**, inviabilizando a monetização do eletroposto
- **Experiência fragmentada**: múltiplos apps, autenticações confusas, sem feedback em tempo real
- **Ineficiência energética**: sem gestão inteligente, o consumo da rede é maior do que o necessário

---

## 💡 Nossa Proposta

O WeCharge é uma plataforma integrada de gerenciamento de eletropostos comerciais com **3 pilares**:

### ⚡ 1. Dynamic Load Balancing
Redistribui potência entre carregadores em tempo real, respeitando o limite contratado com a concessionária. Sem multas, sem desligamentos.

### 💳 2. Billing Integrado
Cobrança por kWh com PIX, cartão de crédito e débito. Tarifa transparente antes e durante o carregamento. Cobrança adicional por tempo na vaga após a conclusão.

### 🤖 3. IA via Groq (Llama 3)
Dicas personalizadas por sessão: analisa o estado da bateria, comenta a meta escolhida e otimiza a distribuição de carga entre os carregadores — reduzindo o consumo desnecessário da rede e o impacto ambiental.

---

## 🏗️ Arquitetura do Sistema

```
┌──────────────────────────────────────────────────────────┐
│                    WeCharge Platform                     │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  Inversores │  │   Baterias  │  │  Carregadores   │  │
│  │   GoodWe    │  │   GoodWe    │  │  (OCPP 2.0)     │  │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘  │
│         └────────────────┴──────────────────┘            │
│                           │                              │
│               ┌───────────▼───────────┐                  │
│               │     CSMS (Backend)    │                  │
│               │  • Load Balancing     │                  │
│               │  • IA Groq / Llama3   │                  │
│               │  • Billing Engine     │                  │
│               └───────────┬───────────┘                  │
│          ┌────────────────┼──────────────┐               │
│          ▼                ▼              ▼               │
│   ┌────────────┐  ┌─────────────┐  ┌──────────────┐     │
│   │ App Mobile │  │   Painel    │  │   Gateway    │     │
│   │ (código ou │  │  Operador   │  │  Pagamento   │     │
│   │  QR Code)  │  │ (Dashboard) │  │PIX/Cartão    │     │
│   └────────────┘  └─────────────┘  └──────────────┘     │
└──────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Protocolo de comunicação | OCPP 2.0 (WebSocket + TLS) |
| Hardware | Carregadores GoodWe, Inversores GoodWe, BESS GoodWe |
| IA | Groq API — Llama 3 8B (dicas personalizadas por sessão) |
| Pagamentos | PIX, Cartão de crédito, Cartão de débito |
| App mobile | React Native (iOS + Android) |
| Backend | API REST + CSMS |
| Simulação (Sprint 2) | Python 3.x — sem dependências externas |

---

## 🧪 Prova de Conceito — Sprint 2

### Como executar

**Requisitos:** Python 3.8 ou superior. Sem bibliotecas externas necessárias.

```bash
# Clonar o repositório
git clone https://github.com/SEU_USUARIO/Challenge-GoodWe.git
cd Challenge-GoodWe

# Executar a simulação interativa
python wecharge_simulacao.py
```

**Para ativar a IA real (Groq):** edite o arquivo e substitua `COLE_SUA_CHAVE_GROQ_AQUI` pela sua chave gratuita em [console.groq.com](https://console.groq.com).

---

### Fluxo da Simulação

A simulação é **totalmente interativa** — o usuário responde as perguntas como se estivesse usando o app real.

```
MÓDULO 1 — Identificação do carregador
  → Digitar código (ex: A-0042, B-9999) — aceita qualquer carregador cadastrado
  → OU simular leitura de QR Code

MÓDULO 2 — Estado da bateria
  → Usuário informa % atual
  → IA WeCharge dá dica sobre o estado e eficiência de carga

MÓDULO 4 — Meta de carregamento
  → Por percentual (ex: carregar até 80%)
  → Por valor em R$ (ex: "quero gastar R$ 50" → sistema calcula até onde vai)
  → IA comenta a meta com foco em eficiência e impacto ambiental

MÓDULO 5 — Dynamic Load Balancing
  → Verifica demanda total do estabelecimento
  → Reduz potência automaticamente se necessário
  → Garante zero multas por ultrapassagem de demanda

MÓDULO 6 — Pagamento
  → PIX, Cartão de crédito ou Cartão de débito
  → Valor transparente antes de iniciar

MÓDULO 7 — Carregamento em andamento
  → Barra de progresso com custo parcial atualizado em tempo real

MÓDULO 8 — Tempo adicional na vaga
  → Cobra R$ 0,20/min após conclusão do carregamento

RESUMO FINAL
  → Carregador, bateria inicial/final, energia, forma de pagamento e total pago
```

### Exemplo de saída

```
══════════════════════════════════════════════════════════════
  MÓDULO 1 — IDENTIFICAÇÃO DO CARREGADOR
══════════════════════════════════════════════════════════════
  [1] Digitar o código   [2] Simular QR Code
  → B-9999
  ✅ Carregador B-9999 encontrado! 22 kW AC | Disponível

══════════════════════════════════════════════════════════════
  MÓDULO 4 — META DE CARREGAMENTO
══════════════════════════════════════════════════════════════
  Meta: 80% | Energia: 36.0 kWh | Tempo: 4h 56min | R$ 43,20
  💬 Nossa IA vai distribuir os 36.0 kWh de forma eficiente
     entre os carregadores — menor impacto ambiental.

══════════════════════════════════════════════════════════════
  MÓDULO 7 — CARREGAMENTO EM ANDAMENTO
══════════════════════════════════════════════════════════════
  🔋  35%  [████████████░░░░░░░░░░░░░░░░░░░░░░░]  R$ 10,80
  🔋  80%  [████████████████████████████░░░░░░░]  R$ 43,20
  ✅ Carregamento concluído!
```

---


## 📈 Impactos Esperados

- ✅ Zero multas por ultrapassagem de demanda contratada
- ✅ Monetização do eletroposto desde o primeiro mês
- ✅ Menor consumo da rede por sessão graças à IA
- ✅ Experiência de usuário simples: código ou QR Code → meta → pagar → carregar

---

## 📊 Status das Sprints

### Sprint 1 — Pesquisa e Proposta ✅
| Disciplina | Responsável | Status |
|---|---|---|
| Pensamento Computacional e Automação com Python | Victor | ✅ |
| Soluções em Energias Renováveis e Sustentáveis | Victor | ✅ |
| Modelagem Linear para Aprendizado de Máquina | Isabela | ✅ |
| Modelagem Matemática e Computacional | Isabela | ✅ |
| Prompt and Artificial Intelligence | Gustavo | ✅ |
| Data Structures and Algorithms | Artur | ✅ |
| Computer Organization and Architecture | Miguel | ✅ |
| Computer Science | Miguel | ✅ |

### Sprint 2 — Prova de Conceito Funcional ✅
| Disciplina | Responsável | Status |
|---|---|---|
| Pensamento Computacional e Automação com Python | Victor | ✅ |
| Soluções em Energias Renováveis e Sustentáveis | Victor | ✅ |
| Modelagem Linear para Aprendizado de Máquina | Isabela | ✅ |
| Modelagem Matemática e Computacional | Isabela | ✅ |
| Prompt and Artificial Intelligence | Gustavo | ✅ |
| Data Structures and Algorithms | Artur | ✅ |
| Computer Organization and Architecture | Miguel | ✅ |
| Computer Science | Miguel | ✅ |

---

*WeCharge — Equipe EV Challenge 2026 | FIAP*
