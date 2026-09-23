/**
 * Mapa de carregadores próximos (painel do usuário).
 *
 * Usa Leaflet + tiles do OpenStreetMap — gratuito, sem chave de API.
 *
 * - Centraliza no local do usuário e acompanha em tempo real (watchPosition).
 * - Busca os carregadores com localização cadastrada em
 *   /painel/api/chargers/proximos e desenha um marcador para cada um.
 * - Carregadores no MESMO local (ex.: os 3 carregadores de um McDonald's)
 *   são agrupados num único marcador "balão", que mostra o total e, ao
 *   clicar, a lista individual de cada um (disponível / em uso).
 * - Atualiza a lista de carregadores periodicamente (30s), sem precisar
 *   recarregar a página, para refletir o que o administrador for cadastrando.
 * - Expõe window.WECHARGE_MOSTRAR_ROTA(carregador) para o Wechat (IoI Chat)
 *   destacar no mapa e traçar a rota até o carregador que ele encontrou.
 *
 * Os pontos são cadastrados pelo dono no painel do operador.
 */

const CENTRO_PADRAO = [-23.5505, -46.6333]; // São Paulo, usado se a geolocalização falhar

// Carregadores a menos de ~11 metros um do outro (mesma casa decimal em 4
// dígitos) são tratados como "o mesmo local" e agrupados num só marcador.
const CASAS_DECIMAIS_AGRUPAMENTO = 4;

let mapa;
let marcadorUsuario;
let marcadorBusca;
let marcadoresCarregadores = [];
let camadaRota = null;
let marcadorDestaque = null;
let urlAdicionarCarregador = "";
let ultimosCarregadores = [];

function mostrarAviso(mensagem) {
  const aviso = document.getElementById("mapa-aviso");
  if (!aviso) return;
  aviso.textContent = mensagem;
  aviso.classList.remove("hidden");
}

function corDoStatus(status) {
  if (status === "em_uso") return "#c0791a";
  return "#18a66a";
}

function escaparHtml(valor) {
  const el = document.createElement("div");
  el.textContent = valor == null ? "" : String(valor);
  return el.innerHTML;
}

// --- "Usar este carregador" direto do mapa -------------------------------
// Clicar no botão do popup já leva pra tela de adicionar carregador com o
// token preenchido e envia automaticamente — sem precisar digitar nada.
function linkUsarCarregador(codigo) {
  if (!urlAdicionarCarregador) return "";
  const url = `${urlAdicionarCarregador}?usar=${encodeURIComponent(codigo)}`;
  return `<a href="${url}" class="btn btn-primary btn-compacto btn-usar-carregador">Usar este carregador</a>`;
}

function conteudoPopupCarregador(c) {
  const podeUsar = c.status === "disponivel";
  return `
    <div class="mapa-infowindow">
      <strong>${escaparHtml(c.apelido)}</strong><br>
      ${c.endereco ? escaparHtml(c.endereco) + "<br>" : ""}
      <span>${escaparHtml(c.status_label)}</span><br>
      <span>Token: <code>${escaparHtml(c.identificador_fisico)}</code></span><br>
      <span>R$ ${Number(c.preco_kwh).toFixed(2).replace(".", ",")} / kWh</span>
      ${podeUsar ? `<div class="mapa-infowindow-acao">${linkUsarCarregador(c.identificador_fisico)}</div>` : ""}
    </div>
  `;
}

function conteudoPopupGrupo(grupo) {
  const total = grupo.length;
  const emUso = grupo.filter((c) => c.status === "em_uso").length;
  const disponiveis = total - emUso;
  const nomeLocal = grupo[0].apelido;
  const endereco = grupo[0].endereco;

  const linhas = grupo
    .map((c) => {
      const podeUsar = c.status === "disponivel";
      return `
        <li class="mapa-infowindow-item">
          <span>Token <code>${escaparHtml(c.identificador_fisico)}</code> — ${escaparHtml(c.status_label)}</span>
          ${podeUsar ? linkUsarCarregador(c.identificador_fisico) : ""}
        </li>
      `;
    })
    .join("");

  return `
    <div class="mapa-infowindow mapa-infowindow-grupo">
      <strong>${escaparHtml(nomeLocal)}</strong><br>
      ${endereco ? escaparHtml(endereco) + "<br>" : ""}
      <span>${total} carregadores neste local — ${disponiveis} disponível(is), ${emUso} em uso</span>
      <ul class="mapa-infowindow-lista">${linhas}</ul>
    </div>
  `;
}

function chaveDeLocal(c) {
  const lat = Number(c.latitude).toFixed(CASAS_DECIMAIS_AGRUPAMENTO);
  const lon = Number(c.longitude).toFixed(CASAS_DECIMAIS_AGRUPAMENTO);
  return `${lat}_${lon}`;
}

function agruparPorLocal(carregadores) {
  const grupos = new Map();
  carregadores.forEach((c) => {
    const chave = chaveDeLocal(c);
    if (!grupos.has(chave)) grupos.set(chave, []);
    grupos.get(chave).push(c);
  });
  return Array.from(grupos.values());
}

