/* =====================================================
   main.js — funções usadas nas páginas internas
   ===================================================== */

document.addEventListener('DOMContentLoaded', function () {
  const paginaLogin = window.location.pathname.endsWith('login.html');

  if (!paginaLogin && !getToken()) {
    window.location.href = 'login.html';
    return;
  }

  if (!paginaLogin) {
    configurarSidebar();
    verificarAcessoDaPagina();
  }
});

async function configurarSidebar() {
  let usuario = getUsuarioSalvo();

  try {
    usuario = await apiFetch('/api/me');
    localStorage.setItem('usuario', JSON.stringify(usuario));
  } catch (erro) {
    return;
  }

  document.querySelectorAll('.usuario-nome').forEach(function (elemento) {
    elemento.textContent = usuario.nome;
  });

  document.querySelectorAll('.usuario-cargo').forEach(function (elemento) {
    elemento.textContent = usuario.nome_perfil;
  });

  document.querySelectorAll('[data-perfis]').forEach(function (elemento) {
    const perfis = elemento.dataset.perfis.split(',');
    elemento.classList.toggle('d-none', !perfis.includes(usuario.perfil));
  });

  document.querySelectorAll('.btn-logout').forEach(function (botao) {
    botao.addEventListener('click', function (evento) {
      evento.preventDefault();
      limparSessao();
      window.location.href = 'login.html';
    });
  });
}

function verificarAcessoDaPagina() {
  const usuario = getUsuarioSalvo();
  if (!usuario) return;

  const arquivo = window.location.pathname.split('/').pop();

  if (arquivo === 'financeiro.html' && !['admin', 'financial'].includes(usuario.perfil)) {
    window.location.href = 'index.html';
  }

  if (['acolhidos.html', 'perfil.html'].includes(arquivo) && usuario.perfil === 'financial') {
    window.location.href = 'index.html';
  }
}
