/* Exemplos para a futura integração com o frontend. */

const API = 'http://127.0.0.1:5000/api';

async function fazerLogin(username, senha) {
  const resposta = await fetch(`${API}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, senha })
  });

  const dados = await resposta.json();

  if (!resposta.ok) {
    throw new Error(dados.erro || 'Erro no login');
  }

  localStorage.setItem('token', dados.access_token);
  localStorage.setItem('usuario', JSON.stringify(dados.usuario));
  return dados;
}

async function listarAcolhidos() {
  const token = localStorage.getItem('token');

  const resposta = await fetch(`${API}/acolhidos`, {
    headers: { Authorization: `Bearer ${token}` }
  });

  if (!resposta.ok) {
    throw new Error('Não foi possível carregar os acolhidos');
  }

  return await resposta.json();
}

async function cadastrarAcolhido(novoAcolhido) {
  const token = localStorage.getItem('token');

  const resposta = await fetch(`${API}/acolhidos`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(novoAcolhido)
  });

  const dados = await resposta.json();
  if (!resposta.ok) throw new Error(dados.erro);
  return dados;
}
