from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoginPorUsernameOuEmailTestCase(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="motorista1",
            email="motorista1@exemplo.com",
            password="senha-segura-123",
        )

    def test_login_com_username(self):
        resposta = self.client.post(
            reverse("contas:login"),
            {"username": "motorista1", "password": "senha-segura-123"},
        )
        self.assertRedirects(resposta, reverse("contas:pos_login"), fetch_redirect_response=False)

    def test_login_com_email(self):
        resposta = self.client.post(
            reverse("contas:login"),
            {"username": "motorista1@exemplo.com", "password": "senha-segura-123"},
        )
        self.assertRedirects(resposta, reverse("contas:pos_login"), fetch_redirect_response=False)

    def test_login_com_email_maiusculo(self):
        resposta = self.client.post(
            reverse("contas:login"),
            {"username": "MOTORISTA1@EXEMPLO.COM", "password": "senha-segura-123"},
        )
        self.assertRedirects(resposta, reverse("contas:pos_login"), fetch_redirect_response=False)

    def test_login_com_senha_errada_falha(self):
        resposta = self.client.post(
            reverse("contas:login"),
            {"username": "motorista1@exemplo.com", "password": "senha-errada"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Usuário ou senha incorretos.")

    def test_login_com_email_de_outro_usuario_nao_vaza_acesso(self):
        resposta = self.client.post(
            reverse("contas:login"),
            {"username": "naoexiste@exemplo.com", "password": "senha-segura-123"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Usuário ou senha incorretos.")


class CadastroLogaAutomaticamenteTestCase(TestCase):
    """Cobre o bug relatado: com dois backends de autenticação
    configurados (username e e-mail), o Django não sabia sozinho qual
    usar pra logar o usuário logo após o cadastro, e o cadastro quebrava
    com ValueError ("multiple authentication backends configured")."""

    def test_cadastro_loga_o_usuario_automaticamente_sem_erro(self):
        resposta = self.client.post(
            reverse("contas:cadastro"),
            {
                "nome_completo": "Victor Vieira Galvão",
                "email": "victorgalvao582@gmail.com",
                "telefone": "",
                "cidade": "",
                "username": "Victor Vieira Galvão",
                "senha": "Arrozdoce123!",
                "confirmar_senha": "Arrozdoce123!",
                "tipo_conta": "usuario",
            },
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(User.objects.filter(username="Victor Vieira Galvão").exists())

        # Confirma que a sessão já ficou autenticada (não precisa logar de
        # novo manualmente depois de se cadastrar).
        resposta_painel = self.client.get(reverse("painel:painel"))
        self.assertEqual(resposta_painel.status_code, 200)
