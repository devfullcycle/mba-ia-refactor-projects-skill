# task-manager-api

API Flask para gestão de tasks, usuários, categorias e relatórios.

## Arquitetura

O projeto separa os papéis por responsabilidade:

- `routes/`: adapters HTTP e serialização;
- `controllers/`: casos de uso e fronteiras transacionais;
- `models/`: entidades e invariantes;
- `repositories/`: persistência SQLAlchemy 2 e consultas agregadas;
- `schemas/`: validação de entrada e presenters públicos;
- `services/`: autenticação, relógio e integrações;
- `app.py`: application factory/composition root;
- `seed.py`: adapter CLI do seed atômico.

Importar `app.py` não cria tabelas nem modifica o banco. O schema é criado
explicitamente pelo seed ou pelo ambiente que hospeda a aplicação.

## Configuração

Copie as chaves de `.env.example` para o mecanismo seguro do seu ambiente. A
aplicação não carrega arquivos `.env` automaticamente e exige
`TASK_MANAGER_SECRET_KEY`. Debug fica desligado por padrão e CORS só é ativado
quando `TASK_MANAGER_CORS_ORIGINS` é definido.

## Autenticação e autorização

Envie o token retornado por `POST /login` no header
`Authorization: Bearer <token>`. A matriz de acesso é:

- público: `GET /`, `GET /health` e `POST /login`;
- `user`, `manager` e `admin`: leitura de tasks e categorias;
- `manager` e `admin`: escrita de tasks/categorias e relatórios;
- `admin`: leitura e escrita de usuários.

Requisições sem token válido recebem `401`; um papel autenticado sem permissão
recebe `403`. Os usuários iniciais só são criados pelo seed com senhas fornecidas
pelo ambiente.

## Como rodar

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt

export TASK_MANAGER_SECRET_KEY='gere-um-segredo-longo'
export TASK_MANAGER_SEED_ADMIN_PASSWORD='defina-uma-senha'
export TASK_MANAGER_SEED_USER_PASSWORD='defina-outra-senha'
export TASK_MANAGER_SEED_MANAGER_PASSWORD='defina-outra-senha'

.venv/bin/python seed.py
.venv/bin/python app.py
```

A aplicação sobe por padrão em `http://127.0.0.1:5000`. Para uso fora de
desenvolvimento, carregue `create_app` em um servidor WSGI e mantenha debug
desligado.

## Testes

Os testes usam apenas SQLite temporário e não acessam `instance/tasks.db`:

```bash
.venv/bin/python -m unittest discover -s tests -v
```
