document.addEventListener('DOMContentLoaded', function () {
  const usuarioSalvo = getUsuarioSalvo();

  if (getToken()) {
    window.location.href = usuarioSalvo?.primeiro_acesso
      ? 'trocar-senha.html'
      : 'index.html';
    return;
  }

  const formulario = document.getElementById('form-login');
  const botao = document.getElementById('btn-entrar');

  formulario.addEventListener('submit', async function (evento) {
    evento.preventDefault();
    esconderAlerta('mensagem-erro');

    const username = document.getElementById('usuario').value.trim();
    const senha = document.getElementById('senha').value;

    botao.disabled = true;
    botao.textContent = 'Entrando...';

    try {
      const resposta = await apiFetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({ username: username, senha: senha })
      });

      salvarSessao(resposta.access_token, resposta.usuario);
      window.location.href = resposta.usuario.primeiro_acesso
        ? 'trocar-senha.html'
        : 'index.html';
    } catch (erro) {
      mostrarAlerta('mensagem-erro', erro.message, 'danger');
    } finally {
      botao.disabled = false;
      botao.textContent = 'Entrar no Sistema';
    }
  });
});
