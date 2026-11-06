# Análise de Codebase — task-manager-api

> Gerado pela skill `refactor-arch` (Fase 1 — Análise).
> Data: 2026-10-22 | Reexecução: 2026-11-05 | Raiz: `/home/eric-ogata/codes/full_cycle/mba_engenharia_ia/desafios/desafio3/mba-ia-refactor-projects-skill/task-manager-api`

## 1. Resumo

| Campo | Valor |
|---|---|
| Linguagem | Python 3 (12.3 no ambiente) |
| Framework | Flask 3.0.0 (declarado) |
| Dependências | flask==3.0.0, flask-sqlalchemy==3.1.1, flask-cors==4.0.0, marshmallow==3.20.1, requests==2.31.0, python-dotenv==1.0.0 |
| Banco de dados | Relacional — SQLite (via Flask-SQLAlchemy) |
| Domínio | Task Manager / gestão de tarefas — tasks, usuários, categorias e relatórios |
| Arquitetura | Monolítico em camadas (Layered) parcial — `routes/` contém roteamento **e** regra de negócio; `services/` existe mas é código morto |
| Entrypoint | `app.py` |
| Tamanho | 15 arquivos `.py` (~1158 LOC, incluindo `__init__.py` de 1 linha) |
| Testes | Nenhum (sem `tests/`, sem pytest) |
| Configuração | Hardcoded em `app.py`; `python-dotenv` declarado mas não utilizado |

## 2. Evidências de detecção

### 2.1 Linguagem
- Manifest: `requirements.txt` — dependências Python (`flask`, `flask-sqlalchemy`, ...).
- Extensões: `.py` = 15 arquivos; nenhuma outra extensão de código.
- **Veredito:** Python 3 — confiança: **alta** (manifesto + código confirmam).

### 2.2 Framework
- Dependências candidatas: `flask==3.0.0`, `flask-sqlalchemy==3.1.1`, `flask-cors==4.0.0`.
- Confirmado no código: `app.py:1` (`from flask import Flask`), `app.py:9` (`app = Flask(__name__)`), `app.py:16` (`db.init_app(app)`), blueprints em `app.py:18-20`.
- Confirmado no código: `routes/task_routes.py:9` (`Blueprint('tasks', ...)`), `routes/user_routes.py:8`, `routes/report_routes.py:10`.
- **Veredito:** Flask 3.0.0 (declarado) — confiança: **alta**.

### 2.3 Banco de dados
- Driver/ORM: `flask-sqlalchemy==3.1.1` → SQLAlchemy ORM (`database.py:1-3`).
- String de conexão: `app.py:11` — `'sqlite:///tasks.db'`.
- Schema criado em runtime por `db.create_all()` (`app.py:30-31`), sem migrations.
- **Veredito:** Relacional — SQLite (arquivo local `tasks.db`), via ORM SQLAlchemy.

### 2.4 Domínio
- Rotas detectadas: `/`, `/health`, `/tasks` (GET/POST), `/tasks/<id>` (GET/PUT/DELETE), `/tasks/search`, `/tasks/stats`, `/users` (GET/POST), `/users/<id>` (GET/PUT/DELETE), `/users/<id>/tasks`, `/login`, `/reports/summary`, `/reports/user/<id>`, `/categories` (GET/POST), `/categories/<id>` (PUT/DELETE).
- Entidades: `Task`, `User`, `Category` (`models/`).
- **Veredito:** API de Task Manager — CRUD de tarefas, usuários e categorias, busca, estatísticas e relatórios de produtividade.

## 3. Inventário

```
task-manager-api/
├── app.py                     # entrypoint + config + rotas / e /health
├── database.py                # instância SQLAlchemy
├── seed.py                    # script de carga inicial
├── requirements.txt
├── models/
│   ├── __init__.py
│   ├── category.py
│   ├── task.py
│   └── user.py
├── routes/
│   ├── __init__.py
│   ├── report_routes.py       # relatórios + CRUD de categorias
│   ├── task_routes.py         # CRUD de tasks + busca + stats
│   └── user_routes.py         # CRUD de usuários + login
├── services/
│   ├── __init__.py
│   └── notification_service.py  # nunca importado (código morto)
└── utils/
    ├── __init__.py
    └── helpers.py             # helpers parcialmente não usados
```

| Linguagem | Arquivos | LOC |
|---|---|---|
| Python | 15 | 1158 |

