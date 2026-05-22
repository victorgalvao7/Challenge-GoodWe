nome do projeto: WeCharge

Integrantes:
- Gustavo Gamba Zancopé RM569287 Turma: 1CCPQ
- Isabela Camargo Souza RM569196 Turma: 1CCPQ
- Artur Souza Pereira RM 570880  Turma: 1CCPQ
- Miguel Silverio de Avila RM568873 Turma: 1CCPQ
- Victor Vieira Galvão RM571483 Turma: 1CCPQ

Contexto do Desafio:

Sprint 1 do projeto de chatbot para o EV Challenge 2026 FIAP + GoodWe, focado em apoiar a operação de uma rede comercial de eletropostos (WeCharge) que utiliza carregadores GoodWe e soluções de gestão de energia.

A GoodWe construiu sua base principalmente em aplicações residenciais (casa + solar + bateria), mas está em um movimento estratégico para ampliar o uso de seus carregadores e soluções de smart charging em ambientes **comerciais e públicos**, como rodosservs, postos em rodovias, redes como Graal, estacionamentos de shopping centers e prédios corporativos. Esses cenários exigem não só carregamento eficiente, mas também gestão de múltiplos pontos, experiência do usuário final e modelos de negócio sustentáveis.[web:90][web:92][web:101]

O problema central abordado é a ausência de mecanismos integrados nos eletropostos comerciais para:

- Orquestrar potência entre múltiplos carregadores em um mesmo site ou rede.
- Registrar e consultar ciclos/sessões de carregamento de forma consolidada.
- Apoiar o faturamento por ponto, site (shopping, posto, rodoserv) e período.
- Comunicar, de forma clara, o estado do sistema para operadores da rede, parceiros comerciais (ex.: shoppings) e usuários finais (motoristas)  a camada de ChargeGrid Intelligence.

Além da camada operacional, o desafio também considera a evolução da WeCharge como experiência completa de carregamento para o motorista, na qual o chatbot atua como “porteiro digital” da rede de eletropostos, permitindo:

- Reservar antecipadamente um carregador em um eletroposto específico (rodosserv, shopping, posto), escolhendo dia e horário, de forma semelhante aos apps modernos de carregamento que oferecem “slot booking” e reserva de estação.

Coletar informações do veículo e da sessão desejada, como modelo do carro, nível atual de bateria (%), quanto o motorista deseja carregar e por quanto tempo pretende ficar parado, para estimar:
  - A energia necessária (kWh estimados).
  - O tempo aproximado de carregamento.
  - O preço estimado da sessão com base na tabela tarifária da WeCharge.
  - Sugerir o melhor eletroposto para carregar em um determinado trajeto, comparando:
  - Preço por kWh ou modelo de cobrança.
  - Potência disponível e tempo esperado de carga.
  - Distância/desvio de rota e disponibilidade do ponto, garantindo que o veículo chegue ao local sem ficar sem bateria, de forma semelhante aos planejadores de rota com estações de carga integradas.
- Em etapas futuras, integrar comandos de voz e assistentes veiculares (ex.: integração com sistemas de infotainment/Android Auto), permitindo que o motorista interaja com o chatbot por voz enquanto dirige, para reservar um carregador, ajustar uma sessão ou recalcular uma rota com base na bateria restante, mantendo foco na segurança e na experiência do usuário.

Proposta do Chatbot WeCharge

O chatbot WeCharge é um assistente de IA focado na operação de uma rede comercial de eletropostos que utilizam carregadores GoodWe e soluções de gestão de energia em ambientes como rodosservs, postos em rodovias, redes como Graal, shoppings e estacionamentos corporativos.

Ele atua como uma camada de inteligência (ChargeGrid Intelligence) e como um “porteiro digital” da rede, com dois pilares principais:

1. Pilar Operacional (B2B – operador/comercial)
   - Consultar o status dos carregadores por site ou rede (ocupado, disponível, em falha, offline).
   - Acompanhar consumo de energia (kWh) e sua origem (solar, bateria, rede), alinhado à lógica de smart charging GoodWe.
   - Apoiar o faturamento por ponto de carga, site (shopping, rodoserv, posto) e período (dia, semana, mês).
   - Identificar situações críticas: carregadores com falha, consumo anormal, baixa utilização em determinados horários.
   - Gerar insights operacionais (horários de pico, sessões de alto valor, uso da potência contratada).

