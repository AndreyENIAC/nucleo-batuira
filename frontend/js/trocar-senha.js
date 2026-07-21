document.addEventListener('DOMContentLoaded', function () {
  if (!getToken()) {
    window.location.href = 'login.html';
    return;
  }

  document.getElementById('form-trocar-senha').addEventListener('submit', trocarSenha);
  document.getElementById('btn-cancelar-sessao').addEventListener('click', function () {
    limparSessao();
    window.location.href = 'login.html';
  });
});

async function trocarSenha(evento) {
  evento.preventDefault();
  esconderAlerta('mensagem-troca-senha');

  const botao = document.getElementById('btn-trocar-senha');
  const dados = {
    senha_atual: document.getElementById('senha-atual').value,
    nova_senha: document.getElementById('nova-senha').value,
    confirmacao: document.getElementById('confirmar-senha').value
  };

  botao.disabled = true;
  botao.textContent = 'Salvando...';

  try {
    await apiFetch('/api/trocar-senha', {
      method: 'POST',
      body: JSON.stringify(dados)
    });

    const usuario = getUsuarioSalvo() || {};
    usuario.primeiro_acesso = false;
    localStorage.setItem('usuario', JSON.stringify(usuario));
    mostrarAlerta('mensagem-troca-senha', 'Senha alterada. Entrando no sistema...');
    setTimeout(function () {
      window.location.href = 'index.html';
    }, 700);
  } catch (erro) {
    mostrarAlerta('mensagem-troca-senha', erro.message, 'danger');
  } finally {
    botao.disabled = false;
    botao.textContent = 'Salvar nova senha';
  }
}
