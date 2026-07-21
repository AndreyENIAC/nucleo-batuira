let categoriasDespesa = [];
let categoriasReceita = [];
let acolhidosFinanceiro = [];


document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('form-gasto')?.addEventListener('submit', cadastrarGasto);
  document.getElementById('form-receita')?.addEventListener('submit', cadastrarReceita);
  document.getElementById('form-documento-institucional')?.addEventListener('submit', enviarDocumentoInstitucional);

  const hoje = new Date().toISOString().split('T')[0];
  document.getElementById('gasto-data').value = hoje;
  document.getElementById('receita-data').value = hoje;

  carregarFinanceiro();
  ativarAbaPelaUrl();
});

async function carregarFinanceiro() {
  try {
    const resultados = await Promise.all([
      apiFetch('/api/documentos?escopo=institucional'),
      apiFetch('/api/categorias-financeiras'),
      apiFetch('/api/receitas'),
      apiFetch('/api/gastos'),
      apiFetch('/api/prestacoes-contas'),
      apiFetch('/api/acolhidos'),
      apiFetch('/api/dashboard')
    ]);

    const categorias = resultados[1];
    categoriasDespesa = ordenarOutrosPorUltimo(categorias.filter(c => c.tipo === 'despesa'));
    categoriasReceita = ordenarOutrosPorUltimo(categorias.filter(c => c.tipo === 'receita'));
    acolhidosFinanceiro = resultados[5];

    preencherSelects();
    renderizarDocumentosInstitucionais(resultados[0]);
    renderizarReceitas(resultados[2]);
    renderizarGastos(resultados[3]);
    renderizarPrestacoes(resultados[4]);
    renderizarResumo(resultados[6]);
  } catch (erro) {
    mostrarAlerta('mensagem-financeiro', erro.message, 'danger');
  }
}

function ordenarOutrosPorUltimo(lista) {
  return [...lista].sort(function (a, b) {
    const aOutro = a.nome.toLowerCase().startsWith('outro');
    const bOutro = b.nome.toLowerCase().startsWith('outro');
    if (aOutro !== bOutro) return aOutro ? 1 : -1;
    return a.nome.localeCompare(b.nome, 'pt-BR');
  });
}

function preencherSelects() {
  document.getElementById('gasto-categoria').innerHTML = '<option value="">Selecione</option>' + categoriasDespesa.map(function (c) {
    return '<option value="' + c.id + '">' + escaparHTML(c.nome) + '</option>';
  }).join('');

  document.getElementById('receita-categoria').innerHTML = '<option value="">Selecione</option>' + categoriasReceita.map(function (c) {
    return '<option value="' + c.id + '">' + escaparHTML(c.nome) + '</option>';
  }).join('');

  document.getElementById('gasto-acolhido').innerHTML = '<option value="">Gasto institucional</option>' + acolhidosFinanceiro.map(function (a) {
    return '<option value="' + a.id + '">' + escaparHTML(a.nome) + '</option>';
  }).join('');
}

function renderizarResumo(dashboard) {
  document.getElementById('resumo-receitas').textContent = formatarDinheiro(dashboard.receitas_mes);
  document.getElementById('resumo-gastos').textContent = formatarDinheiro(dashboard.gastos_mes);
  const saldo = document.getElementById('resumo-saldo');
  saldo.textContent = formatarDinheiro(dashboard.saldo_mes);
  saldo.className = 'fs-5 ' + (Number(dashboard.saldo_mes) < 0 ? 'text-danger' : 'text-primary');
}

function renderizarDocumentosInstitucionais(lista) {
  const container = document.getElementById('lista-documentos-institucionais');
  document.getElementById('total-documentos-institucionais').textContent = lista.length;
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhum documento institucional enviado.</p>';
    return;
  }
  container.innerHTML = lista.map(function (d) {
    const indisponivel = d.arquivo_disponivel === false;
    return '<div class="documento-item linha-documento"><div><strong class="col-doc-nome">' + escaparHTML(d.titulo) + '</strong>' +
      '<div class="small text-muted">' + escaparHTML(d.categoria) + ' · ' + formatarDataHora(d.enviado_em) + '</div></div>' +
      (indisponivel
        ? '<span class="badge bg-secondary">Arquivo indisponível</span>'
        : '<button class="btn btn-outline-primary btn-sm btn-download-doc" data-id="' + d.id + '">⬇ Baixar</button>') + '</div>';
  }).join('');

  container.querySelectorAll('.btn-download-doc').forEach(function (botao) {
    botao.addEventListener('click', function () {
      baixarDocumentoFinanceiro(Number(botao.dataset.id));
    });
  });
}

