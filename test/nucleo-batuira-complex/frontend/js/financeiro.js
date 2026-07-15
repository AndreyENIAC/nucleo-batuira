function renderFinanceiro() {
    const aba  = APP.abaFinanceiroAtiva;
    const abas = [
      {id:'documentos', label:'📁 Documentos'},
      {id:'gastos',     label:'💰 Gastos'},
      {id:'prestacao',  label:'📊 Prestação de Contas'},
      {id:'recursos',   label:'🏛️ Recursos Administrativos'},
    ];
    const tabsHtml = abas.map(ab=>`
      <li class="nav-item">
        <button class="nav-link ${aba === ab.id ? 'active' : ''} aba-financeiro-btn" data-aba="${ab.id}">${ab.label}</button>
      </li>`).join('');
    return `
    <div class="p-4">
      <h4 class="text-primary mb-1">💼 Gestão Financeira e Administrativa</h4>
      <p class="text-muted mb-4">Documentos, gastos e prestação de contas do Núcleo Batuíra</p>
      <div class="card-nb overflow-hidden">
        <ul class="nav nav-tabs-nb px-3 pt-2 mb-0 list-unstyled d-flex gap-1 flex-wrap">${tabsHtml}</ul>
        <div class="p-4" id="conteudo-financeiro">${renderAbaFinanceiroAtual()}</div>
      </div>
    </div>`;
  }

  function renderAbaFinanceiroAtual() {
    switch (APP.abaFinanceiroAtiva) {
      case 'documentos': return renderAbaDocumentosOrg();
      case 'gastos':     return renderAbaGastos();
      case 'prestacao':  return renderAbaPrestacao();
      case 'recursos':   return renderAbaRecursos();
      default:           return renderAbaDocumentosOrg();
    }
  }

  function bindFinanceiro() {
    document.querySelectorAll('.aba-financeiro-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        APP.abaFinanceiroAtiva = btn.dataset.aba;
        document.querySelectorAll('.aba-financeiro-btn').forEach(b => b.classList.toggle('active', b === btn));
        document.getElementById('conteudo-financeiro').innerHTML = renderAbaFinanceiroAtual();
        bindAbaFinanceiroAtual();
      });
    });
    bindAbaFinanceiroAtual();
  }

  function bindAbaFinanceiroAtual() {
    if (APP.abaFinanceiroAtiva === 'documentos') bindDocumentosOrg();
  }

  function renderAbaDocumentosOrg() {
    const docs = APP.documentos;
    const itens = docs.length === 0
      ? '<p class="text-muted text-center py-4">Nenhum documento enviado.</p>'
      : docs.map(d=>`
      <div class="d-flex align-items-center gap-3 py-3 border-bottom">
        <div style="width:48px;height:48px;background:#f0fdf4;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;">📊</div>
        <div class="flex-grow-1">
          <div class="fw-medium">${d.nome}</div>
          <div class="d-flex gap-3 text-muted small flex-wrap">
            <span class="badge bg-info text-dark">${d.tipo}</span>
            <span>📅 ${d.dataUpload}</span>
            <span>💾 ${d.tamanho}</span>
          </div>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-sm btn-primary rounded-2">👁</button>
          <button class="btn btn-sm btn-success rounded-2">⬇</button>
          <button class="btn btn-sm btn-danger rounded-2 btn-del-doc-fin" data-id="${d.id}">🗑</button>
        </div>
      </div>`).join('');
    return `
    <h5 class="mb-4">📁 Documentos</h5>
    <div class="card-nb p-4 mb-4" style="background:#eff6ff;border-color:#bfdbfe;">
      <div class="d-flex gap-3 align-items-center mb-3">
        <span class="fs-3">📊</span>
        <div><div class="fw-medium">Fazer Upload de Documento</div><div class="text-muted small">Formatos: .xlsx, .xls, .csv, .pdf</div></div>
      </div>
      <input type="file" id="inp-fin-doc" accept=".xlsx,.xls,.csv,.pdf" class="d-none">
      <label for="inp-fin-doc" class="btn btn-primary rounded-3 w-100 py-3" style="cursor:pointer;">⬆️ Selecionar Arquivo</label>
    </div>
    <div class="card-nb">
      <div class="p-3 border-bottom bg-light"><h6 class="mb-0">Documentos Armazenados (${docs.length})</h6></div>
      <div class="p-3">${itens}</div>
    </div>`;
  }

  function bindDocumentosOrg() {
    document.getElementById('inp-fin-doc')?.addEventListener('change', function() {
      if (this.files.length) {
        const f = this.files[0];
        APP.documentos.push({ id:Date.now(), nome:f.name, tipo:'Documento', dataUpload:new Date().toLocaleDateString('pt-BR'), tamanho:`${Math.round(f.size/1024)} KB` });
        document.getElementById('conteudo-financeiro').innerHTML = renderAbaFinanceiroAtual();
        bindAbaFinanceiroAtual();
      }
    });
    document.querySelectorAll('.btn-del-doc-fin').forEach(btn => {
      btn.addEventListener('click', () => {
        if (confirm('Excluir este documento?')) {
          APP.documentos = APP.documentos.filter(d => d.id !== parseInt(btn.dataset.id));
          document.getElementById('conteudo-financeiro').innerHTML = renderAbaFinanceiroAtual();
          bindAbaFinanceiroAtual();
        }
      });
    });
  }

  function renderAbaGastos() {
    const total = GASTOS.reduce((s,g)=>s+g.valor,0);
    const saldo  = 2500 - total;
    return `
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <h5>💰 Gastos dos Acolhidos</h5>
      <button class="btn btn-primary rounded-3" id="btn-reg-gasto">➕ Registrar Gasto</button>
    </div>
    <div id="form-novo-gasto" class="card-nb p-4 mb-4 d-none" style="background:#eff6ff;">
      <h6 class="mb-3">Registrar Novo Gasto</h6>
      <div class="row g-3">
        <div class="col-md-6"><label class="form-label">Acolhido</label>
          <select class="form-select form-control-nb">${ACOLHIDOS.map(a=>`<option>${a.nome}</option>`).join('')}</select></div>
        <div class="col-md-6"><label class="form-label">Descrição</label>
          <input type="text" class="form-control form-control-nb" placeholder="Ex: Medicamentos"></div>
        <div class="col-md-4"><label class="form-label">Valor (R$)</label>
          <input type="number" step="0.01" class="form-control form-control-nb"></div>
        <div class="col-md-4"><label class="form-label">Data</label>
          <input type="date" class="form-control form-control-nb"></div>
        <div class="col-md-4"><label class="form-label">Categoria</label>
          <select class="form-select form-control-nb">
            <option>Saúde - Medicamentos</option><option>Alimentação</option><option>Higiene</option><option>Outros</option>
          </select></div>
        <div class="col-12"><label class="form-label">Fornecedor</label>
          <input type="text" class="form-control form-control-nb"></div>
      </div>
      <div class="d-flex gap-2 mt-3">
        <button class="btn btn-success rounded-3" onclick="alert('✅ Gasto registrado!')">✓ Salvar</button>
        <button class="btn btn-secondary rounded-3" id="btn-cancelar-gasto">Cancelar</button>
      </div>
    </div>
    <div class="row g-3 mb-4">
      <div class="col-md-4"><div class="card-nb p-3 text-center" style="background:#eff6ff;border-color:#bfdbfe;">
        <div class="text-primary small">Total</div><div class="fw-bold fs-5">${formatBRL(total)}</div></div></div>
      <div class="col-md-4"><div class="card-nb p-3 text-center" style="background:#f0fdf4;border-color:#bbf7d0;">
        <div class="text-success small">Recursos Recebidos</div><div class="fw-bold fs-5">R$ 2.500,00</div></div></div>
      <div class="col-md-4"><div class="card-nb p-3 text-center" style="background:#faf5ff;border-color:#e9d5ff;">
        <div class="text-muted small">Saldo</div><div class="fw-bold fs-5 ${saldo>=0?'text-success':'text-danger'}">${formatBRL(saldo)}</div></div></div>
    </div>
    ${GASTOS.map(g=>`
    <div class="card-nb p-4 mb-3">
      <div class="d-flex justify-content-between align-items-start mb-2 flex-wrap gap-2">
        <div><h6 class="mb-1">${g.descricao}</h6>
          <div class="text-muted small">Acolhido: ${g.acolhido}</div>
        </div>
        <span class="fw-semibold fs-5">${formatBRL(g.valor)}</span>
      </div>
      <div class="row g-2 text-muted small">
        <div class="col-md-4"><strong class="text-dark">Data:</strong> ${g.data}</div>
        <div class="col-md-4"><strong class="text-dark">Categoria:</strong> ${g.categoria}</div>
        <div class="col-md-4"><strong class="text-dark">Fornecedor:</strong> ${g.fornecedor}</div>
      </div>
    </div>`).join('')}`;
  }

  function renderAbaPrestacao() {
    return `
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <h5>📊 Prestação de Contas</h5>
      <button class="btn btn-primary rounded-3">➕ Novo Relatório</button>
    </div>
    ${PRESTACAO_CONTAS.map(p=>`
    <div class="card-nb p-4 mb-3">
      <div class="d-flex justify-content-between align-items-start mb-3 flex-wrap gap-2">
        <h6 class="mb-0">${p.mes}</h6>
        <span class="badge ${statusBadge(p.status)} badge-status">${p.status === 'Aprovado' ? '✓' : '⏳'} ${p.status}</span>
      </div>
      <div class="row g-3 mb-3">
        <div class="col-md-4"><div class="text-muted small">Total de Gastos</div><div class="fw-medium">${formatBRL(p.totalGastos)}</div></div>
        <div class="col-md-4"><div class="text-muted small">Recursos Recebidos</div><div class="fw-medium">${formatBRL(p.recursosRecebidos)}</div></div>
        <div class="col-md-4"><div class="text-muted small">Saldo</div><div class="fw-medium text-success">${formatBRL(p.saldo)}</div></div>
      </div>
      <button class="btn btn-primary btn-sm rounded-3">📥 Baixar Relatório</button>
    </div>`).join('')}`;
  }

  function renderAbaRecursos() {
    const recursos = RECURSOS_ADMIN.map(r=>`
      <div class="d-flex justify-content-between align-items-center p-3 border-bottom flex-wrap gap-2">
        <div><div class="fw-medium">${r.nome}</div>
          <div class="text-muted small">${r.tipo} · Validade: ${r.validade}</div>
        </div>
        <div class="d-flex gap-2 align-items-center">
          <span class="badge ${statusBadge(r.status)} badge-status">${r.status}</span>
          <button class="btn btn-link btn-sm">Ver</button>
        </div>
      </div>`).join('');
    const beneficios = BENEFICIOS.map(b=>`
      <div class="d-flex justify-content-between align-items-center p-3 border-bottom flex-wrap gap-2">
        <div><div class="fw-medium">${b.acolhido}</div>
          <div class="text-muted small">${b.beneficio}</div>
        </div>
        <div class="d-flex gap-2 align-items-center">
          <span class="fw-medium">${formatBRL(b.valor)}/mês</span>
          <span class="badge bg-success badge-status">${b.status}</span>
        </div>
      </div>`).join('');
    return `
    <h5 class="mb-4">🏛️ Recursos Administrativos</h5>
    <div class="card-nb mb-4">
      <div class="p-3 border-bottom d-flex justify-content-between align-items-center bg-light">
        <h6 class="mb-0">Documentação Institucional</h6>
        <button class="btn btn-primary btn-sm rounded-3">➕ Adicionar Documento</button>
      </div>
      <div>${recursos}</div>
    </div>
    <div class="card-nb">
      <div class="p-3 border-bottom bg-light"><h6 class="mb-0">Benefícios e Auxílios dos Acolhidos</h6></div>
      <div>${beneficios}</div>
    </div>`;
  }

  document.addEventListener('click', function(e) {
    if (e.target.id === 'btn-reg-gasto') document.getElementById('form-novo-gasto')?.classList.toggle('d-none');
    if (e.target.id === 'btn-cancelar-gasto') document.getElementById('form-novo-gasto')?.classList.add('d-none');
  });