function iconeGrupo(grupo) {
  const temDisponivel = grupo.some((c) => c.status !== "em_uso");
  const cor = temDisponivel ? "#18a66a" : "#c0791a";
  return L.divIcon({
    className: "marcador-grupo-carregadores",
    html: `<span style="background:${cor}">${grupo.length}</span>`,
    iconSize: [30, 30],
  });
}

async function carregarCarregadoresProximos(container) {
  const url = container.dataset.apiProximos;
  try {
    const resp = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
    if (!resp.ok) throw new Error("Falha ao buscar carregadores próximos.");
    const data = await resp.json();

    marcadoresCarregadores.forEach((m) => mapa.removeLayer(m));
    marcadoresCarregadores = [];
    ultimosCarregadores = data.carregadores;

    agruparPorLocal(data.carregadores).forEach((grupo) => {
      let marcador;
      if (grupo.length === 1) {
        const c = grupo[0];
        marcador = L.circleMarker([c.latitude, c.longitude], {
          radius: 9,
          color: "#ffffff",
          weight: 2,
          fillColor: corDoStatus(c.status),
          fillOpacity: 1,
        }).addTo(mapa);
        marcador.bindPopup(conteudoPopupCarregador(c));
      } else {
        const [lat, lon] = [grupo[0].latitude, grupo[0].longitude];
        marcador = L.marker([lat, lon], { icon: iconeGrupo(grupo) }).addTo(mapa);
        marcador.bindPopup(conteudoPopupGrupo(grupo));
      }
      marcador._wechargeTokens = grupo.map((c) => c.identificador_fisico);
      marcadoresCarregadores.push(marcador);
    });
  } catch (erro) {
    console.error(erro);
  }
}

// --- Rota até o carregador (usado pelo Wechat) ----------------------------
// Traça a rota de carro entre a localização do usuário e o carregador que
// a IA encontrou, usando o OSRM (gratuito, sem chave). Também destaca o
// marcador do carregador e abre o popup dele.
async function tracarRotaAte(latDestino, lonDestino) {
  const local = window.WECHARGE_USER_LOCATION;
  if (!local) {
    mostrarAviso("Ative sua localização para o Wechat traçar a rota até o carregador.");
    return;
  }

  if (camadaRota) {
    mapa.removeLayer(camadaRota);
    camadaRota = null;
  }

  const url =
    `https://router.project-osrm.org/route/v1/driving/` +
    `${local.lon},${local.lat};${lonDestino},${latDestino}` +
    `?overview=full&geometries=geojson`;

  try {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error("Falha ao calcular rota.");
    const dados = await resp.json();
    const rota = dados.routes && dados.routes[0];
    if (!rota) throw new Error("Nenhuma rota encontrada.");

    const coordenadas = rota.geometry.coordinates.map(([lon, lat]) => [lat, lon]);
    camadaRota = L.polyline(coordenadas, { color: "#2f6fed", weight: 5, opacity: 0.85 }).addTo(mapa);
    mapa.fitBounds(camadaRota.getBounds(), { padding: [40, 40] });
  } catch (erro) {
    console.error(erro);
    // Sem a rota mesmo assim mostramos o carregador no mapa (abaixo).
    mapa.setView([latDestino, lonDestino], 15);
  }
}

function destacarCarregadorNoMapa(carregador) {
  if (marcadorDestaque) {
    mapa.removeLayer(marcadorDestaque);
    marcadorDestaque = null;
  }

  const iconeDestaque = L.divIcon({
    className: "marcador-destaque-wechat",
    html: "<span>📍</span>",
    iconSize: [34, 34],
  });

  marcadorDestaque = L.marker([carregador.latitude, carregador.longitude], {
    icon: iconeDestaque,
    zIndexOffset: 1000,
  }).addTo(mapa);

  const podeUsar = carregador.status !== "Em uso";
  marcadorDestaque.bindPopup(`
    <div class="mapa-infowindow">
      <strong>${escaparHtml(carregador.apelido)}</strong><br>
      ${carregador.endereco ? escaparHtml(carregador.endereco) + "<br>" : ""}
      <span>${escaparHtml(carregador.status)}</span><br>
      <span>Token: <code>${escaparHtml(carregador.identificador_fisico)}</code></span>
      ${podeUsar ? `<div class="mapa-infowindow-acao">${linkUsarCarregador(carregador.identificador_fisico)}</div>` : ""}
    </div>
  `).openPopup();
}

// Chamado pelo ioi_chat.js quando a IA acha um carregador — mostra o
// marcador em destaque e traça a rota até ele.
window.WECHARGE_MOSTRAR_ROTA = function (carregador) {
  if (!mapa || !carregador || carregador.latitude == null || carregador.longitude == null) return;
  destacarCarregadorNoMapa(carregador);
  tracarRotaAte(carregador.latitude, carregador.longitude);
};

