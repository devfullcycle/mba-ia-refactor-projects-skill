# code-smells-project

API de E-commerce em Python/Flask, refatorada para MVC pela skill `refactor-arch`.

## Como rodar

```bash
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, com produtos e usuários de exemplo (senhas gravadas com hash).

## Configuração (variáveis de ambiente — ver `.env.example`)

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | aleatória por processo | Chave do Flask |
| `DEBUG` | `false` | Modo debug |
| `HOST` / `PORT` | `127.0.0.1` / `5000` | Endereço do servidor |
| `DB_PATH` | `loja.db` | Arquivo SQLite |
| `CORS_ORIGINS` | `*` | Origens permitidas (separadas por vírgula) |
| `ADMIN_TOKEN` | vazio | Habilita `/admin/*`; enviar no header `X-Admin-Token` |

## Estrutura

```
app.py            # composition root (create_app)
config/           # settings (env) e constants (domínio)
database/         # conexão por request, schema e seed
models/           # acesso a dados (SQL parametrizado)
services/         # regras de negócio (pedido, relatório, usuário, notificações)
validators/       # validação de entrada
controllers/      # orquestração HTTP por recurso
routes/           # blueprints (só mapeamento)
views/            # serializers (nunca expõem senha)
middlewares/      # error handler central, auth admin
exceptions.py     # exceções de domínio -> status HTTP
```
