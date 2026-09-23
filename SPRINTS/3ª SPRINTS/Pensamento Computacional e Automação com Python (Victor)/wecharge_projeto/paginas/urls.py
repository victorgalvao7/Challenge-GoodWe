from django.urls import path
from . import views

app_name = 'paginas'

urlpatterns = [
    path('', views.home, name='home'),
    path('suporte/', views.suporte, name='suporte'),
    path('api/suporte-chat', views.api_suporte_chat, name='api_suporte_chat'),
    # nova página? crie a função em views.py e adicione uma linha aqui
]
