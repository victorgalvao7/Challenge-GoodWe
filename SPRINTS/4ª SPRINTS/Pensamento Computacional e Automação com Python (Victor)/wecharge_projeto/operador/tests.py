from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from painel.models import Carregador, PontoCarregamento, TOKEN_TAMANHO


class PainelOperadorTestCase(TestCase):
    def setUp(self):
        self.dono = User.objects.create_user(
            username="dono", password="senha-segura", is_staff=True
        )
        self.outro_dono = User.objects.create_user(
            username="outro-dono", password="senha-segura", is_staff=True
        )
        self.motorista = User.objects.create_user(
            username="motorista", password="senha-segura"
        )

    def _dados_ponto(self, quantidade=1, **extra):
        dados = {
            "nome": "WeCharge Centro",
            "quantidade": quantidade,
            "endereco": "Praça da Sé, São Paulo",
            "latitude": "-23.5505",
            "longitude": "-46.6333",
            "preco_kwh": "1.80",
            "ativo": "on",
        }
        dados.update(extra)
        return dados

    def _criar_ponto(self, dono=None, identificador="A1B2C"):
        return PontoCarregamento.objects.create(
            dono=dono or self.dono,
            nome=f"Ponto {identificador}",
            identificador_fisico=identificador,
            endereco="São Paulo",
            latitude=-23.55,
            longitude=-46.63,
            preco_kwh=Decimal("1.80"),
        )

    def test_usuario_normal_nao_acessa_area_do_operador(self):
        self.client.force_login(self.motorista)
        resposta = self.client.get(reverse("operador:painel"))

        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse("painel:painel")))

    def test_dono_cadastra_carregador_com_localizacao_e_preco(self):
        self.client.force_login(self.dono)
        resposta = self.client.post(
            reverse("operador:adicionar_ponto"),
            data=self._dados_ponto(),
        )

        ponto = PontoCarregamento.objects.get()
        self.assertRedirects(
            resposta, reverse("operador:imprimir_qrcode", kwargs={"ponto_id": ponto.id})
        )
        self.assertEqual(ponto.dono, self.dono)
        self.assertEqual(len(ponto.identificador_fisico), TOKEN_TAMANHO)
        self.assertEqual(ponto.preco_kwh, Decimal("1.80"))
        self.assertEqual(ponto.latitude, -23.5505)

    def test_token_e_gerado_automaticamente_e_nao_e_escolhido_no_formulario(self):
        """O operador não escolhe mais o token: ele nasce sozinho, salvo no banco."""
        self.client.force_login(self.dono)
        resposta = self.client.get(reverse("operador:adicionar_ponto"))

        self.assertNotContains(resposta, 'name="identificador_fisico"')

        self.client.post(
            reverse("operador:adicionar_ponto"),
            data=self._dados_ponto(),
        )
        ponto = PontoCarregamento.objects.get()
        self.assertTrue(ponto.identificador_fisico.isalnum())
        self.assertEqual(len(ponto.identificador_fisico), TOKEN_TAMANHO)

    def test_dono_cadastra_varios_carregadores_de_uma_vez_com_tokens_diferentes(self):
        """Ex.: o ADM de um McDonald's cadastrando os 3 carregadores do local
        de uma vez só — mesmo endereço/coordenada, um token por carregador."""
        self.client.force_login(self.dono)

        resposta = self.client.post(
            reverse("operador:adicionar_ponto"),
            data=self._dados_ponto(quantidade=3),
        )

        self.assertRedirects(resposta, reverse("operador:painel"))
        pontos = list(PontoCarregamento.objects.all())
        self.assertEqual(len(pontos), 3)
        tokens = {p.identificador_fisico for p in pontos}
        self.assertEqual(len(tokens), 3)  # todos únicos
        for ponto in pontos:
            self.assertEqual(ponto.latitude, -23.5505)
            self.assertEqual(ponto.endereco, "Praça da Sé, São Paulo")

    def test_formulario_de_cadastro_renderiza_o_mapa(self):
        self.client.force_login(self.dono)

        resposta = self.client.get(reverse("operador:painel"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'id="mapa-cadastro"')
        self.assertContains(resposta, "operador/js/ponto_form.js")

    def test_dono_cadastra_carregador_diretamente_no_painel(self):
        self.client.force_login(self.dono)

        resposta = self.client.post(
            reverse("operador:painel"),
            data=self._dados_ponto(),
        )

        ponto = PontoCarregamento.objects.get()
        self.assertRedirects(
            resposta, reverse("operador:imprimir_qrcode", kwargs={"ponto_id": ponto.id})
        )
        self.assertEqual(ponto.dono, self.dono)
        self.assertEqual(ponto.preco_kwh, Decimal("1.80"))

    def test_dono_edita_preco_do_proprio_carregador(self):
        ponto = self._criar_ponto()
        dados = self._dados_ponto()
        dados["preco_kwh"] = "2.35"
        del dados["quantidade"]  # não existe mais no formulário de edição
        self.client.force_login(self.dono)

        resposta = self.client.post(
            reverse("operador:editar_ponto", kwargs={"ponto_id": ponto.id}),
            data=dados,
        )

        self.assertRedirects(resposta, reverse("operador:painel"))
        ponto.refresh_from_db()
        self.assertEqual(ponto.preco_kwh, Decimal("2.35"))
        # Editar não muda o token que já existia.
        self.assertEqual(ponto.identificador_fisico, "A1B2C")

    def test_dono_nao_edita_carregador_de_outra_conta(self):
        ponto_alheio = self._criar_ponto(
            dono=self.outro_dono, identificador="ZZ999"
        )
        self.client.force_login(self.dono)

        resposta = self.client.get(
            reverse("operador:editar_ponto", kwargs={"ponto_id": ponto_alheio.id})
        )

        self.assertEqual(resposta.status_code, 404)

    def test_painel_mostra_apenas_renda_do_proprio_dono(self):
        ponto = self._criar_ponto()
        ponto_alheio = self._criar_ponto(
            dono=self.outro_dono, identificador="ZZ999"
        )
        Carregador.objects.create(
            usuario=self.motorista,
            ponto=ponto,
            identificador_fisico=ponto.identificador_fisico,
            metodo_identificacao="token",
            apelido=ponto.nome,
            status=Carregador.STATUS_CONCLUIDO,
            tarifa_kwh_aplicada=Decimal("1.80"),
            resumo_final={"energia_kwh": 5, "custo_total": 10},
        )
        Carregador.objects.create(
            usuario=self.motorista,
            ponto=ponto_alheio,
            identificador_fisico=ponto_alheio.identificador_fisico,
            metodo_identificacao="token",
            apelido=ponto_alheio.nome,
            status=Carregador.STATUS_CONCLUIDO,
            tarifa_kwh_aplicada=Decimal("1.80"),
            resumo_final={"energia_kwh": 100, "custo_total": 999},
        )
        self.client.force_login(self.dono)

        resposta = self.client.get(reverse("operador:painel"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["receita_total"], 10.0)
        self.assertContains(resposta, ponto.nome)
        self.assertNotContains(resposta, ponto_alheio.nome)

    def test_dono_pode_desativar_carregador(self):
        ponto = self._criar_ponto()
        self.client.force_login(self.dono)

        resposta = self.client.post(
            reverse("operador:alternar_ponto", kwargs={"ponto_id": ponto.id})
        )

        self.assertRedirects(resposta, reverse("operador:painel"))
        ponto.refresh_from_db()
        self.assertFalse(ponto.ativo)

    def test_qrcode_e_gerado_para_o_carregador_cadastrado(self):
        self.client.force_login(self.dono)
        self.client.post(
            reverse("operador:adicionar_ponto"),
            data=self._dados_ponto(),
        )
        ponto = PontoCarregamento.objects.get()

        resposta_pagina = self.client.get(
            reverse("operador:imprimir_qrcode", kwargs={"ponto_id": ponto.id})
        )
        self.assertEqual(resposta_pagina.status_code, 200)
        self.assertContains(resposta_pagina, ponto.identificador_fisico)

        resposta_imagem = self.client.get(
            reverse("operador:qrcode_png", kwargs={"ponto_id": ponto.id})
        )
        self.assertEqual(resposta_imagem.status_code, 200)
        self.assertEqual(resposta_imagem["Content-Type"], "image/png")
