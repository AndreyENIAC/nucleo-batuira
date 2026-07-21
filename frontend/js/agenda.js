let eventosAgenda = [];
let eventoEmEdicao = null;
let usuarioAgenda = null;

const nomesSetorAgenda = {
  saude: 'Gestão de Saúde',
  institucional: 'Gestão Institucional',
  geral: 'Geral'
};


document.addEventListener('DOMContentLoaded', async function () {
  usuarioAgenda = getUsuarioSalvo();
  configurarSetoresAgenda();
  configurarEventosDaPagina();
  await carregarAcolhidosAgenda();
  await carregarAgendaCompleta();
});

function configurarEventosDaPagina() {
  document.getElementById('form-evento')?.addEventListener('submit', salvarEvento);
  document.getElementById('btn-cancelar-edicao')?.addEventListener('click', limparFormularioEvento);
  document.getElementById('btn-atualizar-agenda')?.addEventListener('click', carregarAgendaCompleta);
  document.getElementById('filtro-setor')?.addEventListener('change', carregarAgendaCompleta);
  document.getElementById('filtro-status')?.addEventListener('change', carregarAgendaCompleta);
  document.getElementById('btn-novo-evento')?.addEventListener('click', function () {
    if (!eventoEmEdicao) prepararDataInicial();
  });
}

function setoresVisiveisNoFrontend() {
  if (['admin', 'staff'].includes(usuarioAgenda?.perfil)) return ['saude', 'institucional', 'geral'];
  if (usuarioAgenda?.perfil === 'technical') return ['saude', 'geral'];
  if (usuarioAgenda?.perfil === 'financial') return ['institucional', 'geral'];
  return ['geral'];
}

function setoresEditaveisNoFrontend() {
  if (usuarioAgenda?.perfil === 'admin') return ['saude', 'institucional', 'geral'];
  if (usuarioAgenda?.perfil === 'technical') return ['saude'];
  if (usuarioAgenda?.perfil === 'financial') return ['institucional'];
  return [];
}

function configurarSetoresAgenda() {
  const visiveis = setoresVisiveisNoFrontend();
  const editaveis = setoresEditaveisNoFrontend();

  document.getElementById('filtro-setor').innerHTML = '<option value="">Todos os setores permitidos</option>' + visiveis.map(function (setor) {
    return '<option value="' + setor + '">' + nomesSetorAgenda[setor] + '</option>';
  }).join('');

  document.getElementById('evento-setor').innerHTML = editaveis.map(function (setor) {
    return '<option value="' + setor + '">' + nomesSetorAgenda[setor] + '</option>';
  }).join('');
}

async function carregarAcolhidosAgenda() {
  try {
    const acolhidos = await apiFetch('/api/acolhidos');
    document.getElementById('evento-acolhido').innerHTML = '<option value="">Evento sem acolhido específico</option>' + acolhidos.map(function (acolhido) {
      return '<option value="' + acolhido.id + '">' + escaparHTML(acolhido.nome) + '</option>';
    }).join('');
  } catch (erro) {
    document.getElementById('evento-acolhido').innerHTML = '<option value="">Não foi possível carregar acolhidos</option>';
  }
}

async function carregarAgendaCompleta() {
  const parametros = new URLSearchParams();
  const setor = document.getElementById('filtro-setor').value;
  const status = document.getElementById('filtro-status').value;
  if (setor) parametros.set('setor', setor);
  if (status) parametros.set('status', status);

  try {
    eventosAgenda = await apiFetch('/api/agenda' + (parametros.toString() ? '?' + parametros.toString() : ''));
    renderizarAgendaCompleta(eventosAgenda);
  } catch (erro) {
    mostrarAlerta('mensagem-agenda', erro.message, 'danger');
  }
}

function renderizarAgendaCompleta(lista) {
  const corpo = document.getElementById('corpo-agenda-completa');
  if (!lista.length) {
    corpo.innerHTML = mensagemVazia('Nenhum evento encontrado.', 7);
    return;
  }

  corpo.innerHTML = lista.map(function (evento) {
    const podeEditar = usuarioPodeEditarEvento(evento);
    const statusClasse = evento.status === 'agendado' ? 'badge-ativo' : evento.status === 'concluido' ? 'badge-aprovado' : 'badge-atencao';
    const acoes = podeEditar
      ? '<button class="btn btn-outline-primary btn-sm btn-editar-evento" data-id="' + evento.id + '">Editar</button> ' +
        '<button class="btn btn-outline-danger btn-sm btn-excluir-evento" data-id="' + evento.id + '">Excluir</button>'
      : '<span class="text-muted small">Somente consulta</span>';

    return '<tr>' +
      '<td class="small"><strong>' + formatarDataHoraAgenda(evento.inicio) + '</strong>' +
      (evento.fim ? '<div class="text-muted">até ' + formatarDataHoraAgenda(evento.fim) + '</div>' : '') + '</td>' +
      '<td><strong>' + escaparHTML(evento.titulo) + '</strong><div class="small text-muted">' + escaparHTML(evento.tipo) + '</div></td>' +
      '<td>' + escaparHTML(nomesSetorAgenda[evento.setor] || evento.setor) + '</td>' +
      '<td>' + escaparHTML(evento.acolhido || '—') + '</td>' +
      '<td>' + escaparHTML(evento.local || '—') + '</td>' +
      '<td><span class="badge-nb ' + statusClasse + '">' + escaparHTML(evento.status) + '</span></td>' +
      '<td class="text-nowrap">' + acoes + '</td></tr>';
  }).join('');

  corpo.querySelectorAll('.btn-editar-evento').forEach(function (botao) {
    botao.addEventListener('click', function () { iniciarEdicaoEvento(Number(botao.dataset.id)); });
  });
  corpo.querySelectorAll('.btn-excluir-evento').forEach(function (botao) {
    botao.addEventListener('click', function () { excluirEvento(Number(botao.dataset.id)); });
  });
}

