let acolhidoId = null;
let acolhidoAtual = null;
let catalogoAlergias = [];

const hojeISO = () => new Date().toISOString().split('T')[0];

function podeEditarSaude() {
  const perfil = getUsuarioSalvo()?.perfil;
  return ['admin', 'technical'].includes(perfil);
}

document.addEventListener('DOMContentLoaded', function () {
  acolhidoId = Number(new URLSearchParams(window.location.search).get('id'));

  if (!acolhidoId) {
    window.location.href = 'acolhidos.html';
    return;
  }

  configurarFormularios();
  configurarAcoesDinamicas();
  definirDatasPadrao();
  carregarPerfilCompleto();
});

function configurarFormularios() {
  const formularios = {
    'form-atualizar-acolhido': atualizarPerfil,
    'form-alergia': cadastrarAlergia,
    'form-familiar': cadastrarFamiliar,
    'form-prescricao': cadastrarPrescricao,
    'form-nota': cadastrarNota,
    'form-pia': cadastrarPia,
    'form-pts': cadastrarPts,
    'form-plano-alta': cadastrarPlanoAlta,
    'form-beneficio': cadastrarBeneficio,
    'form-documento-acolhido': enviarDocumento
  };

  Object.entries(formularios).forEach(function ([id, funcao]) {
    document.getElementById(id)?.addEventListener('submit', funcao);
  });

  document.getElementById('btn-salvar-status')?.addEventListener('click', function () {
    alterarStatusAcolhido(document.getElementById('status-rapido').value);
  });

  document.getElementById('btn-inativar-acolhido')?.addEventListener('click', function () {
    alterarStatusAcolhido('inativo');
  });

  document.getElementById('nota-alerta')?.addEventListener('change', function (evento) {
    document.getElementById('nota-severidade').disabled = !evento.target.checked;
  });
}

function configurarAcoesDinamicas() {
  document.addEventListener('click', async function (evento) {
    const botaoPrescricao = evento.target.closest('[data-alterar-prescricao]');
    if (botaoPrescricao) {
      const id = Number(botaoPrescricao.dataset.alterarPrescricao);
      const status = document.getElementById('status-prescricao-' + id).value;
      await alterarStatusPrescricao(id, status);
      return;
    }

    const botaoAlerta = evento.target.closest('[data-resolver-alerta]');
    if (botaoAlerta) {
      await resolverAlerta(Number(botaoAlerta.dataset.resolverAlerta));
      return;
    }

    const botaoAlta = evento.target.closest('[data-concluir-alta]');
    if (botaoAlta) {
      await concluirPlanoAlta(Number(botaoAlta.dataset.concluirAlta));
      return;
    }

    const botaoBeneficio = evento.target.closest('[data-alterar-beneficio]');
    if (botaoBeneficio) {
      const id = Number(botaoBeneficio.dataset.alterarBeneficio);
      const status = document.getElementById('status-beneficio-' + id).value;
      await alterarStatusBeneficio(id, status);
      return;
    }

    const botaoDownload = evento.target.closest('[data-download-documento]');
    if (botaoDownload) {
      await baixarDocumento(
        Number(botaoDownload.dataset.downloadDocumento),
        botaoDownload.dataset.nomeArquivo
      );
    }
  });
}

function definirDatasPadrao() {
  ['prescricao-data-inicio', 'pia-data', 'pts-data', 'beneficio-inicio'].forEach(function (id) {
    const campo = document.getElementById(id);
    if (campo) campo.value = hojeISO();
  });
  document.getElementById('nota-severidade').disabled = true;
}

