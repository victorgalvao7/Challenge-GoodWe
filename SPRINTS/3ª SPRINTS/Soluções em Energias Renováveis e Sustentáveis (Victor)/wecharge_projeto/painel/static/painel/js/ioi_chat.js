/**
 * Wechat — botão flutuante sobre o mapa que abre uma conversa com a
 * IA (WeCharge + OpenAI). Usa a localização do usuário exposta pelo
 * mapa.js em window.WECHARGE_USER_LOCATION.
 *
 * Quando a IA acha um carregador (ex.: "qual o mais próximo do
 * McDonald's?"), o mapa.js mostra ele automaticamente no mapa com a rota
 * até lá (window.WECHARGE_MOSTRAR_ROTA). E quando a pergunta foi feita por
 * voz, a resposta também é falada de volta (Web Speech API), pra dar pra
 * usar o Wechat sem tirar os olhos da estrada.
 */

document.addEventListener("DOMContentLoaded", () => {
  const btnAbrir = document.getElementById("btn-ioi-chat");
  const painel = document.getElementById("ioi-chat-painel");
  const btnFechar = document.getElementById("btn-fechar-ioi-chat");
  const form = document.getElementById("ioi-chat-form");
  const input = document.getElementById("ioi-chat-input");
  const mensagensEl = document.getElementById("ioi-chat-mensagens");
  const btnMic = document.getElementById("btn-ioi-chat-mic");
  const campoNormal = document.getElementById("ioi-chat-campo-normal");
  const faixaOuvindo = document.getElementById("ioi-chat-ouvindo");

  if (!btnAbrir || !painel || !form) return;

  // Marca se a última pergunta foi feita por voz, pra decidir se a
  // resposta da IA deve ser falada de volta ou só mostrada em texto.
  let ultimaMensagemFoiPorVoz = false;

  // --- Fala a resposta da IA em voz alta (Web Speech API) ------------------
  const sintetizador = window.speechSynthesis;

  function falarResposta(texto) {
    if (!sintetizador || !texto) return;
    sintetizador.cancel(); // corta qualquer fala anterior ainda em andamento
    const fala = new SpeechSynthesisUtterance(texto);
    fala.lang = "pt-BR";
    fala.rate = 1;
    sintetizador.speak(fala);
  }

  // --- Entrada por voz (pra quem tá no carro e não pode digitar) ---
  // Usa a Web Speech API do navegador (Chrome/Edge/Safari recentes).
  const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (btnMic) {
    if (!SpeechRecognitionAPI) {
      // Navegador não suporta: esconde o botão em vez de deixar quebrado.
      btnMic.style.display = "none";
    } else {
      const reconhecimento = new SpeechRecognitionAPI();
      reconhecimento.lang = "pt-BR";
      reconhecimento.continuous = false;
      reconhecimento.interimResults = false;
      reconhecimento.maxAlternatives = 1;

      let ouvindo = false;

      reconhecimento.addEventListener("start", () => {
        ouvindo = true;
        btnMic.classList.add("ouvindo");
        btnMic.setAttribute("aria-label", "Ouvindo... toque para cancelar");
        // Troca o campo de digitar por uma faixa bem visível de "Ouvindo...",
        // com bolinha vermelha piscando e ondinha de áudio — pra ficar
        // claro que o microfone está captando a fala (igual gravação de
        // áudio do WhatsApp).
        if (campoNormal && faixaOuvindo) {
          campoNormal.classList.add("hidden");
          faixaOuvindo.classList.remove("hidden");
        }
      });

      reconhecimento.addEventListener("end", () => {
        ouvindo = false;
        btnMic.classList.remove("ouvindo");
        btnMic.setAttribute("aria-label", "Falar com o Wechat");
        if (campoNormal && faixaOuvindo) {
          faixaOuvindo.classList.add("hidden");
          campoNormal.classList.remove("hidden");
        }
      });

      reconhecimento.addEventListener("result", (evento) => {
        const texto = evento.results[0][0].transcript.trim();
        if (!texto) return;
        input.value = texto;
        ultimaMensagemFoiPorVoz = true;
        // Manda direto — quem tá dirigindo não tem tempo de revisar e apertar enviar.
        form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event("submit", { cancelable: true }));
      });

      reconhecimento.addEventListener("error", (evento) => {
        if (evento.error === "not-allowed" || evento.error === "service-not-allowed") {
          adicionarBolha("Não consegui acessar o microfone. Verifique a permissão do navegador.", "ia");
        }
      });

      btnMic.addEventListener("click", () => {
        if (painel.classList.contains("hidden")) {
          painel.classList.remove("hidden");
        }
        if (ouvindo) {
          reconhecimento.stop();
        } else {
          reconhecimento.start();
        }
      });
    }
  }

  const urlChat = painel.dataset.apiChat;

  btnAbrir.addEventListener("click", () => {
    painel.classList.toggle("hidden");
    if (!painel.classList.contains("hidden")) input.focus();
  });

  btnFechar.addEventListener("click", () => {
    painel.classList.add("hidden");
    if (sintetizador) sintetizador.cancel();
  });

  function adicionarBolha(texto, autor) {
    const bolha = document.createElement("div");
    bolha.className = `ioi-chat-bolha ioi-chat-bolha-${autor}`;
    bolha.textContent = texto;
    mensagensEl.appendChild(bolha);
    mensagensEl.scrollTop = mensagensEl.scrollHeight;
    return bolha;
  }

  // Se digitado normalmente, não foi por voz — só o microfone marca como voz.
  input.addEventListener("input", () => {
    ultimaMensagemFoiPorVoz = false;
  });

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const mensagem = input.value.trim();
    if (!mensagem) return;

    const foiPorVoz = ultimaMensagemFoiPorVoz;
    ultimaMensagemFoiPorVoz = false;

    adicionarBolha(mensagem, "usuario");
    input.value = "";
    input.disabled = true;
    const bolhaCarregando = adicionarBolha("Pensando...", "ia");

    const local = window.WECHARGE_USER_LOCATION || {};

    try {
      const resp = await apiFetch(urlChat, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mensagem: mensagem,
          latitude: local.lat ?? null,
          longitude: local.lon ?? null,
        }),
      });
      const dados = await resp.json();

      if (resp.ok) {
        bolhaCarregando.textContent = dados.resposta;

        // Achou um carregador: mostra automaticamente no mapa + traça a
        // rota até ele (mapa.js cuida do desenho de verdade).
        if (dados.destaque && dados.destaque.carregador && window.WECHARGE_MOSTRAR_ROTA) {
          window.WECHARGE_MOSTRAR_ROTA(dados.destaque.carregador);
        }

        // Se a pergunta foi feita por voz, fala a resposta de volta —
        // hands-free de verdade pra quem tá dirigindo.
        if (foiPorVoz) {
          falarResposta(dados.resposta);
        }
      } else {
        bolhaCarregando.textContent = dados.erro || "Não consegui responder agora.";
      }
    } catch (erro) {
      bolhaCarregando.textContent = "Erro de conexão. Tente de novo.";
    } finally {
      input.disabled = false;
      input.focus();
    }
  });
});
