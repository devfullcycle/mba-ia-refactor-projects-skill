---

#### 2. `analise_heuristica.md` (Análise & Heurísticas)

```markdown
# 📐 Heurísticas para Análise de Projeto Legado

Este documento guia o agente de IA na detecção automática da stack, banco de dados e arquitetura de qualquer projeto legado.

## 1. Detecção de Linguagem e Framework

| Arquivo de Sinalização | Imports / Sintaxe Característica | Framework Detectado |
|---|---|---|
| `requirements.txt`, `Pipfile`, `pyproject.toml` ou arquivos `.py` | `from flask import Flask` / `import flask` | **Python / Flask** |
| `package.json` ou arquivos `.js` | `require('express')` / `import express from 'express'` | **Node.js / Express** |
| `requirements.txt` ou arquivos `.py` | `import fastapi` / `from fastapi import FastAPI` | **Python / FastAPI** |

## 2. Detecção de Banco de Dados e ORM

- **SQLite3:** Presença de `sqlite3`, arquivo `.db`, `.sqlite` ou `sqlite3.Database(':memory:')`.
- **SQLAlchemy (Python):** Presença de `flask_sqlalchemy`, `db.Model`, `db.Column`.
- **PostgreSQL / MySQL:** Presença de `psycopg2`, `mysql.connector`, `pg`, `mysql2`.

## 3. Mapeamento de Arquitetura Atual

1. **Estrutura de Pastas Monolítica:** Todos os arquivos (`app.py`, `models.py`, `controllers.py`) na raiz ou em arquivo único.
2. **Estrutura Parcialmente Organizada:** Pastas existentes (`models/`, `routes/`), mas com violações de acoplamento (ex: chamadas SQL diretas dentro de arquivos de rotas).