async function carregarPerfilCompleto() {
  try {
    const resultados = await Promise.all([
      apiFetch('/api/acolhidos/' + acolhidoId),
      apiFetch('/api/acolhidos/' + acolhidoId + '/familiares'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/alergias'),
      apiFetch('/api/alergias'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/prescricoes'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/notas'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/pias'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/pts'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/planos-alta'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/beneficios'),
      apiFetch('/api/documentos?acolhido_id=' + acolhidoId)
    ]);

    acolhidoAtual = resultados[0];
    catalogoAlergias = resultados[3];

    renderizarCabecalho(resultados[0]);
    preencherFormularioPerfil(resultados[0]);
    renderizarFamiliares(resultados[1]);
    renderizarAlergias(resultados[2], resultados[3]);
    renderizarPrescricoes(resultados[4]);
    renderizarNotas(resultados[5]);
    renderizarPiaPts(resultados[6], resultados[7]);
    renderizarPlanoAlta(resultados[8]);
    renderizarBeneficios(resultados[9]);
    renderizarDocumentos(resultados[10]);

    const somenteLeitura = !podeEditarSaude();
    document.getElementById('dados-somente-leitura').classList.toggle('d-none', !somenteLeitura);
    document.querySelectorAll('#form-atualizar-acolhido input, #form-atualizar-acolhido select, #form-atualizar-acolhido textarea').forEach(function (campo) {
      campo.disabled = somenteLeitura;
    });
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}

function renderizarCabecalho(a) {
  document.title = 'Perfil — ' + a.nome + ' — Núcleo Batuíra';
  document.getElementById('perfil-nome').textContent = a.nome;
  document.getElementById('perfil-resumo').textContent =
    (a.idade ?? '—') + ' anos · Quarto ' + (a.quarto || '—') + ' · ' +
    (a.diagnostico_principal?.descricao || 'Sem condição principal');
  document.getElementById('perfil-status').innerHTML = badgeStatusPerfil(a.status);
  document.getElementById('perfil-cpf').textContent = formatarCPF(a.cpf);
  document.getElementById('perfil-entrada').textContent = formatarData(a.data_admissao);
  document.getElementById('perfil-convenio').textContent = a.convenio || a.tipo_atendimento || '—';
  document.getElementById('perfil-responsavel').textContent = a.contato_principal
    ? a.contato_principal.nome + ' (' + a.contato_principal.parentesco + ')' : '—';
  document.getElementById('perfil-alergias').textContent = a.alergias.length
    ? a.alergias.map(x => x.nome).join(', ') : 'Nenhuma registrada';
  document.getElementById('status-rapido').value = a.status;
}

function preencherFormularioPerfil(a) {
  const valores = {
    'editar-nome': a.nome,
    'editar-cpf': formatarCPF(a.cpf, false),
    'editar-nascimento': a.data_nascimento,
    'editar-admissao': a.data_admissao,
    'editar-ala': a.ala,
    'editar-quarto': a.quarto,
    'editar-status': a.status,
    'editar-tipo-atendimento': a.tipo_atendimento,
    'editar-convenio': a.convenio,
    'editar-condicao': a.diagnostico_principal?.descricao,
    'editar-endereco': a.endereco,
    'editar-rg': a.rg,
    'editar-observacoes': a.observacoes
  };
  Object.entries(valores).forEach(function ([id, valor]) {
    const campo = document.getElementById(id);
    if (campo) campo.value = valor || '';
  });
}

function formatarCPF(valor, pontuar = true) {
  const numeros = String(valor || '').replace(/\D/g, '');
  if (!numeros) return pontuar ? 'Não informado' : '';
  if (!pontuar || numeros.length !== 11) return numeros;
  return numeros.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

function badgeStatusPerfil(status) {
  const map = {
    estavel: ['Estável', 'badge-ativo'],
    monitoramento: ['Monitoramento', 'badge-atencao'],
    critico: ['Crítico', 'badge-critico'],
    alta: ['Alta', 'badge-alta'],
    inativo: ['Inativo', 'badge-pendente']
  };
  const item = map[status] || [status, 'badge-pendente'];
  return '<span class="badge-nb ' + item[1] + '">' + escaparHTML(item[0]) + '</span>';
}

function renderizarAlergias(lista, catalogo) {
  document.getElementById('catalogo-alergias').innerHTML = catalogo.map(function (a) {
    return '<option value="' + escaparHTML(a.nome) + '"></option>';
  }).join('');

  const container = document.getElementById('lista-alergias');
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhuma alergia cadastrada.</p>';
    return;
  }
  container.innerHTML = '<div class="row g-2">' + lista.map(function (a) {
    return '<div class="col-md-4"><div class="card-nb p-3 h-100"><strong>' + escaparHTML(a.nome) + '</strong>' +
      '<div class="small text-muted">Gravidade: ' + escaparHTML(a.gravidade || 'não informada') + '</div>' +
      (a.observacoes ? '<div class="small mt-1">' + escaparHTML(a.observacoes) + '</div>' : '') +
      '</div></div>';
  }).join('') + '</div>';
}

function renderizarFamiliares(lista) {
  const container = document.getElementById('lista-familiares');
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhum familiar cadastrado.</p>';
    return;
  }
  container.innerHTML = lista.map(function (f) {
    return '<div class="card-nb p-3 mb-2"><strong>' + escaparHTML(f.nome) + '</strong>' +
      (f.contato_principal ? ' <span class="badge-nb badge-alta">Contato principal</span>' : '') +
      '<div class="text-muted small">' + escaparHTML(f.parentesco) + ' · ' +
      escaparHTML(f.telefone || 'Sem telefone') + ' · ' + escaparHTML(f.email || 'Sem e-mail') + '</div></div>';
  }).join('');
}

function renderizarPrescricoes(lista) {
  const container = document.getElementById('lista-prescricoes');
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhuma prescrição cadastrada.</p>';
    return;
  }

  container.innerHTML = lista.map(function (p) {
    const classes = { ativa: 'badge-ativo', suspensa: 'badge-atencao', encerrada: 'badge-pendente' };
    const controle = podeEditarSaude()
      ? '<div class="d-flex gap-2 align-items-center"><select id="status-prescricao-' + p.id + '" class="form-select form-select-sm">' +
        ['ativa', 'suspensa', 'encerrada'].map(s => '<option value="' + s + '" ' + (s === p.status ? 'selected' : '') + '>' + s + '</option>').join('') +
        '</select><button type="button" data-alterar-prescricao="' + p.id + '" class="btn btn-outline-primary btn-sm">Atualizar</button></div>'
      : '<span class="badge-nb ' + (classes[p.status] || 'badge-pendente') + '">' + escaparHTML(p.status) + '</span>';

    return '<div class="card-nb p-3 mb-2"><div class="d-flex justify-content-between gap-3 flex-wrap">' +
      '<div><strong>' + escaparHTML(p.medicamento) + '</strong>' +
      '<div class="small">' + escaparHTML(p.dosagem || '') + ' · ' + escaparHTML(p.posologia) + '</div>' +
      '<div class="small text-muted">' + escaparHTML(p.via_administracao || 'Via não informada') +
      (p.frequencia ? ' · ' + escaparHTML(p.frequencia) : '') + '</div>' +
      '<div class="small text-muted">' + escaparHTML(p.profissional) + ' · ' + formatarData(p.data_inicio) + '</div></div>' +
      controle + '</div></div>';
  }).join('');
}

