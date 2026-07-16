function renderUsuarios() {
    const lista = APP.usuarios.map(u=>`
      <div class="d-flex align-items-center gap-4 py-4 border-bottom flex-wrap">
        <div class="flex-grow-1">
          <div class="d-flex align-items-center gap-3 mb-1 flex-wrap">
            <span class="fw-semibold fs-5">${u.nome}</span>
            <span class="badge ${badgeCargo(u.cargo)} badge-status">${nomeCargo(u.cargo)}</span>
          </div>
          <div class="text-muted small">Cadastrado em: ${u.criadoEm}</div>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-primary rounded-3 btn-editar-usuario" data-id="${u.id}" title="Editar">✏️</button>
          <button class="btn btn-danger rounded-3 btn-remover-usuario" data-id="${u.id}" title="Remover">🗑</button>
        </div>
      </div>`).join('');
    return `
    <div class="p-4">
      <h4 class="text-primary mb-1">⚙️ Gerenciar Usuários</h4>
      <p class="text-muted mb-4">Cadastre, edite ou remova usuários do sistema</p>
      <div class="mb-4">
        <button class="btn btn-primary rounded-3 px-4 py-3" id="btn-add-usuario">➕ Adicionar Novo Usuário</button>
      </div>
      <div id="form-novo-usuario" class="card-nb p-4 mb-4 d-none">
        <h6 class="mb-4">Novo Usuário</h6>
        <div class="mb-4"><label class="form-label">Nome Completo</label>
          <input type="text" id="nu-nome" class="form-control form-control-nb" placeholder="Nome completo"></div>
        <div class="mb-4"><label class="form-label">Cargo</label>
          <div class="row g-3" id="nu-cargo-grid">
            ${[{id:'admin',nome:'Administrador',icone:'👑'},{id:'technical',nome:'Equipe Técnica',icone:'🩺'},
              {id:'financial',nome:'Adm. Financeiro',icone:'💰'},{id:'staff',nome:'Funcionário',icone:'👤'},
              ].map(r=>`
            <div class="col-6 col-md-3">
              <button type="button" class="btn border w-100 p-3 rounded-3 cargo-btn ${r.id==='staff'?'border-primary bg-primary bg-opacity-10':''}" data-cargo="${r.id}">
                <div class="fs-3 mb-1">${r.icone}</div>
                <div class="small">${r.nome}</div>
              </button>
            </div>`).join('')}
          </div>
          <input type="hidden" id="nu-cargo" value="staff">
        </div>
        <div class="mb-4"><label class="form-label">Senha Inicial</label>
          <input type="text" id="nu-senha" class="form-control form-control-nb" value="senha123"></div>
        <div class="d-flex gap-3">
          <button class="btn btn-success flex-grow-1 rounded-3 py-3" id="btn-salvar-usuario">✓ Salvar Usuário</button>
          <button class="btn btn-secondary flex-grow-1 rounded-3 py-3" id="btn-cancelar-usuario">✕ Cancelar</button>
        </div>
      </div>
      <div class="card-nb">
        <div class="p-4 border-bottom" style="background:#eff6ff;">
          <h6 class="mb-0">Usuários Cadastrados (${APP.usuarios.length})</h6>
        </div>
        <div class="px-4" id="lista-usuarios">${lista}</div>
      </div>
    </div>`;
  }

  function bindUsuarios() {
    const btnAdd    = document.getElementById('btn-add-usuario');
    const formDiv   = document.getElementById('form-novo-usuario');
    const btnSalvar = document.getElementById('btn-salvar-usuario');
    const btnCancel = document.getElementById('btn-cancelar-usuario');
    const inpCargo  = document.getElementById('nu-cargo');

    btnAdd?.addEventListener('click', () => {
      formDiv?.classList.toggle('d-none');
      btnAdd.textContent = formDiv?.classList.contains('d-none') ? '➕ Adicionar Novo Usuário' : '✕ Fechar';
    });
    btnCancel?.addEventListener('click', () => {
      formDiv?.classList.add('d-none');
      btnAdd.textContent = '➕ Adicionar Novo Usuário';
      document.getElementById('nu-nome').value = '';
    });
    document.querySelectorAll('.cargo-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.cargo-btn').forEach(b => b.classList.remove('border-primary','bg-primary','bg-opacity-10'));
        btn.classList.add('border-primary','bg-primary','bg-opacity-10');
        inpCargo.value = btn.dataset.cargo;
      });
    });
    btnSalvar?.addEventListener('click', () => {
      const nome  = document.getElementById('nu-nome').value.trim();
      const cargo = inpCargo.value;
      if (!nome) { alert('Informe o nome do usuário.'); return; }
      const novo = { id:Date.now(), nome, cargo, criadoEm: new Date().toLocaleDateString('pt-BR') };
      APP.usuarios.push(novo);
      alert(`✅ Usuário "${nome}" (${nomeCargo(cargo)}) cadastrado!`);
      formDiv?.classList.add('d-none');
      btnAdd.textContent = '➕ Adicionar Novo Usuário';
      document.getElementById('nu-nome').value = '';
      document.getElementById('lista-usuarios').innerHTML = renderListaUsuarios();
      bindBotoesUsuarios();
    });
    bindBotoesUsuarios();
  }

  function renderListaUsuarios() {
    return APP.usuarios.map(u=>`
      <div class="d-flex align-items-center gap-4 py-4 border-bottom flex-wrap">
        <div class="flex-grow-1">
          <div class="d-flex align-items-center gap-3 mb-1 flex-wrap">
            <span class="fw-semibold fs-5">${u.nome}</span>
            <span class="badge ${badgeCargo(u.cargo)} badge-status">${nomeCargo(u.cargo)}</span>
          </div>
          <div class="text-muted small">Cadastrado em: ${u.criadoEm}</div>
        </div>
        <div class="d-flex gap-2">
          <button class="btn btn-primary rounded-3 btn-editar-usuario" data-id="${u.id}" title="Editar">✏️</button>
          <button class="btn btn-danger rounded-3 btn-remover-usuario" data-id="${u.id}" title="Remover">🗑</button>
        </div>
      </div>`).join('');
  }

  function bindBotoesUsuarios() {
    document.querySelectorAll('.btn-editar-usuario').forEach(btn => {
      btn.addEventListener('click', () => {
        const u = APP.usuarios.find(x => x.id === parseInt(btn.dataset.id));
        if (u) alert(`✏️ Editar: ${u.nome}\n\nEm produção: abre formulário de edição.`);
      });
    });
    document.querySelectorAll('.btn-remover-usuario').forEach(btn => {
      btn.addEventListener('click', () => {
        const u = APP.usuarios.find(x => x.id === parseInt(btn.dataset.id));
        if (!u) return;
        if (confirm(`Remover "${u.nome}"?`)) {
          APP.usuarios = APP.usuarios.filter(x => x.id !== parseInt(btn.dataset.id));
          document.getElementById('lista-usuarios').innerHTML = renderListaUsuarios();
          bindBotoesUsuarios();
        }
      });
    });
  }
