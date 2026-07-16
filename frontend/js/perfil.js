let acolhidoId = null;

document.addEventListener('DOMContentLoaded', function () {
  acolhidoId = Number(new URLSearchParams(window.location.search).get('id'));

  if (!acolhidoId) {
    window.location.href = 'acolhidos.html';
    return;
  }

  configurarFormularios();
  carregarPerfilCompleto();
});

function configurarFormularios() {
  document.getElementById('form-familiar').addEventListener('submit', cadastrarFamiliar);
  document.getElementById('form-prescricao').addEventListener('submit', cadastrarPrescricao);
  document.getElementById('form-nota').addEventListener('submit', cadastrarNota);
  document.getElementById('form-documento-acolhido').addEventListener('submit', enviarDocumento);
  document.getElementById('prescricao-data-inicio').value = new Date().toISOString().split('T')[0];
}

async function carregarPerfilCompleto() {
  try {
    const resultados = await Promise.all([
      apiFetch('/api/acolhidos/' + acolhidoId),
      apiFetch('/api/acolhidos/' + acolhidoId + '/familiares'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/prescricoes'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/notas'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/pias'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/pts'),
      apiFetch('/api/acolhidos/' + acolhidoId + '/planos-alta'),
      apiFetch('/api/documentos?acolhido_id=' + acolhidoId)
    ]);

    renderizarCabecalho(resultados[0]);
    renderizarFamiliares(resultados[1]);
    renderizarPrescricoes(resultados[2]);
    renderizarNotas(resultados[3]);
    renderizarPiaPts(resultados[4], resultados[5]);
    renderizarPlanoAlta(resultados[6]);
    renderizarDocumentos(resultados[7]);
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
  document.getElementById('perfil-cpf').textContent = a.cpf || '—';
  document.getElementById('perfil-entrada').textContent = formatarData(a.data_admissao);
  document.getElementById('perfil-convenio').textContent = a.convenio || a.tipo_atendimento || '—';
  document.getElementById('perfil-responsavel').textContent = a.contato_principal
    ? a.contato_principal.nome + ' (' + a.contato_principal.parentesco + ')' : '—';
  document.getElementById('perfil-alergias').textContent = a.alergias.length
    ? a.alergias.map(x => x.nome).join(', ') : 'Nenhuma registrada';
}

function badgeStatusPerfil(status) {
  const map = {
    estavel: ['Estável', 'badge-ativo'], monitoramento: ['Atenção', 'badge-atencao'],
    critico: ['Crítico', 'badge-critico'], alta: ['Alta', 'badge-alta']
  };
  const item = map[status] || [status, 'badge-pendente'];
  return '<span class="badge-nb ' + item[1] + '">' + escaparHTML(item[0]) + '</span>';
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
    const ativa = p.status === 'ativa';
    return '<div class="card-nb p-3 mb-2"><div class="d-flex justify-content-between gap-2">' +
      '<div><strong>' + escaparHTML(p.medicamento) + '</strong>' +
      '<div class="small text-muted">' + escaparHTML(p.posologia) + '</div>' +
      '<div class="small text-muted">' + escaparHTML(p.profissional) + ' · ' + formatarData(p.data_inicio) + '</div></div>' +
      '<span class="badge-nb ' + (ativa ? 'badge-ativo' : 'badge-pendente') + '">' + escaparHTML(p.status) + '</span>' +
      '</div></div>';
  }).join('');
}

function renderizarNotas(lista) {
  const container = document.getElementById('lista-notas');
  if (!lista.length) {
    container.innerHTML = '<p class="text-muted">Nenhuma nota clínica cadastrada.</p>';
    return;
  }
  container.innerHTML = lista.map(function (n) {
    return '<div class="card-nb p-3 mb-2"><div class="d-flex justify-content-between flex-wrap">' +
      '<strong>' + escaparHTML(n.tipo) + '</strong><span class="small text-muted">' + formatarDataHora(n.registrado_em) + '</span></div>' +
      '<p class="mb-1 mt-2 texto-preservado">' + escaparHTML(n.conteudo) + '</p>' +
      '<span class="small text-muted">' + escaparHTML(n.profissional) +
      (n.registro_profissional ? ' · ' + escaparHTML(n.registro_profissional) : '') + '</span></div>';
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
      '<p><strong>Situação:</strong> ' + escaparHTML(p.situacao_atual) + '</p>' + metas + '</div>';
  }).join('') : '<p class="text-muted">Nenhum PIA cadastrado.</p>';

  pts.innerHTML = ptsLista.length ? ptsLista.map(function (p) {
    const intervencoes = p.intervencoes.map(function (i) {
      return '<li class="mb-2"><strong>' + escaparHTML(i.especialidade) + ':</strong> ' +
        escaparHTML(i.intervencao) + ' <span class="text-muted">(' + escaparHTML(i.responsavel_nome || i.responsavel_externo || 'Sem responsável') + ')</span></li>';
    }).join('');
    return '<div class="card-nb p-3 mb-3"><strong>PTS — ' + formatarData(p.data_reuniao) + '</strong>' +
      '<p class="mt-2"><strong>Objetivos:</strong> ' + escaparHTML(p.objetivos_terapeuticos) + '</p><ul>' + intervencoes + '</ul></div>';
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
    return '<div class="card-nb p-3"><p><strong>Previsão:</strong> ' + formatarData(p.previsao_alta) + '</p>' +
      '<p><strong>Tipo:</strong> ' + escaparHTML(p.tipo_alta || '—') + '</p>' + etapas +
      '<p class="mt-3 mb-0"><strong>Orientações:</strong> ' + escaparHTML(p.orientacoes || '—') + '</p></div>';
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
    return '<div class="documento-item"><div><strong>' + escaparHTML(d.titulo) + '</strong>' +
      '<div class="small text-muted">' + escaparHTML(d.categoria) + ' · ' + formatarDataHora(d.enviado_em) + '</div></div>' +
      '<button class="btn btn-outline-primary btn-sm" onclick="baixarDocumento(' + d.id + ')">⬇ Baixar</button></div>';
  }).join('');
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
    posologia: document.getElementById('prescricao-posologia').value.trim(),
    data_inicio: document.getElementById('prescricao-data-inicio').value
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/prescricoes', dados, evento.target, 'Prescrição cadastrada.');
}

async function cadastrarNota(evento) {
  evento.preventDefault();
  const dados = {
    tipo: document.getElementById('nota-tipo').value,
    conteudo: document.getElementById('nota-conteudo').value.trim()
  };
  await enviarCadastro('/api/acolhidos/' + acolhidoId + '/notas', dados, evento.target, 'Nota clínica cadastrada.');
}

async function enviarCadastro(rota, dados, formulario, mensagem) {
  try {
    await apiFetch(rota, { method: 'POST', body: JSON.stringify(dados) });
    mostrarAlerta('mensagem-perfil', mensagem);
    formulario.reset();
    carregarPerfilCompleto();
  } catch (erro) {
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}

async function enviarDocumento(evento) {
  evento.preventDefault();
  const formData = new FormData();
  formData.append('arquivo', document.getElementById('documento-arquivo').files[0]);
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

async function baixarDocumento(id) {
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
    mostrarAlerta('mensagem-perfil', erro.message, 'danger');
  }
}
