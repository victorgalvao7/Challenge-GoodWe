document.addEventListener("DOMContentLoaded", () => {
  const painel = document.querySelector(".payment-methods");
  if (!painel) return;
  const urlPagar = painel.dataset.apiPagar;
  const urlSucesso = painel.dataset.urlSucesso;
  const botoesMetodo = document.querySelectorAll(".method-btn");
  const btnPagar = document.getElementById("btn-pagar");
  let metodoSelecionado = null;

  botoesMetodo.forEach((btn) => {
    btn.addEventListener("click", () => {
      botoesMetodo.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      metodoSelecionado = btn.dataset.metodo;
      btnPagar.disabled = false;
    });
  });

  btnPagar.addEventListener("click", async () => {
    if (!metodoSelecionado) return;
    btnPagar.disabled = true;
    btnPagar.textContent = "Processando...";
    const resp = await apiFetch(urlPagar, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ metodo: metodoSelecionado }),
    });
    if (resp.ok) {
      window.location.href = urlSucesso;
    } else {
      const data = await resp.json();
      alert(data.erro || "Erro ao processar pagamento.");
      btnPagar.disabled = false;
      btnPagar.textContent = "Pagar";
    }
  });
});
