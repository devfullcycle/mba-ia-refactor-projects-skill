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
code-smells-project/
├── app.py                  # composition root (create_app)
├── exceptions.py           # exceções de domínio -> status HTTP
├── requirements.txt
├── .env.example
│
├── config/                 # configuração
│   ├── settings.py         #   variáveis de ambiente
│   └── constants.py        #   constantes de domínio
│
├── database/               # persistência
│   ├── connection.py       #   conexão por request
│   └── schema.py           #   schema e seed
│
├── models/                 # M — acesso a dados (SQL parametrizado)
│   └── produto, usuario, pedido, relatorio, sistema
│
├── views/                  # V — serializers (nunca expõem senha)
│   └── serializers.py
│
├── controllers/            # C — orquestração HTTP por recurso
│   └── produto, usuario, pedido, relatorio, sistema
│
├── routes/                 # blueprints (só mapeamento de URLs)
│
├── services/               # regras de negócio
│   └── pedido, relatorio, usuario, notificacao
│
├── validators/             # validação de entrada
│   └── produto, usuario, pedido
│
└── middlewares/            # transversais
    ├── error_handler.py    #   error handler central
    └── auth.py             #   auth admin
```

> O relatório de auditoria da skill fica na raiz do repositório: `../reports/audit-project-1.md`.

### Fluxo de uma requisição

```
Request -> routes -> controllers -> validators
                          |
                          v
                      services -> models -> database
                          |
                          v
                       views -> Response
```