2. Pilar de Experiência do Motorista (B2C – evolução futura)
   - Reservar antecipadamente um carregador em um eletroposto específico, escolhendo dia e horário (slot booking), similar a apps de carregamento comerciais.
   - Coletar dados do veículo e da sessão:
     - Modelo do carro.
     - Nível atual de bateria (%).
     - Quanto o motorista deseja carregar (% ou kWh).
     - Tempo estimado de permanência.
     - A partir disso, estimar:
     - Energia necessária (kWh aproximados).
     - Tempo de carregamento com base na potência do carregador.
     - Preço estimado da sessão com base na tabela tarifária da WeCharge.
     - Recomendar o melhor eletroposto em um trajeto:
     - Comparando preços, potência disponível e tempo de carga.
     - Considerando distância/desvio de rota e disponibilidade dos pontos.
     - Checando se o veículo chega ao eletroposto sem ficar sem bateria, similar a planejadores de rota com estações de carga.
     - Em fases futuras, suporte por voz (via integração com sistemas veiculares/Android Auto), permitindo que o motorista interaja com o chatbot enquanto dirige, mantendo a segurança.

 Tecnologias de IA Selecionadas e Justificativa Técnica

 Modelo de Linguagem (LLM) – Meta Llama 3.x (8B)

  - Escolha: Meta Llama 3.x (8B), acessado por um provedor com free tier (ex.: Groq).
  - Por quê:
  - Modelo open source recente, otimizado para diálogo, com desempenho competitivo em tarefas de chat e análise de texto.
  - Disponível em provedores de API com camada gratuita suficiente para uso acadêmico (prototipagem e testes).
  - Permite, no futuro, migração para execução local (via Ollama ou containers) ou troca de provedor sem reescrever a lógica de negócio.
  - Papel no projeto: interpretar as perguntas em linguagem natural (operador e motorista) e gerar respostas contextualizadas com base em dados operacionais e regras da WeCharge.

 Framework de Orquestração – LangChain (Python)

- Escolha: LangChain, em Python.
- Por quê:
  - Framework open source amplamente usado para construir aplicações com LLM, com suporte a chains, agents, memória de conversa e integração com múltiplos provedores de modelo.
  - Facilita a implementação de:
    - Templates de prompt (system, user, context).
    - Ferramentas/funções Python para buscar dados (ex.: sessões de carga, preços) que o LLM chama quando precisa de informação factual.
    - Futuro RAG com documentos FIAP/GoodWe (PDFs técnicos, tabelas de tarifário etc.).
- Papel no projeto: ser a camada que conecta o LLM com as fontes de dados da WeCharge (mock na Sprint 1; APIs SEMS/GoodWe no futuro).

 Stack de Backend (apoio à IA)

- Linguagem: Python
  - Forte ecossistema para IA e APIs (FastAPI/Flask), além de bibliotecas para integração com APIs GoodWe SEMS.
- API HTTP: FastAPI ou Flask
  - Facilita expor o chatbot como endpoint (REST/WebSocket), integrando depois com web app, bot de chat ou interface veicular.
  - Dados (Sprint 1): arquivos JSON/CSV mockados
  - Representando:
  - Carregadores da rede (ID, site, status, potência).
  - Sessões de carga (inicio/fim, kWh, valor, site, ID do carregador).
  - Tabela tarifária WeCharge (preço por kWh, tarifas por horário).
  - Dados (evolução): integração com GoodWe SEMS / HCA
  - Uso de bibliotecas existentes (`sems-portal-api`, `pygoodwe`) ou APIs oficiais para obter status, energia e eventos dos carregadores em tempo quase real.

Ferramentas de Design e Documentação

- Figma
  - Criação do fluxograma do chatbot (fluxo da pergunta até o consumo de dados e resposta).
- Markdown + GitHub
  - Documentação de todas as decisões técnicas, prompts, modelo de teste e visão de evolução do produto.

A combinação Llama 3 + LangChain + Python foi escolhida por ser gratuita, aberta, flexível e alinhada com o objetivo educacional do EV Challenge 2026, ao mesmo tempo em que permite uma evolução realista para ambientes comerciais de eletropostos.

