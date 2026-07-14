const USUARIOS_MOCK = [
    { id:1, username:'admin',     password:'admin123',    role:'admin',     nome:'Ana Administradora', senhapadrao: false },
    { id:2, username:'tecnico',   password:'senha123',    role:'technical', nome:'Dr. Carlos Técnico', senhapadrao: false },
    { id:3, username:'financeiro',password:'senha123',    role:'financial', nome:'Maria Financeiro',   senhapadrao: false },
    { id:4, username:'func',      password:'senhapadrao', role:'staff',     nome:'João Funcionário',   senhapadrao: true  },
  ];
  const ACOLHIDOS = [
    { id:1, nome:'Maria Silva',       idade:78, quarto:'101-A', condicao:'Demência Moderada', ultimaConsulta:'10/06/2026', status:'Ativo',    tipo:'Plano Privado' },
    { id:2, nome:'José Santos',       idade:82, quarto:'102-B', condicao:'Hipertensão',       ultimaConsulta:'08/06/2026', status:'Ativo',    tipo:'Convênio SUS'  },
    { id:3, nome:'Ana Costa',         idade:75, quarto:'103-A', condicao:'Diabetes Tipo 2',   ultimaConsulta:'05/06/2026', status:'Ativo',    tipo:'Particular'    },
    { id:4, nome:'Pedro Oliveira',    idade:88, quarto:'201-B', condicao:'Insuf. Cardíaca',   ultimaConsulta:'12/06/2026', status:'Crítico',  tipo:'Plano Privado' },
    { id:5, nome:'Luiza Ferreira',    idade:71, quarto:'202-A', condicao:'Parkinson Leve',    ultimaConsulta:'09/06/2026', status:'Ativo',    tipo:'Convênio SUS'  },
    { id:6, nome:'Carlos Mendes',     idade:84, quarto:'203-B', condicao:'Pós-AVC',           ultimaConsulta:'11/06/2026', status:'Atenção',  tipo:'Particular'    },
    { id:7, nome:'Regina Almeida',    idade:79, quarto:'301-A', condicao:'Osteoporose',       ultimaConsulta:'07/06/2026', status:'Alta Méd.',tipo:'Plano Privado' },
  ];
  const PERFIL_ACOLHIDO = {
    id:1, nome:'Maria Silva', idade:78, quarto:'101-A', condicao:'Demência Moderada',
    ultimaConsulta:'10/06/2026', status:'Ativo', tipo:'Plano Privado',
    dataNascimento:'15/03/1948', cpf:'123.456.789-00', rg:'12.345.678-9',
    dataEntrada:'01/02/2024', responsavel:'João Silva (Filho)', telefoneResp:'(11) 98765-4321',
    endereco:'Rua das Flores, 123 - Guarulhos/SP', convenio:'Plano Privado - Bradesco Saúde',
    alergia:'Penicilina, Dipirona', historicoMedico:'HAS, Diabetes tipo 2, Demência em estágio moderado',
    medico:'Dr. Roberto Alves (CRM-SP 12345)', enfermeira:'Enf. Sandra Lima (COREN-SP 54321)',
    peso:'62 kg', altura:'1,58 m', imc:'24,8', pa:'130/80 mmHg', fc:'72 bpm', sat:'97%',
  };
  const PRESCRICOES = [
    { id:1, medicamento:'Donepezila 10mg',   posologia:'1 comp. ao dia (noite)',   prescrito:'Dr. Roberto Alves', data:'01/06/2026', vigente:true  },
    { id:2, medicamento:'Metformina 500mg',  posologia:'2 comp. ao dia (após ref.)',prescrito:'Dr. Roberto Alves', data:'01/06/2026', vigente:true  },
    { id:3, medicamento:'Atenolol 25mg',     posologia:'1 comp. ao dia (manhã)',   prescrito:'Dr. Roberto Alves', data:'15/05/2026', vigente:false },
  ];
  const NOTAS_CLINICAS = [
    { id:1, tipo:'Evolução Médica',    data:'10/06/2026', profissional:'Dr. Roberto Alves',  crm:'CRM-SP 12345', conteudo:'Paciente apresenta melhora cognitiva após ajuste de dose. PA controlada. Família relatou episódio de confusão noturna ontem.' },
    { id:2, tipo:'Evolução Enfermagem',data:'09/06/2026', profissional:'Enf. Sandra Lima',   crm:'COREN-SP 54321',conteudo:'Curativos realizados. Higiene matinal completa. Paciente colaborativa. Ingestão hídrica: 1.200ml. Diurese presente.' },
    { id:3, tipo:'Evolução Psicologia',data:'08/06/2026', profissional:'Psi. Laura Martins', crm:'CRP 06/12345', conteudo:'Sessão de estimulação cognitiva. Paciente identificou familiares em fotos. Sessão de musicoterapia com boa resposta.' },
  ];
  const PLANO_ALTA = {
    previsao:'01/08/2026', tipo:'Alta para domicílio com suporte familiar',
    responsavel:'Dr. Roberto Alves',
    marcos:[
      { descricao:'Estabilização da PA',         status:'concluido' },
      { descricao:'Treinamento familiar',         status:'em_andamento' },
      { descricao:'Adaptação do domicílio',       status:'em_andamento' },
      { descricao:'Avaliação cognitiva final',    status:'pendente' },
      { descricao:'Documentação e relatórios',    status:'pendente' },
    ],
    orientacoes:'Manter medicações conforme prescrição. Consulta de retorno em 30 dias. Fisioterapia domiciliar 3x/semana.',
  };
  const PIAS = [{
    id:1, acolhidoId:1, versao:'v2.1', dataElaboracao:'01/03/2026', proximaRevisao:'01/09/2026',
    equipe:'Dr. Roberto Alves, Enf. Sandra Lima, Psi. Laura Martins',
    metas:[
      { id:1, area:'Cognitivo',   descricao:'Estimulação cognitiva 3x/semana', progresso:60, prazo:'30/06/2026', status:'Em andamento' },
      { id:2, area:'Físico',      descricao:'Fisioterapia motora 2x/semana',   progresso:80, prazo:'30/07/2026', status:'Em andamento' },
      { id:3, area:'Social',      descricao:'Participar de atividades em grupo',progresso:40, prazo:'31/08/2026', status:'Em andamento' },
      { id:4, area:'Nutricional', descricao:'Manter peso entre 60-65kg',        progresso:90, prazo:'Contínuo',   status:'Atingido'    },
    ],
  }];
  const PTS_LIST = [{
    id:1, acolhidoId:1, dataReuniao:'15/05/2026', proximaReuniao:'15/08/2026',
    objetivo:'Manutenção da autonomia e qualidade de vida com foco em demência moderada',
    intervencoes:[
      { profissional:'Medicina',     responsavel:'Dr. Roberto Alves',   descricao:'Ajuste mensal de medicação anticolinesterásica'  },
      { profissional:'Enfermagem',   responsavel:'Enf. Sandra Lima',    descricao:'Cuidados de higiene e monitoramento de sinais vitais diários' },
      { profissional:'Psicologia',   responsavel:'Psi. Laura Martins',  descricao:'Sessões semanais de estimulação cognitiva e suporte emocional' },
      { profissional:'Fisioterapia', responsavel:'Ft. Paulo Henrique',  descricao:'Exercícios de equilíbrio e força 2x/semana'      },
      { profissional:'Social',       responsavel:'AS. Camila Rocha',    descricao:'Articulação com família e orientação de cuidados' },
    ],
  }];
  const DOCUMENTOS = [
    { id:1, nome:'Contrato de Internação - Maria Silva.xlsx', tipo:'Administrativo', dataUpload:'01/02/2024', tamanho:'245 KB' },
    { id:2, nome:'Laudo Médico - Jun_2026.xlsx',              tipo:'Médico',         dataUpload:'10/06/2026', tamanho:'128 KB' },
    { id:3, nome:'Autorização Familiar - Jun_2026.xlsx',      tipo:'Autorização',    dataUpload:'08/06/2026', tamanho:'95 KB'  },
  ];
  const FAMILIARES = [
    { id:1, acolhidoId:1, nome:'João Silva', parentesco:'Filho', telefone:'(11) 98765-4321', email:'joao.silva@email.com',
      responsavelLegal:true, autorizadoVisita:true, ultimaVisita:'10/06/2026', frequencia:'Semanal' },
  ];
  const VISITAS = [
    { id:1, acolhidoId:1, familiar:'João Silva', data:'10/06/2026', horario:'14:00-16:00', observacoes:'Visita tranquila. Trouxe álbum de fotos.' },
    { id:2, acolhidoId:1, familiar:'João Silva', data:'03/06/2026', horario:'10:00-12:00', observacoes:'Paciente reconheceu o filho. Ótima interação.' },
  ];
  const GASTOS = [
    { id:1, descricao:'Medicamentos - Junho/2026',      acolhido:'Maria Silva',  valor:485.50, data:'05/06/2026', categoria:'Saúde - Medicamentos', fornecedor:'Farmácia Popular'    },
    { id:2, descricao:'Fraldas Geriátricas - Jun/2026', acolhido:'José Santos',  valor:189.90, data:'06/06/2026', categoria:'Higiene',              fornecedor:'Distribuidor ABC'    },
    { id:3, descricao:'Nutrição Enteral - Jun/2026',    acolhido:'Ana Costa',    valor:320.00, data:'07/06/2026', categoria:'Saúde - Nutrição',     fornecedor:'Nutri Médica Ltda'   },
    { id:4, descricao:'Cadeira de Rodas - Aluguel',     acolhido:'Pedro Oliveira',valor:150.00,data:'08/06/2026', categoria:'Equipamento',          fornecedor:'Equipa Med'          },
    { id:5, descricao:'Material de Curativo',           acolhido:'Carlos Mendes',valor:89.40,  data:'09/06/2026', categoria:'Saúde - Medicamentos', fornecedor:'Cirúrgica Norte'     },
  ];
  const PRESTACAO_CONTAS = [
    { id:1, mes:'Maio/2026',  totalGastos:12450.00, recursosRecebidos:15000.00, saldo:2550.00, status:'Aprovado'     },
    { id:2, mes:'Abril/2026', totalGastos:11890.50, recursosRecebidos:15000.00, saldo:3109.50, status:'Aprovado'     },
    { id:3, mes:'Junho/2026', totalGastos:8234.80,  recursosRecebidos:15000.00, saldo:6765.20, status:'Em Análise'   },
  ];
  const RECURSOS_ADMIN = [
    { id:1, nome:'CNPJ - Núcleo Batuíra',              tipo:'Documento Legal',     validade:'Permanente',   status:'Ativo'    },
    { id:2, nome:'Alvará de Funcionamento 2026',        tipo:'Licença Municipal',   validade:'31/12/2026',   status:'Ativo'    },
    { id:3, nome:'CEBAS - Certificação',                tipo:'Certificação Federal',validade:'15/08/2026',   status:'Atenção'  },
    { id:4, nome:'Convênio Prefeitura Guarulhos',       tipo:'Convênio Público',    validade:'30/06/2027',   status:'Ativo'    },
    { id:5, nome:'Seguro de Responsabilidade Civil',    tipo:'Seguro',              validade:'01/01/2027',   status:'Ativo'    },
  ];
  const BENEFICIOS = [
    { id:1, acolhido:'Maria Silva',  beneficio:'BPC/LOAS',          valor:1412.00, status:'Ativo'    },
    { id:2, acolhido:'José Santos',  beneficio:'Aposentadoria INSS', valor:1800.00, status:'Ativo'    },
    { id:3, acolhido:'Ana Costa',    beneficio:'Pensão por Morte',   valor:1412.00, status:'Ativo'    },
    { id:4, acolhido:'Pedro Oliveira',beneficio:'BPC/LOAS',          valor:1412.00, status:'Pendente' },
  ];
  const USUARIOS_SISTEMA = [
    { id:1, nome:'Ana Administradora', cargo:'admin',     criadoEm:'01/01/2025' },
    { id:2, nome:'Dr. Carlos Técnico', cargo:'technical', criadoEm:'15/02/2025' },
    { id:3, nome:'Maria Financeiro',   cargo:'financial', criadoEm:'01/03/2025' },
    { id:4, nome:'João Funcionário',   cargo:'staff',     criadoEm:'10/04/2025' },
    { id:5, nome:'Enf. Sandra Lima',   cargo:'technical', criadoEm:'20/04/2025' },
    { id:6, nome:'Psi. Laura Martins', cargo:'technical', criadoEm:'01/05/2025' },
  ];
  const AGENDA = [
    { id:1, titulo:'Consulta - Maria Silva',    data:'14/07/2026', hora:'09:00', tipo:'Médica',        local:'Consultório 1' },
    { id:2, titulo:'Fisioterapia - Grupo',      data:'14/07/2026', hora:'10:00', tipo:'Reabilitação',  local:'Sala Física'   },
    { id:3, titulo:'Reunião de Equipe',         data:'15/07/2026', hora:'14:00', tipo:'Administrativa', local:'Sala Reunião' },
    { id:4, titulo:'Visita Familiar - José',    data:'16/07/2026', hora:'15:00', tipo:'Visita',         local:'Salão'        },
    { id:5, titulo:'Avaliação Nutricional',     data:'17/07/2026', hora:'11:00', tipo:'Nutrição',       local:'Consultório 2'},
  ];

  // Helpers
  function nomeCargo(role) {
    return { admin:'Administrador', technical:'Equipe Técnica', financial:'Adm. Financeiro', staff:'Funcionário' }[role] || role;
  }
  function badgeCargo(role) {
    return { admin:'bg-danger', technical:'bg-success', financial:'bg-warning text-dark', staff:'bg-secondary' }[role] || 'bg-secondary';
  }
  function statusBadge(status) {
    const m = { 'Ativo':'bg-success', 'Crítico':'bg-danger', 'Atenção':'bg-warning text-dark',
                'Alta Méd.':'bg-info text-dark', 'Aprovado':'bg-success', 'Em Análise':'bg-warning text-dark', 'Pendente':'bg-secondary' };
    return m[status] || 'bg-secondary';
  }
  function formatBRL(v) {
    return new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(v);
  }
