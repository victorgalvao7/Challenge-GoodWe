> **EV Challenge 2026 | Sprint 1 — Projeto Sustentável em Arquitetura de Computadores**
---
## Integrantes
| Nome                     | RM       |
|--------------------------|----------|
| Miguel Silverio de Avila | RM568873 |
| Artur Souza Pereira      | RM570880 |
| Gustavo Gamba Zancopé    | RM569287 |
| Isabela Camargo Souza    | RM569196 |
| Victor Vieira Galvão     | RM571483 |
---

## Problema
Eletropostos modernos dependem majoritariamente de **software de alto nível** rodando em **hardware genérico** (PCs industriais, SBCs superdimensionados). Essa escolha, embora conveniente para o desenvolvimento, gera impactos reais:
- **Consumo desnecessário de energia** — processadores operam em capacidade muito superior ao necessário para tarefas simples como leitura de sensores e autenticação de usuários.
- **Baixa eficiência no processamento** — camadas de abstração (sistema operacional, runtime, bibliotecas) adicionam overhead de ciclos de CPU sem agregar valor funcional.
- **Desperdício de recursos computacionais** — tarefas determinísticas e repetitivas (ex: leitura de corrente/tensão) não se beneficiam de hardware complexo.
- **Impacto na sustentabilidade** — cada watt desperdiçado no sistema de controle do eletroposto representa energia renovável que deixa de ser aproveitada pelo veículo elétrico.
---

## Justificativa
A eficiência energética começa **antes** da tomada. Um eletroposto que desperdiça energia em seu próprio sistema de controle contradiz o propósito da mobilidade elétrica sustentável.

Estudos de microcontroladores RISC de baixo consumo demonstram que tarefas de controle embarcado podem ser executadas com **menos de 1 mW de consumo ativo**, em contraste com sistemas baseados em Linux embarcado que consomem **1–5 W apenas para o sistema operacional**.

A programação em **Assembly** elimina todo o overhead de camadas de abstração, permitindo:
- Controle preciso de cada ciclo de clock
- Uso mínimo de registradores
- Ausência de alocação dinâmica de memória
- Latência determinística nas operações críticas
---

## Proposta de Solução

Desenvolvimento de um **módulo de controle embarcado otimizado em Assembly** para gerenciar as operações críticas de um eletroposto, projetado para rodar em microcontroladores RISC de baixo consumo.

## Funcionalidades do Módulo

| Função                    | Descrição                                                          |
|---------------------------|--------------------------------------------------------------------|
| Autenticação de usuário   | Leitura e validação de ID por RFID com verificação de hash simples |
| Controle de carga         | Gerenciamento do ciclo de carga via modulação PWM direta           |
| Monitoramento de sensores | Leitura periódica de tensão, corrente e temperatura via ADC        |
| Comunicação serial        | Transmissão de telemetria para sistema central via UART            |
| Gerenciamento de energia  | Entrada em modo sleep entre eventos para redução máxima de consumo | 


### Fluxo de Operação
```
[Boot] → [Init Periféricos] → [Aguarda Evento]
                                      ↓
                          ┌─── [RFID Detectado]
                          │         ↓
                          │   [Valida ID] → [Falha] → [Sinaliza Erro]
                          │         ↓ OK
                          │   [Inicia Carga PWM]
                          │         ↓
                          │   [Loop: Lê Sensores → Ajusta PWM → Envia Telemetria]
                          │         ↓
                          └─── [Carga Completa → Sleep Mode]
```
---
## Arquitetura Utilizada
'''Escolha: RISC-V (RV32I) / ARM Cortex-M0+'''

A arquitetura **RISC (Reduced Instruction Set Computer)** foi escolhida por:

