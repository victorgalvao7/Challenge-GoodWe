/**
 * Chat de Suporte — pergunta e resposta na própria página de Suporte.
 * Independente do Wechat (que é só da área logada do usuário).
 */

function suporteGetCsrfToken() {
  const nome = "csrftoken";
  const cookies = document.cookie ? document.cookie.split("; ") : [];
  for (const cookie of cookies) {
    const [chave, valor] = cookie.split("=");
    if (chave === nome) return decodeURIComponent(valor);
  }
  return "";
}

document.addEventListener("DOMContentLoaded", () => {
  const painel = document.getElementById("suporte-chat-painel");
  const form = document.getElementById("suporte-chat-form");
  const input = document.getElementById("suporte-chat-input");
  const mensagensEl = document.getElementById("suporte-chat-mensagens");

  if (!painel || !form || !input || !mensagensEl) return;

  const urlChat = painel.dataset.apiChat;

  function adicionarBolha(texto, autor) {
    const bolha = document.createElement("div");
    bolha.className = `suporte-chat-bolha suporte-chat-bolha-${autor}`;
    bolha.textContent = texto;
    mensagensEl.appendChild(bolha);
    mensagensEl.scrollTop = mensagensEl.scrollHeight;
    return bolha;
  }

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const mensagem = input.value.trim();
    if (!mensagem) return;

    adicionarBolha(mensagem, "usuario");
    input.value = "";
    input.disabled = true;
    const bolhaCarregando = adicionarBolha("Pensando...", "ia");

    try {
      const resp = await fetch(urlChat, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": suporteGetCsrfToken(),
        },
        body: JSON.stringify({ mensagem: mensagem }),
      });
      const dados = await resp.json();

      if (resp.ok) {
        bolhaCarregando.textContent = dados.resposta;
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