function renderizarNotas(lista) {
  const container = document.getElementById('lista-notas');
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhuma nota clínica cadastrada.</p>';
    return;
  }

  container.innerHTML = lista.map(function (n) {
    let alerta = '';
    if (n.alerta_id) {
      alerta = '<div class="mt-2 d-flex gap-2 align-items-center flex-wrap"><span class="badge-nb ' +
        (n.alerta_status === 'resolvido' ? 'badge-ativo' : 'badge-critico') + '">Alerta ' +
        escaparHTML(n.alerta_status) + ' · ' + escaparHTML(n.alerta_severidade) + '</span>';
      if (podeEditarSaude() && n.alerta_status !== 'resolvido') {
        alerta += '<button type="button" data-resolver-alerta="' + n.alerta_id + '" class="btn btn-outline-success btn-sm">Marcar resolvido</button>';
      }
      alerta += '</div>';
    }
    return '<div class="card-nb p-3 mb-2"><div class="d-flex justify-content-between flex-wrap">' +
      '<strong>' + escaparHTML(n.tipo) + '</strong><span class="small text-muted">' + formatarDataHora(n.registrado_em) + '</span></div>' +
      '<p class="mb-1 mt-2 texto-preservado">' + escaparHTML(n.conteudo) + '</p>' +
      '<span class="small text-muted">' + escaparHTML(n.profissional) +
      (n.registro_profissional ? ' · ' + escaparHTML(n.registro_profissional) : '') + '</span>' + alerta + '</div>';
  }).join('');
}

