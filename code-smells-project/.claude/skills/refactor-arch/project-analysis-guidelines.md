# Project Analysis Guidelines

## Objetivo
Fornecer regras e heurísticas para detectar linguagem, framework, banco de dados e arquitetura de um projeto legado.

## Linguagem e Framework
### Python
- Detecte `import flask`, `from flask import`, `Flask(__name__)` → Flask.
- Detecte `from flask_sqlalchemy import SQLAlchemy` → Flask + SQLAlchemy.
- Detecte `app.add_url_rule`, `@app.route`, `Blueprint`.
- Detecte `requirements.txt` ou `setup.py` com `Flask`, `flask-cors`, `sqlalchemy`.

### JavaScript / Node.js
- Detecte `require('express')`, `import express from 'express'`, `app.use(express.json())` → Express.
- Detecte `app.listen`, `express.Router()`, `module.exports =`.
- Detecte `package.json` com dependências `express`, `sqlite3`, `body-parser`.

## Banco de Dados
- Detecte arquivos `database.py`, `sqlite3.connect`, `sqlite3.Database`, `SQLAlchemy`, `pg`, `mysql`, `mongoose`.
- Identifique a persistência via queries SQL ou ORM.
- Liste tabelas se conseguir extrair `CREATE TABLE` ou `db.run`/`cursor.execute`.

## Arquitetura Atual
### Monolítico
- Todos os endpoints e lógica em um único arquivo.
- Models de dados, validação e rotas misturados.

### Parcialmente Organizado
- Existe alguma separação de `models/`, `routes/`, `services/` ou `controllers/`, mas ainda há vazamento de lógica entre camadas.

### MVC / Estrutura clara
- `models`, `controllers` e `routes/views` separados.
- `config` e `middlewares` também definidos separadamente.

## Domínio e Contexto
- Determine a área funcional principal do projeto.
- Exemplos:
  - E-commerce API (produtos, pedidos, usuários)
  - LMS API / checkout
  - Task Manager API

## Output Esperado da Análise
- Language: Python / JavaScript
- Framework: Flask / Express
- Dependencies: principais bibliotecas detectadas
- Domain: descrição curta do domínio
- Architecture: monolítico / parcialmente organizado / MVC parcial
- Source files: lista e contagem de arquivos analisados
- DB tables: entidades ou tabelas conhecidas

## Regras de Análise
- Não altere arquivos nesta fase.
- Extraia sinais de arquitetura mesmo quando o código estiver parcialmente organizado.
- Se houver múltiplos projetos no mesmo diretório, limite-se ao projeto atual.
