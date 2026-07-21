# Rotas da API Flask — Núcleo Batuíra

## Acesso e senha
- `GET /`
- `POST /api/login`
- `GET /api/me`
- `POST /api/trocar-senha`
- `POST /api/esqueci-senha`

## Gerenciamento de usuários — administrador
- `GET /api/perfis`
- `GET /api/usuarios`
- `POST /api/usuarios`
- `PUT /api/usuarios/<id>`
- `PATCH /api/usuarios/<id>/status`
- `POST /api/usuarios/<id>/senha-temporaria`
- `GET /api/recuperacoes-senha`
- `POST /api/recuperacoes-senha/<id>/resolver`

## Dashboard
- `GET /api/dashboard`
- `PATCH /api/alertas/<id>/resolver`

O dashboard retorna saldo do mês, contagem dos acolhidos por status, alertas e os próximos eventos permitidos ao perfil conectado.

## Acolhidos
- `GET /api/acolhidos`
- `GET /api/acolhidos/<id>`
- `POST /api/acolhidos`
- `PUT /api/acolhidos/<id>`
- `PATCH /api/acolhidos/<id>/status`

As operações de alteração são permitidas ao administrador e à equipe técnica.

## Família, alergias e saúde
- `GET/POST /api/acolhidos/<id>/familiares`
- `GET /api/alergias`
- `GET/POST /api/acolhidos/<id>/alergias`
- `GET/POST /api/acolhidos/<id>/prescricoes`
- `PATCH /api/prescricoes/<id>/status`
- `GET/POST /api/acolhidos/<id>/notas`

## PIA, PTS, alta e benefícios
- `GET/POST /api/acolhidos/<id>/pias`
- `POST /api/pias/<id>/metas`
- `GET/POST /api/acolhidos/<id>/pts`
- `POST /api/pts/<id>/intervencoes`
- `GET/POST /api/acolhidos/<id>/planos-alta`
- `PATCH /api/planos-alta/<id>/concluir`
- `GET/POST /api/acolhidos/<id>/beneficios`
- `PATCH /api/beneficios/<id>/status`
- `GET /api/beneficios`

## Documentos
- `GET /api/documentos`
- `POST /api/documentos`
- `GET /api/documentos/<id>/download`

## Gestão Institucional
- `GET /api/categorias-financeiras`
- `GET/POST /api/receitas`
- `GET/POST /api/gastos`
- `GET /api/prestacoes-contas`
- `GET /api/recursos-administrativos`

## Agenda
- `GET /api/agenda`
- `POST /api/agenda`
- `PUT /api/agenda/<id>`
- `DELETE /api/agenda/<id>`

Setores usados: `saude`, `institucional` e `geral`.

- Administrador: consulta e altera todos os setores.
- Equipe técnica: consulta Saúde e Geral; altera Saúde.
- Equipe institucional: consulta Institucional e Geral; altera Institucional.
- Funcionário: consulta todos; não altera.

## Autenticação

As rotas protegidas exigem o JWT no cabeçalho:

```text
Authorization: Bearer SEU_TOKEN
```

Quando `primeiro_acesso = 1`, apenas as rotas de identificação e troca de senha ficam liberadas até a senha temporária ser substituída.