function usuarioPodeEditarEvento(evento) {
  if (usuarioAgenda?.perfil === 'admin') return true;
  if (usuarioAgenda?.perfil === 'technical') return evento.setor === 'saude';
  if (usuarioAgenda?.perfil === 'financial') return evento.setor === 'institucional';
  return false;
}

function formatarDataHoraAgenda(valor) {
  if (!valor) return '—';
  const data = new Date(String(valor).replace(' ', 'T'));
  if (Number.isNaN(data.getTime())) return valor;
  return data.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function paraDatetimeLocal(valor) {
  if (!valor) return '';
  return String(valor).replace(' ', 'T').slice(0, 16);
}

function prepararDataInicial() {
  const data = new Date();
  data.setMinutes(data.getMinutes() - data.getTimezoneOffset());
  data.setMinutes(0, 0, 0);
  document.getElementById('evento-inicio').value = data.toISOString().slice(0, 16);
}

function iniciarEdicaoEvento(id) {
  const evento = eventosAgenda.find(item => item.id === id);
  if (!evento) return;

  eventoEmEdicao = id;
  document.getElementById('titulo-form-evento').textContent = 'Editar evento';
  document.getElementById('btn-salvar-evento').textContent = 'Salvar alterações';
  document.getElementById('btn-cancelar-edicao').classList.remove('d-none');
  document.getElementById('evento-titulo').value = evento.titulo || '';
  document.getElementById('evento-tipo').value = evento.tipo || '';
  document.getElementById('evento-setor').value = evento.setor || '';
  document.getElementById('evento-inicio').value = paraDatetimeLocal(evento.inicio);
  document.getElementById('evento-fim').value = paraDatetimeLocal(evento.fim);
  document.getElementById('evento-local').value = evento.local || '';
  document.getElementById('evento-status').value = evento.status || 'agendado';
  document.getElementById('evento-acolhido').value = evento.acolhido_id || '';
  document.getElementById('evento-observacoes').value = evento.observacoes || '';
  bootstrap.Collapse.getOrCreateInstance(document.getElementById('painel-evento')).show();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function limparFormularioEvento() {
  eventoEmEdicao = null;
  document.getElementById('form-evento').reset();
  document.getElementById('titulo-form-evento').textContent = 'Cadastrar evento';
  document.getElementById('btn-salvar-evento').textContent = 'Salvar evento';
  document.getElementById('btn-cancelar-edicao').classList.add('d-none');
  configurarSetoresAgenda();
  prepararDataInicial();
}

async function salvarEvento(eventoSubmit) {
  eventoSubmit.preventDefault();
  const acolhido = document.getElementById('evento-acolhido').value;
  const dados = {
    titulo: document.getElementById('evento-titulo').value.trim(),
    tipo: document.getElementById('evento-tipo').value.trim(),
    setor: document.getElementById('evento-setor').value,
    inicio: document.getElementById('evento-inicio').value,
    fim: document.getElementById('evento-fim').value || null,
    local: document.getElementById('evento-local').value.trim(),
    status: document.getElementById('evento-status').value,
    acolhido_id: acolhido ? Number(acolhido) : null,
    observacoes: document.getElementById('evento-observacoes').value.trim()
  };

  try {
    const rota = eventoEmEdicao ? '/api/agenda/' + eventoEmEdicao : '/api/agenda';
    const metodo = eventoEmEdicao ? 'PUT' : 'POST';
    await apiFetch(rota, { method: metodo, body: JSON.stringify(dados) });
    mostrarAlerta('mensagem-agenda', eventoEmEdicao ? 'Evento atualizado com sucesso.' : 'Evento cadastrado com sucesso.');
    limparFormularioEvento();
    bootstrap.Collapse.getOrCreateInstance(document.getElementById('painel-evento')).hide();
    await carregarAgendaCompleta();
  } catch (erro) {
    mostrarAlerta('mensagem-agenda', erro.message, 'danger');
  }
}

async function excluirEvento(id) {
  if (!window.confirm('Deseja realmente excluir este evento da agenda?')) return;
  try {
    await apiFetch('/api/agenda/' + id, { method: 'DELETE' });
    mostrarAlerta('mensagem-agenda', 'Evento excluído com sucesso.');
    await carregarAgendaCompleta();
  } catch (erro) {
    mostrarAlerta('mensagem-agenda', erro.message, 'danger');
  }
}
