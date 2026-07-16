function renderDashboard() {
    switch (APP.userRole) {
      case 'admin':     return renderDashboardAdmin();
      case 'technical': return renderDashboardTecnico();
      case 'financial': return renderDashboardFinanceiro();
      case 'staff':     return renderDashboardFuncionario();
      default:          return renderDashboardAdmin();
    }
  }
  function bindDashboard() {}

  function renderDashboardAdmin() {
    return `
    <div class="p-4">
      <h4 class="text-primary mb-1">📊 Dashboard Administrativo</h4>
      <p class="text-muted mb-4">Visão geral do Núcleo Batuíra</p>
      <div class="row g-3 mb-4">
        ${[
          {icon:'👥',label:'Acolhidos Ativos',value:'128',sub:'8 em observação',color:'#eff6ff',border:'#bfdbfe',text:'#1e40af'},
          {icon:'👨‍⚕️',label:'Usuários do Sistema',value:'15', sub:'3 online agora',color:'#f0fdf4',border:'#bbf7d0',text:'#166534'},
          {icon:'💰',label:'Receita Mensal',value:'R$ 58k',sub:'Junho/2026',color:'#fefce8',border:'#fef08a',text:'#854d0e'},
          {icon:'⚠️',label:'Alertas Críticos',value:'3',  sub:'Requerem atenção',color:'#fff7ed',border:'#fed7aa',text:'#c2410c'},
        ].map(c=>`
        <div class="col-6 col-lg-3">
          <div class="card-nb p-3" style="background:${c.color};border-color:${c.border};">
            <div class="d-flex align-items-start justify-content-between mb-2">
              <span style="font-size:1.8rem;">${c.icon}</span>
            </div>
            <div class="fw-bold fs-3" style="color:${c.text};">${c.value}</div>
            <div class="fw-medium small" style="color:${c.text};">${c.label}</div>
            <div class="text-muted" style="font-size:.75rem;">${c.sub}</div>
          </div>
        </div>`).join('')}
      </div>

      <div class="row g-4">
        <div class="col-lg-6">
          <div class="card-nb p-4">
            <h6 class="mb-3">📅 Agenda de Hoje</h6>
            ${AGENDA.slice(0,3).map(e=>`
            <div class="d-flex gap-3 mb-3">
              <div class="text-center" style="min-width:48px;">
                <div class="fw-bold text-primary">${e.hora}</div>
                <div class="text-muted" style="font-size:.7rem;">${e.tipo}</div>
              </div>
              <div><div class="fw-medium">${e.titulo}</div>
                <div class="text-muted small">${e.local}</div>
              </div>
            </div>`).join('')}
          </div>
        </div>
        <div class="col-lg-6">
          <div class="card-nb p-4">
            <h6 class="mb-3">👥 Situação dos Acolhidos</h6>
            ${[
              {label:'Ativos',    v:118,total:128,color:'#22c55e'},
              {label:'Atenção',   v:7,  total:128,color:'#f59e0b'},
              {label:'Crítico',   v:3,  total:128,color:'#ef4444'},
            ].map(b=>`
            <div class="mb-3">
              <div class="d-flex justify-content-between mb-1">
                <span class="small">${b.label}</span>
                <span class="small fw-medium">${b.v} / ${b.total}</span>
              </div>
              <div class="progresso-barra">
                <div class="progresso-fill" style="width:${Math.round(b.v/b.total*100)}%;background:${b.color};"></div>
              </div>
            </div>`).join('')}
          </div>
        </div>
      </div>
    </div>`;
  }

  function renderDashboardTecnico() {
    return `
    <div class="p-4">
      <h4 class="text-primary mb-1">🩺 Dashboard Equipe Técnica</h4>
      <p class="text-muted mb-4">Resumo clínico e assistencial</p>
      <div class="row g-3 mb-4">
        ${[
          {icon:'🏥',label:'Acolhidos',         value:'128',color:'#eff6ff',border:'#bfdbfe',text:'#1e40af'},
          {icon:'⚠️',label:'Estado Crítico',     value:'3',  color:'#fff1f2',border:'#fecdd3',text:'#be123c'},
          {icon:'💊',label:'Medicações Hoje',    value:'47', color:'#f0fdf4',border:'#bbf7d0',text:'#166534'},
          {icon:'📅',label:'Consultas Hoje',     value:'8',  color:'#faf5ff',border:'#e9d5ff',text:'#6b21a8'},
        ].map(c=>`
        <div class="col-6 col-lg-3">
          <div class="card-nb p-3" style="background:${c.color};border-color:${c.border};">
            <span style="font-size:1.8rem;">${c.icon}</span>
            <div class="fw-bold fs-3 mt-1" style="color:${c.text};">${c.value}</div>
            <div class="fw-medium small" style="color:${c.text};">${c.label}</div>
          </div>
        </div>`).join('')}
      </div>

      <div class="row g-4 mb-4">
        <div class="col-lg-6">
          <div class="card-nb p-4">
            <h6 class="mb-3">🚨 Alertas Críticos</h6>
            ${[
              {nome:'Pedro Oliveira', alerta:'Pressão elevada: 180/110 mmHg', cor:'danger'},
              {nome:'Carlos Mendes',  alerta:'Glicemia: 320 mg/dL',           cor:'warning'},
              {nome:'Maria Silva',    alerta:'Queda leve ontem à noite',       cor:'info'},
            ].map(a=>`
            <div class="alert alert-${a.cor} py-2 px-3 mb-2">
              <strong>${a.nome}</strong><br><span class="small">${a.alerta}</span>
            </div>`).join('')}
          </div>
        </div>
        <div class="col-lg-6">
          <div class="card-nb p-4">
            <h6 class="mb-3">📅 Consultas de Hoje</h6>
            ${AGENDA.filter(e=>e.tipo==='Médica'||e.tipo==='Reabilitação').map(e=>`
            <div class="d-flex align-items-center gap-3 mb-3">
              <span class="badge bg-primary rounded-pill px-2">${e.hora}</span>
              <div><div class="fw-medium small">${e.titulo}</div>
                <div class="text-muted" style="font-size:.75rem;">${e.local}</div>
              </div>
            </div>`).join('')}
          </div>
        </div>
      </div>
    </div>`;
  }

  function renderDashboardFinanceiro() {
    const totalGastos = GASTOS.reduce((s,g)=>s+g.valor,0);
    return `
    <div class="p-4">
      <h4 class="text-primary mb-1">💼 Dashboard Financeiro</h4>
      <p class="text-muted mb-4">Resumo financeiro e administrativo</p>
      <div class="row g-3 mb-4">
        ${[
          {icon:'💰',label:'Receita Mensal',  value:'R$ 58.000',color:'#f0fdf4',border:'#bbf7d0',text:'#166534'},
          {icon:'📊',label:'Despesas Mensais',value:'R$ 45.200',color:'#fff7ed',border:'#fed7aa',text:'#c2410c'},
          {icon:'🏦',label:'Saldo em Conta',  value:'R$ 12.800',color:'#eff6ff',border:'#bfdbfe',text:'#1e40af'},
          {icon:'📋',label:'Docs Pendentes',  value:'3',         color:'#fefce8',border:'#fef08a',text:'#854d0e'},
        ].map(c=>`
        <div class="col-6 col-lg-3">
          <div class="card-nb p-3" style="background:${c.color};border-color:${c.border};">
            <span style="font-size:1.8rem;">${c.icon}</span>
            <div class="fw-bold fs-4 mt-1" style="color:${c.text};">${c.value}</div>
            <div class="fw-medium small" style="color:${c.text};">${c.label}</div>
          </div>
        </div>`).join('')}
      </div>

      <div class="card-nb p-4 mb-4">
        <h6 class="mb-3">💸 Gastos Recentes</h6>
        ${GASTOS.slice(0,3).map(g=>`
        <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
          <div><div class="fw-medium small">${g.descricao}</div>
            <div class="text-muted" style="font-size:.75rem;">${g.acolhido} · ${g.data}</div>
          </div>
          <span class="fw-semibold text-danger">${formatBRL(g.valor)}</span>
        </div>`).join('')}
        <div class="d-flex justify-content-between mt-3">
          <strong>Total (mês)</strong>
          <strong class="text-danger">${formatBRL(totalGastos)}</strong>
        </div>
      </div>
    </div>`;
  }

  function renderDashboardFuncionario() {
    return `
    <div class="p-4">
      <h4 class="text-primary mb-1">👤 Dashboard Funcionário</h4>
      <p class="text-muted mb-4">Suas tarefas do dia</p>
      <div class="row g-3 mb-4">
        ${[
          {icon:'📋',label:'Tarefas do Dia',   value:'8',  color:'#eff6ff',border:'#bfdbfe',text:'#1e40af'},
          {icon:'✅',label:'Concluídas',        value:'3',  color:'#f0fdf4',border:'#bbf7d0',text:'#166534'},
          {icon:'⏳',label:'Pendentes',         value:'5',  color:'#fff7ed',border:'#fed7aa',text:'#c2410c'},
          {icon:'📅',label:'Próximo Evento',    value:'10h',color:'#faf5ff',border:'#e9d5ff',text:'#6b21a8'},
        ].map(c=>`
        <div class="col-6 col-lg-3">
          <div class="card-nb p-3" style="background:${c.color};border-color:${c.border};">
            <span style="font-size:1.8rem;">${c.icon}</span>
            <div class="fw-bold fs-3 mt-1" style="color:${c.text};">${c.value}</div>
            <div class="fw-medium small" style="color:${c.text};">${c.label}</div>
          </div>
        </div>`).join('')}
      </div>
      <div class="card-nb p-4">
        <h6 class="mb-3">⏰ Agenda de Hoje</h6>
        ${[
          {hora:'07:00',tarefa:'Banho e higiene — Ala A',         status:'✅'},
          {hora:'08:00',tarefa:'Café da manhã — Refeitório',      status:'✅'},
          {hora:'09:00',tarefa:'Medicações matinais',             status:'✅'},
          {hora:'10:00',tarefa:'Atividade física — Pátio',        status:'⏳'},
          {hora:'12:00',tarefa:'Almoço e medicações pós-refeição',status:'⏳'},
          {hora:'14:00',tarefa:'Repouso / atividades recreativas',status:'⏳'},
          {hora:'16:00',tarefa:'Lanche — Refeitório',             status:'⏳'},
          {hora:'19:00',tarefa:'Jantar e medicações noturnas',    status:'⏳'},
        ].map(t=>`
        <div class="hora-bloco d-flex align-items-center gap-3">
          <span class="fw-bold text-primary" style="min-width:42px;">${t.hora}</span>
          <span class="flex-grow-1 small">${t.tarefa}</span>
          <span>${t.status}</span>
        </div>`).join('')}
      </div>
    </div>`;
  }
