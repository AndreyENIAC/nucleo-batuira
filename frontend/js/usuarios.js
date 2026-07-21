let usuariosCadastrados = [];
let perfisDisponiveis = [];

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('btn-novo-usuario').addEventListener('click', abrirNovoUsuario);
  document.getElementById('btn-cancelar-usuario').addEventListener('click', fecharFormularioUsuario);
  document.getElementById('form-usuario').addEventListener('submit', salvarUsuario);
  document.getElementById('corpo-usuarios').addEventListener('click', tratarAcaoUsuario);
  document.getElementById('lista-recuperacoes').addEventListener('click', tratarRecuperacao);
  carregarUsuarios();
});

async function carregarUsuarios() {
  try {
    const resultados = await Promise.all([
      apiFetch('/api/perfis'),
      apiFetch('/api/usuarios'),
      apiFetch('/api/recuperacoes-senha')
    ]);
    perfisDisponiveis = resultados[0];
    usuariosCadastrados = resultados[1];
    preencherPerfis();
    renderizarUsuarios();
    renderizarRecuperacoes(resultados[2]);
  } catch (erro) {
    mostrarAlerta('mensagem-usuarios', erro.message, 'danger');
  }
}

function preencherPerfis() {
  const select = document.getElementById('usuario-perfil-form');
  const valorAtual = select.value;
  select.innerHTML = '<option value="">Selecione</option>' + perfisDisponiveis.map(function (perfil) {
    return '<option value="' + escaparHTML(perfil.codigo) + '">' + escaparHTML(perfil.nome) + '</option>';
  }).join('');
  if (valorAtual) select.value = valorAtual;
}

function renderizarUsuarios() {
  const corpo = document.getElementById('corpo-usuarios');
  document.getElementById('total-usuarios-cadastrados').textContent = usuariosCadastrados.length + ' usuário(s)';

  if (!usuariosCadastrados.length) {
    corpo.innerHTML = mensagemVazia('Nenhum usuário cadastrado.', 6);
    return;
  }

  corpo.innerHTML = usuariosCadastrados.map(function (usuario) {
    const situacao = usuario.ativo
      ? '<span class="badge bg-success">Ativo</span>'
      : '<span class="badge bg-secondary">Inativo</span>';
    const primeiroAcesso = usuario.primeiro_acesso
      ? '<span class="badge bg-warning text-dark">Pendente</span>'
      : '<span class="badge bg-light text-dark border">Concluído</span>';
    const recuperacao = usuario.recuperacao_pendente
      ? '<span class="badge bg-danger ms-1">Senha solicitada</span>'
      : '';

    return '<tr>' +
      '<td><strong>' + escaparHTML(usuario.nome) + '</strong><div class="small text-muted">' + escaparHTML(usuario.email || 'Sem e-mail') + recuperacao + '</div></td>' +
      '<td>' + escaparHTML(usuario.username) + '</td>' +
      '<td>' + escaparHTML(usuario.nome_perfil) + '</td>' +
      '<td>' + situacao + '</td>' +
      '<td>' + primeiroAcesso + '</td>' +
      '<td class="text-nowrap">' +
        '<button type="button" class="btn btn-outline-primary btn-sm me-1" data-acao="editar" data-id="' + usuario.id + '">Editar</button>' +
        '<button type="button" class="btn btn-outline-warning btn-sm me-1" data-acao="senha" data-id="' + usuario.id + '">Senha</button>' +
        '<button type="button" class="btn btn-outline-' + (usuario.ativo ? 'danger' : 'success') + ' btn-sm" data-acao="status" data-id="' + usuario.id + '" data-ativo="' + (usuario.ativo ? '0' : '1') + '">' + (usuario.ativo ? 'Inativar' : 'Reativar') + '</button>' +
      '</td></tr>';
  }).join('');
}

function renderizarRecuperacoes(lista) {
  const container = document.getElementById('lista-recuperacoes');
  document.getElementById('total-recuperacoes').textContent = lista.length;

  if (!lista.length) {
    container.innerHTML = '<p class="text-muted mb-0">Nenhuma solicitação pendente.</p>';
    return;
  }

  container.innerHTML = lista.map(function (item) {
    return '<div class="documento-item">' +
      '<div><strong>' + escaparHTML(item.nome) + '</strong>' +
      '<div class="small text-muted">' + escaparHTML(item.username) + ' · ' + formatarDataHora(item.solicitado_em) + '</div></div>' +
      '<button type="button" class="btn btn-warning btn-sm" data-recuperacao-id="' + item.id + '">Gerar senha temporária</button>' +
      '</div>';
  }).join('');
}

function abrirNovoUsuario() {
  document.getElementById('form-usuario').reset();
  document.getElementById('usuario-id').value = '';
  document.getElementById('titulo-form-usuario').textContent = 'Cadastrar usuário';
  document.getElementById('campo-senha-temporaria').classList.remove('d-none');
  document.getElementById('painel-form-usuario').classList.remove('d-none');
  document.getElementById('senha-temporaria-box').classList.add('d-none');
  preencherPerfis();
  document.getElementById('usuario-nome-form').focus();
}

