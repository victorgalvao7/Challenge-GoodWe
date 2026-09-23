document.addEventListener("DOMContentLoaded", () => {
  const painel = document.querySelector(".charger-detail");
  if (!painel) return;
  const urlIniciar = painel.dataset.apiIniciar;
  const urlFinalizar = painel.dataset.apiFinalizar;
  const urlStatus = painel.dataset.apiStatus;
  const urlReutilizar = painel.dataset.apiReutilizar;
  const urlDetalhe = painel.dataset.urlDetalhe;
  const urlPagamento = painel.dataset.urlPagamento;

  const btnIniciar = document.getElementById("btn-iniciar");
  if (btnIniciar) {
    btnIniciar.addEventListener("click", async () => {
      btnIniciar.disabled = true;
      btnIniciar.textContent = "Iniciando...";
      await apiFetch(urlIniciar, { method: "POST" });
      window.location.reload();
    });
  }

  const btnFinalizar = document.getElementById("btn-finalizar");
  if (btnFinalizar) {
    btnFinalizar.addEventListener("click", async () => {
      btnFinalizar.disabled = true;
      btnFinalizar.textContent = "Finalizando...";
      const resp = await apiFetch(urlFinalizar, { method: "POST" });
      const data = await resp.json();
      if (resp.ok) {
        window.location.href = urlPagamento;
      } else {
        alert(data.erro || "Erro ao finalizar.");
        btnFinalizar.disabled = false;
        btnFinalizar.textContent = "Finalizar carregamento";
      }
    });
  }

  const btnReutilizar = document.getElementById("btn-reutilizar");
  if (btnReutilizar) {
    btnReutilizar.addEventListener("click", async () => {
      btnReutilizar.disabled = true;
      btnReutilizar.textContent = "Liberando...";
      try {
        const resp = await apiFetch(urlReutilizar, { method: "POST" });
        const data = await resp.json();
        if (resp.ok) {
          window.location.href = urlDetalhe;
        } else {
          alert(data.erro || "Não foi possível reutilizar este carregador.");
          btnReutilizar.disabled = false;
          btnReutilizar.textContent = "Usar este carregador de novo";
        }
      } catch (e) {
        alert("Erro de conexão. Tente novamente.");
        btnReutilizar.disabled = false;
        btnReutilizar.textContent = "Usar este carregador de novo";
      }
    });
  }

  if (painel.dataset.status === "carregando") {
    const ring = document.getElementById("ring-progress");
    const circunferencia = 553;
    const pctEl = document.getElementById("pct-bateria");
    const tempoEl = document.getElementById("tempo-decorrido");
    const energiaEl = document.getElementById("energia-kwh");
    const custoEl = document.getElementById("custo-total");
    const blocoExcedente = document.getElementById("bloco-excedente");
    const tempoExcedenteEl = document.getElementById("tempo-excedente");

    async function atualizar() {
      try {
        const resp = await apiFetch(urlStatus);
        const data = await resp.json();
        if (!resp.ok) return;
        const c = data.carregador;

        const pct = c.percentual_bateria;
        ring.style.strokeDashoffset = circunferencia * (1 - pct / 100);
        pctEl.textContent = pct.toFixed(0) + "%";
        tempoEl.textContent = formatarTempo(c.tempo_decorrido_s);
        energiaEl.textContent = c.energia_kwh.toFixed(3) + " kWh";
        custoEl.textContent = formatarReais(c.custo_total_parcial);

        if (c.tempo_excedente_s > 0) {
          blocoExcedente.classList.remove("hidden");
          tempoExcedenteEl.textContent = formatarTempo(c.tempo_excedente_s);
        }
      } catch (e) {
        // silenciosamente tenta de novo no próximo ciclo
      }
    }

    atualizar();
    setInterval(atualizar, 1000);
  }
});
