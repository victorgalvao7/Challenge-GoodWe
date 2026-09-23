"""
Conversor de Representação de Dados
Converte qualquer número inteiro para Decimal, Binário e Hexadecimal.
"""

def converter_numero(numero: int, bits: int = 16):
    decimal = numero        #- Números positivos: conversão direta.
                            #  - Números negativos: representados em complemento de dois (padrão: 16 bits).
    if numero < 0:
        valor_ajustado = (1 << bits) + numero  # complemento de dois
        binario = bin(valor_ajustado)[2:].zfill(bits)
        hexadecimal = hex(valor_ajustado)[2:].upper().zfill(bits // 4)
    else:
        binario = bin(numero)[2:]
        hexadecimal = hex(numero)[2:].upper()

    return decimal, binario, hexadecimal


def exibir_conversao(numero: int, bits: int = 16):
    decimal, binario, hexadecimal = converter_numero(numero, bits)
    print("-" * 36)
    print("Decimal:      {}".format(decimal))
    print("Binario:      {}".format(binario))
    print("Hexadecimal:  {}".format(hexadecimal))
    print("-" * 36)


def main():
    print("=== Conversor de Representação de Dados ===")
    print("Digite um número inteiro para converter (ou 'sair' para encerrar).\n")

    while True:
        entrada = input("Número: ").strip()

        if entrada.lower() in ("sair", "exit", "q"):
            print("Encerrando.")
            break

        try:
            numero = int(entrada)
        except ValueError:
            print("Entrada inválida. Digite um número inteiro.\n")
            continue

        exibir_conversao(numero)
        print()

if __name__ == "__main__":
    # Exemplos automáticos, cobrindo as 3 situações do projeto de recarga
    print("Exemplos das situações do projeto:\n")
    exibir_conversao(2500)   # Situação 1 - energia suficiente
    exibir_conversao(300)    # Situação 2 - energia limitada
    exibir_conversao(-800)   # Situação 3 - energia insuficiente
    print()

    main()