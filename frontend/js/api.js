/* =====================================================
   api.js — comunicação simples com a API Flask
   ===================================================== */

const API_URL = 'http://127.0.0.1:5000';

function getToken() {
  return localStorage.getItem('access_token');
}

function getUsuarioSalvo() {
  const texto = localStorage.getItem('usuario');
  return texto ? JSON.parse(texto) : null;
}

function salvarSessao(token, usuario) {
  localStorage.setItem('access_token', token);
  localStorage.setItem('usuario', JSON.stringify(usuario));
}

function limparSessao() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('usuario');
}

async function apiFetch(rota, opcoes = {}) {
  const headers = opcoes.headers || {};
  const token = getToken();

  if (token) {
    headers.Authorization = 'Bearer ' + token;
  }

  if (opcoes.body && !(opcoes.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const resposta = await fetch(API_URL + rota, {
    ...opcoes,
    headers: headers
  });

  if (resposta.status === 401) {
    limparSessao();
    if (!window.location.pathname.endsWith('login.html')) {
      window.location.href = 'login.html';
    }
  }

  const tipo = resposta.headers.get('content-type') || '';
  const dados = tipo.includes('application/json') ? await resposta.json() : null;

  if (!resposta.ok) {
    throw new Error(dados?.erro || 'Não foi possível concluir a operação.');
  }

  return dados;
}

function escaparHTML(valor) {
  return String(valor ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function formatarData(valor) {
  if (!valor) return '—';
  const data = new Date(valor.length === 10 ? valor + 'T00:00:00' : valor);
  if (Number.isNaN(data.getTime())) return valor;
  return data.toLocaleDateString('pt-BR');
}

function formatarDataHora(valor) {
  if (!valor) return '—';
  const data = new Date(valor);
  if (Number.isNaN(data.getTime())) return valor;
  return data.toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

function formatarDinheiro(valor) {
  return Number(valor || 0).toLocaleString('pt-BR', {
    style: 'currency', currency: 'BRL'
  });
}

function mostrarAlerta(id, mensagem, tipo = 'success') {
  const elemento = document.getElementById(id);
  if (!elemento) return;
  elemento.className = 'alert alert-' + tipo;
  elemento.textContent = mensagem;
  elemento.classList.remove('d-none');
}

function esconderAlerta(id) {
  document.getElementById(id)?.classList.add('d-none');
}

function mensagemVazia(texto, colunas = 1) {
  return '<tr><td colspan="' + colunas + '" class="text-center text-muted py-4">' +
    escaparHTML(texto) + '</td></tr>';
}
