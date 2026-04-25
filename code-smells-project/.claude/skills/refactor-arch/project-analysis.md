# Project Analysis Heuristics

## 1. Language Detection

Procure por estes indicadores na ordem:

| Indicador | Linguagem |
|-----------|-----------|
| `requirements.txt`, arquivos `.py`, `from flask` / `import flask` | Python |
| `package.json`, arquivos `.js`, `require('express')` / `import express` | Node.js/JavaScript |
| `go.mod`, arquivos `.go`, `package main` | Go |
| `pom.xml` ou `build.gradle`, arquivos `.java` | Java |

## 2. Framework Detection

### Python
- `flask` em requirements.txt → Flask (verifique versao no arquivo)
- `django` em requirements.txt → Django
- `fastapi` em requirements.txt → FastAPI
- Se `flask-sqlalchemy` tambem esta presente → Flask + SQLAlchemy ORM

### Node.js
- `express` em package.json dependencies → Express (verifique versao)
- `koa` em package.json dependencies → Koa
- `fastify` em package.json dependencies → Fastify

Extraia a versao da dependencia (ex: `"express": "^4.18.2"` → Express 4.18).

## 3. Database Detection

Procure por:
- `sqlite3` import ou arquivos `.db` → SQLite
- `psycopg2` ou `postgresql://` em connection strings → PostgreSQL
- `pymongo` ou `mongodb://` → MongoDB
- `flask-sqlalchemy` ou `SQLAlchemy` → SQLAlchemy ORM (verifique DB subjacente)
- `:memory:` → SQLite in-memory (dados perdidos ao reiniciar)
- `mysql` imports → MySQL

Verifique se usa ORM (SQLAlchemy, Sequelize, Prisma) ou queries diretas.

## 4. Architecture Classification

Leia todos os arquivos fonte e classifique:

1. **Monolitica** — Toda logica em 1-3 arquivos (routes, DB queries, business rules juntos)
2. **Partial separation** — Alguns arquivos separados (models/, routes/) mas logica vaza entre camadas
3. **Layered** — Separacao clara (models/, controllers/, routes/, config/)
4. **MVC** — Separacao Model-View-Controller adequada

### Sinais para classificar:
- Routes chamando DB diretamente → Monolitica ou separacao pobre
- Controllers com queries SQL → Logica de negocio misturada com acesso a dados
- Models com request/response → Violacao de camada
- Multiplas entidades em um arquivo → God Class/File
- Se existe controllers/ mas routes chamam models diretamente → separacao parcial
- Se existe models/, routes/, services/, utils/ → verificar se a logica realmente respeita as camadas

## 5. Domain Detection

Leia as definicoes de rotas, nomes de models e endpoints:

| Palavras-chave nas rotas | Dominio |
|---------------------------|---------|
| produtos, pedidos, usuarios, carrinho | E-commerce |
| courses, enrollments, payments, checkout | LMS (Learning Management System) |
| tasks, projects, users, categories | Task/Project Management |
| posts, comments, users, likes | Social Media / Blog |

## 6. Dependency Mapping

Liste todas as dependencias externas de:
- Python: `requirements.txt` ou `pyproject.toml`
- Node.js: `package.json` → `dependencies` (NAO incluir devDependencies)

## 7. Source File Analysis

Conte todos os arquivos de codigo fonte:
- Python: `*.py`
- Node.js: `*.js` (excluir `node_modules/`)
- NAO contar: `.git/`, `__pycache__/`, `node_modules/`, `*.db`, `*.json` de lock

Estime o total de linhas de codigo somando todos os arquivos fonte.
Liste cada arquivo com sua funcao resumida.
