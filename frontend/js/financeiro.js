let categorias = [];
let acolhidosFinanceiro = [];

document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('form-gasto').addEventListener('submit', cadastrarGasto);
  document.getElementById('form-documento-institucional').addEventListener('submit', enviarDocumentoInstitucional);
  document.getElementById('gasto-data').value = new Date().toISOString().split('T')[0];
  carregarFinanceiro();
});

async function carregarFinanceiro() {
  try {
    const resultados = await Promise.all([
      apiFetch('/api/documentos?escopo=institucional'),
      apiFetch('/api/categorias-financeiras'),
      apiFetch('/api/gastos'),
      apiFetch('/api/prestacoes-contas'),
      apiFetch('/api/recursos-administrativos'),
      apiFetch('/api/acolhidos'),
      apiFetch('/api/beneficios')
    ]);

    categorias = resultados[1].filter(c => c.tipo === 'despesa');
    acolhidosFinanceiro = resultados[5];

    preencherSelects();
    renderizarDocumentosInstitucionais(resultados[0]);
    renderizarGastos(resultados[2]);
    renderizarPrestacoes(resultados[3]);
    renderizarRecursos(resultados[4], resultados[6]);
  } catch (erro) {
    mostrarAlerta('mensagem-financeiro', erro.message, 'danger');
  }
}

function preencherSelects() {
  document.getElementById('gasto-categoria').innerHTML = '<option value="">Selecione</option>' + categorias.map(function (c) {
    return '<option value="' + c.id + '">' + escaparHTML(c.nome) + '</option>';
  }).join('');

  document.getElementById('gasto-acolhido').innerHTML = '<option value="">Gasto institucional</option>' + acolhidosFinanceiro.map(function (a) {
    return '<option value="' + a.id + '">' + escaparHTML(a.nome) + '</option>';
  }).join('');
}

function renderizarDocumentosInstitucionais(lista) {
  const container = document.getElementById('lista-documentos-institucionais');
  document.getElementById('total-documentos-institucionais').textContent = lista.length;
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhum documento institucional enviado.</p>';
    return;
  }
  container.innerHTML = lista.map(function (d) {
    return '<div class="documento-item linha-documento"><div><strong class="col-doc-nome">' + escaparHTML(d.titulo) + '</strong>' +
      '<div class="small text-muted">' + escaparHTML(d.categoria) + ' · ' + formatarDataHora(d.enviado_em) + '</div></div>' +
      '<button class="btn btn-outline-primary btn-sm" onclick="baixarDocumentoFinanceiro(' + d.id + ')">⬇ Baixar</button></div>';
  }).join('');
}

function renderizarGastos(lista) {
  const corpo = document.getElementById('corpo-gastos');
  const total = lista.reduce((soma, gasto) => soma + Number(gasto.valor), 0);
  document.getElementById('total-gastos').textContent = formatarDinheiro(total);

  if (!lista.length) {
    corpo.innerHTML = mensagemVazia('Nenhum gasto cadastrado.', 6);
    return;
  }

  corpo.innerHTML = lista.map(function (g) {
    return '<tr class="linha-gasto"><td class="col-gasto-desc">' + escaparHTML(g.descricao) + '</td>' +
      '<td class="col-gasto-acolhido text-muted small">' + escaparHTML(g.acolhido || 'Instituição') + '</td>' +
      '<td><span class="badge-nb badge-alta">' + escaparHTML(g.categoria) + '</span></td>' +
      '<td class="text-muted small">' + escaparHTML(g.fornecedor || '—') + '</td>' +
      '<td class="text-muted small">' + formatarData(g.data_gasto) + '</td>' +
      '<td class="fw-semibold text-danger text-end">' + formatarDinheiro(g.valor) + '</td></tr>';
  }).join('');
}

function renderizarPrestacoes(lista) {
  const container = document.getElementById('lista-prestacoes');
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhuma prestação cadastrada.</p>';
    return;
  }
  container.innerHTML = lista.map(function (p) {
    const statusClasse = p.status === 'aprovado' ? 'badge-aprovado' : 'badge-analise';
    return '<div class="card-nb p-4 mb-3"><div class="d-flex justify-content-between mb-3">' +
      '<h6>' + escaparHTML(formatarCompetencia(p.competencia)) + '</h6><span class="badge-nb ' + statusClasse + '">' +
      escaparHTML(p.status.replace('_', ' ')) + '</span></div><div class="row">' +
      '<div class="col-md-4"><small>Gastos</small><strong class="d-block">' + formatarDinheiro(p.total_gastos) + '</strong></div>' +
      '<div class="col-md-4"><small>Receitas</small><strong class="d-block">' + formatarDinheiro(p.total_receitas) + '</strong></div>' +
      '<div class="col-md-4"><small>Saldo</small><strong class="d-block text-success">' + formatarDinheiro(p.saldo) + '</strong></div></div></div>';
  }).join('');
}

