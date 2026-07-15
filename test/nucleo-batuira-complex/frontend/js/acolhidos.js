function renderListaAcolhidos() {
    const lista = ACOLHIDOS.map(a => `
      <div class="card-nb p-4 mb-3">
        <div class="d-flex align-items-start gap-3 flex-wrap">
          <div class="avatar-acolhido">👤</div>
          <div class="flex-grow-1">
            <div class="d-flex align-items-center gap-2 flex-wrap mb-1">
              <h6 class="mb-0 fw-semibold">${a.nome}</h6>
              <span class="badge ${statusBadge(a.status)} badge-status">${a.status}</span>
            </div>
            <div class="text-muted small mb-2">${a.idade} anos · Quarto ${a.quarto} · ${a.condicao}</div>
            <div class="d-flex gap-3 small text-muted flex-wrap">
              <span>📋 ${a.tipo}</span>
              <span>📅 Última consulta: ${a.ultimaConsulta}</span>
            </div>
          </div>
          <button class="btn btn-primary btn-sm rounded-3 btn-ver-perfil" data-id="${a.id}">Ver Perfil →</button>
        </div>
      </div>`).join('');

    return `
    <div class="p-4">
      <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <div>
          <h4 class="text-primary mb-1">👥 Acolhidos</h4>
          <p class="text-muted mb-0">${ACOLHIDOS.length} residentes cadastrados</p>
        </div>
        <button class="btn btn-primary rounded-3 px-4" id="btn-novo-acolhido">➕ Novo Acolhido</button>
      </div>

      <div id="form-novo-acolhido" class="card-nb p-4 mb-4 d-none" style="background:#eff6ff;">
        <h6 class="mb-3">Novo Acolhido</h6>
        <div class="row g-3">
          <div class="col-md-6"><label class="form-label">Nome Completo</label>
            <input type="text" class="form-control form-control-nb" placeholder="Nome completo"></div>
          <div class="col-md-3"><label class="form-label">Idade</label>
            <input type="number" class="form-control form-control-nb" placeholder="Ex: 78"></div>
          <div class="col-md-3"><label class="form-label">Quarto</label>
            <input type="text" class="form-control form-control-nb" placeholder="Ex: 101-A"></div>
          <div class="col-md-6"><label class="form-label">Condição Principal</label>
            <input type="text" class="form-control form-control-nb" placeholder="Diagnóstico principal"></div>
          <div class="col-md-6"><label class="form-label">Tipo de Atendimento</label>
            <select class="form-select form-control-nb">
              <option>Plano Privado</option><option>Convênio SUS</option><option>Particular</option>
            </select></div>
        </div>
        <div class="d-flex gap-2 mt-3">
          <button class="btn btn-success rounded-3" onclick="alert('✅ Acolhido cadastrado! Em produção: salvo no banco.')">✓ Salvar</button>
          <button class="btn btn-secondary rounded-3" id="btn-cancel-acolhido">Cancelar</button>
        </div>
      </div>

      <div class="mb-3 d-flex gap-2 flex-wrap">
        <input type="text" id="busca-acolhido" class="form-control form-control-nb" style="max-width:280px;" placeholder="🔍 Buscar por nome...">
        <select id="filtro-tipo" class="form-select form-control-nb" style="max-width:180px;">
          <option value="">Todos os tipos</option>
          <option>Plano Privado</option><option>Convênio SUS</option><option>Particular</option>
        </select>
        <select id="filtro-status" class="form-select form-control-nb" style="max-width:160px;">
          <option value="">Todos os status</option>
          <option>Ativo</option><option>Crítico</option><option>Atenção</option><option>Alta Méd.</option>
        </select>
      </div>

      <div id="lista-acolhidos">${lista}</div>
    </div>`;
  }

  function bindListaAcolhidos() {
    document.getElementById('btn-novo-acolhido')?.addEventListener('click', () => {
      const f = document.getElementById('form-novo-acolhido');
      f?.classList.toggle('d-none');
    });
    document.getElementById('btn-cancel-acolhido')?.addEventListener('click', () => {
      document.getElementById('form-novo-acolhido')?.classList.add('d-none');
    });
    document.querySelectorAll('.btn-ver-perfil').forEach(btn => {
      btn.addEventListener('click', () => navegar('perfil', { acolhidoId: parseInt(btn.dataset.id) }));
    });
    const filtrar = () => {
      const busca   = document.getElementById('busca-acolhido').value.toLowerCase();
      const tipo    = document.getElementById('filtro-tipo').value;
      const status  = document.getElementById('filtro-status').value;
      const filtrado = ACOLHIDOS.filter(a =>
        (!busca   || a.nome.toLowerCase().includes(busca)) &&
        (!tipo    || a.tipo === tipo) &&
        (!status  || a.status === status)
      );
      document.getElementById('lista-acolhidos').innerHTML = filtrado.length
        ? filtrado.map(a=>`
          <div class="card-nb p-4 mb-3">
            <div class="d-flex align-items-start gap-3 flex-wrap">
              <div class="avatar-acolhido">👤</div>
              <div class="flex-grow-1">
                <div class="d-flex align-items-center gap-2 flex-wrap mb-1">
                  <h6 class="mb-0 fw-semibold">${a.nome}</h6>
                  <span class="badge ${statusBadge(a.status)} badge-status">${a.status}</span>
                </div>
                <div class="text-muted small mb-2">${a.idade} anos · Quarto ${a.quarto} · ${a.condicao}</div>
                <div class="d-flex gap-3 small text-muted flex-wrap">
                  <span>📋 ${a.tipo}</span>
                  <span>📅 Última consulta: ${a.ultimaConsulta}</span>
                </div>
              </div>
              <button class="btn btn-primary btn-sm rounded-3 btn-ver-perfil" data-id="${a.id}">Ver Perfil →</button>
            </div>
          </div>`).join('')
        : '<p class="text-muted text-center py-4">Nenhum acolhido encontrado.</p>';
      document.querySelectorAll('.btn-ver-perfil').forEach(btn => {
        btn.addEventListener('click', () => navegar('perfil', { acolhidoId: parseInt(btn.dataset.id) }));
      });
    };
    document.getElementById('busca-acolhido')?.addEventListener('input', filtrar);
    document.getElementById('filtro-tipo')?.addEventListener('change', filtrar);
    document.getElementById('filtro-status')?.addEventListener('change', filtrar);
  }

  function renderPerfilAcolhido() {
    const a   = PERFIL_ACOLHIDO;
    const aba = APP.abaPerfilAtiva;
    const isFinanceiro = APP.userRole === 'financial';

    const abas = isFinanceiro
      ? [
          {id:'documentos', label:'📁 Documentos'},
          {id:'gastos',     label:'💰 Gastos'},
          {id:'prestacao',  label:'📊 Prestação'},
          {id:'recursos',   label:'🏛️ Recursos'},
        ]
      : [
          {id:'prescricoes', label:'💊 Prescrições'},
          {id:'notas',       label:'📋 Notas Clínicas'},
          {id:'piaPts',      label:'📌 PIA / PTS'},
          {id:'familia',     label:'👨‍👩‍👧 Vínculos'},
          {id:'alta',        label:'🏠 Plano de Alta'},
          {id:'documentos',  label:'📁 Documentos'},
        ];

    const tabsHtml = abas.map(ab=>`
      <li class="nav-item">
        <button class="nav-link ${aba === ab.id ? 'active' : ''} aba-perfil-btn" data-aba="${ab.id}">${ab.label}</button>
      </li>`).join('');

    return `
    <div class="p-4">
      <button class="btn btn-link text-primary px-0 mb-3" id="btn-voltar-lista">← Voltar para lista</button>

      <div class="card-nb p-4 mb-4">
        <div class="d-flex gap-4 align-items-start flex-wrap">
          <div class="avatar-acolhido" style="width:80px;height:80px;font-size:2.5rem;">👤</div>
          <div class="flex-grow-1">
            <div class="d-flex align-items-center gap-2 flex-wrap mb-1">
              <h4 class="mb-0">${a.nome}</h4>
              <span class="badge ${statusBadge(a.status)} badge-status">${a.status}</span>
            </div>
            <p class="text-muted mb-2">${a.condicao} · ${a.idade} anos · Quarto ${a.quarto}</p>
            <div class="row g-2 small text-muted">
              <div class="col-md-3"><strong class="text-dark">CPF:</strong> ${a.cpf}</div>
              <div class="col-md-3"><strong class="text-dark">Entrada:</strong> ${a.dataEntrada}</div>
              <div class="col-md-3"><strong class="text-dark">Convênio:</strong> ${a.convenio}</div>
              <div class="col-md-3"><strong class="text-dark">Responsável:</strong> ${a.responsavel}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="card-nb overflow-hidden">
        <ul class="nav nav-tabs-nb px-3 pt-2 mb-0 list-unstyled d-flex gap-1 flex-wrap">${tabsHtml}</ul>
        <div class="p-4" id="conteudo-aba">${renderAbaPerfilAtual()}</div>
      </div>
    </div>`;
  }

  function renderAbaPerfilAtual() {
    switch (APP.abaPerfilAtiva) {
      case 'prescricoes': return renderAbaPrescricoes();
      case 'notas':       return renderAbaNotas();
      case 'piaPts':      return renderAbaPiaPts();
      case 'familia':     return renderAbaFamilia();
      case 'alta':        return renderAbaAlta();
      case 'documentos':  return renderAbaDocumentos();
      case 'gastos':      return renderAbaGastosAcolhido();
      case 'prestacao':   return renderAbaPrestacaoAcolhido();
      case 'recursos':    return renderAbaRecursosAcolhido();
      default:            return renderAbaPrescricoes();
    }
  }

  function bindPerfilAcolhido() {
    document.getElementById('btn-voltar-lista')?.addEventListener('click', () => {
      APP.acolhidoSelecionado = null;
      navegar('acolhidos');
    });
    document.querySelectorAll('.aba-perfil-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        APP.abaPerfilAtiva = btn.dataset.aba;
        document.querySelectorAll('.aba-perfil-btn').forEach(b => b.classList.toggle('active', b === btn));
        document.getElementById('conteudo-aba').innerHTML = renderAbaPerfilAtual();
        bindAbaAtual();
      });
    });
    bindAbaAtual();
  }

  function bindAbaAtual() {
    if (APP.abaPerfilAtiva === 'familia')    bindAbaFamilia();
    if (APP.abaPerfilAtiva === 'documentos') bindAbaDocumentos();
  }

  function renderAbaPrescricoes() {
    return `
    <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
      <h5>💊 Prescrições Médicas</h5>
      <button class="btn btn-primary btn-sm rounded-3" onclick="alert('Em produção: abre formulário de nova prescrição.')">➕ Nova Prescrição</button>
    </div>
    ${PRESCRICOES.map(p=>`
    <div class="card-nb p-4 mb-3">
      <div class="d-flex align-items-start justify-content-between flex-wrap gap-2">
        <div>
          <h6 class="mb-1">${p.medicamento}</h6>
          <div class="text-muted small mb-1">Posologia: ${p.posologia}</div>
          <div class="text-muted small">Prescrito por: ${p.prescrito} · ${p.data}</div>
        </div>
        <span class="badge ${p.vigente ? 'bg-success' : 'bg-secondary'} badge-status">${p.vigente ? '✓ Vigente' : 'Encerrado'}</span>
      </div>
    </div>`).join('')}`;
  }

  function renderAbaNotas() {
    return `
    <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
      <h5>📋 Notas Clínicas</h5>
      <button class="btn btn-primary btn-sm rounded-3" onclick="alert('Em produção: abre editor de nota clínica.')">➕ Nova Nota</button>
    </div>
    ${NOTAS_CLINICAS.map(n=>`
    <div class="card-nb p-4 mb-3">
      <div class="d-flex justify-content-between mb-2 flex-wrap gap-2">
        <span class="badge bg-primary badge-status">${n.tipo}</span>
        <span class="text-muted small">${n.data} · ${n.profissional} · ${n.crm}</span>
      </div>
      <p class="mb-0 small">${n.conteudo}</p>
    </div>`).join('')}`;
  }

  function renderAbaPiaPts() {
    const sub = APP.abaPiaPtsAtiva;
    return `
    <div class="d-flex gap-2 mb-4">
      <button class="btn ${sub==='pia' ? 'btn-primary' : 'btn-outline-primary'} rounded-3 sub-tab-btn" data-sub="pia">📌 PIA</button>
      <button class="btn ${sub==='pts' ? 'btn-primary' : 'btn-outline-primary'} rounded-3 sub-tab-btn" data-sub="pts">🔗 PTS</button>
    </div>
    <div id="sub-conteudo">${sub === 'pia' ? renderPIA() : renderPTS()}</div>`;
  }

  function renderPIA() {
    const pia = APP.pias[0];
    if (!pia) return '<p class="text-muted">Nenhum PIA cadastrado.</p>';
    return `
    <div class="card-nb p-4 mb-3" style="background:#eff6ff;border-color:#bfdbfe;">
      <div class="row g-2 small">
        <div class="col-md-4"><strong>Versão:</strong> ${pia.versao}</div>
        <div class="col-md-4"><strong>Elaboração:</strong> ${pia.dataElaboracao}</div>
        <div class="col-md-4"><strong>Próx. Revisão:</strong> ${pia.proximaRevisao}</div>
      </div>
      <div class="mt-2 small"><strong>Equipe:</strong> ${pia.equipe}</div>
    </div>
    <h6 class="mb-3">Metas</h6>
    ${pia.metas.map(m=>`
    <div class="card-nb p-3 mb-3">
      <div class="d-flex justify-content-between mb-2 flex-wrap gap-1">
        <span class="fw-medium">${m.area}: ${m.descricao}</span>
        <span class="badge bg-primary badge-status">${m.progresso}%</span>
      </div>
      <div class="progresso-barra mb-2"><div class="progresso-fill" style="width:${m.progresso}%;"></div></div>
      <div class="d-flex gap-3 small text-muted flex-wrap">
        <span>Prazo: ${m.prazo}</span><span>Status: ${m.status}</span>
      </div>
    </div>`).join('')}`;
  }

  function renderPTS() {
    const pts = APP.ptsList[0];
    if (!pts) return '<p class="text-muted">Nenhum PTS cadastrado.</p>';
    return `
    <div class="card-nb p-4 mb-3" style="background:#f0fdf4;border-color:#bbf7d0;">
      <div class="row g-2 small">
        <div class="col-md-4"><strong>Reunião:</strong> ${pts.dataReuniao}</div>
        <div class="col-md-4"><strong>Próxima:</strong> ${pts.proximaReuniao}</div>
      </div>
      <div class="mt-2 small"><strong>Objetivo:</strong> ${pts.objetivo}</div>
    </div>
    <h6 class="mb-3">Intervenções por Profissional</h6>
    ${pts.intervencoes.map(i=>`
    <div class="card-nb p-3 mb-2">
      <div class="fw-medium">${i.profissional} — ${i.responsavel}</div>
      <div class="text-muted small mt-1">${i.descricao}</div>
    </div>`).join('')}`;
  }

  function renderAbaFamilia() {
    const familiar = APP.familiares[0];
    const visitasHtml = APP.visitas.map(v=>`
      <div class="d-flex gap-3 py-3 border-bottom flex-wrap">
        <div class="text-center" style="min-width:60px;">
          <div class="fw-bold small text-primary">${v.data}</div>
          <div class="text-muted" style="font-size:.7rem;">${v.horario}</div>
        </div>
        <div><div class="fw-medium small">${v.familiar}</div>
          <div class="text-muted small">${v.observacoes}</div>
        </div>
      </div>`).join('');

    return `
    <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
      <h5>👨‍👩‍👧 Vínculos Familiares</h5>
      <button class="btn btn-primary btn-sm rounded-3" id="btn-add-familiar">➕ Adicionar Familiar</button>
    </div>

    <div id="form-familiar" class="card-nb p-4 mb-3 d-none" style="background:#eff6ff;">
      <h6 class="mb-3">Novo Familiar/Responsável</h6>
      <div class="row g-3">
        <div class="col-md-6"><label class="form-label">Nome</label>
          <input type="text" id="fam-nome" class="form-control form-control-nb"></div>
        <div class="col-md-6"><label class="form-label">Parentesco</label>
          <input type="text" id="fam-parent" class="form-control form-control-nb" placeholder="Ex: Filho(a)"></div>
        <div class="col-md-6"><label class="form-label">Telefone</label>
          <input type="text" id="fam-tel" class="form-control form-control-nb"></div>
        <div class="col-md-6"><label class="form-label">E-mail</label>
          <input type="email" id="fam-email" class="form-control form-control-nb"></div>
      </div>
      <div class="d-flex gap-2 mt-3">
        <button class="btn btn-success rounded-3" id="btn-salvar-familiar">✓ Salvar</button>
        <button class="btn btn-secondary rounded-3" id="btn-cancel-familiar">Cancelar</button>
      </div>
    </div>

    ${familiar ? `
    <div class="card-nb p-4 mb-4">
      <div class="d-flex align-items-start gap-3 flex-wrap">
        <div class="avatar-acolhido" style="width:56px;height:56px;font-size:1.5rem;">👤</div>
        <div class="flex-grow-1">
          <div class="d-flex align-items-center gap-2 mb-1 flex-wrap">
            <h6 class="mb-0">${familiar.nome}</h6>
            ${familiar.responsavelLegal ? '<span class="badge bg-primary badge-status">Responsável Legal</span>' : ''}
          </div>
          <div class="text-muted small">${familiar.parentesco}</div>
          <div class="row g-2 small mt-2">
            <div class="col-md-6"><strong>Tel:</strong> ${familiar.telefone}</div>
            <div class="col-md-6"><strong>E-mail:</strong> ${familiar.email}</div>
            <div class="col-md-6"><strong>Última Visita:</strong> ${familiar.ultimaVisita}</div>
            <div class="col-md-6"><strong>Frequência:</strong> ${familiar.frequencia}</div>
          </div>
        </div>
      </div>
    </div>` : ''}

    <h6 class="mb-3">📅 Registro de Visitas</h6>
    <div class="card-nb">${visitasHtml}</div>`;
  }

  function bindAbaFamilia() {
    document.getElementById('btn-add-familiar')?.addEventListener('click', () => {
      document.getElementById('form-familiar')?.classList.toggle('d-none');
    });
    document.getElementById('btn-cancel-familiar')?.addEventListener('click', () => {
      document.getElementById('form-familiar')?.classList.add('d-none');
    });
    document.getElementById('btn-salvar-familiar')?.addEventListener('click', () => {
      const nome   = document.getElementById('fam-nome').value.trim();
      const parent = document.getElementById('fam-parent').value.trim();
      const tel    = document.getElementById('fam-tel').value.trim();
      const email  = document.getElementById('fam-email').value.trim();
      if (!nome) { alert('Informe o nome do familiar.'); return; }
      APP.familiares.push({ id: Date.now(), acolhidoId:1, nome, parentesco:parent||'—',
        telefone:tel||'—', email:email||'—', responsavelLegal:false, autorizadoVisita:true,
        ultimaVisita:'—', frequencia:'—' });
      document.getElementById('conteudo-aba').innerHTML = renderAbaPerfilAtual();
      bindAbaAtual();
    });

    // Sub-tabs PIA/PTS (quando aplicável)
    document.querySelectorAll('.sub-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        APP.abaPiaPtsAtiva = btn.dataset.sub;
        document.getElementById('sub-conteudo').innerHTML = APP.abaPiaPtsAtiva === 'pia' ? renderPIA() : renderPTS();
        document.querySelectorAll('.sub-tab-btn').forEach(b => {
          b.className = `btn ${b.dataset.sub === APP.abaPiaPtsAtiva ? 'btn-primary' : 'btn-outline-primary'} rounded-3 sub-tab-btn`;
        });
      });
    });
  }

  function renderAbaAlta() {
    const p = PLANO_ALTA;
    const statusIcon = s => s==='concluido' ? '✅' : s==='em_andamento' ? '🔄' : '⏳';
    return `
    <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
      <h5>🏠 Plano de Alta</h5>
      <button class="btn btn-primary btn-sm rounded-3" onclick="alert('Em produção: edita o plano de alta.')">✏️ Editar</button>
    </div>
    <div class="card-nb p-4 mb-3" style="background:#eff6ff;border-color:#bfdbfe;">
      <div class="row g-2 small">
        <div class="col-md-4"><strong>Previsão:</strong> ${p.previsao}</div>
        <div class="col-md-4"><strong>Tipo:</strong> ${p.tipo}</div>
        <div class="col-md-4"><strong>Responsável:</strong> ${p.responsavel}</div>
      </div>
    </div>
    <h6 class="mb-3">Marcos e Critérios</h6>
    ${p.marcos.map(m=>`
    <div class="d-flex align-items-center gap-3 py-2 border-bottom">
      <span>${statusIcon(m.status)}</span>
      <span class="small flex-grow-1">${m.descricao}</span>
      <span class="badge ${m.status==='concluido'?'bg-success':m.status==='em_andamento'?'bg-warning text-dark':'bg-secondary'} badge-status">${m.status.replace('_',' ')}</span>
    </div>`).join('')}
    <div class="card-nb p-3 mt-3" style="background:#f0fdf4;border-color:#bbf7d0;">
      <strong class="small">Orientações pós-alta:</strong>
      <p class="small mb-0 mt-1">${p.orientacoes}</p>
    </div>`;
  }

  function renderAbaDocumentos() {
    const docs = APP.documentos;
    const itens = docs.length === 0
      ? '<p class="text-muted text-center py-4">Nenhum documento enviado.</p>'
      : docs.map(d=>`
      <div class="d-flex align-items-center gap-3 py-3 border-bottom">
        <div style="width:44px;height:44px;background:#eff6ff;border-radius:10px;display:flex;align-items:center;justify-content:center;">📊</div>
        <div class="flex-grow-1">
          <div class="fw-medium small">${d.nome}</div>
          <div class="text-muted" style="font-size:.75rem;">${d.tipo} · ${d.dataUpload} · ${d.tamanho}</div>
        </div>
        <div class="d-flex gap-1">
          <button class="btn btn-sm btn-outline-primary rounded-2">👁</button>
          <button class="btn btn-sm btn-outline-success rounded-2">⬇</button>
          <button class="btn btn-sm btn-outline-danger rounded-2 btn-del-doc" data-id="${d.id}">🗑</button>
        </div>
      </div>`).join('');

    return `
    <div class="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
      <h5>📁 Documentos</h5>
    </div>
    <div class="card-nb p-4 mb-3" style="background:#eff6ff;border-color:#bfdbfe;">
      <input type="file" id="inp-doc" accept=".xlsx,.xls,.csv,.pdf" class="d-none">
      <label for="inp-doc" class="btn btn-primary w-100 py-3 rounded-3" style="cursor:pointer;">⬆️ Fazer Upload de Documento</label>
    </div>
    <div class="card-nb p-3">${itens}</div>`;
  }

  function bindAbaDocumentos() {
    document.getElementById('inp-doc')?.addEventListener('change', function() {
      if (this.files.length) {
        const f = this.files[0];
        APP.documentos.push({ id:Date.now(), nome:f.name, tipo:'Documento', dataUpload:new Date().toLocaleDateString('pt-BR'), tamanho:`${Math.round(f.size/1024)} KB` });
        document.getElementById('conteudo-aba').innerHTML = renderAbaPerfilAtual();
        bindAbaAtual();
      }
    });
    document.querySelectorAll('.btn-del-doc').forEach(btn => {
      btn.addEventListener('click', () => {
        if (confirm('Excluir este documento?')) {
          APP.documentos = APP.documentos.filter(d => d.id !== parseInt(btn.dataset.id));
          document.getElementById('conteudo-aba').innerHTML = renderAbaPerfilAtual();
          bindAbaAtual();
        }
      });
    });
  }

  function renderAbaGastosAcolhido() {
    const gastos = GASTOS.filter(g => g.acolhido === PERFIL_ACOLHIDO.nome);
    const total  = gastos.reduce((s,g)=>s+g.valor,0);
    return `
    <h5 class="mb-3">💰 Gastos — ${PERFIL_ACOLHIDO.nome}</h5>
    ${gastos.map(g=>`
    <div class="card-nb p-3 mb-3">
      <div class="d-flex justify-content-between flex-wrap gap-2">
        <div><div class="fw-medium small">${g.descricao}</div>
          <div class="text-muted" style="font-size:.75rem;">${g.data} · ${g.categoria}</div>
        </div>
        <span class="fw-semibold">${formatBRL(g.valor)}</span>
      </div>
    </div>`).join('')}
    ${gastos.length === 0 ? '<p class="text-muted">Nenhum gasto registrado.</p>' : `<div class="fw-bold text-end">Total: ${formatBRL(total)}</div>`}`;
  }

  function renderAbaPrestacaoAcolhido() {
    return `
    <h5 class="mb-3">📊 Prestação de Contas</h5>
    ${PRESTACAO_CONTAS.map(p=>`
    <div class="card-nb p-4 mb-3">
      <div class="d-flex justify-content-between mb-2 flex-wrap gap-2">
        <h6 class="mb-0">${p.mes}</h6>
        <span class="badge ${statusBadge(p.status)} badge-status">${p.status}</span>
      </div>
      <div class="row g-2 small">
        <div class="col-md-4">Gastos: ${formatBRL(p.totalGastos)}</div>
        <div class="col-md-4">Recursos: ${formatBRL(p.recursosRecebidos)}</div>
        <div class="col-md-4 text-success">Saldo: ${formatBRL(p.saldo)}</div>
      </div>
    </div>`).join('')}`;
  }

  function renderAbaRecursosAcolhido() {
    const bens = BENEFICIOS.filter(b => b.acolhido === PERFIL_ACOLHIDO.nome);
    return `
    <h5 class="mb-3">🏛️ Benefícios e Recursos</h5>
    ${bens.length === 0 ? '<p class="text-muted">Nenhum benefício cadastrado.</p>' : bens.map(b=>`
    <div class="card-nb p-4 mb-3">
      <div class="d-flex justify-content-between flex-wrap gap-2">
        <div><div class="fw-medium">${b.beneficio}</div>
          <div class="text-muted small">${b.acolhido}</div>
        </div>
        <div class="text-end">
          <div class="fw-semibold">${formatBRL(b.valor)}/mês</div>
          <span class="badge bg-success badge-status">${b.status}</span>
        </div>
      </div>
    </div>`).join('')}`;
  }
