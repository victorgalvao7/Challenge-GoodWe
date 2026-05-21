# ⚡ WeCharge — ChargeGrid Intelligence

> **Sprint 1 | GoodWe EV Challenge 2026 | FIAP**  
> Plataforma de gerenciamento inteligente de eletropostos comerciais integrada ao ecossistema GoodWe.

---

## 👥 Equipe

| Nome | RM |
|------|----|
| Victor Vieira Galvao | *(571483)* |
| Miguel Silverio de Avila | *(568873)* |
| Isabela Camargo Souza | *(569196)* |
| Gustavo Gamba Zancopé | *(569287)* |
| Artur Souza Pereira | *(570880)* |

---

## 🚗 O Problema

A infraestrutura de carregamento de veículos elétricos (VEs) no Brasil ainda enfrenta barreiras críticas para escalar do ambiente residencial para o comercial:

- **Sobrecarga elétrica** em horários de pico com múltiplos carregadores simultâneos
- **Ausência de sistemas de cobrança** nativos, inviabilizando a monetização do eletroposto
- **Experiência do usuário fragmentada**, com múltiplos apps, processos de autenticação confusos e falta de feedback em tempo real
- **Ineficiência energética**: energia solar gerada não é aproveitada no momento ideal de carregamento

Esses problemas representam os principais obstáculos para que empresas, shoppings, estacionamentos e frotas corporativas adotem infraestrutura de carregamento VE em escala.

---

## 💡 Nossa Proposta: WeCharge

O **WeCharge** é uma plataforma de gerenciamento inteligente de eletropostos comerciais que integra carregadores, inversores solares GoodWe, baterias e inteligência artificial em uma solução unificada.

### Os 3 Pilares da Solução

#### ⚡ 1. Controle Dinâmico de Demanda
Algoritmo de **Dynamic Load Balancing** que redistribui a potência disponível entre os carregadores ativos em tempo real, respeitando o limite contratado com a concessionária e priorizando veículos por critérios configuráveis (urgência, tipo de usuário, contrato).

#### 💳 2. Billing Integrado
Sistema completo de cobrança por **kWh consumido**, com suporte a **PIX, cartão e QR Code**. O usuário vê o valor em tempo real antes e durante o carregamento. O operador configura tarifas via painel web.

#### 🤖 3. IA Preditiva de Carregamento
Modelo de **machine learning (LSTM)** que prevê demanda, analisa geração solar e preços de energia para otimizar o agendamento do carregamento — reduzindo custos e maximizando o uso de energia renovável.

---

## 🌱 Sustentabilidade & Energias Renováveis

O WeCharge foi concebido com sustentabilidade como requisito de design, não como opcional:

| Princípio | Implementação no WeCharge |
|-----------|--------------------------|
| **Energia Solar Prioritária** | IA direciona a geração fotovoltaica GoodWe para os carregadores antes de usar a rede |
| **Ciclo de Carbono Zero** | VEs carregados com energia 100% solar eliminam emissões do ciclo de uso |
| **Maximização do Autoconsumo** | Evita exportação de energia solar para a rede com baixa remuneração |
| **Transição de Frota** | Viabiliza economicamente eletropostos comerciais, acelerando a adoção de VEs |

A integração nativa com inversores e baterias GoodWe permite ao WeCharge coordenar em tempo real a tríade **gerar → armazenar → carregar**, tornando o eletroposto um ativo energético ativo dentro do edifício.

---

## 🛠️ Tecnologias Envolvidas

| Camada | Tecnologia |
|--------|-----------|
| Protocolo de comunicação | OCPP 2.0 (WebSocket + TLS) |
| Hardware | Carregadores GoodWe, Inversores GoodWe, BESS GoodWe |
| IA / ML | LSTM para séries temporais de demanda e geração solar |
| Pagamentos | PIX, gateway de cartões, QR Code OCPP |
| App mobile | React Native (iOS + Android) |
| Backend | API REST + CSMS (Charge Point Management System) |
| Painel operador | Dashboard web (React) |

---

## 📈 Impactos Esperados

- **Eliminação de multas** por ultrapassagem de demanda contratada
- **Redução de até 30%** no custo de energia elétrica via otimização com solar
- **Monetização viável** do eletroposto desde o primeiro mês de operação
- **Redução da pegada de carbono** associada ao carregamento de VEs
- **Experiência de usuário** equivalente aos melhores players globais (Tesla Supercharger, IONITY)

---

## 📂 Estrutura do Repositório

```
├── documentacao.pdf        # Pesquisa completa (Sprint 1)
├── apresentacao.pdf        # Slides da apresentação (Sprint 1)
├── video.txt               # Link do vídeo no YouTube
└── README.md               # Este arquivo
```

---

## 🎥 Vídeo de Apresentação

> Link disponível no arquivo https://www.youtube.com/watch?v=WHlv2OApuOY

---

## 📋 Pensamento Computacional Aplicado

| Princípio | Aplicação |
|-----------|-----------|
| **Decomposição** | Problema dividido em 3 pilares independentes com análise e solução próprias |
| **Reconhecimento de Padrões** | Identificação da coordenação centralizada como solução transversal a todos os problemas |
| **Abstração** | Foco nos fluxos (energia, dados, financeiro) sem dependência de hardware específico |
| **Algoritmos** | Cada solução: `entrada de dados → processamento IA → resposta otimizada` |

---

*WeCharge — Equipe EV Challenge 2026 | FIAP*