| Característica       | RISC                         | CISC                        |
|----------------------|------------------------------|-----------------------------|
| Instruções           | Simples, tamanho fixo        | Complexas, tamanho variável |
| Ciclos por instrução | ~1 ciclo (ideal)             | 1–20+ ciclos                |
| Pipeline             | Eficiente (estágios simples) | Mais difícil de otimizar    |
| Consumo energético   | Baixo                        | Mais elevado                |
| Programação Assembly | Direto e previsível          | Mais complexo               |

### Conceitos Aplicados

- **Pipeline de 5 estágios** (IF → ID → EX → MEM → WB): instruções RISC completam 1 instrução por ciclo em regime estacionário.
- **Cache L1**: acesso a dados de sensores em cache (1–2 ciclos) vs RAM (10+ ciclos), reduzindo latência e consumo.
- **Clock dinâmico**: frequência reduzida (ex: 1 MHz) durante monitoramento de rotina; frequência plena (48 MHz) apenas durante processamento intenso.
- **Modos de baixo consumo**: instruções `WFI` (Wait For Interrupt) permitem ao processador consumir < 10 µA enquanto aguarda eventos.
---

# Trechos de Código Assembly
# 1. Inicialização do Sistema (RISC-V / RV32I)
```
; ============================================================
; EletroCore — Inicialização do Sistema
; ============================================================

.section .text
.global _start

_start:
   
    la   sp, _stack_top             ;Inicializa stack pointer

    li   x5, 0          ; t0 = 0 (flag de estado)           ;Zera registradores de uso geral
    li   x6, 0          ; t1 = 0 (contador de leituras)
    li   x7, 0          ; t2 = 0 (valor do sensor)

    li   a0, 0x40000000  ; Base GPIO        ;Configura endereço base dos periféricos
    li   a1, 0x40001000  ; Base UART
    li   a2, 0x40002000  ; Base ADC
    
    call init_gpio                  ; Chama rotina de inicialização de periféricos
    call init_uart
    call init_adc

    j    main_loop              ; Entra no loop principal
    
```
### 2. Leitura de Sensor ADC (Corrente)
```asm

; ============================================================
; Rotina: read_current_sensor
; Entrada: a2 = endereço base do ADC
; Saída:   a0 = valor lido (12 bits, 0–4095)
; Ciclos estimados: ~8 ciclos (vs ~40+ em C compilado)
; ============================================================

read_current_sensor:
    ; Dispara conversão ADC (escreve 1 no bit START)
    li   t0, 0x01
    sw   t0, 0(a2)       ; ADC_CR = START

wait_adc:
    ; Aguarda flag EOC (End of Conversion) — bit 0 do status
    lw   t1, 4(a2)       ; lê ADC_SR
    andi t1, t1, 0x01    ; isola bit EOC
    beqz t1, wait_adc    ; loop enquanto EOC = 0

    ; Lê resultado do registrador de dados
    lw   a0, 8(a2)       ; a0 = ADC_DR (resultado 12 bits)
    andi a0, a0, 0x0FFF  ; máscara para garantir 12 bits

    ret
```

### 3. Controle PWM para Carga da Bateria
```asm
; ============================================================
; Rotina: set_charge_pwm
; Entrada: a0 = duty cycle desejado (0–255)
; Descrição: Ajusta PWM do controlador de carga
; ============================================================

set_charge_pwm:
    li   t0, 0x40003000  ; Base do timer/PWM

    ; Valida range (0–255)
    li   t1, 255
    bltu t1, a0, clamp_max   ; se a0 > 255, vai para clamp
    j    write_pwm

clamp_max:
    li   a0, 255

write_pwm:
    ; Escreve duty cycle no registrador de comparação
    sw   a0, 8(t0)       ; TIM_CCR = duty cycle

    ; Atualiza flag de estado
    li   t2, 1
    sw   t2, 0(x5)       ; estado = CARREGANDO

    ret
```

