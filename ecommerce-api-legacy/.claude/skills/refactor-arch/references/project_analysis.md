# Heurísticas de Análise de Projeto

Este guia de referência descreve as heurísticas e padrões para identificar a stack tecnológica, banco de dados, domínio de negócio e arquitetura atual de qualquer projeto de backend.

## 1. Detecção de Linguagem e Runtime

| Sinais no Diretório | Linguagem / Ambiente |
| :--- | :--- |
| `package.json`, `package-lock.json`, arquivos `.js`, `.ts` | Node.js (JavaScript / TypeScript) |
| `requirements.txt`, `pyproject.toml`, `Pipfile`, arquivos `.py` | Python |
| `Cargo.toml`, arquivos `.rs` | Rust |
| `go.mod`, arquivos `.go` | Go |

## 2. Detecção de Framework

### Python
- **Flask**: Presença de `import flask` ou `from flask import ...` nos arquivos `.py`. Dependência `flask` no `requirements.txt`.
- **FastAPI**: Presença de `import fastapi` ou `from fastapi import ...`. Dependência `fastapi` no `requirements.txt`.
- **Django**: Presença de `django-admin`, `manage.py`, ou imports de `django`.

### Node.js
- **Express**: Dependência `express` no `package.json` e `require('express')` ou `import express` nos arquivos `.js`/`.ts`.
- **NestJS**: Dependência `@nestjs/core` no `package.json`, uso de decoradores como `@Controller()`, `@Get()`.

## 3. Detecção de Banco de Dados

Analise as dependências e strings de conexão no código:

- **SQLite**:
  - Python: `import sqlite3` ou URI começando com `sqlite:///`.
  - Node.js: Dependência `sqlite3` ou `better-sqlite3`.
- **PostgreSQL**:
  - Python: Dependência `psycopg2` ou `pg8000`.
  - Node.js: Dependência `pg`.
- **MySQL**:
  - Python: Dependência `mysql-connector` ou `pymysql`.
  - Node.js: Dependência `mysql2`.
- **ORM / ODM**:
  - Python: `flask_sqlalchemy` ou `SQLAlchemy` (ORM), `peewee`.
  - Node.js: `sequelize`, `prisma`, `typeorm`, `mongoose` (MongoDB).

## 4. Mapeamento de Arquitetura

Para classificar a arquitetura atual do projeto, avalie a organização de arquivos e a distribuição de responsabilidades:

### A) Monolítica Sem Camadas (Tudo em Poucos Arquivos)
- **Sinais**: Menos de 5 arquivos contendo todas as rotas, lógicas de negócio, queries de banco e configurações.
- **Exemplo**: `app.py` que cria rotas, `models.py` que faz queries SQL brutas e manipula request/response, e `database.py` que inicializa o banco de dados.
- **Acoplamento**: Altíssimo. Alterar o banco exige alterar as rotas.

### B) Parcialmente Organizada
- **Sinais**: O projeto possui pastas separadas como `models/`, `routes/`, `services/`, ou `utils/`, mas ainda viola separação de responsabilidades.
- **Exemplo**: Rotas (`routes/`) que calculam faturamento bruto, fazem validações complexas, gerenciam status e disparam e-mails manualmente.
- **Acoplamento**: Médio. Há divisão física de pastas, mas forte acoplamento lógico nas rotas ou controllers (Fat Controllers).

### C) MVC (Model-View-Controller) Alvo
- **Config**: Configurações centralizadas extraídas do código (variáveis de ambiente, configurações do app).
- **Models**: Camada pura de dados e abstração de persistência (completamente isolada de requisições HTTP e de lógica de rotas).
- **Controllers**: Orquestradores de fluxo. Recebem dados validados, invocam regras de negócio nos models ou serviços, e definem a resposta a ser enviada.
- **Views / Routes**: Apenas mapeiam os caminhos de URL (endpoints) para as funções controladoras correspondentes e gerenciam a entrada/saída de dados (JSON/HTML).
- **Middlewares / Handlers**: Camada de processamento de requisição cruzada (logging, segurança, tratamento centralizado de erros).
