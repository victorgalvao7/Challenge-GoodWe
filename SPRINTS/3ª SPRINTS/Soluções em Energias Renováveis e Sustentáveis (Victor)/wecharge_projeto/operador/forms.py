from django import forms

from painel.models import PontoCarregamento


class PontoCarregamentoForm(forms.ModelForm):
    """Formulário de cadastro/edição de carregador pelo operador.

    O token físico (identificador_fisico) não é mais escolhido aqui — ele
    é gerado automaticamente e salvo no banco pelo próprio modelo
    (PontoCarregamento.save). O operador continua vendo o token normalmente
    na tabela de carregadores e no QR Code, só não digita mais ele.

    O campo "quantidade" não pertence ao modelo: é só pra facilitar cadastrar
    de uma vez vários carregadores físicos no mesmo endereço/coordenada
    (ex.: os 3 carregadores de um mesmo McDonald's). Cada um recebe seu
    próprio token único; no mapa do usuário eles aparecem agrupados num
    único marcador, já que ficam na mesma localização.
    """

    quantidade = forms.IntegerField(
        label="Quantidade de carregadores neste local",
        min_value=1,
        max_value=10,
        initial=1,
        help_text="Cadastra vários carregadores de uma vez, todos no mesmo endereço/coordenada.",
    )

    class Meta:
        model = PontoCarregamento
        fields = [
            "nome",
            "endereco",
            "latitude",
            "longitude",
            "preco_kwh",
            "ativo",
        ]
        labels = {
            "preco_kwh": "Preço da energia (R$/kWh)",
            "ativo": "Disponível para novas recargas",
        }
        widgets = {
            "latitude": forms.NumberInput(attrs={"step": "any"}),
            "longitude": forms.NumberInput(attrs={"step": "any"}),
            "preco_kwh": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }
        help_texts = {
            "latitude": "Clique no mapa para preencher as coordenadas.",
            "longitude": "Você também pode ajustar as coordenadas manualmente.",
        }

    def __init__(self, *args, mostrar_quantidade=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not mostrar_quantidade:
            # Edição de um carregador já existente: não faz sentido pedir
            # "quantidade", já que estamos editando um único ponto.
            del self.fields["quantidade"]