function iniciarMapaProximos() {
  const container = document.getElementById("mapa-proximos");
  if (!container || container._leaflet_id) return; // já inicializado, evita duplicar o mapa
  urlAdicionarCarregador = container.dataset.urlAdicionar || "";

  mapa = L.map(container).setView(CENTRO_PADRAO, 13);

  L.tileLayer("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", {
    maxZoom: 20,
    subdomains: "abcd",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
  }).addTo(mapa);

  // Corrige o tamanho do mapa caso ele tenha sido calculado errado no
  // primeiro instante (ex.: se o CSS ainda não tinha aplicado a altura
  // do container quando o Leaflet foi inicializado).
  setTimeout(() => mapa.invalidateSize(), 200);
  window.addEventListener("resize", () => mapa.invalidateSize());

  carregarCarregadoresProximos(container);
  setInterval(() => carregarCarregadoresProximos(container), 30000);

  iniciarBuscaEndereco();

  if (!navigator.geolocation) {
    mostrarAviso("Seu navegador não suporta localização em tempo real. Mostrando um mapa de referência.");
    return;
  }

  const iconeUsuario = L.divIcon({
    className: "marcador-usuario",
    html: '<span></span>',
    iconSize: [18, 18],
  });

  const aoAtualizarPosicao = (posicao) => {
    const local = [posicao.coords.latitude, posicao.coords.longitude];

    if (!marcadorUsuario) {
      mapa.setView(local, 15);
      marcadorUsuario = L.marker(local, { icon: iconeUsuario, zIndexOffset: 999 })
        .addTo(mapa)
        .bindPopup("Você está aqui");
    } else {
      marcadorUsuario.setLatLng(local);
    }

    // Deixa a localização disponível globalmente para outros scripts
    // (ex.: o Wechat, que precisa saber onde o usuário está).
    window.WECHARGE_USER_LOCATION = { lat: local[0], lon: local[1] };
  };

  const aoFalharLocalizacao = () => {
    mostrarAviso("Não conseguimos acessar sua localização. Ative a permissão de localização no navegador para ver os carregadores mais perto de você.");
  };

  navigator.geolocation.getCurrentPosition(aoAtualizarPosicao, aoFalharLocalizacao, {
    enableHighAccuracy: true,
    timeout: 10000,
  });

  navigator.geolocation.watchPosition(aoAtualizarPosicao, aoFalharLocalizacao, {
    enableHighAccuracy: true,
    maximumAge: 5000,
  });
}

// Busca de endereço: digita um endereço e o mapa centraliza nele, com um
// marcador temporário, para facilitar navegar até outra região (ex.: ver
// carregadores perto de um endereço diferente de onde o usuário está).
function iniciarBuscaEndereco() {
  const buscaInput = document.getElementById("busca-endereco-input");
  const buscaBotao = document.getElementById("busca-endereco-botao");
  if (!buscaInput || !buscaBotao) return;

  async function geocodificar(consulta) {
    const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&addressdetails=0&q=${encodeURIComponent(consulta)}`;
    const resp = await fetch(url, { headers: { "Accept-Language": "pt-BR" } });
    if (!resp.ok) throw new Error("Falha ao buscar endereço.");
    return resp.json();
  }

  async function buscarEndereco() {
    const consulta = buscaInput.value.trim();
    if (!consulta) return;

    const textoOriginal = buscaBotao.textContent;
    buscaBotao.disabled = true;
    buscaBotao.textContent = "Buscando...";

    try {
      let resultados = await geocodificar(consulta);

      // Se não achar nada, tenta de novo acrescentando "São Paulo, Brasil"
      // como contexto — ajuda com endereços digitados sem cidade/UF.
      const jaTemContexto = /s(ã|a)o paulo|brasil|brazil/i.test(consulta);
      if (!resultados.length && !jaTemContexto) {
        resultados = await geocodificar(`${consulta}, São Paulo, Brasil`);
      }

      if (!resultados.length) {
        buscaBotao.textContent = "Endereço não encontrado";
        setTimeout(() => { buscaBotao.textContent = textoOriginal; }, 2200);
        return;
      }

      const { lat, lon, display_name } = resultados[0];
      const local = [Number(lat), Number(lon)];

      if (marcadorBusca) mapa.removeLayer(marcadorBusca);
      marcadorBusca = L.marker(local).addTo(mapa).bindPopup(escaparHtml(display_name));
      marcadorBusca.openPopup();
      mapa.setView(local, 15);
    } catch (erro) {
      console.error(erro);
      buscaBotao.textContent = "Erro na busca";
      setTimeout(() => { buscaBotao.textContent = textoOriginal; }, 2200);
    } finally {
      buscaBotao.disabled = false;
      if (buscaBotao.textContent === "Buscando...") buscaBotao.textContent = textoOriginal;
    }
  }

  buscaBotao.addEventListener("click", buscarEndereco);
  buscaInput.addEventListener("keydown", (evento) => {
    if (evento.key === "Enter") {
      evento.preventDefault();
      buscarEndereco();
    }
  });
}

document.addEventListener("DOMContentLoaded", iniciarMapaProximos);