function abrirEdicaoUsuario(id) {
  const usuario = usuariosCadastrados.find(item => item.id === id);
  if (!usuario) return;

  document.getElementById('usuario-id').value = usuario.id;
  document.getElementById('usuario-nome-form').value = usuario.nome || '';
  document.getElementById('usuario-login-form').value = usuario.username || '';
  document.getElementById('usuario-email-form').value = usuario.email || '';
  document.getElementById('usuario-telefone-form').value = usuario.telefone || '';
  document.getElementById('usuario-profissao-form').value = usuario.profissao || '';
  document.getElementById('usuario-conselho-form').value = usuario.conselho_profissional || '';
  document.getElementById('usuario-registro-form').value = usuario.registro_profissional || '';
  document.getElementById('usuario-perfil-form').value = usuario.perfil;
  document.getElementById('titulo-form-usuario').textContent = 'Editar usuário';
  document.getElementById('campo-senha-temporaria').classList.add('d-none');
  document.getElementById('painel-form-usuario').classList.remove('d-none');
  document.getElementById('senha-temporaria-box').classList.add('d-none');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function fecharFormularioUsuario() {
  document.getElementById('painel-form-usuario').classList.add('d-none');
  document.getElementById('form-usuario').reset();
  document.getElementById('usuario-id').value = '';
}

async function salvarUsuario(evento) {
  evento.preventDefault();
  esconderAlerta('mensagem-usuarios');
  const id = Number(document.getElementById('usuario-id').value || 0);
  const dados = {
    nome: document.getElementById('usuario-nome-form').value.trim(),
    username: document.getElementById('usuario-login-form').value.trim(),
    perfil: document.getElementById('usuario-perfil-form').value,
    email: document.getElementById('usuario-email-form').value.trim(),
    telefone: document.getElementById('usuario-telefone-form').value.trim(),
    profissao: document.getElementById('usuario-profissao-form').value.trim(),
    conselho_profissional: document.getElementById('usuario-conselho-form').value.trim(),
    registro_profissional: document.getElementById('usuario-registro-form').value.trim(),
    senha_temporaria: document.getElementById('usuario-senha-form').value
  };

  try {
    const resposta = await apiFetch(id ? '/api/usuarios/' + id : '/api/usuarios', {
      method: id ? 'PUT' : 'POST',
      body: JSON.stringify(dados)
    });
    mostrarAlerta('mensagem-usuarios', resposta.mensagem);
    if (resposta.senha_temporaria) mostrarSenhaTemporaria(resposta.senha_temporaria);
    fecharFormularioUsuario();
    await carregarUsuarios();
  } catch (erro) {
    mostrarAlerta('mensagem-usuarios', erro.message, 'danger');
  }
}

async function tratarAcaoUsuario(evento) {
  const botao = evento.target.closest('button[data-acao]');
  if (!botao) return;
  const id = Number(botao.dataset.id);

  if (botao.dataset.acao === 'editar') {
    abrirEdicaoUsuario(id);
    return;
  }

  if (botao.dataset.acao === 'status') {
    const ativo = botao.dataset.ativo === '1';
    if (!confirm((ativo ? 'Reativar' : 'Inativar') + ' este usuário?')) return;
    try {
      const resposta = await apiFetch('/api/usuarios/' + id + '/status', {
        method: 'PATCH',
        body: JSON.stringify({ ativo: ativo })
      });
      mostrarAlerta('mensagem-usuarios', resposta.mensagem);
      await carregarUsuarios();
    } catch (erro) {
      mostrarAlerta('mensagem-usuarios', erro.message, 'danger');
    }
    return;
  }

  if (botao.dataset.acao === 'senha') {
    if (!confirm('Gerar uma nova senha temporária para este usuário?')) return;
    try {
      const resposta = await apiFetch('/api/usuarios/' + id + '/senha-temporaria', { method: 'POST' });
      mostrarSenhaTemporaria(resposta.senha_temporaria);
      mostrarAlerta('mensagem-usuarios', resposta.mensagem);
      await carregarUsuarios();
    } catch (erro) {
      mostrarAlerta('mensagem-usuarios', erro.message, 'danger');
    }
  }
}

async function tratarRecuperacao(evento) {
  const botao = evento.target.closest('button[data-recuperacao-id]');
  if (!botao) return;
  if (!confirm('Resolver a solicitação e gerar uma senha temporária?')) return;

  try {
    const resposta = await apiFetch('/api/recuperacoes-senha/' + botao.dataset.recuperacaoId + '/resolver', { method: 'POST' });
    mostrarSenhaTemporaria(resposta.senha_temporaria);
    mostrarAlerta('mensagem-usuarios', resposta.mensagem);
    await carregarUsuarios();
  } catch (erro) {
    mostrarAlerta('mensagem-usuarios', erro.message, 'danger');
  }
}

function mostrarSenhaTemporaria(senha) {
  document.getElementById('senha-temporaria-valor').textContent = senha;
  document.getElementById('senha-temporaria-box').classList.remove('d-none');
}
