# Frontend integrado — Núcleo Batuíra

## Como executar

1. Inicie o Backend Flask na pasta `backend`.
2. Nesta pasta `frontend`, execute `iniciar_frontend.bat`.
3. Abra no navegador: `http://127.0.0.1:5500/login.html`.

O frontend usa HTML, Bootstrap e JavaScript puro. A comunicação com o Flask fica em `js/api.js`.

## Páginas de acesso

- `login.html`: entrada no sistema.
- `trocar-senha.html`: troca obrigatória da senha temporária.
- `esqueci-senha.html`: registra uma solicitação ao administrador.
- `usuarios.html`: gerenciamento exclusivo do administrador.

## Gestão de Saúde

A página `perfil.html` permite consultar e, conforme o perfil, alterar dados do acolhido, alergias, prescrições, notas, PIA, PTS, plano de alta, benefícios e documentos. O perfil `staff` possui somente leitura.


## Agenda e Gestão Institucional

- `agenda.html`: consulta e gerenciamento de eventos conforme o perfil.
- `financeiro.html`: documentos, receitas e doações, gastos, prestação de contas e recursos.
- `index.html`: dashboard com saldo, alertas, próximos eventos e acolhidos por status.
