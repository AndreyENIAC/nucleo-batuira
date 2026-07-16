# Rotas da API Núcleo Batuíra

Base: `http://127.0.0.1:5000/api`

## Acolhidos e família

| Método | Rota |
|---|---|
| `POST` | `/api/acolhidos` |
| `GET` | `/api/acolhidos` |
| `DELETE` | `/api/acolhidos/<int:resident_id>` |
| `GET` | `/api/acolhidos/<int:resident_id>` |
| `PUT` | `/api/acolhidos/<int:resident_id>` |
| `POST` | `/api/acolhidos/<int:resident_id>/familiares` |
| `GET` | `/api/acolhidos/<int:resident_id>/familiares` |
| `POST` | `/api/acolhidos/<int:resident_id>/visitas` |
| `GET` | `/api/acolhidos/<int:resident_id>/visitas` |
| `DELETE` | `/api/familiares/<int:family_id>` |
| `PUT` | `/api/familiares/<int:family_id>` |
| `DELETE` | `/api/visitas/<int:visit_id>` |
| `PUT` | `/api/visitas/<int:visit_id>` |

## Autenticação

| Método | Rota |
|---|---|
| `POST` | `/api/auth/login` |
| `POST` | `/api/auth/logout` |
| `GET` | `/api/auth/me` |
| `POST` | `/api/auth/trocar-senha` |

## Clínico

| Método | Rota |
|---|---|
| `GET` | `/api/acolhidos/<int:resident_id>/administracoes-medicamentos` |
| `POST` | `/api/acolhidos/<int:resident_id>/alergias` |
| `GET` | `/api/acolhidos/<int:resident_id>/alergias` |
| `DELETE` | `/api/acolhidos/<int:resident_id>/alergias/<int:allergy_id>` |
| `POST` | `/api/acolhidos/<int:resident_id>/diagnosticos` |
| `GET` | `/api/acolhidos/<int:resident_id>/diagnosticos` |
| `POST` | `/api/acolhidos/<int:resident_id>/notas-clinicas` |
| `GET` | `/api/acolhidos/<int:resident_id>/notas-clinicas` |
| `POST` | `/api/acolhidos/<int:resident_id>/prescricoes` |
| `GET` | `/api/acolhidos/<int:resident_id>/prescricoes` |
| `POST` | `/api/acolhidos/<int:resident_id>/sinais-vitais` |
| `GET` | `/api/acolhidos/<int:resident_id>/sinais-vitais` |
| `POST` | `/api/administracoes-medicamentos` |
| `PUT` | `/api/administracoes-medicamentos/<int:record_id>` |
| `POST` | `/api/alergias` |
| `GET` | `/api/alergias` |
| `DELETE` | `/api/diagnosticos/<int:record_id>` |
| `PUT` | `/api/diagnosticos/<int:record_id>` |
| `DELETE` | `/api/notas-clinicas/<int:record_id>` |
| `PUT` | `/api/notas-clinicas/<int:record_id>` |
| `DELETE` | `/api/prescricao-horarios/<int:record_id>` |
| `DELETE` | `/api/prescricoes/<int:record_id>` |
| `GET` | `/api/prescricoes/<int:record_id>` |
| `PUT` | `/api/prescricoes/<int:record_id>` |
| `POST` | `/api/prescricoes/<int:record_id>/horarios` |
| `DELETE` | `/api/sinais-vitais/<int:record_id>` |
| `PUT` | `/api/sinais-vitais/<int:record_id>` |

## Dashboard

| Método | Rota |
|---|---|
| `GET` | `/api/dashboard` |

## Documentos

| Método | Rota |
|---|---|
| `GET` | `/api/acolhidos/<int:resident_id>/documentos` |
| `GET` | `/api/documentos` |
| `POST` | `/api/documentos` |
| `DELETE` | `/api/documentos/<int:document_id>` |
| `GET` | `/api/documentos/<int:document_id>` |
| `PUT` | `/api/documentos/<int:document_id>` |
| `GET` | `/api/documentos/<int:document_id>/download` |
| `POST` | `/api/recursos-administrativos` |
| `GET` | `/api/recursos-administrativos` |
| `DELETE` | `/api/recursos-administrativos/<int:record_id>` |
| `PUT` | `/api/recursos-administrativos/<int:record_id>` |

