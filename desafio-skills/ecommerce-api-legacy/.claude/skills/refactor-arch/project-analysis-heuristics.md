# Heurísticas de análise de projeto (agnóstico)

## 1. Detecção de linguagem e runtime

| Sinal | Linguagem provável |
|--------|---------------------|
| `requirements.txt`, `*.py`, `pyproject.toml` | Python |
| `package.json`, `*.js` | JavaScript (Node) |
| `go.mod` | Go (fora do escopo destes desafios; ainda assim mapear) |

## 2. Framework web

### Python

- **Flask:** `from flask import Flask`, `Flask(__name__)`, `requirements.txt` com `flask`.
- **FastAPI:** `FastAPI()` — tratar como “camada de rotas moderna”; MVC ainda se aplica (models/services/controllers).

### Node.js

- **Express:** `require('express')`, `express()`, `app.get/post`, dependência `express` em `package.json`.

## 3. Banco de dados

| Sinal | Conclusão |
|--------|-----------|
| `sqlite3.connect`, arquivo `*.db` | SQLite em arquivo |
| `new sqlite3.Database(':memory:')` | SQLite em memória |
| `SQLAlchemy`, `db.Model`, `flask_sqlalchemy` | SQLAlchemy ORM |
| Strings `CREATE TABLE` em código | Schema gerenciado manualmente |

## 4. Contagem de arquivos fonte

Incluir: `**/*.py` ou `**/*.js` do diretório do app (excluir `node_modules`, `venv`, `.venv`, `__pycache__`, `dist`, `build`).

Reportar **N** e listar pastas principais.

## 5. Mapeamento “arquivo → papel MVC” (atual)

Use para descrever a arquitetura **antes** da refatoração:

| Padrão observado | Classificação típica |
|------------------|----------------------|
| Rotas definidas no mesmo arquivo que SQL e regras | Monólito / sem MVC |
| `routes/` + `models/` mas lógica pesada nas rotas | MVC parcial |
| Classe única “Manager” com DB + HTTP | God Class |

## 6. Domínio

Inferir de:

- prefixos de rota (`/tasks`, `/produtos`, `/api/checkout`)
- nomes de tabelas / models
- README do projeto

## 7. Ramificações por stack

- **Flask + SQL raw:** risco alto de SQL injection por concatenação — priorizar leitura de `*.py` com `execute("... "+`.
- **Express + sqlite3 callbacks:** risco de callback hell e N+1 — inspecionar `forEach` aninhados com queries.
