document.addEventListener('DOMContentLoaded', carregarDashboard);

async function carregarDashboard() {
  try {
    const resultados = await Promise.all([
      apiFetch('/api/dashboard'),
      apiFetch('/api/gastos')
    ]);

    const dashboard = resultados[0];
    const gastos = resultados[1];

    preencherTexto('total-acolhidos', dashboard.total_acolhidos);
    preencherTexto('total-usuarios', dashboard.usuarios_ativos);
    preencherTexto('total-saldo', formatarDinheiro(dashboard.saldo_mes));
    preencherTexto('total-alertas', dashboard.total_alertas_abertos);

    renderizarAlertas(dashboard.alertas || []);
    renderizarAgenda(dashboard.agenda || []);
    renderizarSituacao(dashboard.situacao_acolhidos || {});
    renderizarGastosRecentes(gastos.slice(0, 4));
  } catch (erro) {
    mostrarAlerta('erro-dashboard', erro.message, 'danger');
  }
}

function preencherTexto(id, valor) {
  const elemento = document.getElementById(id);
  if (elemento) elemento.textContent = valor;
}

function renderizarAlertas(alertas) {
  const container = document.getElementById('lista-alertas');

  if (!alertas.length) {
    container.innerHTML = '<p class="text-muted mb-0">Nenhum alerta aberto.</p>';
    return;
  }

  const classes = { critica: 'danger', alta: 'danger', media: 'warning', baixa: 'info' };
  container.innerHTML = alertas.map(function (alerta) {
    const classe = classes[alerta.severidade] || 'warning';
    return '<div class="alert alert-' + classe + ' py-2 px-3 mb-2">' +
      '<strong>' + escaparHTML(alerta.acolhido || alerta.tipo) + '</strong><br>' +
      '<span class="small">' + escaparHTML(alerta.mensagem) + '</span></div>';
  }).join('');
}

function renderizarAgenda(eventos) {
  const corpo = document.getElementById('corpo-agenda');

  if (!eventos.length) {
    corpo.innerHTML = mensagemVazia('Nenhum próximo evento cadastrado.', 5);
    return;
  }

  const nomesSetor = {
    saude: 'Gestão de Saúde',
    institucional: 'Gestão Institucional',
    geral: 'Geral'
  };

  corpo.innerHTML = eventos.map(function (evento) {
    const data = interpretarDataHora(evento.inicio);
    const dia = data ? data.toLocaleDateString('pt-BR') : '—';
    const hora = data ? data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }) : '—';
    return '<tr>' +
      '<td class="fw-semibold text-primary">' + dia + '</td>' +
      '<td>' + hora + '</td>' +
      '<td><strong>' + escaparHTML(evento.titulo) + '</strong>' +
      (evento.acolhido ? '<div class="small text-muted">' + escaparHTML(evento.acolhido) + '</div>' : '') + '</td>' +
      '<td><span class="badge-nb badge-alta">' + escaparHTML(nomesSetor[evento.setor] || evento.setor) + '</span></td>' +
      '<td>' + escaparHTML(evento.local || '—') + '</td></tr>';
  }).join('');
}

function interpretarDataHora(valor) {
  if (!valor) return null;
  const data = new Date(String(valor).replace(' ', 'T'));
  return Number.isNaN(data.getTime()) ? null : data;
}

function renderizarSituacao(situacao) {
  const container = document.getElementById('situacao-acolhidos');
  const itens = [
    { chave: 'estavel', nome: 'Estável', cor: '#22c55e' },
    { chave: 'monitoramento', nome: 'Monitoramento', cor: '#f59e0b' },
    { chave: 'critico', nome: 'Crítico', cor: '#ef4444' },
    { chave: 'alta', nome: 'Alta', cor: '#3b82f6' },
    { chave: 'inativo', nome: 'Inativo', cor: '#64748b' }
  ];
  const total = itens.reduce(function (soma, item) {
    return soma + Number(situacao[item.chave] || 0);
  }, 0);

  container.innerHTML = itens.map(function (item) {
    const valor = Number(situacao[item.chave] || 0);
    const porcentagem = total ? Math.round(valor / total * 100) : 0;
    return '<div class="mb-3">' +
      '<div class="d-flex justify-content-between"><span>' + item.nome + '</span>' +
      '<span>' + valor + ' / ' + total + '</span></div>' +
      '<div class="progresso-barra"><div class="progresso-fill" style="background:' + item.cor + ';width:' + porcentagem + '%"></div></div>' +
      '</div>';
  }).join('');
}

function renderizarGastosRecentes(gastos) {
  const corpo = document.getElementById('corpo-gastos-recentes');

  if (!gastos.length) {
    corpo.innerHTML = mensagemVazia('Nenhum gasto cadastrado.', 3);
    return;
  }

  corpo.innerHTML = gastos.map(function (gasto) {
    return '<tr><td>' + escaparHTML(gasto.descricao) + '</td>' +
      '<td class="text-muted small">' + escaparHTML(gasto.acolhido || 'Instituição') + '</td>' +
      '<td class="fw-semibold text-danger text-end">' + formatarDinheiro(gasto.valor) + '</td></tr>';
  }).join('');
}
