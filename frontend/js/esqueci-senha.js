document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('form-esqueci-senha').addEventListener('submit', solicitarRecuperacao);
});

async function solicitarRecuperacao(evento) {
  evento.preventDefault();
  esconderAlerta('mensagem-recuperacao');
  const botao = document.getElementById('btn-solicitar');
  botao.disabled = true;
  botao.textContent = 'Enviando...';

  try {
    const resposta = await apiFetch('/api/esqueci-senha', {
      method: 'POST',
      body: JSON.stringify({
        identificacao: document.getElementById('identificacao').value.trim()
      })
    });
    mostrarAlerta('mensagem-recuperacao', resposta.mensagem);
    evento.target.reset();
  } catch (erro) {
    mostrarAlerta('mensagem-recuperacao', erro.message, 'danger');
  } finally {
    botao.disabled = false;
    botao.textContent = 'Solicitar recuperação';
  }
}
