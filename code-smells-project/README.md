# code-smells-project

API de E-commerce em Python/Flask refatorada para **MVC** (com camada de serviços) no desafio `refactor-arch`.

## Como rodar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Or with uv (uses `.venv` automatically):

```bash
uv sync
uv run python app.py
```

A aplicação sobe em `http://127.0.0.1:5003` por padrão. O banco SQLite (`loja.db`) é criado/migrado no boot, com produtos e usuários de exemplo.

### Variáveis de ambiente

| Variável | Default | Descrição |
|----------|---------|-----------|
| `SECRET_KEY` | `dev-only-change-me` | Chave Flask (não expor) |
| `FLASK_DEBUG` | `0` | `1` habilita debug |
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `5003` | Porta HTTP |
| `DB_PATH` | `loja.db` | Caminho do SQLite |
| `AMBIENTE` | `desenvolvimento` | Label no `/health` |
| `ADMIN_TOKEN` | _(vazio)_ | Token para `POST /admin/reset-db` |

## Arquitetura (MVC)

```text
HTTP → views/routes.py → controllers/ → services/ → models/ → db (SQLite)
```

| Camada | Pacote | Responsabilidade |
|--------|--------|------------------|
| View | `src/views` | Registro de rotas |
| Controller | `src/controllers` | HTTP in/out |
| Service | `src/services` | Regras de negócio |
| Model | `src/models` | SQL parametrizado |
| Config/DB | `src/config`, `src/db` | Settings e conexão por request |

## Testes

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Endpoints

Mesmos paths da API original (`/produtos`, `/usuarios`, `/pedidos`, `/login`, `/relatorios/vendas`, `/health`).

- `POST /admin/query` **removido** (SQL arbitrário).
- `POST /admin/reset-db` exige header `X-Admin-Token` igual a `ADMIN_TOKEN`.

Usuários seed: `joao@email.com` / `123456` (senhas agora hasheadas).

Relatórios da skill: pasta [`docs/`](./docs/).
