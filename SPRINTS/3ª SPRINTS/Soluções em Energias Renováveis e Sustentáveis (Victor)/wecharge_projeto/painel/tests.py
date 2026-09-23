import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Carregador, PontoCarregamento


class FluxoCarregadorTestCase(TestCase):
    def setUp(self):
        self.dono = User.objects.create_user(
            username="dono", password="senha-segura", is_staff=True
        )
        self.motorista = User.objects.create_user(
            username="motorista", password="senha-segura"
        )
        self.outro_motorista = User.objects.create_user(
            username="outro", password="senha-segura"
        )
        self.ponto = PontoCarregamento.objects.create(
            dono=self.dono,
            nome="WeCharge Centro",
            identificador_fisico="A1B2C",
            endereco="Praça da Sé, São Paulo",
            latitude=-23.5505,
            longitude=-46.6333,
            preco_kwh=Decimal("1.50"),
        )

    def _adicionar(self, usuario, token="A1B2C"):
        self.client.force_login(usuario)
        return self.client.post(
            reverse("painel:api_add_charger"),
            data=json.dumps({"metodo": "token", "valor": token}),
            content_type="application/json",
        )

    def test_mapa_lista_ponto_fisico_com_preco(self):
        self.client.force_login(self.motorista)
        resposta = self.client.get(reverse("painel:api_carregadores_proximos"))

        self.assertEqual(resposta.status_code, 200)
        ponto = resposta.json()["carregadores"][0]
        self.assertEqual(ponto["apelido"], "WeCharge Centro")
        self.assertEqual(ponto["identificador_fisico"], "A1B2C")
        self.assertEqual(ponto["status"], "disponivel")
        self.assertEqual(ponto["preco_kwh"], 1.5)

    def test_mapa_nao_lista_ponto_desativado(self):
        self.ponto.ativo = False
        self.ponto.save()
        self.client.force_login(self.motorista)

        resposta = self.client.get(reverse("painel:api_carregadores_proximos"))

        self.assertEqual(resposta.json()["carregadores"], [])

    def test_motorista_so_adiciona_carregador_cadastrado(self):
        resposta = self._adicionar(self.motorista, token="XXXXX")

        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(Carregador.objects.count(), 0)

    def test_sessao_recebe_ponto_e_congela_preco(self):
        resposta = self._adicionar(self.motorista)
        self.assertEqual(resposta.status_code, 200)

        sessao = Carregador.objects.get()
        self.assertEqual(sessao.ponto, self.ponto)
        self.assertEqual(sessao.tarifa_kwh_aplicada, Decimal("1.50"))

        self.ponto.preco_kwh = Decimal("2.40")
        self.ponto.save()
        sessao.status = Carregador.STATUS_CARREGANDO
        sessao.inicio_carregamento = timezone.now() - timezone.timedelta(hours=1)
        sessao.save()

        estado = sessao.estado_atual()
        self.assertEqual(estado["tarifa_kwh"], 1.5)
        self.assertAlmostEqual(estado["custo_energia"], 11.10, places=2)

    def test_carregador_nao_pode_ser_usado_por_duas_pessoas(self):
        primeira = self._adicionar(self.motorista)
        segunda = self._adicionar(self.outro_motorista)

        self.assertEqual(primeira.status_code, 200)
        self.assertEqual(segunda.status_code, 409)
        self.assertEqual(Carregador.objects.count(), 1)

    def test_finalizacao_salva_tarifa_do_dono(self):
        self._adicionar(self.motorista)
        sessao = Carregador.objects.get()
        sessao.status = Carregador.STATUS_CARREGANDO
        sessao.inicio_carregamento = timezone.now() - timezone.timedelta(minutes=30)
        sessao.save()
        self.client.force_login(self.motorista)

        resposta = self.client.post(
            reverse("painel:api_finalizar", kwargs={"charger_id": sessao.id})
        )

        self.assertEqual(resposta.status_code, 200)
        sessao.refresh_from_db()
        self.assertEqual(sessao.resumo_final["tarifa_kwh"], 1.5)

    def test_nao_pode_usar_outro_carregador_com_pagamento_pendente(self):
        ponto2 = PontoCarregamento.objects.create(
            dono=self.dono,
            nome="WeCharge Zona Leste",
            identificador_fisico="Z9Z9Z",
            endereco="Av. Aricanduva, São Paulo",
            latitude=-23.57,
            longitude=-46.55,
            preco_kwh=Decimal("1.90"),
        )

        self._adicionar(self.motorista, token="A1B2C")
        sessao = Carregador.objects.get(identificador_fisico="A1B2C")
        sessao.status = Carregador.STATUS_AGUARDANDO_PAGAMENTO
        sessao.save()

        resposta = self._adicionar(self.motorista, token="Z9Z9Z")

        self.assertEqual(resposta.status_code, 409)
        self.assertIn("pagamento pendente", resposta.json()["erro"])
        # Não criou sessão nenhuma pro segundo carregador.
        self.assertEqual(
            Carregador.objects.filter(ponto=ponto2).count(), 0
        )

    def test_nao_pode_usar_outro_carregador_com_carregamento_em_andamento(self):
        ponto2 = PontoCarregamento.objects.create(
            dono=self.dono,
            nome="WeCharge Zona Leste",
            identificador_fisico="Z9Z9Z",
            endereco="Av. Aricanduva, São Paulo",
            latitude=-23.57,
            longitude=-46.55,
            preco_kwh=Decimal("1.90"),
        )

        self._adicionar(self.motorista, token="A1B2C")
        sessao = Carregador.objects.get(identificador_fisico="A1B2C")
        sessao.status = Carregador.STATUS_CARREGANDO
        sessao.inicio_carregamento = timezone.now()
        sessao.save()

        resposta = self._adicionar(self.motorista, token="Z9Z9Z")

        self.assertEqual(resposta.status_code, 409)
        self.assertEqual(Carregador.objects.filter(ponto=ponto2).count(), 0)

    def test_pode_usar_outro_carregador_depois_de_pago(self):
        ponto2 = PontoCarregamento.objects.create(
            dono=self.dono,
            nome="WeCharge Zona Leste",
            identificador_fisico="Z9Z9Z",
            endereco="Av. Aricanduva, São Paulo",
            latitude=-23.57,
            longitude=-46.55,
            preco_kwh=Decimal("1.90"),
        )

        self._adicionar(self.motorista, token="A1B2C")
        sessao = Carregador.objects.get(identificador_fisico="A1B2C")
        sessao.status = Carregador.STATUS_CONCLUIDO
        sessao.concluido_em = timezone.now()
        sessao.save()

        resposta = self._adicionar(self.motorista, token="Z9Z9Z")

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Carregador.objects.filter(ponto=ponto2).count(), 1)


