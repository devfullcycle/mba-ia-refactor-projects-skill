# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, refatorada para o padrão MVC.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env   # ajuste SECRET_KEY e demais valores
python app.py          # ou: python -m src.app
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo (desative com `SEED_DB=false`). Senhas em texto plano de bancos criados pela versão anterior são convertidas para hash na inicialização.

## Estrutura

```text
app.py                  # entrypoint de compatibilidade (expõe `app` para WSGI)
src/
├── app.py              # application factory (create_app) e main()
├── config/             # settings via variáveis de ambiente, conexão/schema SQLite, seed
├── models/             # acesso a dados com queries parametrizadas
├── controllers/        # regras de negócio e validações
├── routes/             # Blueprints HTTP (apenas mapeiam request -> controller)
├── services/           # notificações de pedido
├── middlewares/        # tratamento global de erros e token administrativo
└── utils/              # exceções de domínio
```

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória por processo | Chave do Flask |
| `DEBUG` | `false` | Modo debug (nunca ative em produção) |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `DB_PATH` | `loja.db` | Arquivo SQLite |
| `SEED_DB` / `SEED_ADMIN_PASSWORD` | `true` / `admin123` | Dados de exemplo |
| `ADMIN_TOKEN` | vazio | Habilita `/admin/reset-db` e `/admin/query` (header `X-Admin-Token`) |
| `LOG_LEVEL` | `INFO` | Nível de log |
