# code-smells-project

API de e-commerce em Python/Flask, organizada em domínio, casos de uso, adapters HTTP e infraestrutura SQLite.

## Requisitos

- Python 3.12 ou superior
- Dependências de `requirements.txt`

## Como rodar

Defina um segredo com pelo menos 32 caracteres. O caminho do banco e as demais opções são externos ao código:

```bash
export APP_SECRET='substitua-por-um-segredo-aleatorio-com-32-caracteres'
export DATABASE_PATH='loja.db'
pip install -r requirements.txt
python app.py
```

A aplicação sobe por padrão em `http://127.0.0.1:5000`. O schema SQLite e os produtos de exemplo são criados na primeira requisição que acessa a API; importar `app` não cria nem altera o banco.

## Primeiro administrador

Uma instalação nova não possui credenciais padrão. Para criar o primeiro administrador, informe as duas variáveis apenas no primeiro boot:

```bash
export BOOTSTRAP_ADMIN_EMAIL='admin@example.com'
export BOOTSTRAP_ADMIN_PASSWORD='uma-senha-forte-e-unica'
```

Depois do primeiro acesso bem-sucedido, remova essas variáveis do ambiente. Senhas legadas existentes são convertidas para hash adaptativo durante a inicialização.

O login em `POST /login` devolve um token. Envie-o nas rotas protegidas:

```text
Authorization: Bearer <token>
```

Leituras de produtos, cadastro de cliente, login e health check são públicos. Alterações de catálogo, relatórios, listagem global e rotas administrativas exigem administrador; cada cliente pode criar e consultar somente os próprios pedidos.

## Configuração

| Variável | Default | Finalidade |
|---|---|---|
| `APP_SECRET` | obrigatório | assinatura de tokens e segredo Flask |
| `DATABASE_PATH` | `loja.db` | arquivo SQLite |
| `APP_ENV` | `development` | nome do ambiente exibido no health |
| `APP_HOST` | `127.0.0.1` | interface de bind |
| `APP_PORT` | `5000` | porta HTTP |
| `APP_DEBUG` | `false` | modo debug |
| `CORS_ORIGINS` | `*` | origem única ou lista separada por vírgulas |
| `TOKEN_TTL_SECONDS` | `3600` | validade do token de acesso |

`POST /admin/query` continua registrado por compatibilidade de método/path, porém rejeita execução de SQL arbitrário com `410 Gone` após autenticação administrativa.

## Testes

Os testes usam somente a biblioteca padrão e bancos temporários:

```bash
APP_SECRET='segredo-de-teste-com-pelo-menos-32-caracteres' \
python -m unittest discover -s tests -v
```
