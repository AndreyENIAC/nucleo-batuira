# API Flask — Núcleo Batuíra

API REST em Flask + SQLite para o sistema de gestão do Núcleo Batuíra.

## 1. Preparar o ambiente

No Windows/PowerShell:

```powershell
cd api_flask_batuira
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

No Linux/macOS:

```bash
cd api_flask_batuira
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. Criar o banco do zero

O pacote já contém um `batuira.db` pronto. Para recriá-lo:

```bash
python criar_banco.py
```

Login inicial:

```text
usuário: admin
senha: admin123
```

A troca da senha será exigida no primeiro acesso.

## 3. Executar

```bash
python app.py
```

Endereço padrão:

```text
http://127.0.0.1:5000
```

Teste de saúde:

```text
GET http://127.0.0.1:5000/api/health
```

Lista automática de rotas:

```text
GET http://127.0.0.1:5000/api/rotas
```

## 4. Autenticação

Login:

```http
POST /api/auth/login
Content-Type: application/json

{
  "login": "admin",
  "senha": "admin123"
}
```

Nas rotas protegidas, envie:

```http
Authorization: Bearer SEU_ACCESS_TOKEN
```

Troca da senha inicial:

```http
POST /api/auth/trocar-senha
Authorization: Bearer SEU_ACCESS_TOKEN
Content-Type: application/json

{
  "nova_senha": "NovaSenha123",
  "confirmacao": "NovaSenha123"
}
```

## 5. Módulos implementados

- autenticação JWT e troca obrigatória de senha;
- usuários e perfis de acesso;
- acolhidos, familiares e visitas;
- diagnósticos, alergias e sinais vitais;
- prescrições, horários e administrações de medicamentos;
- notas clínicas;
- PIA, metas, PTS, intervenções e planos de alta;
- documentos e upload de arquivos;
- recursos administrativos;
- gastos, receitas, prestações de contas e benefícios;
- agenda, tarefas, alertas e logs de auditoria;
- dashboard por perfil.

## 6. Endpoints principais

| Módulo | Método e rota |
|---|---|
| Login | `POST /api/auth/login` |
| Usuário atual | `GET /api/auth/me` |
| Trocar senha | `POST /api/auth/trocar-senha` |
| Dashboard | `GET /api/dashboard` |
| Usuários | `GET/POST /api/usuarios` |
| Usuário | `GET/PUT/DELETE /api/usuarios/<id>` |
| Acolhidos | `GET/POST /api/acolhidos` |
| Acolhido | `GET/PUT/DELETE /api/acolhidos/<id>` |
| Familiares | `GET/POST /api/acolhidos/<id>/familiares` |
| Visitas | `GET/POST /api/acolhidos/<id>/visitas` |
| Diagnósticos | `GET/POST /api/acolhidos/<id>/diagnosticos` |
| Sinais vitais | `GET/POST /api/acolhidos/<id>/sinais-vitais` |
| Prescrições | `GET/POST /api/acolhidos/<id>/prescricoes` |
| Notas clínicas | `GET/POST /api/acolhidos/<id>/notas-clinicas` |
| PIA | `GET/POST /api/acolhidos/<id>/pias` |
| PTS | `GET/POST /api/acolhidos/<id>/pts` |
| Plano de alta | `GET/POST /api/acolhidos/<id>/planos-alta` |
| Documentos | `GET/POST /api/documentos` |
| Gastos | `GET/POST /api/gastos` |
| Receitas | `GET/POST /api/receitas` |
| Prestação | `GET/POST /api/prestacoes-contas` |
| Agenda | `GET/POST /api/agenda` |
| Tarefas | `GET/POST /api/tarefas` |
| Alertas | `GET/POST /api/alertas` |

A rota `/api/rotas` mostra todas as rotas e métodos disponíveis.

## 7. Upload de documento

Use `multipart/form-data`:

```text
arquivo: contrato.pdf
escopo: acolhido
acolhido_id: 1
titulo: Contrato de acolhimento
categoria: Administrativo
descricao: Documento assinado
```

Arquivos permitidos: PDF, DOC, DOCX, XLS, XLSX, CSV, TXT, JPG, JPEG e PNG.

## 8. Testes

```bash
pytest -q
```

Também há uma coleção do Postman na pasta `postman/`.
