"""
URL configuration for core project.

Para adicionar um novo app ao site:
1. Crie o app: python manage.py startapp nome_do_app
2. Adicione 'nome_do_app' em INSTALLED_APPS (core/settings.py)
3. Crie um arquivo urls.py dentro do app
4. Inclua esse app aqui embaixo com path('rota/', include('nome_do_app.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('paginas.urls')),
    path('conta/', include('contas.urls')),
    path('painel/', include('painel.urls')),
    path('operador/', include('operador.urls')),
    # exemplo para o futuro:
    # path('blog/', include('blog.urls')),
]