function renderizarReceitas(lista) {
  const corpo = document.getElementById('corpo-receitas');
  const total = lista.reduce((soma, receita) => soma + Number(receita.valor), 0);
  document.getElementById('total-receitas').textContent = formatarDinheiro(total);

  if (!lista.length) {
    corpo.innerHTML = mensagemVazia('Nenhuma receita cadastrada.', 5);
    return;
  }

  corpo.innerHTML = lista.map(function (r) {
    return '<tr><td>' + escaparHTML(r.descricao) + '</td>' +
      '<td><span class="badge-nb badge-ativo">' + escaparHTML(r.categoria || 'Sem categoria') + '</span></td>' +
      '<td class="text-muted small">' + escaparHTML(r.fonte || '—') + '</td>' +
      '<td class="text-muted small">' + formatarData(r.data_recebimento) + '</td>' +
      '<td class="fw-semibold text-success text-end">' + formatarDinheiro(r.valor) + '</td></tr>';
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
    container.innerHTML = '<p class="text-muted">Nenhum movimento financeiro cadastrado.</p>';
    return;
  }

  container.innerHTML = lista.map(function (p) {
    const classes = {
      aprovado: 'badge-aprovado',
      em_analise: 'badge-analise',
      rascunho: 'badge-atencao',
      rejeitado: 'badge-critico',
      resumo: 'badge-ativo'
    };
    const statusTexto = p.status === 'resumo' ? 'Resumo automático' : p.status.replace('_', ' ');
    const saldoClasse = Number(p.saldo) < 0 ? 'text-danger' : 'text-success';
    return '<div class="card-nb p-4 mb-3"><div class="d-flex justify-content-between mb-3 flex-wrap gap-2">' +
      '<h6>' + escaparHTML(formatarCompetencia(p.competencia)) + '</h6><span class="badge-nb ' + (classes[p.status] || 'badge-analise') + '">' +
      escaparHTML(statusTexto) + '</span></div><div class="row g-3">' +
      '<div class="col-md-4"><small>Gastos</small><strong class="d-block text-danger">' + formatarDinheiro(p.total_gastos) + '</strong></div>' +
      '<div class="col-md-4"><small>Receitas</small><strong class="d-block text-success">' + formatarDinheiro(p.total_receitas) + '</strong></div>' +
      '<div class="col-md-4"><small>Saldo</small><strong class="d-block ' + saldoClasse + '">' + formatarDinheiro(p.saldo) + '</strong></div></div></div>';
  }).join('');
}

function formatarCompetencia(valor) {
  const partes = valor.split('-');
  return partes.length === 2 ? partes[1] + '/' + partes[0] : valor;
}

async function cadastrarReceita(evento) {
  evento.preventDefault();
  const dados = {
    categoria_id: Number(document.getElementById('receita-categoria').value),
    descricao: document.getElementById('receita-descricao').value.trim(),
    valor: Number(document.getElementById('receita-valor').value),
    data_recebimento: document.getElementById('receita-data').value,
    fonte: document.getElementById('receita-fonte').value.trim(),
    observacoes: document.getElementById('receita-observacoes').value.trim()
  };

  try {
    await apiFetch('/api/receitas', { method: 'POST', body: JSON.stringify(dados) });
    mostrarAlerta('mensagem-financeiro', 'Receita cadastrada com sucesso.');
    evento.target.reset();
    document.getElementById('receita-data').value = new Date().toISOString().split('T')[0];
    bootstrap.Collapse.getOrCreateInstance(document.getElementById('form-receita-collapse')).hide();
    await carregarFinanceiro();
  } catch (erro) {
    mostrarAlerta('mensagem-financeiro', erro.message, 'danger');
  }
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
    await carregarFinanceiro();
  } catch (erro) {
    mostrarAlerta('mensagem-financeiro', erro.message, 'danger');
  }
}

async function enviarDocumentoInstitucional(evento) {
  evento.preventDefault();
  const arquivo = document.getElementById('doc-inst-arquivo').files[0];
  if (!arquivo) {
    mostrarAlerta('mensagem-financeiro', 'Selecione um arquivo.', 'danger');
    return;
  }

  const formData = new FormData();
  formData.append('arquivo', arquivo);
  formData.append('titulo', document.getElementById('doc-inst-titulo').value.trim());
  formData.append('categoria', document.getElementById('doc-inst-categoria').value.trim());
  formData.append('escopo', 'institucional');

  try {
    await apiFetch('/api/documentos', { method: 'POST', body: formData });
    mostrarAlerta('mensagem-financeiro', 'Documento enviado com sucesso.');
    evento.target.reset();
    await carregarFinanceiro();
  } catch (erro) {
    mostrarAlerta('mensagem-financeiro', erro.message, 'danger');
  }
}

async function baixarDocumentoFinanceiro(id) {
  try {
    const resposta = await fetch(API_URL + '/api/documentos/' + id + '/download', {
      headers: { Authorization: 'Bearer ' + getToken() }
    });
    if (!resposta.ok) {
      const dados = (resposta.headers.get('content-type') || '').includes('application/json') ? await resposta.json() : null;
      throw new Error(dados?.erro || 'Não foi possível baixar o documento.');
    }

    const blob = await resposta.blob();
    const disposicao = resposta.headers.get('Content-Disposition') || '';
    const nomeUtf8 = disposicao.match(/filename\*=UTF-8''([^;]+)/i);
    const nomeSimples = disposicao.match(/filename="?([^";]+)"?/i);
    const nome = decodeURIComponent(nomeUtf8?.[1] || nomeSimples?.[1] || 'documento');

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = nome;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (erro) {
    mostrarAlerta('mensagem-financeiro', erro.message, 'danger');
  }
}

function ativarAbaPelaUrl() {
  const mapa = {
    '#tab-documentos': 'btn-tab-documentos',
    '#tab-receitas': 'btn-tab-receitas',
    '#tab-gastos': 'btn-tab-gastos',
    '#tab-prestacao': 'btn-tab-prestacao'
  };
  const botao = document.getElementById(mapa[window.location.hash]);
  if (botao) bootstrap.Tab.getOrCreateInstance(botao).show();
}
