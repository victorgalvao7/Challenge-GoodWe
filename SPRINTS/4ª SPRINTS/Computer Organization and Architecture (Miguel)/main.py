"""
SPRINT 4 - GoodWe Smart Charging Station
Raspberry Pi Pico + MicroPython (Wokwi)
"""
# Link do Wokwi - https://wokwi.com/projects/478514386565341185

from machine import Pin, ADC, I2C
import time

# 1) CONVERSOR DE REPRESENTACAO DE DADOS (base da Sprint 3)
#   Alteração: preenchimento com zeros foi feito pela funcao _zfill.

def _zfill(texto, tamanho):
    return "0" * (tamanho - len(texto)) + texto


def converter_numero(numero: int, bits: int = 16):
    decimal = numero        #- Números positivos: conversão direta
                            #  - Números negativos:complemento de dois
    if numero < 0:
        valor_ajustado = (1 << bits) + numero  # complemento de dois
        binario = _zfill(bin(valor_ajustado)[2:], bits)
        hexadecimal = _zfill(hex(valor_ajustado)[2:].upper(), bits // 4)
    else:
        binario = bin(numero)[2:]
        hexadecimal = hex(numero)[2:].upper()

    return decimal, binario, hexadecimal


def exibir_conversao(numero: int, bits: int = 16):
    decimal, binario, hexadecimal = converter_numero(numero, bits)
    print("-" * 36)
    print("Decimal:      {}".format(decimal))
    print("Binario:      {}".format(binario))
    print("Hexadecimal:  0x{}".format(hexadecimal))
    print("-" * 36)


# 2) HARDWARE
# LEDs de cada veiculo: (verde, amarelo, vermelho)
LEDS = [
    (Pin(15, Pin.OUT), Pin(14, Pin.OUT), Pin(13, Pin.OUT)),  # EV1
    (Pin(12, Pin.OUT), Pin(11, Pin.OUT), Pin(10, Pin.OUT)),  # EV2
    (Pin(9, Pin.OUT),  Pin(8, Pin.OUT),  Pin(7, Pin.OUT)),   # EV3
]

btn_cenario = Pin(16, Pin.IN, Pin.PULL_UP)   # troca a situacao 1 -> 2 -> 3
btn_modo = Pin(17, Pin.IN, Pin.PULL_UP)      # alterna automatico / manual (potenciometro)

pot_geracao = ADC(26)   # energia disponivel (modo manual)
pot_consumo = ADC(27)   # Sprint 3

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000)


class LCD:
    """Driver minimo LCD 16x2 com adaptador I2C PCF8574 (endereco 0x27)."""
    def __init__(self, i2c, addr=0x27):
        self.i2c = i2c
        self.addr = addr
        time.sleep_ms(50)
        for n in (3, 3, 3, 2):
            self._nibble(n, 0)
            time.sleep_ms(5)
        self.cmd(0x28)
        self.cmd(0x0C)
        self.cmd(0x06)
        self.clear()

    def _write(self, b):
        self.i2c.writeto(self.addr, bytes([b | 0x08]))

    def _nibble(self, n, rs):
        d = (n << 4) | rs
        self._write(d | 0x04)
        self._write(d & ~0x04)

    def cmd(self, c):
        self._nibble(c >> 4, 0)
        self._nibble(c & 0x0F, 0)

    def _data(self, c):
        self._nibble(c >> 4, 1)
        self._nibble(c & 0x0F, 1)

    def clear(self):
        self.cmd(0x01)
        time.sleep_ms(2)

    def put(self, texto, linha):
        self.cmd(0x80 | (0x40 if linha else 0x00))
        texto = (texto + " " * 16)[:16]
        for ch in texto:
            self._data(ord(ch))


try:
    lcd = LCD(i2c)
except OSError:
    lcd = None
    print("LCD nao encontrado - usando apenas o Monitor Serial")

# 3) DADOS DOS VEICULOS (ficam na memoria RAM durante a execucao)
VEICULOS = [
    {"id": "EV1", "bateria": 45, "solicitado": 2000},
    {"id": "EV2", "bateria": 20, "solicitado": 2500},
    {"id": "EV3", "bateria": 70, "solicitado": 3000},
]

