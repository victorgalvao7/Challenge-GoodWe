from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):
    """
    Informações pessoais extras do usuário, além do que o Django já
    guarda por padrão (username, e-mail, senha).

    O tipo de conta (usuário comum ou administrador) NÃO fica guardado
    aqui - ele usa o campo is_staff do próprio User do Django, porque é
    esse campo que o Django já entende nativamente para dar permissões.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    nome_completo = models.CharField(max_length=150)
    telefone = models.CharField(max_length=20, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome_completo
