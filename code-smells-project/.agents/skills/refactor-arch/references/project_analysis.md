# Heurísticas de Análise de Projeto

Este documento define as heurísticas padronizadas para a **Fase 1 (Project Analysis)** da skill `refactor-arch`. O objetivo é inspecionar o repositório, detectar a stack tecnológica (linguagem, framework, banco de dados), mapear a topologia de diretórios e extrair métricas base sem alterar nenhum arquivo.

---

## 1. Detecção de Linguagem e Gerenciador de Dependências

A detecção da linguagem primária é orientada pela presença de arquivos de manifesto na raiz ou no primeiro nível de diretórios:

| Arquivo de Manifesto | Linguagem Primária | Gerenciador de Pacotes |
|---|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml`, `setup.py` | Python | `pip` / `poetry` / `pipenv` |
| `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` | JavaScript / TypeScript (Node.js) | `npm` / `yarn` / `pnpm` |
| `go.mod` | Go | `go modules` |
| `pom.xml`, `build.gradle`, `build.gradle.kts` | Java / Kotlin | `maven` / `gradle` |
| `composer.json` | PHP | `composer` |
| `Gemfile` | Ruby | `bundler` |
| `Cargo.toml` | Rust | `cargo` |
| `*.csproj`, `*.sln` | C# (.NET) | `dotnet` / `nuget` |

### Heurística de Resolução:
1. Examine os arquivos no diretório raiz do projeto.
2. Leia o conteúdo do manifesto para identificar dependências declaradas.
3. Conte os arquivos por extensão (`.py`, `.js`, `.ts`, etc.) para confirmar a linguagem predominante.

---

## 2. Detecção de Framework Web

A detecção de framework baseia-se na inspeção de dependências declaradas e imports no código-fonte:

### Python:
- **Flask**: Presença de `flask`, `flask-cors`, `flask-sqlalchemy` no `requirements.txt` ou imports `from flask import Flask`.
- **FastAPI**: Presença de `fastapi`, `uvicorn` ou imports `from fastapi import FastAPI`.
- **Django**: Presença de `django` ou arquivo `manage.py`, `settings.py`.
- **Bottle/Tornado/Sanic**: Presença de pacotes correspondentes.

### Node.js / JavaScript:
- **Express**: Presença de `"express"` em `package.json` ou `require('express')` / `import express from 'express'`.
- **Fastify**: Presença de `"fastify"` em `package.json`.
- **NestJS**: Presença de `@nestjs/core` em `package.json`.
- **Koa**: Presença de `"koa"` em `package.json`.

---

## 3. Detecção de Banco de Dados e Camada de Persistência

Inspecione os arquivos de configuração, strings de conexão e bibliotecas de banco de dados:

### Bibliotecas e Drivers:
- **SQLite**: Import de `sqlite3`, arquivos `.db`, `.sqlite`, `.sqlite3`, ou URI contendo `sqlite:///`.
- **PostgreSQL**: Dependências `psycopg2`, `pg`, `pg-promise` ou URI contendo `postgresql://` / `postgres://`.
- **MySQL / MariaDB**: Dependências `mysql`, `mysql2`, `pymysql` ou URI contendo `mysql://`.
- **MongoDB**: Dependências `pymongo`, `mongodb`, `mongoose` ou URI contendo `mongodb://`.
- **ORM / Query Builders**:
  - Python: `SQLAlchemy`, `Flask-SQLAlchemy`, `Peewee`, `Tortoise-ORM`.
  - Node.js: `Prisma`, `TypeORM`, `Sequelize`, `Knex`, `Mongoose`.
  - Raw SQL: Uso direto de `sqlite3.connect()`, `db.cursor()`, `db.run()`, `db.all()`, `db.query()`.

---

## 4. Mapeamento da Arquitetura Atual

A classificação arquitetural do projeto segue as seguintes regras estruturais:

### A. Monolítica Não-Estruturada (Tudo em Raiz ou "Frankenstein")
- **Critérios**: Menos de 5 a 8 arquivos, todos os controladores, modelos, regras e rotas concentrados em arquivos grandes como `app.py`, `models.py`, `controllers.py` ou `AppManager.js`.
- **Sintoma**: Não há pastas dedicadas por camada (`models/`, `views/`, `controllers/`, `services/`).

### B. Arquitetura Híbrida / Parcialmente Organizada
- **Critérios**: Presença de algumas pastas (ex.: `models/`, `routes/`, `services/`), mas com vazamento de responsabilidades (ex.: queries dentro de rotas, controllers chamando banco diretamente, ausência de camada de controle unificada, lógica de negócio dispersa).

### C. Arquitetura MVC Estruturada
- **Critérios**: Separação clara em `models/` (entidades e repositórios), `views/` ou `routes/` (apenas transporte HTTP/roteamento) e `controllers/` (orquestração do fluxo), com injeção de dependências e configuração desacoplada (`config/`).

---

## 5. Mapeamento de Domínio e Recursos

Para cada endpoint identificado no código (via `@app.route`, `app.add_url_rule`, `app.get`, `app.post`, `app.use`, Blueprints ou routers):
1. Liste a URL base e parâmetros dinâmicos (ex: `/produtos/<int:id>`, `/api/checkout`).
2. Mapeie o método HTTP correspondente (`GET`, `POST`, `PUT`, `DELETE`).
3. Agrupe os endpoints por entidade de domínio (ex: *Produtos*, *Usuários*, *Pedidos*, *Matrículas*, *Tarefas*, *Relatórios*).
4. Mapeie as tabelas do banco de dados declaradas (`CREATE TABLE` ou classes ORM).

---

## 6. Formato de Saída Obrigatório da Fase 1

Ao concluir a Fase 1, imprima exatamente o seguinte bloco informativo formatado no terminal/conversa:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <Nome da Linguagem e Versão detectada/inferida>
Framework:     <Nome e Versão do Framework Web>
Dependencies:  <Principais bibliotecas detectadas>
Domain:        <Domínio da aplicação e principais recursos>
Architecture:  <Classificação arquitetural atual e diagnóstico>
Source files:  <Quantidade exata de arquivos de código analisados>
DB tables:     <Lista de tabelas/coleções encontradas no schema>
Endpoints:     <Quantidade total de rotas/endpoints mapeados>
================================
```
