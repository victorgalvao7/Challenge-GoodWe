from django.urls import path
from . import views

app_name = 'operador'

urlpatterns = [
    path('', views.painel, name='painel'),
    path('carregadores/novo/', views.adicionar_ponto, name='adicionar_ponto'),
    path('carregadores/<int:ponto_id>/editar/', views.editar_ponto, name='editar_ponto'),
    path('carregadores/<int:ponto_id>/alternar/', views.alternar_ponto, name='alternar_ponto'),
    path('carregadores/<int:ponto_id>/qrcode/', views.imprimir_qrcode, name='imprimir_qrcode'),
    path('carregadores/<int:ponto_id>/qrcode/imagem/', views.qrcode_png, name='qrcode_png'),
]