Maiores arquivos: `routes/task_routes.py` (299), `routes/report_routes.py` (223), `routes/user_routes.py` (211), `utils/helpers.py` (116), `seed.py` (99).

## 4. Arquitetura

### 4.1 Classificação
**Rótulo:** Monolítico em camadas (Layered), parcialmente aplicado.

**Justificativa:** Há diretórios por camada técnica (`models/`, `routes/`, `services/`, `utils/`) e o entrypoint `app.py` registra blueprints. Porém a camada `routes/` acumula roteamento HTTP, validação, regra de negócio, acesso a dados e serialização (ex.: `routes/task_routes.py:11-63`), não existindo controllers/services de domínio. `services/notification_service.py` não é referenciado por nenhum módulo, e `utils/helpers.py:57-108` (`process_task_data`) duplica validações que estão inline nas rotas. Não existe camada de configuração nem middleware de erro.

### 4.2 Tabela de camadas

| Camada candidata | Diretório/arquivo | Existe? | Veredito |
|---|---|---|---|
| Model | `models/task.py`, `models/user.py`, `models/category.py` | sim | Parcial — entidades e `to_dict`, mas `User.to_dict` expõe senha e o hashing MD5 vive no Model |
| Controller | `routes/*.py` | sim | Papel violado — roteiam **e** executam regra de negócio, validação e serialização |
| View | — | não | Ausente (API); representação JSON está embutida nas rotas |
| Service | `services/notification_service.py` | sim | Decorativa — nunca importado, estado mutável global na instância |
| Config | — | não | Ausente — config hardcoded em `app.py:11-13` |
| Middleware | — | não | Ausente — `try/except` repetido por handler |
| Data access | `models/*.py` + queries nas rotas | parcial | ORM usado diretamente nas rotas, sem repositórios |
| Utils | `utils/helpers.py` | sim | Parcial — alguns helpers usados (`format_date`, `calculate_percentage`), outros duplicam lógica das rotas |

Legenda: `adequada` | `parcial` | `papel violado` | `ausente` | `decorativa`

### 4.3 Leitura dos arquivos-chave

| Arquivo | LOC | Papel real | Observações |
|---|---|---|---|
| `app.py` | 34 | Composition root + config + rotas `/` e `/health` | `SECRET_KEY` literal (`:13`), `debug=True` (`:34`), `db.create_all()` no import (`:30-31`), imports não usados (`:7`) |
| `models/user.py` | 38 | Entidade + hashing | MD5 (`:29`, `:32`); `to_dict` inclui `password` (`:21`) |
| `models/task.py` | 60 | Entidade + serialização + regras | `to_dict`, `validate_status`, `validate_priority`, `is_overdue` — regra de domínio aceitável, mas duplicada nas rotas |
| `routes/task_routes.py` | 299 | Roteamento + regra + queries + serialização | Serialização manual duplicando `Task.to_dict` (`:16-59`); N+1 (`:41-57`); `except:` nu (`:62`); `Query.get` legado |
| `routes/user_routes.py` | 211 | Roteamento + regra + queries | Login retorna token fake (`:210`); `to_dict` devolve hash de senha (`:85`, `:129`, `:209`); N+1 por `len(u.tasks)` (`:22`) |
| `routes/report_routes.py` | 223 | Relatórios + CRUD de categorias | Múltiplas contagens separadas (`:19-28`) e N+1 por usuário (`:55-56`, `:163`); `except:` nu |
| `services/notification_service.py` | 48 | Serviço de e-mail não utilizado | Credenciais SMTP hardcoded (`:7-10`); lista mutável compartilhada (`:6`) |
| `utils/helpers.py` | 116 | Helpers | `process_task_data` (`:57-108`) duplica validação das rotas; imports não usados (`:3-7`) |

## 5. Entrypoints, configuração e testes

- **Entrypoints:** `app.py` (servidor HTTP); `seed.py` (script de carga, importa `app`).
- **Configuração:** hardcoded em `app.py:11-13` (`SQLALCHEMY_DATABASE_URI`, `SECRET_KEY`). `python-dotenv==1.0.0` declarado mas não importado em nenhum arquivo.
- **Testes:** ausentes — nenhum `tests/`, `pytest.ini` ou dependência de teste.
- **CI/CD:** ausente (sem `.github/workflows/`, `.gitlab-ci.yml`).
- **Containerização:** ausente (sem `Dockerfile`/`docker-compose.yml`).
- **Dependências mortas:** `marshmallow`, `requests`, `python-dotenv` declaradas em `requirements.txt` e não usadas no código.

