/* =====================================================
   main.js — Núcleo Batuíra
   JavaScript básico: apenas validação e filtros.
   Sem geração de HTML, sem estado global.
   ===================================================== */

/* -------------------------------------------------------
   LOGIN — valida os campos e redireciona
   ------------------------------------------------------- */
var formLogin = document.getElementById('form-login');
if (formLogin) {
  formLogin.addEventListener('submit', function (e) {
    e.preventDefault();

    var usuario = document.getElementById('usuario').value.trim();
    var senha   = document.getElementById('senha').value.trim();
    var erro    = document.getElementById('mensagem-erro');

    /* Lista de usuários de teste */
    var usuarios = [
      { login: 'admin',       senha: 'admin123' },
      { login: 'tecnico',     senha: 'senha123' },
      { login: 'financeiro',  senha: 'senha123' },
      { login: 'func',        senha: 'senha123'  }
    ];

    var encontrado = false;
    for (var i = 0; i < usuarios.length; i++) {
      if (usuarios[i].login === usuario && usuarios[i].senha === senha) {
        encontrado = true;
        break;
      }
    }

    if (encontrado) {
      window.location.href = 'index.html';
    } else {
      erro.classList.remove('d-none');
    }
  });

  /* Esconde o erro quando o usuário começa a digitar de novo */
  document.getElementById('usuario').addEventListener('input', function () {
    document.getElementById('mensagem-erro').classList.add('d-none');
  });
  document.getElementById('senha').addEventListener('input', function () {
    document.getElementById('mensagem-erro').classList.add('d-none');
  });
}

/* -------------------------------------------------------
   FILTRO DE ACOLHIDOS — busca por nome e status
   Funciona na tabela de acolhidos.html
   ------------------------------------------------------- */
var campoBusca  = document.getElementById('busca-acolhido');
var filtroStatus = document.getElementById('filtro-status');

function filtrarAcolhidos() {
  var textoBusca = campoBusca ? campoBusca.value.toLowerCase() : '';
  var statusSel  = filtroStatus ? filtroStatus.value.toLowerCase() : '';

  var linhas = document.querySelectorAll('.linha-acolhido');

  linhas.forEach(function (linha) {
    var nome   = linha.querySelector('.col-nome').textContent.toLowerCase();
    var status = linha.querySelector('.col-status').textContent.toLowerCase();

    var nomeOk   = nome.includes(textoBusca);
    var statusOk = statusSel === '' || status.includes(statusSel);

    if (nomeOk && statusOk) {
      linha.style.display = '';
    } else {
      linha.style.display = 'none';
    }
  });
}

if (campoBusca)   campoBusca.addEventListener('input', filtrarAcolhidos);
if (filtroStatus) filtroStatus.addEventListener('change', filtrarAcolhidos);

/* -------------------------------------------------------
   SIDEBAR MOBILE — botão hamburguer (opcional)
   ------------------------------------------------------- */
var btnMenu   = document.getElementById('btn-menu');
var sidebarEl = document.querySelector('.sidebar');

if (btnMenu && sidebarEl) {
  btnMenu.addEventListener('click', function () {
    sidebarEl.classList.toggle('d-none');
  });
}
