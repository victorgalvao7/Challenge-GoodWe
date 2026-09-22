# ⚡ WeCharge — ChargeGrid Intelligence

**WeCharge | GoodWe EV Challenge 2026 | FIAP**

Plataforma web de gerenciamento de eletropostos, com painel do operador (dono do ponto de recarga) e painel do motorista (sessão de carga completa, do cadastro ao pagamento).

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

🔗 [COLAR LINK DO VÍDEO NOVO AQUI]

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

## 💡 O que foi construído (Sprint 3)

Nas Sprints 1 e 2 o WeCharge era uma proposta — ainda não existia código. Na
Sprint 3 o time construiu um **protótipo funcional real em Django**, com
todo o fluxo de recarga simulado de ponta a ponta (sem hardware físico
GoodWe ainda, mas com toda a lógica de negócio, cobrança e dados
funcionando de verdade sobre banco de dados).

### ⚡ 1. Cadastro de pontos de recarga (operador)
O dono do eletroposto cadastra o ponto físico (nome, endereço, posição
no mapa, tarifa por kWh) e recebe um **token de 5 caracteres + QR Code**
gerado automaticamente para colar no equipamento.

### 🔌 2. Sessão de recarga (motorista)
O motorista adiciona o carregador pelo token ou QR Code, libera e
inicia a sessão. O sistema acompanha em **tempo real**: kWh entregues,
% de bateria e custo acumulado — com cobrança adicional por tempo
excedente na vaga após a bateria completar.

### 💳 3. Pagamento
Tela de cobrança com Pix, cartão de crédito ou débito (interface
completa; sem gateway de pagamento real integrado ainda).

### 🤖 4. WeChat — assistente de IA
Assistente que responde perguntas como *"qual carregador mais perto de
um McDonald's?"*: primeiro tenta casar o lugar citado com o
nome/endereço dos próprios pontos cadastrados; se não achar, usa
geocodificação gratuita (Nominatim/OpenStreetMap, o mesmo serviço do
mapa) para localizar o lugar e comparar a distância com os pontos do
banco. A IA (OpenAI) só interpreta a pergunta e formata a resposta — a
busca e o cálculo de distância são feitos em Python puro, para não
haver risco de a IA inventar um carregador ou distância inexistente.

### 📊 5. Painel do operador
Mostra dados agregados **reais** (não mais valores de exemplo):
sessões em uso, energia vendida, receita e lucro estimado, apenas dos
pontos pertencentes à conta logada.

---

## 🏗️ Arquitetura do Sistema

```
┌──────────────────────────────────────────────────────────┐
│                    WeCharge Platform (Django)             │
│                                                            │
│   contas/            painel/                operador/     │
│  cadastro,        motorista: adicionar,    dono do ponto: │
│  login, define    liberar, iniciar,        cadastra pontos│
│  is_staff →        acompanhar, finalizar,   (mapa, tarifa,│
│  painel/operador   pagar, WeChat            token/QR),    │
│                                              vê receita     │
│         └────────────────┬─────────────────────┘          │
│                           │                                │
│                  Banco de dados (SQLite)                   │
│         PontoCarregamento  ·  Carregador (sessão)           │
└──────────────────────────────────────────────────────────┘
```

- **`contas`** — cadastro/login; o campo `is_staff` decide se a pessoa
  vai para `painel` (motorista) ou `operador` (dono do ponto).
- **`operador`** — cadastra `PontoCarregamento` (nome, endereço,
  lat/long via mapa Leaflet, tarifa) e gera o token/QR do equipamento.
- **`painel`** — usa o token/QR para abrir um `Carregador` (sessão),
  acompanha em tempo real e paga ao final.
- Todos os apps leem e gravam no mesmo banco, então o preço definido
  pelo operador e o cobrado do motorista são sempre o mesmo dado — e
  uma alteração de tarifa não muda uma sessão já em andamento.

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| Backend | Django (Python) |
| Banco de dados | SQLite (dev) |
| Mapa / geolocalização | Leaflet + Nominatim (OpenStreetMap) |
| IA (WeChat) | OpenAI API — interpretação de linguagem natural |
| Pagamentos | Pix, cartão de crédito, cartão de débito (interface) |
| Identificação do ponto | Token físico de 5 caracteres + QR Code |
| Frontend | HTML/CSS/JS (tema escuro "voltaico") servido pelo próprio Django |

> Hardware GoodWe real, protocolo OCPP e app mobile React Native fazem
> parte da visão de produto de longo prazo do time, mas não fazem parte
> deste protótipo — que é 100% simulado em software.

---

## 🧪 Como rodar o projeto

**Requisitos:** Python 3.10+ (recomendado).

```bash
cd wecharge_v1.12
python -m venv venv
# Windows: venv\Scripts\activate      Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/` — a tela inicial é o site público, com
**Entrar** / **Cadastre-se** no menu. Ao cadastrar, escolha o tipo de
conta (Usuário ou Administrador) para cair no painel certo.

(Opcional) Para ver tudo pelo admin do Django:
```bash
python manage.py createsuperuser
```

Veja `REGISTRO_INTEGRACAO.md` para o histórico completo de como o
protótipo foi construído e testado (isolamento entre usuários, CSRF,
fluxo ponta a ponta).

---

## 📈 Impactos Esperados

- ✅ Monetização do eletroposto desde o primeiro mês (cobrança nativa)
- ✅ Rastreabilidade total de cada sessão de carga (kWh, custo, tempo)
- ✅ Experiência simples: token/QR Code → liberar → carregar → pagar
- ✅ Assistente de IA reduz atrito na hora de achar um ponto disponível

---

## 📊 Status das Sprints

### Sprint 1 — Pesquisa e Proposta ✅
### Sprint 2 — Prova de Conceito (simulação em Python) ✅
### Sprint 3 — Prototipagem Funcional e Integração ✅

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