## 6. Candidatos a anti-pattern

Achados que a leitura de código já revelou. **Não** são o relatório de auditoria — a Fase 2 confirma, classifica severidade e localiza linha exata.

| # | Sinal observado | Evidência | Anti-pattern candidato |
|---|---|---|---|
| 1 | `SECRET_KEY` literal no código | `app.py:13` | Credencial hardcoded |
| 2 | Senha de e-mail literal | `services/notification_service.py:10` | Credencial hardcoded |
| 3 | Hash de senha com MD5 sem salt | `models/user.py:29`, `:32` | Criptografia fraca |
| 4 | `to_dict` devolve o hash da senha | `models/user.py:21` | Exposição de dado sensível |
| 5 | Login devolve token fake previsível | `routes/user_routes.py:210` | Autenticação fictícia / insegura |
| 6 | Rotas de escrita sem autenticação/autorização | `routes/task_routes.py:85`, `:156`, `:225` | Ausência de autorização |
| 7 | Query dentro de loop sobre tasks | `routes/task_routes.py:41-57` | N+1 queries |
| 8 | Query dentro de loop sobre usuários | `routes/report_routes.py:55-56` | N+1 queries |
| 9 | Query por categoria em loop | `routes/report_routes.py:163` | N+1 queries |
| 10 | `len(u.tasks)` força lazy load por usuário | `routes/user_routes.py:22` | N+1 queries |
| 11 | Regra de negócio e validação dentro das rotas | `routes/task_routes.py:85-154` | Lógica de negócio no Controller |
| 12 | Serialização manual duplicando `Task.to_dict` | `routes/task_routes.py:16-59`, `routes/user_routes.py:162-181` | Duplicação de código |
| 13 | Validação duplicada entre helper e rotas | `utils/helpers.py:57-108` vs `routes/task_routes.py:92-114` | Duplicação de código |
| 14 | `except:` nu engolindo exceções | `routes/task_routes.py:62`, `:236`; `routes/report_routes.py:186`, `:207`, `:221` | Tratamento de erro genérico |
| 15 | `try/except` repetido por handler, sem handler global | `routes/*.py` | Tratamento de erro não centralizado |
| 16 | `datetime.utcnow()` (deprecated no Python 3.12) | `models/task.py:15-16`, `:52`; `routes/*` (várias) | API deprecated |
| 17 | `Query.get()` (legacy no SQLAlchemy 2.0) | `routes/task_routes.py:67`, `:117`, `:122`; `routes/user_routes.py:29` | API deprecated |
| 18 | `db.create_all()` no import, sem migrations | `app.py:30-31` | Schema sem versionamento |
| 19 | Estado mutável compartilhado (`self.notifications`) | `services/notification_service.py:6` | Estado global mutável |
| 20 | Módulo de serviço nunca importado | `services/notification_service.py` inteiro | Código morto |
| 21 | Imports não usados | `app.py:7`; `routes/task_routes.py:7`; `routes/user_routes.py:6`; `utils/helpers.py:3-7` | Código morto |
| 22 | `print()` como logging de aplicação | `routes/task_routes.py:149`, `:153`, `:219`, `:234`; `routes/user_routes.py:83`, `:89`, `:147` | Logging inadequado |
| 23 | `debug=True` e bind `0.0.0.0` | `app.py:34` | Config insegura |
| 24 | Constantes de domínio repetidas como literais | `['pending','in_progress','done','cancelled']` em `routes/task_routes.py:110`, `:177` etc. | Magic values / duplicação |

## 7. Notas e lacunas

- O ambiente possui Python 3.12.3; as versões das libs são as **declaradas** em `requirements.txt` (não foi verificado se estão instaladas).
- Não há lockfile (`requirements.txt` sem hashes/pin transitivo), então versões efetivas de runtime não podem ser confirmadas.
- Não foi possível avaliar comportamento em runtime (a Fase 1 é somente leitura); boot e respostas dos endpoints serão verificados na Fase 4.
- Dependências declaradas e não confirmadas no código: `marshmallow`, `requests`, `python-dotenv`.
- `seed.py` carrega senhas fracas de exemplo (`1234`, `abcd`, `pass`) — relevante para auditoria, não para detecção de stack.
- As referências da skill cobrem adequadamente o ecossistema Python/Flask; nenhuma lacuna de cobertura identificada.
