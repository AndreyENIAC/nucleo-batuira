document.addEventListener('DOMContentLoaded', carregarDashboard);

async function carregarDashboard() {
  try {
    const resultados = await Promise.all([
      apiFetch('/api/dashboard'),
      apiFetch('/api/acolhidos'),
      apiFetch('/api/gastos')
    ]);

    const dashboard = resultados[0];
    const acolhidos = resultados[1];
    const gastos = resultados[2];

    document.getElementById('total-acolhidos').textContent = dashboard.total_acolhidos;
    document.getElementById('total-usuarios').textContent = dashboard.usuarios_ativos;
    document.getElementById('total-receitas').textContent = formatarDinheiro(dashboard.receitas_mes);
    document.getElementById('total-alertas').textContent = dashboard.alertas.length;

    renderizarAlertas(dashboard.alertas);
    renderizarAgenda(dashboard.agenda);
    renderizarSituacao(acolhidos);
    renderizarGastosRecentes(gastos.slice(0, 4));
  } catch (erro) {
    mostrarAlerta('erro-dashboard', erro.message, 'danger');
  }
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
    corpo.innerHTML = mensagemVazia('Nenhum evento cadastrado.', 4);
    return;
  }

  corpo.innerHTML = eventos.map(function (evento) {
    const data = new Date(evento.inicio);
    const hora = Number.isNaN(data.getTime()) ? '—' : data.toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'});
    return '<tr><td class="fw-semibold text-primary">' + hora + '</td>' +
      '<td>' + escaparHTML(evento.titulo) + '</td>' +
      '<td>' + escaparHTML(evento.local || '—') + '</td>' +
      '<td><span class="badge-nb badge-alta">' + escaparHTML(evento.tipo) + '</span></td></tr>';
  }).join('');
}

function renderizarSituacao(acolhidos) {
  const total = acolhidos.length || 1;
  const criticos = acolhidos.filter(a => a.status === 'critico').length;
  const atencao = acolhidos.filter(a => a.status === 'monitoramento').length;
  const ativos = acolhidos.filter(a => !['alta', 'inativo'].includes(a.status)).length;

  preencherProgresso('ativos', ativos, total);
  preencherProgresso('atencao', atencao, total);
  preencherProgresso('criticos', criticos, total);
}

function preencherProgresso(prefixo, valor, total) {
  document.getElementById(prefixo + '-texto').textContent = valor + ' / ' + total;
  document.getElementById(prefixo + '-barra').style.width = Math.round(valor / total * 100) + '%';
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
