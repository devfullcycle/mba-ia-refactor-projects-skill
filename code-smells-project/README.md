# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch` — **refatorada para MVC** pela skill (`.claude/skills/refactor-arch`).

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # opcional: exporte as variáveis desejadas
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (configure `PORT`/`HOST` por variável de ambiente — no macOS a porta 5000 costuma estar ocupada pelo AirPlay, use `PORT=5051 python app.py`). O banco SQLite (`loja.db`, ou `DATABASE_PATH`) é criado automaticamente no primeiro boot com produtos e usuários de exemplo (senhas armazenadas com hash).

## Estrutura

```
app.py                      # entry point (shim) -> src.app.create_app()
src/
├── app.py                  # composition root (injeção de dependências)
├── config/settings.py      # configuração via variáveis de ambiente
├── database/               # conexão por request, schema, seed e migração de senhas
├── models/                 # produto, usuario, pedido, admin (SQL parametrizado + regras)
├── controllers/            # fluxo dos casos de uso
├── views/                  # Blueprints (rotas HTTP)
├── validators/             # validação de entrada
├── services/               # notificações
├── middlewares/            # error handler central + guard de admin
└── utils/errors.py         # exceções de domínio
```

## Endpoints administrativos

`POST /admin/reset-db` e `POST /admin/query` só funcionam com `ADMIN_TOKEN` definido e o header `X-Admin-Token`. `/admin/query` aceita apenas um `SELECT` executado em conexão somente leitura.