function renderizarPiaPts(pias, ptsLista) {
  const pia = document.getElementById('conteudo-pia');
  const pts = document.getElementById('conteudo-pts');

  pia.innerHTML = pias.length ? pias.map(function (p) {
    const metas = p.metas.map(function (m) {
      return '<div class="mb-3"><div class="d-flex justify-content-between"><span>' + escaparHTML(m.area + ': ' + m.objetivo) +
        '</span><strong>' + m.progresso + '%</strong></div><div class="progresso-barra"><div class="progresso-fill" style="width:' +
        m.progresso + '%"></div></div><div class="small text-muted mt-1">' + escaparHTML(m.acoes) + '</div></div>';
    }).join('');
    return '<div class="card-nb p-3 mb-3"><strong>PIA ' + escaparHTML(p.versao) + '</strong>' +
      '<div class="small text-muted mb-2">Elaborado em ' + formatarData(p.data_elaboracao) + ' · ' + escaparHTML(p.status) + '</div>' +
      '<p><strong>Situação:</strong> ' + escaparHTML(p.situacao_atual) + '</p>' +
      '<p><strong>Necessidades:</strong> ' + escaparHTML(p.necessidades) + '</p>' + metas + '</div>';
  }).join('') : '<p class="text-muted">Nenhum PIA cadastrado.</p>';

  pts.innerHTML = ptsLista.length ? ptsLista.map(function (p) {
    const intervencoes = p.intervencoes.map(function (i) {
      return '<li class="mb-2"><strong>' + escaparHTML(i.especialidade) + ':</strong> ' +
        escaparHTML(i.intervencao) + ' <span class="text-muted">(' + escaparHTML(i.responsavel_nome || i.responsavel_externo || 'Sem responsável') + ')</span></li>';
    }).join('');
    return '<div class="card-nb p-3 mb-3"><strong>PTS — ' + formatarData(p.data_reuniao) + '</strong>' +
      '<div class="small text-muted">Status: ' + escaparHTML(p.status) + '</div>' +
      '<p class="mt-2"><strong>Diagnóstico:</strong> ' + escaparHTML(p.diagnostico_situacao) + '</p>' +
      '<p><strong>Objetivos:</strong> ' + escaparHTML(p.objetivos_terapeuticos) + '</p><ul>' + intervencoes + '</ul></div>';
  }).join('') : '<p class="text-muted">Nenhum PTS cadastrado.</p>';
}

function renderizarPlanoAlta(planos) {
  const container = document.getElementById('conteudo-alta');
  if (!planos.length) {
    container.innerHTML = '<p class="text-muted">Nenhum plano de alta cadastrado.</p>';
    return;
  }
  container.innerHTML = planos.map(function (p) {
    const etapas = p.etapas.map(function (e) {
      const icone = e.status === 'concluido' ? '✅' : e.status === 'em_andamento' ? '🔄' : '⏳';
      return '<div class="py-2 border-bottom">' + icone + ' ' + escaparHTML(e.descricao) + '</div>';
    }).join('');
    const botao = podeEditarSaude() && p.status !== 'concluido'
      ? '<button type="button" data-concluir-alta="' + p.id + '" class="btn btn-success btn-sm mt-3">Concluir e marcar acolhido como alta</button>'
      : '';
    return '<div class="card-nb p-3 mb-3"><div class="d-flex justify-content-between"><strong>Plano de alta</strong><span class="badge-nb badge-pendente">' + escaparHTML(p.status) + '</span></div>' +
      '<p class="mt-2"><strong>Previsão:</strong> ' + formatarData(p.previsao_alta) + '</p>' +
      '<p><strong>Tipo:</strong> ' + escaparHTML(p.tipo_alta || '—') + '</p>' + etapas +
      '<p class="mt-3 mb-0"><strong>Orientações:</strong> ' + escaparHTML(p.orientacoes || '—') + '</p>' + botao + '</div>';
  }).join('');
}

