document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("mapa-cadastro");
  const latitudeInput = document.getElementById("id_latitude");
  const longitudeInput = document.getElementById("id_longitude");
  const enderecoInput = document.getElementById("id_endereco");
  const botaoLocalizacao = document.getElementById("usar-localizacao");
  const buscaBotao = document.getElementById("busca-endereco-botao");

  if (!container || !latitudeInput || !longitudeInput || !window.L) return;

  const centroPadrao = [-23.5505, -46.6333];
  const latitudeInicial = Number.parseFloat(latitudeInput.value);
  const longitudeInicial = Number.parseFloat(longitudeInput.value);
  const temCoordenadas = Number.isFinite(latitudeInicial) && Number.isFinite(longitudeInicial);
  const centroInicial = temCoordenadas
    ? [latitudeInicial, longitudeInicial]
    : centroPadrao;

  const mapa = L.map(container).setView(centroInicial, temCoordenadas ? 16 : 12);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    maxZoom: 20,
    subdomains: "abcd",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  }).addTo(mapa);

  let marcador = null;

  function definirLocal(latitude, longitude, centralizar = false) {
    latitudeInput.value = Number(latitude).toFixed(6);
    longitudeInput.value = Number(longitude).toFixed(6);

    if (marcador) {
      marcador.setLatLng([latitude, longitude]);
    } else {
      marcador = L.marker([latitude, longitude], { draggable: true }).addTo(mapa);
      marcador.on("dragend", () => {
        const posicao = marcador.getLatLng();
        definirLocal(posicao.lat, posicao.lng);
      });
    }

    if (centralizar) mapa.setView([latitude, longitude], 17);
  }

  if (temCoordenadas) definirLocal(latitudeInicial, longitudeInicial);

  mapa.on("click", (evento) => {
    definirLocal(evento.latlng.lat, evento.latlng.lng);
  });

  botaoLocalizacao?.addEventListener("click", () => {
    if (!navigator.geolocation) {
      botaoLocalizacao.textContent = "Localização não suportada pelo navegador";
      return;
    }

    botaoLocalizacao.disabled = true;
    botaoLocalizacao.textContent = "Buscando localização...";
    navigator.geolocation.getCurrentPosition(
      (posicao) => {
        definirLocal(posicao.coords.latitude, posicao.coords.longitude, true);
        botaoLocalizacao.disabled = false;
        botaoLocalizacao.textContent = "Usar minha localização atual";
      },
      () => {
        botaoLocalizacao.disabled = false;
        botaoLocalizacao.textContent = "Não foi possível obter a localização";
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });

  // Busca de endereço: agora usa o próprio campo "Endereço" do formulário.
  // Digitar ali e clicar em "Localizar no mapa" (ou apertar Enter) já
  // geocodifica e preenche latitude/longitude, sem precisar de um campo
  // separado (que antes causava a confusão de preencher o campo errado).
  async function geocodificar(consulta) {
    const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&addressdetails=0&q=${encodeURIComponent(consulta)}`;
    const resp = await fetch(url, { headers: { "Accept-Language": "pt-BR" } });
    if (!resp.ok) throw new Error("Falha ao buscar endereço.");
    return resp.json();
  }

  async function buscarEndereco() {
    if (!enderecoInput || !buscaBotao) return;
    const consulta = enderecoInput.value.trim();
    if (!consulta) return;

    const textoOriginal = buscaBotao.textContent;
    buscaBotao.disabled = true;
    buscaBotao.textContent = "Buscando...";

    try {
      let resultados = await geocodificar(consulta);

      // Se não achar nada, tenta de novo acrescentando "São Paulo, Brasil"
      // como contexto — ajuda muito com endereços digitados sem cidade/UF
      // ou de forma abreviada (ex.: "n87" em vez de "nº 87").
      const jaTemContexto = /s(ã|a)o paulo|brasil|brazil/i.test(consulta);
      if (!resultados.length && !jaTemContexto) {
        resultados = await geocodificar(`${consulta}, São Paulo, Brasil`);
      }

      if (!resultados.length) {
        buscaBotao.textContent = "Endereço não encontrado";
        setTimeout(() => { buscaBotao.textContent = textoOriginal; }, 2200);
        return;
      }

      const { lat, lon } = resultados[0];
      definirLocal(Number(lat), Number(lon), true);
    } catch (erro) {
      console.error(erro);
      buscaBotao.textContent = "Erro na busca";
      setTimeout(() => { buscaBotao.textContent = textoOriginal; }, 2200);
    } finally {
      buscaBotao.disabled = false;
      if (buscaBotao.textContent === "Buscando...") buscaBotao.textContent = textoOriginal;
    }
  }

  buscaBotao?.addEventListener("click", buscarEndereco);
  enderecoInput?.addEventListener("keydown", (evento) => {
    if (evento.key === "Enter") {
      evento.preventDefault();
      buscarEndereco();
    }
  });

  setTimeout(() => mapa.invalidateSize(), 150);
});
