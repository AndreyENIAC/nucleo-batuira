document.addEventListener('DOMContentLoaded', function () {
  carregarAcolhidos();

  document.getElementById('busca-acolhido').addEventListener('input', carregarAcolhidos);
  document.getElementById('filtro-status').addEventListener('change', carregarAcolhidos);
  document.getElementById('form-cadastro-acolhido').addEventListener('submit', cadastrarAcolhido);

  document.getElementById('data-admissao').value = new Date().toISOString().split('T')[0];
});

async function carregarAcolhidos() {
  const busca = document.getElementById('busca-acolhido').value.trim();
  const status = document.getElementById('filtro-status').value;
  const parametros = new URLSearchParams();

  if (busca) parametros.set('busca', busca);
  if (status) parametros.set('status', status);

  try {
    const rota = '/api/acolhidos' + (parametros.toString() ? '?' + parametros.toString() : '');
    const acolhidos = await apiFetch(rota);
    renderizarAcolhidos(acolhidos);
  } catch (erro) {
    mostrarAlerta('mensagem-acolhidos', erro.message, 'danger');
  }
}

function renderizarAcolhidos(acolhidos) {
  const corpo = document.getElementById('corpo-acolhidos');
  document.getElementById('quantidade-acolhidos').textContent = acolhidos.length + ' acolhido(s) exibido(s)';

  if (!acolhidos.length) {
    corpo.innerHTML = mensagemVazia('Nenhum acolhido encontrado.', 8);
    return;
  }

  corpo.innerHTML = acolhidos.map(function (a) {
    return '<tr><td class="fw-semibold">' + escaparHTML(a.nome) + '</td>' +
      '<td>' + (a.idade ?? '—') + '</td>' +
      '<td>' + escaparHTML(a.quarto || '—') + '</td>' +
      '<td>' + escaparHTML(a.condicao_principal || '—') + '</td>' +
      '<td class="text-muted small">' + escaparHTML(a.tipo_atendimento || '—') + '</td>' +
      '<td class="text-muted small">' + formatarData(a.ultima_consulta) + '</td>' +
      '<td>' + badgeStatus(a.status) + '</td>' +
      '<td><a href="perfil.html?id=' + a.id + '" class="btn btn-primary btn-sm">Ver Perfil →</a></td></tr>';
  }).join('');
}

function badgeStatus(status) {
  const dados = {
    estavel: ['Estável', 'badge-ativo'],
    monitoramento: ['Atenção', 'badge-atencao'],
    critico: ['Crítico', 'badge-critico'],
    alta: ['Alta', 'badge-alta']
  };
  const item = dados[status] || [status, 'badge-pendente'];
  return '<span class="badge-nb ' + item[1] + '">' + escaparHTML(item[0]) + '</span>';
}

async function cadastrarAcolhido(evento) {
  evento.preventDefault();
  esconderAlerta('mensagem-acolhidos');

  const dados = {
    nome: document.getElementById('acolhido-nome').value.trim(),
    data_nascimento: document.getElementById('data-nascimento').value,
    modalidade_acolhimento: document.getElementById('modalidade').value,
    data_admissao: document.getElementById('data-admissao').value,
    quarto: document.getElementById('quarto').value.trim(),
    status: document.getElementById('status').value,
    condicao_principal: document.getElementById('condicao-principal').value.trim(),
    tipo_atendimento: document.getElementById('tipo-atendimento').value
  };

  try {
    await apiFetch('/api/acolhidos', {
      method: 'POST',
      body: JSON.stringify(dados)
    });

    mostrarAlerta('mensagem-acolhidos', 'Acolhido cadastrado com sucesso.');
    evento.target.reset();
    document.getElementById('data-admissao').value = new Date().toISOString().split('T')[0];
    bootstrap.Collapse.getOrCreateInstance(document.getElementById('form-novo-acolhido')).hide();
    carregarAcolhidos();
  } catch (erro) {
    mostrarAlerta('mensagem-acolhidos', erro.message, 'danger');
  }
}
