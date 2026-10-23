from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

TIPO_CONTA_CHOICES = [
    ('usuario', 'Usuário'),
    ('administrador', 'Administrador'),
]


class LoginForm(AuthenticationForm):
    """Mesma validação de sempre do Django, só com os campos estilizados
    (placeholder em cinza claro dentro do campo, sem rótulo visível em
    cima) para a tela de login ficar mais moderna."""

    username = forms.CharField(
        label='Usuário ou e-mail',
        widget=forms.TextInput(attrs={
            'placeholder': 'Usuário ou e-mail',
            'autocomplete': 'username',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Senha',
            'autocomplete': 'current-password',
        }),
    )


class CadastroForm(forms.Form):
    nome_completo = forms.CharField(label='Nome completo', max_length=150)
    email = forms.EmailField(label='E-mail')
    telefone = forms.CharField(label='Telefone', max_length=20, required=False)
    cidade = forms.CharField(label='Cidade', max_length=100, required=False)
    username = forms.CharField(label='Usuário (login)', max_length=150)
    senha = forms.CharField(label='Senha', widget=forms.PasswordInput)
    confirmar_senha = forms.CharField(label='Confirmar senha', widget=forms.PasswordInput)
    tipo_conta = forms.ChoiceField(
        label='Tipo de conta',
        choices=TIPO_CONTA_CHOICES,
        widget=forms.RadioSelect,
        initial='usuario',
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Esse nome de usuário já está em uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Já existe uma conta com esse e-mail.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        senha = cleaned_data.get('senha')
        confirmar_senha = cleaned_data.get('confirmar_senha')
        if senha and confirmar_senha and senha != confirmar_senha:
            self.add_error('confirmar_senha', 'As senhas não coincidem.')
        return cleaned_data


class ContaForm(forms.Form):
    """Formulário da página 'Conta': edição dos dados pessoais do usuário
    já logado (nome, e-mail, telefone, cidade)."""
    nome_completo = forms.CharField(label='Nome completo', max_length=150)
    email = forms.EmailField(label='E-mail')
    telefone = forms.CharField(label='Telefone', max_length=20, required=False)
    cidade = forms.CharField(label='Cidade', max_length=100, required=False)

    def __init__(self, *args, usuario_atual=None, **kwargs):
        self.usuario_atual = usuario_atual
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email']
        ja_existe = User.objects.filter(email=email)
        if self.usuario_atual:
            ja_existe = ja_existe.exclude(pk=self.usuario_atual.pk)
        if ja_existe.exists():
            raise forms.ValidationError('Já existe uma conta com esse e-mail.')
        return email