class IoIChatBuscaPorNomeTestCase(TestCase):
    """Cobre o bug relatado: perguntar pelo carregador perto de um nome
    específico (ex.: "FIAP Paulista") que o Nominatim não conhece, mas que
    já está cadastrado no nosso próprio banco com esse nome."""

    def setUp(self):
        self.dono = User.objects.create_user(
            username="dono", password="senha-segura", is_staff=True
        )
        self.ponto = PontoCarregamento.objects.create(
            dono=self.dono,
            nome="WeCharge FIAP Paulista 1",
            identificador_fisico="F1A9P",
            endereco="Av. Paulista, 1106 - Bela Vista, São Paulo - SP",
            latitude=-23.5615,
            longitude=-46.6540,
            preco_kwh=Decimal("2.20"),
        )

    def test_acha_carregador_pelo_nome_exato(self):
        from .ioi_chat import _executar_ferramenta

        resultado = _executar_ferramenta(
            "carregador_mais_proximo_de",
            {"lugar_referencia": "FIAP Paulista"},
            -23.55, -46.63,
        )
        self.assertIsNone(resultado.get("erro"))
        self.assertEqual(resultado["carregador_mais_proximo"]["identificador_fisico"], "F1A9P")

    def test_acha_carregador_com_variacao_da_pergunta(self):
        """Cobre o caso real relatado: o usuário digitou/falou errado
        ("fia paulista" em vez de "fiap paulista") e ainda assim deve achar."""
        from .ioi_chat import _executar_ferramenta

        resultado = _executar_ferramenta(
            "carregador_mais_proximo_de",
            {"lugar_referencia": "faculdade fia paulista"},
            -23.55, -46.63,
        )
        self.assertIsNone(resultado.get("erro"))
        self.assertEqual(resultado["carregador_mais_proximo"]["identificador_fisico"], "F1A9P")

    def test_nao_bate_com_termo_curto_generico(self):
        """Termos genéricos demais (menos de 3 letras úteis) não devem
        "achar" um carregador aleatório por coincidência."""
        from .ioi_chat import _buscar_carregador_por_nome

        self.assertIsNone(_buscar_carregador_por_nome("a"))
        self.assertIsNone(_buscar_carregador_por_nome(""))


class IoIChatGeocodificacaoTestCase(TestCase):
    """Cobre o bug relatado: o usuário pediu o carregador mais próximo de
    "uma hamburgueria" e a IA recomendou um lugar bem longe (perto da
    FIAP Paulista) por causa de um rodízio de hambúrguer que aparecia
    como resultado "mais relevante" do Nominatim — só que não era o mais
    PRÓXIMO. A busca precisa escolher o resultado mais perto do usuário,
    não o primeiro/mais "importante" da lista do Nominatim."""

    def test_geocodificacao_escolhe_o_resultado_mais_proximo_nao_o_primeiro(self):
        from unittest.mock import MagicMock, patch

        from .ioi_chat import _geocodificar_local

        # Localização de teste: usuário perto de Anália Franco.
        lat_usuario, lon_usuario = -23.5614, -46.5604

        # O Nominatim devolve o resultado "mais relevante" (longe, na
        # Paulista) PRIMEIRO na lista, e o mais perto de verdade (do lado
        # da casa do usuário) depois — é assim que o Nominatim realmente
        # ordena (por importância, não por distância).
        resultados_fake = [
            {
                "display_name": "Rodízio de Hambúrguer Top - Av. Paulista",
                "lat": "-23.5615",
                "lon": "-46.6540",
            },
            {
                "display_name": "Hamburgueria da Esquina - perto do usuário",
                "lat": "-23.5620",
                "lon": "-46.5610",
            },
        ]

        with patch("painel.ioi_chat.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = resultados_fake
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            resultado = _geocodificar_local("hamburgueria", lat_usuario, lon_usuario)

        self.assertIn("Esquina", resultado["nome"])

