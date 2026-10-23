from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .forms import CadastroForm, ContaForm
from .models import Perfil


def cadastro(request):
    """
    Tela de cadastro. Pede informações pessoais + escolha do tipo de
    conta (usuário ou administrador) e salva tudo no banco.

    O tipo de conta escolhido vira o campo is_staff do usuário:
    - 'usuario'        -> is_staff = False
    - 'administrador'  -> is_staff = True

    Depois de cadastrar, a pessoa já é logada automaticamente e mandada
    para o painel certo (ver contas/views.py -> pos_login).
    """
    if request.method == 'POST':
        form = CadastroForm(request.POST)
        if form.is_valid():
            dados = form.cleaned_data

            usuario = User.objects.create_user(
                username=dados['username'],
                email=dados['email'],
                password=dados['senha'],
                is_staff=(dados['tipo_conta'] == 'administrador'),
            )
            Perfil.objects.create(
                usuario=usuario,
                nome_completo=dados['nome_completo'],
                telefone=dados['telefone'],
                cidade=dados['cidade'],
            )

            # Especifica o backend explicitamente: como agora há dois
            # backends de autenticação configurados (login por username ou
            # por e-mail), o Django não sabe sozinho qual usar pra logar
            # automaticamente o usuário recém-criado — sem isso, dava erro
            # "multiple authentication backends configured".
            login(request, usuario, backend='contas.backends.UsuarioOuEmailBackend')
            return redirect('contas:pos_login')
    else:
        form = CadastroForm()

    return render(request, 'contas/cadastro.html', {'form': form})


@login_required
def pos_login(request):
    """
    Depois do login (ou cadastro), decide para qual painel mandar:
    - is_staff = True  -> área do administrador (operador do eletroposto)
    - is_staff = False -> área do usuário comum (motorista)
    """
    if request.user.is_staff:
        return redirect('operador:painel')
    return redirect('painel:painel')


@login_required
def conta(request):
    """
    Página 'Conta': dados pessoais editáveis, histórico de carregamentos
    (só para usuários comuns) e botão de sair no final.
    """
    perfil, _ = Perfil.objects.get_or_create(
        usuario=request.user,
        defaults={'nome_completo': request.user.get_full_name() or request.user.username},
    )

    if request.method == 'POST':
        form = ContaForm(request.POST, usuario_atual=request.user)
        if form.is_valid():
            dados = form.cleaned_data
            request.user.email = dados['email']
            request.user.save(update_fields=['email'])

            perfil.nome_completo = dados['nome_completo']
            perfil.telefone = dados['telefone']
            perfil.cidade = dados['cidade']
            perfil.save()

            messages.success(request, 'Dados atualizados com sucesso.')
            return redirect('contas:conta')
    else:
        form = ContaForm(usuario_atual=request.user, initial={
            'nome_completo': perfil.nome_completo,
            'email': request.user.email,
            'telefone': perfil.telefone,
            'cidade': perfil.cidade,
        })

    contexto = {
        'titulo': 'Conta',
        'form': form,
    }
    return render(request, 'contas/conta.html', contexto)
