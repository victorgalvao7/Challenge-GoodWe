// Funções utilitárias compartilhadas entre páginas
function formatarTempo(totalSegundos) {
  const h = Math.floor(totalSegundos / 3600).toString().padStart(2, "0");
  const m = Math.floor((totalSegundos % 3600) / 60).toString().padStart(2, "0");
  const s = Math.floor(totalSegundos % 60).toString().padStart(2, "0");
  return `${h}:${m}:${s}`;
}

function formatarReais(valor) {
  return "R$ " + valor.toFixed(2).replace(".", ",");
}

// O Django exige o token CSRF em toda requisição POST/PUT/DELETE feita por
// JavaScript (fetch). Ele fica salvo automaticamente num cookie chamado
// "csrftoken" assim que a página carrega (porque o <meta> abaixo, no
// base_app.html, tem {% csrf_token %} numa tag <form> escondida).
function getCsrfToken() {
  const nome = "csrftoken";
  const cookies = document.cookie ? document.cookie.split("; ") : [];
  for (const cookie of cookies) {
    const [chave, valor] = cookie.split("=");
    if (chave === nome) return decodeURIComponent(valor);
  }
  return "";
}

// Wrapper em volta do fetch() padrão que já inclui o cabeçalho CSRF em
// requisições que alteram dados (POST). Use isso em vez de fetch() puro
// para chamar a API do painel.
function apiFetch(url, options = {}) {
  const opts = { ...options };
  opts.headers = { ...(opts.headers || {}), "X-CSRFToken": getCsrfToken() };
  return fetch(url, opts);
}