POTENCIA_MINIMA = 500                 # W - abaixo disso o veiculo fica em espera
CENARIOS = [8000, 5000, 2000]         # situacoes 1, 2 e 3 (W)
ENERGIA_MAX = 8000

VERDE, AMARELO, VERMELHO = 0, 1, 2
NOME_COR = ("VERDE", "AMARELO", "VERMELHO")
NOME_ESTADO = ("ATIVA", "REDUZIDA", "ESPERA")

# 4) ALGORITMO DE GERENCIAMENTO DE ENERGIA
#    Prioridade = menor bateria primeiro. Cada veiculo, na ordem:
#      - cabe inteiro no que sobrou      -> recarga ativa (verde)
#      - sobrou >= POTENCIA_MINIMA       -> recarga reduzida (amarelo)
#      - sobrou menos que o minimo       -> espera (vermelho)

def distribuir(energia):
    restante = energia
    resultado = {}
    ordem = sorted(VEICULOS, key=lambda v: v["bateria"])
    for v in ordem:
        if restante >= v["solicitado"]:
            alocado, estado = v["solicitado"], VERDE
        elif restante >= POTENCIA_MINIMA:
            alocado, estado = restante, AMARELO
        else:
            alocado, estado = 0, VERMELHO
        restante -= alocado
        resultado[v["id"]] = (alocado, estado)
    return resultado


def status_geral(resultado):
    estados = [e for (_, e) in resultado.values()]
    if VERMELHO in estados:
        return "RECARGA LIMITADA"
    if AMARELO in estados:
        return "RECARGA CONTROLADA"
    return "RECARGA ATIVA"

# 5) SAIDAS
def acender_leds(resultado):
    for i, v in enumerate(VEICULOS):
        estado = resultado[v["id"]][1]
        for cor in range(3):
            LEDS[i][cor].value(1 if cor == estado else 0)


def mostrar(energia, resultado, rotulo):
    demanda = sum(v["solicitado"] for v in VEICULOS)
    status = status_geral(resultado)

    print("=" * 40)
    print(rotulo)
    print("ENERGIA DISPONIVEL: {} W".format(energia))
    for v in VEICULOS:
        alocado, estado = resultado[v["id"]]
        print("{} bat {}% solicita {} W -> {} W [{}] {}".format(
            v["id"], v["bateria"], v["solicitado"], alocado,
            NOME_COR[estado], NOME_ESTADO[estado]))
    print("DEMANDA TOTAL: {} W".format(demanda))
    print("STATUS: {}".format(status))
    print("Representacao da energia disponivel:")
    exibir_conversao(energia)

    if lcd:
        lcd.put("{}W {}".format(energia, status[8:]), 0)
        linha = ""
        for v in VEICULOS:
            linha += "{}{} ".format(v["id"][2], "GYR"[resultado[v["id"]][1]])
        lcd.put(linha, 1)


def aplicar(energia, rotulo):
    resultado = distribuir(energia)
    acender_leds(resultado)
    mostrar(energia, resultado, rotulo)

# 6) LOOP PRINCIPAL
def main():
    print("=== GoodWe Smart Charging Station ===")
    print("Botao GP16: troca de situacao | Botao GP17: modo manual (potenciometro)")

    idx = 0
    manual = False
    ultima_energia = None
    ant_cenario = 1
    ant_modo = 1

    while True:
        atual_cenario = btn_cenario.value()
        atual_modo = btn_modo.value()

        if ant_cenario == 1 and atual_cenario == 0:
            idx = (idx + 1) % 3
            manual = False
            ultima_energia = None
        if ant_modo == 1 and atual_modo == 0:
            manual = not manual
            ultima_energia = None
        ant_cenario, ant_modo = atual_cenario, atual_modo

        if manual:
            bruto = pot_geracao.read_u16()
            energia = (bruto * ENERGIA_MAX // 65535) // 50 * 50   # passos de 50 W
            rotulo = "MODO MANUAL (potenciometro Geracao)"
        else:
            energia = CENARIOS[idx]
            rotulo = "SITUACAO {}".format(idx + 1)

        if energia != ultima_energia:
            aplicar(energia, rotulo)
            ultima_energia = energia

        time.sleep_ms(100)


main()