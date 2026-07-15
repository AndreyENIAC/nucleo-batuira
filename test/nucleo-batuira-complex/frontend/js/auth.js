const APP = {
    logado: false, userRole: '', userName: '',
    secaoAtiva: 'dashboard', acolhidoSelecionado: null,
    abaPerfilAtiva: 'prescricoes', abaPiaPtsAtiva: 'pia',
    abaFinanceiroAtiva: 'documentos', needsPasswordChange: false,
    usuarios: [...USUARIOS_SISTEMA], documentos: [...DOCUMENTOS],
    familiares: [...FAMILIARES], visitas: [...VISITAS],
    pias: [...PIAS], ptsList: [...PTS_LIST],
  };

  function navegar(secao, params = {}) {
    APP.secaoAtiva = secao;
    if (params.acolhidoId !== undefined) APP.acolhidoSelecionado = params.acolhidoId;
    if (params.aba) APP.abaPerfilAtiva = params.aba;
    renderApp();
  }

  function renderApp() {
    const root = document.getElementById('root');
    if (!APP.logado)           { root.innerHTML = renderTelaLogin();    bindLogin();    return; }
    if (APP.needsPasswordChange){ root.innerHTML = renderTrocaSenha();  bindTrocaSenha();return; }

    root.innerHTML = `
      <div id="layout-principal">
        <div id="sidebar-wrapper">${renderSidebar()}</div>
        <main id="conteudo-principal">${renderConteudo()}</main>
      </div>`;
    bindSidebar();
    bindConteudo();
  }

  function renderTelaLogin() {
    return `
    <div id="tela-login">
      <div class="login-card">
        <div class="text-center mb-4">
          <img src="https://nucleobatuira.org.br/wp-content/uploads/2021/07/LOGO-HDV-BATUIRA-1-768x324.png"
              alt="Núcleo Batuíra" style="max-width:200px;height:auto;" onerror="this.style.display='none'">
          <h5 class="mt-3 text-primary fw-bold">Sistema de Gestão de Cuidados</h5>
          <p class="text-muted small">Núcleo Batuíra · Guarulhos/SP</p>
        </div>
        <div id="login-erro" class="alert alert-danger d-none small"></div>
        <div class="mb-3"><label class="form-label fw-medium">Usuário</label>
          <input type="text" id="inp-user" class="form-control form-control-nb" placeholder="Login"></div>
        <div class="mb-4"><label class="form-label fw-medium">Senha</label>
          <input type="password" id="inp-pass" class="form-control form-control-nb" placeholder="Senha"></div>
        <button id="btn-entrar" class="btn btn-primary w-100 py-3 rounded-3 fw-semibold">Entrar no Sistema</button>
        <div class="mt-3 p-3 rounded-3" style="background:#f8f9fa;font-size:.8rem;">
          <strong>Logins de teste:</strong><br>
          admin / admin123 · tecnico / senha123 · financeiro / senha123 · func / senhapadrao
        </div>
      </div>
    </div>`;
  }

  function bindLogin() {
    const entrar = () => {
      const u = document.getElementById('inp-user').value.trim();
      const p = document.getElementById('inp-pass').value;
      const found = USUARIOS_MOCK.find(x => x.username === u && x.password === p);
      if (found) {
        APP.logado = true; APP.userRole = found.role; APP.userName = found.nome;
        APP.needsPasswordChange = !!found.senhapadrao;
        renderApp();
      } else {
        const el = document.getElementById('login-erro');
        el.textContent = 'Usuário ou senha incorretos.'; el.classList.remove('d-none');
      }
    };
    document.getElementById('btn-entrar')?.addEventListener('click', entrar);
    document.getElementById('inp-pass')?.addEventListener('keydown', e => { if(e.key==='Enter') entrar(); });
  }

  function renderTrocaSenha() {
    return `
    <div id="tela-login">
      <div class="login-card">
        <div class="text-center mb-4">
          <div style="font-size:3rem;">🔐</div>
          <h5 class="text-primary fw-bold">Troca de Senha Obrigatória</h5>
          <p class="text-muted small">Por segurança, defina uma nova senha antes de continuar.</p>
        </div>
        <div class="mb-3"><label class="form-label">Nova Senha</label>
          <input type="password" id="nova-senha" class="form-control form-control-nb" placeholder="Mínimo 6 caracteres"></div>
        <div class="mb-4"><label class="form-label">Confirmar Senha</label>
          <input type="password" id="confirma-senha" class="form-control form-control-nb" placeholder="Repita a senha"></div>
        <div id="troca-erro" class="alert alert-danger d-none small mb-3"></div>
        <button id="btn-trocar" class="btn btn-primary w-100 py-3 rounded-3 fw-semibold">Salvar Nova Senha</button>
      </div>
    </div>`;
  }

  function bindTrocaSenha() {
    document.getElementById('btn-trocar')?.addEventListener('click', () => {
      const n = document.getElementById('nova-senha').value;
      const c = document.getElementById('confirma-senha').value;
      const err = document.getElementById('troca-erro');
      if (n.length < 6) { err.textContent='Mínimo 6 caracteres.'; err.classList.remove('d-none'); return; }
      if (n !== c)      { err.textContent='As senhas não coincidem.'; err.classList.remove('d-none'); return; }
      APP.needsPasswordChange = false;
      renderApp();
    });
  }

  function fazerLogout() {
    APP.logado = false; APP.userRole = ''; APP.userName = '';
    APP.secaoAtiva = 'dashboard'; APP.acolhidoSelecionado = null;
    renderApp();
  }