function renderizarBeneficios(lista) {
  const container = document.getElementById('lista-beneficios');
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhum benefício cadastrado.</p>';
    return;
  }

  container.innerHTML = lista.map(function (b) {
    const controle = podeEditarSaude()
      ? '<div class="d-flex gap-2"><select id="status-beneficio-' + b.id + '" class="form-select form-select-sm"><option value="ativo" ' + (b.status === 'ativo' ? 'selected' : '') + '>Ativo</option><option value="suspenso" ' + (b.status === 'suspenso' ? 'selected' : '') + '>Suspenso</option><option value="encerrado" ' + (b.status === 'encerrado' ? 'selected' : '') + '>Encerrado</option></select><button type="button" data-alterar-beneficio="' + b.id + '" class="btn btn-outline-primary btn-sm">Atualizar</button></div>'
      : '<span class="badge-nb ' + (b.status === 'ativo' ? 'badge-ativo' : 'badge-pendente') + '">' + escaparHTML(b.status) + '</span>';
    return '<div class="card-nb p-3 mb-2"><div class="d-flex justify-content-between gap-3 flex-wrap"><div><strong>' + escaparHTML(b.tipo_beneficio) + '</strong>' +
      '<div>' + formatarDinheiro(b.valor_mensal) + ' por mês</div><div class="small text-muted">' + escaparHTML(b.orgao_pagador || 'Órgão não informado') +
      ' · desde ' + formatarData(b.data_inicio) + '</div></div>' + controle + '</div></div>';
  }).join('');
}

function renderizarDocumentos(lista) {
  const container = document.getElementById('lista-documentos-acolhido');
  document.getElementById('total-documentos-acolhido').textContent = lista.length;
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhum documento enviado.</p>';
    return;
  }
  container.innerHTML = lista.map(function (d) {
    const indisponivel = d.status === 'indisponivel';
    const acao = indisponivel
      ? '<span class="badge-nb badge-pendente">Arquivo indisponível</span>'
      : '<button type="button" class="btn btn-outline-primary btn-sm" data-download-documento="' + d.id + '" data-nome-arquivo="' + escaparHTML(d.nome_original) + '">⬇ Baixar</button>';
    return '<div class="documento-item"><div><strong>' + escaparHTML(d.titulo) + '</strong>' +
      '<div class="small text-muted">' + escaparHTML(d.categoria) + ' · ' + escaparHTML(d.nome_original) + ' · ' + formatarDataHora(d.enviado_em) + '</div></div>' + acao + '</div>';
  }).join('');
}

async function atualizarPerfil(evento) {
  evento.preventDefault();
  const dados = {
    nome: document.getElementById('editar-nome').value.trim(),
    cpf: document.getElementById('editar-cpf').value.trim(),
    data_nascimento: document.getElementById('editar-nascimento').value,
    data_admissao: document.getElementById('editar-admissao').value,
    ala: document.getElementById('editar-ala').value.trim(),
    quarto: document.getElementById('editar-quarto').value.trim(),
    status: document.getElementById('editar-status').value,
    tipo_atendimento: document.getElementById('editar-tipo-atendimento').value.trim(),
    convenio: document.getElementById('editar-convenio').value.trim(),
    condicao_principal: document.getElementById('editar-condicao').value.trim(),
    endereco: document.getElementById('editar-endereco').value.trim(),
    rg: document.getElementById('editar-rg').value.trim(),
    observacoes: document.getElementById('editar-observacoes').value.trim()
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId, dados, evento.target, 'Perfil atualizado.', 'PUT', false);
}

