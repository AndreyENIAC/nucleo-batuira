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
var campoBusca   = document.getElementById('busca-acolhido');
var filtroStatus = document.getElementById('filtro-status');

function filtrarAcolhidos() {
  var textoBusca = campoBusca  ? campoBusca.value.toLowerCase()  : '';
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
   FILTRO DE DOCUMENTOS — busca pelo nome do arquivo
   Funciona na aba Documentos de financeiro.html
   ------------------------------------------------------- */
var buscaDocumento = document.getElementById('busca-documento');

function filtrarDocumentos() {
  var texto = buscaDocumento ? buscaDocumento.value.toLowerCase() : '';
  var itens = document.querySelectorAll('.linha-documento');

  itens.forEach(function (item) {
    var nome = item.querySelector('.col-doc-nome').textContent.toLowerCase();

    if (nome.includes(texto)) {
      item.style.display = '';
    } else {
      item.style.display = 'none';
    }
  });
}

if (buscaDocumento) buscaDocumento.addEventListener('input', filtrarDocumentos);

/* -------------------------------------------------------
   FILTRO DE GASTOS — busca por descrição ou acolhido
   Funciona na aba Gastos de financeiro.html
   ------------------------------------------------------- */
var buscaGasto = document.getElementById('busca-gasto');

function filtrarGastos() {
  var texto = buscaGasto ? buscaGasto.value.toLowerCase() : '';
  var linhas = document.querySelectorAll('.linha-gasto');

  linhas.forEach(function (linha) {
    var descricao = linha.querySelector('.col-gasto-desc').textContent.toLowerCase();
    var acolhido  = linha.querySelector('.col-gasto-acolhido').textContent.toLowerCase();

    if (descricao.includes(texto) || acolhido.includes(texto)) {
      linha.style.display = '';
    } else {
      linha.style.display = 'none';
    }
  });
}

if (buscaGasto) buscaGasto.addEventListener('input', filtrarGastos);

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
