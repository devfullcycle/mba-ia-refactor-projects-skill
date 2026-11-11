# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, refatorada para o padrão MVC.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # ajuste SECRET_KEY e demais valores
python app.py          # ou: python -m src.app
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`, relativo à raiz do projeto) e seus índices são criados/migrados automaticamente no boot. Com `SEED_DB=true` e `APP_ENV` diferente de `producao`, são criados produtos e usuários de exemplo; senhas não informadas em `SEED_ADMIN_PASSWORD` / `SEED_CLIENTE_PASSWORD` são geradas e exibidas uma vez no log.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Autenticação

`POST /login` devolve um `token` assinado (validade `TOKEN_TTL_SEGUNDOS`). Envie-o em `Authorization: Bearer <token>`.

| Acesso | Endpoints |
|---|---|
| Público | `GET /`, `GET /health`, `GET /produtos`, `GET /produtos/busca`, `GET /produtos/<id>`, `POST /usuarios`, `POST /login` |
| Usuário autenticado | `POST /pedidos` (pedido do próprio usuário), `GET /usuarios/<id>` e `GET /pedidos/usuario/<id>` (apenas os próprios dados; admin vê todos) |
| Admin (`tipo = admin`) | `POST/PUT/DELETE /produtos`, `GET /usuarios`, `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas` |
| Manutenção (`X-Admin-Token`) | `POST /admin/reset-db`, `POST /admin/query` (somente leitura, sem acesso a `usuarios.senha`) |

Regras de pedido: transições `pendente → aprovado | cancelado`, `aprovado → enviado | cancelado`, `enviado → entregue`; cancelar devolve o estoque. O relatório de vendas não fatura pedidos cancelados. `DELETE /produtos/<id>` é exclusão lógica (`ativo = 0`).

## Estrutura

```text
app.py                  # entrypoint de compatibilidade (expõe `app` para WSGI)
src/
├── app.py              # application factory (create_app) e main()
├── config/             # settings via variáveis de ambiente, conexão/schema/migrações SQLite, seed
├── models/             # acesso a dados com queries parametrizadas, StatusPedido
├── controllers/        # regras de negócio, validações e autorização por recurso
├── routes/             # Blueprints HTTP (apenas mapeiam request -> controller)
├── services/           # tokens de acesso e notificações de pedido
├── middlewares/        # tratamento global de erros, login_required/admin_required, token de manutenção
└── utils/              # exceções de domínio, validadores, envelope de resposta
tests/                  # suíte pytest (test_client com banco temporário)
```

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória por processo | Assina a sessão e os tokens de login |
| `TOKEN_TTL_SEGUNDOS` | `3600` | Validade do token de login |
| `APP_ENV` | `producao` | Em `producao` o seed nunca roda |
| `DEBUG` | `false` | Modo debug (nunca ative em produção) |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `CORS_ORIGINS` | vazio (CORS desabilitado) | Origens permitidas, separadas por vírgula |
| `DB_PATH` | `loja.db` | Arquivo SQLite (relativo à raiz do projeto) |
| `SEED_DB` | `false` | Popula dados de exemplo (fora de produção) |
| `SEED_ADMIN_PASSWORD` / `SEED_CLIENTE_PASSWORD` | geradas | Senhas dos usuários de exemplo |
| `ADMIN_TOKEN` | vazio | Habilita `/admin/*` (header `X-Admin-Token`) |
| `LOG_LEVEL` | `INFO` | Nível de log |
