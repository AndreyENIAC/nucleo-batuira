# Rotas da API Flask — Núcleo Batuíra

## Acesso
- `GET /`
- `POST /api/login`
- `GET /api/me`

## Dashboard
- `GET /api/dashboard`

## Acolhidos
- `GET /api/acolhidos`
- `GET /api/acolhidos/<id>`
- `POST /api/acolhidos`
- `PUT /api/acolhidos/<id>`

## Perfil do acolhido
- `GET/POST /api/acolhidos/<id>/familiares`
- `GET/POST /api/acolhidos/<id>/prescricoes`
- `GET/POST /api/acolhidos/<id>/notas`
- `GET /api/acolhidos/<id>/pias`
- `GET /api/acolhidos/<id>/pts`
- `GET /api/acolhidos/<id>/planos-alta`

## Documentos
- `GET /api/documentos`
- `POST /api/documentos`
- `GET /api/documentos/<id>/download`

## Financeiro
- `GET /api/categorias-financeiras`
- `GET/POST /api/gastos`
- `GET /api/prestacoes-contas`
- `GET /api/recursos-administrativos`
- `GET /api/beneficios`

## Agenda
- `GET /api/agenda`

Todas as rotas `/api`, exceto `/api/login`, exigem o token JWT no cabeçalho:

```text
Authorization: Bearer SEU_TOKEN
```
