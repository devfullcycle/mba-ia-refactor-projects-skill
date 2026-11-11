# 📑 Relatório de Auditoria Arquitetural — `task-manager-api`

**Data da Auditoria:** `2026-11-10`  
**Stack Detectada:** `Python 3` / `Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.x)`  
**Domínio da Aplicação:** `Task Manager (tarefas, usuários, categorias, relatórios de produtividade)`  

---

## 📊 1. Resumo Executivo por Severidade

| Severidade | Quantidade Identificada |
|---|---|
| 🚨 **CRITICAL** | `3` |
| ⚠️ **HIGH** | `3` |
| ⚡ **MEDIUM** | `7` |
| 🔵 **LOW** | `7` |
| **TOTAL** | **`20`** |

> **APIs Deprecated:** `Query.get()` (legado no SQLAlchemy 2.x → `db.session.get()`) e `datetime.utcnow()` (deprecated no Python 3.12+). As APIs do catálogo para Flask (`@app.before_first_request`, `json.loads(request.data)`) **não** foram encontradas.
> Callback Hell (#5 do catálogo) não se aplica (Python síncrono).

---

## 🔍 2. Detalhamento dos Achados

### Achado #1: Hardcoded Secrets
- **Severidade:** `CRITICAL`
- **Arquivo / Localização:** `app.py (Linhas 11 e 13)`, `services/notification_service.py (Linhas 7 a 10)`, `seed.py (Linhas 19, 26, 33)`
- **Descrição do Problema:** `SECRET_KEY = 'super-secret-key-123'` e a URI do banco estão fixos no código; o serviço de notificação contém usuário e senha SMTP (`taskmanager@gmail.com` / `senha123`); o seed cria usuários com senhas triviais (`1234`, `abcd`, `pass`), incluindo um admin.
- **Recomendação de Refatoração:** `src/config/settings.py` lendo variáveis de ambiente (`.env` via `python-dotenv`, já listado no `requirements.txt`); SMTP configurável e desabilitado por padrão; senhas do seed via ambiente ou geradas.

### Achado #2: Exposição do hash de senha nas respostas da API
- **Severidade:** `CRITICAL`
- **Arquivo / Localização:** `models/user.py (Linha 21)`, `routes/user_routes.py (Linhas 33, 85, 129, 209)`
- **Descrição do Problema:** `User.to_dict()` inclui o campo `password`; ele é devolvido em `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login`. Como o hash é MD5 sem salt (Achado #5), é trivialmente reversível por rainbow tables.
- **Recomendação de Refatoração:** Remover `password` da serialização pública do Model.

### Achado #3: Autenticação falsa e escalonamento de privilégio
- **Severidade:** `CRITICAL`
- **Arquivo / Localização:** `routes/user_routes.py (Linhas 52, 71 a 72, 119 a 125, 210)`, todas as rotas em `routes/`
- **Descrição do Problema:** O login devolve `'fake-jwt-token-' + id` — token previsível que nenhuma rota valida. Todos os endpoints são públicos: qualquer pessoa cria um usuário com `role: "admin"`, promove/desativa outros usuários via `PUT /users/<id>`, apaga usuários, tasks e categorias.
- **Recomendação de Refatoração:** Token assinado (`itsdangerous`, dependência do Flask) com expiração; middlewares `login_required` / `admin_required`; cadastro público sempre com `role = user`; alteração de `role`/`active` restrita a admin; usuário comum só altera o próprio perfil.

### Achado #4: Bypass de Camadas / Regras em Rotas
- **Severidade:** `HIGH`
- **Arquivo / Localização:** `routes/task_routes.py (Linhas 11 a 299)`, `routes/user_routes.py (Linhas 10 a 211)`, `routes/report_routes.py (Linhas 12 a 223)`
- **Descrição do Problema:** Os handlers fazem tudo: validação, consultas ORM, regras de negócio (atraso, taxa de conclusão), persistência/commit e serialização. Não existe camada de controller; os Models são apenas mapeamento.
- **Recomendação de Refatoração:** `src/models/` (entidades + repositórios/consultas), `src/controllers/` (validação e regras), `src/routes/` (Blueprints finos que só traduzem HTTP ↔ controller).

### Achado #5: Hashing de senhas obsoleto (MD5 sem salt)
- **Severidade:** `HIGH`
- **Arquivo / Localização:** `models/user.py (Linhas 27 a 32)`, `routes/user_routes.py (Linhas 64, 115)`
- **Descrição do Problema:** `hashlib.md5` sem salt; senha mínima de 4 caracteres.
- **Recomendação de Refatoração:** `werkzeug.security.generate_password_hash` / `check_password_hash`; migração transparente: no login bem-sucedido com hash MD5 legado, regravar com o algoritmo novo.

### Achado #6: Modo DEBUG ativo e servidor exposto em 0.0.0.0
- **Severidade:** `HIGH`
- **Arquivo / Localização:** `app.py (Linha 34)`
- **Descrição do Problema:** `debug=True` + `host='0.0.0.0'` expõe o debugger interativo do Werkzeug (execução remota de código) a toda a rede.
- **Recomendação de Refatoração:** `DEBUG` e `HOST` por variável de ambiente, padrão `false` / `127.0.0.1`.

### Achado #7: Queries N+1 no Banco
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `routes/task_routes.py (Linhas 41 a 57)`, `routes/user_routes.py (Linha 22)`, `routes/report_routes.py (Linhas 15 a 28, 53 a 68, 159 a 164)`
- **Descrição do Problema:** `GET /tasks` faz 2 queries extras por task (usuário e categoria); `GET /users` carrega `u.tasks` por usuário; o relatório faz 11 `COUNT` separados + 1 query por usuário; `GET /categories` faz 1 `COUNT` por categoria.
- **Recomendação de Refatoração:** `joinedload`/`JOIN` e agregações `GROUP BY` / `func.sum(case(...))` no Model.

### Achado #8: Falta de paginação em listagens
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `routes/task_routes.py (Linhas 14, 266, 281)`, `routes/user_routes.py (Linha 12)`, `routes/report_routes.py (Linhas 30, 53, 159)`
- **Descrição do Problema:** Todas as listagens fazem `.all()` sem limite.
- **Recomendação de Refatoração:** Paginação opcional (`?page=&per_page=`, com teto) que preserve o formato atual quando os parâmetros não forem enviados.

### Achado #9: Tratamento Inseguro de Exceções
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `routes/task_routes.py (Linhas 62, 137, 204, 236)`, `routes/user_routes.py (Linhas 130, 149)`, `routes/report_routes.py (Linhas 186, 207, 221)`, `utils/helpers.py (Linhas 46, 49, 88)`, `services/notification_service.py (Linhas 23 a 25)`
- **Descrição do Problema:** `except:` nus engolem qualquer erro (inclusive `KeyboardInterrupt`) sem log; não há handler global, então erros não previstos retornam a página HTML padrão do Flask.
- **Recomendação de Refatoração:** Exceções de domínio + `errorhandler` centralizado que loga o stacktrace e devolve JSON `{"error": ...}`.

### Achado #10: APIs Deprecated / Obsoletas
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `Query.get()` → `routes/task_routes.py (Linhas 42, 51, 67, 117, 122, 158, 188, 195, 227)`, `routes/user_routes.py (Linhas 29, 94, 136, 155)`, `routes/report_routes.py (Linhas 105, 192, 213)`; `datetime.utcnow()` → `models/*.py`, `routes/*.py`, `utils/helpers.py (Linha 38)`, `services/notification_service.py (Linha 35)`
- **Descrição do Problema:** `Query.get()` emite `LegacyAPIWarning` no SQLAlchemy 2.x; `datetime.utcnow()` está deprecated desde o Python 3.12.
- **Recomendação de Refatoração:** `db.session.get(Model, id)`; função utilitária `agora_utc()` baseada em `datetime.now(timezone.utc)` (mantendo valores naive em UTC para compatibilidade com os dados gravados).

### Achado #11: Duplicação de código
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** cálculo de atraso em `routes/task_routes.py (Linhas 30 a 39, 71 a 80, 283 a 287)`, `routes/user_routes.py (Linhas 171 a 180)`, `routes/report_routes.py (Linhas 34 a 36, 132 a 135)` vs `models/task.py (Linhas 50 a 60)`; serialização manual em `routes/task_routes.py (Linhas 17 a 28)` vs `Task.to_dict()`; regex de e-mail em `routes/user_routes.py (Linhas 61, 106)` vs `utils/helpers.py (Linhas 19 a 23)`; listas de status/roles repetidas em 6 pontos.
- **Recomendação de Refatoração:** Regras no Model (`Task.is_overdue`) e validações em um único módulo de controller/validators.

### Achado #12: Validação de entrada frágil (erros 500 em vez de 400)
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `routes/task_routes.py (Linhas 96, 113, 141, 167, 182, 261, 264)`, `routes/report_routes.py (Linhas 196 a 202)`, `routes/user_routes.py (Linhas 102, 125)`
- **Descrição do Problema:** `priority: "alta"` → `TypeError` (500); `?priority=abc` → `ValueError` (500); `PUT /categories/<id>` sem corpo → `TypeError` (500); `title` numérico → 500; `active: "não"` é gravado como booleano truthy; `name` vazio aceito no PUT de usuário; cor da categoria não validada.
- **Recomendação de Refatoração:** Validação de tipos no controller com `ValidationError` → HTTP 400.

### Achado #13: Integridade referencial ao excluir categorias
- **Severidade:** `MEDIUM`
- **Arquivo / Localização:** `routes/report_routes.py (Linhas 211 a 223)`, `app.py (Linha 11)`
- **Descrição do Problema:** O SQLite não aplica FKs sem `PRAGMA foreign_keys = ON`; excluir uma categoria deixa tasks com `category_id` apontando para um registro inexistente.
- **Recomendação de Refatoração:** Habilitar FKs por conexão e, ao excluir a categoria, desvincular as tasks (`category_id = NULL`) na mesma transação.

### Achado #14: Logs e Print Statements Dispersos
- **Severidade:** `LOW`
- **Arquivo / Localização:** `routes/task_routes.py (Linhas 149, 153, 219, 234)`, `routes/user_routes.py (Linhas 83, 89, 147)`, `services/notification_service.py (Linhas 21, 24)`, `utils/helpers.py (Linhas 39 a 41)`, `seed.py (Linhas 92 a 95)`
- **Descrição do Problema:** `print()` no lugar de `logging`.
- **Recomendação de Refatoração:** `logging.getLogger(__name__)` com nível configurável.

### Achado #15: Imports e dependências não utilizados
- **Severidade:** `LOW`
- **Arquivo / Localização:** `app.py (Linha 7)`, `routes/task_routes.py (Linha 7)`, `routes/user_routes.py (Linha 6)`, `routes/report_routes.py (Linhas 7 e 8)`, `models/task.py (Linha 3)`, `utils/helpers.py (Linhas 3 a 7)`, `requirements.txt (marshmallow, requests)`
- **Descrição do Problema:** `os, sys, json, time, hashlib, re, math` importados sem uso; `marshmallow` e `requests` nunca usados.
- **Recomendação de Refatoração:** Remover imports e dependências mortas.

### Achado #16: Código morto
- **Severidade:** `LOW`
- **Arquivo / Localização:** `services/notification_service.py (Linhas 1 a 48)`, `utils/helpers.py (Linhas 9 a 116)`, `models/task.py (Linhas 38 a 60)`, `models/user.py (Linhas 34 a 38)`
- **Descrição do Problema:** `NotificationService` nunca é instanciado; de `helpers.py` só `calculate_percentage`/`format_date` são importados (e nem esses são usados); `Task.validate_status`, `validate_priority`, `is_overdue` e `User.is_admin` existem mas as rotas reimplementam a lógica.
- **Recomendação de Refatoração:** Reaproveitar as regras do Model nos controllers e remover o restante.

### Achado #17: Magic Numbers soltos pelo código
- **Severidade:** `LOW`
- **Arquivo / Localização:** `routes/task_routes.py (Linhas 96, 99, 104, 113, 167, 169, 182)`, `routes/user_routes.py (Linhas 64, 115)`, `routes/report_routes.py (Linhas 24 a 28, 45, 129, 180)`
- **Descrição do Problema:** `3`, `200`, `1..5`, `4`, `7` (dias), `<= 2` (alta prioridade), `'#000000'` sem nome.
- **Recomendação de Refatoração:** Constantes nomeadas (`TITULO_MIN`, `PRIORIDADE_MAX`, `DIAS_ATIVIDADE_RECENTE`, `PRIORIDADE_ALTA_MAX`...).

### Achado #18: Nomenclatura ruim de variáveis e código verboso
- **Severidade:** `LOW`
- **Arquivo / Localização:** `routes/report_routes.py (Linhas 24 a 28: p1..p5)`, `routes/task_routes.py (Linhas 16, 51: t, cat)`, `routes/user_routes.py (Linha 14: u)`, `models/category.py (Linha 14: d)`, `models/task.py (Linhas 38 a 60)`, `models/user.py (Linhas 34 a 38)`
- **Descrição do Problema:** Nomes de uma letra e `if/else` aninhados que retornam booleanos.
- **Recomendação de Refatoração:** Nomes descritivos e expressões booleanas diretas.

### Achado #19: CRUD de categorias no módulo de relatórios
- **Severidade:** `LOW`
- **Arquivo / Localização:** `routes/report_routes.py (Linhas 157 a 223)`
- **Descrição do Problema:** Endpoints `/categories` vivem em `report_routes.py`, misturando responsabilidades e dificultando a localização do código.
- **Recomendação de Refatoração:** `category_routes.py` + `category_controller.py` próprios.

### Achado #20: Seed destrutivo e bootstrap acoplado ao import
- **Severidade:** `LOW`
- **Arquivo / Localização:** `seed.py (Linhas 1 a 16)`, `app.py (Linhas 9 a 31)`
- **Descrição do Problema:** `seed.py` apaga **todos** os dados sem confirmação; `app.py` cria o app e executa `db.create_all()` no import do módulo (sem application factory), o que impede testes isolados.
- **Recomendação de Refatoração:** Application factory `create_app(config)`; seed movido para `src/config/seed.py`, idempotente, acionado por `SEED_DB=true` fora de produção (mantendo `python seed.py` como atalho).

---

## 🏗️ 3. Plano de Reestruturação para MVC

1. **Camada Model:** `src/models/{task,user,category}.py` com entidades SQLAlchemy, serialização pública (sem `password`), regra `is_overdue`, hashing seguro com migração do MD5, e funções de consulta (listagens com `joinedload`, agregações de relatórios em poucas queries, paginação).
2. **Camada Controller:** `src/controllers/{task,user,category,report,auth}_controller.py` concentrando validações (tipos, faixas, status, roles), regras de autorização por recurso e orquestração; exceções de domínio (`ValidationError`, `NotFoundError`, `ConflictError`, `ForbiddenError`, `UnauthorizedError`).
3. **Camada Routes / Views:** Blueprints finos em `src/routes/` mantendo **os mesmos paths, métodos e formatos de resposta**; `category_routes.py` separado; middlewares `login_required`/`admin_required` e `errorhandler` global em `src/middlewares/`.
4. **Configurações:** `src/config/settings.py` (`SECRET_KEY`, `DATABASE_URL`, `DEBUG`, `HOST`, `PORT`, `CORS_ORIGINS`, `TOKEN_TTL`, `SMTP_*`, `SEED_*`), `src/config/database.py` (instância `db` + `PRAGMA foreign_keys`), `.env.example`, logging padronizado; `app.py` na raiz mantido como entrypoint de compatibilidade.