## Financeiro

| Método | Rota |
|---|---|
| `POST` | `/api/beneficios` |
| `GET` | `/api/beneficios` |
| `DELETE` | `/api/beneficios/<int:record_id>` |
| `PUT` | `/api/beneficios/<int:record_id>` |
| `POST` | `/api/categorias-financeiras` |
| `GET` | `/api/categorias-financeiras` |
| `PUT` | `/api/categorias-financeiras/<int:record_id>` |
| `POST` | `/api/gastos` |
| `GET` | `/api/gastos` |
| `DELETE` | `/api/gastos/<int:record_id>` |
| `PUT` | `/api/gastos/<int:record_id>` |
| `POST` | `/api/prestacoes-contas` |
| `GET` | `/api/prestacoes-contas` |
| `DELETE` | `/api/prestacoes-contas/<int:record_id>` |
| `PUT` | `/api/prestacoes-contas/<int:record_id>` |
| `POST` | `/api/receitas` |
| `GET` | `/api/receitas` |
| `DELETE` | `/api/receitas/<int:record_id>` |
| `PUT` | `/api/receitas/<int:record_id>` |

## Geral

| Método | Rota |
|---|---|
| `GET` | `/api/health` |
| `GET` | `/api/rotas` |

## Agenda, tarefas e alertas

| Método | Rota |
|---|---|
| `POST` | `/api/agenda` |
| `GET` | `/api/agenda` |
| `DELETE` | `/api/agenda/<int:record_id>` |
| `PUT` | `/api/agenda/<int:record_id>` |
| `POST` | `/api/alertas` |
| `GET` | `/api/alertas` |
| `PUT` | `/api/alertas/<int:record_id>` |
| `GET` | `/api/logs-auditoria` |
| `POST` | `/api/tarefas` |
| `GET` | `/api/tarefas` |
| `DELETE` | `/api/tarefas/<int:record_id>` |
| `PUT` | `/api/tarefas/<int:record_id>` |

## PIA, PTS e planos de alta

| Método | Rota |
|---|---|
| `POST` | `/api/acolhidos/<int:resident_id>/pias` |
| `GET` | `/api/acolhidos/<int:resident_id>/pias` |
| `POST` | `/api/acolhidos/<int:resident_id>/planos-alta` |
| `GET` | `/api/acolhidos/<int:resident_id>/planos-alta` |
| `POST` | `/api/acolhidos/<int:resident_id>/pts` |
| `GET` | `/api/acolhidos/<int:resident_id>/pts` |
| `DELETE` | `/api/pia-metas/<int:goal_id>` |
| `PUT` | `/api/pia-metas/<int:goal_id>` |
| `GET` | `/api/pias/<int:pia_id>` |
| `PUT` | `/api/pias/<int:pia_id>` |
| `POST` | `/api/pias/<int:pia_id>/metas` |
| `DELETE` | `/api/plano-alta-etapas/<int:step_id>` |
| `PUT` | `/api/plano-alta-etapas/<int:step_id>` |
| `GET` | `/api/planos-alta/<int:plan_id>` |
| `PUT` | `/api/planos-alta/<int:plan_id>` |
| `POST` | `/api/planos-alta/<int:plan_id>/etapas` |
| `DELETE` | `/api/pts-intervencoes/<int:item_id>` |
| `PUT` | `/api/pts-intervencoes/<int:item_id>` |
| `GET` | `/api/pts/<int:pts_id>` |
| `PUT` | `/api/pts/<int:pts_id>` |
| `POST` | `/api/pts/<int:pts_id>/intervencoes` |

## Usuários

| Método | Rota |
|---|---|
| `GET` | `/api/perfis` |
| `POST` | `/api/usuarios` |
| `GET` | `/api/usuarios` |
| `DELETE` | `/api/usuarios/<int:user_id>` |
| `GET` | `/api/usuarios/<int:user_id>` |
| `PUT` | `/api/usuarios/<int:user_id>` |
| `POST` | `/api/usuarios/<int:user_id>/redefinir-senha` |
