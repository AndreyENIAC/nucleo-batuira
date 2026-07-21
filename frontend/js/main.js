/* =====================================================
   main.js — funções usadas nas páginas internas
   ===================================================== */

document.addEventListener('DOMContentLoaded', function () {
  const arquivo = window.location.pathname.split('/').pop();
  const paginaLogin = arquivo === 'login.html' || arquivo === '';

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

  if (usuario.primeiro_acesso && !window.location.pathname.endsWith('trocar-senha.html')) {
    window.location.href = 'trocar-senha.html';
    return;
  }

  document.querySelectorAll('.usuario-nome').forEach(function (elemento) {
    elemento.textContent = usuario.nome;
  });

  document.querySelectorAll('.usuario-cargo').forEach(function (elemento) {
    elemento.textContent = usuario.nome_perfil;
  });

  document.querySelectorAll('[data-perfis]').forEach(function (elemento) {
    const perfis = elemento.dataset.perfis.split(',').map(p => p.trim());
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

  if (arquivo === 'usuarios.html' && usuario.perfil !== 'admin') {
    window.location.href = 'index.html';
    return;
  }

  if (arquivo === 'financeiro.html' && !['admin', 'financial', 'staff'].includes(usuario.perfil)) {
    window.location.href = 'index.html';
    return;
  }

  if (['acolhidos.html', 'perfil.html'].includes(arquivo) && !['admin', 'technical', 'staff'].includes(usuario.perfil)) {
    window.location.href = 'index.html';
  }
}
