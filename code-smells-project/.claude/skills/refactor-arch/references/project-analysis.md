# Análise de Projeto — Heurísticas (Fase 1)

Objetivo: descobrir **o que** o projeto é e **como** está organizado, usando evidências (manifestos, imports, nomes) — nunca suposições.

## 1. Inventário de arquivos

```bash
# arquivos de código (ajuste extensões conforme a linguagem detectada)
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.rb" -o -name "*.go" -o -name "*.java" -o -name "*.php" \) \
  -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/venv/*" \
  -not -path "*/__pycache__/*" -not -path "*/.git/*" -not -path "*/.claude/*" | sort
# linhas por arquivo
... | xargs wc -l
```

Conte **somente** código-fonte da aplicação (inclua scripts como `seed.py`; exclua lockfiles, bancos `.db`, `.http`, docs).

## 2. Detecção de linguagem

| Evidência | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`, arquivos `*.py` | Python |
| `package.json` + `*.js` / `*.mjs` / `*.cjs` | JavaScript (Node.js) |
| `package.json` + `tsconfig.json` / `*.ts` | TypeScript (Node.js) |
| `go.mod` | Go |
| `pom.xml`, `build.gradle` | Java/Kotlin |
| `Gemfile` | Ruby |
| `composer.json` | PHP |

Versão: `python_requires`, `.python-version`, `engines.node` no `package.json`, `runtime.txt`, `Dockerfile` (`FROM python:3.x`). Se não declarada, informe "não declarada" e a versão local (`python3 --version` / `node --version`) entre parênteses.

## 3. Detecção de framework

| Sinal (manifesto / import) | Framework |
|---|---|
| `flask` em requirements; `from flask import Flask`; `Blueprint`; `@app.route` / `add_url_rule` | Flask |
| `django` ; `manage.py`; `settings.py`; `urls.py` | Django |
| `fastapi`; `@app.get(...)`; `APIRouter` | FastAPI |
| `express` em dependencies; `require('express')`; `app.get/post(...)`; `express.Router()` | Express |
| `@nestjs/core`; decorators `@Controller` | NestJS |
| `fastify`, `koa`, `hapi` | respectivos |
| `spring-boot-starter-web`; `@RestController` | Spring Boot |

Use a **versão exata** do manifesto (`flask==3.1.1`, `"express": "^4.18.2"`). Para `^`/`~`, reporte o range e, se houver lockfile, a versão resolvida (`package-lock.json` → `node_modules/express/package.json`).

## 4. Banco de dados e acesso a dados

| Sinal | Banco / acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect(` | SQLite via driver cru (SQL manual) |
| `require('sqlite3')`, `new sqlite3.Database(` | SQLite via driver cru (callbacks) |
| `':memory:'` | banco em memória (dados somem no restart) |
| `flask_sqlalchemy`, `SQLAlchemy()`, `db.Model` | ORM SQLAlchemy |
| `SQLALCHEMY_DATABASE_URI = 'sqlite:///x.db'` | SQLite via ORM |
| `psycopg2`, `pg`, `mysql`, `pymysql`, `mongoose`, `prisma`, `sequelize`, `typeorm` | Postgres/MySQL/Mongo/ORMs |

Tabelas/entidades: procure `CREATE TABLE <nome>`, `__tablename__ = '<nome>'`, `class X(db.Model)`, `mongoose.model('X'`, `sequelize.define('x'`.

## 5. Domínio da aplicação

Inferir pelos substantivos dominantes em tabelas, rotas e mensagens:

- `produtos`, `pedidos`, `itens_pedido`, `carrinho`, `checkout` → **E-commerce**
- `courses`, `enrollments`, `students`, `lessons` → **LMS / plataforma de cursos** (se tiver `payments`/`checkout`, mencione o fluxo de checkout)
- `tasks`, `projects`, `categories`, `due_date`, `priority` → **Task Manager**
- `accounts`, `transactions`, `balance` → **Financeiro**

Descreva em 1 linha: *"<Tipo de API> (<entidade1>, <entidade2>, ...)"*.

## 6. Mapeamento de arquitetura atual

Classifique o projeto em uma das categorias abaixo (use a mais próxima e justifique em poucas palavras):

| Categoria | Sinais |
|---|---|
| **Monolito "God File/Class"** | 1–5 arquivos; um arquivo/classe contém conexão com banco + SQL + regras + rotas (ex.: classe `AppManager` com `initDb()` e `setupRoutes()`) |
| **Monolito com pseudo-camadas** | arquivos chamados `models`/`controllers` existem, mas `models` mistura SQL + regras + formatação de vários domínios e o entry point ainda contém rotas e SQL |
| **Camadas parciais** | pastas `models/`, `routes/`, `services/`, `utils/` existem, mas rotas contêm regra de negócio/queries, services estão desconectados, utils não são usados, config hardcoded |
| **MVC/Layered adequado** | camadas com dependências unidirecionais (routes → controllers → models), config externa, error handler central |

Perguntas para mapear:
1. Onde a app é criada (entry point)? Existe *composition root* ou tudo é global?
2. Onde ficam as rotas? (`@app.route`, `add_url_rule`, `Blueprint`, `app.get`, `router.post`)
3. Onde ficam as queries? Estão em quantos arquivos diferentes?
4. Onde está a regra de negócio (cálculos, validações, status)?
5. Existe estado global mutável? (`global x`, variável de módulo reatribuída, `let cache = {}` exportado)
6. Como a configuração é carregada? (literal no código vs `os.environ`/`process.env`)
7. Como erros são tratados? (try/except em cada handler vs handler central)

## 7. Inventário de endpoints

```bash
# Flask
grep -rnE "@[a-z_]+\.route\(|add_url_rule\(" --include=*.py .
# Express
grep -rnE "(app|router)\.(get|post|put|patch|delete)\(" --include=*.js --include=*.ts . | grep -v node_modules
# FastAPI
grep -rnE "@(app|router)\.(get|post|put|patch|delete)\(" --include=*.py .
```

Para Blueprints/Routers, combine o `url_prefix`/`app.use('/prefix', router)` com o path da rota.

## 8. Entry point e execução

- Python: arquivo com `if __name__ == "__main__":` / `app.run(...)`; README; `Procfile`.
- Node: `scripts.start` / `main` do `package.json`; `app.listen(`.
- Anote porta (`port=5000`, `config.port`, `process.env.PORT`), `debug=True`, `host='0.0.0.0'` e se existe script de seed (`seed.py`, `npm run seed`).

## 9. Baseline de comportamento

Antes de qualquer refatoração, registre o comportamento atual para comparação na Fase 3:

- **Python/Flask**: em uma cópia temporária, `from app import app; c = app.test_client(); c.get('/rota')` — ou suba o servidor numa porta livre.
- **Node/Express**: em uma cópia temporária, `PORT=<livre> npm start &` e `curl -s -w ' [%{http_code}]' ...`.
- Registre para cada endpoint: método, path, payload usado, status, chaves do JSON de resposta.
- macOS: a porta 5000 costuma estar ocupada pelo AirPlay Receiver — confira com `lsof -nP -iTCP:5000 -sTCP:LISTEN`.
