document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector(".tabs-root");
  const urlApiAdd = root.dataset.apiAdd;
  const urlBaseCarregador = root.dataset.urlCarregadorBase; // ex: /painel/carregador/

  const tabBtns = document.querySelectorAll(".tab-btn");
  const panels = { qrcode: document.getElementById("panel-qrcode"), token: document.getElementById("panel-token") };

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      Object.entries(panels).forEach(([key, el]) => {
        el.classList.toggle("hidden", key !== btn.dataset.tab);
      });
    });
  });

  async function enviarCarregador(metodo, valor, feedbackEl) {
    feedbackEl.textContent = "Adicionando...";
    feedbackEl.classList.remove("ok");
    try {
      const resp = await apiFetch(urlApiAdd, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ metodo, valor }),
      });
      const data = await resp.json();
      if (!resp.ok) {
        feedbackEl.textContent = data.erro || "Não foi possível adicionar o carregador.";
        return;
      }
      feedbackEl.textContent = "Carregador adicionado!";
      feedbackEl.classList.add("ok");
      window.location.href = urlBaseCarregador + data.carregador.id + "/";
    } catch (e) {
      feedbackEl.textContent = "Erro de conexão. Tente novamente.";
    }
  }

  // --- Token manual ---
  const tokenForm = document.getElementById("token-form");
  const tokenFeedback = document.getElementById("token-feedback");
  tokenForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const valor = document.getElementById("token-input").value.trim();
    if (!valor) {
      tokenFeedback.textContent = "Digite o token do carregador.";
      return;
    }
    enviarCarregador("token", valor, tokenFeedback);
  });

  // --- "Usar este carregador" clicado direto no popup do mapa --------------
  // Chega aqui como /painel/adicionar/?usar=TOKEN — já preenche o token e
  // envia sozinho, sem o usuário precisar digitar nada.
  const tokenParaUsar = new URLSearchParams(window.location.search).get("usar");
  if (tokenParaUsar) {
    tabBtns.forEach((b) => b.classList.remove("active"));
    document.querySelector('.tab-btn[data-tab="token"]').classList.add("active");
    Object.entries(panels).forEach(([key, el]) => el.classList.toggle("hidden", key !== "token"));

    document.getElementById("token-input").value = tokenParaUsar.toUpperCase();
    enviarCarregador("token", tokenParaUsar.toUpperCase(), tokenFeedback);
  }

  // --- QR Code ---
  const qrFeedback = document.getElementById("qr-feedback");
  if (tokenParaUsar) {
    // Já veio com o token pronto pra usar — não precisa abrir a câmera.
  } else if (window.Html5Qrcode) {
    const qr = new Html5Qrcode("qr-reader");
    let lido = false;
    Html5Qrcode.getCameras()
      .then((cameras) => {
        if (!cameras || !cameras.length) {
          qrFeedback.textContent = "Nenhuma câmera encontrada. Use a opção de token.";
          return;
        }
        qr.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: 220 },
          (decodedText) => {
            if (lido) return;
            lido = true;
            qr.stop().catch(() => {});
            enviarCarregador("qrcode", decodedText, qrFeedback);
          },
          () => {}
        ).catch(() => {
          qrFeedback.textContent = "Não foi possível acessar a câmera. Use a opção de token.";
        });
      })
      .catch(() => {
        qrFeedback.textContent = "Câmera indisponível neste dispositivo. Use a opção de token.";
      });
  } else {
    qrFeedback.textContent = "Leitor de QR Code não carregou. Use a opção de token.";
  }
});
