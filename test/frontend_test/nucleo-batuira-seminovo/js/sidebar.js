function renderSidebar() {
    const itens = [
      { id:'dashboard',  label:'📊 Dashboard',          roles:['admin','technical','financial','staff'] },
      { id:'acolhidos',  label:'👥 Acolhidos',           roles:['admin','technical','staff']             },
      { id:'financeiro', label:'💼 Gestão Financeira',   roles:['admin','financial']                     },
      { id:'usuarios',   label:'⚙️ Gerenciar Usuários',  roles:['admin']                                 },
    ].filter(i => i.roles.includes(APP.userRole));

    const itensHtml = itens.map(i => `
      <button class="nav-item-btn ${APP.secaoAtiva === i.id ? 'ativo' : ''}" data-secao="${i.id}">${i.label}</button>
    `).join('');

    return `
      <div class="d-flex flex-column h-100">
        <div class="p-3 border-bottom" style="background:#eff6ff;">
          <img src="https://nucleobatuira.org.br/wp-content/uploads/2021/07/LOGO-HDV-BATUIRA-1-768x324.png"
              alt="Núcleo Batuíra" class="sidebar-logo mb-3 d-block" onerror="this.style.display='none'">
          <div class="sidebar-usuario">
            <div class="fw-medium">${APP.userName}</div>
            <div class="text-muted small">${nomeCargo(APP.userRole)}</div>
          </div>
        </div>
        <nav class="flex-grow-1 p-3">${itensHtml}</nav>
        <div class="p-3 border-top">
          <button id="btn-logout" class="btn btn-danger w-100 rounded-3 py-2">🚪 Sair</button>
        </div>
      </div>`;
  }

  function bindSidebar() {
    document.querySelectorAll('.nav-item-btn[data-secao]').forEach(btn => {
      btn.addEventListener('click', () => navegar(btn.dataset.secao));
    });
    document.getElementById('btn-logout')?.addEventListener('click', fazerLogout);
  }

  function renderConteudo() {
    if (APP.secaoAtiva === 'perfil' && APP.acolhidoSelecionado !== null) return renderPerfilAcolhido();
    switch (APP.secaoAtiva) {
      case 'dashboard':  return renderDashboard();
      case 'acolhidos':  return renderListaAcolhidos();
      case 'financeiro': return renderFinanceiro();
      case 'usuarios':   return renderUsuarios();
      default:           return renderDashboard();
    }
  }

  function bindConteudo() {
    bindDashboard();
    if (APP.secaoAtiva === 'perfil')     bindPerfilAcolhido();
    if (APP.secaoAtiva === 'acolhidos')  bindListaAcolhidos();
    if (APP.secaoAtiva === 'financeiro') bindFinanceiro();
    if (APP.secaoAtiva === 'usuarios')   bindUsuarios();
  }
