from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class UsuarioOuEmailBackend(ModelBackend):
    """Autentica o login tanto por username quanto por e-mail.

    O ModelBackend padrão do Django só reconhece o campo `username` —
    então, mesmo a tela de login dizendo "Usuário ou e-mail", digitar o
    e-mail sempre falhava (a menos que o e-mail fosse, por coincidência,
    igual ao username). Esse backend resolve isso: procura o usuário por
    username OU e-mail (sem diferenciar maiúsculas/minúsculas) antes de
    conferir a senha.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identificador = username if username is not None else kwargs.get(User.USERNAME_FIELD)
        if identificador is None or password is None:
            return None

        try:
            usuario = User.objects.get(
                Q(username__iexact=identificador) | Q(email__iexact=identificador)
            )
        except User.DoesNotExist:
            # Mesmo comportamento do ModelBackend original: roda o hasher
            # da senha "no vazio" pra não vazar, por tempo de resposta,
            # se o usuário existe ou não.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # Dois usuários diferentes compartilhando o mesmo e-mail (não
            # deveria acontecer, mas por segurança não autentica nenhum).
            return None

        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None
