from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm

app_name = 'contas'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(
        template_name='contas/login.html',
        authentication_form=LoginForm,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('pos-login/', views.pos_login, name='pos_login'),
    path('', views.conta, name='conta'),
]
