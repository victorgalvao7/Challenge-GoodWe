from django.urls import path

from . import views

app_name = 'painel'

urlpatterns = [
    # Páginas
    path('', views.painel, name='painel'),
    path('historico/', views.historico, name='historico'),
    path('adicionar/', views.adicionar, name='adicionar'),
    path('carregador/<uuid:charger_id>/', views.detalhe_carregador, name='detalhe_carregador'),
    path('pagamento/<uuid:charger_id>/', views.pagamento, name='pagamento'),
    path('pagamento/<uuid:charger_id>/sucesso/', views.pagamento_sucesso, name='pagamento_sucesso'),

    # API (JSON, chamada via fetch() pelo JavaScript das páginas)
    path('api/chargers/proximos', views.api_carregadores_proximos, name='api_carregadores_proximos'),
    path('api/ioi-chat', views.api_ioi_chat, name='api_ioi_chat'),
    path('api/chargers/add', views.api_add_charger, name='api_add_charger'),
    path('api/chargers/<uuid:charger_id>/iniciar', views.api_iniciar, name='api_iniciar'),
    path('api/chargers/<uuid:charger_id>/status', views.api_status, name='api_status'),
    path('api/chargers/<uuid:charger_id>/finalizar', views.api_finalizar, name='api_finalizar'),
    path('api/chargers/<uuid:charger_id>/pagar', views.api_pagar, name='api_pagar'),
    path('api/chargers/<uuid:charger_id>/reutilizar', views.api_reutilizar, name='api_reutilizar'),
]
