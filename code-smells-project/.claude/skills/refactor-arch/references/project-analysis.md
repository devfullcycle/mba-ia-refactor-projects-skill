# Heurísticas de Análise de Projeto (Fase 1)

Detecte tudo a partir de evidências nos arquivos. Nunca chute: se algo não for inferível, declare "não identificado".

## 1. Detecção de linguagem

| Evidência | Linguagem |
|---|---|
| `*.py`, `requirements.txt`, `pyproject.toml`, `Pipfile` | Python |
| `*.js`/`*.mjs`/`*.cjs`, `package.json` | JavaScript (Node.js) |
| `*.ts`, `tsconfig.json` | TypeScript (Node.js) |
| `*.rb`, `Gemfile` | Ruby |
| `*.php`, `composer.json` | PHP |
| `*.java`, `pom.xml`, `build.gradle` | Java |
| `*.go`, `go.mod` | Go |
| `*.cs`, `*.csproj` | C# |

Se houver mais de uma, a linguagem principal é a dos arquivos de aplicação (não de scripts auxiliares).

## 2. Detecção de framework e versão

Procure no manifesto de dependências e nos imports do entry point:

| Evidência (manifesto ou import) | Framework |
|---|---|
| `flask` / `from flask import` | Flask |
| `django` / `INSTALLED_APPS` | Django |
| `fastapi` / `from fastapi import` | FastAPI |
| `express` / `require('express')` | Express |
| `@nestjs/core` | NestJS |
| `koa` | Koa |
| `rails` | Ruby on Rails |
| `laravel/framework` | Laravel |
| `spring-boot` | Spring Boot |

**Versão**: extraia do manifesto (`requirements.txt` com `==`, `package.json` em `dependencies`, lockfiles). Reporte a restrição declarada (ex.: `express ^4.18.2`).

## 3. Detecção de banco de dados

| Evidência | Banco / acesso |
|---|---|
| `import sqlite3`, `sqlite3.connect(...)`, arquivo `*.db` | SQLite (driver direto) |
| `require('sqlite3')`, `new sqlite3.Database(...)` | SQLite (Node) — `:memory:` indica banco em memória |
| `flask_sqlalchemy`, `SQLAlchemy()`, `db.Model` | SQLAlchemy (ORM) — veja `SQLALCHEMY_DATABASE_URI` para o banco real |
| `psycopg2`, `pg`, `postgres://` | PostgreSQL |
| `mysql`, `pymysql`, `mysql2` | MySQL |
| `mongoose`, `pymongo` | MongoDB |
| `prisma`, `sequelize`, `typeorm` | ORM Node — veja config para o banco real |

**Tabelas/entidades**: extraia de `CREATE TABLE ...`, classes `db.Model`/entities do ORM, ou migrations.

## 4. Identificação do domínio

Combine sinais para descrever o que a aplicação faz em uma frase:
- Nomes de tabelas/entidades (ex.: `produtos, pedidos` → e-commerce; `tasks, categories` → gerenciador de tarefas; `courses, enrollments, payments` → LMS/checkout).
- Nomes de rotas e endpoints.
- Strings de mensagens, README do projeto, nome do pacote.

## 5. Mapeamento da arquitetura atual

Classifique em um dos perfis (isso muda a estratégia da Fase 3):

| Perfil | Sinais |
|---|---|
| **Monolito em arquivo único** | Toda a lógica (rotas + negócio + dados) em 1 arquivo |
| **Monolito em poucos arquivos** | Arquivos separados por tipo técnico (ex.: `app`, `controllers`, `models`) mas sem isolamento real de responsabilidades — SQL nos "models", validação nos "controllers", tudo global |
| **God Class** | Uma classe concentra conexão de banco, schema/seed, rotas e regras de negócio |
| **Parcialmente organizado** | Existem diretórios de camadas (`models/`, `routes/`, `services/`...), mas com vazamentos: lógica de negócio nas rotas, camadas ignoradas, duplicação |
| **MVC adequado** | Camadas presentes e respeitadas (raro em projetos legados) |

Para mapear:
1. Identifique o **entry point** (arquivo que sobe o servidor: `app.py`, `src/app.js`, `main.*`, script `start` do `package.json`).
2. Siga os imports a partir dele e anote a responsabilidade real de cada arquivo (roteamento, negócio, acesso a dados, configuração, utilidades).
3. Registre onde as responsabilidades se misturam — isso alimenta a Fase 2.

## 6. Contagem de arquivos

`Source files` = arquivos de código-fonte da aplicação. **Incluir**: código da aplicação e scripts de seed. **Excluir**: dependências instaladas (`node_modules/`, `venv/`), caches (`__pycache__/`), lockfiles, `.claude/`, documentação, arquivos de requisição (`*.http`).