### 4. Comparação de Eficiência: C vs Assembly
```c
// Versão em C — compilador gera ~15–20 instruções
int read_sensor(int* adc_base) {
    *(adc_base + 0) = 1;           // START
    while (!(*(adc_base + 1) & 1)); // wait EOC
    return *(adc_base + 2) & 0xFFF; // read
}
// Estimativa: ~20 ciclos de CPU
```
```asm
; Versão Assembly equivalente — 8 instruções diretas
; Estimativa: ~8 ciclos de CPU → ~60% de redução
read_sensor:
    li   t0, 1
    sw   t0, 0(a0)
.loop:
    lw   t1, 4(a0)
    andi t1, t1, 1
    beqz t1, .loop
    lw   a0, 8(a0)
    andi a0, a0, 0xFFF
    ret
```
---

## Impactos Esperados
### Redução de Consumo Energético

| Componente             | Sis. Tradicional(Linux + Py) | EletroCore (Assembly + MCU)| Redução     | 
|------------------------|------------------------------|----------------------------|-------------|
| Processador (ativo)    | ~2.000 mW                    | ~5 mW                      | **~99,75%** |
| Processador (idle)     | ~500 mW                      | ~0,01 mW                   | **~99,99%** |
| Memória RAM utilizada  | ~256 MB                      | ~4 KB                      | **~99,99%** |
| Energia anual (contr.) | ~17,5 kWh                    | ~0,04 kWh                  | **~99,8%**  |

> *Valores estimados para comparação conceitual entre um SBC (ex: Raspberry Pi) vs microcontrolador RISC-V (ex: GD32VF103)*

### Impacto em Escala
Considerando uma rede de **1.000 eletropostos**:
- Economia de ~17.460 kWh/ano apenas no sistema de controle
- Equivalente a ~87 carregamentos completos de veículos elétricos (bateria de 200 kWh)
- Redução de ~8,7 toneladas de CO₂ (considerando a matriz energética média)
---

## Relação com Sustentabilidade e Energias Renováveis
A proposta se conecta à sustentabilidade em múltiplas dimensões:

### 1. Eficiência Energética Direta
 Menor consumo do sistema de controle = mais energia disponível para o veículo. Em eletropostos alimentados por energia solar ou eólica, cada watt economizado no controle representa menor dependência da rede elétrica convencional.

### 2. Longevidade do Hardware
 Microcontroladores com consumo ultra-baixo geram menos calor, o que:
- Elimina necessidade de sistemas de resfriamento
- Aumenta vida útil do hardware (menos ciclos térmicos)
- Reduz geração de lixo eletrônico (e-waste)

### 3. Menor Pegada de Carbono na Fabricação
 Microcontroladores RISC de baixo consumo têm:
- Menor área de silício (menos matéria-prima)
- Processo de fabricação menos intensivo em energia
- Embalagem e logística mais simples

### 4. Habilitando Eletropostos Off-Grid
 Com consumo de controle na faixa de miliWatts, torna-se viável alimentar o sistema de controle **inteiramente por painéis solares pequenos** (5–10 W), permitindo eletropostos completamente autônomos em locais remotos.

---

## Tecnologias e Ferramentas
- **Assembly RISC-V (RV32I)** — linguagem de programação principal
- **RARS (RISC-V Assembler and Runtime Simulator)** — simulador para testes
- **RISC-V INTERPRETER** - website com simulador para demonstrações na apresentação
- **Wokwi** — simulação de microcontroladores embarcados
- **GCC RISC-V Toolchain** — compilação cruzada para validação
- **Conceitos aplicados**: Pipeline, Cache, Modos de baixo consumo, PWM, ADC, UART
---

## Referências
- Patterson, D. A., & Hennessy, J. L. *Computer Organization and Design RISC-V Edition*. Morgan Kaufmann, 2020.
- RISC-V International. *The RISC-V Instruction Set Manual, Volume I: Unprivileged ISA*. 2023.
- ARM Ltd. *Cortex-M0+ Technical Reference Manual*. 2012.
- IEA. *Global EV Outlook 2024*. International Energy Agency, 2024.
---