function formatarCompetencia(valor) {
  const partes = valor.split('-');
  return partes.length === 2 ? partes[1] + '/' + partes[0] : valor;
}

function renderizarRecursos(recursos, beneficios) {
  const container = document.getElementById('lista-recursos');
  container.innerHTML = recursos.length ? recursos.map(function (r) {
    return '<div class="documento-item"><div><strong>' + escaparHTML(r.nome) + '</strong>' +
      '<div class="small text-muted">' + escaparHTML(r.tipo) + ' · Validade: ' + formatarData(r.data_validade) + '</div></div>' +
      '<span class="badge-nb ' + (r.status === 'ativo' ? 'badge-ativo' : 'badge-atencao') + '">' + escaparHTML(r.status) + '</span></div>';
  }).join('') : '<p class="text-muted">Nenhum recurso administrativo cadastrado.</p>';

  const corpo = document.getElementById('corpo-beneficios');
  corpo.innerHTML = beneficios.length ? beneficios.map(function (b) {
    return '<tr><td>' + escaparHTML(b.acolhido) + '</td><td>' + escaparHTML(b.tipo_beneficio) + '</td>' +
      '<td>' + formatarDinheiro(b.valor_mensal) + '</td><td>' + escaparHTML(b.status) + '</td></tr>';
  }).join('') : mensagemVazia('Nenhum benefício cadastrado.', 4);
}

async function cadastrarGasto(evento) {
  evento.preventDefault();
  const acolhidoValor = document.getElementById('gasto-acolhido').value;
  const dados = {
    categoria_id: Number(document.getElementById('gasto-categoria').value),
    descricao: document.getElementById('gasto-descricao').value.trim(),
    valor: Number(document.getElementById('gasto-valor').value),
    data_gasto: document.getElementById('gasto-data').value,
    acolhido_id: acolhidoValor ? Number(acolhidoValor) : null,
    fornecedor: document.getElementById('gasto-fornecedor').value.trim()
  };

  try {
    await apiFetch('/api/gastos', { method: 'POST', body: JSON.stringify(dados) });
    mostrarAlerta('mensagem-financeiro', 'Gasto cadastrado com sucesso.');
    evento.target.reset();
    document.getElementById('gasto-data').value = new Date().toISOString().split('T')[0];
    bootstrap.Collapse.getOrCreateInstance(document.getElementById('form-gasto-collapse')).hide();
    carregarFinanceiro();
  } catch (erro) {
    mostrarAlerta('mensagem-financeiro', erro.message, 'danger');
  }
}

async function enviarDocumentoInstitucional(evento) {
  evento.preventDefault();
  const formData = new FormData();
  formData.append('arquivo', document.getElementById('doc-inst-arquivo').files[0]);
  formData.append('titulo', document.getElementById('doc-inst-titulo').value.trim());
  formData.append('categoria', document.getElementById('doc-inst-categoria').value.trim());
  formData.append('escopo', 'institucional');

  try {
    await apiFetch('/api/documentos', { method: 'POST', body: formData });
    mostrarAlerta('mensagem-financeiro', 'Documento enviado com sucesso.');
    evento.target.reset();
    carregarFinanceiro();
  } catch (erro) {
    mostrarAlerta('mensagem-financeiro', erro.message, 'danger');
  }
}

async function baixarDocumentoFinanceiro(id) {
  try {
    const resposta = await fetch(API_URL + '/api/documentos/' + id + '/download', {
      headers: { Authorization: 'Bearer ' + getToken() }
    });
    if (!resposta.ok) throw new Error('Não foi possível baixar o documento.');
    const blob = await resposta.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = '';
    link.click();
    URL.revokeObjectURL(url);
  } catch (erro) {
    mostrarAlerta('mensagem-financeiro', erro.message, 'danger');
  }
}