async function alterarStatusAcolhido(status) {
  const textos = { alta: 'dar alta ao acolhido', inativo: 'inativar o acolhido' };
  if (textos[status] && !window.confirm('Confirma que deseja ' + textos[status] + '? O histórico será preservado.')) return;
  try {
    await apiFetch('/api/acolhidos/' + acolhidoId + '/status', {
      method: 'PATCH', body: JSON.stringify({ status })
    });
    mostrarAlerta('mensagem-perfil', 'Situação atualizada.');
    carregarPerfilCompleto();
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}

async function cadastrarAlergia(evento) {
  evento.preventDefault();
  const nome = document.getElementById('alergia-nome').value.trim();
  const existente = catalogoAlergias.find(a => a.nome.toLowerCase() === nome.toLowerCase());
  const dados = {
    alergia_id: existente?.id || null,
    nome,
    gravidade: document.getElementById('alergia-gravidade').value,
    observacoes: document.getElementById('alergia-observacoes').value.trim()
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/alergias', dados, evento.target, 'Alergia cadastrada.');
}

async function cadastrarFamiliar(evento) {
  evento.preventDefault();
  const dados = {
    nome: document.getElementById('familiar-nome').value.trim(),
    parentesco: document.getElementById('familiar-parentesco').value.trim(),
    telefone: document.getElementById('familiar-telefone').value.trim(),
    email: document.getElementById('familiar-email').value.trim(),
    contato_principal: document.getElementById('familiar-principal').checked
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/familiares', dados, evento.target, 'Familiar cadastrado.');
}

async function cadastrarPrescricao(evento) {
  evento.preventDefault();
  const dados = {
    tipo_prescricao: document.getElementById('prescricao-tipo').value,
    medicamento: document.getElementById('prescricao-medicamento').value.trim(),
    dosagem: document.getElementById('prescricao-dosagem').value.trim(),
    via_administracao: document.getElementById('prescricao-via').value.trim(),
    frequencia: document.getElementById('prescricao-frequencia').value.trim(),
    posologia: document.getElementById('prescricao-posologia').value.trim(),
    data_inicio: document.getElementById('prescricao-data-inicio').value,
    status: document.getElementById('prescricao-status').value,
    observacoes: document.getElementById('prescricao-observacoes').value.trim()
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/prescricoes', dados, evento.target, 'Prescrição cadastrada.');
}

async function alterarStatusPrescricao(id, status) {
  try {
    await apiFetch('/api/prescricoes/' + id + '/status', { method: 'PATCH', body: JSON.stringify({ status }) });
    mostrarAlerta('mensagem-perfil', 'Status da prescrição atualizado.');
    carregarPerfilCompleto();
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}

async function cadastrarNota(evento) {
  evento.preventDefault();
  const gerarAlerta = document.getElementById('nota-alerta').checked;
  const dados = {
    tipo: document.getElementById('nota-tipo').value,
    conteudo: document.getElementById('nota-conteudo').value.trim(),
    gerar_alerta: gerarAlerta,
    severidade: document.getElementById('nota-severidade').value
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/notas', dados, evento.target, gerarAlerta ? 'Nota e alerta cadastrados.' : 'Nota clínica cadastrada.');
  document.getElementById('nota-severidade').disabled = true;
}

async function resolverAlerta(id) {
  try {
    await apiFetch('/api/alertas/' + id + '/resolver', { method: 'PATCH' });
    mostrarAlerta('mensagem-perfil', 'Alerta resolvido.');
    carregarPerfilCompleto();
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}

async function cadastrarPia(evento) {
  evento.preventDefault();
  const dados = {
    versao: document.getElementById('pia-versao').value.trim(),
    situacao_atual: document.getElementById('pia-situacao').value.trim(),
    necessidades: document.getElementById('pia-necessidades').value.trim(),
    potencialidades: document.getElementById('pia-potencialidades').value.trim(),
    data_elaboracao: document.getElementById('pia-data').value,
    data_revisao: document.getElementById('pia-revisao').value || null,
    status: document.getElementById('pia-status').value,
    meta_inicial: {
      area: document.getElementById('pia-meta-area').value.trim(),
      objetivo: document.getElementById('pia-meta-objetivo').value.trim(),
      acoes: document.getElementById('pia-meta-acoes').value.trim()
    }
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/pias', dados, evento.target, 'PIA cadastrado.');
  document.getElementById('pia-data').value = hojeISO();
}

async function cadastrarPts(evento) {
  evento.preventDefault();
  const dados = {
    diagnostico_situacao: document.getElementById('pts-diagnostico').value.trim(),
    objetivos_terapeuticos: document.getElementById('pts-objetivos').value.trim(),
    avaliacao_equipe: document.getElementById('pts-avaliacao').value.trim(),
    data_reuniao: document.getElementById('pts-data').value,
    data_revisao: document.getElementById('pts-revisao').value || null,
    status: document.getElementById('pts-status').value,
    intervencao_inicial: {
      especialidade: document.getElementById('pts-especialidade').value.trim(),
      intervencao: document.getElementById('pts-intervencao').value.trim(),
      frequencia: document.getElementById('pts-frequencia').value.trim()
    }
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/pts', dados, evento.target, 'PTS cadastrado.');
  document.getElementById('pts-data').value = hojeISO();
}

async function cadastrarPlanoAlta(evento) {
  evento.preventDefault();
  const etapas = document.getElementById('alta-etapas').value.split('\n').map(x => x.trim()).filter(Boolean);
  const dados = {
    previsao_alta: document.getElementById('alta-previsao').value || null,
    tipo_alta: document.getElementById('alta-tipo').value.trim(),
    orientacoes: document.getElementById('alta-orientacoes').value.trim(),
    etapas
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/planos-alta', dados, evento.target, 'Plano de alta cadastrado.');
}

async function concluirPlanoAlta(id) {
  if (!window.confirm('Concluir o plano e alterar a situação do acolhido para Alta?')) return;
  try {
    await apiFetch('/api/planos-alta/' + id + '/concluir', { method: 'PATCH' });
    mostrarAlerta('mensagem-perfil', 'Plano concluído e alta registrada.');
    carregarPerfilCompleto();
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}

async function cadastrarBeneficio(evento) {
  evento.preventDefault();
  const dados = {
    tipo_beneficio: document.getElementById('beneficio-tipo').value,
    valor_mensal: document.getElementById('beneficio-valor').value,
    orgao_pagador: document.getElementById('beneficio-orgao').value.trim(),
    numero_beneficio: document.getElementById('beneficio-numero').value.trim(),
    data_inicio: document.getElementById('beneficio-inicio').value || null,
    data_fim: document.getElementById('beneficio-fim').value || null,
    status: document.getElementById('beneficio-status').value,
    observacoes: document.getElementById('beneficio-observacoes').value.trim()
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/beneficios', dados, evento.target, 'Benefício cadastrado.');
  document.getElementById('beneficio-inicio').value = hojeISO();
}

async function alterarStatusBeneficio(id, status) {
  try {
    await apiFetch('/api/beneficios/' + id + '/status', { method: 'PATCH', body: JSON.stringify({ status }) });
    mostrarAlerta('mensagem-perfil', 'Status do benefício atualizado.');
    carregarPerfilCompleto();
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}

async function enviarCadastro(rota, dados, formulario, mensagem, metodo = 'POST', limpar = true) {
  try {
    await apiFetch(rota, { method: metodo, body: JSON.stringify(dados) });
    mostrarAlerta('mensagem-perfil', mensagem);
    if (limpar) formulario.reset();
    await carregarPerfilCompleto();
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}

async function enviarDocumento(evento) {
  evento.preventDefault();
  const arquivo = document.getElementById('documento-arquivo').files[0];
  if (!arquivo) return;

  const formData = new FormData();
  formData.append('arquivo', arquivo);
  formData.append('titulo', document.getElementById('documento-titulo').value.trim());
  formData.append('categoria', document.getElementById('documento-categoria').value.trim());
  formData.append('escopo', 'acolhido');
  formData.append('acolhido_id', acolhidoId);

  try {
    await apiFetch('/api/documentos', { method: 'POST', body: formData });
    mostrarAlerta('mensagem-perfil', 'Documento enviado.');
    evento.target.reset();
    carregarPerfilCompleto();
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}

function nomeArquivoDoCabecalho(cabecalho, fallback) {
  if (!cabecalho) return fallback || 'documento';
  const utf8 = cabecalho.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8) return decodeURIComponent(utf8[1]);
  const comum = cabecalho.match(/filename="?([^";]+)"?/i);
  return comum ? comum[1] : (fallback || 'documento');
}

async function baixarDocumento(id, nomeFallback) {
  try {
    const resposta = await fetch(API_URL + '/api/documentos/' + id + '/download', {
      headers: { Authorization: 'Bearer ' + getToken() }
    });

    if (!resposta.ok) {
      const tipo = resposta.headers.get('content-type') || '';
      const dados = tipo.includes('application/json') ? await resposta.json() : null;
      throw new Error(dados?.erro || 'Não foi possível baixar o documento.');
    }

    const blob = await resposta.blob();
    const nome = nomeArquivoDoCabecalho(resposta.headers.get('content-disposition'), nomeFallback);
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = nome;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}
