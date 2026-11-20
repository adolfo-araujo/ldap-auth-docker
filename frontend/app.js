// O Nginx encaminha /api para o container do backend, então usamos caminho relativo.
const API = "/api";
const $ = (id) => document.getElementById(id);
let token = sessionStorage.getItem("token");

async function chamar(rota, opcoes = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(API + rota, { ...opcoes, headers });
  const dados = await resp.json().catch(() => ({}));
  return { ok: resp.ok, status: resp.status, dados };
}

function mostrarLogin() {
  $("tela-login").hidden = false;
  $("tela-painel").hidden = true;
}

function mostrarPainel(u) {
  $("p-nome").textContent = u.nome;
  $("p-uid").textContent = u.uid;
  $("p-email").textContent = u.email;
  $("p-grupos").textContent = u.grupos.join(", ") || "(nenhum)";
  $("saida-admin").hidden = true;
  $("tela-login").hidden = true;
  $("tela-painel").hidden = false;
}

$("form-login").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("msg-login").textContent = "";
  const r = await chamar("/login", {
    method: "POST",
    body: JSON.stringify({ username: $("username").value, password: $("password").value }),
  });
  if (!r.ok) {
    $("msg-login").textContent = r.dados.erro || "Falha no login";
    return;
  }
  token = r.dados.token;
  sessionStorage.setItem("token", token);
  $("password").value = "";
  mostrarPainel(r.dados.usuario);
});

$("btn-admin").addEventListener("click", async () => {
  const r = await chamar("/admin");
  const saida = $("saida-admin");
  saida.hidden = false;
  saida.className = r.ok ? "" : "erro";
  saida.textContent = `HTTP ${r.status}\n` + JSON.stringify(r.dados, null, 2);
});

$("btn-sair").addEventListener("click", () => {
  token = null;
  sessionStorage.removeItem("token");
  mostrarLogin();
});

// Ao recarregar a página, valida o token salvo
(async () => {
  if (!token) return mostrarLogin();
  const r = await chamar("/me");
  if (r.ok) mostrarPainel(r.dados.usuario);
  else { sessionStorage.removeItem("token"); token = null; mostrarLogin(); }
})();
