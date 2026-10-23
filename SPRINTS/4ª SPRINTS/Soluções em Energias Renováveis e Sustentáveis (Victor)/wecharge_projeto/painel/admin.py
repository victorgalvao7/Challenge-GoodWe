from django.contrib import admin

from .models import Carregador, PontoCarregamento


@admin.register(Carregador)
class CarregadorAdmin(admin.ModelAdmin):
    list_display = ("apelido", "usuario", "ponto", "status", "identificador_fisico", "endereco", "criado_em")
    list_filter = ("status", "metodo_identificacao")
    search_fields = ("apelido", "identificador_fisico", "usuario__username", "endereco")
    fieldsets = (
        (None, {
            "fields": ("usuario", "ponto", "apelido", "identificador_fisico", "metodo_identificacao", "status"),
        }),
        ("Localização (usada no mapa de carregadores próximos)", {
            "fields": ("endereco", "latitude", "longitude"),
        }),
    )


@admin.register(PontoCarregamento)
class PontoCarregamentoAdmin(admin.ModelAdmin):
    list_display = (
        "nome", "dono", "identificador_fisico", "preco_kwh",
        "endereco", "ativo", "atualizado_em",
    )
    list_filter = ("ativo",)
    search_fields = ("nome", "identificador_fisico", "endereco", "dono__username")
